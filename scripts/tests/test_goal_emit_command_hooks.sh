#!/usr/bin/env bash
# Story 2: create-goal after save + implement-phase origin emit
# name goal-emit.py and treat emit verdicts as notes. [AC-2.1, AC-2.2, AC-2.3, AC-2.5]
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
CREATE="$REPO/commands/create-goal.md"
PHASE="$REPO/commands/implement-phase.md"
STORY="$REPO/commands/implement-story.md"

fail() { printf 'FAIL: %s\n' "$1" >&2; exit 1; }
ok() { printf 'PASS: %s\n' "$1"; }

# Work in a temp tree copy of the two command files so the assertion
# harness never writes the real repo.
TMP="$(mktemp -d "${TMPDIR:-/tmp}/goal-emit-hooks.XXXXXX")"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT
mkdir -p "$TMP/commands"
cp "$CREATE" "$TMP/commands/create-goal.md"
cp "$PHASE" "$TMP/commands/implement-phase.md"
CREATE_COPY="$TMP/commands/create-goal.md"
PHASE_COPY="$TMP/commands/implement-phase.md"

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

grep -F 'python3 scripts/goal-emit.py emit --card' "$PHASE_COPY" \
  || fail "implement-phase.md must invoke python3 scripts/goal-emit.py emit --card"
grep -q 'Origin:' "$PHASE_COPY" \
  || fail "implement-phase.md must resolve origin from spec Origin:"
grep -q 'spec_ref' "$PHASE_COPY" \
  || fail "implement-phase.md must resolve origin from issue spec_ref"
grep -q 'add_note' "$PHASE_COPY" \
  || fail "implement-phase.md must add_note missing origin / emit verdicts"
ok "implement-phase origin emit named"

# Notes-only for fail/unverifiable; finding only for missing helper / exit 2
for file in "$CREATE_COPY" "$PHASE_COPY"; do
  grep -q 'add_finding' "$file" \
    || fail "$(basename "$file") must add_finding when helper is missing or exits 2"
  grep -q 'exits 2' "$file" || grep -q 'exit 2' "$file" \
    || fail "$(basename "$file") must name helper exit 2 as a finding"
done
ok "helper missing / exit 2 is a finding"

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
