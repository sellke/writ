#!/usr/bin/env bash
# Story 3: check_spawn_cap registration and note-vs-finding split.
# [AC-3.2, AC-3.4]
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
  mkdir -p "$root/scripts" "$root/commands"
  cp "$EVAL" "$root/scripts/eval.sh"
  printf '# command\n' > "$root/commands/implement-story.md"
  case "$mode" in
    missing)
      ;;
    usage)
      write_stub "$root/scripts/spawn-cap.py" "$(cat <<'PY'
#!/usr/bin/env python3
raise SystemExit(2)
PY
)"
      ;;
    fail)
      write_stub "$root/scripts/spawn-cap.py" "$(cat <<'PY'
#!/usr/bin/env python3
print("fail")
print("reason: over_cap")
print("spawn-cap: fail (fixture)")
raise SystemExit(1)
PY
)"
      ;;
    unverifiable)
      write_stub "$root/scripts/spawn-cap.py" "$(cat <<'PY'
#!/usr/bin/env python3
print("unverifiable")
print("reason: missing_command")
print("spawn-cap: unverifiable (fixture)")
raise SystemExit(0)
PY
)"
      ;;
    *)
      write_stub "$root/scripts/spawn-cap.py" "$(cat <<'PY'
#!/usr/bin/env python3
print("pass")
print("spawn-cap: pass (fixture)")
raise SystemExit(0)
PY
)"
      ;;
  esac
  printf "%s" "$root"
}

run_check() {
  local root="$1" rc=0
  ( cd "$root" && bash scripts/eval.sh --check=spawn-cap --report=eval-report.md >/dev/null 2>&1 ) || rc=$?
  printf "%s" "$rc"
}

ROOT="$(new_root pass)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 0 ] || { cat "$ROOT/eval-report.md"; fail "pass: expected exit 0, got $rc"; }
grep -Fq 'NOTE [spawn-cap]:' "$ROOT/eval-report.md" \
  || fail "pass: spawn-cap verdict must be a note"
ok "pass stub -> exit 0, add_note"

ROOT="$(new_root fail)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 0 ] || { cat "$ROOT/eval-report.md"; fail "fail: spawn-cap fail must not fail the check, got $rc"; }
grep -Fq 'NOTE [spawn-cap]: fail' "$ROOT/eval-report.md" \
  || fail "fail: spawn-cap fail must be a note"
if grep -q '^FAIL' "$ROOT/eval-report.md"; then
  cat "$ROOT/eval-report.md"; fail "fail: must have zero findings"
fi
ok "spawn-cap fail stub -> exit 0, add_note only"

ROOT="$(new_root unverifiable)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 0 ] || fail "unverifiable: expected exit 0, got $rc"
grep -Fq 'NOTE [spawn-cap]: unverifiable' "$ROOT/eval-report.md" \
  || fail "unverifiable: must be a note"
ok "unverifiable stub -> exit 0, add_note"

ROOT="$(new_root missing)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || fail "missing: expected exit 1, got $rc"
grep -Fq 'spawn-cap helper is missing' "$ROOT/eval-report.md" \
  || fail "missing: must add_finding"
ok "missing helper -> exit 1, add_finding"

ROOT="$(new_root usage)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || fail "usage: expected exit 1, got $rc"
grep -Fq 'refused' "$ROOT/eval-report.md" \
  || fail "usage: exit 2 must add_finding"
ok "usage exit 2 -> exit 1, add_finding"

awk '/^CHECKS=\(/{f=1} f && /^\)/{exit} f' "$EVAL" | grep -Fxq "  spawn-cap" \
  || fail "spawn-cap must be registered in CHECKS=(...)"
awk '/^CHECKS=\(/{f=1} f && /^\)/{exit} f' "$EVAL" | grep -Fxq "  goal-emit" \
  || fail "goal-emit must remain in CHECKS=(...)"
awk '/^CHECKS=\(/{f=1} f && /^\)/{exit} f' "$EVAL" | tr '\n' '|' | grep -Fq '  goal-emit|  spawn-cap|' \
  || fail "spawn-cap must be listed immediately after goal-emit"
grep -q '^check_spawn_cap()' "$EVAL" \
  || fail "check_spawn_cap must be defined"
grep -q '^check_goal_emit()' "$EVAL" \
  || fail "goal-emit check must remain"
ok "registration: spawn-cap in CHECKS; goal-emit kept"

printf '\nAll %d spawn-cap eval-wiring assertions passed.\n' "$pass_count"
