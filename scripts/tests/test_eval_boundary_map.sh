#!/usr/bin/env bash
# Tests check_boundary_map and check_change_surface wiring (spec
# 2026-09-08-phase11-stage2b-mechanize-the-gates, Story 4, AC-4.5).
#
# Harness: copy eval.sh into a temp scripts/ so PROJECT_ROOT is the
# fixture tree. Parent owns registering the names on the real eval.sh;
# this file patches the copy so --check=boundary-map / change-surface
# can be exercised with stubs. No mutation of the real repository.
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

patch_eval() {
  local dest="$1"
  python3 - "$dest" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
if "\n  boundary-map\n" not in text:
    if "\n  review-override\n)" in text:
        text = text.replace(
            "\n  review-override\n)",
            "\n  review-override\n  boundary-map\n  change-surface\n)",
            1,
        )
    else:
        text = text.replace(
            "\n)\n",
            "\n  boundary-map\n  change-surface\n)\n",
            1,
        )

fns = r'''
check_boundary_map() {
  local helper="$PROJECT_ROOT/scripts/boundary-map.py"
  local output rc=0

  if [ ! -f "$helper" ]; then
    add_finding "scripts/boundary-map.py" "boundary-map helper is missing." \
      "Restore scripts/boundary-map.py so check can run."
    return
  fi

  output="$(python3 "$helper" compute --story "$PROJECT_ROOT/story.md" --repo "$PROJECT_ROOT" 2>&1)" || rc=$?
  if [ "$rc" -eq 2 ]; then
    add_finding "scripts/boundary-map.py" "boundary-map.py compute refused: ${output##*$'\n'}" \
      "Fix the boundary-map.py CLI so compute --story PATH --repo . parses."
    return
  fi
  if [ "$rc" -eq 1 ]; then
    add_finding "scripts/boundary-map.py" "boundary-map.py reported a malformed story." \
      "Fix the story file passed to compute."
    return
  fi
  add_note "NOTE [boundary-map]: $output"
}

check_change_surface() {
  local helper="$PROJECT_ROOT/scripts/change-surface.py"
  local output rc=0

  if [ ! -f "$helper" ]; then
    add_finding "scripts/change-surface.py" "change-surface helper is missing." \
      "Restore scripts/change-surface.py so check can run."
    return
  fi

  output="$(python3 "$helper" classify --changed "$PROJECT_ROOT/fixture.css" 2>&1)" || rc=$?
  if [ "$rc" -eq 2 ]; then
    add_finding "scripts/change-surface.py" "change-surface.py classify refused: ${output##*$'\n'}" \
      "Fix the change-surface.py CLI so classify --changed FILE parses."
    return
  fi
  if [ "$rc" -ne 0 ]; then
    add_finding "scripts/change-surface.py" "change-surface.py classify failed." \
      "Investigate scripts/change-surface.py."
    return
  fi
  add_note "NOTE [change-surface]: $output"
}

'''
if "check_boundary_map()" not in text:
    needle = "run_check() {"
    if needle not in text:
        raise SystemExit("eval.sh fixture missing run_check")
    text = text.replace(needle, fns + needle, 1)
path.write_text(text, encoding="utf-8")
PY
}

new_root() {
  local root kind="${1:-map-ok}"
  root="$(mktemp -d)"
  TMP_ROOTS+=("$root")
  mkdir -p "$root/scripts" "$root/commands"
  cp "$EVAL" "$root/scripts/eval.sh"
  patch_eval "$root/scripts/eval.sh"
  printf '# story\n' > "$root/story.md"
  printf 'body{}\n' > "$root/fixture.css"
  case "$kind" in
    map-fail)
      write_stub "$root/scripts/boundary-map.py" "$(cat <<'PY'
#!/usr/bin/env python3
raise SystemExit(1)
PY
)"
      write_stub "$root/scripts/change-surface.py" "$(cat <<'PY'
#!/usr/bin/env python3
print("style-only")
raise SystemExit(0)
PY
)"
      ;;
    surface-fail)
      write_stub "$root/scripts/boundary-map.py" "$(cat <<'PY'
#!/usr/bin/env python3
print('{"owned":[],"readable":[],"out_of_scope":[]}')
raise SystemExit(0)
PY
)"
      write_stub "$root/scripts/change-surface.py" "$(cat <<'PY'
#!/usr/bin/env python3
raise SystemExit(2)
PY
)"
      ;;
    *)
      write_stub "$root/scripts/boundary-map.py" "$(cat <<'PY'
#!/usr/bin/env python3
print('{"owned":["src/auth/login.ts"],"readable":[],"out_of_scope":[]}')
raise SystemExit(0)
PY
)"
      write_stub "$root/scripts/change-surface.py" "$(cat <<'PY'
#!/usr/bin/env python3
print("style-only")
raise SystemExit(0)
PY
)"
      ;;
  esac
  printf "%s" "$root"
}

run_check() {
  local root="$1" name="$2" rc=0
  ( cd "$root" && bash scripts/eval.sh --check="$name" --report=eval-report.md >/dev/null 2>&1 ) || rc=$?
  printf "%s" "$rc"
}

report_of() {
  cat "$1/eval-report.md"
}

