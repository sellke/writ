# UAT Plan: Phase 11 Stage 4a: Goal Emit

> **Generated:** 2026-09-25
> **Spec:** `.writ/specs/2026-09-09-phase11-stage4-goal-emit/`
> **Stories Covered:** 3 of 3 completed
> **Total Scenarios:** 21

## How to Use This Plan

1. Work through scenarios in order (grouped by story, ordered by priority).
2. Run every command from the repository root. Scenarios marked "scratch" write only under a temp directory.
3. Mark Pass or Fail. Add notes for any output that differs from the Expected Result.
4. File a Fail as an issue or feed it back to the spec. Do not fix it inline.
5. The feature passes UAT when every scenario passes, or when a failure is accepted as a known limitation.

> **Scratch setup used by most scenarios.** Run once before starting:
> ```
> export UAT=$(mktemp -d)
> export F=scripts/tests/fixtures/goal-emit
> ```
> Delete with `rm -rf "$UAT"` when done. Scenario 14 is the only one that writes inside the repo, and it tells you how to clean up.

## What This Spec Delivered

`scripts/goal-emit.py` turns a `loop: yes` Goal Card into `GOAL.md` and `VERIFY.md` and prints a `/goal` invoke line copied byte-for-byte from `adapters/claude-code.md`. `/create-goal` runs it after saving a card; `/implement-phase` runs it (Step 1.4) when a spec's origin is a Goal Card. The Claude Code adapter tells the human to paste the printed line unchanged. `eval.sh` has a `goal-emit` check. Proof is gold-file equality; no live `/goal` session was run.

## Honest Notes (read before signing off)

1. **The invoke line is the same for every card.** It is the `/implement-phase` stop-hook template. Nothing from the card goes into it. It contains a literal `{timestamp}` placeholder in the state-file path. "Paste unchanged, zero manual edits" means the `/goal` evaluator must work out which state file `{timestamp}` refers to. Nobody has tested that in a live session. Scenario 20 covers it.
2. **VERIFY.md's "how to check" line cannot be run as written when the card has a `spec_ref`.** It says "run `python3 scripts/exit-criteria.py` against the spec named by spec_ref". `exit-criteria.py check` takes `--command` and `--state` (a run record), not a spec. The real Phase 11 card also lists six specs in `spec_ref`. Scenario 8 covers it.
3. **`.writ/goals/` is not gitignored.** An emit of the real Phase 11 card already sits untracked at `.writ/goals/2026-09-05-writ-contract-and-verifier-layer/`. The spec does not say whether emitted files should be committed. Scenario 21 covers it.
4. **The eval check relays the whole invoke text as notes.** A `pass` run adds 12 note lines, 10 of them the `/goal` template. This is harmless but noisy.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: CLI + Schema — goal-emit.py Emit and Check | ✅ Covered | 8 | AC: 5, Errors: 2, Drift: 1 |
| Story 2: Hooks — create-goal After Save and implement-phase Origin Emit | ✅ Covered | 6 | AC: 5, Experience: 1 |
| Story 3: Adapter + Eval + Gold Round-Trip | ✅ Covered | 7 | AC: 5, Experience: 2 |

Error map rows "`emit --card` missing path" and "`emit` on `loop: no`" are covered by Scenario 3; "`eval.sh` live" and "Helper missing" by Scenarios 16–17. Shadow paths Happy / Nil / Empty are covered by Scenarios 1 and 3; Upstream (helper exit 2) by Scenario 16.

---

## Story 1: CLI + Schema — goal-emit.py Emit and Check

### Scenario 1: Emit writes both files, matches gold, and overwrites in place

**Source:** Acceptance Criteria (AC-1.1) — Story 1

**Preconditions:**
- `python3` 3.9 or later; scratch setup done.

