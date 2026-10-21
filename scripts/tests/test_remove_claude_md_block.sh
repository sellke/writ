#!/usr/bin/env bash
# Tests remove_claude_md_block() bundled from scripts/uninstall.sh, Story 4 of
# 2026-10-20-claude-code-parity.
#
# AC-4.1: with user content on both sides of the Writ block (CRLF lines,
#         trailing spaces, non-ASCII, blank lines next to both markers, no
#         final newline), the file keeps every byte outside the start-marker
#         line through the end-marker line. No blank-line trimming, no
#         final-newline change, same file mode.
# AC-4.2: a block-only file is deleted; a file with no markers is untouched;
#         malformed markers return 13 with a ❌ line on stderr and leave the
#         file untouched; no file gives a note and creates nothing.
#
# Loads only the writ-remove-claude-md-bundled region, so the region must
# carry its own marker-count helper.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
UNINSTALL_SRC="$REPO/scripts/uninstall.sh"
BUNDLE_MARKER_BEGIN='# <<< writ-remove-claude-md-bundled-begin (used by scripts/tests/test_remove_claude_md_block.sh — keep synced) >>>'
BUNDLE_MARKER_END='# <<< writ-remove-claude-md-bundled-end >>>'

ROOT=$(mktemp -d "${TMPDIR:-/tmp}/writ-remove-claude-md-test.XXXXXX")
trap 'rm -rf "$ROOT"' EXIT

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

assert_file_eq() {
  local expected="$1" actual="$2" label="$3"
  [ -f "$actual" ] || fail "$label: $actual does not exist"
  cmp -s "$expected" "$actual" || {
    printf 'Expected bytes:\n' >&2
    od -c "$expected" | sed 's/^/  /' >&2
    printf 'Actual bytes:\n' >&2
    od -c "$actual" | sed 's/^/  /' >&2
    fail "$label: files differ"
  }
}

assert_note() {
  local expected="$1" label="$2"
  [ "${REMOVE_CLAUDE_MD_NOTE:-}" = "$expected" ] \
    || fail "$label: note is '${REMOVE_CLAUDE_MD_NOTE:-}', expected '$expected'"
}

assert_rc() {
  local expected="$1" actual="$2" label="$3"
  [ "$actual" = "$expected" ] || fail "$label: returned $actual, expected $expected"
}

# Full st_mode in octal, the same on macOS and Linux.
mode_of() {
  python3 -c 'import os, sys; print(oct(os.stat(sys.argv[1]).st_mode))' "$1"
}