# ---------------------------------------------------------------------------
# boundary-map well-formed -> exit 0, JSON relayed via add_note
# ---------------------------------------------------------------------------
ROOT="$(new_root map-ok)"
rc="$(run_check "$ROOT" boundary-map)"
[ "$rc" -eq 0 ] || { report_of "$ROOT"; fail "boundary-map ok: expected exit 0, got $rc"; }
grep -q '^PASS' "$ROOT/eval-report.md" || { report_of "$ROOT"; fail "boundary-map ok: report must say PASS"; }
if grep -q '^FAIL' "$ROOT/eval-report.md"; then
  report_of "$ROOT"; fail "boundary-map ok: must have zero findings"
fi
grep -Fq 'src/auth/login.ts' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "boundary-map ok: map must be relayed as a note"; }
ok "boundary-map well-formed -> exit 0, JSON via add_note"

# ---------------------------------------------------------------------------
# boundary-map malformed (exit 1) -> finding, not a crash
# ---------------------------------------------------------------------------
ROOT="$(new_root map-fail)"
rc="$(run_check "$ROOT" boundary-map)"
[ "$rc" -eq 1 ] || { report_of "$ROOT"; fail "boundary-map fail: expected exit 1, got $rc"; }
grep -q '^FAIL' "$ROOT/eval-report.md" || { report_of "$ROOT"; fail "boundary-map fail: report must say FAIL"; }
grep -Fq 'malformed story' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "boundary-map fail: finding must name malformed story"; }
ok "boundary-map malformed -> exit 1, finding via add_finding"

# ---------------------------------------------------------------------------
# change-surface class -> exit 0, token via add_note
# ---------------------------------------------------------------------------
ROOT="$(new_root map-ok)"
rc="$(run_check "$ROOT" change-surface)"
[ "$rc" -eq 0 ] || { report_of "$ROOT"; fail "change-surface ok: expected exit 0, got $rc"; }
grep -q '^PASS' "$ROOT/eval-report.md" || { report_of "$ROOT"; fail "change-surface ok: report must say PASS"; }
grep -Fq 'style-only' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "change-surface ok: class must be relayed as a note"; }
ok "change-surface class -> exit 0, token via add_note"

# ---------------------------------------------------------------------------
# change-surface usage (exit 2) -> finding
# ---------------------------------------------------------------------------
ROOT="$(new_root surface-fail)"
rc="$(run_check "$ROOT" change-surface)"
[ "$rc" -eq 1 ] || { report_of "$ROOT"; fail "change-surface usage: expected exit 1, got $rc"; }
grep -q '^FAIL' "$ROOT/eval-report.md" || { report_of "$ROOT"; fail "change-surface usage: report must say FAIL"; }
ok "change-surface usage -> finding via add_finding"

# ---------------------------------------------------------------------------
# missing helper -> one finding, not a crash
# ---------------------------------------------------------------------------
ROOT="$(new_root map-ok)"
rm "$ROOT/scripts/boundary-map.py"
rc="$(run_check "$ROOT" boundary-map)"
[ "$rc" -eq 1 ] || { report_of "$ROOT"; fail "no-helper: expected exit 1, got $rc"; }
grep -Fq 'boundary-map.py' "$ROOT/eval-report.md" \
  || { report_of "$ROOT"; fail "no-helper: finding must name the helper"; }
ok "missing boundary-map helper -> exit 1, one finding"

# ---------------------------------------------------------------------------
# Real eval.sh: --prose-only-blocking still not passed (Story 5)
# ---------------------------------------------------------------------------
if awk '/^check_verdict_provenance\(\)/,/^}/' "$EVAL" | grep '"\$helper" check ' | grep -q -- '--prose-only-blocking'; then
  fail "check_verdict_provenance must not pass --prose-only-blocking yet (Story 5 flips it)"
fi
ok "provenance not blocking"

# When the parent has registered the names, require add_finding / add_note.
if awk '/^CHECKS=\(/{f=1} f && /^\)/{exit} f' "$EVAL" | grep -Fxq "  boundary-map"; then
  grep -q '^check_boundary_map()' "$EVAL" \
    || fail "check_boundary_map must be defined in scripts/eval.sh"
  awk '/^check_boundary_map\(\)/,/^}/' "$EVAL" | grep -q 'add_finding' \
    || fail "check_boundary_map must relay findings via add_finding"
  awk '/^check_boundary_map\(\)/,/^}/' "$EVAL" | grep -q 'add_note' \
    || fail "check_boundary_map must relay the map via add_note"
  ok "registration: boundary-map in CHECKS, findings/notes relayed"
fi
if awk '/^CHECKS=\(/{f=1} f && /^\)/{exit} f' "$EVAL" | grep -Fxq "  change-surface"; then
  grep -q '^check_change_surface()' "$EVAL" \
    || fail "check_change_surface must be defined in scripts/eval.sh"
  awk '/^check_change_surface\(\)/,/^}/' "$EVAL" | grep -q 'add_finding' \
    || fail "check_change_surface must relay findings via add_finding"
  awk '/^check_change_surface\(\)/,/^}/' "$EVAL" | grep -q 'add_note' \
    || fail "check_change_surface must relay the class via add_note"
  ok "registration: change-surface in CHECKS, findings/notes relayed"
fi

printf '\nAll %d boundary-map / change-surface check assertions passed.\n' "$pass_count"
