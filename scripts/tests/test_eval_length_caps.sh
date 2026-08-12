#!/usr/bin/env bash
# Tests scripts/eval.sh check_length() — the three length caps it enforces.
#
# Primary contract (spec 2026-08-11-autonomy-gate-classes, Business Rule 2):
# the commands/_preamble.md cap was raised 80 -> 95 to fit the Autonomy Gate
# Classes section. A cap raised to fit content stops being a cap unless someone
# proves it still fires, so this test asserts BOTH sides of the boundary:
# 95 lines passes, 96 lines produces a blocking finding and a non-zero exit.
#
# Secondary contract (Business Rule 3): that spec owns exactly one constant in
# check_length(). The two neighbouring limits — commands/*.md and spec-lite.md
# at 100 — are owned by other Phase 10 work and must be byte-identical.
# Fixtures below assert both still speak with their own numbers.
#
# The commands/*.md limit moved on 2026-08-12, by its OWN owner
# (2026-08-12-governor-enforcement Story 3) and not by a stray edit from this
# side: 2000 -> 400, and add_finding -> add_note. ADR-021's amendment makes an
# absolute byte budget the binding instrument and retains the line cap as a
# "secondary, non-binding tripwire". Scenario 3 below asserts the new posture,
# and it is still the ownership tripwire it always was — the _preamble cap at
# 95 sits eleven lines away and must never move with it.
#
# Tripwire (Business Rule 4): file_has_exemption() short-circuits the whole
# check, so an `eval-exempt: length` marker in commands/_preamble.md would
# remove the cap rather than resize it, silently. The last two scenarios
# demonstrate the bypass on a fixture and assert the real file has no marker.
#
# Harness: scripts/eval.sh derives PROJECT_ROOT from its own directory
# (scripts/eval.sh:13), so copying it into a temp `scripts/` dir alongside
# synthetic content exercises the real check against a synthetic tree — no new
# flag, no environment variable, no mutation of the real repository.
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

TMP_ROOTS=()
cleanup() {
  local rc=$? root
  for root in "${TMP_ROOTS[@]:-}"; do
    [ -n "$root" ] || continue
    rm -rf "$root"
  done
  # Preserve the real exit status: an EXIT trap whose last command fails would
  # otherwise turn an all-green run into a non-zero exit.
  return "$rc"
}
trap cleanup EXIT

# usage: new_root -> prints a fresh temp project root with scripts/eval.sh in it
new_root() {
  local root
  root="$(mktemp -d)"
  TMP_ROOTS+=("$root")
  mkdir -p "$root/scripts" "$root/commands" "$root/.writ/state"
  cp "$EVAL" "$root/scripts/eval.sh"
  printf "%s" "$root"
}

# usage: gen_lines <path> <n> -- writes exactly <n> newline-terminated lines
gen_lines() {
  local path="$1" n="$2" i
  : > "$path"
  for ((i = 1; i <= n; i++)); do
    printf 'line %d\n' "$i" >> "$path"
  done
  # Guard the boundary itself: eval.sh's line_count() helper must agree with
  # wc -l, or every 95-vs-96 assertion below is off by one and means nothing.
  local awk_count wc_count
  awk_count="$(awk 'END { print NR }' "$path")"
  wc_count="$(wc -l < "$path" | tr -d ' ')"
  [ "$awk_count" -eq "$n" ] || fail "fixture $path: awk counted $awk_count, wanted $n"
  [ "$wc_count" -eq "$n" ] || fail "fixture $path: wc -l counted $wc_count, wanted $n"
}

# usage: run_length <root> -> prints exit code; report left at <root>/eval-report.md
run_length() {
  local root="$1" rc=0
  ( cd "$root" && bash scripts/eval.sh --check=length --report=eval-report.md >/dev/null 2>&1 ) || rc=$?
  printf "%s" "$rc"
}

report_of() {
  cat "$1/eval-report.md"
}

# ---------------------------------------------------------------------------
# Scenario 1: commands/_preamble.md at exactly 95 lines -> legal.
# The test is `-gt`, so 95 is the last passing value. This is the side of the
# boundary the cap raise exists to permit.
# ---------------------------------------------------------------------------
ROOT95="$(new_root)"
gen_lines "$ROOT95/commands/_preamble.md" 95
RC="$(run_length "$ROOT95")"
[ "$RC" -eq 0 ] || { report_of "$ROOT95"; fail "95-line _preamble.md must pass --check=length (exit 0), got exit $RC"; }
if grep -q '_preamble.md`:' "$ROOT95/eval-report.md"; then
  report_of "$ROOT95"
  fail "95-line _preamble.md must produce no _preamble finding"
