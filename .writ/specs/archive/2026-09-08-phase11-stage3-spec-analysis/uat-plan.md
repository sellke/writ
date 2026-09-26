# UAT Plan: Phase 11 Stage 3: Spec Analysis

> **Generated:** 2026-09-25
> **Spec:** `.writ/specs/2026-09-08-phase11-stage3-spec-analysis/`
> **Stories Covered:** 3 of 3 completed
> **Total Scenarios:** 21

## How to Use This Plan

1. Work through scenarios in order (grouped by story, ordered by priority).
2. Run every command from the repository root. Scenarios marked "scratch" build throwaway files under a temp directory; they never touch tracked files.
3. Mark Pass or Fail. Add notes for any output that differs from the Expected Result.
4. File a Fail as an issue or feed it back to the spec. Do not fix it inline.
5. The feature passes UAT when every scenario passes, or when a failure is accepted as a known limitation.

> **Note on this methodology repo:** the deliverables are one Python script, two command-file edits, one `eval.sh` check, and fixtures. Most scenarios run the script or read a command file. There is no UI.
>
> **Scratch setup used by several scenarios.** Run once before starting:
> ```
> export UAT=$(mktemp -d)
> ```
> Every scratch file below lives under `$UAT`. Delete it with `rm -rf "$UAT"` when done.

## What This Spec Delivered

`scripts/spec-analyze.py check` scans story files for three structural defects (empty criterion, vague "then" clause, fewer than three criteria) and schema-checks a findings JSON that an LLM pass writes. `/create-spec` gained Step 2.6c and `/verify-spec` gained Check 3g; both relay the result as notes and never fail. `eval.sh` gained a `spec-analyze` check that only fails when the helper is missing or refuses its arguments.

## Honest Notes (read before signing off)

1. **The script does not detect contradictions, gaps, or ambiguity.** It only checks that the LLM's JSON is well-formed. On the contradiction fixture with its gold findings it prints `pass` and nothing about the contradiction. The recorded precision (4 TP / 0 FP) measures the schema check against hand-written labels, not semantic detection. Scenario 21 shows this directly.
2. **The contradiction may never reach the user.** Step 2.6c and Step 2.9 tell the orchestrator to relay "the verdict line and every `reason:`". A well-formed findings file with a real contradiction produces `pass` and no reasons, so a literal reading relays nothing about it. The spec's Moment of Truth says the contradiction should show as a named note. Scenario 15 tests this and may Fail.
3. **The eval check analyzes one spec.** `check_spec_analyze` in `scripts/eval.sh` runs against this spec's own folder when it exists, otherwise the first spec folder. It does not sweep all specs.
4. **A missing findings file is `malformed_findings`, not `unverifiable`.** The spec did not cover a `--findings` path that does not exist. The script treats it as malformed (exit 1). Scenario 7 records this.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: CLI + Schema | ✅ Covered | 7 | AC: 5, Errors: 2, Shadow: 0, Edge: 0 |
| Story 2: Hooks — create-spec Step 2.6c and verify-spec Check 3g | ✅ Covered | 8 | AC: 5, Errors: 0, Shadow: 1, Edge: 1, Experience: 1 |
| Story 3: Eval Check + Precision Record | ✅ Covered | 6 | AC: 5, Errors: 0, Shadow: 1, Edge: 0 |

Error map rows "Structural scan" and "LLM pass" are covered by Scenarios 1–3. Rows "`eval.sh` live repo" and "Helper missing" are covered by Scenarios 16 and 18. Edge cases "story added after 2.6c" and "concurrent verify-spec" are covered by Scenario 13 (verify-spec reads current files and writes nothing to the story tree).

---

## Story 1: CLI + Schema

### Scenario 1: The three structural defects are caught, and a clean story is not flagged

**Source:** Acceptance Criteria (AC-1.1) — Story 1

**Preconditions:**
- `python3` 3.9 or later on PATH.
- `$UAT` set (see scratch setup).

