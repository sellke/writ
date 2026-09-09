#!/usr/bin/env bash
# Story 2: create-spec Step 2.6c + verify-spec 3g name spec-analyze.py
# and treat script fail as notes, not a failed command contract. [AC-2.1, AC-2.3, AC-2.5]
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

printf '\nAll spec-analyze command-hook assertions passed.\n'
