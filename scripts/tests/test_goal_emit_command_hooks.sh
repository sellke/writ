#!/usr/bin/env bash
# Spec 2026-09-09-phase11-stage4-goal-emit, Story 2: create-goal after save names
# goal-emit.py and treats emit verdicts as notes. [AC-2.1, AC-2.2, AC-2.3, AC-2.5]
# Spec 2026-11-06-lean-implement-phase, Story 2: /implement-phase no longer emits;
# only /create-goal does. [AC-2.4]
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
CREATE="$REPO/commands/create-goal.md"
PHASE="$REPO/commands/implement-phase.md"
STORY="$REPO/commands/implement-story.md"
CONTRACT="$REPO/.writ/docs/agent-cli-contract.md"

fail() { printf 'FAIL: %s\n' "$1" >&2; exit 1; }
ok() { printf 'PASS: %s\n' "$1"; }

# Work in a temp tree copy of the create-goal command so the assertion
# harness never writes the real repo.
TMP="$(mktemp -d "${TMPDIR:-/tmp}/goal-emit-hooks.XXXXXX")"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT
mkdir -p "$TMP/commands"
cp "$CREATE" "$TMP/commands/create-goal.md"
CREATE_COPY="$TMP/commands/create-goal.md"

grep -q '### Phase 3: Decision and Save' "$CREATE_COPY" \
  || fail "create-goal.md must keep Phase 3 Decision and Save"
grep -F 'python3 scripts/goal-emit.py emit --card' "$CREATE_COPY" \
  || fail "create-goal.md must invoke python3 scripts/goal-emit.py emit --card after save"
python3 - "$CREATE_COPY" <<'PY' || fail "emit --card must appear after Phase 3 save"
import sys
text = open(sys.argv[1], encoding="utf-8").read()
phase3 = text.find("### Phase 3: Decision and Save")
save = text.find("**save**: write the file")
emit = text.find("python3 scripts/goal-emit.py emit --card")
assert phase3 != -1 and save != -1 and emit != -1 and phase3 < save < emit, (phase3, save, emit)
PY
ok "create-goal Phase 3 save plus emit --card"

grep -qi 'loop: no' "$CREATE_COPY" \
  || fail "create-goal.md must mention loop: no"
grep -q 'add_note' "$CREATE_COPY" \
  || fail "create-goal.md must add_note emit verdicts"
grep -q 'loop_no' "$CREATE_COPY" \
  || fail "create-goal.md must name unverifiable loop_no as a note"
ok "create-goal loop: no is notes-only"

# Notes-only for fail/unverifiable; finding only for missing helper / exit 2
grep -q 'add_finding' "$CREATE_COPY" \
  || fail "create-goal.md must add_finding when helper is missing or exits 2"
grep -q 'exits 2' "$CREATE_COPY" || grep -q 'exit 2' "$CREATE_COPY" \
  || fail "create-goal.md must name helper exit 2 as a finding"
ok "helper missing / exit 2 is a finding"

# /create-goal is the only command that emits: the phase command no longer
# runs goal-emit.py, and the contract row no longer lists it as a caller.
if grep -q 'goal-emit.py' "$PHASE"; then
  fail "implement-phase.md must not name goal-emit.py (emit lives in /create-goal)"
fi
grep -E '^\| `goal-emit\.py` \|' "$CONTRACT" | grep -q 'commands/create-goal.md' \
  || fail "agent-cli-contract.md goal-emit.py row must list commands/create-goal.md"
if grep -E '^\| `goal-emit\.py` \|' "$CONTRACT" | grep -q 'commands/implement-phase.md'; then
  fail "agent-cli-contract.md goal-emit.py row must not list commands/implement-phase.md"
fi
ok "implement-phase emits no Goal files; create-goal is the only emit caller"

# Core Rule 4 and no /goal registration
grep -q 'never registers a `/goal` hook' "$CREATE_COPY" \
  || fail "create-goal Core Rule 4 must still refuse /goal registration"
grep -q 'never iterates' "$CREATE_COPY" \
  || fail "create-goal Core Rule 4 must still refuse iterate"
grep -q 'never calls `/create-spec`' "$CREATE_COPY" \
  || fail "create-goal Core Rule 4 must still refuse /create-spec"
ok "create-goal Core Rule 4 intact"

# implement-story spawn unchanged — the real file, not a copy, must not
# mention goal-emit
if grep -q 'goal-emit.py' "$STORY"; then
  fail "implement-story.md must not name goal-emit.py (spawn unchanged)"
fi
ok "implement-story.md spawn unchanged"

printf '\nAll goal-emit command-hook assertions passed.\n'
