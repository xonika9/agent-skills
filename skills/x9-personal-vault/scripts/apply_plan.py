#!/usr/bin/env python3
"""Apply a personal-vault file manifest with verification, a journal, and undo.

Operations: mkdir, move, copy, symlink, remove. Every operation is validated
before anything changes and rechecked before apply or undo. These checks do not
lock filesystem paths against changes between checks and system calls. Names are compared
after Unicode NFC normalization and case folding, so nothing is overwritten on
case-insensitive or normalizing file systems. Copies are verified by SHA-256
and keep file metadata where the platform allows. Destinations must stay
inside the vault and never pass through a link. Cloud files that are not
downloaded (macOS dataless files) are refused. Supported on macOS and Linux. `remove` runs only in a manifest of its own and
deletes a source only when an independent, byte-identical copy exists inside
the vault. Without --apply the script only reports the plan.
"""

from __future__ import annotations

import argparse
import ctypes
import errno
import datetime as dt
import hashlib
import json
import os
import shutil
import stat
import sys
import unicodedata
from pathlib import Path

JOURNAL_DIR = ".x9-personal-vault"
SF_DATALESS = getattr(stat, "SF_DATALESS", 0x40000000)
# macOS copyfile(3): ACL | STAT | XATTR | DATA, fail if the destination exists, never follow the source link.
COPYFILE_FLAGS = 0xF | (1 << 17) | (1 << 18)

# Metadata fingerprints exclude atime: reading to verify a copy changes it.
_METADATA_LIBC = ctypes.CDLL(None, use_errno=True) if sys.platform == "darwin" else None


def metadata_snapshot(descriptor: int) -> dict:
    info = os.fstat(descriptor)
    attributes = []
    acl_digest = None
    if sys.platform == "darwin":
        libc = _METADATA_LIBC
        libc.flistxattr.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]
        libc.flistxattr.restype = ctypes.c_ssize_t
        libc.fgetxattr.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint32, ctypes.c_int]
        libc.fgetxattr.restype = ctypes.c_ssize_t
        length = libc.flistxattr(descriptor, None, 0, 0)
        if length < 0:
            error = ctypes.get_errno()
            raise OSError(error, os.strerror(error))
        names = ctypes.create_string_buffer(length)
        if length and libc.flistxattr(descriptor, names, length, 0) != length:
            raise OSError("extended attributes changed while being read")
        for name in sorted(filter(None, names.raw.split(b"\0"))):
            length = libc.fgetxattr(descriptor, name, None, 0, 0, 0)
            if length < 0:
                error = ctypes.get_errno()
                raise OSError(error, os.strerror(error))
            value = ctypes.create_string_buffer(length)
            if libc.fgetxattr(descriptor, name, value, length, 0, 0) != length:
                raise OSError("extended attribute changed while being read")
            attributes.append((name, value.raw))
        libc.acl_get_fd_np.argtypes = [ctypes.c_int, ctypes.c_int]
        libc.acl_get_fd_np.restype = ctypes.c_void_p
        libc.acl_to_text.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ssize_t)]
        libc.acl_to_text.restype = ctypes.c_void_p
        libc.acl_free.argtypes = [ctypes.c_void_p]
        # macOS extended ACLs; a valid descriptor with no ACL returns ENOENT.
        acl = libc.acl_get_fd_np(descriptor, 0x100)
        if not acl:
            error = ctypes.get_errno()
            if error not in (errno.ENOENT, errno.ENOTSUP):
                raise OSError(error, os.strerror(error))
        else:
            acl_text = None
            try:
                acl_length = ctypes.c_ssize_t()
                acl_text = libc.acl_to_text(acl, ctypes.byref(acl_length))
                if not acl_text:
                    error = ctypes.get_errno()
                    raise OSError(error, os.strerror(error))
                acl_digest = hashlib.sha256(ctypes.string_at(acl_text, acl_length.value)).hexdigest()
            finally:
                if acl_text:
                    libc.acl_free(acl_text)
                libc.acl_free(acl)
    elif hasattr(os, "listxattr"):
        attributes = [(os.fsencode(name), os.getxattr(descriptor, name)) for name in sorted(os.listxattr(descriptor))]
    digest = hashlib.sha256()
    for name, value in attributes:
        digest.update(len(name).to_bytes(8, "big") + name + len(value).to_bytes(8, "big") + value)
    return {"mode": stat.S_IMODE(info.st_mode), "uid": info.st_uid, "gid": info.st_gid,
            "mtime_ns": info.st_mtime_ns, "flags": getattr(info, "st_flags", 0), "xattrs": digest.hexdigest(), "acl": acl_digest}


