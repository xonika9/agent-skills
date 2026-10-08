# Bootstrapping a new project

The result is a local repository that passes `bun run verify` against a real database, with the reference `orders` module as the pattern for new modules and the rules block in `AGENTS.md`.

## Inputs

- Target directory: absent, or empty except `.git`. The script refuses anything else, so an existing project goes through the audit instead.
- Sign-in variant (A, B, C, or none yet) and whether server rendering is needed. Neither blocks the scaffold; ask only when the user has not said and the answer is needed for the step at hand.
- The current stable Bun version, discovered live (for example `gh api repos/oven-sh/bun/releases/latest --jq .tag_name`). The local `bun` should match it; the script warns when it does not.

`python3`, `bun`, and `git` are required; Docker is needed for the dev database and the container build.

## Scaffold

```bash
python3 <skill-directory>/scripts/bootstrap.py <target> --bun-version <x.y.z> [--name <package-name>]
```

The script copies `assets/project`, installs the newest release of every dependency that is older than `minimumReleaseAge` (a week), moves dependencies shared by several workspaces into the root catalog, generates the first migration and `routeTree.gen.ts`, formats, and creates `.env` from `.env.example`. Package installs reach the public npm registry; that is part of the bootstrap request. When a step fails, fix the cause and rerun the same command; a marker file lets the script continue in the partly built directory instead of refusing it.

Then start the dev database and verify:

```bash
bun run db:up
bun run verify          # first run writes apps/api/openapi.json
CI=true bun run verify  # proves the snapshot and generated files are stable
```

If installation or verification fails, fix the cause within the scaffold. When a library change breaks an asset, correct the asset in the project and report the difference so the skill's asset can be updated; do not pin an older version to hide it.

## Finish the project

- Check the GitHub Action major versions in `.github/workflows/` against their current releases; Dependabot keeps them current afterwards.
- Initialise shadcn/ui in `apps/web` with the current CLI and Base UI; its components go to `src/components/ui/`.
- Sign-in: replace `authenticate` in `apps/api/src/index.ts` with the chosen variant's token or session check (see [library notes](library-notes.md#sign-in)) and add the variant's services to `compose.yaml`.
- `AGENTS.md`, `CLAUDE.md`, and the README run path: create them with `x9-context-files-generator`, then write the rules block as described in [agents-block.md](agents-block.md). Without that skill, create `AGENTS.md` with a one-line project summary and the block, and report the context files as degraded.
- New modules copy `orders` on both server and client; delete `orders` once a real module exists, together with its error code, migration, and client messages.

## Done

`bun run verify` and `CI=true bun run verify` both exit 0 in the new project; `git status` shows the generated `bun.lock`, migration, `routeTree.gen.ts`, and `openapi.json` ready to commit and no `.env`; `AGENTS.md` contains the rules block; the report lists the Bun version, the sign-in variant or that it is pending, and anything not verified.
