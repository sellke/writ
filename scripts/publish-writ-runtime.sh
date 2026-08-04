#!/usr/bin/env bash
# Publishes @sellke/writ with a dedicated package README instead of this
# repo's full product README.md — npm always bundles whatever file is
# literally named README.md at the package root (package.json, README,
# and LICENSE are always included regardless of the `files` array), and
# package.json lives at the repo root, so the only way to ship a
# dedicated description is to swap it in for the publish step only.
#
# Usage:
#   scripts/publish-writ-runtime.sh --dry-run   # swap, npm pack, restore — no registry call
#   scripts/publish-writ-runtime.sh             # swap, npm publish --access public, restore
#
# Safe by construction: the swap is restored via `git checkout -- README.md`
# in a trap, so the repo's real README.md is never left modified — even if
# `npm publish`/`npm pack` fails or the script is interrupted.

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

PKG_NAME=$(node -p "require('./package.json').name" 2>/dev/null || echo "")
if [ "$PKG_NAME" != "@sellke/writ" ]; then
  echo "error: package.json#name is '${PKG_NAME}', expected '@sellke/writ'. Refusing to publish." >&2
  exit 1
fi

if [ -n "$(git status --porcelain README.md package.json 2>/dev/null)" ]; then
  echo "error: README.md or package.json has uncommitted changes. Commit or stash first." >&2
  exit 1
fi

DRY_RUN=0
if [ "${1:-}" = "--dry-run" ]; then
  DRY_RUN=1
fi

restore() {
  git checkout -- README.md
}
trap restore EXIT

cp scripts/writ-runtime-readme.md README.md

if [ "$DRY_RUN" -eq 1 ]; then
  echo "--- npm pack --dry-run (dedicated README swapped in) ---"
  npm pack --dry-run
  echo "--- README.md that would be published ---"
  head -5 README.md
  echo "..."
else
  npm publish --access public
fi

# `restore` runs automatically via the EXIT trap.
