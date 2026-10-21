#!/usr/bin/env bash
# Tests merge_claude_md() bundled from scripts/update.sh (see writ-merge markers).
# Structurally mirrors scripts/tests/test_merge_claude_md.sh (install.sh's version),
# but exercises update.sh's own separately-maintained copy — same decision tree,
# using update.sh's naming convention (CLAUDE_MD_ACTION / CLAUDE_MD_NOTE) instead
# of install.sh's (CLAUDE_MERGE_NOTE).
#
# AC coverage (spec 2026-08-13-claude-md-install-merge): AC-2.1 (absent-file restore), AC-2.2 (pre-fix-upgrade restore,
# see the crux-case comment below), AC-2.3 (malformed markers -> error),
# AC-2.4 (baseline/force -> update), AC-2.5 (neither match -> preserved).
# Cases 8-12 test the preserved-block warning, writ_block_inner_has_line, and the
# system-instructions.md manifest line.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
UPDATE_SRC="$REPO/scripts/update.sh"
BUNDLE_MARKER_BEGIN='# <<< writ-merge-bundled-begin (used by scripts/tests/test_update_claude_md.sh — keep synced) >>>'
BUNDLE_MARKER_END='# <<< writ-merge-bundled-end >>>'

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

assert_file_contains() {
  grep -Fq -- "$2" "$1" || fail "File '$1' missing expected substring '$2'"
}

