#!/usr/bin/env bash
# Tests check_verdict_provenance in scripts/eval.sh (spec
# 2026-09-07-phase11-stage2-prune-the-base, Story 4, AC-4.3 / AC-4.4).
#
# Harness: copy eval.sh and verdict-provenance.py into a temp scripts/ so
# PROJECT_ROOT is the fixture tree, then write a commands/implement-story.md
# fixture per case. No mutation of the real repository.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
EVAL="$REPO/scripts/eval.sh"
HELPER="$REPO/scripts/verdict-provenance.py"

pass_count=0
fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}
ok() {
  pass_count=$((pass_count + 1))
  printf 'PASS: %s\n' "$1"
}

TMP_ROOTS=()
cleanup() {
  local rc=$? root
  for root in "${TMP_ROOTS[@]:-}"; do
    [ -n "$root" ] || continue
    rm -rf "$root"
  done
  return "$rc"
}
trap cleanup EXIT

new_root() {
  local root
  root="$(mktemp -d)"
  TMP_ROOTS+=("$root")
  mkdir -p "$root/scripts" "$root/commands"
  cp "$EVAL" "$root/scripts/eval.sh"
  cp "$HELPER" "$root/scripts/verdict-provenance.py"
  printf '# stub\n' > "$root/scripts/build-smoke.py"
  printf '# stub\n' > "$root/scripts/test-integrity.py"
  printf "%s" "$root"
}

run_check() {
  local root="$1" rc=0
  ( cd "$root" && bash scripts/eval.sh --check=verdict-provenance --report=eval-report.md >/dev/null 2>&1 ) || rc=$?
  printf "%s" "$rc"
}

report_of() {
  cat "$1/eval-report.md"
}

# Write a ten-gate fixture command file. $2 selects a mutation:
#   ""            clean: 2 script entries, 8 prose-only
#   drop-entry    gate2_5_surface entry removed  -> heading_without_entry
#   drop-heading  Gate 3.5 heading removed       -> entry_without_heading
#   bad-value     gate5_docs verification: manual -> unknown_verification_value
write_fixture() {
  local dest="$1" mutate="${2:-}"
  python3 - "$dest" "$mutate" <<'PY'
import sys
from pathlib import Path

dest = Path(sys.argv[1])
mutate = sys.argv[2]
ids = ["gate0_arch", "gate0_5_boundary", "gate1_coding", "gate2_build",
       "gate2_5_surface", "gate3_review", "gate3_5_drift", "gate4_tests",
       "gate4_5_visual", "gate5_docs"]
scripts = {"gate2_build": "scripts/build-smoke.py", "gate4_tests": "scripts/test-integrity.py"}
numbers = ["0", "0.5", "1", "2", "2.5", "3", "3.5", "4", "4.5", "5"]

fm = ["---", "name: implement-story", 'description: "fixture"', "gates:"]
for gid in ids:
    if mutate == "drop-entry" and gid == "gate2_5_surface":
        continue
    fm.append("  - id: %s" % gid)
    if gid in scripts:
        fm.append("    script: %s" % scripts[gid])
    elif mutate == "bad-value" and gid == "gate5_docs":
        fm.append("    verification: manual")
    else:
        fm.append("    verification: prose-only")
fm.append("---")

body = ["# Fixture", "", "## Overview", "", "### Step 3: Run Pipeline", ""]
for n in numbers:
    if mutate == "drop-heading" and n == "3.5":
        continue
    body.extend(["#### Gate %s: Fixture" % n, "", "Prose.", ""])
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text("\n".join(fm + body), encoding="utf-8")
PY
}

# ---------------------------------------------------------------------------
# AC-4.3 / AC-4.4: clean fixture -> PASS, exit 0, prose_only_count via add_note
# ---------------------------------------------------------------------------
ROOT="$(new_root)"
write_fixture "$ROOT/commands/implement-story.md"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 0 ] || { report_of "$ROOT"; fail "clean: expected exit 0, got $rc"; }
grep -q '^PASS' "$ROOT/eval-report.md" || { report_of "$ROOT"; fail "clean: report must say PASS"; }
if grep -q '^FAIL' "$ROOT/eval-report.md"; then
  report_of "$ROOT"; fail "clean: must have zero findings"
