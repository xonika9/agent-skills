#!/usr/bin/env python3
"""Inventory Markdown, write x9 OKF metadata, or remove retired fields without changing bodies."""

from __future__ import annotations

import argparse
import ctypes
import errno
import hashlib
import json
import os
import shutil
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


def copy_metadata(source: Path, destination: Path) -> None:
    """Carry mode, Finder created and modified dates, extended attributes such as Finder tags, and macOS ACLs."""
    shutil.copymode(source, destination)
    if sys.platform == "darwin":
        libc = ctypes.CDLL(None, use_errno=True)
        libc.copyfile.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_uint32]
        # copyfile(3) COPYFILE_ACL | COPYFILE_STAT | COPYFILE_XATTR; STAT keeps the dates.
        if libc.copyfile(os.fsencode(source), os.fsencode(destination), None, 0x1 | 0x2 | 0x4) != 0:
            error = ctypes.get_errno()
            raise OSError(error, os.strerror(error), str(destination))
    elif hasattr(os, "listxattr"):
        # Like shutil.copystat: skip attributes the file system or policy does not allow.
        skip = (errno.EPERM, errno.ENOTSUP, errno.ENODATA, errno.EINVAL)
        try:
            names = os.listxattr(source)
        except OSError as error:
            if error.errno not in skip:
                raise
            names = []
        for name in names:
            try:
                os.setxattr(destination, name, os.getxattr(source, name))
            except OSError as error:
                if error.errno not in skip:
                    raise
    if sys.platform != "darwin":
        info = os.stat(source)
        os.utime(destination, ns=(info.st_atime_ns, info.st_mtime_ns))


def unlinked_parent(path: Path) -> None:
    if os.path.realpath(path.parent) != str(path.parent):
        raise OSError(f"write parent changed or goes through a link: {path}")


def write_temporary(path: Path, data: bytes) -> Path:
    """Write data durably next to path and give it path's current metadata."""
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        copy_metadata(path, temp)
    except BaseException:
        temp.unlink(missing_ok=True)
        raise
    return temp


def fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_replace_many(pending):
    """Recheck each file just before replacing it; on failure roll back only files still holding our output.

    This is a best-effort batch, not an atomic multi-file transaction or a lock on editors.
    """
    prepared, replaced = [], []
    try:
        for rel, path, expected, output in pending:
            unlinked_parent(path)
            if path.read_bytes() != expected:
                raise SystemExit(f"file changed during the run, nothing written: {rel}")
            prepared.append((rel, path, expected, output, write_temporary(path, output)))
        try:
            for rel, path, expected, output, temp in prepared:
                unlinked_parent(path)
                if path.read_bytes() != expected:
                    raise OSError(f"file changed before replacement: {rel}")
                os.replace(temp, path)
                replaced.append((rel, path, expected, output))
                fsync_directory(path.parent)
        except BaseException as error:
            kept = []
            for rel, path, expected, output in reversed(replaced):
                try:
                    unlinked_parent(path)
                    # A later edit belongs to the user; only our own output is rolled back.
                    if path.read_bytes() != output:
                        kept.append(rel)
                        continue
                    os.replace(write_temporary(path, expected), path)
                    fsync_directory(path.parent)
                except OSError:
                    kept.append(rel)
            if kept:
                raise OSError(f"{error}; not restored, check by hand: {', '.join(reversed(kept))}") from error
            raise
    finally:
        for *_, temp in prepared:
            temp.unlink(missing_ok=True)


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


def read_targets(targets, concepts: dict, errors):
    """Read and parse every target with one YAML process; skip unreadable ones into errors."""
    loaded = []
    for rel in targets:
        data, header, body, bom, error = read_document(concepts[rel])
        if error:
            errors.append(f"{rel}: {error}")
        else:
            loaded.append({"rel": rel, "path": concepts[rel], "data": data, "header": header, "body": body, "bom": bom})
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
    for item in read_targets(list(proposals), concepts, errors):
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
    finish(args, [(p["rel"], p["path"], p["data"], p["output"]) for p in planned if p["output"] != p["data"]], notes)


def remove_fields(args, concepts: dict, root: Path):
    dropped = set(args.remove_fields)
    protected = dropped & set(REQUIRED)
    if protected:
        raise SystemExit(f"required fields cannot be removed: {', '.join(sorted(protected))}")
    targets = resolve_named(concepts, args.paths, root) if args.paths else list(concepts)
    errors, notes, planned = [], [], []
    for item in read_targets(targets, concepts, errors):
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
    finish(args, [(p["rel"], p["path"], p["data"], p["output"]) for p in planned if p["output"] != p["data"]], notes)


def finish(args, pending, notes):
    if not args.dry_run:
        try:
            atomic_replace_many(pending)
        except OSError as exc:
            raise SystemExit(f"write failed; files still holding only this run's output were restored: {exc}") from None
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
