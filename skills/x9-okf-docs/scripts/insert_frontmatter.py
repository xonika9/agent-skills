#!/usr/bin/env python3
"""Inventory Markdown, write x9 OKF metadata, or remove retired fields without changing bodies."""

from __future__ import annotations

import argparse
import ctypes
import errno
import hashlib
import json
import os
import stat
import secrets
import sys
import tempfile
from pathlib import Path

from okf_rules import (
    BOM,
    FIELDS,
    REQUIRED,
    field_issue,
    line_endings,
    load_scope,
    markdown_files,
    nfc,
    parse_headers,
    partition,
    resolve_named,
    split_document,
    validate_fields,
)

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


INVENTORY_VERSION = 5
PROPOSER_KEYS = {"path", "confidence", "basis"}


def preferred_eol(data: bytes, fallback: bytes = b""):
    counts = line_endings(data)
    if not any(counts.values()):
        return preferred_eol(fallback) if fallback else b"\n"
    dominant = max(counts, key=counts.get)
    return {"crlf": b"\r\n", "lf": b"\n", "cr": b"\r"}[dominant]


def yaml_value(value):
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return json.dumps(value, ensure_ascii=False, separators=(", ", ": "))
    raise ValueError(f"unsupported metadata value: {value!r}")


def kept_lines(header: bytes, top_keys, dropped: set):
    """Return the header bytes without the top-level keys in `dropped`.

    Comments and blank lines that follow a dropped key belong to what comes next and stay.
    """
    lines = header.splitlines(keepends=True)
    starts = [(item["line"], item["key"]) for item in top_keys]
    kept = lines[: starts[0][0]] if starts else list(lines)
    for position, (start, key) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        span = lines[start:end]
        if key not in dropped:
            kept.extend(span)
            continue
        tail = len(span)
        while tail > 1 and (not span[tail - 1].strip() or span[tail - 1].startswith(b"#")):
            tail -= 1
        kept.extend(span[tail:])
    return b"".join(kept)


def rewrite_problem(header: bytes, result):
    """Explain why a header cannot be cut by lines safely, or return None."""
    if not result["top_keys"]:
        return None
    if not result["block"]:
        return "the header is written in { } style; rewrite it one field per line by hand first"
    lines = [item["line"] for item in result["top_keys"]]
    if lines != sorted(set(lines)) or lines[-1] >= len(header.splitlines()):
        return "several fields share a line or the line breaks are unusual; edit the header by hand"
    return None


def build_document(bom: bool, body: bytes, eol: bytes, serialized, preserved: bytes):
    if not serialized and not preserved.strip():
        return (BOM if bom else b"") + body
    output = b"---" + eol
    for key, value in serialized:
        output += f"{key}: {yaml_value(value)}".encode("utf-8") + eol
    if preserved:
        output += preserved
        if not preserved.endswith((b"\n", b"\r")):
            output += eol
    return (BOM if bom else b"") + output + b"---" + eol + body


def read_document(path: Path):
    """Return (data, header text or '' when missing, body, bom, error)."""
    data = path.read_bytes()
    try:
        header, body, bom, split_error = split_document(data)
    except UnicodeDecodeError as exc:
        return data, None, None, None, f"frontmatter is not UTF-8: {exc}"
    if split_error == "missing":
        return data, "", body, bom, None
    if split_error:
        return data, None, None, None, split_error
    return data, header, body, bom, None


def verify_outputs(planned):
    """Re-read every new header and require exactly the expected fields and values."""
    texts = []
    for item in planned:
        header, new_body, _, split_error = split_document(item["output"])
        if new_body != item["body"]:
            raise SystemExit(f"internal check failed, nothing written: body would change in {item['rel']}")
        texts.append("" if split_error == "missing" else header)
    errors = []
    for item, (result, error) in zip(planned, parse_headers(texts)):
        if error or result["value"] != item["expected"]:
            errors.append(f"{item['rel']}: the rewritten header would not match; edit it by hand")
    if errors:
        raise SystemExit("nothing written:\n" + "\n".join(errors))