**Steps:**
1. `python3 scripts/goal-emit.py emit --card $F/loop-yes/card.md --out "$UAT/out" > "$UAT/stdout.txt"; echo "exit=$?"`
2. `head -2 "$UAT/stdout.txt"`
3. `diff "$UAT/out/GOAL.md" $F/loop-yes/GOAL.md && diff "$UAT/out/VERIFY.md" $F/loop-yes/VERIFY.md && echo FILES-EQUAL`
4. `grep -c "Production remains a human decision" "$UAT/out/GOAL.md" "$UAT/out/VERIFY.md"`
5. Record `wc -c "$UAT/out/GOAL.md"`, run step 1 again, then run `wc -c` again.
6. Default location: `mkdir -p "$UAT/repo" && cp $F/loop-yes/card.md "$UAT/repo/my-card.md" && python3 scripts/goal-emit.py emit --card "$UAT/repo/my-card.md" --project "$UAT/repo" >/dev/null && ls "$UAT/repo/.writ/goals/"`
7. `grep -n "^import\|^from" scripts/goal-emit.py`

**Expected Result:**
- Step 1: `exit=0`.
- Step 2: `pass`, then `goal-emit: pass (GOAL.md and VERIFY.md)`. The `/goal` text follows the summary.
- Step 3: `FILES-EQUAL`.
- Step 4: each file reports `1`.
- Step 5: same byte count both times (1140). Re-emit replaces the files; it does not append.
- Step 6: prints `my-card`. The default output folder is `.writ/goals/<card filename without .md>/`.
- Step 7: only `__future__`, `argparse`, `re`, `sys`, `pathlib`, `typing`. No LLM or network library.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `scripts/goal-emit.py` (invoke is a pinned literal); commit `0cbe967`

**Notes:**

---

### Scenario 2: Check validates an emit folder and catches a missing boundary sentence

**Source:** Acceptance Criteria (AC-1.2) — Story 1

**Preconditions:**
- `$UAT/out` from Scenario 1.

**Steps:**
1. `cp $F/loop-yes/card.md "$UAT/card-copy.md"`
2. `python3 scripts/goal-emit.py check --card "$UAT/card-copy.md" --out "$UAT/out"; echo "exit=$?"`
3. `cmp $F/loop-yes/card.md "$UAT/card-copy.md" && echo CARD-UNCHANGED`
4. Delete the sentence from VERIFY.md: `sed -i.bak 's/Production remains a human decision.//' "$UAT/out/VERIFY.md"`
5. Run step 2 again.

**Expected Result:**
- Step 2: `pass`, summary; `exit=0`.
- Step 3: `CARD-UNCHANGED`.
- Step 5: `fail`, `reason: missing_boundary`, `goal-emit: fail (missing_boundary)`; `exit=1`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 3: Verdicts for missing card, `loop: no`, and bad arguments

**Source:** Acceptance Criteria (AC-1.3); Error Map (`emit --card` missing, `emit` on `loop: no`); Shadow Paths (Nil, Empty) — Story 1

**Preconditions:**
- Scratch setup done.

**Steps:**
1. `python3 scripts/goal-emit.py emit; echo "exit=$?"`
2. `python3 scripts/goal-emit.py emit --card "$UAT/nope.md" --out "$UAT/x"; echo "exit=$?"; ls "$UAT/x"`
3. `python3 scripts/goal-emit.py emit --card $F/loop-no/card.md --out "$UAT/no"; echo "exit=$?"; ls "$UAT/no"`
4. `python3 scripts/goal-emit.py bogus; echo "exit=$?"`
5. `python3 scripts/goal-emit.py emit --card $F/loop-yes/card.md --out "$UAT/w" | grep -Ewi "accept|reject|modify-spec"; echo "grep-exit=$?"`
6. `grep -n "/goal\b" scripts/goal-emit.py | grep -vi "invoke\|INVOKE\|^.*\"\"\"\|Treat this stop" `

**Expected Result:**
- Steps 1 and 2: `unverifiable`, `reason: missing_card`, `goal-emit: unverifiable (missing_card)`; `exit=0`. Step 2's `ls` reports no such directory.
- Step 3: `unverifiable`, `reason: loop_no`, `goal-emit: unverifiable (loop_no)`; `exit=0`; no directory created.
- Step 4: usage error naming `invalid choice: 'bogus'`; `exit=2`.
- Step 5: no whole-word match; `grep-exit=1`. (The invoke text contains "acceptable", which is not the word "accept"; see drift DEV-003.)
- Step 6: no line that runs or registers `/goal`. The script only writes files and prints text.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 4: The pytest suite passes on Python 3.9