def path_metadata(path: Path) -> dict:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        return metadata_snapshot(descriptor)
    finally:
        os.close(descriptor)


class PlanError(Exception):
    pass


def key(value) -> str:
    return unicodedata.normalize("NFC", str(value)).casefold()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_placeholder(path: Path) -> bool:
    """macOS marks cloud files that are not downloaded as dataless."""
    try:
        return bool(getattr(os.lstat(path), "st_flags", 0) & SF_DATALESS)
    except OSError:
        return False


def lexists(path: Path) -> bool:
    return os.path.lexists(path)


def is_link(path: Path) -> bool:
    return os.path.islink(path)


def occupied(path: Path) -> Path | None:
    """Return the existing entry that path would collide with, if any."""
    if lexists(path):
        return path
    parent = path.parent
    if parent.is_dir():
        wanted = key(path.name)
        for name in os.listdir(parent):
            if key(name) == wanted:
                return parent / name
    return None


def walk_files(root: Path):
    """Yield (relative path, absolute path) for files and links under root, not following links."""
    if is_link(root) or root.is_file():
        yield Path("."), root
        return
    for current, dirs, files in os.walk(root, followlinks=False):
        base = Path(current)
        for name in sorted(dirs):
            entry = base / name
            if is_link(entry):
                yield entry.relative_to(root), entry
        dirs[:] = [d for d in dirs if not is_link(base / d)]
        for name in sorted(files):
            entry = base / name
            yield entry.relative_to(root), entry


def walk_entries(root: Path):
    """Include directories so verification and undo preserve empty/user directories."""
    yield Path("."), root
    if is_link(root) or not root.is_dir():
        return
    for current, dirs, files in os.walk(root, followlinks=False):
        base = Path(current)
        for name in sorted(dirs + files):
            entry = base / name
            yield entry.relative_to(root), entry
        dirs[:] = [name for name in dirs if not is_link(base / name)]


def compare_trees(src: Path, copy: Path) -> str | None:
    """Return the first entry of src without an identical twin in copy."""
    for rel, entry in walk_entries(src):
        twin = copy if rel == Path(".") else copy / rel
        if is_link(entry):
            if not is_link(twin) or os.readlink(twin) != os.readlink(entry):
                return str(rel)
        elif entry.is_dir():
            if not twin.is_dir() or is_link(twin):
                return str(rel)
        elif not twin.is_file() or is_link(twin) or sha256(twin) != sha256(entry):
            return str(rel)
    return None


def within(path: Path, root: Path) -> bool:
    # Collision equivalence is not filesystem containment on case-sensitive volumes.
    try:
        Path(os.path.abspath(path)).relative_to(Path(os.path.abspath(root)))
        return True
    except ValueError:
        return False


