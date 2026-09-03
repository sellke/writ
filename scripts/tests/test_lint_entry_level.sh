#!/usr/bin/env bash
# Tests the entry_level consumer in scripts/lint-skill.sh
# (spec 2026-09-03-model-delegation, Story 5: AC-5.4).
#
# The VALUE grammar is already pinned by Story 1's fixtures in
# scripts/tests/test_lint_model_tier.sh (lines ~150-161): `high|standard|any`
# are clean, `max` and `High` are rejected with a ❌ naming all three allowed
# values. Those assertions are NOT repeated here.
#
# This file holds only what Story 5 adds:
#   (a) the 31 real commands/*.md all carry a valid entry_level — the lint
#       exits 0 over them and prints no line mentioning entry_level;
#   (b) ROUTING — lint-skill.sh was a SKILL.md lint. Pointing it at a command
#       file used to fail on skill-boundary body patterns (`Task(`, `/slash`)
#       and ADR-014 lifecycle checks that do not apply to commands. Command
#       paths are now routed to a value-checks-only pass, while a file whose
#       basename is SKILL.md keeps the full lint even when `commands/` appears
#       in its path (basename wins).
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
LINT="$REPO/scripts/lint-skill.sh"

pass_count=0
fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}
ok() {
  pass_count=$((pass_count + 1))
  printf 'PASS: %s\n' "$1"
}

WORK="$(mktemp -d "${TMPDIR:-/tmp}/writ-lint-entry-level.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT

count_of() {  # $1 needle, $2 haystack -> number of lines containing needle
  local n
  n=$(printf '%s\n' "$2" | grep -cF -- "$1" || true)
  printf '%s' "$n"
}

# ❌ FINDING lines only — the lint also prints a trailing
# "❌ N lint violation(s) found across input files" summary, which is not a
# finding and must not be counted as one.
finding_count() {  # $1 haystack
  local n
  n=$(printf '%s\n' "$1" | grep -F -- '❌' | grep -vcF 'lint violation(s) found' || true)
  printf '%s' "$n"
}

# A command-shaped body that the SKILL.md boundary lint rejects twice
# (Subagent dispatch + Slash command) and that lacks `status:`, so the
# lifecycle check would also fire under the full lint. Under command routing
# none of these may appear — only the entry_level value is judged.
BOUNDARY_BODY="$(printf '%s\n' \
  '# Fixture command' '' \
  'Spawn the worker with Task({ subagent_type: "generalPurpose" }).' '' \
  '/status')"

# usage: write_command <path> <entry_level line>
write_command() {
  mkdir -p "$(dirname "$1")"
  {
    printf '%s\n' '---'
    printf '%s\n' 'name: fixture'
    printf '%s\n' 'description: "Fixture command for the entry_level routing test."'
    printf '%s\n' 'problem: "..."'
    printf '%s\n' 'outcome: "..."'
    printf '%s\n' "$2"
    printf '%s\n' 'exit_criteria:'
    printf '%s\n' '  - "..."'
    printf '%s\n' '---'
    printf '\n%s\n' "$BOUNDARY_BODY"
  } > "$1"
}

# ---------------------------------------------------------------------------
# (a) The real tree: every commands/*.md passes, and nothing about entry_level
# is printed. Run from the repo root so the relative `commands/*.md` glob form
# — the one /refresh-command and the story's verification step use — is the
# form under test.
# ---------------------------------------------------------------------------
rc=0
out="$(cd "$REPO" && bash scripts/lint-skill.sh commands/*.md 2>&1)" || rc=$?
[ "$rc" -eq 0 ] || fail "lint over the real commands/*.md must exit 0, got $rc:
$out"
[ "$(count_of 'entry_level' "$out")" -eq 0 ] \
  || fail "lint over the real commands/*.md must print no entry_level line:
$(printf '%s\n' "$out" | grep -F 'entry_level')"
n_files=$(ls "$REPO"/commands/*.md | wc -l | tr -d ' ')
[ "$(count_of '✅' "$out")" -eq "$n_files" ] \
  || fail "expected one ✅ line per commands/*.md file ($n_files), got $(count_of '✅' "$out"):
$out"
ok "real commands/*.md: exit 0, no entry_level finding, one ✅ per file"

# ---------------------------------------------------------------------------
# (b) Routing: a command path gets value checks only.
# ---------------------------------------------------------------------------
FOO="$WORK/commands/foo.md"
write_command "$FOO" 'entry_level: max'
rc=0
out="$(bash "$LINT" "$FOO" 2>&1)" || rc=$?
[ "$rc" -eq 1 ] || fail "commands/foo.md with entry_level: max must exit 1, got $rc:
$out"
[ "$(finding_count "$out")" -eq 1 ] \
  || fail "commands/foo.md must produce exactly one ❌ finding (the value), got $(finding_count "$out"):
$out"
printf '%s\n' "$out" | grep -F '❌' | grep -qF "entry_level 'max'" \
  || fail "the single ❌ must be the entry_level value finding:
$out"
printf '%s\n' "$out" | grep -qF "'high', 'standard' or 'any'" \
  || fail "the ❌ must name the three allowed values (AC-5.4):
$out"
for boundary in 'Subagent dispatch' 'Slash command' 'Lifecycle-missing' 'description:'; do
  [ "$(count_of "$boundary" "$out")" -eq 0 ] \
    || fail "commands/foo.md must not receive the skill-boundary finding '$boundary':
$out"
done
ok "routing: commands/foo.md (entry_level: max) -> exit 1, one ❌, no boundary findings"

BAR="$WORK/commands/bar.md"
write_command "$BAR" 'entry_level: high'
rc=0
out="$(bash "$LINT" "$BAR" 2>&1)" || rc=$?
[ "$rc" -eq 0 ] || fail "commands/bar.md with entry_level: high must exit 0, got $rc:
$out"
[ "$(count_of '❌' "$out")" -eq 0 ] || fail "commands/bar.md must produce no ❌:
$out"
[ "$(count_of '✅' "$out")" -eq 1 ] || fail "commands/bar.md must print one ✅ line:
$out"
ok "routing: commands/bar.md (entry_level: high) -> exit 0, clean"

# Basename wins: a SKILL.md under a directory literally named `commands/` is
# still a skill and keeps the full boundary lint.
SKILL="$WORK/skills/commands/SKILL.md"
mkdir -p "$(dirname "$SKILL")"
{
  printf '%s\n' '---'
  printf '%s\n' 'name: fixture-skill'
  printf '%s\n' 'description: "How to exercise the routing rule with a skill under commands/."'
  printf '%s\n' 'status: candidate'
  printf '%s\n' '---'
  printf '\n%s\n' "$BOUNDARY_BODY"
} > "$SKILL"
rc=0
out="$(bash "$LINT" "$SKILL" 2>&1)" || rc=$?
[ "$rc" -eq 1 ] || fail "skills/commands/SKILL.md with boundary violations must exit 1, got $rc:
$out"
[ "$(finding_count "$out")" -ge 1 ] || fail "skills/commands/SKILL.md must receive ❌ boundary findings:
$out"
[ "$(count_of 'Subagent dispatch' "$out")" -eq 1 ] \
  || fail "skills/commands/SKILL.md must receive the Subagent dispatch finding (full lint):
$out"
ok "routing: skills/commands/SKILL.md -> basename wins, full boundary lint still applies"

printf '\nAll %d entry_level lint assertions passed.\n' "$pass_count"