**Source:** Acceptance Criteria (AC-1.4) — Story 1

**Preconditions:**
- `uv` installed.

**Steps:**
1. `uv run --python 3.9 pytest -q -p no:cacheprovider scripts/tests/test_goal_emit.py`

**Expected Result:**
- `41 passed`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `scripts/tests/test_goal_emit.py`

**Notes:**

---

### Scenario 5: Output shape, `--project` alias, and Story 1 stayed in its lane

**Source:** Acceptance Criteria (AC-1.5) — Story 1

**Preconditions:**
- Scratch setup done.

**Steps:**
1. `python3 scripts/goal-emit.py check --card $F/loop-yes/card.md --out $F/loop-yes --repo .`
2. `python3 scripts/goal-emit.py check --card $F/loop-yes/card.md --out $F/loop-yes --project .`
3. `git show --stat 0cbe967 | grep -E "commands/|adapters/|eval.sh|install.sh"; echo "grep-exit=$?"`

**Expected Result:**
- Steps 1 and 2 print the same two lines: `pass`, then `goal-emit: pass (GOAL.md and VERIFY.md)`.
- Step 3: no match; `grep-exit=1`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 6: A malformed card fails and writes nothing

**Source:** Error Map (Parse card: missing OBJECTIVE / DONE WHEN / STOP-CAPS) — Story 1

**Preconditions:**
- Scratch setup done.

**Steps:**
1. Remove the STOP-CAPS heading: `grep -v "STOP-CAPS" $F/loop-yes/card.md > "$UAT/bad.md"`
2. `python3 scripts/goal-emit.py emit --card "$UAT/bad.md" --out "$UAT/b"; echo "exit=$?"; ls "$UAT/b"`
3. Remove the loop header: `grep -v "loop:" $F/loop-yes/card.md > "$UAT/noloop.md"`
4. `python3 scripts/goal-emit.py emit --card "$UAT/noloop.md" --out "$UAT/nl"; echo "exit=$?"`

**Expected Result:**
- Step 2: `fail`, `reason: malformed_card`, `goal-emit: fail (malformed_card)`; `exit=1`; no directory created.
- Step 4: same `fail` / `malformed_card` / `exit=1`. A card with no `loop:` header is treated as malformed.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 7: Check on a folder that was never emitted fails without creating it

**Source:** Error Map (`check` written files) plus drift DEV-002 — Story 1

**Preconditions:**
- Scratch setup done.

**Steps:**
1. `python3 scripts/goal-emit.py check --card $F/loop-yes/card.md --out "$UAT/never"; echo "exit=$?"; ls "$UAT/never"`

**Expected Result:**
- `fail`, `reason: missing_boundary`, `goal-emit: fail (missing_boundary)`; `exit=1`.
- `ls` reports no such directory.

**Status:** [ ] Pass  [ ] Fail

**Notes:** The spec only planned `missing_boundary` for files that lack the ADR sentence. Using it for absent files was an auto-amended Small drift.

---

### Scenario 8: VERIFY.md points to `exit-criteria.py` when the card has a `spec_ref`

**Source:** Drift Log DEV-001 — Story 1

**Preconditions:**
- Scratch setup done. Run from the repo root (the spec path resolves against `--repo .`).

**Steps:**
1. Build a card with a `spec_ref` to an existing spec:
   ```
   (sed -n 1,3p $F/loop-yes/card.md; echo "> **spec_ref:** .writ/specs/2026-09-09-phase11-stage4-goal-emit/spec.md"; sed -n '4,$p' $F/loop-yes/card.md) > "$UAT/sr.md"
   python3 scripts/goal-emit.py emit --card "$UAT/sr.md" --out "$UAT/sr" >/dev/null
   grep "How to check" "$UAT/sr/VERIFY.md"
   ```
2. Compare with the fixture that has no `spec_ref`: `grep "How to check" $F/loop-yes/VERIFY.md`
3. Try to follow the step 1 instruction literally: `python3 scripts/exit-criteria.py check --help`