def capture_write_state(path: Path, root: Path | None = None) -> dict:
    """Bind a planned write to the file and its current unlinked parent objects."""
    absolute = Path(os.path.abspath(path))
    if root is not None:
        allowed = Path(os.path.abspath(root))
        try:
            absolute.relative_to(allowed)
        except ValueError:
            raise OSError(f"write leaves the approved root: {path}") from None
        if Path(os.path.realpath(allowed)) != allowed or Path(os.path.realpath(absolute.parent)) != absolute.parent:
            raise OSError(f"write goes through a link: {path}")
        canonical = absolute
    else:
        canonical = absolute.parent.resolve() / absolute.name
    if path.is_symlink() or not path.is_file():
        raise OSError(f"write requires a regular unlinked file: {path}")
    parents = {}
    for parent in (canonical.parent, *canonical.parent.parents):
        info = os.lstat(parent)
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise OSError(f"write parent is not an unlinked directory: {parent}")
        parents[str(parent)] = [info.st_dev, info.st_ino]
    info = os.lstat(canonical)
    return {"path": str(canonical), "parents": parents, "identity": [info.st_dev, info.st_ino],
            "metadata": path_metadata(canonical)}


def guard_write_state(state: dict) -> Path:
    path = Path(state["path"])
    if Path(os.path.realpath(path.parent)) != path.parent:
        raise OSError(f"write parent changed or goes through a link: {path}")
    for raw, expected in state["parents"].items():
        info = os.lstat(raw)
        if not stat.S_ISDIR(info.st_mode) or [info.st_dev, info.st_ino] != expected:
            raise OSError(f"write parent changed: {raw}")
    return path


def open_current(parent_fd: int, name: str, state=None, expected=None):
    descriptor = os.open(name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=parent_fd)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise OSError(f"write target is not a regular file: {name}")
        if state is not None:
            if [info.st_dev, info.st_ino] != state["identity"] or metadata_snapshot(descriptor) != state["metadata"]:
                raise OSError(f"file or metadata changed during the run: {name}")
        with os.fdopen(os.dup(descriptor), "rb") as reader:
            data = reader.read()
        if expected is not None and data != expected:
            raise OSError(f"file changed before replacement: {name}")
        return descriptor, data
    except BaseException:
        os.close(descriptor)
        raise


def make_temporary(parent_fd: int, name: str):
    for _ in range(20):
        temp_name = f".{name}.{secrets.token_hex(8)}.tmp"
        try:
            return os.open(temp_name, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=parent_fd), temp_name
        except FileExistsError:
            continue
    raise OSError(f"could not create a unique temporary file for {name}")


def copy_metadata_fd(source_fd: int, destination_fd: int) -> None:
    if sys.platform == "darwin":
        libc = _METADATA_LIBC
        libc.fcopyfile.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
        if libc.fcopyfile(source_fd, destination_fd, None, 0x7) != 0:
            error = ctypes.get_errno()
            raise OSError(error, os.strerror(error))
    else:
        info = os.fstat(source_fd)
        os.fchmod(destination_fd, stat.S_IMODE(info.st_mode))
        os.utime(destination_fd, ns=(info.st_atime_ns, info.st_mtime_ns))
        if hasattr(os, "listxattr"):
            for name in os.listxattr(source_fd):
                os.setxattr(destination_fd, name, os.getxattr(source_fd, name))


