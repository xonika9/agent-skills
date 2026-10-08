#!/usr/bin/env python3
"""Create a new project from the x9-web-stack template.

Copies assets/project into an empty target directory, substitutes the Bun
version and project name, installs the newest release of every dependency that
is older than minimumReleaseAge, moves dependencies shared by several
workspaces into the root catalog, and generates the files the first verify run
needs. If a step fails, fix the cause and rerun the same command: the marker
file lets it continue in the partly built directory.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets" / "project"

# Every asset file. The script refuses to run when assets/project differs from
# this list, so a stray file never reaches a new project.
FILES = (
    "Caddyfile",
    "_dockerignore",
    "_env.example",
    "_github/dependabot.yml",
    "_github/workflows/audit.yml",
    "_github/workflows/ci.yml",
    "_gitignore",
    "apps/api/Dockerfile",
    "apps/api/drizzle.config.ts",
    "apps/api/package.json",
    "apps/api/src/app.ts",
    "apps/api/src/contract.ts",
    "apps/api/src/db/client.ts",
    "apps/api/src/db/migrate.ts",
    "apps/api/src/db/schema.ts",
    "apps/api/src/env.ts",
    "apps/api/src/index.ts",
    "apps/api/src/modules/orders/index.ts",
    "apps/api/src/modules/orders/orders.test.ts",
    "apps/api/src/modules/orders/queries.ts",
    "apps/api/src/modules/orders/routes.ts",
    "apps/api/src/modules/orders/schema.ts",
    "apps/api/src/modules/orders/schemas.ts",
    "apps/api/src/modules/orders/service.ts",
    "apps/api/src/modules/orders/testing.ts",
    "apps/api/src/shared/columns.ts",
    "apps/api/src/shared/ctx.ts",
    "apps/api/src/shared/errors.ts",
    "apps/api/src/shared/log.ts",
    "apps/api/src/shared/pagination.ts",
    "apps/api/src/shared/problem-schema.ts",
    "apps/api/test/app.ts",
    "apps/api/test/global-setup.ts",
    "apps/api/test/openapi.test.ts",
    "apps/api/tsconfig.json",
    "apps/api/vitest.config.ts",
    "apps/web/Dockerfile",
    "apps/web/index.html",
    "apps/web/package.json",
    "apps/web/src/api/client.ts",
    "apps/web/src/api/messages.ts",
    "apps/web/src/main.tsx",
    "apps/web/src/modules/orders/components/order-list.tsx",
    "apps/web/src/modules/orders/forms/new-order-form.test.tsx",
    "apps/web/src/modules/orders/forms/new-order-form.tsx",
    "apps/web/src/modules/orders/index.ts",
    "apps/web/src/modules/orders/queries.ts",
    "apps/web/src/routes/__root.tsx",
    "apps/web/src/routes/index.tsx",
    "apps/web/src/routes/orders/index.tsx",
    "apps/web/src/styles.css",
    "apps/web/src/test-setup.ts",
    "apps/web/tsconfig.json",
    "apps/web/vite.config.ts",
    "biome.json",
    "bunfig.toml",
    "compose.dev.yaml",
    "compose.yaml",
    "package.json",
    "scripts/dev-db-init.sql",
    "tsconfig.base.json",
)

# Stored without a leading dot so packaging tools never drop them.
RENAMES = {"_gitignore": ".gitignore", "_dockerignore": ".dockerignore", "_env.example": ".env.example", "_github": ".github"}

DEPENDENCIES = {
    ".": {"dev": ["@biomejs/biome"]},
    "apps/api": {
        "prod": ["hono", "@hono/zod-openapi", "zod", "drizzle-orm", "postgres"],
        "dev": ["drizzle-kit", "vitest", "typescript", "@types/bun", "@types/node"],
    },
    "apps/web": {
        "prod": [
            "react",
            "react-dom",
            "@tanstack/react-router",
            "@tanstack/react-query",
            "@tanstack/react-form",
            "zod",
            "hono",
            "api@workspace:*",
        ],
        "dev": [
            "vite",
            "@vitejs/plugin-react",
            "@tanstack/router-plugin",
            "@rolldown/plugin-babel",
            "babel-plugin-react-compiler",
            "@babel/core",
            "tailwindcss",
            "@tailwindcss/vite",
            "typescript",
            "@types/react",
            "@types/react-dom",
            "vitest",
            "jsdom",
            "@testing-library/react",
            "@testing-library/jest-dom",
        ],
    },
}

MARKER = ".x9-web-stack-bootstrap"
OS_JUNK = {".DS_Store", "Thumbs.db"}

TEXT_SUFFIXES = {".json", ".ts", ".tsx", ".toml", ".yaml", ".yml", ".md", ".css", ".html", ".sql", ""}


def run(cmd: list[str], cwd: Path) -> None:
    print("$", " ".join(cmd), f"  (in {cwd})", flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def check_assets() -> None:
    present = {
        p.relative_to(ASSETS).as_posix() for p in ASSETS.rglob("*") if p.is_file() and p.name not in OS_JUNK
    }
    expected = set(FILES)
    if present != expected:
        raise SystemExit(
            f"assets/project does not match FILES: missing {sorted(expected - present)}, "
            f"unexpected {sorted(present - expected)}"
        )


def copy_assets(target: Path, name: str, bun_version: str) -> None:
    for rel in FILES:
        source = ASSETS / rel
        parts = [RENAMES.get(part, part) for part in source.relative_to(ASSETS).parts]
        dest = target.joinpath(*parts)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix in TEXT_SUFFIXES or source.name == "Dockerfile":
            text = source.read_text(encoding="utf-8")
            text = text.replace("__BUN_VERSION__", bun_version).replace("__APP_NAME__", name)
            dest.write_text(text, encoding="utf-8")
        else:
            shutil.copy2(source, dest)


def move_shared_to_catalog(target: Path) -> list[str]:
    root_path = target / "package.json"
    root = json.loads(root_path.read_text())
    manifests = {p: json.loads((target / p / "package.json").read_text()) for p in ("apps/api", "apps/web")}

    def deps(manifest: dict) -> dict[str, str]:
        return {**manifest.get("dependencies", {}), **manifest.get("devDependencies", {})}

    names = [set(deps(m)) for m in manifests.values()]
    shared = sorted(set.intersection(*names))
    shared = [n for n in shared if not deps(manifests["apps/api"])[n].startswith("workspace:")]
    first = deps(manifests["apps/api"])
    root["workspaces"]["catalog"] = {n: first[n] for n in shared}
    root_path.write_text(json.dumps(root, indent=2) + "\n")
    for path, manifest in manifests.items():
        for section in ("dependencies", "devDependencies"):
            for n in manifest.get(section, {}):
                if n in shared:
                    manifest[section][n] = "catalog:"
        (target / path / "package.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return shared


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path, help="new project directory; must be absent or empty except .git")
    parser.add_argument("--bun-version", required=True, help="current stable Bun release, e.g. 1.4.2")
    parser.add_argument("--name", help="package name of the root workspace (default: directory name)")
    args = parser.parse_args()

    if not re.fullmatch(r"\d+\.\d+\.\d+", args.bun_version):
        parser.error("--bun-version must look like 1.4.2")
    target = args.target.resolve()
    if target.exists() and not target.is_dir():
        parser.error(f"{target} is not a directory")
    resuming = (target / MARKER).exists()
    if target.exists() and not resuming and any(p.name not in {".git", *OS_JUNK} for p in target.iterdir()):
        parser.error(f"{target} is not empty; refusing to overwrite")
    name = args.name or re.sub(r"[^a-z0-9-]+", "-", target.name.lower()).strip("-") or "app"
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", name):
        parser.error("--name must be a lowercase npm package name")

    bun, git = shutil.which("bun"), shutil.which("git")
    if not bun or not git:
        print("bun and git must be on PATH", file=sys.stderr)
        return 2
    local = subprocess.run([bun, "--version"], capture_output=True, text=True).stdout.strip()
    if local != args.bun_version:
        print(f"warning: local bun is {local}, project pins {args.bun_version}", file=sys.stderr)

    check_assets()
    if resuming:
        print(f"continuing the bootstrap in {target}")
    else:
        target.mkdir(parents=True, exist_ok=True)
        (target / MARKER).write_text("bootstrap in progress; rerun bootstrap.py to continue\n")
        copy_assets(target, name, args.bun_version)
        inside = subprocess.run([git, "rev-parse", "--show-toplevel"], cwd=target, capture_output=True, text=True)
        if inside.returncode == 0 and Path(inside.stdout.strip()).resolve() != target:
            print(f"warning: {target} is inside the repository {inside.stdout.strip()}", file=sys.stderr)
        if not (target / ".git").exists():
            run([git, "init", "-q"], target)

    for workspace, groups in DEPENDENCIES.items():
        cwd = target / workspace
        if groups.get("prod"):
            run([bun, "add", *groups["prod"]], cwd)
        if groups.get("dev"):
            run([bun, "add", "-d", *groups["dev"]], cwd)
    shared = move_shared_to_catalog(target)
    print("catalog:", ", ".join(shared))
    run([bun, "install"], target)

    run([bun, "run", "db:generate", "--name", "init"], target / "apps/api")
    # Also generates src/routeTree.gen.ts, which typecheck needs.
    run([bun, "run", "build"], target / "apps/web")
    run([str(target / "node_modules/.bin/biome"), "check", "--write", "."], target)

    if not (target / ".env").exists():
        shutil.copy2(target / ".env.example", target / ".env")
    (target / MARKER).unlink()
    print(f"\nCreated {target}. Next: start the dev database and run `bun run verify`.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.CalledProcessError as error:
        print(f"\nstep failed: {' '.join(error.cmd)}\nFix the cause and rerun the same command to continue.", file=sys.stderr)
        sys.exit(1)