**Steps:**
1. Build a story with one vague criterion and one empty criterion:
   ```
   mkdir -p "$UAT/vague/user-stories"
   printf -- '- [ ] Given a user, when they log in, then it works correctly\n- [ ] Given x, when y, then `a.txt` exists\n- [ ] Given\n' > "$UAT/vague/user-stories/story-1-x.md"
   python3 scripts/spec-analyze.py check --spec "$UAT/vague"; echo "exit=$?"
   ```
2. Build a story with only one criterion:
   ```
   mkdir -p "$UAT/short/user-stories"
   printf -- '- [ ] Given a, when b, then `c` exists\n' > "$UAT/short/user-stories/story-1-y.md"
   python3 scripts/spec-analyze.py check --spec "$UAT/short"; echo "exit=$?"
   ```
3. Run against the committed clean fixture:
   ```
   python3 scripts/spec-analyze.py check --spec scripts/tests/fixtures/spec-analyze/story-4-messaging-migration-quick-split-guard; echo "exit=$?"
   ```
4. Confirm the script does not load `ac-trace`: `grep -n "ac.trace\|ac_trace" scripts/spec-analyze.py`.

**Expected Result:**
- Step 1 prints `fail`, then `reason: unmeasurable_criterion` and `reason: empty_criterion`, then `spec-analyze: fail (structural or schema)`; `exit=1`.
- Step 2 prints `fail`, `reason: under_min_criteria`, the summary line; `exit=1`.
- Step 3 prints `unverifiable`, `reason: no_findings`, and a summary line; `exit=0`. No `unmeasurable_criterion` appears, even though one criterion ends "then the verdict is pass".
- Step 4 finds only the docstring line saying it does not import ac-trace parsers. No import statement.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `scripts/spec-analyze.py` (vague phrases: "works correctly", "as expected", "looks good" and "it …" variants); commit `14f8d54`

**Notes:**

---

### Scenario 2: Findings JSON is schema-checked; `[]` is valid

**Source:** Acceptance Criteria (AC-1.2) — Story 1

**Preconditions:**
- `$UAT` set.

**Steps:**
1. `echo '[]' > "$UAT/empty.json"` and run `python3 scripts/spec-analyze.py check --spec .writ/specs/2026-09-08-phase11-stage3-spec-analysis --findings "$UAT/empty.json"; echo "exit=$?"`
2. `echo '[{"code":"typo","story":"spec","summary":"x"}]' > "$UAT/badcode.json"` and run the same command with `--findings "$UAT/badcode.json"`.
3. `echo '[{"code":"gap","story":"spec","summary":"x","ac_ids":["AC-1"]}]' > "$UAT/badac.json"` and run with `--findings "$UAT/badac.json"`.
4. `echo '[{"code":"gap","story":"spec","summary":"  "}]' > "$UAT/blank.json"` and run with `--findings "$UAT/blank.json"`.
5. `echo '[{"code":"ambiguity","story":"story-1-spec-analyze-cli.md","summary":"unclear","ac_ids":["AC-1.2"]}]' > "$UAT/good.json"` and run with `--findings "$UAT/good.json"`.
6. Confirm no network or LLM client is imported: `grep -n "^import\|^from" scripts/spec-analyze.py`.

**Expected Result:**
- Step 1: `pass`, no reason lines, `spec-analyze: pass (no structural hit; findings well-formed)`, `exit=0`.
- Steps 2, 3, 4: each prints `fail`, `reason: malformed_findings`, summary; `exit=1`.
- Step 5: `pass`, `exit=0`.
- Step 6: only `__future__`, `argparse`, `json`, `re`, `sys`, `pathlib`, `typing`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `scripts/spec-analyze.py` (`_schema_check`)

**Notes:**

---

### Scenario 3: Verdict table and exit codes

**Source:** Acceptance Criteria (AC-1.3) — Story 1

**Preconditions:**
- None.

**Steps:**
1. `python3 scripts/spec-analyze.py check --spec .writ/specs/2026-09-08-phase11-stage3-spec-analysis; echo "exit=$?"`
2. `python3 scripts/spec-analyze.py check; echo "exit=$?"`
3. `python3 scripts/spec-analyze.py frob; echo "exit=$?"`
4. `python3 scripts/spec-analyze.py check --spec .writ/specs/2026-09-08-phase11-stage3-spec-analysis | grep -Ei "accept|reject|modify-spec"; echo "grep-exit=$?"`

