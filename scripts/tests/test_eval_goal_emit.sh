#!/usr/bin/env bash
# Story 3: check_goal_emit registration and note-vs-finding split.
# [AC-3.2, AC-3.3]
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

write_stub() {
  printf '%s\n' "$2" > "$1"
  chmod +x "$1"
}

new_root() {
  local root mode="${1:-pass}"
  root="$(mktemp -d)"
  TMP_ROOTS+=("$root")
  mkdir -p "$root/scripts" "$root/commands" "$root/.writ/issues/goals"
  cp "$EVAL" "$root/scripts/eval.sh"
  printf '# card\n> **loop:** yes\n' > "$root/.writ/issues/goals/demo.md"
  case "$mode" in
    missing)
      ;;
    usage)
      write_stub "$root/scripts/goal-emit.py" "$(cat <<'PY'
#!/usr/bin/env python3
raise SystemExit(2)
PY
)"
      ;;
    fail)
      write_stub "$root/scripts/goal-emit.py" "$(cat <<'PY'
#!/usr/bin/env python3
print("fail")
print("reason: malformed_card")
print("goal-emit: fail (fixture)")
raise SystemExit(1)
PY
)"
      ;;
    unverifiable)
      write_stub "$root/scripts/goal-emit.py" "$(cat <<'PY'
#!/usr/bin/env python3
print("unverifiable")
print("reason: loop_no")
print("goal-emit: unverifiable (fixture)")
raise SystemExit(0)
PY
)"
      ;;
    *)
      write_stub "$root/scripts/goal-emit.py" "$(cat <<'PY'
#!/usr/bin/env python3
print("pass")
print("goal-emit: pass (fixture)")
raise SystemExit(0)
PY
)"
      ;;
  esac
  printf "%s" "$root"
}

run_check() {
  local root="$1" rc=0
  ( cd "$root" && bash scripts/eval.sh --check=goal-emit --report=eval-report.md >/dev/null 2>&1 ) || rc=$?
  printf "%s" "$rc"
}

ROOT="$(new_root pass)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 0 ] || { cat "$ROOT/eval-report.md"; fail "pass: expected exit 0, got $rc"; }
grep -Fq 'NOTE [goal-emit]:' "$ROOT/eval-report.md" \
  || fail "pass: emit verdict must be a note"
ok "pass stub -> exit 0, add_note"

ROOT="$(new_root fail)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 0 ] || { cat "$ROOT/eval-report.md"; fail "fail: emit fail must not fail the check, got $rc"; }
grep -Fq 'NOTE [goal-emit]: fail' "$ROOT/eval-report.md" \
  || fail "fail: emit fail must be a note"
if grep -q '^FAIL' "$ROOT/eval-report.md"; then
  cat "$ROOT/eval-report.md"; fail "fail: must have zero findings"
fi
ok "emit fail stub -> exit 0, add_note only"

ROOT="$(new_root unverifiable)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 0 ] || fail "unverifiable: expected exit 0, got $rc"
grep -Fq 'NOTE [goal-emit]: unverifiable' "$ROOT/eval-report.md" \
  || fail "unverifiable: must be a note"
ok "unverifiable stub -> exit 0, add_note"

ROOT="$(new_root missing)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || fail "missing: expected exit 1, got $rc"
grep -Fq 'goal-emit helper is missing' "$ROOT/eval-report.md" \
  || fail "missing: must add_finding"
ok "missing helper -> exit 1, add_finding"

ROOT="$(new_root usage)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || fail "usage: expected exit 1, got $rc"
grep -Fq 'refused' "$ROOT/eval-report.md" \
  || fail "usage: exit 2 must add_finding"
ok "usage exit 2 -> exit 1, add_finding"

awk '/^CHECKS=\(/{f=1} f && /^\)/{exit} f' "$EVAL" | grep -Fxq "  goal-emit" \
  || fail "goal-emit must be registered in CHECKS=(...)"
grep -q '^check_goal_emit()' "$EVAL" \
  || fail "check_goal_emit must be defined"
grep -q '^check_spec_analyze()' "$EVAL" \
  || fail "spec-analyze check must remain"
ok "registration: goal-emit in CHECKS; spec-analyze kept"

printf '\nAll %d goal-emit eval-wiring assertions passed.\n' "$pass_count"
