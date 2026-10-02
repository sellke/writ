#!/usr/bin/env bash
# Spec 2026-10-01-behavioral-verification, Story 5: check_app_verify registration,
# the real fixture run on this repo, and a stub app-verify.py that always exits 0
# (so the fail and refuse expectations break) yielding findings and exit 1.
# [AC-5.4, AC-5.5]
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
# Authenticity pin: test-integrity.py extracts JS-style from '…' specifiers,
# not shell paths. This test's unit under test is the script it runs.
# from "../eval.sh"
EVAL="$REPO/scripts/eval.sh"

fail() { printf 'FAIL: %s\n' "$1" >&2; exit 1; }
ok() { printf 'PASS: %s\n' "$1"; }

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

awk '/^CHECKS=\(/{f=1} f&&/^\)/{f=0} f' "$EVAL" | grep -qx '  app-verify' \
  || fail "app-verify must be registered in CHECKS=(...)"
grep -q '^check_app_verify() {' "$EVAL" || fail "check_app_verify() must be defined"
ok "registration: app-verify in CHECKS, check_app_verify defined"

report_of() { cat "$1/eval-report.md" 2>/dev/null || true; }
run_check() {
  local root="$1" rc=0
  ( cd "$root" && bash scripts/eval.sh --check=app-verify --report=eval-report.md >/dev/null 2>&1 ) || rc=$?
  printf "%s" "$rc"
}

# Real repo: the fixture runs end to end. Report goes to a temp file, not the repo.
REAL_REPORT="$(mktemp)"
TMP_ROOTS+=("$REAL_REPORT")
rc=0
( cd "$REPO" && bash scripts/eval.sh --check=app-verify --report="$REAL_REPORT" >/dev/null 2>&1 ) || rc=$?
[ "$rc" -eq 0 ] || { cat "$REAL_REPORT"; fail "real repo: expected exit 0, got $rc"; }
! grep -q '^FAIL' "$REAL_REPORT" || { cat "$REAL_REPORT"; fail "real repo: no FAIL line expected"; }
grep -Fq 'NOTE [app-verify]:' "$REAL_REPORT" || { cat "$REAL_REPORT"; fail "real repo: expected the app-verify note"; }
ok "real repo: --check=app-verify exits 0 with no FAIL line"

ROOT="$(mktemp -d)"
TMP_ROOTS+=("$ROOT")
mkdir -p "$ROOT/scripts/tests/fixtures" "$ROOT/.writ/docs"
cp "$EVAL" "$ROOT/scripts/eval.sh"
cp "$REPO/scripts/exit-criteria.py" "$ROOT/scripts/exit-criteria.py"
cp -R "$REPO/scripts/tests/fixtures/app-verify" "$ROOT/scripts/tests/fixtures/app-verify"
cp "$REPO/.writ/docs/exit-criteria-classification.md" "$ROOT/.writ/docs/"
printf '%s\n' '#!/usr/bin/env python3' 'print("app-verify: 1/1 pass — stub")' 'raise SystemExit(0)' \
  > "$ROOT/scripts/app-verify.py"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || { report_of "$ROOT"; fail "stub: expected exit 1, got $rc"; }
grep -Fq 'app-verify:recipe-fail' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "stub: the fail recipe exiting 0 must be a finding"; }
grep -Fq 'app-verify:recipe-safety-refused' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "stub: the refused recipe exiting 0 must be a finding"; }
ok "stub app-verify.py that always exits 0 -> add_finding, exit 1"

# A stub honouring the exit-code contract but breaking one safety rule each.
write_contract_stub() {
  cat > "$ROOT/scripts/app-verify.py" <<PY
#!/usr/bin/env python3
import json, os, subprocess, sys
from pathlib import Path
args = sys.argv
recipe = args[args.index("--recipe") + 1]
spec = Path(args[args.index("--spec") + 1])
label = args[args.index("--run-label") + 1]
mode = "$1"
if "recipe-pass" in recipe:
    out = spec / "evidence" / label / "home"
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps({"verdict": "pass"}))
    if mode == "orphan":
        child = subprocess.Popen(["sleep", "30"], start_new_session=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        Path(os.environ["APP_VERIFY_FIXTURE_PIDFILE"]).write_text(str(child.pid))
    print("app-verify: 1/1 pass"); sys.exit(0)
if "recipe-fail" in recipe:
    print("app-verify: 1/2 fail"); sys.exit(1)
if mode == "launch":
    (spec / "evidence" / label / "_launch").mkdir(parents=True, exist_ok=True)
print("app-verify: refused (APP_VERIFY_FIXTURE_DB matches a Never pattern)"); sys.exit(2)
PY
}

write_contract_stub launch
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || { report_of "$ROOT"; fail "launch stub: expected exit 1, got $rc"; }
grep -Fq 'a refused run created _launch/' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "launch stub: a refused run with _launch/ must be a finding"; }
grep -q '^FAIL (1 finding' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "launch stub: exactly one finding expected"; }
ok "refused run that created _launch/ -> one finding"

write_contract_stub orphan
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || { report_of "$ROOT"; fail "orphan stub: expected exit 1, got $rc"; }
grep -Fq 'survived the run' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "orphan stub: a surviving process must be a finding"; }
ok "process surviving a run -> finding (and the check kills it)"

rm "$ROOT/scripts/app-verify.py"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || { report_of "$ROOT"; fail "missing helper: expected exit 1, got $rc"; }
grep -Fq 'scripts/app-verify.py' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "missing helper must be named in a finding"; }
ok "missing app-verify.py -> finding, exit 1"

echo "All app-verify eval check assertions passed."