**Expected Result:**
- Step 1: `unverifiable`, `reason: no_findings`, summary; `exit=0`. Omitting `--findings` is not a fail.
- Step 2: `unverifiable`, `reason: missing_spec`, `spec-analyze: unverifiable (no --spec)`; `exit=0`.
- Step 3: argparse usage error on stderr naming `invalid choice: 'frob'`; `exit=2`.
- Step 4: no match; `grep-exit=1`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — `--spec` is optional in argparse so a missing flag is `unverifiable`, not exit 2 (Implementation Decision 1).

**Notes:**

---

### Scenario 4: The pytest suite passes on Python 3.9

**Source:** Acceptance Criteria (AC-1.4) — Story 1

**Preconditions:**
- `uv` installed.

**Steps:**
1. `uv run --python 3.9 pytest -q scripts/tests/test_spec_analyze.py -p no:cacheprovider`

**Expected Result:**
- `14 passed`. No failures or errors.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `scripts/tests/test_spec_analyze.py`

**Notes:**

---

### Scenario 5: Output shape, `--project` alias, and read-only behavior

**Source:** Acceptance Criteria (AC-1.5) — Story 1

**Preconditions:**
- Working tree state recorded: `git status --porcelain > "$UAT/before.txt"`.

**Steps:**
1. `python3 scripts/spec-analyze.py check --spec .writ/specs/2026-09-08-phase11-stage3-spec-analysis --project .`
2. `python3 scripts/spec-analyze.py check --spec .writ/specs/2026-09-08-phase11-stage3-spec-analysis --repo .`
3. `git status --porcelain | diff "$UAT/before.txt" -; echo "diff-exit=$?"`
4. `git show --stat 14f8d54 | grep -E "commands/|ac-trace"; echo "grep-exit=$?"`

**Expected Result:**
- Steps 1 and 2 print identical output: one verdict line first, zero or more `reason:` lines, and a `spec-analyze: …` summary line last.
- Step 3: no difference; `diff-exit=0`. The script wrote nothing.
- Step 4: no match; Story 1's commit did not touch `commands/` or `ac-trace.py`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 6: A missing or empty spec folder is `unverifiable`, not `fail`

**Source:** Error Map (`check --spec`: folder missing / unreadable) — Story 1

**Preconditions:**
- `$UAT` set.

**Steps:**
1. `python3 scripts/spec-analyze.py check --spec /nonexistent/folder; echo "exit=$?"`
2. `mkdir -p "$UAT/nostories/user-stories"` then `python3 scripts/spec-analyze.py check --spec "$UAT/nostories"; echo "exit=$?"`

**Expected Result:**
- Both print `unverifiable`, `reason: spec_unreadable`, `spec-analyze: unverifiable (spec unreadable)`; `exit=0`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 7: Non-JSON or missing findings file is `malformed_findings`

**Source:** Error Map (`check --findings`: JSON not an array / bad object) — Story 1

**Preconditions:**
- `$UAT` set.

**Steps:**
1. `echo 'not json' > "$UAT/nj.json"` then `python3 scripts/spec-analyze.py check --spec .writ/specs/2026-09-08-phase11-stage3-spec-analysis --findings "$UAT/nj.json"; echo "exit=$?"`
2. `echo '{"code":"gap"}' > "$UAT/obj.json"` then run with `--findings "$UAT/obj.json"` (an object, not an array).
3. Run with `--findings "$UAT/does-not-exist.json"`.

**Expected Result:**
- Steps 1 and 2: `fail`, `reason: malformed_findings`, summary; `exit=1`.
- Step 3: also `fail` / `malformed_findings` / `exit=1`. The spec did not define this case; record in Notes whether you accept it. In the command flow it is still only a note.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 2: Hooks — create-spec Step 2.6c and verify-spec Check 3g

### Scenario 8: Step 2.6c sits after 2.6b and runs the script

