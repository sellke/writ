#!/usr/bin/env bash
# Tests check_review_override in scripts/eval.sh (spec
# 2026-09-08-phase11-stage2b-mechanize-the-gates, Story 1, AC-1.5).
# AC-1.5
#
# Harness: copy eval.sh and a stub review-override.py into a temp scripts/
# so PROJECT_ROOT is the fixture tree. No mutation of the real repository.
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
  return "$rc"
}
trap cleanup EXIT

write_stub() {
  local dest="$1" body="$2"
  printf '%s\n' "$body" > "$dest"
  chmod +x "$dest"
}

new_root() {
  local root verdict="${1:-pass}"
  root="$(mktemp -d)"
  TMP_ROOTS+=("$root")
  mkdir -p "$root/scripts" "$root/commands"
  cp "$EVAL" "$root/scripts/eval.sh"
  case "$verdict" in
    fail)
      write_stub "$root/scripts/review-override.py" "$(cat <<'PY'
#!/usr/bin/env python3
print("fail")
print("reason: coverage_below_threshold")
print("review-override: fail (fixture)")
raise SystemExit(1)
PY
)"
      ;;
    unverifiable)
      write_stub "$root/scripts/review-override.py" "$(cat <<'PY'
#!/usr/bin/env python3
print("unverifiable")
print("reason: missing_spec")
print("review-override: unverifiable (fixture)")
raise SystemExit(0)
PY
)"
      ;;
    *)
      write_stub "$root/scripts/review-override.py" "$(cat <<'PY'
#!/usr/bin/env python3
print("pass")
print("review-override: pass (fixture)")
raise SystemExit(0)
PY
)"
      ;;
  esac
  printf "%s" "$root"
}

run_check() {
  local root="$1" rc=0
  ( cd "$root" && bash scripts/eval.sh --check=review-override --report=eval-report.md >/dev/null 2>&1 ) || rc=$?
  printf "%s" "$rc"
}

report_of() {
  cat "$1/eval-report.md"
}

# ---------------------------------------------------------------------------
# pass -> exit 0, summary via add_note, no findings
# ---------------------------------------------------------------------------
ROOT="$(new_root pass)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 0 ] || { report_of "$ROOT"; fail "pass: expected exit 0, got $rc"; }
grep -q '^PASS' "$ROOT/eval-report.md" || { report_of "$ROOT"; fail "pass: report must say PASS"; }
if grep -q '^FAIL' "$ROOT/eval-report.md"; then
  report_of "$ROOT"; fail "pass: must have zero findings"
fi
grep -Fq 'review-override: pass' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "pass: summary must be relayed as a note"; }
ok "pass fixture -> exit 0, summary via add_note"

# ---------------------------------------------------------------------------
# fail -> exit 1, finding names the reason
# ---------------------------------------------------------------------------
ROOT="$(new_root fail)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || { report_of "$ROOT"; fail "fail: expected exit 1, got $rc"; }
grep -q '^FAIL' "$ROOT/eval-report.md" || { report_of "$ROOT"; fail "fail: report must say FAIL"; }
grep -Fq 'coverage_below_threshold' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "fail: finding must name coverage_below_threshold"; }
ok "fail fixture -> exit 1, reason via add_finding"

# ---------------------------------------------------------------------------
# unverifiable -> exit 0, reason via add_note (not count-blocking)
# ---------------------------------------------------------------------------
ROOT="$(new_root unverifiable)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 0 ] || { report_of "$ROOT"; fail "unverifiable: expected exit 0, got $rc"; }
grep -q '^PASS' "$ROOT/eval-report.md" || { report_of "$ROOT"; fail "unverifiable: must PASS"; }
grep -Fq 'missing_spec' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "unverifiable: reason must be a note"; }
ok "unverifiable fixture -> exit 0, reason via add_note"

# ---------------------------------------------------------------------------
# missing helper -> one finding, not a crash
# ---------------------------------------------------------------------------
ROOT="$(new_root pass)"
rm "$ROOT/scripts/review-override.py"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || { report_of "$ROOT"; fail "no-helper: expected exit 1, got $rc"; }
grep -Fq 'review-override.py' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "no-helper: finding must name the helper"; }
ok "missing helper -> exit 1, one finding"

# ---------------------------------------------------------------------------
# Registration and the not-yet-blocking provenance contract
# ---------------------------------------------------------------------------
awk '/^CHECKS=\(/{f=1} f && /^\)/{exit} f' "$EVAL" | grep -Fxq "  review-override" \
  || fail "review-override must be registered in CHECKS=(...)"
grep -q '^check_review_override()' "$EVAL" \
  || fail "check_review_override must be defined in scripts/eval.sh"
awk '/^check_review_override\(\)/,/^}/' "$EVAL" | grep -q 'add_finding' \
  || fail "check_review_override must relay findings via add_finding"
awk '/^check_review_override\(\)/,/^}/' "$EVAL" | grep -q 'add_note' \
  || fail "check_review_override must relay the summary via add_note"
if awk '/^check_verdict_provenance\(\)/,/^}/' "$EVAL" | grep '"\$helper" check ' | grep -q -- '--prose-only-blocking'; then
  fail "check_verdict_provenance must not pass --prose-only-blocking yet (Story 5 flips it)"
fi
ok "registration: review-override in CHECKS, findings/notes relayed, provenance not blocking"

printf '\nAll %d review-override check assertions passed.\n' "$pass_count"
