#!/usr/bin/env bash
# Tests check_claude_md in eval.sh (Story 1 of 2026-10-20-claude-code-parity,
# AC-1.5). Each case runs eval.sh in a temp root holding eval.sh, the
# generator, the manifest, and claude-code/. Never touches the real template.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
EVAL="$REPO/scripts/eval.sh"
GEN="$REPO/scripts/gen-claude-md.py"
REMEDY='python3 scripts/gen-claude-md.py'

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

# A temp root with a freshly generated claude-code/CLAUDE.md.
new_root() {
  local root
  root="$(mktemp -d)"
  TMP_ROOTS+=("$root")
  mkdir -p "$root/scripts" "$root/.writ" "$root/claude-code"
  cp "$EVAL" "$root/scripts/eval.sh"
  cp "$GEN" "$root/scripts/gen-claude-md.py"
  cp "$REPO/.writ/manifest.yaml" "$root/.writ/manifest.yaml"
  cp -R "$REPO/claude-code/agents" "$root/claude-code/agents"
  python3 "$root/scripts/gen-claude-md.py" >/dev/null
  printf "%s" "$root"
}

run_check() {
  local root="$1" rc=0
  ( cd "$root" && bash scripts/eval.sh --check=claude-md --report=eval-report.md >/dev/null 2>&1 ) || rc=$?
  printf "%s" "$rc"
}

section() {
  awk '/^## claude-md$/{f=1; next} f && /^## /{exit} f' "$1/eval-report.md"
}

# AC-1.5: a fresh copy passes.
ROOT="$(new_root)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 0 ] || fail "fresh: expected exit 0, got $rc"
section "$ROOT" | awk 'NF {print; exit}' | grep -Fxq 'PASS' || fail "fresh: claude-md section should PASS"
section "$ROOT" | grep -Fq 'gen-claude-md: pass (' || fail "fresh: summary line should be a note"
ok "fresh template -> PASS, exit 0"

# AC-1.5: delete the /revert row -> one finding naming /revert and the remedy.
ROOT="$(new_root)"
grep -q '^| `/revert` |' "$ROOT/claude-code/CLAUDE.md" || fail "fixture: no /revert row"
grep -v '^| `/revert` |' "$ROOT/claude-code/CLAUDE.md" > "$ROOT/edited" && mv "$ROOT/edited" "$ROOT/claude-code/CLAUDE.md"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || fail "deleted row: expected exit 1, got $rc"
section "$ROOT" | grep -Fxq 'FAIL (1 finding(s))' || fail "deleted row: expected exactly one finding"
finding="$(section "$ROOT" | grep -F 'manifest command /revert is missing from the Claude Code template.' || true)"
[ -n "$finding" ] || fail "deleted row: finding must name /revert"
[[ "$finding" == *"Run $REMEDY and commit claude-code/CLAUDE.md."* ]] || fail "deleted row: finding must carry the remedy '$REMEDY'"
ok "deleted /revert row -> one finding naming /revert with the remedy"

# AC-1.5: add a manifest command without regenerating -> one finding naming it.
ROOT="$(new_root)"
awk '{print} /^commands:$/ {print "  - name: zz-new"; print "    file: commands/zz-new.md"; print "    purpose: \"A new command.\""}' \
  "$REPO/.writ/manifest.yaml" > "$ROOT/.writ/manifest.yaml"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || fail "new command: expected exit 1, got $rc"
section "$ROOT" | grep -Fxq 'FAIL (1 finding(s))' || fail "new command: expected exactly one finding"
finding="$(section "$ROOT" | grep -F 'manifest command /zz-new is missing from the Claude Code template.' || true)"
[ -n "$finding" ] || fail "new command: finding must name /zz-new"
[[ "$finding" == *"$REMEDY"* ]] || fail "new command: finding must carry the remedy '$REMEDY'"
ok "new manifest command -> one finding naming /zz-new with the remedy"

# Any other byte difference -> one stale finding.
ROOT="$(new_root)"
printf '\nhand edit\n' >> "$ROOT/claude-code/CLAUDE.md"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || fail "stale: expected exit 1, got $rc"
section "$ROOT" | grep -Fxq 'FAIL (1 finding(s))' || fail "stale: expected exactly one finding"
finding="$(section "$ROOT" | grep -F 'stale claude-code/CLAUDE.md' || true)"
[[ "$finding" == *"$REMEDY"* ]] || fail "stale: finding must carry the remedy '$REMEDY'"
ok "hand-edited template -> one stale finding with the remedy"

# A missing manifest is unverifiable; CI must not pass on it.
ROOT="$(new_root)"
rm "$ROOT/.writ/manifest.yaml"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || fail "no manifest: expected exit 1, got $rc"
section "$ROOT" | grep -Fxq 'FAIL (1 finding(s))' || fail "no manifest: expected exactly one finding"
section "$ROOT" | grep -Fq 'manifest missing: .writ/manifest.yaml' || fail "no manifest: finding must carry the reason"
ok "missing manifest -> one finding"

# A missing helper is a finding.
ROOT="$(new_root)"
rm "$ROOT/scripts/gen-claude-md.py"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || fail "missing helper: expected exit 1, got $rc"
section "$ROOT" | grep -Fq 'scripts/gen-claude-md.py' || fail "missing helper: finding must name the helper"
ok "missing helper -> finding"

# AC-1.5: claude-md is registered once, after codex-tomls, so the full run and CI include it.
checks="$(awk '/^CHECKS=\(/{f=1; next} f && /^\)/{exit} f' "$EVAL")"
[ "$(printf '%s\n' "$checks" | grep -cFx '  claude-md')" -eq 1 ] \
  || fail "claude-md must be registered exactly once in CHECKS=(...)"
printf '%s\n' "$checks" | sed -n '/^  codex-tomls$/,$p' | grep -Fxq '  claude-md' \
  || fail "claude-md must come after codex-tomls in CHECKS=(...)"
grep -q '^check_claude_md()' "$EVAL" || fail "check_claude_md must be defined"
ok "registration: claude-md in CHECKS after codex-tomls; check_claude_md defined"

printf '\nAll %d claude-md check assertions passed.\n' "$pass_count"
