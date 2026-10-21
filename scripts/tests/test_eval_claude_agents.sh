#!/usr/bin/env bash
# Tests check_claude_agents (Story 3 of 2026-10-20-claude-agent-generator,
# AC-3.4). Runs eval.sh against a temp copy; never touches the real
# claude-code/agents/.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
EVAL="$REPO/scripts/eval.sh"
GEN="$REPO/scripts/gen-claude-agents.py"
REMEDY='python3 scripts/gen-claude-agents.py'

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

new_root() {
  local root
  root="$(mktemp -d)"
  TMP_ROOTS+=("$root")
  mkdir -p "$root/scripts" "$root/claude-code/agents"
  cp "$EVAL" "$root/scripts/eval.sh"
  cp "$GEN" "$root/scripts/gen-claude-agents.py"
  cp -R "$REPO/agents" "$root/agents"
  python3 "$root/scripts/gen-claude-agents.py" >/dev/null
  printf "%s" "$root"
}

run_check() {
  local root="$1" rc=0
  ( cd "$root" && bash scripts/eval.sh --check=claude-agents --report=eval-report.md >/dev/null 2>&1 ) || rc=$?
  printf "%s" "$rc"
}

ROOT="$(new_root)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 0 ] || fail "fresh: expected exit 0, got $rc"
awk '/^## claude-agents$/{f=1; next} f && NF {print; exit}' "$ROOT/eval-report.md" | grep -Fxq 'PASS' \
  || fail "fresh: claude-agents section should PASS"
ok "freshly generated agents -> PASS, exit 0"

ROOT="$(new_root)"
printf '\nOne canonical line, not regenerated.\n' >> "$ROOT/agents/coding-agent.md"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || fail "stale: expected exit 1, got $rc"
grep -Fq 'FAIL (1 finding(s))' "$ROOT/eval-report.md" || fail "stale: expected exactly one finding"
finding="$(grep -F 'stale coding-agent' "$ROOT/eval-report.md" || true)"
[ -n "$finding" ] || fail "stale: finding must name coding-agent"
[[ "$finding" == *"agents/coding-agent.md"* ]] || fail "stale: finding must name agents/coding-agent.md"
[[ "$finding" == *"$REMEDY"* ]] || fail "stale: finding must carry remedy '$REMEDY'"
ok "edited canonical agent -> one stale finding naming the stem with remedy"

ROOT="$(new_root)"
printf '<!-- hand edit -->\n' >> "$ROOT/claude-code/agents/writ-reviewer.md"
rm "$ROOT/claude-code/agents/writ-tester.md"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || fail "multi: expected exit 1, got $rc"
grep -Fq 'FAIL (2 finding(s))' "$ROOT/eval-report.md" || fail "multi: expected one finding per reason line"
finding="$(grep -F 'stale review-agent' "$ROOT/eval-report.md" || true)"
[[ "$finding" == *"$REMEDY"* ]] || fail "multi: stale finding must carry remedy '$REMEDY'"
finding="$(grep -F 'missing testing-agent' "$ROOT/eval-report.md" || true)"
[[ "$finding" == *"$REMEDY"* ]] || fail "multi: missing finding must carry remedy '$REMEDY'"
ok "hand-edited and deleted agent files -> two findings"

ROOT="$(new_root)"
printf '# New Agent\n' > "$ROOT/agents/zz-new-agent.md"
printf '# Retired\n' > "$ROOT/claude-code/agents/writ-retired.md"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || fail "unmapped/orphan: expected exit 1, got $rc"
grep -Fq 'FAIL (2 finding(s))' "$ROOT/eval-report.md" || fail "unmapped/orphan: expected two findings"
finding="$(grep -F 'unmapped zz-new-agent' "$ROOT/eval-report.md" || true)"
[[ "$finding" == *"Add an OVERLAY entry"* ]] || fail "unmapped: remedy must say to add an OVERLAY entry"
[[ "$finding" == *"$REMEDY"* ]] || fail "unmapped: remedy must name '$REMEDY'"
finding="$(grep -F 'orphan writ-retired' "$ROOT/eval-report.md" || true)"
[[ "$finding" == *"claude-code/agents/writ-retired.md"* ]] || fail "orphan: finding must name the orphan file"
[[ "$finding" == *"Delete the orphan file"* ]] || fail "orphan: remedy must say to delete the orphan file"
[[ "$finding" == *"$REMEDY"* ]] || fail "orphan: remedy must name '$REMEDY'"
ok "unmapped agent and orphan file -> one finding each with their own remedy"

ROOT="$(new_root)"
rm "$ROOT/scripts/gen-claude-agents.py"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || fail "missing generator: expected exit 1, got $rc"
finding="$(grep -F 'Claude agent generator is missing' "$ROOT/eval-report.md" || true)"
[ -n "$finding" ] || fail "missing generator: finding must say the Claude agent generator is missing"
[[ "$finding" == *"Restore scripts/gen-claude-agents.py"* ]] || fail "missing generator: remedy must say to restore it"
ok "missing generator -> finding with restore remedy"

ROOT="$(new_root)"
printf 'import sys\nsys.exit(2)\n' > "$ROOT/scripts/gen-claude-agents.py"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || fail "crashing generator: expected exit 1, got $rc"
grep -Fq -- '--check exited 2' "$ROOT/eval-report.md" || fail "crashing generator: finding must report the exit code"
ok "generator --check exit 2 -> finding"

ROOT="$(new_root)"
printf 'import sys\nprint("fail")\nsys.exit(1)\n' > "$ROOT/scripts/gen-claude-agents.py"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || fail "silent failure: expected exit 1, got $rc"
grep -Fq 'FAIL (1 finding(s))' "$ROOT/eval-report.md" || fail "silent failure: expected exactly one finding"
grep -Fq -- '--check failed without a reason line.' "$ROOT/eval-report.md" \
  || fail "silent failure: finding must say --check failed without a reason line"
ok "generator --check exit 1 with no reason line -> one finding"

registry="$(awk '/^CHECKS=\(/{f=1} f && /^\)/{exit} f' "$EVAL")"
printf '%s\n' "$registry" | grep -Fxq "  claude-agents" \
  || fail "claude-agents must be registered in CHECKS=(...)"
printf '%s\n' "$registry" | grep -A1 -Fx "  codex-tomls" | grep -Fxq "  claude-agents" \
  || fail "claude-agents must be registered right after codex-tomls"
grep -q '^check_claude_agents()' "$EVAL" || fail "check_claude_agents must be defined"
ok "registration: claude-agents in CHECKS after codex-tomls; check_claude_agents defined"

printf '\nAll %d claude-agents check assertions passed.\n' "$pass_count"
