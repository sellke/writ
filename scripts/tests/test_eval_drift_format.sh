#!/usr/bin/env bash
# Tests check_drift_format and --prose-only-blocking (Story 5, AC-5.2).
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
  local root verdict="${1:-pass}"
  root="$(mktemp -d)"
  TMP_ROOTS+=("$root")
  mkdir -p "$root/scripts" "$root/commands"
  cp "$EVAL" "$root/scripts/eval.sh"
  printf '# story\n' > "$root/story.md"
  case "$verdict" in
    fail)
      write_stub "$root/scripts/drift-format.py" "$(cat <<'PY'
#!/usr/bin/env python3
print("fail")
print("reason: malformed_entry")
print("drift-format: fail (fixture)")
raise SystemExit(1)
PY
)"
      ;;
    *)
      write_stub "$root/scripts/drift-format.py" "$(cat <<'PY'
#!/usr/bin/env python3
print("pass")
print("drift-format: pass (fixture)")
raise SystemExit(0)
PY
)"
      ;;
  esac
  printf "%s" "$root"
}

run_check() {
  local root="$1" rc=0
  ( cd "$root" && bash scripts/eval.sh --check=drift-format --report=eval-report.md >/dev/null 2>&1 ) || rc=$?
  printf "%s" "$rc"
}

ROOT="$(new_root pass)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 0 ] || fail "pass: expected exit 0, got $rc"
grep -Fq 'drift-format: pass' "$ROOT/eval-report.md" || fail "pass: summary note missing"
ok "pass fixture -> exit 0, summary via add_note"

ROOT="$(new_root fail)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || fail "fail: expected exit 1, got $rc"
grep -Fq 'malformed_entry' "$ROOT/eval-report.md" || fail "fail: reason finding missing"
ok "fail fixture -> exit 1, reason via add_finding"

awk '/^CHECKS=\(/{f=1} f && /^\)/{exit} f' "$EVAL" | grep -Fxq "  drift-format" \
  || fail "drift-format must be registered in CHECKS=(...)"
grep -q '^check_drift_format()' "$EVAL" \
  || fail "check_drift_format must be defined"
awk '/^check_verdict_provenance\(\)/,/^}/' "$EVAL" | grep '"\$helper" check ' | grep -q -- '--prose-only-blocking' \
  || fail "check_verdict_provenance must pass --prose-only-blocking after Story 5"
ok "registration: drift-format in CHECKS; provenance blocking on"

printf '\nAll %d drift-format check assertions passed.\n' "$pass_count"
