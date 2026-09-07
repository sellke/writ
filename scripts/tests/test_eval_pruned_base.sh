#!/usr/bin/env bash
# Tests check_pruned_base in scripts/eval.sh (spec
# 2026-09-07-phase11-stage2-prune-the-base, Story 1, AC-1.4 / AC-1.5).
#
# Harness: copy eval.sh and prune-ledger.py into a temp scripts/ so
# PROJECT_ROOT is the fixture tree, `git init` the fixture and commit the two
# base files once, then point the check at that commit through
# WRIT_PRUNE_BASE_COMMIT (the real pin, cf84742, does not exist in a fixture).
# No mutation of the real repository.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
EVAL="$REPO/scripts/eval.sh"
HELPER="$REPO/scripts/prune-ledger.py"
LEDGER_REL=".writ/decision-records/pruned-instructions-ledger.md"

export GIT_AUTHOR_NAME=Test GIT_AUTHOR_EMAIL=test@example.com
export GIT_COMMITTER_NAME=Test GIT_COMMITTER_EMAIL=test@example.com

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

# A fixture root with both base files committed; prints "<root>".
new_root() {
  local root
  root="$(mktemp -d)"
  TMP_ROOTS+=("$root")
  mkdir -p "$root/scripts" "$root/commands"
  cp "$EVAL" "$root/scripts/eval.sh"
  cp "$HELPER" "$root/scripts/prune-ledger.py"
  printf '# System\n\n## Identity\nKeep this line.\nCut this line.\n' > "$root/system-instructions.md"
  printf '# Preamble\n\n## Tools\nRead the spec first.\n' > "$root/commands/_preamble.md"
  git -C "$root" init -q
  git -C "$root" -c commit.gpgsign=false add -A
  git -C "$root" -c commit.gpgsign=false commit -q -m base
  printf "%s" "$root"
}

base_of() {
  git -C "$1" rev-parse HEAD
}

write_ledger_header() {
  mkdir -p "$1/.writ/decision-records"
  printf '# Pruned Instructions Ledger\n\n| Date | File | Class | Reason | Text |\n|---|---|---|---|---|\n' > "$1/$LEDGER_REL"
}

run_check() {
  local root="$1" rc=0
  ( cd "$root" && WRIT_PRUNE_BASE_COMMIT="$(base_of "$root")" \
      bash scripts/eval.sh --check=pruned-base --report=eval-report.md >/dev/null 2>&1 ) || rc=$?
  printf "%s" "$rc"
}

report_of() {
  cat "$1/eval-report.md" 2>/dev/null || printf '(no eval-report.md written)\n'
}

# ---------------------------------------------------------------------------
# AC-1.5: no removals, empty ledger -> PASS, summary + ledger_missing + over_cap as notes, exit 0
# ---------------------------------------------------------------------------
ROOT="$(new_root)"
write_ledger_header "$ROOT"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 0 ] || { report_of "$ROOT"; fail "empty ledger: expected exit 0, got $rc"; }
grep -q '^PASS' "$ROOT/eval-report.md" || { report_of "$ROOT"; fail "empty ledger: report must say PASS"; }
grep -Fq 'ledger_missing' "$ROOT/eval-report.md" || { report_of "$ROOT"; fail "empty ledger: ledger_missing must surface as a note"; }
grep -Eq '^- NOTE \[pruned-base\]: base: [0-9]+ bytes \(cap 10000\), ledger: 0 rows, removed: 0, re-added: 0$' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "empty ledger: summary line must surface as a note"; }
ok "no removals, empty ledger -> PASS with summary and ledger_missing notes, exit 0"

# ---------------------------------------------------------------------------
# AC-1.5: no ledger file at all -> still a note, not a finding
# ---------------------------------------------------------------------------
ROOT="$(new_root)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 0 ] || { report_of "$ROOT"; fail "no ledger file: expected exit 0, got $rc"; }
grep -Fq 'ledger_missing' "$ROOT/eval-report.md" || { report_of "$ROOT"; fail "no ledger file: ledger_missing note expected"; }
ok "no ledger file -> note, exit 0"

# ---------------------------------------------------------------------------
# AC-1.5: a removal with no row -> one finding naming file and text, exit 1
# ---------------------------------------------------------------------------
ROOT="$(new_root)"
write_ledger_header "$ROOT"
printf '# System\n\n## Identity\nKeep this line.\n' > "$ROOT/system-instructions.md"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || { report_of "$ROOT"; fail "removal without row: expected exit 1, got $rc"; }
grep -q '^FAIL (1 finding' "$ROOT/eval-report.md" || { report_of "$ROOT"; fail "removal without row: expected exactly one finding"; }
grep -Fq 'removed_not_in_ledger' "$ROOT/eval-report.md" || { report_of "$ROOT"; fail "removal without row: finding code missing"; }
grep -Fq 'system-instructions.md: Cut this line.' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "removal without row: finding must name file and text"; }
ok "removal without row -> one finding naming file and text, exit 1"

