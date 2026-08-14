#!/usr/bin/env bash
# Tests merge_claude_md() bundled from scripts/install.sh (see writ-merge markers).
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

printf 'OK merge_claude_md fixtures\n'