**Source:** Acceptance Criteria (AC-2.1) — Story 2

**Preconditions:**
- None. Reading exercise plus grep.

**Steps:**
1. `grep -n "^#### Step 2.6\|^#### Step 2.7" commands/create-spec.md`
2. Open `commands/create-spec.md` at the Step 2.6c heading and read the numbered list.

**Expected Result:**
- Step 1: headings appear in order 2.6a, 2.6b, 2.6c, 2.7. Step 2.6b is not renumbered.
- Step 2: the step says to run it once per `/create-spec`; item 1 describes one orchestrator LLM pass for contradiction, gap, and ambiguity, grounded in exit-criteria grammar, writing a JSON array to a per-run path under `.writ/state/` (or `[]`, or omitting `--findings` if skipped); the command block shows `python3 scripts/spec-analyze.py check --spec .writ/specs/<folder> [--findings .writ/state/spec-analyze-<run>.json]`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — Files: `commands/create-spec.md` (Step 2.6c); commit `125782b`

**Notes:**

---

### Scenario 9: Analysis results are notes and never block the package

**Source:** Acceptance Criteria (AC-2.2) — Story 2

**Preconditions:**
- None.

**Steps:**
1. Read item 3 of Step 2.6c in `commands/create-spec.md`.
2. Read Step 2.9 in the same file.

**Expected Result:**
- Item 3 says: carry the verdict and every `reason:` into Step 2.9 as notes (`add_note`); `add_finding` only when the helper is missing or exits 2; a `fail` (including `malformed_findings`) or `unverifiable` does not fail package creation, does not mark the spec `DEGRADED`, and does not open an AskQuestion gate.
- Step 2.9 says the Step 2.6c verdict and `reason:` lines appear as notes and never fail the review or block the package.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 10: verify-spec Check 3g is separate from 3e/3f and cannot fail the report

**Source:** Acceptance Criteria (AC-2.3) — Story 2

**Preconditions:**
- None.

**Steps:**
1. `grep -n "^\*\*3[a-g]\." commands/verify-spec.md`
2. Read the Check 3g block.
3. Read the Check 3e and 3f blocks and confirm they still reference `ac-trace.py`.

**Expected Result:**
- Step 1: seven sub-checks, 3a through 3g. 3g is titled "Spec analysis (advisory — not in the 3a–3f roll-up)".
- Step 2: 3g runs `python3 scripts/spec-analyze.py check --spec <folder> [--findings <json>]`, relays the verdict and reasons as notes, and states a `fail` or `unverifiable` does not fail the check, the 3a–3f status cell, or the report.
- Step 3: 3e and 3f still use `ac-trace.py`; 3g does not reuse them.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — 3g is kept outside the 3a–3f worst-status cell (Implementation Decision 2).

**Notes:**

---

### Scenario 11: No new agent, no API key, no spawn change

**Source:** Acceptance Criteria (AC-2.4) — Story 2

**Preconditions:**
- None.

**Steps:**
1. `git show --stat 125782b | grep -E "agents/|implement-story|spec-analyze.py"; echo "grep-exit=$?"`
2. `grep -in "api_key\|anthropic\|openai\|requests\|urllib" scripts/spec-analyze.py; echo "grep-exit=$?"`

**Expected Result:**
- Step 1: no match; `grep-exit=1`. Story 2's commit added no file under `agents/`, did not touch `commands/implement-story.md`, and did not edit `scripts/spec-analyze.py`.
- Step 2: no match; `grep-exit=1`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 12: Command-hook test passes

**Source:** Acceptance Criteria (AC-2.5) — Story 2

**Preconditions:**
- None.

**Steps:**
1. `bash scripts/tests/test_spec_analyze_command_hooks.sh; echo "exit=$?"`

**Expected Result:**
- Output ends with `PASS: verify-spec 3g advisory; 3e/3f still ac-trace`, `PASS: script fail is notes-only for the command contract`, and `All spec-analyze command-hook assertions passed.`; `exit=0`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — Files: `scripts/tests/test_spec_analyze_command_hooks.sh`

**Notes:**

---

