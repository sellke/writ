#!/usr/bin/env bash
# Tests scripts/eval.sh check_entry_level() — the non-blocking presence note
# for the ADR-024 A3 `entry_level:` frontmatter field
# (spec 2026-09-03-model-delegation, Story 5: AC-5.5).
#
# Contract: for every commands/*.md except `_*.md`, a missing `entry_level:`
# key in the `---` frontmatter produces ONE add_note line naming the file. It
# is a note, never a finding — the eval still ends `Findings: 0` and exits 0.
#
# Scoping: the predicate is FRONTMATTER-scoped, not file-wide. A column-0
# `entry_level:` line inside a fenced body block (commands/new-command.md
# carries exactly such a scaffold literal) must not satisfy the check, or a
# command that documents the field would be exempt from declaring it.
#
# Harness: scripts/eval.sh derives PROJECT_ROOT from its own directory, so
# copying it into a temp `scripts/` dir beside a synthetic `commands/` tree
# exercises the real check with no flag, no env var, and no mutation of the
# repository (same approach as test_eval_length_caps.sh).
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

ROOT="$(mktemp -d "${TMPDIR:-/tmp}/writ-eval-entry-level.XXXXXX")"
cleanup() {
  local rc=$?
  rm -rf "$ROOT"
  return "$rc"
}
trap cleanup EXIT

mkdir -p "$ROOT/scripts" "$ROOT/commands" "$ROOT/.writ/state"
cp "$EVAL" "$ROOT/scripts/eval.sh"

# usage: write_command <name> <with|without> -- minimal command frontmatter
write_command() {
  local path="$ROOT/commands/$1.md"
  {
    printf '%s\n' '---'
    printf '%s\n' "name: $1"
    printf '%s\n' 'description: "Synthetic command."'
    printf '%s\n' 'problem: "..."'
    printf '%s\n' 'outcome: "..."'
    [ "$2" = with ] && printf '%s\n' 'entry_level: high'
    printf '%s\n' 'exit_criteria:'
    printf '%s\n' '  - "..."'
    printf '%s\n' '---'
    printf '\n%s\n' '## Overview'
  } > "$path"
  printf '%s' "$path"
}

write_command a with    >/dev/null
write_command b without >/dev/null
# c: no field in the frontmatter, but a column-0 declaration inside a fenced
# body block — the scaffold shape new-command.md has. Must still be noted.
C="$(write_command c without)"
{
  printf '\n%s\n' 'Scaffold:'
  printf '%s\n' '```markdown'
  printf '%s\n' '---'
  printf '%s\n' 'entry_level: high'
  printf '%s\n' '---'
  printf '%s\n' '```'
} >> "$C"
write_command _preamble without >/dev/null

rc=0
( cd "$ROOT" && bash scripts/eval.sh --check=entry-level --report=eval-report.md >/dev/null 2>&1 ) || rc=$?
REPORT="$ROOT/eval-report.md"
[ -f "$REPORT" ] || fail "--check=entry-level produced no report (exit $rc) — is the check registered in CHECKS?"
report="$(cat "$REPORT")"

[ "$rc" -eq 0 ] || fail "--check=entry-level must exit 0 (notes never block), got $rc:
$report"
ok "exit 0 with missing entry_level fields present"

printf '%s\n' "$report" | grep -qF -- '- Findings: 0' \
  || fail "report must end Findings: 0 — the presence pass is add_note, never add_finding:
$report"
grep -q '^FAIL' "$REPORT" && fail "entry-level check must PASS; a note is not a finding:
$report"
ok "report carries Findings: 0 and the check PASSes"

grep -Fq 'NOTE [commands/b.md]: no entry_level: in frontmatter (ADR-024 A3).' "$REPORT" \
  || fail 'expected: NOTE [commands/b.md]: no entry_level: in frontmatter (ADR-024 A3).
'"$report"
ok "b.md (no field anywhere) is noted"

grep -Fq 'NOTE [commands/c.md]: no entry_level: in frontmatter (ADR-024 A3).' "$REPORT" \
  || fail 'expected: NOTE [commands/c.md] — a fenced body entry_level: line must not satisfy the frontmatter check
'"$report"
ok "c.md (field only inside a fenced body block) is still noted — predicate is frontmatter-scoped"

grep -Fq 'system-instructions.md § Model Tiers' "$REPORT" \
  || fail "the note must point the reader at system-instructions.md § Model Tiers for the Q1/Q2 derivation:
$report"
ok "note names the derivation source"

grep -q 'commands/a.md' "$REPORT" && fail "a.md declares entry_level and must not be noted:
$report"
ok "a.md (field present) is not noted"

grep -q '_preamble.md' "$REPORT" && fail "commands/_preamble.md is not a command and must never be noted:
$report"
ok "_preamble.md is skipped"

n_notes="$(grep -c 'no entry_level: in frontmatter' "$REPORT" || true)"
[ "$n_notes" -eq 2 ] || fail "expected exactly 2 notes (b.md, c.md), got $n_notes:
$report"
ok "exactly one note per missing file"

printf '\nAll %d entry_level eval-note assertions passed.\n' "$pass_count"
