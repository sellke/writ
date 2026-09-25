#!/usr/bin/env bash
# Story 2: create-spec Step 2.6c + verify-spec 3g name spec-analyze.py
# and treat script fail as notes, not a failed command contract. [AC-2.1, AC-2.3, AC-2.5]
# Also pins the 2026-09-25-jev-judgment-pilot Story 3 Jev cascade wiring.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
CREATE="$REPO/commands/create-spec.md"
VERIFY="$REPO/commands/verify-spec.md"

fail() { printf 'FAIL: %s\n' "$1" >&2; exit 1; }
ok() { printf 'PASS: %s\n' "$1"; }

grep -q '#### Step 2.6c: Spec analysis' "$CREATE" \
  || fail "create-spec.md must define Step 2.6c"
awk '/^#### Step 2.6b:/,/^#### Step 2.6c:/' "$CREATE" | grep -q '#### Step 2.6b:' \
  || fail "Step 2.6b must still exist (not renumbered)"
# 2.6c comes after 2.6b in file order
python3 - "$CREATE" <<'PY' || fail "Step 2.6c must follow Step 2.6b"
import sys
text = open(sys.argv[1], encoding="utf-8").read()
b = text.find("#### Step 2.6b:")
c = text.find("#### Step 2.6c:")
a = text.find("#### Step 2.6a:")
assert a != -1 and b != -1 and c != -1 and a < b < c, (a, b, c)
PY
grep -F 'python3 scripts/spec-analyze.py check' "$CREATE" \
  || fail "create-spec.md Step 2.6c must invoke spec-analyze.py check"
grep -q 'ac-trace.py' "$CREATE" \
  || fail "create-spec.md must still name ac-trace (Step 2.6a)"
ok "create-spec Step 2.6c after 2.6b; script named; 2.6a ac-trace kept"

grep -q '**3g. Spec analysis' "$VERIFY" || grep -q '3g. Spec analysis' "$VERIFY" \
  || fail "verify-spec.md must add advisory check 3g"
grep -F 'python3 scripts/spec-analyze.py check' "$VERIFY" \
  || fail "verify-spec.md 3g must invoke spec-analyze.py check"
# 3e/3f still name ac-trace
awk '/\*\*3e\./,/\*\*3f\./' "$VERIFY" | grep -q 'ac-trace.py' \
  || fail "verify-spec 3e must still name ac-trace.py"
grep -q 'does not' "$VERIFY" && grep -q 'fail this check' "$VERIFY" \
  || fail "verify-spec 3g must say a script fail does not fail the check"
ok "verify-spec 3g advisory; 3e/3f still ac-trace"

# Notes-only: Step 2.9 and 3g both say continue / do not fail the report
grep -A8 '#### Step 2.9' "$CREATE" | grep -qi 'never fail' \
  || fail "Step 2.9 must say analysis notes never fail the review"
ok "script fail is notes-only for the command contract"

# Story 3 of 2026-09-25-jev-judgment-pilot: the Jev cascade. [AC-3.3, AC-3.4, AC-3.5]
STEP_26C="$(awk '/^#### Step 2.6c:/{f=1} /^#### Step 2.7:/{f=0} f' "$CREATE")"
printf '%s\n' "$STEP_26C" | grep -Fq 'python3 scripts/jev-judge.py status' \
  || fail "Step 2.6c must gate Jev on jev-judge.py status"
printf '%s\n' "$STEP_26C" | grep -Fq 'prints `pass`' \
  || fail "Step 2.6c must run spec-findings only when status prints pass"
printf '%s\n' "$STEP_26C" \
  | grep -Fq 'python3 scripts/jev-judge.py spec-findings --spec .writ/specs/<folder> --out .writ/state/spec-analyze-<run>.json' \
  || fail "Step 2.6c must call spec-findings with --spec and --out"
printf '%s\n' "$STEP_26C" | grep -Fq '<out>.escalate.json' \
  || fail "Step 2.6c must read the escalation list"
printf '%s\n' "$STEP_26C" | grep -Fq 'only over the stories listed in `<out>.escalate.json`' \
  || fail "Step 2.6c must limit the orchestrator pass to escalated stories"
printf '%s\n' "$STEP_26C" | grep -Fq 'merge' \
  || fail "Step 2.6c must merge Jev and orchestrator findings"
printf '%s\n' "$STEP_26C" | grep -Fq 'Otherwise' \
  && printf '%s\n' "$STEP_26C" | grep -Fq 'over every story' \
  || fail "Step 2.6c must fall back to the full pass when Jev is off or fails"
python3 - "$CREATE" <<'PY' || fail "the Jev sub-step must sit inside 2.6c, before the LLM-pass item"
import sys
text = open(sys.argv[1], encoding="utf-8").read()
c = text.find("#### Step 2.6c:")
jev = text.find("python3 scripts/jev-judge.py status", c)
llm = text.find("1. **LLM pass", c)
nxt = text.find("#### Step 2.7:", c)
assert -1 < c < jev < llm < nxt, (c, jev, llm, nxt)
PY
printf '%s\n' "$STEP_26C" | grep -Fq 'Any `jev-judge.py` or `spec-analyze.py` `fail`' \
  || fail "Step 2.6c's notes-only rule must cover jev-judge.py outcomes too"
printf '%s\n' "$STEP_26C" | grep -Fq 'does **not** open an AskQuestion gate' \
  || fail "Step 2.6c must still say no analysis outcome opens an AskQuestion gate"
awk '/^#### Step 2.9:/{f=1} /^## Completion/{f=0} f' "$CREATE" | grep -Fq '`jev:' \
  || fail "Step 2.9 must carry a jev: note line"
ok "create-spec 2.6c: status-gated spec-findings, escalated-only pass, full-pass fallback, jev: note"

STEP_3G="$(awk '/\*\*3g\. Spec analysis/{f=1} /^#### Check 4:/{f=0} f' "$VERIFY")"
printf '%s\n' "$STEP_3G" | grep -Fq 'python3 scripts/jev-judge.py status' \
  || fail "verify-spec 3g must gate Jev on jev-judge.py status"
printf '%s\n' "$STEP_3G" | grep -Fq 'spec-findings --spec <folder> --out <json>' \
  || fail "verify-spec 3g must call spec-findings"
printf '%s\n' "$STEP_3G" | grep -Fq '<json>.escalate.json' \
  || fail "verify-spec 3g must read the escalation list"
printf '%s\n' "$STEP_3G" | grep -Fq 'does not' \
  && printf '%s\n' "$STEP_3G" | grep -Fq 'fail this check, the 3a–3f status cell, or the verify report' \
  || fail "verify-spec 3g results must stay notes"
ok "verify-spec 3g: same Jev conditional; results stay notes"

printf '\nAll spec-analyze command-hook assertions passed.\n'