def atomic_replace_many(pending):
    """Bind writes to checked directory descriptors; roll back only unchanged owned outputs.

    This is a best-effort batch, not an atomic multi-file transaction or a lock on editors.
    """
    prepared = []
    try:
        for item in pending:
            rel, raw_path, expected, output, *saved = item
            state = saved[0] if saved else capture_write_state(raw_path)
            path = guard_write_state(state)
            parent_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0))
            source_fd = None
            temp_name = None
            try:
                parent_info = os.fstat(parent_fd)
                if [parent_info.st_dev, parent_info.st_ino] != state["parents"][str(path.parent)]:
                    raise OSError(f"write parent changed: {path.parent}")
                source_fd, original = open_current(parent_fd, path.name, state)
                if original != expected:
                    raise SystemExit(f"file changed during the run, nothing written: {rel}")
                temp_fd, temp_name = make_temporary(parent_fd, path.name)
                try:
                    with os.fdopen(os.dup(temp_fd), "wb") as stream:
                        stream.write(output)
                        stream.flush()
                        os.fsync(stream.fileno())
                    copy_metadata_fd(source_fd, temp_fd)
                    os.fsync(temp_fd)
                    written_info = os.fstat(temp_fd)
                    written_state = {"identity": [written_info.st_dev, written_info.st_ino],
                                     "metadata": metadata_snapshot(temp_fd)}
                finally:
                    os.close(temp_fd)
                prepared.append({"rel": rel, "path": path, "state": state, "parent_fd": parent_fd,
                                 "source_fd": source_fd, "temp": temp_name, "original": original,
                                 "output": output, "written_state": written_state, "replaced": False})
                parent_fd = source_fd = None
            finally:
                if source_fd is not None:
                    os.close(source_fd)
                if parent_fd is not None:
                    if temp_name is not None:
                        os.unlink(temp_name, dir_fd=parent_fd)
                    os.close(parent_fd)
        try:
            for item in prepared:
                guard_write_state(item["state"])
                current_fd, _ = open_current(item["parent_fd"], item["path"].name, item["state"], item["original"])
                os.close(current_fd)
            for item in prepared:
                guard_write_state(item["state"])
                current_fd, _ = open_current(item["parent_fd"], item["path"].name, item["state"], item["original"])
                os.close(current_fd)
                os.replace(item["temp"], item["path"].name, src_dir_fd=item["parent_fd"], dst_dir_fd=item["parent_fd"])
                item["temp"] = None
                item["replaced"] = True
                os.fsync(item["parent_fd"])
        except BaseException:
            for item in reversed(prepared):
                if not item["replaced"]:
                    continue
                rollback_name = None
                try:
                    guard_write_state(item["state"])
                    current_fd, _ = open_current(item["parent_fd"], item["path"].name, item["written_state"], item["output"])
                    os.close(current_fd)
                    rollback_fd, rollback_name = make_temporary(item["parent_fd"], item["path"].name)
                    try:
                        with os.fdopen(os.dup(rollback_fd), "wb") as stream:
                            stream.write(item["original"])
                            stream.flush()
                            os.fsync(stream.fileno())
                        copy_metadata_fd(item["source_fd"], rollback_fd)
                        os.fsync(rollback_fd)
                    finally:
                        os.close(rollback_fd)
                    # An edit while the rollback file was prepared still belongs to the user.
                    current_fd, _ = open_current(item["parent_fd"], item["path"].name, item["written_state"], item["output"])
                    os.close(current_fd)
                    guard_write_state(item["state"])
                    os.replace(rollback_name, item["path"].name, src_dir_fd=item["parent_fd"], dst_dir_fd=item["parent_fd"])
                    rollback_name = None
                    os.fsync(item["parent_fd"])
                except OSError:
                    # A conflict or failed rollback must not stop recovery of other unchanged writes.
                    continue
                finally:
                    if rollback_name is not None:
                        os.unlink(rollback_name, dir_fd=item["parent_fd"])
            raise
    finally:
        for item in prepared:
            try:
                if item["temp"] is not None:
                    os.unlink(item["temp"], dir_fd=item["parent_fd"])
            finally:
                os.close(item["source_fd"])
                os.close(item["parent_fd"])


def inventory(concepts: dict):
    files = {}
    for rel, path in concepts.items():
        data = path.read_bytes()
        try:
            _, body, bom, split_error = split_document(data)
        except UnicodeDecodeError:
            body, bom, split_error = data, data.startswith(BOM), "not UTF-8"
        files[rel] = {
            "file_sha256": hashlib.sha256(data).hexdigest(),
            "body_sha256": hashlib.sha256(body).hexdigest(),
            "bom": bom,
            "line_endings": line_endings(body),
            "had_frontmatter": split_error is None,
        }
    return files


def load_inventory(path: Path):
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit(f"cannot read inventory: {exc}") from None
    files = raw.get("files") if isinstance(raw, dict) else None
    valid = (
        isinstance(files, dict)
        and raw.get("version") == INVENTORY_VERSION
        and all(isinstance(record, dict) and isinstance(record.get("file_sha256"), str) for record in files.values())
    )
    if not valid:
        raise SystemExit(f"unsupported inventory; recreate it with --inventory-out (format {INVENTORY_VERSION})")
    return {nfc(rel): record for rel, record in files.items()}