setup_ws() {
  WORK=$(mktemp -d "${TMPDIR:-/tmp}/writ-update-claude-test.XXXXXX")
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
  ' "$UPDATE_SRC") || fail "Could not extract merge bundle from update.sh"

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

# ----- Case 1: file absent -> restore (unit-tested directly, per story's Gate 0
# guidance — update.sh's own CLI guard at update.sh:104-109 makes this branch
# unreachable via the real entry point, so we exercise the function directly). -----
MANIFEST_FILE="$WORK/absent.manifest"
: >"$MANIFEST_FILE"
FORCE=false
merge_claude_md preview
[ "$CLAUDE_MD_ACTION" = "restore" ] || fail "case1(preview): expected restore, got $CLAUDE_MD_ACTION"
[ ! -e CLAUDE.md ] || fail 'case1(preview): CLAUDE.md should not be created by preview'
merge_claude_md apply
[ "$CLAUDE_MD_ACTION" = "restore" ] || fail "case1(apply): expected restore, got $CLAUDE_MD_ACTION"
[ -f CLAUDE.md ] || fail 'case1(apply): CLAUDE.md should exist'
assert_file_contains CLAUDE.md '<!-- writ:start -->'
assert_file_contains CLAUDE.md 'UPSTREAM_STUB_CLAUDE_MD_BODY'

# ----- Case 2: pre-fix upgrade — old bare-key manifest (no CLAUDE.md.writ-block
# key) + unmarked CLAUDE.md on disk -> restore (append), never error. This is the
# crux acceptance criterion (AC-2.2): the marker-count check must run before any
# manifest-baseline lookup so an absent CLAUDE.md.writ-block key is never treated
# as "malformed" or misrouted. -----
run
MANIFEST_FILE="$WORK/prefix-upgrade.manifest"
{
  printf '%s\n' 'deadbeefcafefeed  CLAUDE.md'
} >"$MANIFEST_FILE"
printf '%s\n' 'USER_LINE_PREFIX' >CLAUDE.md
# Sanity: the old bare key must not resolve for the new key name.
[ -z "$(manifest_hash_for "CLAUDE.md.writ-block")" ] || fail 'case2: sanity check failed — old manifest unexpectedly has a writ-block key'
merge_claude_md apply
[ "$CLAUDE_MD_ACTION" = "restore" ] || fail "case2: expected restore for pre-fix upgrade, got $CLAUDE_MD_ACTION"
grep -Fq 'USER_LINE_PREFIX' CLAUDE.md || fail 'case2: existing content lost'
grep -Fq 'UPSTREAM_STUB_CLAUDE_MD_BODY' CLAUDE.md || fail 'case2: upstream block not appended'
awk 'BEGIN{ok=0} /^USER_LINE_PREFIX$/{ok=1} /^<!-- writ:start -->$/ && ok==1 {found=1} END{exit found?0:1}' CLAUDE.md \
  || fail 'case2: user line should precede the appended markers'

# ----- Case 3: malformed markers -> error, return 13, no write -----
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
set +e
merge_claude_md apply
RC=$?
set -e
[ "$RC" -eq 13 ] || fail "case3: expected return 13 for malformed markers, got $RC"
[ "$CLAUDE_MD_ACTION" = "error" ] || fail "case3: expected error action, got $CLAUDE_MD_ACTION"
diff -q "$WORK/bad.before" CLAUDE.md >/dev/null || fail 'case3: malformed-marker file should be left untouched'

# ----- Case 4: well-formed + baseline match -> update, inner-only overwrite -----
run
MANIFEST_FILE="$WORK/clean.manifest"
{
  printf '%s\n' '# user top'
  printf '%s\n' '<!-- writ:start -->'
  printf '%s\n' 'OLD_INNER_BODY'
  printf '%s\n' '<!-- writ:end -->'
  printf '%s\n' '# user bot'
} >CLAUDE.md
OLD_INNER_HASH="$(writ_compute_writ_block_inner_hash "CLAUDE.md")" || fail 'case4: inner hash computation failed'
printf '%s\n' "$OLD_INNER_HASH"'  CLAUDE.md.writ-block' >"$MANIFEST_FILE"
FORCE=false
merge_claude_md preview
[ "$CLAUDE_MD_ACTION" = "update" ] || fail "case4(preview): expected update, got $CLAUDE_MD_ACTION"
merge_claude_md apply
[ "$CLAUDE_MD_ACTION" = "update" ] || fail "case4(apply): expected update, got $CLAUDE_MD_ACTION"
grep -Fq 'OLD_INNER_BODY' CLAUDE.md && fail 'case4: old inner should be gone'
grep -Fq 'UPSTREAM_STUB_CLAUDE_MD_BODY' CLAUDE.md || fail 'case4: new inner missing'
grep -Fq '# user top' CLAUDE.md || fail 'case4: content above marker clipped'
grep -Fq '# user bot' CLAUDE.md || fail 'case4: content below marker clipped'

# ----- Case 4b: --force overwrites even without a matching baseline -----
run
MANIFEST_FILE="$WORK/force.manifest"
: >"$MANIFEST_FILE"
{
  printf '%s\n' '<!-- writ:start -->'
  printf '%s\n' 'CUSTOM_LOCAL_INNER'
  printf '%s\n' '<!-- writ:end -->'
} >CLAUDE.md
FORCE=true
merge_claude_md apply
[ "$CLAUDE_MD_ACTION" = "update" ] || fail "case4b: expected update (forced), got $CLAUDE_MD_ACTION"
grep -Fq 'CUSTOM_LOCAL_INNER' CLAUDE.md && fail 'case4b: inner should have been overwritten'
grep -Fq 'UPSTREAM_STUB_CLAUDE_MD_BODY' CLAUDE.md || fail 'case4b: template missing'

# ----- Case 5: well-formed + matches upstream -> unchanged -----
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
[ "$CLAUDE_MD_ACTION" = "unchanged" ] || fail "case5: expected unchanged, got $CLAUDE_MD_ACTION"
diff -q "$WORK/noop.before" CLAUDE.md >/dev/null || fail 'case5: file matching upstream should be left untouched'

# ----- Case 6: well-formed + neither upstream nor baseline match, no --force ->
# preserved with warning, no overwrite. -----
run
MANIFEST_FILE="$WORK/mod.manifest"
UPSTREAM_HASH="$(hash_file "$WRIT_SRC/claude-code/CLAUDE.md")"
printf '%s\n' "$UPSTREAM_HASH"'  CLAUDE.md.writ-block' >"$MANIFEST_FILE"
{
  printf '%s\n' '<!-- writ:start -->'
  printf '%s\n' 'CUSTOM_LOCAL_INNER'
  printf '%s\n' '<!-- writ:end -->'
} >CLAUDE.md
cp CLAUDE.md "$WORK/mod.before"
FORCE=false
merge_claude_md apply >"$WORK/mod.out" 2>&1
[ "$CLAUDE_MD_ACTION" = "preserved" ] || fail "case6: expected preserved, got $CLAUDE_MD_ACTION"
diff -q "$WORK/mod.before" CLAUDE.md >/dev/null || fail 'case6: preserved file should not be overwritten'
grep -Fq 'CUSTOM_LOCAL_INNER' CLAUDE.md || fail 'case6: local inner should remain'
grep -Fq 'Preserved' "$WORK/mod.out" || fail 'case6: expected a Preserved warning line to be printed'

# ----- Case 7: manifest-write fix (Gate 0 gap) — after merge_claude_md apply,
# write_copy_manifest must record CLAUDE.md.writ-block (inner-hash keyed) and must
# NOT re-introduce the retired bare CLAUDE.md whole-file-hash key. -----
run
MANIFEST_FILE="$WORK/gate0.manifest"
: >"$MANIFEST_FILE"
PLATFORM="claude"
PLATFORM_DIR="$WORK/.claude"
SKILLS_DIR="$WORK/.claude/skills"
mkdir -p "$PLATFORM_DIR/commands" "$PLATFORM_DIR/agents"
WRIT_REPO="test-repo"
FORCE=false
merge_claude_md apply
[ -f CLAUDE.md ] || fail 'case7: CLAUDE.md should exist before manifest write'

# write_copy_manifest lives outside the bundled decision-tree markers (it's shared
# manifest-regeneration logic, not part of merge_claude_md itself); pull it directly
# from update.sh and stub its unrelated helper deps (shippable-script/docs scanning
# is out of scope for this assertion).
append_manifest_shippable_scripts() { :; }
append_manifest_writ_docs() { :; }
wcm_chunk=$(awk '/^write_copy_manifest\(\) \{/{p=1} p{print} p && /^}/{exit}' "$UPDATE_SRC") \
  || fail 'case7: could not extract write_copy_manifest from update.sh'
eval "$wcm_chunk"
# write_copy_manifest records platform files through record_file_baseline.
rfb_chunk=$(awk '/^record_file_baseline\(\) \{/{p=1} p{print} p && /^}/{exit}' "$UPDATE_SRC")
[ -n "$rfb_chunk" ] || fail 'case7: could not extract record_file_baseline from update.sh'
eval "$rfb_chunk"

write_copy_manifest "test-version" "$MANIFEST_FILE"

grep -q '  CLAUDE.md.writ-block$' "$MANIFEST_FILE" || fail 'case7: manifest missing CLAUDE.md.writ-block key after apply'
grep -q '  CLAUDE.md$' "$MANIFEST_FILE" && fail 'case7: manifest should NOT contain the retired bare CLAUDE.md key'
true

# ===== Story 2 of 2026-10-20-claude-code-parity =====
# AC-2.4: a preserved block without the import line prints a warning that names
# the line and --force, in preview and apply, and CLAUDE.md stays byte-identical.
# A preserved block with the line prints no warning. AC-2.2: on the replace and
# --force paths the bytes outside the markers stay, CRLF lines included.
IMPORT_LINE='@.claude/system-instructions.md'
UPDATE_WARNING='⚠️  CLAUDE.md: the preserved Writ block has no @.claude/system-instructions.md line. Add it inside the block, or re-run update.sh --force to replace the block.'
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
[ "$CLAUDE_MD_ACTION" = "preserved" ] || fail "case9(preview): expected preserved, got $CLAUDE_MD_ACTION"
grep -qxF "$UPDATE_WARNING" "$WORK/warn.preview" || fail "case9(preview): no warning: $(cat "$WORK/warn.preview")"
cmp -s "$WORK/warn.before" CLAUDE.md || fail 'case9(preview): CLAUDE.md changed'
merge_claude_md apply >"$WORK/warn.apply" 2>&1
[ "$CLAUDE_MD_ACTION" = "preserved" ] || fail "case9(apply): expected preserved, got $CLAUDE_MD_ACTION"
grep -qxF "$UPDATE_WARNING" "$WORK/warn.apply" || fail "case9(apply): no warning: $(cat "$WORK/warn.apply")"
cmp -s "$WORK/warn.before" CLAUDE.md || fail 'case9(apply): CLAUDE.md changed'

# ----- Case 10: preserved block with the import line (CRLF) -> no warning -----
run
MANIFEST_FILE="$WORK/has-line.manifest"
printf '%s\n' "$(hash_file "$WRIT_SRC/claude-code/CLAUDE.md")  CLAUDE.md.writ-block" >"$MANIFEST_FILE"
printf '%s\r\n' '# user top' '<!-- writ:start -->' 'CUSTOM_LOCAL_INNER' "$IMPORT_LINE" '<!-- writ:end -->' >CLAUDE.md
cp CLAUDE.md "$WORK/has-line.before"
FORCE=false
merge_claude_md preview >"$WORK/has-line.preview" 2>&1
[ "$CLAUDE_MD_ACTION" = "preserved" ] || fail "case10(preview): expected preserved, got $CLAUDE_MD_ACTION"
grep -qF "$WARNING_TEXT" "$WORK/has-line.preview" && fail 'case10(preview): warned about a block that has the line'
merge_claude_md apply >"$WORK/has-line.apply" 2>&1
[ "$CLAUDE_MD_ACTION" = "preserved" ] || fail "case10(apply): expected preserved, got $CLAUDE_MD_ACTION"
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
[ "$CLAUDE_MD_ACTION" = "update" ] || fail "case11: expected update, got $CLAUDE_MD_ACTION"
cmp "$WORK/crlf.expected" CLAUDE.md || fail 'case11: bytes outside the markers changed on the replace path'
grep -qF "$WARNING_TEXT" "$WORK/crlf.apply" && fail 'case11: warned on the replace path'
{
  cat "$WORK/crlf.prefix"
  printf '%s\n' '<!-- writ:start -->' 'CUSTOM_LOCAL_INNER' '<!-- writ:end -->'
  cat "$WORK/crlf.suffix"
} >CLAUDE.md
FORCE=true
merge_claude_md apply >"$WORK/crlf.force" 2>&1
[ "$CLAUDE_MD_ACTION" = "update" ] || fail "case11: expected a forced update, got $CLAUDE_MD_ACTION"
cmp "$WORK/crlf.expected" CLAUDE.md || fail 'case11: bytes outside the markers changed on the --force path'
grep -qF "$WARNING_TEXT" "$WORK/crlf.force" && fail 'case11: warned on the --force path'
FORCE=false

# ----- Case 12: write_copy_manifest records .claude/system-instructions.md (AC-2.1) -----
# Under the key system-instructions.md, with the upstream hash when the local
# copy matches, and no line when there is no local copy. Uses the
# write_copy_manifest and record_file_baseline that case 7 loaded.
run
MANIFEST_FILE="$WORK/sysinst.manifest"
: >"$MANIFEST_FILE"
PLATFORM="claude"
PLATFORM_DIR="$WORK/.claude"
SKILLS_DIR="$WORK/.claude/skills"
mkdir -p "$PLATFORM_DIR"
WRIT_REPO="test-repo"
printf '%s\n' '# System instructions stub' '## Prime Directive' >"$WRIT_SRC/system-instructions.md"
FORCE=false
merge_claude_md apply
write_copy_manifest "test-version" "$MANIFEST_FILE"
grep -q '  system-instructions.md$' "$MANIFEST_FILE" && fail 'case12: manifest records system-instructions.md with no local copy'
cp "$WRIT_SRC/system-instructions.md" "$PLATFORM_DIR/system-instructions.md"
write_copy_manifest "test-version" "$MANIFEST_FILE"
grep -qxF "$(hash_file "$WRIT_SRC/system-instructions.md")  system-instructions.md" "$MANIFEST_FILE" \
  || fail "case12: manifest does not record system-instructions.md: $(cat "$MANIFEST_FILE")"
[ "$(grep -c '  system-instructions.md$' "$MANIFEST_FILE")" = 1 ] || fail 'case12: system-instructions.md recorded more than once'

printf 'OK merge_claude_md (update.sh) fixtures\n'
