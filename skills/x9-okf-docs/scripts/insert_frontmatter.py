#!/usr/bin/env python3
"""Inventory, write, and safely migrate OKF frontmatter without changing bodies."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from okf_rules import (
    BOM,
    ONBOARDING_FILES,
    RESERVED_FILES,
    concept_files,
    line_endings,
    split_document,
    strict_yaml,
    valid_actor,
    valid_datetime,
    validate_fields,
)
from okf_yaml import inspect_yaml

SEMANTIC_FIELDS = ("type", "title", "description", "resource", "tags")
CANONICAL_ORDER = (
    "type", "title", "description", "resource", "tags", "generated", "verified",
    "status", "stale_after", "sources", "usage_window", "runtime", "parameters",
    "computation", "executor", "attester", "timestamp",
)


def split_for_write(data: bytes):
    header, body, bom, error = split_document(data)
    if error == "missing":
        return b"", body, bom, False
    if error:
        raise ValueError(f"{error} existing frontmatter")
    return header.encode("utf-8"), body, bom, True


def preferred_eol(data: bytes, fallback: bytes = b""):
    counts = line_endings(data)
    if not any(counts.values()):
        return preferred_eol(fallback) if fallback else b"\n"
    dominant = max(counts, key=counts.get)
    return {"crlf": b"\r\n", "lf": b"\n", "cr": b"\r"}[dominant]


def parsed_header(header: bytes):
    if not header:
        return {}
    try:
        text = header.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"existing frontmatter is not UTF-8: {exc}") from None
    parsed, _, error = strict_yaml(text)
    if error:
        raise ValueError(error)
    return parsed


def valid_semantic_value(key: str, value, catalog: set[str] | None):
    if key in {"title", "description", "resource"}:
        return (
            isinstance(value, str)
            and bool(value.strip())
            and (key != "description" or "\n" not in value and "\r" not in value)
        )
    if key == "type":
        return isinstance(value, str) and bool(value.strip()) and (catalog is None or value in catalog)
    if key == "tags":
        return isinstance(value, list) and all(isinstance(tag, str) and tag.strip() for tag in value)
    return False


def valid_generated(value):
    return (
        isinstance(value, dict)
        and valid_actor(value.get("by"))
        and ("at" not in value or valid_datetime(value.get("at")))
    )


def merge_existing_meta(
    meta: dict,
    header: bytes,
    catalog: set[str] | None,
    replace_existing: bool,
    operation_timestamp: str,
    actor: str | None,
):
    merged = dict(meta)
    preserved = []
    if not header:
        return merged, preserved
    existing = parsed_header(header)
    for key in SEMANTIC_FIELDS:
        value = existing.get(key)
        if (
            key in merged
            and not replace_existing
            and valid_semantic_value(key, value, catalog)
            and merged[key] != value
        ):
            merged[key] = value
            preserved.append(key)
    meaning_changed = any(
        key in merged and existing.get(key) != merged[key]
        for key in SEMANTIC_FIELDS
    )
    existing_generated = existing.get("generated")
    if meaning_changed:
        if not actor:
            raise ValueError("meaning-changing metadata repair requires --actor")
        merged["generated"] = {"by": actor, "at": operation_timestamp}
    elif valid_generated(existing_generated):
        if merged.get("generated") != existing_generated:
            merged["generated"] = existing_generated
            preserved.append("generated")
    return merged, preserved


def raw_preserved_fields(header: bytes, replaced_keys: set[str], removed_keys: set[str]):
    if not header:
        return b""
    try:
        parsed, error = inspect_yaml(header.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise ValueError(f"existing frontmatter is not UTF-8: {exc}") from None
    if error:
        raise ValueError(error)
    lines = header.splitlines(keepends=True)
    starts = [(item["line"], item["key"]) for item in parsed["top_keys"]]
    kept = lines[: starts[0][0]] if starts else lines
    for position, (start, key) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        if key not in replaced_keys and key not in removed_keys:
            kept.extend(lines[start:end])
    return b"".join(kept)


def normalize_eol(data: bytes, eol: bytes):
    if not data:
        return data
    terminated = data.endswith((b"\n", b"\r"))
    output = eol.join(data.splitlines())
    return output + eol if terminated else output


def yaml_value(value):
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ": "))
    raise ValueError(f"unsupported metadata value: {value!r}")


def header_bytes(
    meta: dict,
    eol: bytes,
    existing_header: bytes = b"",
    removed_keys: set[str] | None = None,
):
    removed = removed_keys or set()
    ordered = [key for key in CANONICAL_ORDER if key in meta]
    ordered.extend(sorted(set(meta) - set(ordered)))
    lines = ["---", *[f"{key}: {yaml_value(meta[key])}" for key in ordered]]
    output = eol.join(line.encode("utf-8") for line in lines) + eol
    preserved = normalize_eol(
        raw_preserved_fields(existing_header, set(meta), removed),
        eol,
    )
    if preserved:
        output += preserved
        if not preserved.endswith((b"\n", b"\r")):
            output += eol
    return output + b"---" + eol


def source_timestamp(root: Path, path: Path, header: bytes):
    if header:
        text = header.decode("utf-8")
        existing, raw_scalars, error = strict_yaml(text)
        if error:
            raise ValueError(error)
        generated = existing.get("generated")
        if isinstance(generated, dict) and valid_datetime(generated.get("at")):
            return generated["at"], "generated.at", False
        timestamp = existing.get("timestamp")
        raw_timestamp = raw_scalars.get("timestamp")
        if valid_datetime(timestamp, raw_timestamp):
            return raw_timestamp if isinstance(raw_timestamp, str) else timestamp, "timestamp", False
    try:
        repo = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )
        repo_root = Path(repo.stdout.strip()).resolve() if repo.returncode == 0 else None
        rel = path.resolve().relative_to(repo_root).as_posix() if repo_root else None
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "log", "-1", "--format=%cI", "--", rel],
            capture_output=True,
            text=True,
            check=False,
        ) if repo_root and rel else None
        candidate = proc.stdout.strip() if proc else ""
        if proc and proc.returncode == 0 and valid_datetime(candidate):
            return candidate, "git", False
    except (FileNotFoundError, ValueError):
        pass
    return (
        datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds"),
        "filesystem_mtime",
        True,
    )


def inventory(
    root: Path,
    excludes: set[str],
    include_readme: bool = False,
    whole_bundle: bool = False,
):
    files = {}
    for path in concept_files(root, excludes, include_readme, whole_bundle):
        data = path.read_bytes()
        header, body, bom, had_header = split_for_write(data)
        suggested, freshness_source, freshness_degraded = source_timestamp(root, path, header)
        files[path.relative_to(root).as_posix()] = {
            "file_sha256": hashlib.sha256(data).hexdigest(),
            "body_sha256": hashlib.sha256(body).hexdigest(),
            "bom": bom,
            "line_endings": line_endings(body),
            "had_frontmatter": had_header,
            "suggested_generated_at": suggested,
            "suggested_timestamp": suggested,
            "freshness_source": freshness_source,
            "freshness_degraded": freshness_degraded,
        }
    return {"version": 4, "root": str(root), "files": files}


def load_inventory(path: Path):
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot read inventory: {exc}") from None
    if not isinstance(raw, dict) or raw.get("version") != 4 or not isinstance(raw.get("files"), dict):
        version = raw.get("version") if isinstance(raw, dict) else None
        raise SystemExit(f"unsupported inventory format {version!r}; recreate inventory with format v4")
    return raw["files"]


def mutation_path(root: Path, rel: str):
    relative = Path(rel)
    if relative.is_absolute() or ".." in relative.parts:
        raise SystemExit(f"mutation path escapes root: {rel}")
    lexical = root / relative
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise SystemExit(f"mutation path uses a symlink: {rel}")
    try:
        resolved = lexical.resolve(strict=True)
        resolved.relative_to(root)
    except (FileNotFoundError, ValueError):
        raise SystemExit(f"mutation path is missing or outside root: {rel}") from None
    if not resolved.is_file():
        raise SystemExit(f"mutation path is not a regular file: {rel}")
    return lexical


def atomic_replace_many(pending):
    """Prepare same-directory durable temp files, then replace as one best-effort transaction."""
    prepared = []
    originals = []
    try:
        for rel, path, expected, output in pending:
            current = path.read_bytes()
            if current != expected:
                raise SystemExit(f"stale content immediately before write: {rel}")
            mode = stat.S_IMODE(path.stat(follow_symlinks=False).st_mode)
            descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
            temp_path = Path(temp_name)
            try:
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(output)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.chmod(temp_path, mode)
            except BaseException:
                temp_path.unlink(missing_ok=True)
                raise
            prepared.append((rel, path, temp_path))
            originals.append((rel, path, current, mode))

        for rel, path, expected, _ in pending:
            if path.read_bytes() != expected:
                raise SystemExit(f"stale content immediately before replacement: {rel}")

        replaced = 0
        try:
            for _, path, temp_path in prepared:
                os.replace(temp_path, path)
                replaced += 1
                directory_fd = os.open(path.parent, os.O_RDONLY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
        except BaseException:
            for rel, path, original, mode in reversed(originals[:replaced]):
                descriptor, rollback_name = tempfile.mkstemp(prefix=f".{path.name}.rollback.", dir=path.parent)
                rollback = Path(rollback_name)
                try:
                    with os.fdopen(descriptor, "wb") as stream:
                        stream.write(original)
                        stream.flush()
                        os.fsync(stream.fileno())
                    os.chmod(rollback, mode)
                    os.replace(rollback, path)
                finally:
                    rollback.unlink(missing_ok=True)
            raise
    finally:
        for _, _, temp_path in prepared:
            temp_path.unlink(missing_ok=True)


def load_manifest(path: Path):
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return {
            item["path"]: {
                key: value for key, value in item.items()
                if key not in {"path", "confidence", "basis", "preserve"}
            }
            for item in raw
        }
    if isinstance(raw, dict) and "files" in raw:
        return raw["files"]
    if isinstance(raw, dict):
        return raw
    raise ValueError("manifest must be an object, a files object, or a list with path fields")


def validate_manifest_meta(
    meta: dict,
    target_version: str,
    profile: str,
    catalog: set[str] | None,
):
    if not isinstance(meta, dict):
        raise ValueError("manifest metadata must be an object")
    issues = validate_fields(meta, {}, target_version, profile, catalog)
    if issues:
        raise ValueError("; ".join(issues))


def preflight_inventory(
    data: bytes,
    before: dict,
    existing_header: bytes | None = None,
    body: bytes | None = None,
    bom: bool | None = None,
):
    if existing_header is None or body is None or bom is None:
        existing_header, body, bom, _ = split_for_write(data)
    if bom != before["bom"]:
        raise ValueError("BOM changed since inventory")
    if hashlib.sha256(body).hexdigest() != before["body_sha256"]:
        raise ValueError("body changed since inventory")
    if hashlib.sha256(data).hexdigest() != before["file_sha256"]:
        raise ValueError("frontmatter changed since inventory")
    return existing_header, body, bom


def apply_manifest(args, root: Path):
    if not args.inventory:
        raise SystemExit("--inventory is required when applying a manifest")
    before = load_inventory(args.inventory)
    manifest = load_manifest(args.manifest)
    if args.target_version == "0.2" and args.profile == "curated" and not args.actor:
        raise SystemExit("--actor is required for curated OKF v0.2 manifest application")
    allowed = {
        path.relative_to(root).as_posix()
        for path in concept_files(
            root,
            set(args.exclude),
            args.include_readme,
            args.whole_bundle,
        )
    }
    operation_timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    catalog = set(args.types.split(",")) if args.types else None
    pending = []
    preserved_by_file = {}
    for rel, proposed in manifest.items():
        if rel not in allowed:
            raise SystemExit(f"manifest path is outside concept scope: {rel}")
        if rel not in before:
            raise SystemExit(f"manifest path absent from inventory: {rel}")
        if "file_sha256" not in before[rel]:
            raise SystemExit(f"inventory lacks full-file hash; recreate it before applying: {rel}")
        path = mutation_path(root, rel)
        data = path.read_bytes()
        try:
            existing_header, body, bom = preflight_inventory(data, before[rel])
            meta = dict(proposed)
            if args.actor and "generated" not in meta and args.target_version == "0.2":
                meta["generated"] = {
                    "by": args.actor,
                    "at": before[rel]["suggested_generated_at"],
                }
            effective_meta, preserved = merge_existing_meta(
                meta,
                existing_header,
                catalog,
                args.replace_existing_metadata,
                operation_timestamp,
                args.actor,
            )
            validate_manifest_meta(
                effective_meta,
                args.target_version,
                args.profile,
                catalog,
            )
        except ValueError as exc:
            raise SystemExit(f"cannot prepare metadata for {rel}: {exc}") from None
        if preserved:
            preserved_by_file[rel] = preserved
        output = (
            (BOM if bom else b"")
            + header_bytes(effective_meta, preferred_eol(body, existing_header), existing_header)
            + body
        )
        if output != data:
            pending.append((rel, path, data, output))

    if not args.dry_run:
        atomic_replace_many(pending)
    for rel, _, _, _ in pending:
        print(("would update" if args.dry_run else "updated") + f": {rel}")
    for rel, keys in preserved_by_file.items():
        print(f"preserved existing metadata: {rel} ({', '.join(keys)})")
    print(f"files changed: {len(pending)}")


def migrate_v01(args, root: Path, excludes: set[str]):
    if args.apply and not args.actor:
        raise SystemExit("--actor is required with --apply for v0.1 migration")
    before = {}
    if args.apply:
        if not args.inventory:
            raise SystemExit("--inventory is required with --apply")
        before = load_inventory(args.inventory)

    pending = []
    counts = {"legacy": 0, "native": 0, "minimal": 0, "skipped": 0, "invalid": 0}
    for path in concept_files(root, excludes, args.include_readme, args.whole_bundle):
        rel = path.relative_to(root).as_posix()
        data = path.read_bytes()
        try:
            header, body, bom, split_error = split_document(data)
        except UnicodeDecodeError as exc:
            print(f"INVALID {rel}: {exc}")
            counts["invalid"] += 1
            continue
        if split_error == "missing":
            print(f"SKIP {rel}: no frontmatter")
            counts["skipped"] += 1
            continue
        if split_error:
            print(f"INVALID {rel}: {split_error}")
            counts["invalid"] += 1
            continue
        fields, raw_scalars, yaml_error = strict_yaml(header)
        if yaml_error:
            print(f"INVALID {rel}: {yaml_error}")
            counts["invalid"] += 1
            continue
        v01_issues = validate_fields(fields, raw_scalars, "0.1", "okf")
        v02_issues = validate_fields(fields, raw_scalars, "0.2", "okf")
        curated_issues = []
        if args.profile == "curated":
            curated_issues = validate_fields(
                fields,
                raw_scalars,
                "0.1",
                "curated",
            )
        issues = list(dict.fromkeys(v01_issues + v02_issues + curated_issues))
        if issues:
            print(f"INVALID {rel}: {'; '.join(issues)}")
            counts["invalid"] += 1
            continue
        if "generated" in fields:
            label = "dual-write" if "timestamp" in fields else "native-v0.2"
            print(f"KEEP {rel}: {label}")
            counts["native"] += 1
            continue
        timestamp = fields.get("timestamp")
        raw_timestamp = raw_scalars.get("timestamp")
        if "timestamp" not in fields:
            print(f"KEEP {rel}: compatible-minimal; no legacy timestamp to migrate")
            counts["minimal"] += 1
            continue
        if not valid_datetime(timestamp, raw_timestamp):
            print(f"INVALID {rel}: invalid legacy timestamp")
            counts["invalid"] += 1
            continue
        timestamp = raw_timestamp if isinstance(raw_timestamp, str) else timestamp

        counts["legacy"] += 1
        print(f"{'MIGRATE' if args.apply else 'WOULD MIGRATE'} {rel}: timestamp -> generated.at")
        if not args.apply:
            continue
        path = mutation_path(root, rel)
        if rel not in before:
            raise SystemExit(f"migration path absent from inventory: {rel}")
        try:
            existing_header, current_body, current_bom = preflight_inventory(
                data,
                before[rel],
                header.encode("utf-8"),
                body,
                bom,
            )
        except ValueError as exc:
            raise SystemExit(f"cannot migrate {rel}: {exc}") from None
        generated = {"by": args.actor, "at": timestamp}
        removed = {"timestamp"} if args.drop_legacy_timestamp else set()
        output = (
            (BOM if current_bom else b"")
            + header_bytes(
                {"generated": generated},
                preferred_eol(current_body, existing_header),
                existing_header,
                removed_keys=removed,
            )
            + current_body
        )
        if output != data:
            pending.append((rel, path, data, output))

    if counts["invalid"]:
        raise SystemExit(
            f"migration blocked: {counts['invalid']} invalid concept(s); no files changed"
        )
    if args.apply and counts["skipped"]:
        raise SystemExit(
            f"migration incomplete: {counts['skipped']} concept(s) have no frontmatter; "
            "no files changed"
        )
    if args.apply and not args.dry_run:
        atomic_replace_many(pending)
    for rel, _, _, _ in pending:
        print(f"{'would update' if args.dry_run else 'updated'}: {rel}")
    print(
        "migration summary: "
        f"legacy={counts['legacy']} native={counts['native']} "
        f"minimal={counts['minimal']} skipped={counts['skipped']} changed={len(pending)}"
    )


def touch_files(args, root: Path):
    if not args.actor:
        raise SystemExit("--actor is required with --touch")
    if args.target_version != "0.2":
        raise SystemExit("--touch always updates files to OKF v0.2")

    operation_timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    catalog = set(args.types.split(",")) if args.types else None
    pending = []
    results = []
    seen = set()

    for raw_rel in args.touch:
        rel = Path(raw_rel).as_posix()
        if rel in seen:
            continue
        seen.add(rel)
        name = Path(rel).name
        if name in RESERVED_FILES:
            raise SystemExit(f"--touch does not mutate reserved OKF files: {rel}")
        if name in ONBOARDING_FILES and name != "README.md":
            raise SystemExit(f"--touch does not mutate repository instruction files: {rel}")

        path = mutation_path(root, rel)
        data = path.read_bytes()
        try:
            header, body, bom, split_error = split_document(data)
        except UnicodeDecodeError as exc:
            raise SystemExit(f"cannot touch {rel}: {exc}") from None
        if split_error:
            raise SystemExit(
                f"cannot touch {rel}: {split_error} frontmatter; use --manifest for new documents"
            )
        fields, raw_scalars, yaml_error = strict_yaml(header)
        if yaml_error:
            raise SystemExit(f"cannot touch {rel}: {yaml_error}")

        source_profile = "0.2" if "generated" in fields else "0.1"
        issues = validate_fields(fields, raw_scalars, source_profile, args.profile, catalog)
        if issues:
            raise SystemExit(f"cannot touch {rel}: {'; '.join(issues)}")

        updates = {
            "generated": {
                "by": args.actor,
                "at": operation_timestamp,
            }
        }
        removed = set()
        if "timestamp" in fields:
            if args.drop_legacy_timestamp:
                removed.add("timestamp")
            else:
                updates["timestamp"] = operation_timestamp

        existing_header = header.encode("utf-8")
        output = (
            (BOM if bom else b"")
            + header_bytes(
                updates,
                preferred_eol(body, existing_header),
                existing_header,
                removed_keys=removed,
            )
            + body
        )
        output_header, _, _, output_error = split_document(output)
        if output_error:
            raise SystemExit(f"cannot touch {rel}: generated invalid frontmatter")
        output_fields, output_scalars, output_yaml_error = strict_yaml(output_header)
        if output_yaml_error:
            raise SystemExit(f"cannot touch {rel}: {output_yaml_error}")
        output_issues = validate_fields(
            output_fields,
            output_scalars,
            "0.2",
            args.profile,
            catalog,
        )
        if output_issues:
            raise SystemExit(f"cannot touch {rel}: {'; '.join(output_issues)}")

        result = (
            ("migrate", "migrated")
            if "generated" not in fields
            else ("refresh", "refreshed")
        )
        results.append((rel, result))
        if output != data:
            pending.append((rel, path, data, output))

    if not args.dry_run:
        atomic_replace_many(pending)
    changed = {rel for rel, _, _, _ in pending}
    for rel, (verb, completed) in results:
        action = f"would {verb}" if args.dry_run and rel in changed else completed
        print(f"{action}: {rel}")
    print(f"files changed: {len(pending)}")


def declare_version(args, root: Path):
    if not args.apply:
        raise SystemExit("--declare-version is read-only unless --apply is provided")
    if not args.whole_bundle:
        raise SystemExit("--declare-version requires --whole-bundle")
    if args.exclude:
        raise SystemExit("--declare-version rejects --exclude because it must validate the full bundle")
    validator = Path(__file__).with_name("validate_okf.py")
    command = [
        sys.executable,
        str(validator),
        str(root),
        "--profile",
        "okf",
        "--target-version",
        args.declare_version,
        "--whole-bundle",
        "--ignore-version-declaration",
    ]
    checked = subprocess.run(command, capture_output=True, text=True, check=False)
    if checked.returncode != 0:
        detail = checked.stdout.strip() or checked.stderr.strip()
        raise SystemExit(f"version declaration blocked by whole-bundle validation:\n{detail}")

    index = mutation_path(root, "index.md")
    data = index.read_bytes()
    header, body, bom, error = split_document(data)
    if error not in {None, "missing"}:
        raise SystemExit(f"cannot update root index.md: {error}")
    existing_header = b"" if error == "missing" else header.encode("utf-8")
    if existing_header:
        fields = parsed_header(existing_header)
        if set(fields) - {"okf_version"}:
            raise SystemExit("root index.md frontmatter contains fields other than okf_version")
    output = (
        (BOM if bom else b"")
        + header_bytes(
            {"okf_version": args.declare_version},
            preferred_eol(body, existing_header),
            existing_header,
        )
        + body
    )
    if output != data:
        if not args.dry_run:
            atomic_replace_many([("index.md", index, data, output)])
        print(
            f"{'would update' if args.dry_run else 'updated'}: "
            f"index.md (okf_version {args.declare_version})"
        )
    else:
        print(f"unchanged: index.md already declares OKF {args.declare_version}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--inventory-out", type=Path)
    action.add_argument("--manifest", type=Path)
    action.add_argument("--migrate-v01", action="store_true")
    action.add_argument("--touch", nargs="+", metavar="PATH")
    action.add_argument("--declare-version", choices=("0.1", "0.2"))
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--target-version", choices=("0.1", "0.2"), default="0.2")
    parser.add_argument("--profile", choices=("okf", "curated"), default="curated")
    parser.add_argument("--actor")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--drop-legacy-timestamp", action="store_true")
    parser.add_argument("--exclude", nargs="*", default=[])
    parser.add_argument("--include-readme", action="store_true")
    parser.add_argument("--whole-bundle", action="store_true")
    parser.add_argument("--types")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--replace-existing-metadata", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        raise SystemExit(f"not a directory: {root}")
    if args.actor and not valid_actor(args.actor):
        raise SystemExit("--actor must use producer/version, human:<id>, or process:<id>")
    if args.drop_legacy_timestamp and not (args.migrate_v01 or args.touch):
        raise SystemExit("--drop-legacy-timestamp is only valid with --migrate-v01 or --touch")
    if args.apply and not (args.migrate_v01 or args.declare_version):
        raise SystemExit("--apply is only valid with --migrate-v01 or --declare-version")
    excludes = set(args.exclude)

    if args.inventory_out:
        args.inventory_out.write_text(
            json.dumps(
                inventory(root, excludes, args.include_readme, args.whole_bundle),
                indent=2,
                ensure_ascii=False,
            ) + "\n",
            encoding="utf-8",
        )
        print(f"inventory: {args.inventory_out}")
        return
    if args.migrate_v01:
        migrate_v01(args, root, excludes)
        return
    if args.touch:
        touch_files(args, root)
        return
    if args.declare_version:
        declare_version(args, root)
        return
    apply_manifest(args, root)


if __name__ == "__main__":
    main()
