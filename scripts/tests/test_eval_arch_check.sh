#!/usr/bin/env bash
# Tests check_arch_check in scripts/eval.sh (spec
# 2026-09-08-phase11-stage2b-mechanize-the-gates, Story 2, AC-2.5).
#
# Harness: copy eval.sh and a stub arch-check.py into a temp scripts/
# so PROJECT_ROOT is the fixture tree. No mutation of the real repository.
#
# The real eval.sh may not register arch-check yet (parent wires it to
# match check_review_override). Relay tests inject a minimal
# check_arch_check + CHECKS entry into the temp copy. Real-file
# registration is asserted last and skipped with PARENT WIRES eval.sh
# when the parent has not landed that function.
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

# Inject check_arch_check + CHECKS entry when the copied eval.sh lacks them.
ensure_arch_check_wired() {
  local eval_copy="$1"
  python3 - "$eval_copy" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
if "  arch-check\n" not in text and "\n  arch-check\n" not in text.split("CHECKS=(")[-1]:
    if "  review-override\n)" in text:
        text = text.replace("  review-override\n)", "  review-override\n  arch-check\n)", 1)
    elif "CHECKS=(" in text:
        text = text.replace("CHECKS=(\n", "CHECKS=(\n  arch-check\n", 1)

fn = '''
check_arch_check() {
  # Story 2 of 2026-09-08-phase11-stage2b-mechanize-the-gates: Gate 0's
  # mechanical re-derivation. Relays arch-check.py findings via add_finding
  # and the summary / unverifiable reasons via add_note. Not count-blocking.
  local helper="$PROJECT_ROOT/scripts/arch-check.py"
  local output rc line

  if [ ! -f "$helper" ]; then
    add_finding "scripts/arch-check.py" "arch-check helper is missing." \\
      "Restore scripts/arch-check.py so check can run."
    return
  fi

  rc=0
  output="$(python3 "$helper" check --repo "$PROJECT_ROOT" 2>&1)" || rc=$?
  if [ "$rc" -eq 2 ]; then
    add_finding "scripts/arch-check.py" "arch-check.py check refused: ${output##*$'\\n'}" \\
      "Fix the arch-check.py CLI so python3 scripts/arch-check.py check --repo . parses."
    return
  fi
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    case "$line" in
      fail)
        add_finding "scripts/arch-check.py" "arch-check printed fail." \\
          "Resolve the story-deps graph or file-set finding the checker reported."
        ;;
      pass|unverifiable)
        add_note "NOTE [arch-check]: $line"
        ;;
      "reason: "*)
        if [ "$rc" -eq 1 ]; then
          add_finding "arch-check:${line#reason: }" "${line#reason: }" \\
            "Resolve the helper finding; Gate 0 fail applies the existing BLOCKED path."
        else
          add_note "NOTE [arch-check]: $line"
        fi
        ;;
      *)
        add_note "NOTE [arch-check]: $line"
        ;;
    esac
  done <<< "$output"
}
'''
if "check_arch_check()" not in text:
    # Place the function before run_check() when present so it is defined.
    marker = "run_check() {"
    if marker in text:
        text = text.replace(marker, fn.lstrip("\n") + "\n" + marker, 1)
    else:
        text = text + "\n" + fn
path.write_text(text, encoding="utf-8")
PY
}

new_root() {
  local root verdict="${1:-pass}"
  root="$(mktemp -d)"
  TMP_ROOTS+=("$root")
  mkdir -p "$root/scripts" "$root/commands"
  cp "$EVAL" "$root/scripts/eval.sh"
  ensure_arch_check_wired "$root/scripts/eval.sh"
  case "$verdict" in
    fail)
      write_stub "$root/scripts/arch-check.py" "$(cat <<'PY'
#!/usr/bin/env python3
print("fail")
print("reason: dependency_cycle")
print("arch-check: fail (fixture)")
raise SystemExit(1)
PY
)"
      ;;
    unverifiable)
      write_stub "$root/scripts/arch-check.py" "$(cat <<'PY'