### Scenario 13: A live `/verify-spec` shows Check 3g as a note and still passes

**Source:** Shadow Path (verify-spec check: happy path and empty input) — Story 2

**Preconditions:**
- An AI coding session (Claude Code or Cursor) open in this repo.

**Steps:**
1. Run `/verify-spec 2026-09-08-phase11-stage3-spec-analysis --check`.
2. Read the report the command prints.

**Expected Result:**
- The report includes a 3g entry reporting `unverifiable` / `no_findings` (no findings file exists for this run) as a note or INFO line.
- The Completion integrity row is not downgraded because of 3g, and the overall result is not failed because of 3g. (The 2026-09-25 verification report shows exactly this: `[INFO-1] Check 3g`.)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 14: Findings files are per-run, gitignored, and written once

**Source:** Edge Case (double invoke; findings JSON from a previous spec) — Story 2

**Preconditions:**
- None.

**Steps:**
1. `git check-ignore -v .writ/state/spec-analyze-example.json`
2. Re-read the first paragraph of Step 2.6c in `commands/create-spec.md`.

**Expected Result:**
- Step 1 prints a `.gitignore` rule covering `.writ/state/`. Findings files never get committed.
- Step 2 says to run the step once per `/create-spec` and not to loop; the path pattern `spec-analyze-<run>.json` is per-run.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 15: A real contradiction appears to the user as a named note

**Source:** Experience Design (Moment of Truth) — Story 2

**Preconditions:**
- `$UAT` set.

**Steps:**
1. Write the contradiction fixture's gold findings to a file:
   ```
   python3 -c "import json;print(json.dumps(json.load(open('scripts/tests/fixtures/spec-analyze/story-2-event-creation-payment-flow/gold.json'))['findings']))" > "$UAT/contra.json"
   ```
2. `python3 scripts/spec-analyze.py check --spec scripts/tests/fixtures/spec-analyze/story-2-event-creation-payment-flow --findings "$UAT/contra.json"`
3. Re-read Step 2.6c item 3 and Step 2.9 in `commands/create-spec.md`. Decide: following those words literally, what would the user see about this contradiction?

**Expected Result (per spec):**
- The user sees a note naming `contradiction` and its summary, and the package still completes.

**What was built:**
- Step 2 prints `pass` and the pass summary only. The script does not echo the finding.
- Steps 2.6c and 2.9 say to relay "the verdict line and every `reason:`". There are no reason lines here, so a literal reading relays only `pass`.
- Mark **Fail** if the command text does not tell the orchestrator to surface the findings JSON contents. See Honest Note 2.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 3: Eval Check + Precision Record

### Scenario 16: `spec-analyze` is registered, and a missing helper fails eval

**Source:** Acceptance Criteria (AC-3.1) and Error Map (Helper missing) — Story 3

**Preconditions:**
- None. The test builds its own temp tree.

**Steps:**
1. `grep -n "^  spec-analyze$\|^check_spec_analyze()" scripts/eval.sh`
2. `bash scripts/tests/test_eval_spec_analyze.sh; echo "exit=$?"`

**Expected Result:**
- Step 1: two hits, the `CHECKS` entry and the function definition.
- Step 2 includes `PASS: missing helper -> exit 1, add_finding` and `PASS: registration: spec-analyze in CHECKS`, ends with `All 5 spec-analyze eval-wiring assertions passed.`; `exit=0`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — Files: `scripts/eval.sh` (`check_spec_analyze`), `scripts/tests/test_eval_spec_analyze.sh`; commit `d07ac94`

**Notes:**

---

### Scenario 17: A usage refusal (exit 2) is a finding, not a note

**Source:** Acceptance Criteria (AC-3.2) — Story 3

**Preconditions:**
- None.

**Steps:**
1. `bash scripts/tests/test_eval_spec_analyze.sh | grep "usage exit 2"`
2. Read `check_spec_analyze()` in `scripts/eval.sh`.

**Expected Result:**
- Step 1: `PASS: usage exit 2 -> exit 1, add_finding`.
- Step 2: an exit code of 2 leads to `add_finding` with "spec-analyze.py check refused"; every other outcome leads to `add_note`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 18: On the live repo, analysis results are notes and eval passes

