#!/usr/bin/env bash
# /new-skill in a project that got Writ from install.sh or the Claude Code
# plugin. Neither creates .writ/manifest.yaml, so the command's name check must
# read what is installed, and its write must land in the platform's skills
# folder without creating a manifest.
#
# For each install.sh platform, and for the plugin in a project with no
# install, this runs the skill-target.py call exactly as the installed
# new-skill.md spells it, and checks:
#   - an installed command, agent, and skill name each fail, naming the file
#   - a free name passes with the platform's skills folder as target and
#     `manifest: none`
#   - the project (and the plugin) are byte-identical afterwards, with no
#     .writ/manifest.yaml
#
# Runs the real install.sh from this checkout into temp projects. Does `git
# init`: run outside any sandbox. Never point it at the Writ repo itself.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
WORK=$(mktemp -d "${TMPDIR:-/tmp}/writ-new-skill-installed.XXXXXX")
trap 'rm -rf "$WORK"' EXIT
# skill-target.py prints plugin paths resolved; match that form.
WORK=$(cd "$WORK" && pwd -P)

FREE=zz-free-skill
pass_count=0

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

ok() {
  pass_count=$((pass_count + 1))
  printf 'PASS: %s\n' "$1"
}

# Every file under DIR (except .git) with its hash, one per line.
snapshot() {
  (cd "$1" && find . -path ./.git -prune -o -type f -print | LC_ALL=C sort | while read -r f; do
    printf '%s  %s\n' "$(shasum -a 256 "$f" | cut -d' ' -f1)" "$f"
  done)
}

# The skill-target.py call in FILE, as the command spells it.
call_in() {
  local line
  line=$(grep -m1 'skill-target.py check <name> --platform <platform>' "$1" | sed 's/^ *//') \
    || fail "$1: no skill-target.py call"
  printf '%s' "$line"
}

# run_call CALL NAME PLATFORM PROJECT [PLUGIN]: print the call's stdout.
run_call() {
  local cmd
  cmd=${1//<name>/$2}
  cmd=${cmd//<platform>/$3}
  (cd "$4" && CLAUDE_PLUGIN_ROOT="${5:-}" bash -c "$cmd") || true
}

# expect_taken LABEL CALL NAME PLATFORM PROJECT TAKEN [PLUGIN]
expect_taken() {
  local out
  out=$(run_call "$2" "$3" "$4" "$5" "${7:-}")
  [ "$(printf '%s\n' "$out" | head -1)" = fail ] || fail "$1: $3 did not fail: $out"
  printf '%s\n' "$out" | grep -qxF "reason: name taken by $6" \
    || fail "$1: $3 does not name '$6': $out"
}

# expect_free LABEL CALL PLATFORM PROJECT TARGET [PLUGIN]
expect_free() {
  local out
  out=$(run_call "$2" "$FREE" "$3" "$4" "${6:-}")
  [ "$(printf '%s\n' "$out" | head -1)" = pass ] || fail "$1: $FREE did not pass: $out"
  printf '%s\n' "$out" | grep -qxF "target: $5" || fail "$1: target is not $5: $out"
  printf '%s\n' "$out" | grep -qxF "manifest: none" || fail "$1: manifest is not none: $out"
}

# check_platform PLATFORM DIR AGENT_FILE SKILLS_DIR
check_platform() {
  local platform="$1" dir="$2" agent="$3" skills="$4" proj="$WORK/$1" out before call
  mkdir -p "$proj"
  git -C "$proj" init -q
  out=$(cd "$proj" && bash "$REPO/scripts/install.sh" --platform "$platform" --no-commit 2>&1) \
    || fail "$platform: install exited non-zero: $out"
  [ ! -e "$proj/.writ/manifest.yaml" ] || fail "$platform: install created .writ/manifest.yaml"
  [ -f "$proj/$agent" ] || fail "$platform: fixture: no $agent"
  [ -f "$proj/$skills/tdd-cycle/SKILL.md" ] || fail "$platform: fixture: no $skills/tdd-cycle"

  call=$(call_in "$proj/$dir/commands/new-skill.md")
  [ "$call" = 'python3 scripts/skill-target.py check <name> --platform <platform>' ] \
    || fail "$platform: unexpected call: $call"
  before=$(snapshot "$proj")
  expect_taken "$platform" "$call" review "$platform" "$proj" "command $dir/commands/review.md"
  expect_taken "$platform" "$call" "$(basename "${agent%.*}")" "$platform" "$proj" "agent $agent"
  expect_taken "$platform" "$call" tdd-cycle "$platform" "$proj" "skill $skills/tdd-cycle"
  expect_free "$platform" "$call" "$platform" "$proj" "$skills/$FREE/SKILL.md"
  [ "$(snapshot "$proj")" = "$before" ] || fail "$platform: the calls changed the project"
  [ ! -e "$proj/.writ/manifest.yaml" ] || fail "$platform: a call created .writ/manifest.yaml"
  ok "$platform install: installed names are taken, $FREE targets $skills/, no manifest"
}

check_platform claude .claude .claude/agents/writ-coder.md .claude/skills
check_platform cursor .cursor .cursor/agents/coding-agent.md .cursor/skills
check_platform codex .codex .codex/agents/coding-agent.toml .agents/skills

# ----- Claude Code plugin, no install -----
PLUGIN="$WORK/plugin"
cp -R "$REPO/plugins/writ" "$PLUGIN"
PROJ="$WORK/plugin-project"
mkdir -p "$PROJ"
git -C "$PROJ" init -q
call=$(call_in "$PLUGIN/commands/new-skill.md")
[ "$call" = 'python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skill-target.py check <name> --platform <platform>' ] \
  || fail "plugin: unexpected call: $call"
plugin_before=$(snapshot "$PLUGIN")
before=$(snapshot "$PROJ")
expect_taken plugin "$call" review claude "$PROJ" "command $PLUGIN/commands/review.md" "$PLUGIN"
expect_taken plugin "$call" writ-coder claude "$PROJ" "agent $PLUGIN/agents/writ-coder.md" "$PLUGIN"
expect_taken plugin "$call" tdd-cycle claude "$PROJ" "skill $PLUGIN/skills/tdd-cycle" "$PLUGIN"
expect_free plugin "$call" claude "$PROJ" ".claude/skills/$FREE/SKILL.md" "$PLUGIN"
[ "$(snapshot "$PROJ")" = "$before" ] || fail "plugin: the calls changed the project"
[ "$(snapshot "$PLUGIN")" = "$plugin_before" ] || fail "plugin: the calls changed the plugin"
[ ! -e "$PROJ/.writ/manifest.yaml" ] || fail "plugin: a call created .writ/manifest.yaml"
ok "plugin: the plugin's names are taken, $FREE targets .claude/skills/, no manifest"

printf 'test_new_skill_installed: %d passed\n' "$pass_count"
