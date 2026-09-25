#!/usr/bin/env bash
# Tests scripts/eval.sh check_manifest() treatment of lean siblings
# (spec 2026-09-24-flagged-harness-cuts, Story 4).
#
# Contract: `commands/<stem>.lean.md` is the WRIT_HARNESS_LEAN=1 alternate
# body for `commands/<stem>.md`, not a command of its own, so it needs no
# .writ/manifest.yaml entry. A regular command missing from the manifest is
# still a finding — the exclusion is by the `.lean.md` suffix only.
#
# Harness: scripts/eval.sh derives PROJECT_ROOT from its own directory, so
# copying it into a temp `scripts/` dir beside a synthetic tree exercises the
# real check with no mutation of the repository (same approach as
# test_eval_entry_level_note.sh).
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
EVAL="$REPO/scripts/eval.sh"

pass_count=0
fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}
ok() {
  pass_count=$((pass_count + 1))
  printf 'PASS: %s\n' "$1"
}

ROOT="$(mktemp -d "${TMPDIR:-/tmp}/writ-eval-manifest-lean.XXXXXX")"
cleanup() {
  local rc=$?
  rm -rf "$ROOT"
  return "$rc"
}
trap cleanup EXIT

mkdir -p "$ROOT/scripts" "$ROOT/commands" "$ROOT/agents" "$ROOT/.writ/state"
cp "$EVAL" "$ROOT/scripts/eval.sh"

for name in listed listed.lean unlisted orphan.lean _preamble _preamble.lean; do
  printf -- '---\nname: %s\ndescription: "d"\n---\n\n## Overview\n' "$name" \
    > "$ROOT/commands/$name.md"
done

cat > "$ROOT/.writ/manifest.yaml" <<'EOF'
commands:
  - name: listed
    file: commands/listed.md
agents:
EOF

rc=0
( cd "$ROOT" && bash scripts/eval.sh --check=manifest --report=eval-report.md >/dev/null 2>&1 ) || rc=$?
REPORT="$ROOT/eval-report.md"
[ -f "$REPORT" ] || fail "eval.sh wrote no report (rc=$rc)"

if grep -q 'commands/listed.lean.md' "$REPORT"; then
  fail "a lean sibling was reported as a command missing from the manifest"
fi
ok "commands/listed.lean.md needs no manifest entry"

if grep -q 'commands/_preamble.lean.md' "$REPORT"; then
  fail "the lean preamble was reported as a command missing from the manifest"
fi
ok "commands/_preamble.lean.md needs no manifest entry"

grep -q '`commands/unlisted.md`: command file exists but is not listed' "$REPORT" \
  || fail "an ordinary unlisted command was not reported"
ok "an ordinary unlisted command is still a finding"

if grep -q '`commands/listed.md`: command file exists but is not listed' "$REPORT"; then
  fail "a listed command was reported as unlisted"
fi
ok "a listed command passes"

grep -q '`commands/orphan.lean.md`: command file exists but is not listed' "$REPORT" \
  || fail "an orphan .lean.md with no default sibling was not reported"
ok "an orphan .lean.md (no commands/orphan.md) is still a finding"

printf '%d passed\n' "$pass_count"
