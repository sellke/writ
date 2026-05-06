#!/usr/bin/env bash
# Tests remove_agents_md_block() bundled from scripts/uninstall.sh.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
UNINSTALL_SRC="$REPO/scripts/uninstall.sh"
BUNDLE_MARKER_BEGIN='# <<< writ-remove-agents-md-bundled-begin (used by scripts/tests/test_remove_agents_md_block.sh — keep synced) >>>'
BUNDLE_MARKER_END='# <<< writ-remove-agents-md-bundled-end >>>'

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

assert_file_eq() {
  local expected="$1" actual="$2"
  cmp -s "$expected" "$actual" || {
    printf 'Expected:\n' >&2
    sed 's/^/  /' "$expected" >&2
    printf 'Actual:\n' >&2
    sed 's/^/  /' "$actual" >&2
    fail "files differ: $expected vs $actual"
  }
}

load_remove_bundle() {
  local chunk
  chunk=$(awk -v s="$BUNDLE_MARKER_BEGIN" -v e="$BUNDLE_MARKER_END" '
    index($0,s) { p=1; next }
    index($0,e) { exit }
    p
  ' "$UNINSTALL_SRC") || fail "Could not extract remove bundle from uninstall.sh"

  eval "$chunk"
}

setup_ws() {
  WORK=$(mktemp -d "${TMPDIR:-/tmp}/writ-remove-test.XXXXXX")
  cd "$WORK"
}

run_case() {
  load_remove_bundle
  setup_ws
}

run_case
cat >AGENTS.md <<'EOF'
<!-- writ:start -->
Writ block
<!-- writ:end -->
EOF
remove_agents_md_block AGENTS.md
[ ! -e AGENTS.md ] || fail "writ-only case should delete AGENTS.md"

run_case
cat >AGENTS.md <<'EOF'
User content above.
<!-- writ:start -->
Writ block
<!-- writ:end -->
EOF
printf '%s\n' 'User content above.' >expected
remove_agents_md_block AGENTS.md
assert_file_eq expected AGENTS.md

run_case
cat >AGENTS.md <<'EOF'
Top content.

<!-- writ:start -->
Writ block
<!-- writ:end -->

Bottom content.
EOF
cat >expected <<'EOF'
Top content.

Bottom content.
EOF
remove_agents_md_block AGENTS.md
assert_file_eq expected AGENTS.md

run_case
cat >AGENTS.md <<'EOF'
No Writ markers here.
EOF
cp AGENTS.md expected
remove_agents_md_block AGENTS.md
assert_file_eq expected AGENTS.md
[ "$REMOVE_AGENTS_MD_NOTE" = "✓ AGENTS.md (no Writ block present)" ] || fail "unexpected no-marker note: $REMOVE_AGENTS_MD_NOTE"

run_case
cat >AGENTS.md <<'EOF'
<!-- writ:start -->
Missing end marker.
EOF
if remove_agents_md_block AGENTS.md; then
  fail "malformed markers should fail"
fi

printf 'OK remove_agents_md_block fixtures\n'