class Plan:
    def __init__(self, manifest: dict):
        vault = manifest.get("vault")
        if not vault or not Path(vault).is_absolute():
            raise PlanError("manifest needs an absolute 'vault' path")
        self.vault = Path(os.path.realpath(vault))
        if not self.vault.is_dir():
            raise PlanError(f"vault does not exist: {self.vault}")
        self.operations = manifest.get("operations")
        if not isinstance(self.operations, list) or not self.operations:
            raise PlanError("manifest needs a non-empty 'operations' list")
        self.planned_links: list[Path] = []

    def lexical(self, value: str) -> Path:
        path = Path(value)
        if not path.is_absolute():
            path = self.vault / path
        return Path(os.path.normpath(path))

    def destination(self, value: str, field: str) -> Path:
        """A path the plan creates: inside the vault, not through any link."""
        path = self.lexical(value)
        if path == self.vault or not within(path, self.vault):
            raise PlanError(f"{field} leaves the vault: {value}")
        if not within(Path(os.path.realpath(path.parent)), self.vault) or Path(os.path.realpath(path.parent)) != path.parent:
            raise PlanError(f"{field} goes through a link: {value}")
        for link in self.planned_links:
            if within(path, link):
                raise PlanError(f"{field} is inside a link created by this plan: {value}")
        return path

    def source(self, value: str, op: str) -> Path:
        path = self.lexical(value)
        resolved = Path(os.path.realpath(path.parent)) / path.name
        if op in ("move", "remove") and within(path, self.vault) and resolved != path:
            raise PlanError(f"{op} source goes through a link: {value}")
        return resolved

    def validate(self) -> list[dict]:
        ops = [raw.get("op") for raw in self.operations]
        if "remove" in ops and set(ops) != {"remove"}:
            raise PlanError("remove operations must be in a manifest of their own")
        planned: list[dict] = []
        claimed: dict[str, Path] = {}
        new_dirs: set[str] = set()
        for index, raw in enumerate(self.operations):
            op = raw.get("op")
            where = f"operation {index + 1} ({op})"
            if op == "mkdir":
                path = self.destination(raw["path"], "path")
                existing = occupied(path)
                if (existing and not existing.is_dir()) or key(path) in claimed:
                    raise PlanError(f"{where}: exists and is not a folder: {path}")
                new_dirs.add(key(path))
                planned.append({"op": op, "path": path})
            elif op in ("move", "copy"):
                src = self.source(raw["from"], op)
                dst = self.destination(raw["to"], "to")
                if not lexists(src):
                    raise PlanError(f"{where}: source missing: {src}")
                if occupied(dst) or key(dst) in claimed or key(dst) in new_dirs:
                    raise PlanError(f"{where}: destination already exists: {dst}")
                if within(dst, src):
                    raise PlanError(f"{where}: destination is inside the source")
                if within(self.vault, src):
                    raise PlanError(f"{where}: source contains the vault")
                for _, entry in walk_files(src):
                    if is_placeholder(entry):
                        raise PlanError(f"{where}: cloud placeholder not downloaded: {entry}")
                if not dst.parent.is_dir() and key(dst.parent) not in new_dirs:
                    raise PlanError(f"{where}: destination folder missing: {dst.parent}")
                claimed[key(dst)] = dst
                planned.append({"op": op, "from": src, "to": dst})
            elif op == "symlink":
                path = self.destination(raw["path"], "path")
                if occupied(path) or key(path) in claimed or key(path) in new_dirs:
                    raise PlanError(f"{where}: path already exists: {path}")
                if not Path(raw["target"]).is_absolute():
                    raise PlanError(f"{where}: target must be absolute")
                claimed[key(path)] = path
                self.planned_links.append(path)
                planned.append({"op": op, "path": path, "target": raw["target"]})
            elif op == "remove":
                planned.append(self.validate_remove(raw, where))
            else:
                raise PlanError(f"{where}: unknown operation")
        removes = [step for step in planned if step["op"] == "remove"]
        for step in removes:
            for other in removes:
                if within(other["verified_copy"], step["path"]):
                    raise PlanError(f"removing {step['path']} would delete the verified copy {other['verified_copy']}")
        return planned

    def validate_remove(self, raw: dict, where: str) -> dict:
        path = self.source(raw["path"], "remove")
        copy = self.destination(raw["verified_copy"], "verified_copy")
        if not lexists(path):
            raise PlanError(f"{where}: path missing: {path}")
        if within(self.vault, path) or key(path) == key(self.vault / JOURNAL_DIR):
            raise PlanError(f"{where}: refusing to remove the vault, its parent, or the journal")
        if not lexists(copy) or is_link(copy):
            raise PlanError(f"{where}: verified copy missing or a link: {copy}")
        real_path, real_copy = Path(os.path.realpath(path)), Path(os.path.realpath(copy))
        if os.path.samefile(path, copy) or within(real_copy, real_path) or within(real_path, real_copy):
            raise PlanError(f"{where}: the verified copy is not independent of the source")
        mismatch = compare_trees(path, copy)
        if mismatch:
            raise PlanError(f"{where}: copy differs from source: {mismatch}")
        return {"op": "remove", "path": path, "verified_copy": copy}


