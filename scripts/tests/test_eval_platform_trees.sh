#!/usr/bin/env bash
# Tests check_platform_trees in eval.sh (Story 4 of
# 2026-10-22-generated-platform-trees, AC-4.4). Each case runs eval.sh in a
# temp root holding eval.sh, every top-level scripts/ file, and what the
# driver's --check reads: adapters/, agents/, commands/, skills/, the three
# platform directories, the Claude Code plugin tree (plugins/, .claude-plugin/;
# the claude-code-plugin target), system-instructions.md, the manifest,
# and VERSION. Never touches the repo's generated files.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
EVAL="$REPO/scripts/eval.sh"
DRIVER="scripts/gen-platform-trees.py"
REMEDY='Run python3 scripts/gen-platform-trees.py, then commit the regenerated files.'
CLEAN_SUMMARY='gen-platform-trees: pass (0 stale, 0 missing, 0 orphan, 0 unmapped, 0 vendor)'

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

# A temp root that is a fresh copy of the committed tree's inputs and
# generated files.
new_root() {
  local root
  root="$(mktemp -d)"
  TMP_ROOTS+=("$root")
  mkdir -p "$root/scripts" "$root/.writ"
  cp "$EVAL" "$root/scripts/eval.sh"
  find "$REPO/scripts" -maxdepth 1 -type f -exec cp -p {} "$root/scripts/" \;
  cp -R "$REPO/adapters" "$REPO/agents" "$REPO/commands" "$REPO/skills" \
        "$REPO/cursor" "$REPO/claude-code" "$REPO/codex" \
        "$REPO/plugins" "$REPO/.claude-plugin" "$root/"
  cp "$REPO/system-instructions.md" "$root/system-instructions.md"
  cp "$REPO/.writ/manifest.yaml" "$root/.writ/manifest.yaml"
  cp "$REPO/VERSION" "$root/VERSION"
  printf "%s" "$root"
}

run_check() {
  local root="$1" rc=0
  ( cd "$root" && bash scripts/eval.sh --check=platform-trees --report=eval-report.md >/dev/null 2>&1 ) || rc=$?
  printf "%s" "$rc"
}

section() {
  awk '/^## platform-trees$/{f=1; next} f && /^## /{exit} f' "$1/eval-report.md"
}

run_errors() {
  awk -F': ' '/^- Run errors: /{print $2}' "$1/eval-report.md"
}

# AC-4.4: a fresh copy passes; the summary is a note.
ROOT="$(new_root)"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 0 ] || fail "fresh: expected exit 0, got $rc"
section "$ROOT" | awk 'NF {print; exit}' | grep -Fxq 'PASS' || fail "fresh: platform-trees section should PASS"
section "$ROOT" | grep -Fq "NOTE [platform-trees]: $CLEAN_SUMMARY" || fail "fresh: summary line should be a note"
[ "$(run_errors "$ROOT")" = "0" ] || fail "fresh: expected 0 run errors"
ok "fresh tree -> PASS, exit 0, summary note"

# AC-4.4: a hand edit to cursor/writ.mdc -> one stale finding with the remedy.
ROOT="$(new_root)"
printf '\nhand edit\n' >> "$ROOT/cursor/writ.mdc"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || fail "stale: expected exit 1, got $rc"
section "$ROOT" | grep -Fxq 'FAIL (1 finding(s))' || fail "stale: expected exactly one finding"
finding="$(section "$ROOT" | grep -F 'stale cursor/writ.mdc' || true)"
[ -n "$finding" ] || fail "stale: finding must name cursor/writ.mdc"
[[ "$finding" == '- `cursor/writ.mdc`: gen-platform-trees --check: stale cursor/writ.mdc'* ]] \
  || fail "stale: finding must be located at cursor/writ.mdc: $finding"
[[ "$finding" == *"$REMEDY"* ]] || fail "stale: finding must carry the remedy: $finding"
ok "hand-edited cursor/writ.mdc -> one stale finding with the remedy"

# AC-4.4: a vendor token in a command -> one vendor finding naming file:line,
# beside the stale plugin copy of that command (the claude-code-plugin target).
ROOT="$(new_root)"
printf '\n`TodoWrite`\n' >> "$ROOT/commands/status.md"
line="$(wc -l < "$ROOT/commands/status.md" | tr -d ' ')"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 1 ] || fail "vendor: expected exit 1, got $rc"
section "$ROOT" | grep -Fxq 'FAIL (2 finding(s))' || fail "vendor: expected exactly two findings"
section "$ROOT" | grep -Fq -- '- `plugins/writ/commands/status.md`: gen-platform-trees --check: stale plugins/writ/commands/status.md' \
  || fail "vendor: the plugin copy of the edited command must be a stale finding"
finding="$(section "$ROOT" | grep -F "vendor TodoWrite in commands/status.md:$line" || true)"
[ -n "$finding" ] || fail "vendor: finding must name commands/status.md:$line"
[[ "$finding" == "- \`commands/status.md:$line\`: gen-platform-trees --check: vendor TodoWrite in commands/status.md:$line"* ]] \
  || fail "vendor: finding must be located at commands/status.md:$line: $finding"
[[ "$finding" == *"$REMEDY"* ]] || fail "vendor: finding must carry the remedy: $finding"
ok "vendor token in a command -> one vendor finding naming file:line with the remedy"

# AC-4.4: a helper exit of 2 is a run error, not a pass.
ROOT="$(new_root)"
printf 'import sys\nsys.exit(2)\n' > "$ROOT/$DRIVER"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 2 ] || fail "exit 2: expected exit 2 (run error), got $rc"
section "$ROOT" | grep -Fq "$DRIVER" || fail "exit 2: finding must name $DRIVER"
section "$ROOT" | grep -Fq -- '--check exited 2 without a verdict' || fail "exit 2: finding must say the helper exited 2 without a verdict"
[ "$(run_errors "$ROOT")" = "1" ] || fail "exit 2: expected 1 run error, got $(run_errors "$ROOT")"
ok "helper exit 2 -> run error, finding names the driver"

# A missing helper is a run error and a finding.
ROOT="$(new_root)"
rm "$ROOT/$DRIVER"
rc="$(run_check "$ROOT")"
[ "$rc" -eq 2 ] || fail "missing helper: expected exit 2 (run error), got $rc"
section "$ROOT" | grep -Fq "$DRIVER" || fail "missing helper: finding must name $DRIVER"
[ "$(run_errors "$ROOT")" = "1" ] || fail "missing helper: expected 1 run error"
ok "missing helper -> run error, finding names the driver"

# AC-4.4: platform-trees is registered once, after claude-md, so the full run and CI include it.
checks="$(awk '/^CHECKS=\(/{f=1; next} f && /^\)/{exit} f' "$EVAL")"
[ "$(printf '%s\n' "$checks" | grep -cFx '  platform-trees')" -eq 1 ] \
  || fail "platform-trees must be registered exactly once in CHECKS=(...)"
printf '%s\n' "$checks" | sed -n '/^  claude-md$/,$p' | grep -Fxq '  platform-trees' \
  || fail "platform-trees must come after claude-md in CHECKS=(...)"
grep -q '^check_platform_trees()' "$EVAL" || fail "check_platform_trees must be defined"
ok "registration: platform-trees in CHECKS after claude-md; check_platform_trees defined"

printf '\nAll %d platform-trees check assertions passed.\n' "$pass_count"
