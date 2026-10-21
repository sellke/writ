#!/usr/bin/env bash
# scripts/gen-claude-md.py is dev-only (Story 1 of
# 2026-10-20-claude-code-parity, AC-1.4). It reads .writ/manifest.yaml, which
# installed projects do not have, so the ship filter rejects it in all three
# lifecycle scripts and install never copies it.
#
# The install runs in a temp project against a committed temp copy of this
# working tree. Does `git init`: run outside any sandbox. Never point it at
# the Writ repo itself.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
WORK=$(mktemp -d "${TMPDIR:-/tmp}/writ-gen-claude-md-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT

NAME=gen-claude-md.py

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

filter_body() {
  sed -n '/^is_shippable_script() {/,/^}/p' "$1"
}

# ----- AC-1.4: the filter rejects the generator in all three scripts, one body -----
for s in install update unlink; do
  body=$(filter_body "$REPO/scripts/$s.sh")
  [ -n "$body" ] || fail "$s.sh: cannot load is_shippable_script"
  if bash -c "$body"$'\n''is_shippable_script "$1"' _ "$NAME"; then
    fail "$s.sh: is_shippable_script accepts $NAME"
  fi
  bash -c "$body"$'\n''is_shippable_script "$1"' _ spec-status.py \
    || fail "$s.sh: is_shippable_script rejects spec-status.py"
done
[ "$(filter_body "$REPO/scripts/install.sh")" = "$(filter_body "$REPO/scripts/update.sh")" ] \
  || fail "is_shippable_script differs between install.sh and update.sh"
[ "$(filter_body "$REPO/scripts/install.sh")" = "$(filter_body "$REPO/scripts/unlink.sh")" ] \
  || fail "is_shippable_script differs between install.sh and unlink.sh"

# ----- AC-1.4: the docs name it as dev-only -----
note=$(awk '/^## Classification$/{f=1} f && /^\*\*Not in the table\.\*\*/{print; exit}' \
  "$REPO/.writ/docs/agent-cli-contract.md")
[ -n "$note" ] || fail "agent-cli-contract.md: no note under the Classification table"
printf '%s' "$note" | grep -qF "\`$NAME\`" || fail "agent-cli-contract.md note does not name $NAME"
printf '%s' "$note" | grep -qF 'dev-only' || fail "agent-cli-contract.md note does not say dev-only"

step3=$(sed -n '/^\*\*Apply same logic to runtime scripts\*\*/,/^\*\*Apply same logic to Writ reference docs\*\*/p' \
  "$REPO/commands/update-writ.md")
[ -n "$step3" ] || fail "update-writ.md: runtime-scripts exclusion prose not found"
printf '%s' "$step3" | grep -qE "dev-only[^.]*\`$NAME\`" \
  || fail "update-writ.md Step 3 does not name $NAME as dev-only"

# ----- AC-1.4: a temp install copies no generator and records no manifest line -----
SRC="$WORK/src"
mkdir -p "$SRC"
(cd "$REPO" && tar --exclude=.git --exclude=.cursor --exclude=.claude --exclude=.codex --exclude=.writ \
  --exclude=__pycache__ -cf - .) | (cd "$SRC" && tar -xf -)
mkdir -p "$SRC/.writ/docs"
cp "$REPO"/.writ/docs/*.md "$SRC/.writ/docs/"
git -C "$SRC" init -q -b main
git -C "$SRC" -c user.name=t -c user.email=t@example.invalid add -A
git -C "$SRC" -c user.name=t -c user.email=t@example.invalid commit -q -m source
[ -f "$SRC/scripts/$NAME" ] || fail "fixture: source copy has no scripts/$NAME"

PROJ="$WORK/proj"
mkdir -p "$PROJ"
out=$(cd "$PROJ" && bash "$SRC/scripts/install.sh" --platform claude --no-commit 2>&1) \
  || fail "install exited non-zero: $out"
MANIFEST="$PROJ/.claude/.writ-manifest"
[ -f "$MANIFEST" ] || fail "install: no manifest at .claude/.writ-manifest"
[ -f "$PROJ/scripts/spec-status.py" ] || fail "install: spec-status.py missing, so the script copy did not run"
[ ! -e "$PROJ/scripts/$NAME" ] || fail "install copied scripts/$NAME"
if grep -qF "$NAME" "$MANIFEST"; then
  fail "install recorded $NAME in the manifest: $(grep -F "$NAME" "$MANIFEST")"
fi
if printf '%s' "$out" | grep -qF "$NAME"; then
  fail "install output names $NAME"
fi

echo "PASS test_gen_claude_md_not_shipped"