# ---------------------------------------------------------------------------
# AC-1.5: the same removal with its row -> PASS, exit 0
# ---------------------------------------------------------------------------
ROOT="$(new_root)"
write_ledger_header "$ROOT"
printf '# System\n\n## Identity\nKeep this line.\n' > "$ROOT/system-instructions.md"
printf '| 2026-09-08 | system-instructions.md | behavior-request | models do it | Cut this line. |\n' >> "$ROOT/$LEDGER_REL"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 0 ] || { report_of "$ROOT"; fail "removal with row: expected exit 0, got $rc"; }
grep -q '^PASS' "$ROOT/eval-report.md" || { report_of "$ROOT"; fail "removal with row: report must say PASS"; }
ok "removal with row -> PASS, exit 0"

# ---------------------------------------------------------------------------
# AC-1.4: over cap is a note without the marker, a finding with it
# ---------------------------------------------------------------------------
# The fixture base is far under 10,000 bytes; pad system-instructions.md past
# the cap by appending lines (additions are not removals).
ROOT="$(new_root)"
write_ledger_header "$ROOT"
python3 -c 'import sys; open(sys.argv[1], "a").write("pad line\n" * 1200)' "$ROOT/system-instructions.md"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 0 ] || { report_of "$ROOT"; fail "over cap, no marker: expected exit 0, got $rc"; }
grep -Fq 'over_cap' "$ROOT/eval-report.md" || { report_of "$ROOT"; fail "over cap, no marker: over_cap note expected"; }
grep -q '^PASS' "$ROOT/eval-report.md" || { report_of "$ROOT"; fail "over cap, no marker: report must say PASS"; }
ok "over cap without marker -> note, exit 0"

printf '\n<!-- cap: blocking -->\n' >> "$ROOT/$LEDGER_REL"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || { report_of "$ROOT"; fail "over cap, marker: expected exit 1, got $rc"; }
grep -q '^FAIL (1 finding' "$ROOT/eval-report.md" || { report_of "$ROOT"; fail "over cap, marker: expected exactly one finding"; }
grep -Fq 'over_cap' "$ROOT/eval-report.md" || { report_of "$ROOT"; fail "over cap, marker: over_cap finding expected"; }
ok "over cap with <!-- cap: blocking --> marker -> finding, exit 1"

# ---------------------------------------------------------------------------
# Exit 2 from the helper (bad base commit) -> one finding carrying git's message
# ---------------------------------------------------------------------------
ROOT="$(new_root)"
write_ledger_header "$ROOT"
rc=0
( cd "$ROOT" && WRIT_PRUNE_BASE_COMMIT=nosuchrev bash scripts/eval.sh --check=pruned-base --report=eval-report.md >/dev/null 2>&1 ) || rc=$?
[ "$rc" -eq 1 ] || { report_of "$ROOT"; fail "bad base commit: expected exit 1, got $rc"; }
grep -q '^FAIL (1 finding' "$ROOT/eval-report.md" || { report_of "$ROOT"; fail "bad base commit: expected exactly one finding"; }
grep -Fq 'bad revision' "$ROOT/eval-report.md" || { report_of "$ROOT"; fail "bad base commit: finding must carry git's own message"; }
ok "helper exit 2 -> one finding carrying git's message"

# ---------------------------------------------------------------------------
# Missing helper -> one finding
# ---------------------------------------------------------------------------
ROOT="$(new_root)"
rm "$ROOT/scripts/prune-ledger.py"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || { report_of "$ROOT"; fail "missing helper: expected exit 1, got $rc"; }
grep -Fq 'scripts/prune-ledger.py' "$ROOT/eval-report.md" || { report_of "$ROOT"; fail "missing helper: finding must name the helper"; }
ok "missing helper -> one finding"

awk '/^CHECKS=\(/{f=1} f && /^\)/{exit} f' "$EVAL" | grep -Fxq "  pruned-base" \
  || fail "pruned-base must be registered in CHECKS=(...)"
grep -q '^check_pruned_base()' "$EVAL" \
  || fail "check_pruned_base must be defined in scripts/eval.sh"
ok "registration: pruned-base in CHECKS and check_pruned_base exists"

printf '\nAll %d pruned-base check assertions passed.\n' "$pass_count"