#!/usr/bin/env python3
print("unverifiable")
print("reason: no_file_mode")
print("arch-check: unverifiable (fixture)")
raise SystemExit(0)
PY
)"
      ;;
    *)
      write_stub "$root/scripts/arch-check.py" "$(cat <<'PY'
#!/usr/bin/env python3
print("pass")
print("rederived: proceed")
print("arch-check: pass (fixture)")
raise SystemExit(0)
PY
)"
      ;;
  esac
  printf "%s" "$root"
}

run_check() {
  local root="$1" rc=0
  ( cd "$root" && bash scripts/eval.sh --check=arch-check --report=eval-report.md >/dev/null 2>&1 ) || rc=$?
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
grep -Fq 'arch-check: pass' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "pass: summary must be relayed as a note"; }
ok "pass fixture -> exit 0, summary via add_note"

# ---------------------------------------------------------------------------
# fail -> exit 1, finding names the reason
# ---------------------------------------------------------------------------
ROOT="$(new_root fail)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || { report_of "$ROOT"; fail "fail: expected exit 1, got $rc"; }
grep -q '^FAIL' "$ROOT/eval-report.md" || { report_of "$ROOT"; fail "fail: report must say FAIL"; }
grep -Fq 'dependency_cycle' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "fail: finding must name dependency_cycle"; }
ok "fail fixture -> exit 1, reason via add_finding"

# ---------------------------------------------------------------------------
# unverifiable -> exit 0, reason via add_note (not count-blocking)
# ---------------------------------------------------------------------------
ROOT="$(new_root unverifiable)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 0 ] || { report_of "$ROOT"; fail "unverifiable: expected exit 0, got $rc"; }
grep -q '^PASS' "$ROOT/eval-report.md" || { report_of "$ROOT"; fail "unverifiable: must PASS"; }
grep -Fq 'no_file_mode' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "unverifiable: reason must be a note"; }
ok "unverifiable fixture -> exit 0, reason via add_note"

# ---------------------------------------------------------------------------
# missing helper -> one finding, not a crash
# ---------------------------------------------------------------------------
ROOT="$(new_root pass)"
rm "$ROOT/scripts/arch-check.py"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || { report_of "$ROOT"; fail "no-helper: expected exit 1, got $rc"; }
grep -Fq 'arch-check.py' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "no-helper: finding must name the helper"; }
ok "missing helper -> exit 1, one finding"

# ---------------------------------------------------------------------------
# Injected check_arch_check relays findings via add_finding and notes
# ---------------------------------------------------------------------------
ROOT="$(new_root pass)"
awk '/^check_arch_check\(\)/,/^}/' "$ROOT/scripts/eval.sh" | grep -q 'add_finding' \
  || fail "injected check_arch_check must relay findings via add_finding"
awk '/^check_arch_check\(\)/,/^}/' "$ROOT/scripts/eval.sh" | grep -q 'add_note' \
  || fail "injected check_arch_check must relay the summary via add_note"
ok "injected check_arch_check relays findings via add_finding and summary via add_note"

# ---------------------------------------------------------------------------
# Real eval.sh registration — parent wires check_arch_check to match
# check_review_override. Skip (do not fail) until that lands.
# PARENT WIRES eval.sh
# ---------------------------------------------------------------------------
if awk '/^CHECKS=\(/{f=1} f && /^\)/{exit} f' "$EVAL" | grep -Fxq "  arch-check" \
  && grep -q '^check_arch_check()' "$EVAL"; then
  awk '/^check_arch_check\(\)/,/^}/' "$EVAL" | grep -q 'add_finding' \
    || fail "check_arch_check must relay findings via add_finding"
  awk '/^check_arch_check\(\)/,/^}/' "$EVAL" | grep -q 'add_note' \
    || fail "check_arch_check must relay the summary via add_note"
  ok "registration: arch-check in CHECKS, findings/notes relayed"
else
  # PARENT WIRES eval.sh
  ok "registration: skipped until parent wires arch-check in real eval.sh"
fi

printf '\nAll %d arch-check check assertions passed.\n' "$pass_count"