**Expected Result:**
- Step 1: `How to check DONE WHEN: run \`python3 scripts/exit-criteria.py\` against the spec named by spec_ref.`
- Step 2: `How to check DONE WHEN: count DONE WHEN lines on the card.`
- Step 3: judge whether a human can run the step 1 instruction without further research. `exit-criteria.py check` takes a command name and a run-record state file, not a spec path. If you cannot build a working command from VERIFY.md alone, mark **Fail** (see Honest Note 2).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 2: Hooks — create-goal After Save and implement-phase Origin Emit

### Scenario 9: `/create-goal` emits after save and still never registers `/goal`

**Source:** Acceptance Criteria (AC-2.1) — Story 2

**Preconditions:**
- None. Reading exercise.

**Steps:**
1. Open `commands/create-goal.md` and find the paragraph starting **Emit after save.**
2. Read Core Rule 4 under `## Core Rules`.

**Expected Result:**
- Step 1: the paragraph sits after the save confirmation block. It runs `python3 scripts/goal-emit.py emit --card .writ/issues/goals/<YYYY-MM-DD>-<slug>.md`, prints the invoke line the helper prints after its summary on `pass`, and states Core Rule 4 still holds.
- Step 2: "The card is not a runner. This command never registers a `/goal` hook, never iterates, and never calls `/create-spec`."

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — Files: `commands/create-goal.md`; commit `4edc097`

**Notes:**

---

### Scenario 10: A `loop: no` save still succeeds and creates no folder

**Source:** Acceptance Criteria (AC-2.2) — Story 2

**Preconditions:**
- None.

**Steps:**
1. Read items 4 and 5 of **Emit after save** in `commands/create-goal.md`.

**Expected Result:**
- `loop_no` is relayed with `add_note`. The helper writes no emit folder, and the command is told not to create one.
- "A `loop: no` save is still success. Emit notes never fail this command."
- The command always runs emit and lets the helper decide; it does not branch on `loop:` itself (Implementation Decision 1).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 11: `/implement-phase` Step 1.4 emits only when a Goal Card origin resolves

**Source:** Acceptance Criteria (AC-2.3) — Story 2

**Preconditions:**
- None.

**Steps:**
1. `grep -n "^#### Step 1.4\|^### Phase 2" commands/implement-phase.md`
2. Read Step 1.4.

**Expected Result:**
- Step 1: Step 1.4 "Emit Goal files when origin is a Goal Card" comes before Phase 2 (sequencing).
- Step 2: resolves from spec `Origin:` or issue `spec_ref`; no path → `add_note` `unverifiable` and continue, "Do not invent a card"; otherwise runs `python3 scripts/goal-emit.py emit --card <path>` and prints the invoke line on `pass`; "Notes never fail the phase."

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — Files: `commands/implement-phase.md` (Step 1.4)

**Notes:**

---

### Scenario 12: Notes vs findings; no `/goal` call; no spawn or agent change

**Source:** Acceptance Criteria (AC-2.4) — Story 2

**Preconditions:**
- None.

**Steps:**
1. In both `commands/create-goal.md` (Emit after save) and `commands/implement-phase.md` (Step 1.4), find the `add_note` / `add_finding` rules.
2. `grep -n "goal-emit" commands/implement-story.md; echo "grep-exit=$?"`
3. `git show --stat 4edc097 | grep -E "agents/|implement-story|adapters/"; echo "grep-exit=$?"`

**Expected Result:**
- Step 1: both say `pass` / `fail` / `unverifiable` → `add_note`; helper missing or exit 2 → `add_finding`; no AskQuestion on emit notes; neither registers `/goal`.
- Step 2: no match.
- Step 3: no match. Story 2 added no agent file and did not touch `implement-story.md` or any adapter.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 13: Command-hook test passes

**Source:** Acceptance Criteria (AC-2.5) — Story 2

**Preconditions:**
- None.

**Steps:**
1. `bash scripts/tests/test_goal_emit_command_hooks.sh; echo "exit=$?"`

**Expected Result:**
- PASS lines include `create-goal loop: no is notes-only`, `implement-phase origin emit named`, `helper missing / exit 2 is a finding`, `create-goal Core Rule 4 intact`, `implement-story.md spawn unchanged`; last line `All goal-emit command-hook assertions passed.`; `exit=0`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 14: End to end — `/create-goal` on a real `loop: yes` card

**Source:** Experience Design (Entry point, Happy path steps 1–3) — Story 2

