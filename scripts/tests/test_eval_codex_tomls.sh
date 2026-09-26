#!/usr/bin/env bash
# Tests check_codex_tomls (Story 1 of 2026-09-26-arch-lint-and-follow-ups,
# AC-1.5). Runs eval.sh against a temp copy; never touches the real codex/agents/.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
EVAL="$REPO/scripts/eval.sh"
GEN="$REPO/scripts/gen-codex-agent-tomls.py"
REMEDY='python3 scripts/gen-codex-agent-tomls.py'

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
  mkdir -p "$root/scripts" "$root/codex/agents"
  cp "$EVAL" "$root/scripts/eval.sh"
  cp "$GEN" "$root/scripts/gen-codex-agent-tomls.py"
  cp -R "$REPO/agents" "$root/agents"
  python3 "$root/scripts/gen-codex-agent-tomls.py" >/dev/null
  printf "%s" "$root"
}

run_check() {
  local root="$1" rc=0
  ( cd "$root" && bash scripts/eval.sh --check=codex-tomls --report=eval-report.md >/dev/null 2>&1 ) || rc=$?
  printf "%s" "$rc"
}

ROOT="$(new_root)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 0 ] || fail "fresh: expected exit 0, got $rc"
awk '/^## codex-tomls$/{f=1; next} f && NF {print; exit}' "$ROOT/eval-report.md" | grep -Fxq 'PASS' \
  || fail "fresh: codex-tomls section should PASS"
ok "freshly generated TOMLs -> PASS, exit 0"

ROOT="$(new_root)"
printf '# hand edit\n' >> "$ROOT/codex/agents/review-agent.toml"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || fail "stale: expected exit 1, got $rc"
grep -Fq 'FAIL (1 finding(s))' "$ROOT/eval-report.md" || fail "stale: expected exactly one finding"
finding="$(grep -F 'stale review-agent' "$ROOT/eval-report.md" || true)"
[ -n "$finding" ] || fail "stale: finding must name review-agent"
[[ "$finding" == *"$REMEDY"* ]] || fail "stale: finding must carry remediation '$REMEDY'"
ok "hand-edited TOML -> one finding naming the stem with remediation"

ROOT="$(new_root)"
printf '# hand edit\n' >> "$ROOT/codex/agents/coding-agent.toml"
rm "$ROOT/codex/agents/testing-agent.toml"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || fail "multi: expected exit 1, got $rc"
grep -Fq 'FAIL (2 finding(s))' "$ROOT/eval-report.md" || fail "multi: expected one finding per reason line"
grep -Fq 'stale coding-agent' "$ROOT/eval-report.md" || fail "multi: stale finding missing"
grep -Fq 'missing testing-agent' "$ROOT/eval-report.md" || fail "multi: missing finding missing"
ok "two problems -> two findings"

ROOT="$(new_root)"
printf '# New Agent\n' > "$ROOT/agents/zz-new-agent.md"
printf 'name = "retired-agent"\n' > "$ROOT/codex/agents/retired-agent.toml"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || fail "unmapped/orphan: expected exit 1, got $rc"
grep -Fq 'FAIL (2 finding(s))' "$ROOT/eval-report.md" || fail "unmapped/orphan: expected two findings"
finding="$(grep -F 'unmapped zz-new-agent' "$ROOT/eval-report.md" || true)"
[[ "$finding" == *"Add PURPOSES and SANDBOX entries"* ]] || fail "unmapped: remediation must name PURPOSES and SANDBOX"
finding="$(grep -F 'orphan retired-agent' "$ROOT/eval-report.md" || true)"
[[ "$finding" == *"Delete the orphan TOML"* ]] || fail "orphan: remediation must say to delete the orphan TOML"
ok "unmapped agent and orphan TOML -> one finding each with their own remediation"

ROOT="$(new_root)"
rm "$ROOT/scripts/gen-codex-agent-tomls.py"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || fail "missing helper: expected exit 1, got $rc"
grep -Fq 'scripts/gen-codex-agent-tomls.py' "$ROOT/eval-report.md" \
  || fail "missing helper: finding must name the helper"
ok "missing helper -> finding"

awk '/^CHECKS=\(/{f=1} f && /^\)/{exit} f' "$EVAL" | grep -Fxq "  codex-tomls" \
  || fail "codex-tomls must be registered in CHECKS=(...)"
grep -q '^check_codex_tomls()' "$EVAL" || fail "check_codex_tomls must be defined"
ok "registration: codex-tomls in CHECKS; check_codex_tomls defined"

printf '\nAll %d codex-tomls check assertions passed.\n' "$pass_count"