def load_manifest(path: Path):
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit(f"cannot read manifest: {exc}") from None
    if isinstance(raw, list):
        entries = {}
        for item in raw:
            if not isinstance(item, dict) or not isinstance(item.get("path"), str):
                raise SystemExit("each manifest list item needs a 'path'")
            if item["path"] in entries:
                raise SystemExit(f"manifest names the same document twice: {item['path']}")
            entries[item["path"]] = item
    elif isinstance(raw, dict):
        entries = raw.get("files", raw)
        if not isinstance(entries, dict):
            raise SystemExit("manifest 'files' must be an object keyed by path")
    else:
        raise SystemExit("manifest must be an object keyed by path or a list of objects with 'path'")
    manifest = {}
    for rel, meta in entries.items():
        if not isinstance(meta, dict):
            raise SystemExit(f"manifest entry must be an object: {rel}")
        proposed = {key: value for key, value in meta.items() if key not in PROPOSER_KEYS}
        extra = sorted(set(proposed) - set(FIELDS))
        if extra:
            raise SystemExit(f"manifest may set only {', '.join(FIELDS)}; {rel} also sets {', '.join(extra)}")
        for key, value in proposed.items():
            issue = field_issue(key, value)
            if issue:
                raise SystemExit(f"manifest {rel}: {issue}")
        manifest[rel] = proposed
    return manifest


def show(value):
    return json.dumps(value, ensure_ascii=False)


def read_targets(targets, concepts: dict, errors, root: Path | None = None):
    """Read and parse every target with one YAML process; skip unreadable ones into errors."""
    loaded = []
    for rel in targets:
        try:
            write_state = capture_write_state(concepts[rel], root)
            data, header, body, bom, error = read_document(concepts[rel])
        except OSError as error:
            errors.append(f"{rel}: {error}")
            continue
        if error:
            errors.append(f"{rel}: {error}")
        else:
            loaded.append({"rel": rel, "path": concepts[rel], "data": data, "header": header, "body": body, "bom": bom, "write_state": write_state})
    for item, (result, error) in zip(loaded, parse_headers([item["header"] for item in loaded])):
        item["result"], item["error"] = result, error
    return loaded


def apply_manifest(args, concepts: dict, root: Path):
    if not args.inventory:
        raise SystemExit("--inventory is required with --manifest")
    before = load_inventory(args.inventory)
    manifest = load_manifest(args.manifest)
    errors, notes, planned = [], [], []
    proposals = {}
    for raw_rel, proposed in manifest.items():
        rel = resolve_named(concepts, [raw_rel], root)[0]
        if rel in proposals:
            raise SystemExit(f"manifest names the same document twice: {rel}")
        proposals[rel] = proposed
    for item in read_targets(list(proposals), concepts, errors, root):
        rel = item["rel"]
        record = before.get(rel)
        if record is None:
            errors.append(f"{rel}: not in the inventory; recreate it")
            continue
        if hashlib.sha256(item["data"]).hexdigest() != record["file_sha256"]:
            errors.append(f"{rel}: changed since the inventory; recreate it")
            continue
        if item["error"]:
            errors.append(f"{rel}: existing frontmatter cannot be read ({item['error']}); fix it by hand first")
            continue
        header = item["header"].encode("utf-8")
        problem = rewrite_problem(header, item["result"])
        if problem:
            errors.append(f"{rel}: {problem}")
            continue
        existing = item["result"]["value"]
        final = {key: existing[key] for key in FIELDS if key in existing}
        for key, value in proposals[rel].items():
            old = existing.get(key)
            if key not in existing or old == value:
                final[key] = value
            elif field_issue(key, old) is not None or args.replace_existing:
                final[key] = value
                notes.append(f"replaced: {rel} {key}: {show(old)} -> {show(value)}")
            else:
                notes.append(f"kept existing: {rel} {key}: {show(old)}")
        issues = validate_fields(final)
        if issues:
            errors.append(f"{rel}: {'; '.join(issues)}")
            continue
        if header and all(existing.get(key) == final.get(key) for key in FIELDS):
            continue
        eol = preferred_eol(header, item["body"])
        serialized = [(key, final[key]) for key in FIELDS if key in final]
        preserved = kept_lines(header, item["result"]["top_keys"], set(FIELDS))
        expected = {key: value for key, value in existing.items() if key not in FIELDS}
        expected.update(final)
        output = build_document(item["bom"], item["body"], eol, serialized, preserved)
        planned.append({**item, "output": output, "expected": expected})
    if errors:
        raise SystemExit("nothing written:\n" + "\n".join(errors))
    verify_outputs(planned)
    finish(args, [(p["rel"], p["path"], p["data"], p["output"], p["write_state"]) for p in planned if p["output"] != p["data"]], notes)