**Preconditions:**
- A Claude Code or Cursor session open in this repo.
- Note the current contents of `.writ/issues/goals/` and `.writ/goals/` so you can clean up.

**Steps:**
1. Run `/create-goal` and describe a small recurring task that has a checkable finish line (for example: "keep `bash scripts/eval.sh` at Findings 0 while I trim command files, stop after 5 rounds").
2. Accept the card when offered so the command saves it.
3. Read what the command prints after the save confirmation.
4. `ls .writ/goals/<the new card's filename without .md>/`

**Expected Result:**
- The save confirmation shows `(loop: yes, …)`.
- After it, the command reports the helper's `pass` and prints the `/goal Treat this stop as acceptable when ANY …` block.
- Step 4 lists `GOAL.md` and `VERIFY.md`.
- The command does not register or run `/goal`, and does not start iterating.
- If the interview ends in `loop: no`, you instead see a `loop_no` note, the save still succeeds, and no `.writ/goals/` folder is created for it.

**Cleanup:** delete the new card from `.writ/issues/goals/` and its folder under `.writ/goals/`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 3: Adapter + Eval + Gold Round-Trip

### Scenario 15: The Claude Code adapter says to paste the printed line; other adapters unchanged

**Source:** Acceptance Criteria (AC-3.1) — Story 3

**Preconditions:**
- None.

**Steps:**
1. Open `adapters/claude-code.md` at `### The /goal Stop Hook` and find the paragraph starting **Paste the emitter's printed invoke line unchanged.**
2. `grep -n "/goal" adapters/cursor.md adapters/codex.md adapters/openclaw.md; echo "grep-exit=$?"`

**Expected Result:**
- Step 1: the paragraph names `python3 scripts/goal-emit.py emit --card PATH`, says to paste the printed text as-is, and says it must match the three-way template below it without rewriting clauses (a)/(b)/(c). The template block follows.
- Step 2: no match; `grep-exit=1`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — Files: `adapters/claude-code.md`; commit `379401c`

**Notes:**

---

### Scenario 16: `goal-emit` is registered; missing helper or exit 2 fails eval

**Source:** Acceptance Criteria (AC-3.2); Error Map (Helper missing); Shadow Path (Upstream) — Story 3

**Preconditions:**
- None. The test builds a temp tree.

**Steps:**
1. `grep -n "^  goal-emit$\|^  spec-analyze$\|^check_goal_emit()" scripts/eval.sh`
2. `bash scripts/tests/test_eval_goal_emit.sh; echo "exit=$?"`

**Expected Result:**
- Step 1: `goal-emit` and `spec-analyze` both in `CHECKS`, plus the function definition.
- Step 2: includes `PASS: missing helper -> exit 1, add_finding`, `PASS: usage exit 2 -> exit 1, add_finding`, `PASS: registration: goal-emit in CHECKS; spec-analyze kept`; ends `All 6 goal-emit eval-wiring assertions passed.`; `exit=0`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 17: On the live repo, emit results are notes and nothing is written to `.writ/goals/`

**Source:** Acceptance Criteria (AC-3.3); Error Map (`eval.sh` live) — Story 3

**Preconditions:**
- Run outside any sandbox. The run writes one report file under `.writ/state/` (gitignored).
- Record `ls -la .writ/goals/*/` before starting.

**Steps:**
1. `bash scripts/eval.sh --check=goal-emit; echo "exit=$?"`
2. Open the report path the command prints.
3. Run `ls -la .writ/goals/*/` again.

**Expected Result:**
- `exit=0`.
- Report `## goal-emit` says `PASS`; notes start with `pass` and `goal-emit: pass (GOAL.md and VERIFY.md)`, followed by the invoke text line by line. `Findings: 0`.
- Step 3: timestamps unchanged. The check emits into a temp folder and deletes it (Implementation Decision 1).

**Status:** [ ] Pass  [ ] Fail

**Notes:** The check emits the first card in `.writ/issues/goals/` only.

---

### Scenario 18: Fixture tree has `loop-yes` gold and a `loop-no` card

**Source:** Acceptance Criteria (AC-3.4) — Story 3

**Preconditions:**
- None.

