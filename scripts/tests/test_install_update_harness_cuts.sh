#!/usr/bin/env bash
# Upgrade path for Story 1 of 2026-10-20-harness-cuts: the lean command
# siblings (commands/*.lean.md) are deleted from the source, so install ships
# none, and update treats an old installed copy as stale because upstream no
# longer has it. An unmodified copy is removed; a locally modified copy is
# kept and warned about on every run.
#
# Runs the real scripts against temp targets. update.sh clones WRIT_REPO, so
# the source is a committed copy of this working tree. Does `git init`: run
# outside any sandbox. Never point it at the Writ repo itself.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
WORK=$(mktemp -d "${TMPDIR:-/tmp}/writ-harness-cuts-test.XXXXXX")
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

# One line per file under $1: "<sha256> <relative path>", sorted. Two equal
# digests mean nothing on disk changed.
tree_digest() {
  local dir="$1" f
  (cd "$dir" && find . -type f | LC_ALL=C sort | while IFS= read -r f; do
    printf '%s %s\n' "$(hash_file "$f")" "$f"
  done)
}

# Committed source copy of the working tree.
SRC="$WORK/src"
mkdir -p "$SRC"
(cd "$REPO" && tar --exclude=.git --exclude=.cursor --exclude=.claude --exclude=.codex --exclude=.writ \
  --exclude=__pycache__ -cf - .) | (cd "$SRC" && tar -xf -)