load_remove_bundle() {
  grep -qF "$BUNDLE_MARKER_BEGIN" "$UNINSTALL_SRC" \
    || fail "uninstall.sh has no writ-remove-claude-md-bundled region"
  grep -qF "$BUNDLE_MARKER_END" "$UNINSTALL_SRC" \
    || fail "uninstall.sh has no writ-remove-claude-md-bundled end marker"
  local chunk
  chunk=$(awk -v s="$BUNDLE_MARKER_BEGIN" -v e="$BUNDLE_MARKER_END" '
    index($0,s) { p=1; next }
    index($0,e) { exit }
    p
  ' "$UNINSTALL_SRC") || fail "could not extract the remove bundle from uninstall.sh"
  [ -n "$chunk" ] || fail "the writ-remove-claude-md-bundled region is empty"
  eval "$chunk"
  declare -F remove_claude_md_block >/dev/null \
    || fail "the bundled region does not define remove_claude_md_block"
}

# Each case runs in a fresh directory with its own temp directory, so a
# leaked temp file shows up. macOS mktemp ignores TMPDIR, so the bundle's
# bare `mktemp` is pointed there by a shell function.
CASE_N=0
new_case() {
  CASE_N=$((CASE_N + 1))
  CASE="$ROOT/case-$CASE_N"
  mkdir -p "$CASE/tmp"
  cd "$CASE"
  unset REMOVE_CLAUDE_MD_NOTE
}

mktemp() {
  command mktemp "$CASE/tmp/tmp.XXXXXX"
}

# run_remove: call the function in this shell (so the note is visible),
# capture its return code in RC and its stderr in ./stderr.
run_remove() {
  RC=0
  remove_claude_md_block "$@" 2>"$CASE/stderr" || RC=$?
}

assert_no_temp_left() {
  local label="$1" left
  left=$(find "$CASE/tmp" -mindepth 1 | head -n 5)
  [ -z "$left" ] || fail "$label: temp files left behind: $left"
}

assert_untouched_error() {
  local label="$1"
  assert_rc 13 "$RC" "$label"
  assert_note "CLAUDE.md block error: malformed markers" "$label"
  grep -q '^❌ ' "$CASE/stderr" || fail "$label: no ❌ line on stderr: $(cat "$CASE/stderr")"
  assert_file_eq "$CASE/original" "$CASE/CLAUDE.md" "$label"
  assert_no_temp_left "$label"
}

load_remove_bundle

# Shared pieces. BEFORE ends with a blank line next to the start marker;
# AFTER starts with blank lines (LF, then CRLF) next to the end marker and has
# no final newline. The end marker itself is a CRLF line.
BEFORE='# Team notes\r\nKeep this line.   \r\nNon-ASCII: café, naïve, 東京\n\n'
START='<!-- writ:start -->\n'
INNER='# Writ\r\n@.claude/system-instructions.md\n\nInner text.\n'
END_CRLF='<!-- writ:end -->\r\n'
AFTER='\n\r\nBelow the block.   \r\n@notes.md\n\nLast line, no newline   '

# ----- AC-4.1: every byte outside the block survives; mode unchanged -----
new_case
printf "$BEFORE$START$INNER$END_CRLF$AFTER" >CLAUDE.md
printf "$BEFORE$AFTER" >expected
chmod 640 CLAUDE.md
mode_before=$(mode_of CLAUDE.md)
run_remove CLAUDE.md
assert_rc 0 "$RC" "rich fixture"
assert_note "🗑  Removed: CLAUDE.md Writ block" "rich fixture"
assert_file_eq expected CLAUDE.md "rich fixture"
[ "$(mode_of CLAUDE.md)" = "$mode_before" ] \
  || fail "rich fixture: mode changed from $mode_before to $(mode_of CLAUDE.md)"
[ ! -s "$CASE/stderr" ] || fail "rich fixture: unexpected stderr: $(cat "$CASE/stderr")"
assert_no_temp_left "rich fixture"

# The block on line 1: only the bytes after it remain.
new_case
printf "$START$INNER$END_CRLF$AFTER" >CLAUDE.md
printf "$AFTER" >expected
run_remove CLAUDE.md
assert_rc 0 "$RC" "block on line 1"
assert_note "🗑  Removed: CLAUDE.md Writ block" "block on line 1"
assert_file_eq expected CLAUDE.md "block on line 1"

# The block last, end marker with no final newline: only the bytes before it remain.
new_case
printf "$BEFORE$START$INNER<!-- writ:end -->" >CLAUDE.md
printf "$BEFORE" >expected
run_remove CLAUDE.md
assert_rc 0 "$RC" "block last"
assert_note "🗑  Removed: CLAUDE.md Writ block" "block last"
assert_file_eq expected CLAUDE.md "block last"

# Only whitespace left: kept as is, because only zero bytes counts as empty.
new_case
printf "\n  \n$START$INNER$END_CRLF\t\n" >CLAUDE.md
printf '\n  \n\t\n' >expected
run_remove CLAUDE.md
assert_rc 0 "$RC" "whitespace remainder"
assert_note "🗑  Removed: CLAUDE.md Writ block" "whitespace remainder"
assert_file_eq expected CLAUDE.md "whitespace remainder"

# ----- AC-4.2: block only → file deleted -----
new_case
printf "$START$INNER<!-- writ:end -->\n" >CLAUDE.md
run_remove CLAUDE.md
assert_rc 0 "$RC" "block only"
assert_note "🗑  Removed: CLAUDE.md (empty after Writ block removal)" "block only"
[ ! -e CLAUDE.md ] || fail "block only: CLAUDE.md still exists"
assert_no_temp_left "block only"

# ----- AC-4.2: no markers → byte-identical -----
new_case
printf "$BEFORE$AFTER" >CLAUDE.md
cp CLAUDE.md original
chmod 640 CLAUDE.md
mode_before=$(mode_of CLAUDE.md)
run_remove CLAUDE.md
assert_rc 0 "$RC" "no markers"
assert_note "✓ CLAUDE.md (no Writ block present)" "no markers"
assert_file_eq original CLAUDE.md "no markers"
[ "$(mode_of CLAUDE.md)" = "$mode_before" ] || fail "no markers: mode changed"
assert_no_temp_left "no markers"

# ----- AC-4.2: two start markers → return 13, ❌ on stderr, byte-identical -----
new_case
printf "$BEFORE$START$INNER$START$END_CRLF$AFTER" >CLAUDE.md
cp CLAUDE.md original
run_remove CLAUDE.md
assert_untouched_error "two start markers"

# Malformed in other ways: end before start, and a start with no end.
new_case
printf "$BEFORE$END_CRLF$INNER$START$AFTER" >CLAUDE.md
cp CLAUDE.md original
run_remove CLAUDE.md
assert_untouched_error "end before start"

new_case
printf "$BEFORE$START$INNER$AFTER" >CLAUDE.md
cp CLAUDE.md original
run_remove CLAUDE.md
assert_untouched_error "start without end"

# ----- AC-4.2: no file → note only, nothing created -----
new_case
run_remove CLAUDE.md
assert_rc 0 "$RC" "no file"
assert_note "✓ CLAUDE.md (no file present)" "no file"
[ ! -e CLAUDE.md ] || fail "no file: CLAUDE.md was created"
assert_no_temp_left "no file"

# The default argument is CLAUDE.md in the working directory.
new_case
printf "$BEFORE$START$INNER$END_CRLF$AFTER" >CLAUDE.md
printf "$BEFORE$AFTER" >expected
run_remove
assert_rc 0 "$RC" "default argument"
assert_file_eq expected CLAUDE.md "default argument"

printf 'OK remove_claude_md_block fixtures\n'
