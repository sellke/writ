#!/usr/bin/env bash
# Story 2 of 2026-09-25-jev-judgment-pilot: check_jev_judge registration,
# note-vs-finding split, and the no-network / no-key wiring. [AC-2.4]
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
EVAL="$REPO/scripts/eval.sh"

pass_count=0
fail() { printf 'FAIL: %s\n' "$1" >&2; exit 1; }
ok() { pass_count=$((pass_count + 1)); printf 'PASS: %s\n' "$1"; }

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

# Planted keys: the check must strip them before calling the helper.
FAKE_KEY="sk-jev-FAKE-eval-wiring-DO-NOT-PRINT"
export TYPESAFE_API_KEY="$FAKE_KEY" AI_GATEWAY_API_KEY="$FAKE_KEY" VERCEL_OIDC_TOKEN="$FAKE_KEY"
# A live attempt would hit a dead proxy and fail, never connect.
export HTTPS_PROXY="http://127.0.0.1:9" https_proxy="http://127.0.0.1:9"

write_stub() {
  printf '%s\n' "$2" > "$1"
  chmod +x "$1"
}

# Stub guard: refuse (exit 2 -> add_finding) if a key reaches the helper, or
# if probe runs without WRIT_JEV_REPLAY. A wiring regression fails the test.
STUB_GUARD='import os, sys
action = sys.argv[1] if len(sys.argv) > 1 else ""
for var in ("TYPESAFE_API_KEY", "AI_GATEWAY_API_KEY", "VERCEL_OIDC_TOKEN"):
    if os.environ.get(var):
        print("stub: key var %s reached helper" % var)
        raise SystemExit(2)
if action == "probe" and not os.environ.get("WRIT_JEV_REPLAY"):
    print("stub: probe without WRIT_JEV_REPLAY")
    raise SystemExit(2)'

new_root() {
  local root mode="${1:-pass}"
  root="$(mktemp -d)"
  TMP_ROOTS+=("$root")
  mkdir -p "$root/scripts/tests/fixtures/jev-replay/inputs" "$root/commands" "$root/.writ"
  cp "$EVAL" "$root/scripts/eval.sh"
  printf '{}\n' > "$root/scripts/tests/fixtures/jev-replay/inputs/state.json"
  printf '{}\n' > "$root/scripts/tests/fixtures/jev-replay/inputs/questions.json"
  case "$mode" in
    missing)
      ;;
    usage)
      write_stub "$root/scripts/jev-judge.py" "$(cat <<'PY'
#!/usr/bin/env python3
raise SystemExit(2)
PY
)"
      ;;
    probe-usage)
      write_stub "$root/scripts/jev-judge.py" "$(cat <<PY
#!/usr/bin/env python3
$STUB_GUARD
if action == "probe":
    print("error: bad probe args")
    raise SystemExit(2)
print("unverifiable")
print("reason: no_config_line")
print("jev-judge: unverifiable (no_config_line) backend=none")
PY
)"
      ;;
    fail)
      write_stub "$root/scripts/jev-judge.py" "$(cat <<PY
#!/usr/bin/env python3
$STUB_GUARD
print("fail")
print("reason: malformed_response")
print("jev-judge: fail (malformed_response) %s" % action)
raise SystemExit(1)
PY
)"
      ;;
    real)
      cp "$REPO/scripts/jev-judge.py" "$root/scripts/jev-judge.py"
      cp "$REPO/scripts/tests/fixtures/jev-replay/"*.json "$root/scripts/tests/fixtures/jev-replay/"
      cp "$REPO/scripts/tests/fixtures/jev-replay/inputs/"*.json \
        "$root/scripts/tests/fixtures/jev-replay/inputs/"
      ;;
    *)
      write_stub "$root/scripts/jev-judge.py" "$(cat <<PY
#!/usr/bin/env python3
$STUB_GUARD
print("unverifiable")
print("reason: no_config_line")
print("jev-judge: unverifiable (no_config_line) %s" % action)
raise SystemExit(0)
PY
)"
      ;;
  esac
  printf "%s" "$root"
}