def copy_file(src: Path, dst: Path) -> list[int]:
    """Own an exclusive destination descriptor and clean up only that inode on failure."""
    source_fd = os.open(src, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    destination_fd = None
    owned = None
    try:
        destination_fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        owned = os.fstat(destination_fd)
        if sys.platform == "darwin":
            libc = ctypes.CDLL(None, use_errno=True)
            libc.fcopyfile.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
            if libc.fcopyfile(source_fd, destination_fd, None, 0xF) != 0:
                error = ctypes.get_errno()
                raise OSError(error, os.strerror(error), str(dst))
        else:
            with os.fdopen(os.dup(source_fd), "rb") as reader, os.fdopen(os.dup(destination_fd), "wb") as writer:
                shutil.copyfileobj(reader, writer, 1 << 20)
            shutil.copystat(src, dst, follow_symlinks=False)
        return [owned.st_dev, owned.st_ino]
    except BaseException:
        if owned is not None and lexists(dst):
            current = os.lstat(dst)
            if (current.st_dev, current.st_ino) == (owned.st_dev, owned.st_ino):
                dst.unlink()
        raise
    finally:
        os.close(source_fd)
        if destination_fd is not None:
            os.close(destination_fd)


def copy_directory_metadata(src: Path, dst: Path) -> None:
    """Copy directory metadata after contents, including macOS ACLs and xattrs."""
    if sys.platform == "darwin":
        libc = ctypes.CDLL(None, use_errno=True)
        libc.copyfile.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_uint32]
        if libc.copyfile(os.fsencode(src), os.fsencode(dst), None, 0x7) != 0:
            error = ctypes.get_errno()
            raise OSError(error, os.strerror(error), str(dst))
    else:
        shutil.copystat(src, dst, follow_symlinks=False)



def created_entry(path: Path, identity=None, **kind) -> dict:
    info = os.lstat(path)
    actual = [info.st_dev, info.st_ino]
    if identity is not None and actual != identity:
        raise PlanError(f"destination changed during copy: {path}")
    entry = {"path": str(path), "identity": actual, **kind}
    if not is_link(path):
        entry["metadata"] = path_metadata(path)
    return entry


def entry_changed(item: dict, *, directory_times=True) -> bool:
    path = Path(item["path"])
    if not lexists(path) or "identity" not in item:
        return True
    info = os.lstat(path)
    if [info.st_dev, info.st_ino] != item["identity"]:
        return True
    if "link" in item:
        return not is_link(path) or os.readlink(path) != item["link"]
    if is_link(path) or (not path.is_dir() if item.get("dir") else not path.is_file()):
        return True
    if "metadata" not in item:
        return True
    current, expected = path_metadata(path), item["metadata"]
    if item.get("dir") and not directory_times:
        current = {k: v for k, v in current.items() if k != "mtime_ns"}
        expected = {k: v for k, v in expected.items() if k != "mtime_ns"}
    if current != expected:
        return True
    return item.get("sha256") is not None and sha256(path) != item["sha256"]


