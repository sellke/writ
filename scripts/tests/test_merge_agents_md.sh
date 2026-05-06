#!/usr/bin/env bash
# Tests merge_agents_md() bundled from scripts/install.sh (see writ-merge markers).
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
  WORK=$(mktemp -d "${TMPDIR:-/tmp}/writ-merge-test.XXXXXX")
  mkdir -p "$WORK/writ-src/codex"
  WRIT_SRC="$WORK/writ-src"
  printf '%s\n' 'UPSTREAM_STUB_TEMPLATE_BODY' > "$WRIT_SRC/codex/AGENTS.md.template"
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
merge_agents_md apply
[ -f AGENTS.md ] || fail 'case1: AGENTS.md should exist'
assert_file_contains AGENTS.md '<!-- writ:start -->'
assert_file_contains AGENTS.md 'UPSTREAM_STUB_TEMPLATE_BODY'

# ----- Case 2: existing file without markers -----
run
MANIFEST_FILE="$WORK/no-marker.manifest"
: >"$MANIFEST_FILE"
printf '%s\n' 'USER_LINE_A' >AGENTS.md
merge_agents_md apply
awk 'BEGIN{ok=0} /^USER_LINE_A$/{ok=1} /^<!-- writ:start -->$/ && ok==1 {found=1} END{exit found?0:1}' AGENTS.md || fail 'case2: user line should precede markers'
grep -Fq 'UPSTREAM_STUB_TEMPLATE_BODY' AGENTS.md || fail 'case2: template inner missing'

# ----- Case 3: markers clean — replace inner from upstream -----
run
MANIFEST_FILE="$WORK/clean.manifest"
{
  printf '%s\n' '# user top'
  printf '%s\n' '<!-- writ:start -->'
  printf '%s\n' 'OLD_INNER_BODY'
  printf '%s\n' '<!-- writ:end -->'
  printf '%s\n' '# user bot'
} >AGENTS.md
OLD_INNER_HASH=""
OLD_INNER_HASH="$(writ_compute_writ_block_inner_hash "AGENTS.md")" || fail 'case3: inner hash computation failed'
{
  printf '%s\n' "$OLD_INNER_HASH"'  AGENTS.md.writ-block'
} >"$MANIFEST_FILE"
FORCE=false
merge_agents_md apply
grep -Fq 'OLD_INNER_BODY' AGENTS.md && fail 'case3: old inner should be gone'
grep -Fq 'UPSTREAM_STUB_TEMPLATE_BODY' AGENTS.md || fail 'case3: new inner missing'
grep -Fq '# user top' AGENTS.md || fail 'case3: user top clipped'
grep -Fq '# user bot' AGENTS.md || fail 'case3: user bottom clipped'

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
} >AGENTS.md
if merge_agents_md apply; then
  fail 'case4: malformed markers should return non-zero'
fi

# ----- Case 5: local modifications preserved (inner drift from manifest baseline) -----
run
MANIFEST_FILE="$WORK/mod.manifest"
UPSTREAM_HASH=""
UPSTREAM_HASH="$(hash_file "$WRIT_SRC/codex/AGENTS.md.template")"
{
  printf '%s\n' "$UPSTREAM_HASH"'  AGENTS.md.writ-block'
} >"$MANIFEST_FILE"
{
  printf '%s\n' '<!-- writ:start -->'
  printf '%s\n' 'CUSTOM_LOCAL_INNER'
  printf '%s\n' '<!-- writ:end -->'
} >AGENTS.md
FORCE=false
merge_agents_md apply
grep -Fq 'CUSTOM_LOCAL_INNER' AGENTS.md || fail 'case5: inner should remain'
grep -Fq 'UPSTREAM_STUB_TEMPLATE_BODY' AGENTS.md && fail 'case5: upstream leaked into preserved block'

# ----- Case 5b: --force overwrites locally modified -----
run
MANIFEST_FILE="$WORK/mod2.manifest"
{
  printf '%s\n' '<!-- writ:start -->'
  printf '%s\n' 'CUSTOM_LOCAL_INNER'
  printf '%s\n' '<!-- writ:end -->'
} >AGENTS.md
STUB_HASH_B=""
STUB_HASH_B="$(writ_compute_writ_block_inner_hash "AGENTS.md")" || fail 'case5b: baseline hash computation failed'
{
  printf '%s\n' "$STUB_HASH_B"'  AGENTS.md.writ-block'
} >"$MANIFEST_FILE"
FORCE=true
merge_agents_md apply
grep -Fq 'CUSTOM_LOCAL_INNER' AGENTS.md && fail 'case5b: inner should have been overwritten'
grep -Fq 'UPSTREAM_STUB_TEMPLATE_BODY' AGENTS.md || fail 'case5b: template missing'

printf 'OK merge_agents_md fixtures\n'