def remove_fields(args, concepts: dict, root: Path):
    dropped = set(args.remove_fields)
    protected = dropped & set(REQUIRED)
    if protected:
        raise SystemExit(f"required fields cannot be removed: {', '.join(sorted(protected))}")
    targets = resolve_named(concepts, args.paths, root) if args.paths else list(concepts)
    errors, notes, planned = [], [], []
    for item in read_targets(targets, concepts, errors, root):
        rel = item["rel"]
        if item["error"]:
            errors.append(f"{rel}: {item['error']}")
            continue
        existing = item["result"]["value"]
        present = [key for key in existing if key in dropped]
        if not present:
            continue
        header = item["header"].encode("utf-8")
        problem = rewrite_problem(header, item["result"])
        if problem:
            errors.append(f"{rel}: {problem}")
            continue
        preserved = kept_lines(header, item["result"]["top_keys"], dropped)
        output = build_document(item["bom"], item["body"], preferred_eol(header, item["body"]), [], preserved)
        expected = {key: value for key, value in existing.items() if key not in dropped}
        planned.append({**item, "output": output, "expected": expected})
        notes.append(f"removed: {rel} ({', '.join(present)})")
    if errors:
        raise SystemExit("nothing written:\n" + "\n".join(errors))
    verify_outputs(planned)
    finish(args, [(p["rel"], p["path"], p["data"], p["output"], p["write_state"]) for p in planned if p["output"] != p["data"]], notes)


def finish(args, pending, notes):
    if not args.dry_run:
        try:
            atomic_replace_many(pending)
        except OSError as exc:
            raise SystemExit(f"write failed; unchanged writes were restored where safe; preserve and inspect any concurrent edits or partial changed files: {exc}") from None
    for note in notes:
        print(note)
    for rel, *_ in pending:
        print(("would change" if args.dry_run else "changed") + f": {rel}")
    print(f"files {'to change' if args.dry_run else 'changed'}: {len(pending)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--inventory-out", type=Path, help="write body hashes of documents in scope")
    action.add_argument("--manifest", type=Path, help="write type, title, description, tags from a JSON manifest")
    action.add_argument("--remove-fields", nargs="+", metavar="FIELD", help="remove these top-level fields")
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--paths", nargs="+", metavar="PATH", help="limit --remove-fields to these documents")
    parser.add_argument("--replace-existing", action="store_true", help="replace valid existing values")
    parser.add_argument("--exclude", nargs="*", default=[])
    parser.add_argument("--include-readme", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        raise SystemExit(f"not a directory: {root}")
    if args.paths and not args.remove_fields:
        raise SystemExit("--paths is only valid with --remove-fields")
    scope = load_scope(root, args.exclude, args.include_readme)
    concepts, _ = partition(markdown_files(scope))
    print(scope.describe())

    if args.inventory_out:
        try:
            args.inventory_out.write_text(
                json.dumps(
                    {"version": INVENTORY_VERSION, "root": str(root), "files": inventory(concepts)},
                    indent=2,
                    ensure_ascii=False,
                ) + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            raise SystemExit(f"cannot write inventory: {exc}") from None
        print(f"inventory: {args.inventory_out} ({len(concepts)} documents)")
    elif args.manifest:
        apply_manifest(args, concepts, root)
    else:
        remove_fields(args, concepts, root)


if __name__ == "__main__":
    sys.exit(main())