def copy_tree(src: Path, dst: Path, created: list[dict]) -> None:
    """Record ownership immediately; copy metadata after directory contents."""
    if is_link(src):
        target = os.readlink(src)
        os.symlink(target, dst)
        created.append(created_entry(dst, link=target))
        return
    if src.is_file():
        identity = copy_file(src, dst)
        entry = created_entry(dst, identity, sha256=None)
        created.append(entry)
        digest = sha256(src)
        if sha256(dst) != digest or entry_changed(entry):
            raise PlanError(f"copy verification failed: {dst}")
        entry["sha256"] = digest
        return
    os.mkdir(dst)
    created.append(created_entry(dst, dir=True))
    for current, dirs, files in os.walk(src, followlinks=False):
        base = Path(current)
        target_base = dst / base.relative_to(src)
        for name in sorted(dirs):
            entry = base / name
            if is_link(entry):
                copy_tree(entry, target_base / name, created)
            else:
                os.mkdir(target_base / name)
                created.append(created_entry(target_base / name, dir=True))
        dirs[:] = [d for d in dirs if not is_link(base / d)]
        for name in sorted(files):
            copy_tree(base / name, target_base / name, created)
    owned = {item["path"]: item for item in created}
    for current, _, _ in os.walk(src, topdown=False, followlinks=False):
        base = Path(current)
        if is_link(base):
            continue
        target = dst / base.relative_to(src)
        item = owned[str(target)]
        if entry_changed(item, directory_times=False):
            raise PlanError(f"destination changed during copy: {target}")
        copy_directory_metadata(base, target)
        item["metadata"] = path_metadata(target)


def discard(created: list[dict]) -> list[str]:
    """Remove only unchanged owned entries; leave replacements and edits in place."""
    kept = []
    for item in reversed(created):
        path = Path(item["path"])
        if not lexists(path):
            continue
        try:
            if entry_changed(item, directory_times=False):
                kept.append(str(path))
            elif item.get("dir"):
                os.rmdir(path)
            else:
                path.unlink()
        except OSError:
            kept.append(str(path))
    return kept


def fresh_copy(src: Path, dst: Path) -> list[dict]:
    created: list[dict] = []
    try:
        copy_tree(src, dst, created)
    except BaseException as error:
        kept = discard(created)
        if kept:
            raise PlanError(f"{error}; cleanup kept changed or nonempty entries: {', '.join(kept)}") from error
        raise
    return created


def remove_tree(path: Path) -> None:
    if is_link(path) or path.is_file():
        path.unlink()
    else:
        shutil.rmtree(path)


def same_device(src: Path, dst_parent: Path) -> bool:
    return os.lstat(src).st_dev == os.stat(dst_parent).st_dev


def guard_parent(path: Path) -> None:
    """Reject a changed/symlinked ancestor before any script-owned write."""
    absolute = Path(os.path.abspath(path))
    if Path(os.path.realpath(absolute.parent)) != absolute.parent:
        raise PlanError(f"path parent changed or goes through a link: {path}")


def guard_step(step: dict, vault: Path) -> None:
    op = step["op"]
    destination = step.get("to") if op in ("move", "copy") else step.get("verified_copy") if op == "remove" else step.get("path")
    if destination is not None:
        destination = Path(destination)
        if destination == vault or not within(destination, vault):
            raise PlanError(f"destination leaves the vault: {destination}")
        guard_parent(destination)
    source = step.get("from") if op in ("move", "copy") else step.get("path") if op == "remove" else None
    if source is not None:
        guard_parent(Path(source))


