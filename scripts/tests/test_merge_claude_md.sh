#!/usr/bin/env bash
# Tests merge_claude_md() bundled from scripts/install.sh (see writ-merge markers).
# Cases 8-11 test the preserved-block warning and writ_block_inner_has_line.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
INSTALL_SRC="$REPO/scripts/install.sh"
BUNDLE_MARKER_BEGIN='# <<< writ-merge-bundled-begin (used by scripts/tests/test_merge_agents_md.sh — keep synced) >>>'
BUNDLE_MARKER_END='# <<< writ-merge-bundled-end >>>'

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

assert_file_contains() {
  grep -Fq -- "$2" "$1" || fail "File '$1' missing expected substring '$2'"
}

setup_ws() {
  WORK=$(mktemp -d "${TMPDIR:-/tmp}/writ-merge-claude-test.XXXXXX")
  mkdir -p "$WORK/writ-src/claude-code"
  WRIT_SRC="$WORK/writ-src"
  printf '%s\n' 'UPSTREAM_STUB_CLAUDE_MD_BODY' > "$WRIT_SRC/claude-code/CLAUDE.md"
  cd "$WORK"
}

load_merge_bundle() {
  local chunk
  chunk=$(awk -v s="$BUNDLE_MARKER_BEGIN" -v e="$BUNDLE_MARKER_END" '
    index($0,s) { p=1; next }
    index($0,e) { exit }
    p
  ' "$INSTALL_SRC") || fail "Could not extract merge bundle from install.sh"

  hash_file() {
    if command -v shasum &>/dev/null; then
      shasum -a 256 "$1" | cut -d' ' -f1
    elif command -v sha256sum &>/dev/null; then
      sha256sum "$1" | cut -d' ' -f1
    else
      openssl dgst -sha256 "$1" | awk '{print $NF}'
    fi
  }

  manifest_hash_for() {
    local path="$1"
    [ -f "${MANIFEST_FILE:-}" ] && grep "  ${path}$" "$MANIFEST_FILE" | cut -d' ' -f1 || true
  }

  eval "$chunk"
}

run() {
  load_merge_bundle
  setup_ws
}

run

# AC coverage (spec 2026-08-13-claude-md-install-merge): AC-1.1 (case 1), AC-1.2 (case 2), AC-1.3 (case 4), AC-1.4
# (cases 5, 5b), AC-1.5 (cases 3, 3b — manifest baseline round-trip).

# ----- Case 1: file absent -----
MANIFEST_FILE="$WORK/absent.manifest"
: >"$MANIFEST_FILE"
FORCE=false
merge_claude_md apply
[ -f CLAUDE.md ] || fail 'case1: CLAUDE.md should exist'
assert_file_contains CLAUDE.md '<!-- writ:start -->'
assert_file_contains CLAUDE.md 'UPSTREAM_STUB_CLAUDE_MD_BODY'

# ----- Case 2: existing file without markers -----
run
MANIFEST_FILE="$WORK/no-marker.manifest"
: >"$MANIFEST_FILE"
printf '%s\n' 'USER_LINE_A' >CLAUDE.md
merge_claude_md apply
awk 'BEGIN{ok=0} /^USER_LINE_A$/{ok=1} /^<!-- writ:start -->$/ && ok==1 {found=1} END{exit found?0:1}' CLAUDE.md || fail 'case2: user line should precede markers'
grep -Fq 'UPSTREAM_STUB_CLAUDE_MD_BODY' CLAUDE.md || fail 'case2: template inner missing'

# ----- Case 3: markers clean — replace inner from upstream -----
run
MANIFEST_FILE="$WORK/clean.manifest"
{
  printf '%s\n' '# user top'
  printf '%s\n' '<!-- writ:start -->'
  printf '%s\n' 'OLD_INNER_BODY'
  printf '%s\n' '<!-- writ:end -->'
  printf '%s\n' '# user bot'
} >CLAUDE.md
OLD_INNER_HASH=""
OLD_INNER_HASH="$(writ_compute_writ_block_inner_hash "CLAUDE.md")" || fail 'case3: inner hash computation failed'
{
  printf '%s\n' "$OLD_INNER_HASH"'  CLAUDE.md.writ-block'
} >"$MANIFEST_FILE"
FORCE=false
merge_claude_md apply
grep -Fq 'OLD_INNER_BODY' CLAUDE.md && fail 'case3: old inner should be gone'
grep -Fq 'UPSTREAM_STUB_CLAUDE_MD_BODY' CLAUDE.md || fail 'case3: new inner missing'
grep -Fq '# user top' CLAUDE.md || fail 'case3: user top clipped'
grep -Fq '# user bot' CLAUDE.md || fail 'case3: user bottom clipped'

# ----- Case 3b: markers clean and already matching upstream — no-op -----
run
MANIFEST_FILE="$WORK/noop.manifest"
: >"$MANIFEST_FILE"
{
  printf '%s\n' '# user top'
  printf '%s\n' '<!-- writ:start -->'
  printf '%s\n' 'UPSTREAM_STUB_CLAUDE_MD_BODY'
  printf '%s\n' '<!-- writ:end -->'
  printf '%s\n' '# user bot'
} >CLAUDE.md
cp CLAUDE.md "$WORK/noop.before"
FORCE=false
merge_claude_md apply
diff -q "$WORK/noop.before" CLAUDE.md >/dev/null || fail 'case3b: file matching upstream should be left untouched'

# ----- Case 4: malformed markers (two starts) -----
run
MANIFEST_FILE="$WORK/bad.manifest"
: >"$MANIFEST_FILE"
{
  printf '%s\n' '<!-- writ:start -->'
  printf '%s\n' 'inner1'
  printf '%s\n' '<!-- writ:start -->'
  printf '%s\n' 'inner2'
  printf '%s\n' '<!-- writ:end -->'
} >CLAUDE.md
cp CLAUDE.md "$WORK/bad.before"
if merge_claude_md apply; then
  fail 'case4: malformed markers should return non-zero'
fi
diff -q "$WORK/bad.before" CLAUDE.md >/dev/null || fail 'case4: malformed markers file should be left untouched'

# ----- Case 5: local modifications preserved (inner drift from manifest baseline) -----
run
MANIFEST_FILE="$WORK/mod.manifest"
UPSTREAM_HASH=""
UPSTREAM_HASH="$(hash_file "$WRIT_SRC/claude-code/CLAUDE.md")"
{
  printf '%s\n' "$UPSTREAM_HASH"'  CLAUDE.md.writ-block'
} >"$MANIFEST_FILE"
{
  printf '%s\n' '<!-- writ:start -->'
  printf '%s\n' 'CUSTOM_LOCAL_INNER'
  printf '%s\n' '<!-- writ:end -->'
} >CLAUDE.md
FORCE=false
merge_claude_md apply
grep -Fq 'CUSTOM_LOCAL_INNER' CLAUDE.md || fail 'case5: inner should remain'
grep -Fq 'UPSTREAM_STUB_CLAUDE_MD_BODY' CLAUDE.md && fail 'case5: upstream leaked into preserved block'

# ----- Case 5b: --force overwrites locally modified -----
run
MANIFEST_FILE="$WORK/mod2.manifest"
{
  printf '%s\n' '<!-- writ:start -->'
  printf '%s\n' 'CUSTOM_LOCAL_INNER'
  printf '%s\n' '<!-- writ:end -->'
} >CLAUDE.md
STUB_HASH_B=""
STUB_HASH_B="$(writ_compute_writ_block_inner_hash "CLAUDE.md")" || fail 'case5b: baseline hash computation failed'
{
  printf '%s\n' "$STUB_HASH_B"'  CLAUDE.md.writ-block'
} >"$MANIFEST_FILE"
FORCE=true
merge_claude_md apply
grep -Fq 'CUSTOM_LOCAL_INNER' CLAUDE.md && fail 'case5b: inner should have been overwritten'
grep -Fq 'UPSTREAM_STUB_CLAUDE_MD_BODY' CLAUDE.md || fail 'case5b: template missing'

# ----- Case 6: existing file but empty — treated as no markers, appended with no leading blank line -----
run
MANIFEST_FILE="$WORK/empty.manifest"
: >"$MANIFEST_FILE"
: >CLAUDE.md
merge_claude_md apply
[ -s CLAUDE.md ] || fail 'case6: CLAUDE.md should not be empty after merge'
FIRST_LINE="$(head -n1 CLAUDE.md)"
[ "$FIRST_LINE" = '<!-- writ:start -->' ] || fail "case6: expected no leading blank-line artifact, first line was: $FIRST_LINE"
assert_file_contains CLAUDE.md 'UPSTREAM_STUB_CLAUDE_MD_BODY'

# ----- Case 7: upstream template missing -> clear error, no write, no CLAUDE.md created -----
run
rm -f "$WRIT_SRC/claude-code/CLAUDE.md"
MANIFEST_FILE="$WORK/missing-template.manifest"
: >"$MANIFEST_FILE"
set +e
merge_claude_md apply
RC=$?
set -e
[ "$RC" -eq 12 ] || fail "case7: expected exit code 12 for missing upstream template, got $RC"
[ ! -e CLAUDE.md ] || fail 'case7: CLAUDE.md should not be created when upstream template is missing'

# ===== Story 2 of 2026-10-20-claude-code-parity =====
# AC-2.4: a preserved block without the import line prints a warning that names
# the line and --force, in preview and apply, and CLAUDE.md stays byte-identical.
# A preserved block with the line prints no warning. AC-2.2: on the replace and
# --force paths the bytes outside the markers stay, CRLF lines included.
IMPORT_LINE='@.claude/system-instructions.md'
INSTALL_WARNING='⚠️  CLAUDE.md: the preserved Writ block has no @.claude/system-instructions.md line. Add it inside the block, or re-run install.sh --force to replace the block.'
WARNING_TEXT='has no @.claude/system-instructions.md line'

# ----- Case 8: writ_block_inner_has_line reads only the lines between the markers -----
run
printf '%s\r\n' '# user top' '<!-- writ:start -->' 'custom' "$IMPORT_LINE" '<!-- writ:end -->' >CLAUDE.md
writ_block_inner_has_line CLAUDE.md "$IMPORT_LINE" || fail 'case8: CRLF import line inside the markers not found'
printf '%s\n' "$IMPORT_LINE" '<!-- writ:start -->' 'custom' '<!-- writ:end -->' "$IMPORT_LINE" >CLAUDE.md
if writ_block_inner_has_line CLAUDE.md "$IMPORT_LINE"; then
  fail 'case8: an import line outside the markers counted as inside'
fi
printf '%s\n' '<!-- writ:start -->' "  $IMPORT_LINE" "\`$IMPORT_LINE\`" '<!-- writ:end -->' >CLAUDE.md
if writ_block_inner_has_line CLAUDE.md "$IMPORT_LINE"; then
  fail 'case8: a line that only contains the import text counted as the import line'
fi

# ----- Case 9: preserved block without the import line -> warning, file unchanged -----
# The user wrote the import line above the block; the block itself lacks it.
run
MANIFEST_FILE="$WORK/warn.manifest"
printf '%s\n' "$(hash_file "$WRIT_SRC/claude-code/CLAUDE.md")  CLAUDE.md.writ-block" >"$MANIFEST_FILE"
{
  printf '# user top\r\n%s\r\n' "$IMPORT_LINE"
  printf '%s\n' '<!-- writ:start -->' 'CUSTOM_LOCAL_INNER' '<!-- writ:end -->'
  printf 'user bottom, no final newline'
} >CLAUDE.md
cp CLAUDE.md "$WORK/warn.before"
FORCE=false
merge_claude_md preview >"$WORK/warn.preview" 2>&1
grep -qxF "$INSTALL_WARNING" "$WORK/warn.preview" || fail "case9(preview): no warning: $(cat "$WORK/warn.preview")"
cmp -s "$WORK/warn.before" CLAUDE.md || fail 'case9(preview): CLAUDE.md changed'
merge_claude_md apply >"$WORK/warn.apply" 2>&1
[ "$CLAUDE_MERGE_NOTE" = 'CLAUDE.md: Writ block preserved (local modifications)' ] \
  || fail "case9(apply): expected the preserved note, got $CLAUDE_MERGE_NOTE"
grep -qxF "$INSTALL_WARNING" "$WORK/warn.apply" || fail "case9(apply): no warning: $(cat "$WORK/warn.apply")"
cmp -s "$WORK/warn.before" CLAUDE.md || fail 'case9(apply): CLAUDE.md changed'

# ----- Case 10: preserved block with the import line (CRLF) -> no warning -----
run
MANIFEST_FILE="$WORK/has-line.manifest"
printf '%s\n' "$(hash_file "$WRIT_SRC/claude-code/CLAUDE.md")  CLAUDE.md.writ-block" >"$MANIFEST_FILE"
printf '%s\r\n' '# user top' '<!-- writ:start -->' 'CUSTOM_LOCAL_INNER' "$IMPORT_LINE" '<!-- writ:end -->' >CLAUDE.md
cp CLAUDE.md "$WORK/has-line.before"
FORCE=false
merge_claude_md preview >"$WORK/has-line.preview" 2>&1
grep -qF 'Would preserve Writ block' "$WORK/has-line.preview" || fail 'case10(preview): block not preserved'
grep -qF "$WARNING_TEXT" "$WORK/has-line.preview" && fail 'case10(preview): warned about a block that has the line'
merge_claude_md apply >"$WORK/has-line.apply" 2>&1
[ "$CLAUDE_MERGE_NOTE" = 'CLAUDE.md: Writ block preserved (local modifications)' ] \
  || fail "case10(apply): expected the preserved note, got $CLAUDE_MERGE_NOTE"
grep -qF "$WARNING_TEXT" "$WORK/has-line.apply" && fail 'case10(apply): warned about a block that has the line'
cmp -s "$WORK/has-line.before" CLAUDE.md || fail 'case10: CLAUDE.md changed'

# ----- Case 11: CRLF user content outside the markers on the replace and --force paths -----
run
MANIFEST_FILE="$WORK/crlf.manifest"
printf '# user top\r\ntrailing spaces   \r\nnon-ASCII: café, 東京\n@notes.md\n' >"$WORK/crlf.prefix"
printf 'user bottom\r\n@notes.md\nno final newline   ' >"$WORK/crlf.suffix"
{
  cat "$WORK/crlf.prefix"
  printf '%s\n' '<!-- writ:start -->' 'OLD_INNER_BODY' '<!-- writ:end -->'
  cat "$WORK/crlf.suffix"
} >CLAUDE.md
{
  cat "$WORK/crlf.prefix"
  printf '%s\n' '<!-- writ:start -->' 'UPSTREAM_STUB_CLAUDE_MD_BODY' '<!-- writ:end -->'
  cat "$WORK/crlf.suffix"
} >"$WORK/crlf.expected"
OLD_INNER_HASH="$(writ_compute_writ_block_inner_hash "CLAUDE.md")" || fail 'case11: inner hash computation failed'
printf '%s\n' "$OLD_INNER_HASH"'  CLAUDE.md.writ-block' >"$MANIFEST_FILE"
FORCE=false
merge_claude_md apply >"$WORK/crlf.apply" 2>&1
[ "$CLAUDE_MERGE_NOTE" = 'CLAUDE.md: Writ block updated' ] || fail "case11: expected an update, got $CLAUDE_MERGE_NOTE"
cmp "$WORK/crlf.expected" CLAUDE.md || fail 'case11: bytes outside the markers changed on the replace path'
grep -qF "$WARNING_TEXT" "$WORK/crlf.apply" && fail 'case11: warned on the replace path'
{
  cat "$WORK/crlf.prefix"
  printf '%s\n' '<!-- writ:start -->' 'CUSTOM_LOCAL_INNER' '<!-- writ:end -->'
  cat "$WORK/crlf.suffix"
} >CLAUDE.md
FORCE=true
merge_claude_md apply >"$WORK/crlf.force" 2>&1
[ "$CLAUDE_MERGE_NOTE" = 'CLAUDE.md: Writ block updated (--force)' ] || fail "case11: expected a forced update, got $CLAUDE_MERGE_NOTE"
cmp "$WORK/crlf.expected" CLAUDE.md || fail 'case11: bytes outside the markers changed on the --force path'
grep -qF "$WARNING_TEXT" "$WORK/crlf.force" && fail 'case11: warned on the --force path'
FORCE=false

printf 'OK merge_claude_md fixtures\n'
