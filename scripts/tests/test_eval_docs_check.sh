#!/usr/bin/env bash
# Tests check_docs_check in scripts/eval.sh (spec
# 2026-09-08-phase11-stage2b-mechanize-the-gates, Story 3, AC-3.5).
#
# Harness: copy eval.sh and a stub docs-check.py into a temp scripts/
# so PROJECT_ROOT is the fixture tree. No mutation of the real repository.
# If the real eval.sh does not yet register docs-check, the copy is wired
# so relay assertions can run; registration assertions still target the
# real file (parent lands check_docs_check to match check_review_override).
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

# Parent owns the real eval.sh registration. The fixture copy must be able
# to run --check=docs-check even before that lands. Insert the function
# *before* run_check() so the dispatcher can find it.
wire_docs_check() {
  local eval_sh="$1"
  python3 - "$eval_sh" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
if "  docs-check\n" not in text:
    if "  review-override\n" in text:
        text = text.replace("  review-override\n", "  review-override\n  docs-check\n", 1)
    else:
        text = text.replace("CHECKS=(\n", "CHECKS=(\n  docs-check\n", 1)

fn = """
check_docs_check() {
  local helper="$PROJECT_ROOT/scripts/docs-check.py"
  local output rc line

  if [ ! -f "$helper" ]; then
    add_finding "scripts/docs-check.py" "docs-check helper is missing." \\
      "Restore scripts/docs-check.py so check can run."
    return
  fi

  rc=0
  output="$(python3 "$helper" check --repo "$PROJECT_ROOT" 2>&1)" || rc=$?
  if [ "$rc" -eq 2 ]; then
    add_finding "scripts/docs-check.py" "docs-check.py check refused: ${output##*$'\\n'}" \\
      "Fix the docs-check.py CLI so python3 scripts/docs-check.py check --repo . parses."
    return
  fi
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    case "$line" in
      fail)
        add_finding "scripts/docs-check.py" "docs-check printed fail." \\
          "Document the missing public export the checker reported."
        ;;
      pass|unverifiable)
        add_note "NOTE [docs-check]: $line"
        ;;
      "reason: "*)
        if [ "$rc" -eq 1 ]; then
          add_finding "docs-check:${line#reason: }" "${line#reason: }" \\
            "Document the public export; Gate 5 fail is BLOCKED with documentation-agent."
        else
          add_note "NOTE [docs-check]: $line"
        fi
        ;;
      *)
        add_note "NOTE [docs-check]: $line"
        ;;
    esac
  done <<< "$output"
}

"""
if "check_docs_check()" not in text:
    needle = "run_check() {"
    if needle not in text:
        raise SystemExit("eval.sh fixture is missing run_check(); cannot wire docs-check")
    text = text.replace(needle, fn + needle, 1)
path.write_text(text, encoding="utf-8")
PY
}

new_root() {
  local root verdict="${1:-pass}"
  root="$(mktemp -d)"
  TMP_ROOTS+=("$root")
  mkdir -p "$root/scripts" "$root/commands"
  cp "$EVAL" "$root/scripts/eval.sh"
  wire_docs_check "$root/scripts/eval.sh"
  case "$verdict" in
    fail)
      write_stub "$root/scripts/docs-check.py" "$(cat <<'PY'
#!/usr/bin/env python3
print("fail")
print("reason: undocumented_export")
print("docs-check: fail (fixture)")
raise SystemExit(1)
PY
)"
      ;;
    unverifiable)
      write_stub "$root/scripts/docs-check.py" "$(cat <<'PY'
#!/usr/bin/env python3
print("unverifiable")
print("reason: no_public_exports")
print("docs-check: unverifiable (fixture)")
raise SystemExit(0)
PY
)"
      ;;
    *)
      write_stub "$root/scripts/docs-check.py" "$(cat <<'PY'
#!/usr/bin/env python3
print("pass")
print("docs-check: pass (fixture)")
raise SystemExit(0)
PY
)"
      ;;
  esac
  printf "%s" "$root"
}

run_check() {
  local root="$1" rc=0
  ( cd "$root" && bash scripts/eval.sh --check=docs-check --report=eval-report.md >/dev/null 2>&1 ) || rc=$?
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
grep -Fq 'docs-check: pass' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "pass: summary must be relayed as a note"; }
ok "pass fixture -> exit 0, summary via add_note"

# ---------------------------------------------------------------------------
# fail -> exit 1, finding names the reason
# ---------------------------------------------------------------------------
ROOT="$(new_root fail)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || { report_of "$ROOT"; fail "fail: expected exit 1, got $rc"; }
grep -q '^FAIL' "$ROOT/eval-report.md" || { report_of "$ROOT"; fail "fail: report must say FAIL"; }
grep -Fq 'undocumented_export' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "fail: finding must name undocumented_export"; }
ok "fail fixture -> exit 1, reason via add_finding"

# ---------------------------------------------------------------------------
# unverifiable -> exit 0, reason via add_note (not count-blocking)
# ---------------------------------------------------------------------------
ROOT="$(new_root unverifiable)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 0 ] || { report_of "$ROOT"; fail "unverifiable: expected exit 0, got $rc"; }
grep -q '^PASS' "$ROOT/eval-report.md" || { report_of "$ROOT"; fail "unverifiable: must PASS"; }
grep -Fq 'no_public_exports' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "unverifiable: reason must be a note"; }
ok "unverifiable fixture -> exit 0, reason via add_note"

# ---------------------------------------------------------------------------
# missing helper -> one finding, not a crash
# ---------------------------------------------------------------------------
ROOT="$(new_root pass)"
rm "$ROOT/scripts/docs-check.py"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || { report_of "$ROOT"; fail "no-helper: expected exit 1, got $rc"; }
grep -Fq 'docs-check.py' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "no-helper: finding must name the helper"; }
ok "missing helper -> exit 1, one finding"

# ---------------------------------------------------------------------------
# Registration and the not-yet-blocking provenance contract
# ---------------------------------------------------------------------------
awk '/^CHECKS=\(/{f=1} f && /^\)/{exit} f' "$EVAL" | grep -Fxq "  docs-check" \
  || fail "docs-check must be registered in CHECKS=(...)"
grep -q '^check_docs_check()' "$EVAL" \
  || fail "check_docs_check must be defined in scripts/eval.sh"
awk '/^check_docs_check\(\)/,/^}/' "$EVAL" | grep -q 'add_finding' \
  || fail "check_docs_check must relay findings via add_finding"
awk '/^check_docs_check\(\)/,/^}/' "$EVAL" | grep -q 'add_note' \
  || fail "check_docs_check must relay the summary via add_note"
if awk '/^check_verdict_provenance\(\)/,/^}/' "$EVAL" | grep '"\$helper" check ' | grep -q -- '--prose-only-blocking'; then
  fail "check_verdict_provenance must not pass --prose-only-blocking yet (Story 5 flips it)"
fi
ok "registration: docs-check in CHECKS, findings/notes relayed, provenance not blocking"

printf '\nAll %d docs-check check assertions passed.\n' "$pass_count"
