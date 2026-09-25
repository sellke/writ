#!/usr/bin/env bash
# install.sh / update.sh do not ship commands/<stem>.lean.md while the
# default <stem>.md exists (Story 5 of 2026-09-24-flagged-harness-cuts, task
# 5.4). The lean siblings are the WRIT_HARNESS_LEAN=1 bodies; until a keep
# flips the default load path they reach a project only through
# `pipeline-baseline.py run --lean`. A `.lean.md` with no default is an
# ordinary command and still ships. update.sh also removes an unmodified lean
# sibling a previous install left behind.
#
# Runs the real scripts against temp targets. update.sh clones WRIT_REPO, so
# the source is a committed copy of this working tree. Does `git init`: run
# outside any sandbox.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
WORK=$(mktemp -d "${TMPDIR:-/tmp}/writ-lean-siblings-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

hash_file() {
  if command -v shasum &>/dev/null; then
    shasum -a 256 "$1" | cut -d' ' -f1
  else
    sha256sum "$1" | cut -d' ' -f1
  fi
}

# Committed source copy of the working tree, plus an orphan lean command.
SRC="$WORK/src"
mkdir -p "$SRC"
(cd "$REPO" && tar --exclude=.git --exclude=.cursor --exclude=.claude --exclude=.codex --exclude=.writ \
  --exclude=__pycache__ -cf - .) | (cd "$SRC" && tar -xf -)
mkdir -p "$SRC/.writ/docs"
cp "$REPO"/.writ/docs/*.md "$SRC/.writ/docs/"
printf '# /orphan\n' > "$SRC/commands/orphan.lean.md"
git -C "$SRC" init -q -b main
git -C "$SRC" -c user.name=t -c user.email=t@example.invalid add -A
git -C "$SRC" -c user.name=t -c user.email=t@example.invalid commit -q -m source

ls "$SRC"/commands/*.lean.md >/dev/null 2>&1 || fail "fixture: no lean siblings in source"
[ -f "$SRC/commands/implement-story.lean.md" ] || fail "fixture: implement-story.lean.md missing"

assert_no_lean_siblings() {
  local dir="$1" f base
  for f in "$dir"/*.lean.md; do
    [ -e "$f" ] || continue
    base=$(basename "$f")
    [ "$base" = "orphan.lean.md" ] && continue
    fail "$2: lean sibling installed: $f"
  done
}

# ----- install: dry run lists defaults, never a lean sibling -----
T1="$WORK/dry"
mkdir -p "$T1"
out=$(cd "$T1" && bash "$SRC/scripts/install.sh" --platform claude --dry-run --no-commit 2>&1) \
  || fail "install --dry-run exited non-zero: $out"
printf '%s' "$out" | grep -q 'commands/implement-story.md' || fail "dry run does not list implement-story.md"
if printf '%s' "$out" | grep -q 'implement-story.lean.md\|_preamble.lean.md'; then
  fail "dry run lists a lean sibling"
fi

# ----- install: defaults land, lean siblings do not, orphan does -----
T2="$WORK/proj"
mkdir -p "$T2"
out=$(cd "$T2" && bash "$SRC/scripts/install.sh" --platform claude --no-commit 2>&1) \
  || fail "install exited non-zero: $out"
for stem in implement-story _preamble create-spec implement-phase verify-spec; do
  [ -f "$T2/.claude/commands/$stem.md" ] || fail "install: default $stem.md missing"
  cmp -s "$T2/.claude/commands/$stem.md" "$SRC/commands/$stem.md" || fail "install: $stem.md is not the default body"
done
assert_no_lean_siblings "$T2/.claude/commands" install
[ -f "$T2/.claude/commands/orphan.lean.md" ] || fail "install: an orphan .lean.md (no default) must still ship"
if grep -q '\.lean\.md$' "$T2/.claude/.writ-manifest" && ! grep -q 'orphan.lean.md$' "$T2/.claude/.writ-manifest"; then
  fail "install: manifest records a lean sibling"
fi
printf '%s' "$out" | grep -q 'Commands:' || fail "install: no command count printed"
expected=0
for f in "$SRC"/commands/*.md; do
  b=$(basename "$f")
  if [ "${b%.lean.md}" != "$b" ] && [ -f "$SRC/commands/${b%.lean.md}.md" ]; then
    continue
  fi
  expected=$((expected + 1))
done
printf '%s' "$out" | grep -q "Commands:  $expected\$" || fail "install: command count is not $expected (lean siblings counted?)"

# ----- update: no lean sibling added; a left-behind unmodified one is removed -----
cp "$SRC/commands/implement-story.lean.md" "$T2/.claude/commands/implement-story.lean.md"
printf '%s  commands/implement-story.lean.md\n' "$(hash_file "$T2/.claude/commands/implement-story.lean.md")" \
  >> "$T2/.claude/.writ-manifest"
# a user-modified left-behind sibling is preserved, like any modified file
printf 'local edit\n' > "$T2/.claude/commands/verify-spec.lean.md"
printf '%s  commands/verify-spec.lean.md\n' "$(hash_file "$SRC/commands/verify-spec.lean.md")" \
  >> "$T2/.claude/.writ-manifest"

out=$(cd "$T2" && WRIT_REPO="$SRC" bash "$SRC/scripts/update.sh" --platform claude --dry-run --no-commit 2>&1) \
  || fail "update --dry-run exited non-zero: $out"
if printf '%s' "$out" | grep -q '✨ New:.*\.lean\.md\|Update:.*\.lean\.md'; then
  fail "update dry run would ship a lean sibling: $out"
fi

out=$(cd "$T2" && WRIT_REPO="$SRC" bash "$SRC/scripts/update.sh" --platform claude --no-commit 2>&1) \
  || fail "update exited non-zero: $out"
[ ! -e "$T2/.claude/commands/implement-story.lean.md" ] || fail "update: left-behind lean sibling not removed"
[ -f "$T2/.claude/commands/verify-spec.lean.md" ] || fail "update: user-modified lean sibling was removed"
rm -f "$T2/.claude/commands/verify-spec.lean.md"
assert_no_lean_siblings "$T2/.claude/commands" update
[ -f "$T2/.claude/commands/implement-story.md" ] || fail "update: default implement-story.md missing"
grep -q 'implement-story.lean.md$' "$T2/.claude/.writ-manifest" && fail "update: manifest still records the lean sibling"

echo "PASS test_install_update_lean_siblings"