run_check() {
  local root="$1" rc=0
  ( cd "$root" && bash scripts/eval.sh --check=jev-judge --report=eval-report.md >/dev/null 2>&1 ) || rc=$?
  printf "%s" "$rc"
}

assert_no_key() {
  if grep -Fq "$FAKE_KEY" "$1/eval-report.md"; then
    fail "$2: key value reached the eval report"
  fi
}

ROOT="$(new_root pass)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 0 ] || { cat "$ROOT/eval-report.md"; fail "pass: expected exit 0, got $rc"; }
grep -Fq 'NOTE [jev-judge]: jev-judge: unverifiable (no_config_line) status' "$ROOT/eval-report.md" \
  || { cat "$ROOT/eval-report.md"; fail "pass: status verdict must be a note"; }
grep -Fq 'NOTE [jev-judge]: jev-judge: unverifiable (no_config_line) probe' "$ROOT/eval-report.md" \
  || { cat "$ROOT/eval-report.md"; fail "pass: probe verdict must be a note"; }
grep -Fq -- '- Findings: 0' "$ROOT/eval-report.md" || fail "pass: must report Findings 0"
assert_no_key "$ROOT" pass
ok "unverifiable stub -> exit 0, add_note; keys stripped; probe under replay"

ROOT="$(new_root fail)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 0 ] || { cat "$ROOT/eval-report.md"; fail "fail: helper fail must not fail the check, got $rc"; }
grep -Fq 'NOTE [jev-judge]: fail' "$ROOT/eval-report.md" \
  || fail "fail: helper fail must be a note"
if grep -q '^FAIL' "$ROOT/eval-report.md"; then
  cat "$ROOT/eval-report.md"; fail "fail: must have zero findings"
fi
ok "helper fail stub -> exit 0, add_note only"

ROOT="$(new_root missing)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || fail "missing: expected exit 1, got $rc"
grep -Fq 'jev-judge helper is missing' "$ROOT/eval-report.md" \
  || fail "missing: must add_finding"
ok "missing helper -> exit 1, add_finding"

ROOT="$(new_root usage)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || fail "usage: expected exit 1, got $rc"
grep -Fq 'status refused' "$ROOT/eval-report.md" \
  || fail "usage: status exit 2 must add_finding"
ok "status exit 2 -> exit 1, add_finding"

ROOT="$(new_root probe-usage)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || fail "probe-usage: expected exit 1, got $rc"
grep -Fq 'probe refused' "$ROOT/eval-report.md" \
  || fail "probe-usage: probe exit 2 must add_finding"
ok "probe exit 2 -> exit 1, add_finding"

ROOT="$(new_root real)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 0 ] || { cat "$ROOT/eval-report.md"; fail "real: expected exit 0, got $rc"; }
grep -Fq 'NOTE [jev-judge]: jev-judge: unverifiable (no_config_line) backend=none' "$ROOT/eval-report.md" \
  || { cat "$ROOT/eval-report.md"; fail "real: disabled status must be a note"; }
grep -Fq 'NOTE [jev-judge]: jev-judge: pass (judged) backend=typesafe model=jev-1.13.0 input_tokens=280 attempts=1' \
  "$ROOT/eval-report.md" \
  || { cat "$ROOT/eval-report.md"; fail "real: replayed probe must be a note"; }
grep -Fq -- '- Findings: 0' "$ROOT/eval-report.md" || fail "real: must report Findings 0"
assert_no_key "$ROOT" real
ok "real helper, provider disabled -> Findings 0; probe served from replay"

awk '/^CHECKS=\(/{f=1} f && /^\)/{exit} f' "$EVAL" | grep -Fxq "  jev-judge" \
  || fail "jev-judge must be registered in CHECKS=(...)"
grep -q '^check_jev_judge()' "$EVAL" \
  || fail "check_jev_judge must be defined"
ok "registration: jev-judge in CHECKS"

printf '\nAll %d jev-judge eval-wiring assertions passed.\n' "$pass_count"