fi
ok "_preamble cap: 95 lines -> exit 0, no finding (95 is legal; the test is -gt)"

# ---------------------------------------------------------------------------
# Scenario 2: commands/_preamble.md at 96 lines -> blocking finding.
# This is the scenario that proves the cap still binds. Asserting the finding
# TEXT and not just the exit code matters: --check=length runs three separate
# limits, so a bare exit-code assertion cannot distinguish "the preamble cap
# fired" from "some other limit fired on a stray fixture".
# ---------------------------------------------------------------------------
ROOT96="$(new_root)"
gen_lines "$ROOT96/commands/_preamble.md" 96
RC="$(run_length "$ROOT96")"
[ "$RC" -eq 1 ] || { report_of "$ROOT96"; fail "96-line _preamble.md must fail --check=length (exit 1), got exit $RC"; }
grep -Fq '`commands/_preamble.md`: 96 lines (limit 95).' "$ROOT96/eval-report.md" \
  || { report_of "$ROOT96"; fail 'report must contain: `commands/_preamble.md`: 96 lines (limit 95).'; }
grep -q '^FAIL' "$ROOT96/eval-report.md" \
  || { report_of "$ROOT96"; fail "the _preamble cap must be a blocking finding, not a non-blocking note"; }
ok "_preamble cap: 96 lines -> exit 1 with a blocking \`limit 95\` finding (the cap still binds)"

# ---------------------------------------------------------------------------
# Scenario 3: the commands/*.md tripwire is 400 and NON-BINDING.
#
# ADR-021, amended 2026-08-12: the binding instrument is COMMAND_BYTE_BUDGET
# (24,960 bytes) in scripts/eval-leanness.py; the line cap is retained only as
# a secondary tripwire. So a 401-line command file must produce a NOTE and exit
# 0 — never a blocking finding. Asserting the note text and not just the exit
# code matters: --check=length runs three separate limits, and a bare exit-code
# assertion cannot distinguish "the command tripwire stayed quiet" from "it
# fired as a note".
#
# The retired 2000 is asserted absent. It was 2.02x the largest command in the
# tree (989 lines) and could never bind — ADR-021 reason 1 — and leaving it
# beside a real byte budget taught readers that lines are a governed quantity.
# ---------------------------------------------------------------------------
ROOTCMD="$(new_root)"
gen_lines "$ROOTCMD/commands/example.md" 401
RC="$(run_length "$ROOTCMD")"
[ "$RC" -eq 0 ] || { report_of "$ROOTCMD"; fail "401-line command file must NOT fail --check=length (the tripwire is non-binding), got exit $RC"; }
grep -Fq 'NOTE [commands/example.md]: 401 lines (secondary tripwire 400, non-binding).' "$ROOTCMD/eval-report.md" \
  || { report_of "$ROOTCMD"; fail 'expected a non-blocking NOTE: `commands/example.md`: 401 lines (secondary tripwire 400, non-binding).'; }
grep -Fq 'COMMAND_BYTE_BUDGET' "$ROOTCMD/eval-report.md" \
  || { report_of "$ROOTCMD"; fail 'the tripwire must point the reader at the limit that actually binds (COMMAND_BYTE_BUDGET)'; }
grep -q '^FAIL' "$ROOTCMD/eval-report.md" \
  && { report_of "$ROOTCMD"; fail "the command tripwire must be a non-blocking note, not a blocking finding"; }
ok "command tripwire: 401 lines -> exit 0 with a non-binding NOTE naming COMMAND_BYTE_BUDGET"

# ---------------------------------------------------------------------------
# Scenario 3b: 400 lines is legal. The test is `-gt`, and the boundary is
# asserted rather than left to a reading of the code.
# ---------------------------------------------------------------------------
ROOT400="$(new_root)"
gen_lines "$ROOT400/commands/example.md" 400
RC="$(run_length "$ROOT400")"
[ "$RC" -eq 0 ] || { report_of "$ROOT400"; fail "400-line command file must pass --check=length, got exit $RC"; }
if grep -q 'commands/example.md' "$ROOT400/eval-report.md"; then
  report_of "$ROOT400"
  fail "400-line command file must produce no note (400 is legal; the test is -gt)"
fi
ok "command tripwire: 400 lines -> exit 0, no note (400 is legal; the test is -gt)"