**Source:** Acceptance Criteria (AC-3.3) and Error Map (`eval.sh` live repo) — Story 3

**Preconditions:**
- Run outside any sandbox (eval.sh may create temp git repos). The run writes one report file under `.writ/state/` (gitignored).

**Steps:**
1. `bash scripts/eval.sh --check=spec-analyze; echo "exit=$?"`
2. Open the report path the command prints.

**Expected Result:**
- `exit=0`.
- The report's `## spec-analyze` section says `PASS` and lists three notes: `unverifiable`, `reason: no_findings`, and the unverifiable summary line.
- Summary: `Findings: 0`, `Run errors: 0`.

**Status:** [ ] Pass  [ ] Fail

**Notes:** The check runs against `.writ/specs/2026-09-08-phase11-stage3-spec-analysis` only (Honest Note 3).

---

### Scenario 19: Four labeled fixtures with gold labels exist

**Source:** Acceptance Criteria (AC-3.4) — Story 3

**Preconditions:**
- None.

**Steps:**
1. `ls scripts/tests/fixtures/spec-analyze/`
2. `grep -h '"label"' scripts/tests/fixtures/spec-analyze/*/gold.json`
3. `grep -rn "AC-[0-9]" scripts/tests/fixtures/spec-analyze/; echo "grep-exit=$?"`

**Expected Result:**
- Step 1: four folders named after Stage 1 yuss slugs: `story-2-event-creation-payment-flow`, `story-3-fee-sharing-pro-exemption`, `story-3-settlement-view-share-link`, `story-4-messaging-migration-quick-split-guard`. Each holds `gold.json` and `user-stories/<slug>.md`.
- Step 2: one each of `contradiction`, `ambiguity`, `gap`, `clean`.
- Step 3: no match. Fixture stories carry no `AC-n.m` tokens, so they are not scanned as citations (Implementation Decision 3).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 20: Precision is recorded in the story and the decision log

**Source:** Acceptance Criteria (AC-3.5) — Story 3

**Preconditions:**
- `uv` installed.

**Steps:**
1. `uv run --python 3.9 pytest -q scripts/tests/test_spec_analyze_precision.py -p no:cacheprovider`
2. `grep -n "stage-3:" .writ/decision-log.md`
3. Read "Test Results" under What Was Built in `user-stories/story-3-eval-and-precision.md`.

**Expected Result:**
- Step 1: all tests pass.
- Step 2: three `2026-09-08 stage-3:` lines; the last reads `spec-analyze.py advisory; hooks after 2.6a + verify-spec; precision {contradiction 1/0, gap 1/0, ambiguity 1/0, clean 1/0; overall 4/0}`.
- Step 3: the same per-class numbers and "overall 4 TP / 0 FP"; the record states no yuss checkout, eight-run, or `/revert`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 21: What the precision number measures

**Source:** Shadow Path (Precision score: mis-labeled gold) — Story 3

**Preconditions:**
- `$UAT/contra.json` from Scenario 15.

**Steps:**
1. `python3 scripts/spec-analyze.py check --spec scripts/tests/fixtures/spec-analyze/story-2-event-creation-payment-flow`
2. `python3 scripts/spec-analyze.py check --spec scripts/tests/fixtures/spec-analyze/story-2-event-creation-payment-flow --findings "$UAT/contra.json"`
3. `echo '[]' > "$UAT/none.json"` then run step 2 again with `--findings "$UAT/none.json"`.

**Expected Result:**
- Step 1: `unverifiable` / `no_findings`. The script finds nothing on its own in a story whose criteria contradict.
- Steps 2 and 3: both print `pass`. The script gives the same verdict whether the findings file names the contradiction or is empty.
- Conclusion to confirm: "4 TP / 0 FP" means the schema check accepted four hand-written, well-formed label files. It is not a measure of how well an LLM pass finds contradictions, gaps, or ambiguity. Record whether that is acceptable for an advisory-only release.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Pending Stories

None. All three stories are Completed ✅.