mkdir -p "$SRC/.writ/docs"
cp "$REPO"/.writ/docs/*.md "$SRC/.writ/docs/"
git -C "$SRC" init -q -b main
git -C "$SRC" -c user.name=t -c user.email=t@example.invalid add -A
git -C "$SRC" -c user.name=t -c user.email=t@example.invalid commit -q -m source

# The path under test is "upstream no longer has the file". If the source
# still carried a lean sibling, update would reach the stale branch some
# other way and this test would prove nothing about the deletion.
for f in "$SRC"/commands/*.lean.md; do
  [ -e "$f" ] && fail "source still ships $(basename "$f"); the lean siblings must be deleted"
done
[ -f "$SRC/commands/implement-story.md" ] || fail "fixture: source has no commands/implement-story.md"

# ----- AC-1.2: install --dry-run lists commands, never a .lean.md -----
T1="$WORK/dry"
mkdir -p "$T1"
out=$(cd "$T1" && bash "$SRC/scripts/install.sh" --platform claude --dry-run --no-commit 2>&1) \
  || fail "install --dry-run exited non-zero: $out"
printf '%s' "$out" | grep -q 'commands/implement-story.md' \
  || fail "install dry run does not list commands/implement-story.md: $out"
if printf '%s\n' "$out" | grep -q '\.lean\.md'; then
  fail "install dry run lists a .lean.md file: $(printf '%s\n' "$out" | grep '\.lean\.md')"
fi

# ----- AC-1.2: install copies and records no .lean.md, counts every command -----
T2="$WORK/proj"
mkdir -p "$T2"
out=$(cd "$T2" && bash "$SRC/scripts/install.sh" --platform claude --no-commit 2>&1) \
  || fail "install exited non-zero: $out"
CMDS="$T2/.claude/commands"
MANIFEST="$T2/.claude/.writ-manifest"
[ -f "$CMDS/implement-story.md" ] || fail "install: commands/implement-story.md missing"
[ -f "$MANIFEST" ] || fail "install: no manifest at .claude/.writ-manifest"
for f in "$CMDS"/*.lean.md; do
  [ -e "$f" ] && fail "install copied $(basename "$f") into .claude/commands/"
done
if grep -q '\.lean\.md$' "$MANIFEST"; then
  fail "install recorded a .lean.md in the manifest: $(grep '\.lean\.md$' "$MANIFEST")"
fi
expected=0
for f in "$SRC"/commands/*.md; do
  [ -f "$f" ] && expected=$((expected + 1))
done
printf '%s' "$out" | grep -q "Commands:  $expected\$" \
  || fail "install: command count is not $expected (every commands/*.md): $(printf '%s\n' "$out" | grep 'Commands:')"

# ----- Plant an old install: two unmodified lean copies and one edited copy -----
# Each gets a manifest line, since update only removes what the manifest
# records. The source no longer has the real files, so any content works.
plant() {
  local name="$1"
  printf '# old %s from an earlier install\n' "$name" > "$CMDS/$name"
  printf '%s  commands/%s\n' "$(hash_file "$CMDS/$name")" "$name" >> "$MANIFEST"
}
plant implement-story.lean.md
plant _preamble.lean.md
plant verify-spec.lean.md
VERIFY_BASELINE=$(hash_file "$CMDS/verify-spec.lean.md")
printf 'local edit\n' >> "$CMDS/verify-spec.lean.md"
VERIFY_MODIFIED=$(hash_file "$CMDS/verify-spec.lean.md")

KEPT_WARNING='⚠️  Stale (no longer shipped, locally modified — kept): commands/verify-spec.lean.md'

# ----- AC-1.3: update --dry-run lists both unmodified copies as stale, changes nothing -----
before=$(tree_digest "$T2")
out=$(cd "$T2" && WRIT_REPO="$SRC" bash "$SRC/scripts/update.sh" --platform claude --dry-run --no-commit 2>&1) \
  || fail "update --dry-run exited non-zero: $out"
printf '%s' "$out" | grep -qF 'Stale files (removed upstream, would be deleted):' \
  || fail "update dry run prints no stale-file list: $out"
for name in implement-story.lean.md _preamble.lean.md; do
  printf '%s' "$out" | grep -qF "🗑  commands/$name" \
    || fail "update dry run does not list commands/$name as stale: $out"
done
if printf '%s' "$out" | grep -qF '🗑  commands/verify-spec.lean.md'; then
  fail "update dry run lists the modified verify-spec.lean.md for deletion: $out"
fi
# AC-1.4: the dry run already warns about the modified copy.
printf '%s' "$out" | grep -qF "$KEPT_WARNING" \
  || fail "update dry run does not warn on the modified verify-spec.lean.md: $out"
[ "$(tree_digest "$T2")" = "$before" ] || fail "update --dry-run changed files on disk"

# ----- AC-1.3 / AC-1.4: update removes the unmodified copies, keeps the edited one -----
out=$(cd "$T2" && WRIT_REPO="$SRC" bash "$SRC/scripts/update.sh" --platform claude --no-commit 2>&1) \
  || fail "update exited non-zero: $out"
for name in implement-story.lean.md _preamble.lean.md; do
  [ ! -e "$CMDS/$name" ] || fail "update: unmodified commands/$name not removed"
  printf '%s' "$out" | grep -qF "🗑  Removed: commands/$name" \
    || fail "update: removal of commands/$name not reported: $out"
  if grep -qF "commands/$name" "$MANIFEST"; then
    fail "update: manifest still records the removed commands/$name"
  fi
done
[ -f "$CMDS/verify-spec.lean.md" ] || fail "update: locally modified verify-spec.lean.md was removed"
[ "$(hash_file "$CMDS/verify-spec.lean.md")" = "$VERIFY_MODIFIED" ] \
  || fail "update: locally modified verify-spec.lean.md was changed"
printf '%s' "$out" | grep -qF "$KEPT_WARNING" \
  || fail "update: no stale warning names the modified verify-spec.lean.md: $out"
grep -q "^$VERIFY_BASELINE  commands/verify-spec.lean.md\$" "$MANIFEST" \
  || fail "update: manifest dropped the original baseline of the kept verify-spec.lean.md"
[ -f "$CMDS/implement-story.md" ] || fail "update: default commands/implement-story.md missing"

# ----- AC-1.4: a second update still warns and leaves the edited copy alone -----
out=$(cd "$T2" && WRIT_REPO="$SRC" bash "$SRC/scripts/update.sh" --platform claude --no-commit 2>&1) \
  || fail "second update exited non-zero: $out"
printf '%s' "$out" | grep -qF "$KEPT_WARNING" \
  || fail "second update no longer warns on the kept verify-spec.lean.md: $out"
[ "$(hash_file "$CMDS/verify-spec.lean.md")" = "$VERIFY_MODIFIED" ] \
  || fail "second update changed the kept verify-spec.lean.md"
for name in implement-story.lean.md _preamble.lean.md; do
  [ ! -e "$CMDS/$name" ] || fail "second update: commands/$name reappeared"
done

echo "PASS test_install_update_harness_cuts"