# ---------------------------------------------------------------------------
# Scenario 3c: the retired 2000-line limit is gone from the source, in any
# form. Leaving it in place beside a real byte budget teaches a reader that
# line count is a governed quantity when it is not.
# ---------------------------------------------------------------------------
if grep -Eq 'gt[[:space:]]+2000' "$EVAL"; then
  fail "scripts/eval.sh still holds a 2000-line command limit — ADR-021's amendment retired it"
fi
ok "retired: no 2000-line command limit survives in scripts/eval.sh"

# ---------------------------------------------------------------------------
# Scenario 4 (ownership boundary): the spec-lite.md limit belongs to nobody in
# this spec. A 101-line spec-lite.md must still report `limit 100`.
#
# spec_lite_files() enumerates via `git ls-files -co --exclude-standard`, so the
# fixture root has to be a git repo. The file stays untracked — `-o` covers it,
# so no commit (and no git identity) is required.
# ---------------------------------------------------------------------------
ROOTLITE="$(new_root)"
git -C "$ROOTLITE" init -q 2>/dev/null || fail "could not git init the spec-lite fixture root"
mkdir -p "$ROOTLITE/.writ/specs/2026-01-01-demo"
gen_lines "$ROOTLITE/.writ/specs/2026-01-01-demo/spec-lite.md" 101
RC="$(run_length "$ROOTLITE")"
[ "$RC" -eq 1 ] || { report_of "$ROOTLITE"; fail "101-line spec-lite.md must still fail --check=length, got exit $RC"; }
grep -Fq '101 lines (limit 100).' "$ROOTLITE/eval-report.md" \
  || { report_of "$ROOTLITE"; fail 'adjacent spec-lite limit changed — expected `101 lines (limit 100).`'; }
ok "ownership boundary: spec-lite.md limit untouched (101 lines -> \`limit 100\`)"

# ---------------------------------------------------------------------------
# Scenario 5 (the exemption trap, demonstrated): an `eval-exempt: length`
# marker does not resize the cap — it deletes it. A 96-line preamble carrying
# one passes silently, with no finding and no note. This scenario exists to
# make the bypass visible so Scenario 6's tripwire is obviously load-bearing.
# ---------------------------------------------------------------------------
ROOTEX="$(new_root)"
gen_lines "$ROOTEX/commands/_preamble.md" 95
printf '<!-- eval-exempt: length -->\n' >> "$ROOTEX/commands/_preamble.md"
[ "$(awk 'END { print NR }' "$ROOTEX/commands/_preamble.md")" -eq 96 ] \
  || fail "exemption fixture should be 96 lines"
RC="$(run_length "$ROOTEX")"
[ "$RC" -eq 0 ] || { report_of "$ROOTEX"; fail "exempted 96-line _preamble.md unexpectedly failed (harness assumption wrong)"; }
if grep -q '_preamble.md`:' "$ROOTEX/eval-report.md"; then
  report_of "$ROOTEX"
  fail "exempted _preamble.md should produce no finding"
fi
ok "exemption trap: \`eval-exempt: length\` skips the check entirely (removes the cap, not resizes it)"

# ---------------------------------------------------------------------------
# Scenario 6 (the tripwire): the REAL commands/_preamble.md must carry no
# exemption marker. Business Rule 4 of 2026-08-11-autonomy-gate-classes bans it
# permanently — Scenario 5 shows why. This is the assertion that would catch a
# future "fix" for a preamble that outgrows 95 again.
# ---------------------------------------------------------------------------
REAL_PREAMBLE="$REPO/commands/_preamble.md"
[ -f "$REAL_PREAMBLE" ] || fail "commands/_preamble.md is missing from the repository"
if grep -q 'eval-exempt:' "$REAL_PREAMBLE"; then
  fail "commands/_preamble.md carries an eval-exempt marker — the cap was bypassed, not resized (Business Rule 4)"
fi
ok "tripwire: the real commands/_preamble.md carries no eval-exempt marker"

# ---------------------------------------------------------------------------
# Scenario 7: the real commands/_preamble.md is within its own cap, and within
# the budget the cap was derived from (79 baseline + 14 section + 2 reserve).
# ---------------------------------------------------------------------------
REAL_COUNT="$(awk 'END { print NR }' "$REAL_PREAMBLE")"
[ "$REAL_COUNT" -le 95 ] \
  || fail "commands/_preamble.md is $REAL_COUNT lines, over the 95-line cap — cut prose, do not raise the cap (Business Rule 1)"
ok "real commands/_preamble.md is $REAL_COUNT lines, within the 95-line cap"

printf '\nAll %d length-cap assertions passed.\n' "$pass_count"