def apply(planned: list[dict], journal: Path) -> dict:
    vault = journal.parent.parent
    guard_parent(journal)
    if journal.parent.is_symlink():
        raise PlanError("journal directory must not be a link")
    journal.parent.mkdir(parents=True, exist_ok=True)
    done = 0
    with journal.open("x", encoding="utf-8") as log:
        def record(entry: dict) -> None:
            log.write(json.dumps(entry, ensure_ascii=False) + "\n")
            log.flush()
            os.fsync(log.fileno())

        try:
            for seq, step in enumerate(planned):
                guard_parent(journal)
                guard_step(step, vault)
                record({"seq": seq, "status": "intent", **{k: v if isinstance(v, bool) else str(v) for k, v in step.items()}})
                record({"seq": seq, "status": "done", **apply_step(step, seq, record)})
                done += 1
        except (PlanError, OSError) as error:
            raise PlanError(f"{error}; {done} operations completed; undo with --undo {journal}") from error
    return {"applied": done, "journal": str(journal)}


def apply_step(step: dict, seq: int, record) -> dict:
    op = step["op"]
    if op == "mkdir":
        path = step["path"]
        existing = occupied(path)
        if existing and existing.is_dir():
            return {"created": []}
        missing = [p for p in [path, *path.parents] if not p.exists()]
        path.mkdir(parents=True)
        return {"created": [str(p) for p in reversed(missing)]}
    if op == "symlink":
        if occupied(step["path"]):
            raise PlanError(f"destination appeared before apply: {step['path']}")
        os.symlink(step["target"], step["path"])
        return {}
    if op == "remove":
        mismatch = compare_trees(step["path"], step["verified_copy"])
        if mismatch:
            raise PlanError(f"copy changed before removal: {mismatch}")
        remove_tree(step["path"])
        return {"irreversible": True}
    src, dst = step["from"], step["to"]
    if occupied(dst):
        raise PlanError(f"destination appeared before apply: {dst}")
    if op == "copy":
        return {"created": fresh_copy(src, dst)}
    if same_device(src, dst.parent):
        os.rename(src, dst)
        return {"renamed": True}
    created = fresh_copy(src, dst)
    mismatch = compare_trees(src, dst)
    if mismatch:
        discard(created)
        raise PlanError(f"move verification failed: {mismatch}")
    record({"seq": seq, "status": "copied", "created": created})
    remove_tree(src)
    return {"renamed": False, "created": created}


def load_journal(journal: Path) -> tuple[list[dict], bool]:
    states: dict[int, dict] = {}
    undone = False
    for line in journal.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        if entry.get("undone"):
            undone = True
            continue
        states.setdefault(entry["seq"], {}).update(entry)
    return [states[seq] for seq in sorted(states)], undone


def undo(journal: Path) -> dict:
    guard_parent(journal)
    if journal.is_symlink() or journal.parent.name != JOURNAL_DIR:
        raise PlanError("undo requires an unlinked vault journal")
    vault = journal.parent.parent
    entries, undone = load_journal(journal)
    if undone:
        raise PlanError(f"journal was already undone: {journal}")
    reversed_count, skipped = 0, []
    for entry in reversed(entries):
        guard_step(entry, vault)
        for item in entry.get("created", []):
            path = Path(item["path"] if isinstance(item, dict) else item)
            if not within(path, vault):
                raise PlanError(f"journal created path leaves the vault: {path}")
            guard_parent(path)
        note = undo_entry(entry)
        if note:
            skipped.append(note)
        else:
            reversed_count += 1
    with journal.open("a", encoding="utf-8") as log:
        log.write(json.dumps({"undone": True, "at": dt.datetime.now(dt.timezone.utc).isoformat()}) + "\n")
    return {"reversed": reversed_count, "skipped": skipped}