fi
note_count="$(grep -c '^\- NOTE' "$ROOT/eval-report.md" || true)"
[ "$note_count" -eq 1 ] || { report_of "$ROOT"; fail "clean: expected exactly one add_note, got $note_count"; }
grep -Fq 'prose_only_count: 8 (cap 2)' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "clean: note must carry prose_only_count: 8 (cap 2)"; }
ok "clean ten-gate fixture -> PASS, exit 0, prose_only_count relayed as a note"

# ---------------------------------------------------------------------------
# AC-4.4: each drift -> exit 1, one finding naming the code and the gate id
# ---------------------------------------------------------------------------
check_drift() {
  local mutate="$1" code="$2" gate="$3" root rc
  root="$(new_root)"
  write_fixture "$root/commands/implement-story.md" "$mutate"
  rc="$(run_check "$root")"
  [ "$rc" -eq 1 ] || { report_of "$root"; fail "$mutate: expected exit 1, got $rc"; }
  grep -q '^FAIL (1 finding' "$root/eval-report.md" \
    || { report_of "$root"; fail "$mutate: expected exactly one finding"; }
  grep -Fq "$code" "$root/eval-report.md" \
    || { report_of "$root"; fail "$mutate: finding must name $code"; }
  grep -Fq "$gate" "$root/eval-report.md" \
    || { report_of "$root"; fail "$mutate: finding must name $gate"; }
  grep -Fq 'prose_only_count' "$root/eval-report.md" \
    || { report_of "$root"; fail "$mutate: the count note must still be relayed"; }
  ok "$mutate -> exit 1, one finding ($code $gate), note still relayed"
}
check_drift drop-entry heading_without_entry gate2_5_surface
check_drift drop-heading entry_without_heading gate3_5_drift
check_drift bad-value unknown_verification_value gate5_docs

# ---------------------------------------------------------------------------
# Missing command file / missing helper -> one finding, not a crash
# ---------------------------------------------------------------------------
ROOT="$(new_root)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || { report_of "$ROOT"; fail "no-command: expected exit 1, got $rc"; }
grep -Fq 'commands/implement-story.md' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "no-command: finding must name the command file"; }
ok "missing commands/implement-story.md -> exit 1, one finding"

ROOT="$(new_root)"
write_fixture "$ROOT/commands/implement-story.md"
rm "$ROOT/scripts/verdict-provenance.py"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || { report_of "$ROOT"; fail "no-helper: expected exit 1, got $rc"; }
grep -Fq 'verdict-provenance.py' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "no-helper: finding must name the helper"; }
ok "missing helper -> exit 1, one finding"

# ---------------------------------------------------------------------------
# Registration and the not-yet-blocking contract (technical-spec §5)
# ---------------------------------------------------------------------------
awk '/^CHECKS=\(/{f=1} f && /^\)/{exit} f' "$EVAL" | grep -Fxq "  verdict-provenance" \
  || fail "verdict-provenance must be registered in CHECKS=(...)"
grep -q '^check_verdict_provenance()' "$EVAL" \
  || fail "check_verdict_provenance must be defined in scripts/eval.sh"
awk '/^check_verdict_provenance\(\)/,/^}/' "$EVAL" | grep -q '"\$helper" check ' \
  || fail "check_verdict_provenance must invoke \"\$helper\" check"
if awk '/^check_verdict_provenance\(\)/,/^}/' "$EVAL" | grep '"\$helper" check ' | grep -q -- '--prose-only-blocking'; then
  fail "check_verdict_provenance must not pass --prose-only-blocking yet (mechanization spec flips it)"
fi
ok "registration: verdict-provenance in CHECKS, function defined, count not blocking"

printf '\nAll %d verdict-provenance check assertions passed.\n' "$pass_count"