**Steps:**
1. `ls $F/loop-yes $F/loop-no`
2. `grep -rn "AC-[0-9]" $F; echo "grep-exit=$?"`

**Expected Result:**
- `loop-yes`: `GOAL.md`, `VERIFY.md`, `card.md`, `invoke.txt`. `loop-no`: `card.md` only.
- Step 2: no match; `grep-exit=1`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 19: Gold round-trip — emitted files and invoke equal gold and the adapter

**Source:** Acceptance Criteria (AC-3.5); Experience Design (Moment of truth) — Story 3

**Preconditions:**
- `$UAT/stdout.txt` from Scenario 1. `uv` installed.

**Steps:**
1. `tail -n +3 "$UAT/stdout.txt" | diff - $F/loop-yes/invoke.txt && echo INVOKE-EQ-GOLD`
2. Extract the adapter template and compare:
   ```
   awk '/^Word the condition as an explicit three-way/{f=1;next} f&&/^```$/{if(g){exit}g=1;next} g{print}' adapters/claude-code.md > "$UAT/adapter.txt"
   diff "$UAT/adapter.txt" $F/loop-yes/invoke.txt && echo ADAPTER-EQ-GOLD
   ```
3. `uv run --python 3.9 pytest -q -p no:cacheprovider scripts/tests/test_goal_emit_gold.py`
4. `grep -n "stage-4a:" .writ/decision-log.md`

**Expected Result:**
- Step 1: `INVOKE-EQ-GOLD`. Step 2: `ADAPTER-EQ-GOLD`. (Scenario 1 step 3 already showed GOAL.md and VERIFY.md equal gold.)
- Step 3: `3 passed`.
- Step 4: four `2026-09-09 stage-4a:` lines. The last names emit + hooks + adapter paste line + eval check + gold equality, and says "Live /goal not run; gold files are the proof."

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — Files: `scripts/tests/test_goal_emit_gold.py`, `scripts/tests/fixtures/goal-emit/`

**Notes:** `adapters/claude-code.md` was edited again later (commit `38dfdcf`, Stage 4b). Steps 1–3 confirm the template is still byte-equal after that edit.

---

### Scenario 20: Pasting the printed line needs zero edits

**Source:** Experience Design (Happy path step 4: "the human pastes that line unchanged") — Story 3

**Preconditions:**
- `$UAT/stdout.txt` from Scenario 1.

**Steps:**
1. `grep -n "{timestamp}" "$UAT/stdout.txt"`
2. `ls .writ/state/phase-execution-*.json 2>/dev/null | head`
3. Emit a second, unrelated card (for example the real one: `python3 scripts/goal-emit.py emit --card .writ/issues/goals/2026-09-05-writ-contract-and-verifier-layer.md --out "$UAT/real" | tail -n +3 > "$UAT/real-invoke.txt"`) and `diff "$UAT/real-invoke.txt" $F/loop-yes/invoke.txt && echo SAME-FOR-EVERY-CARD`.
4. Optional, if you have a Claude Code session running `/implement-phase`: paste the printed line unchanged and watch whether the stop hook registers and evaluates clause (a) against the right state file.

**Expected Result (per spec):**
- The line works when pasted with no edits.

**What was built:**
- Step 1 shows a literal `{timestamp}` in clause (a).
- Step 3 prints `SAME-FOR-EVERY-CARD`. The line carries nothing from the card.
- Mark Pass only if step 4 (or your judgment) shows the evaluator resolves `{timestamp}` to the current run's state file. Otherwise mark Fail (see Honest Note 1). No live session was run during implementation.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 21: Where emitted files live in git

**Source:** Experience Design (State catalog: Populated / Edge — re-emit overwrites the same stem folder) — Story 3

**Preconditions:**
- None.

**Steps:**
1. `git check-ignore -v .writ/goals/anything || echo NOT-IGNORED`
2. `git status --porcelain .writ/goals/`

**Expected Result:**
- The spec does not say. Record the decision: either `.writ/goals/` should be gitignored like `.writ/state/`, or emitted files are meant to be committed next to their cards.
- As built: step 1 prints `NOT-IGNORED`; step 2 shows `?? .writ/goals/`. Every `/create-goal` save leaves untracked files.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Pending Stories

None. All three stories are Completed ✅.