def undo_entry(entry: dict) -> str | None:
    op, status = entry["op"], entry["status"]
    if op == "remove":
        if status == "intent":
            return f"removal of {entry['path']} was interrupted; the full copy is {entry['verified_copy']}"
        return f"removed {entry['path']} cannot be restored; its copy is {entry['verified_copy']}"
    if op == "move" and status == "copied":
        return restore_move(entry)
    if status != "done":
        return f"operation {entry['seq'] + 1} ({op}) was interrupted; check {entry.get('to') or entry.get('path')} by hand"
    if op == "mkdir":
        kept = []
        for created in reversed(entry["created"]):
            try:
                os.rmdir(created)
            except OSError:
                kept.append(created)
        return f"folders not empty, kept: {', '.join(kept)}" if kept else None
    if op == "symlink":
        path = Path(entry["path"])
        if lexists(path) and is_link(path) and os.readlink(path) == entry["target"]:
            path.unlink()
            return None
        return f"link changed since apply: {path}"
    if op == "move" and entry.get("renamed"):
        src, dst = Path(entry["from"]), Path(entry["to"])
        if occupied(src) or not lexists(dst):
            return f"cannot move back {dst} to {src}"
        os.rename(dst, src)
        return None
    if op == "move":
        return restore_move(entry)
    dst = Path(entry["to"])
    changed = changed_since(dst, entry["created"])
    if changed:
        return f"copy changed since apply, kept: {changed}"
    remove_tree(dst)
    return None


def restore_move(entry: dict) -> str | None:
    """Restore missing entries, then metadata of newly restored directories."""
    src, dst = Path(entry["from"]), Path(entry["to"])
    changed = changed_since(dst, entry["created"])
    if changed:
        return f"moved copy changed since apply, kept both: {changed}"
    restored: list[dict] = []
    new_directories = []
    try:
        if not lexists(src):
            restored = fresh_copy(dst, src)
        else:
            for rel, item in walk_entries(dst):
                back = src if rel == Path(".") else src / rel
                if lexists(back):
                    continue
                back.parent.mkdir(parents=True, exist_ok=True)
                if item.is_dir() and not is_link(item):
                    back.mkdir()
                    new_directories.append((item, back))
                else:
                    copy_tree(item, back, restored)
            for item, back in reversed(new_directories):
                copy_directory_metadata(item, back)
        mismatch = compare_trees(dst, src)
        if mismatch:
            return f"restored {src} differs at {mismatch}; the moved copy is kept at {dst}"
        # Existing source directories may have been changed by interrupted removal.
        # Keep them untouched; a non-time metadata conflict retains the recovery copy.
        for rel, item in walk_entries(dst):
            if is_link(item):
                continue
            back = src if rel == Path(".") else src / rel
            before, after = path_metadata(item), path_metadata(back)
            if item.is_dir():
                before.pop("mtime_ns", None)
                after.pop("mtime_ns", None)
            if before != after:
                return f"restored metadata differs at {back}; the moved copy is kept at {dst}"
    except (PlanError, OSError) as error:
        return f"could not restore {src}: {error}; the moved copy is kept at {dst}"
    remove_tree(dst)
    return None


def changed_since(root: Path, created: list[dict]) -> str | None:
    known = {item["path"] for item in created}
    if not lexists(root):
        return str(root)
    for _, entry in walk_entries(root):
        if str(entry) not in known:
            return str(entry)
    for item in created:
        try:
            if entry_changed(item):
                return item["path"]
        except OSError:
            return item["path"]
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", nargs="?", type=Path)
    parser.add_argument("--apply", action="store_true", help="perform the operations")
    parser.add_argument("--undo", type=Path, metavar="JOURNAL", help="reverse a journal")
    args = parser.parse_args(argv)
    try:
        if args.undo:
            result = undo(args.undo)
        else:
            if not args.manifest:
                parser.error("a manifest is required")
            plan = Plan(json.loads(args.manifest.read_text(encoding="utf-8")))
            planned = plan.validate()
            if args.apply:
                stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
                result = apply(planned, plan.vault / JOURNAL_DIR / f"journal-{stamp}.jsonl")
            else:
                result = {"would_apply": [{k: str(v) for k, v in step.items()} for step in planned]}
    except (PlanError, KeyError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not result.get("skipped") else 2


if __name__ == "__main__":
    sys.exit(main())
