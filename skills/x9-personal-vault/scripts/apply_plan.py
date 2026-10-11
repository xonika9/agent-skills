#!/usr/bin/env python3
"""Apply a personal-vault file manifest with verification, a journal, and undo.

Operations: mkdir, move, copy, symlink, remove. Every operation is validated
before anything changes and rechecked just before it runs. Names are compared
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


def compare_trees(src: Path, copy: Path) -> str | None:
    """Return the first entry of src without an identical twin in copy."""
    for rel, entry in walk_files(src):
        twin = copy if rel == Path(".") else copy / rel
        if is_link(entry):
            if not is_link(twin) or os.readlink(twin) != os.readlink(entry):
                return str(rel)
        elif not twin.is_file() or is_link(twin) or sha256(twin) != sha256(entry):
            return str(rel)
    return None


def within(path: Path, root: Path) -> bool:
    path_key, root_key = key(path), key(root)
    return path_key == root_key or path_key.startswith(root_key.rstrip(os.sep) + os.sep)


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
        if not within(Path(os.path.realpath(path.parent)), self.vault) or key(os.path.realpath(path.parent)) != key(path.parent):
            raise PlanError(f"{field} goes through a link: {value}")
        for link in self.planned_links:
            if within(path, link):
                raise PlanError(f"{field} is inside a link created by this plan: {value}")
        return path

    def source(self, value: str, op: str) -> Path:
        path = self.lexical(value)
        resolved = Path(os.path.realpath(path.parent)) / path.name
        if op in ("move", "remove") and within(path, self.vault) and key(resolved) != key(path):
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


def copy_file(src: Path, dst: Path) -> None:
    """Copy one file with its metadata, failing if dst exists."""
    if sys.platform == "darwin":
        libc = ctypes.CDLL(None, use_errno=True)
        libc.copyfile.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_uint32]
        if libc.copyfile(os.fsencode(src), os.fsencode(dst), None, COPYFILE_FLAGS) != 0:
            error = ctypes.get_errno()
            raise OSError(error, os.strerror(error), str(dst))
        return
    with src.open("rb") as reader, dst.open("xb") as writer:
        shutil.copyfileobj(reader, writer, 1 << 20)
    shutil.copystat(src, dst, follow_symlinks=False)




def copy_tree(src: Path, dst: Path, created: list[dict]) -> None:
    """Copy files and links, verifying each file and recording every entry as it is created."""
    if is_link(src):
        target = os.readlink(src)
        os.symlink(target, dst)
        created.append({"path": str(dst), "link": target})
        return
    if src.is_file():
        copy_file(src, dst)
        created.append({"path": str(dst), "sha256": None})
        digest = sha256(src)
        if sha256(dst) != digest:
            raise PlanError(f"copy verification failed: {dst}")
        created[-1]["sha256"] = digest
        return
    os.mkdir(dst)
    created.append({"path": str(dst), "dir": True})
    for current, dirs, files in os.walk(src, followlinks=False):
        base = Path(current)
        target_base = dst / base.relative_to(src)
        for name in sorted(dirs):
            entry = base / name
            if is_link(entry):
                copy_tree(entry, target_base / name, created)
            else:
                os.mkdir(target_base / name)
                created.append({"path": str(target_base / name), "dir": True})
        dirs[:] = [d for d in dirs if not is_link(base / d)]
        for name in sorted(files):
            copy_tree(base / name, target_base / name, created)
    shutil.copystat(src, dst)


def discard(created: list[dict]) -> None:
    """Remove entries this run created, newest first."""
    for item in reversed(created):
        path = Path(item["path"])
        if item.get("dir"):
            try:
                os.rmdir(path)
            except OSError:
                pass
        elif lexists(path):
            path.unlink()


def fresh_copy(src: Path, dst: Path) -> list[dict]:
    created: list[dict] = []
    try:
        copy_tree(src, dst, created)
    except BaseException:
        discard(created)
        raise
    return created


def remove_tree(path: Path) -> None:
    if is_link(path) or path.is_file():
        path.unlink()
    else:
        shutil.rmtree(path)


def same_device(src: Path, dst_parent: Path) -> bool:
    return os.lstat(src).st_dev == os.stat(dst_parent).st_dev


def apply(planned: list[dict], journal: Path) -> dict:
    journal.parent.mkdir(parents=True, exist_ok=True)
    done = 0
    with journal.open("x", encoding="utf-8") as log:
        def record(entry: dict) -> None:
            log.write(json.dumps(entry, ensure_ascii=False) + "\n")
            log.flush()
            os.fsync(log.fileno())

        try:
            for seq, step in enumerate(planned):
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
    entries, undone = load_journal(journal)
    if undone:
        raise PlanError(f"journal was already undone: {journal}")
    reversed_count, skipped = 0, []
    for entry in reversed(entries):
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
    """Put back every source entry missing after a cross-device move, then drop the copy."""
    src, dst = Path(entry["from"]), Path(entry["to"])
    changed = changed_since(dst, entry["created"])
    if changed:
        return f"moved copy changed since apply, kept both: {changed}"
    restored: list[dict] = []
    try:
        for rel, item in walk_files(dst):
            back = src if rel == Path(".") else src / rel
            if lexists(back):
                continue
            back.parent.mkdir(parents=True, exist_ok=True)
            copy_tree(item, back, restored)
    except (PlanError, OSError) as error:
        return f"could not restore {src}: {error}; the moved copy is kept at {dst}"
    mismatch = compare_trees(dst, src)
    if mismatch:
        return f"restored {src} differs at {mismatch}; the moved copy is kept at {dst}"
    remove_tree(dst)
    return None


def changed_since(root: Path, created: list[dict]) -> str | None:
    known = {key(item["path"]) for item in created}
    if not lexists(root):
        return str(root)
    for _, entry in walk_files(root):
        if key(entry) not in known:
            return str(entry)
    for item in created:
        path = Path(item["path"])
        if "sha256" in item and (not path.is_file() or sha256(path) != item["sha256"]):
            return item["path"]
        if "link" in item and (not is_link(path) or os.readlink(path) != item["link"]):
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
