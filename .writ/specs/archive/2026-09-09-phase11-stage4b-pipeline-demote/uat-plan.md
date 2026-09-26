# UAT Plan: Phase 11 Stage 4b: Pipeline Demote

> **Generated:** 2026-09-25
> **Spec:** `.writ/specs/2026-09-09-phase11-stage4b-pipeline-demote/`
> **Stories Covered:** 3 of 3 completed
> **Total Scenarios:** 30
> **Updated:** 2026-09-25 after defect fixes

## How to Use This Plan

1. Work through scenarios in order (grouped by story, ordered by priority).
2. Run every command from the repository root. Scenarios marked "scratch" build throwaway files under a temp directory; they never touch tracked files.
3. Mark Pass or Fail. Add notes for any output that differs from the Expected Result.
4. File a Fail as an issue or feed it back to the spec. Do not fix it inline.
5. The feature passes UAT when every scenario passes, or when a failure is accepted as a known limitation.

> **Note on this methodology repo:** the deliverables are one new agent file with two platform peers, a rewrite of `commands/implement-story.md`, one Python script, one `eval.sh` check, four adapter edits, and tests. Most scenarios run a script or read a file. Only Scenario 18 runs `/implement-story` live, and it is optional.
>
> **Scratch setup used by several scenarios.** Run once before starting:
> ```
> export UAT=$(mktemp -d)
> ```
> Every scratch file below lives under `$UAT`. Delete it with `rm -rf "$UAT"` when done.

## What This Spec Delivered

No-flag `/implement-story` now names two spawn sites: `coding-agent` (Gate 1) and a new read-only `evaluator-agent` (Gate 3) whose rubric is the story's acceptance criteria and recorded test results. Gates 0, 4, and 5 run their Stage 2b scripts only; Gate 4.5 is skipped. The old six-agent path is behind `--full-pipeline`. A second consecutive evaluator FAIL switches the rest of the story to `--full-pipeline`. `scripts/spawn-cap.py` statically counts default-path `> **Agent:**` / `Task(` lines, and `eval.sh` runs it as a check: a `fail` verdict is a blocking finding; `pass` and `unverifiable` are notes.

## Honest Notes (read before signing off)

1. **The proof counts marker lines, not spawns.** `spawn-cap.py` excludes a marker only inside an explicit `--full-pipeline` scope: a line that is exactly `**`--full-pipeline`:**` plus the contiguous `>` lines directly under it. Everything else is a text match. Prose such as "Spawn `review-agent` instead" is invisible to the scan, and any marker placed inside a labeled scope is excluded regardless of what it says. No scenario except the optional live run (Scenario 18) measures what an orchestrator actually spawns.
2. **Default drops visual QA.** With the default path, a story that has `## Visual References` gets no visual-qa spawn. This is by design (Business Rule 2 / Gate 4.5), but a tester used to the old behavior should know.
3. **Adapter knowledge-loading lines still name old recipients.** For example `adapters/cursor.md` line ~313 says `knowledge_context` goes into "the architecture-check, coding, and review agent prompts". On default, those are coding and evaluator. Accepted as DEV-003.
4. **Story 3's text predates the 2026-09-25 fixes.** `story-3-eval-adapters-proof.md` AC-3.2, AC-3.4, and tasks 3.2 / 3.4 still say a helper `fail` → `add_note` only, "do not count-block the suite". Its Test Results report 14 spawn-cap tests. Current behavior: a spawn-cap `fail` is a blocking finding, and there are 19 pytest cases. Scenarios 22, 24, 26, and 27 describe current behavior, so they contradict AC-3.2 as written. Amend the story or accept the deviation before sign-off.
5. **Zero default sites reports `over_cap`.** A command with no default spawn markers prints `fail` / `reason: over_cap` (Scenario 28). The verdict is right; the reason name is misleading.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: Evaluator Agent | ✅ Covered | 6 | AC: 5, Errors: 1, Shadow: 0, Edge: 0 |
| Story 2: Default Path and Flags | ✅ Covered | 12 | AC: 6, Errors: 2, Shadow: 0, Edge: 3, Experience: 1 |
| Story 3: Eval, Adapters, and Spawn-Cap Proof | ✅ Covered | 12 | AC: 8, Errors: 1, Shadow: 3, Edge: 0 |

Error map rows: "Spawn evaluator" → Scenario 6; "Evaluator FAIL (1st)" and "(2nd)" → Scenario 9; "`review-override.py` pass vs evaluator FAIL" → Scenario 13; "Gate 4 script fail on default" → Scenario 10; "Gate 0 ABORT-class on default" → Scenario 14; "`spawn-cap.py` command file missing" → Scenario 19; "third default Agent marker" → Scenario 20; "`eval.sh` helper missing" → Scenario 23. Shadow path "Default `/implement-story`" (nil input, evaluator run) → Scenario 18. Edge case "Re-run after escalation" → Scenario 15.

---

## Story 1: Evaluator Agent

### Scenario 1: The evaluator agent file declares its config and a rubric-only prompt

**Source:** Acceptance Criteria (AC-1.1) — Story 1

**Preconditions:**
- None.

**Steps:**
1. `sed -n '/## Agent Configuration/,/^## Responsibilities/p' agents/evaluator-agent.md`
2. `grep -n "acceptance criteria\|recorded test results" agents/evaluator-agent.md | head`
3. `grep -n "architecture, security, and taste" agents/evaluator-agent.md`
4. `grep -n "Suggested Fix" agents/evaluator-agent.md`
5. `grep -n -i "do not apply a patch\|do not tell the coder how to fix" agents/evaluator-agent.md`
6. `grep -n -i "rewrite this function\|be actionable" agents/evaluator-agent.md; echo "grep-exit=$?"`
7. `grep -n "| \`recorded_test_results\`" agents/evaluator-agent.md`

**Expected Result:**
- Step 1 shows `subagent_type: "generalPurpose"`, `model_tier: anchor`, `readonly: true`, and `problem:`, `outcome:`, `exit_criteria:` with three entries.
- Step 2 shows the rubric is the acceptance criteria and the recorded test results (both named as "primary rubric").
- Step 3 shows the residual scan is limited to architecture, security, and taste.
- Step 4 shows Suggested Fix is optional, report-only, and never applied.
- Step 5 shows both "do not tell the coder how to fix" and "do not apply a patch" in the prompt.
- Step 6: no match; `grep-exit=1`.
- Step 7: the input row says `recorded_test_results` is "The orchestrator's own run of the story's test files before Gate 3 (command, exit code, output tail) — not the coding agent's self-report".

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `agents/evaluator-agent.md` (227 lines; output heading `EVALUATION_RESULT`); commit `cddc3e3`

**Notes:**

---

### Scenario 2: Claude Code and Codex peers are read-only and parity is clean

**Source:** Acceptance Criteria (AC-1.2) — Story 1

**Preconditions:**
- None.

**Steps:**
1. `head -10 claude-code/agents/writ-evaluator.md`
2. `grep -n "^name\|sandbox_mode" codex/agents/evaluator-agent.toml`
3. `grep -n "evaluator-agent" scripts/check-agent-parity.sh`
4. `sed -n '/^claude_exempt()/,/^}/p' scripts/check-agent-parity.sh`
5. `bash scripts/check-agent-parity.sh; echo "exit=$?"`

**Expected Result:**
- Step 1: `tools: Read, Grep, Glob, Bash`, `disallowedTools: Write, Edit`, `permissionMode: plan`.
- Step 2: `name = "evaluator-agent"` and `sandbox_mode = "read-only"`.
- Step 3: `evaluator-agent) echo "writ-evaluator.md" ;;` inside `claude_counterpart()`.
- Step 4: only `visual-qa-agent` is exempt; `evaluator-agent` does not appear.
- Step 5: `parity OK — agents/, claude-code/agents/, and codex/agents/ aligned ...`, no `⚠️` lines, `exit=0`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `claude-code/agents/writ-evaluator.md`, `codex/agents/evaluator-agent.toml`, `scripts/check-agent-parity.sh`

**Notes:**

---

### Scenario 3: Manifest lists the evaluator; Cursor gets it through the symlink

**Source:** Acceptance Criteria (AC-1.3) — Story 1

**Preconditions:**
- None.

**Steps:**
1. `grep -n -A3 "name: evaluator-agent" .writ/manifest.yaml`
2. `ls -la .cursor | grep agents`
3. `ls .cursor/agents/`
4. `git show --stat --format= cddc3e3 | grep -i cursor; echo "grep-exit=$?"`

**Expected Result:**
- Step 1: an entry with `file: agents/evaluator-agent.md` and `model_tier: anchor`.
- Step 2: `agents -> ../agents` (a symlink, not a directory).
- Step 3: the list includes `evaluator-agent.md`.
- Step 4: no match; `grep-exit=1`. Story 1 created no Cursor-specific file.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `.writ/manifest.yaml` (`agents:`); `SKILL.md` regenerated via `bash scripts/gen-skill.sh`

**Notes:**

---

### Scenario 4: The evaluator contract test passes on Python 3.9

**Source:** Acceptance Criteria (AC-1.4) — Story 1

**Preconditions:**
- `uv` installed.

**Steps:**
1. `uv run --python 3.9 pytest -q scripts/tests/test_evaluator_agent_contract.py -p no:cacheprovider`
2. `bash scripts/tests/test_model_tier_migration.sh; echo "exit=$?"`

**Expected Result:**
- Step 1: `10 passed`. No failures or errors.
- Step 2: passes with 8 agents; `exit=0`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `scripts/tests/test_evaluator_agent_contract.py` (includes a git-diff assertion that `agents/review-agent.md` is not edited)

**Notes:**

---

### Scenario 5: Story 1 did not touch the files it was told to leave alone

**Source:** Acceptance Criteria (AC-1.5) — Story 1

**Preconditions:**
- Full git history available (not a shallow clone).

**Steps:**
1. `git show --stat --format= cddc3e3 | grep -E "implement-story.md|review-agent.md|eval.sh|review-override.py"; echo "grep-exit=$?"`
2. `git show --stat --format= cddc3e3 | tail -1`

**Expected Result:**
- Step 1: no match; `grep-exit=1`.
- Step 2: the summary line lists 17 files changed. The list (visible without `tail`) contains spec files, the agent file and peers, the parity script, `SKILL.md`, and two test files only.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — commit `cddc3e32ac4fdb56c157e55326e1358b424165be`

**Notes:**

---

### Scenario 6: A missing evaluator peer is reported (scratch)

**Source:** Error Map ("Spawn evaluator — agent file missing") — Story 1

**Preconditions:**
- `$UAT` set.

**Steps:**
1. Copy the agent trees and the parity script into scratch, then delete the Claude peer:
   ```
   mkdir -p "$UAT/p/scripts" "$UAT/p/claude-code" "$UAT/p/codex"
   cp -R agents "$UAT/p/"; cp -R claude-code/agents "$UAT/p/claude-code/"; cp -R codex/agents "$UAT/p/codex/"
   cp scripts/check-agent-parity.sh "$UAT/p/scripts/"
   rm "$UAT/p/claude-code/agents/writ-evaluator.md"
   bash "$UAT/p/scripts/check-agent-parity.sh"; echo "exit=$?"
   ```
2. `grep -n -i "fallback" commands/implement-story.md | grep -i review; echo "grep-exit=$?"`

**Expected Result:**
- Step 1 prints `⚠️ agents/evaluator-agent.md has no counterpart in claude-code/agents/` and `exit=0`. The script warns; it never fails.
- Step 2: no match; `grep-exit=1`. The default path has no silent fallback to `review-agent` when the evaluator is missing.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `scripts/check-agent-parity.sh` (warnings-only by contract)

**Notes:**

---

## Story 2: Default Path and Flags

### Scenario 7: The Invocation table matches the flag matrix and has no `--default`

**Source:** Acceptance Criteria (AC-2.1) — Story 2

**Preconditions:**
- None.

**Steps:**
1. `sed -n '/^## Invocation/,/^## Pipeline/p' commands/implement-story.md`
2. `grep -c -- "--default" commands/implement-story.md`

**Expected Result:**
- Step 1 shows five rows: interactive selection; `story-3` = `coding-agent` + `evaluator-agent` + scripts; `--full-pipeline` = architecture-check, coding, review, testing, optional visual-qa, documentation; `--quick` = `coding-agent` only; `--review-only` = `evaluator-agent` only, with "FAIL ends the run; no recode; no silent `--full-pipeline`". Below the table: "`--full-pipeline`, `--quick`, `--review-only` are mutually exclusive: on a conflict, stop with a usage error; pick no winner."
- Step 2 prints `0`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — Files: `commands/implement-story.md` (Invocation table); commit `b99c4a3`

**Notes:**

---

### Scenario 8: Default spawn sites are Gate 1 and Gate 3 only

**Source:** Acceptance Criteria (AC-2.2) — Story 2

**Preconditions:**
- None.

**Steps:**
1. `grep -n -B2 "^> \*\*Agent:\*\*" commands/implement-story.md`
2. `sed -n '/^| Stage | Name/,/^| Step 4/p' commands/implement-story.md`
3. `grep -n "Gate 1 and Gate 3" commands/implement-story.md`

**Expected Result:**
- Step 1: eight marker lines. Gate 0.5 is `None — inline`. Gate 1 names `agents/coding-agent.md` (line ~216) and Gate 3 names `agents/evaluator-agent.md` (line ~264), each directly under its `#### Gate` heading. The other five (`architecture-check-agent`, `review-agent`, `testing-agent`, `visual-qa-agent`, `documentation-agent`) each sit directly under a `**`--full-pipeline`:**` line.
- Step 2: Gate 0 `arch-check.py` on default; Gate 3 `evaluator-agent` on default and `review-agent` on `--full-pipeline`; Gate 4 `test-integrity.py` on default (no testing-agent spawn); Gate 4.5 `visual-qa-agent` on `--full-pipeline` only, skipped on default even with visual refs; Gate 5 `docs-check.py` on default.
- Step 3: two lines (sub-agent completeness and worktree-integration notes), each reading "every spawn (Gate 1 and Gate 3; `--full-pipeline` also Gate 0, 4, 4.5)".

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — `--full-pipeline` Agent markers sit on the line after a `--full-pipeline` guard (Implementation Decision 3)

**Notes:**

---

### Scenario 9: Two-fail escalation is stated without an AskQuestion

**Source:** Acceptance Criteria (AC-2.3); Error Map ("Evaluator FAIL (1st)", "Evaluator FAIL (2nd)") — Story 2

**Preconditions:**
- None.

**Steps:**
1. `grep -n "evaluator_fail_count" commands/implement-story.md`
2. Read that line in full.
3. `grep -n "never escalates" commands/implement-story.md`

**Expected Result:**
- Step 2 (the Control flow line, ~96) states, in order: the counter starts at 0 per story; an evaluator FAIL increments it; the first FAIL recodes via Gate 1 and counts toward the review cycle; the second consecutive FAIL prints one notice that the rest of the story runs as `--full-pipeline`, then recodes via Gate 1 as for any FAIL, and the next Gate 3 spawns `review-agent`; it does not restart Gate 0 and does not AskQuestion; an evaluator PASS resets the counter.
- Step 3: both the Control flow line and the Quick Mode section say `--quick` never escalates.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — counter reset on PASS is Implementation Decision 4

**Notes:**

---

### Scenario 10: FAIL-only override still runs after Gate 3; default Gate 4 fail recodes via the coder

**Source:** Acceptance Criteria (AC-2.4); Error Map ("Gate 4 script fail on default") — Story 2

**Preconditions:**
- None.

**Steps:**
1. `sed -n '/^#### Gate 3: Review Agent/,/^#### Gate 3.5/p' commands/implement-story.md | grep -n "review-override.py\|FAIL-only\|Residual\|recorded_test_results"`
2. `sed -n '/^#### Gate 4: Testing Agent/,/^#### Gate 4.5/p' commands/implement-story.md | grep -n "coding-agent\|testing-agent"`
3. `grep -n "^| Evaluator Agent" commands/implement-story.md`

**Expected Result:**
- Step 1: the Gate 3 body says `recorded_test_results` is the orchestrator's own run of the story's tests (command, exit code, output tail), not the coding agent's report. `python3 scripts/review-override.py check ...` is still invoked after the agent returns. The override is FAIL-only: a script `pass` or `unverifiable` leaves the evaluator FAIL or PAUSE standing. The residual sentence names `evaluator-agent` on default and `review-agent` on `--full-pipeline`.
- Step 2: "Default: do not spawn `testing-agent`." A `test-integrity.py` `fail` on default uses BLOCKED escalation with agent `coding-agent`, restarting Gate 1; `--full-pipeline` keeps `testing-agent`, restarting Gate 4.
- Step 3: the Step 2 routing table has an `Evaluator Agent (Gate 3, default)` row: `spec_lite_for_review`, plus `knowledge_context` + AC + `recorded_test_results`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — Files: `commands/implement-story.md` (Gate 3, Gate 4 bodies)

**Notes:**

---

### Scenario 11: Gates 0, 4.5, 5 are script-only or skipped; gate numbers and provenance unchanged

**Source:** Acceptance Criteria (AC-2.5) — Story 2

**Preconditions:**
- Full git history available.

**Steps:**
1. `grep -n "^\*\*Default:\*\*" commands/implement-story.md`
2. `grep -n "ADR-024\|ABORT ask-user" commands/implement-story.md | head -4`
3. `grep -n "^#### Gate" commands/implement-story.md`
4. `grep -n -A1 "id: gate3_review" commands/implement-story.md`
5. `git show --stat --format= b99c4a3 | grep -E "review-override.py|eval.sh|review-agent.md"; echo "grep-exit=$?"`
6. `grep -n "Gate 0.5 exists only\|Gate 0.5 runs inline" commands/implement-story.md`

**Expected Result:**
- Step 1: Gate 0 "do not spawn `architecture-check-agent`. Run the script only"; Gate 4 "do not spawn `testing-agent`"; Gate 4.5 "skip — no `visual-qa-agent` spawn even with visual refs"; Gate 5 "do not spawn `documentation-agent`. Run the script only".
- Step 2: the ABORT ask-user and the ADR-024 floor→anchor re-run are `--full-pipeline` only.
- Step 3: headings are Gate 0, 0.5, 1, 2, 2.5, 3, 3.5, 4, 4.5, 5 — no new numbers. Gate 3's heading is still `Gate 3: Review Agent`.
- Step 4: `script: scripts/review-override.py`.
- Step 5: no match; `grep-exit=1`.
- Step 6: one line (~202): "Gate 0.5 runs inline on default and `--full-pipeline`." No "exists only on the full pipeline" line remains.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — file kept at 34063 bytes (still 34063 after the 2026-09-25 fixes) so the governor's `KNOWN_OVER_BUDGET` still matches (Implementation Decision 1)

**Notes:**

---

### Scenario 12: The default-path command test passes

**Source:** Acceptance Criteria (AC-2.1–AC-2.5, verified by Task 2.6) — Story 2

**Preconditions:**
- `uv` installed.

**Steps:**
1. `uv run --python 3.9 pytest -q scripts/tests/test_implement_story_default_path.py -p no:cacheprovider`
2. `wc -c commands/implement-story.md`

**Expected Result:**
- Step 1: `9 passed`.
- Step 2: `34063 commands/implement-story.md`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — Files: `scripts/tests/test_implement_story_default_path.py` (288 lines)

**Notes:**

---

### Scenario 13: A mechanical pass does not wash an evaluator FAIL

**Source:** Error Map ("`review-override.py` pass vs evaluator FAIL") — Story 2

**Preconditions:**
- `uv` installed.

**Steps:**
1. `uv run --python 3.9 pytest -q scripts/tests/test_review_override.py -p no:cacheprovider`
2. `bash scripts/tests/test_eval_review_override.sh`
3. `git log --oneline cddc3e3^..38dfdcf -- scripts/review-override.py; echo "lines=$(git log --oneline cddc3e3^..38dfdcf -- scripts/review-override.py | wc -l)"`

**Expected Result:**
- Step 1: `11 passed`.
- Step 2: `All 6 review-override check assertions passed.`
- Step 3: `lines=0`. No Stage 4b commit changed the override script.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — `review-override.py` does not parse agent output, so `EVALUATION_RESULT` needed no script change (Story 1 Implementation Decision 2)

**Notes:**

---

### Scenario 14: On default, Gate 0 without a planned set is `unverifiable`, not a third spawn

**Source:** Error Map ("Gate 0 ABORT-class on default") — Story 2

**Preconditions:**
- None.

**Steps:**
1. `python3 scripts/arch-check.py check --story .writ/specs/2026-09-09-phase11-stage4b-pipeline-demote/user-stories/story-2-default-path-and-flags.md --repo .; echo "exit=$?"`
2. `sed -n '/^#### Gate 0: Architecture/,/^\*\*`--full-pipeline`:\*\*/p' commands/implement-story.md | grep -n "unverifiable\|never prints"`

**Expected Result:**
- Step 1: `unverifiable`, `reason: no_file_mode`, `arch-check: unverifiable (no --planned or --changed)`; `exit=0`.
- Step 2: the Gate 0 body says an `unverifiable` verdict continues the pipeline and does not mark the story DEGRADED, and that the script never prints `abort`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — Files: `commands/implement-story.md` (Gate 0 default body)

**Notes:**

---

### Scenario 15: `--quick`, `--review-only`, and re-run behavior around escalation

**Source:** Edge Case ("`--quick` and two-fail", "`--review-only` FAIL", "Re-run after escalation") — Story 2

**Preconditions:**
- None.

**Steps:**
1. `sed -n '/^## Quick Mode/,/^## Completion/p' commands/implement-story.md`
2. `grep -n "review-only" commands/implement-story.md | grep -i "fail ends\|no recode"`
3. `grep -n "starts at 0 per story" commands/implement-story.md`

**Expected Result:**
- Step 1: `--quick` skips Gate 3 (evaluator), so no evaluator FAIL can occur and "never escalates" is stated. It keeps Gate 1, Gate 2, and the Gate 0/4/5 scripts.
- Step 2: at least two lines (Invocation row and Gate 3 header) say a `--review-only` FAIL ends the run with no recode and no silent `--full-pipeline`.
- Step 3: the counter is per story, so a new invocation starts at 0.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — DEV-002 (Control flow line omits the `--review-only` exception; stated in Invocation and Gate 3 instead)

**Notes:**

---

### Scenario 16: Visual references do not trigger visual QA on default

**Source:** Edge Case ("Visual refs on default") — Story 2

**Preconditions:**
- None.

**Steps:**
1. `sed -n '/^#### Gate 4.5/,/^#### Gate 5/p' commands/implement-story.md | head -12`

**Expected Result:**
- "**Default:** skip — no `visual-qa-agent` spawn even with visual refs." The `visual-qa-agent` marker sits directly under `**`--full-pipeline`:**`. The auto-activation rule follows, and the next line starts "`--full-pipeline` spawn:".

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — Files: `commands/implement-story.md` (Gate 4.5)

**Notes:**

---

### Scenario 17: Conflicting flags have a documented resolution

**Source:** Edge Case ("Concurrent `--full-pipeline` + `--quick`") — Story 2

**Preconditions:**
- None.

**Steps:**
1. `grep -n -i "conflict\|mutually exclusive\|both flags" commands/implement-story.md; echo "grep-exit=$?"`
2. Read the Invocation table and Quick Mode section for any rule covering `/implement-story story-3 --full-pipeline --quick`.

**Expected Result:**
- Step 1: one match at line ~75: "`--full-pipeline`, `--quick`, `--review-only` are mutually exclusive: on a conflict, stop with a usage error; pick no winner."; `grep-exit=0`.
- Step 2: that line sits directly under the Invocation table. `/implement-story story-3 --full-pipeline --quick` stops with a usage error; neither flag wins.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 18 (optional, live): A default run spawns exactly two sub-agents

**Source:** Experience Design (Entry point, Happy path, Moment of truth); Shadow Path ("Default `/implement-story`") — Story 2

**Preconditions:**
- Claude Code installed. About 15–30 minutes and model budget for one small story.
- `$UAT` set.
- A throwaway clone: `git clone -q . "$UAT/clone"`. Work only in the clone.

**Steps:**
1. In the clone, create `.writ/specs/2099-01-01-uat-demo/` with a one-paragraph `spec.md`, a short `spec-lite.md`, and `user-stories/story-1-hello.md` containing `> **Status:** Not Started`, three Given/When/Then acceptance criteria (for example: `scripts/uat_hello.py` exists; `python3 scripts/uat_hello.py` prints `hello`; a pytest file covers it), and matching tasks.
2. In the clone, start `claude` and run `/implement-story` with no argument.
3. Pick `story-1-hello` from the selector.
4. Let the run finish. In the transcript, count the sub-agent (Task) spawns and note their names.
5. Look for the Gate 0, Gate 4, and Gate 5 script outputs (`arch-check`, `test-integrity`, `docs-check`) in the transcript.

**Expected Result:**
- Step 2 shows a story selector (nil-input shadow path), not an error.
- Step 4: exactly two spawns, `writ-coder` then `writ-evaluator`. No `writ-architect`, `writ-reviewer`, `writ-tester`, or `writ-documenter`.
- Step 5: each script prints `pass`, `fail`, or `unverifiable`; an `unverifiable` result does not mark the story DEGRADED.
- If the evaluator FAILs twice, one notice says the rest of the story runs as `--full-pipeline`, with no AskQuestion. The coder recodes, and the next Gate 3 spawns `writ-reviewer`.
- The story file ends with `## What Was Built`. Delete the clone afterwards.

**Status:** [ ] Pass  [ ] Fail  [ ] Skipped

**Notes:**

---

## Story 3: Eval, Adapters, and Spawn-Cap Proof

### Scenario 19: `spawn-cap.py` verdict table on the real command, missing input, and bad argv

**Source:** Acceptance Criteria (AC-3.1); Error Map ("`spawn-cap.py` — command file missing") — Story 3

**Preconditions:**
- `python3` 3.9 or later on PATH.

**Steps:**
1. `python3 scripts/spawn-cap.py check --command commands/implement-story.md; echo "exit=$?"`
2. `python3 scripts/spawn-cap.py check; echo "exit=$?"`
3. `python3 scripts/spawn-cap.py check --command does-not-exist.md; echo "exit=$?"`
4. `python3 scripts/spawn-cap.py frob; echo "exit=$?"`
5. `python3 scripts/spawn-cap.py check --bogus; echo "exit=$?"`
6. `python3 scripts/spawn-cap.py check --project . --command commands/implement-story.md; echo "exit=$?"`

**Expected Result:**
- Step 1: `pass`, then `spawn-cap: pass (default spawn sites at or under cap)`; `exit=0`.
- Step 2: `unverifiable`, `reason: missing_command`, `spawn-cap: unverifiable (no --command)`; `exit=0`.
- Step 3: `unverifiable`, `reason: missing_command`, `spawn-cap: unverifiable (command unreadable)`; `exit=0`.
- Step 4: usage on stderr naming `invalid choice: 'frob'`; `exit=2`.
- Step 5: usage error on stderr; `exit=2`.
- Step 6: same as Step 1 (`--project` is an alias of `--repo`).

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — Files: `scripts/spawn-cap.py` (161 lines after the 2026-09-25 scope fix); commit `38dfdcf`

**Notes:**

---

### Scenario 20: A third or disallowed default spawn site fails with `over_cap` (scratch)

**Source:** Acceptance Criteria (AC-3.1); Error Map ("`spawn-cap.py` — third default Agent marker") — Story 3

**Preconditions:**
- `$UAT` set.

**Steps:**
1. Add a third unguarded marker:
   ```
   cp commands/implement-story.md "$UAT/over.md"
   printf '\n#### Gate 9: Extra\n\n> **Agent:** `agents/testing-agent.md`\n' >> "$UAT/over.md"
   python3 scripts/spawn-cap.py check --command "$UAT/over.md"; echo "exit=$?"
   ```
2. Swap the default Gate 3 evaluator for `review-agent`:
   ```
   sed 's#> \*\*Agent:\*\* `agents/evaluator-agent.md`#> **Agent:** `agents/review-agent.md`#' commands/implement-story.md > "$UAT/swap.md"
   python3 scripts/spawn-cap.py check --command "$UAT/swap.md"; echo "exit=$?"
   ```
3. Add an unguarded `Task(` spawn line:
   ```
   printf '\nTask(subagent_type="testing-agent")\n' | cat commands/implement-story.md - > "$UAT/task.md"
   python3 scripts/spawn-cap.py check --command "$UAT/task.md"; echo "exit=$?"
   ```

**Expected Result:**
- Each step prints `fail`, `reason: over_cap`, `spawn-cap: fail (default spawn sites over cap)`; `exit=1`.
- Step 1 and 3 show the count cap. Step 2 shows the stem allow-list: two sites, but one is not `coding-agent` or `evaluator-agent`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 21: Output shape, no accept/reject wording, no live Tasks, read-only

**Source:** Acceptance Criteria (AC-3.1) — Story 3

**Preconditions:**
- Working tree state recorded: `git status --porcelain > "$UAT/before.txt"`.

**Steps:**
1. `python3 scripts/spawn-cap.py check --command commands/implement-story.md | grep -Ei "accept|reject|modify-spec"; echo "grep-exit=$?"`
2. `grep -n "^import\|^from" scripts/spawn-cap.py`
3. `git status --porcelain | diff "$UAT/before.txt" - && echo unchanged`

**Expected Result:**
- Step 1: no match; `grep-exit=1`.
- Step 2: only `__future__`, `argparse`, `re`, `sys`, `pathlib`, `typing`. No `subprocess`, network, or agent client, so the script cannot spawn a Task.
- Step 3: `unchanged`.
- Across Scenarios 19–20, every run printed one verdict line first and the `spawn-cap:` summary last.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 22: `spawn-cap` is registered in `eval.sh` and reports as a note on the live repo

**Source:** Acceptance Criteria (AC-3.2) — Story 3

**Preconditions:**
- Run outside any sandbox (`eval.sh` may create temp git repos in other checks; this one does not).

**Steps:**
1. `sed -n '/^CHECKS=(/,/^)/p' scripts/eval.sh | tail -4`
2. `sed -n '/^check_spawn_cap()/,/^}/p' scripts/eval.sh`
3. `bash scripts/eval.sh --check=spawn-cap; echo "exit=$?"`
4. Open the report file path printed in Step 3.

**Expected Result:**
- Step 1: `spec-analyze`, `goal-emit`, `spawn-cap`, `)` — `spawn-cap` is right after `goal-emit`.
- Step 2: missing helper → `add_finding`; helper exit 2 → `add_finding`; a `fail` line → `add_finding` ("spawn-cap printed fail: ..."); a `reason:` line → `add_finding` when the helper exited 1, otherwise a note; every other line (verdict `pass` / `unverifiable`, the summary) → `add_note "NOTE [spawn-cap]: ..."`.
- Step 3: `Eval report: .writ/state/eval-<timestamp>.md`; `exit=0`.
- Step 4: `## spawn-cap` reads `PASS`, with notes `NOTE [spawn-cap]: pass` and `NOTE [spawn-cap]: spawn-cap: pass (default spawn sites at or under cap)`; `Findings: 0`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — Files: `scripts/eval.sh` (`CHECKS`, `check_spawn_cap`)

**Notes:**

---

### Scenario 23: A missing helper is an eval finding (scratch)

**Source:** Error Map ("`eval.sh` — helper missing") — Story 3

**Preconditions:**
- `$UAT` set.

**Steps:**
1. Copy `eval.sh` and the command into a scratch root with no helper:
   ```
   mkdir -p "$UAT/e1/scripts" "$UAT/e1/commands"
   cp scripts/eval.sh "$UAT/e1/scripts/"; cp commands/implement-story.md "$UAT/e1/commands/"
   bash "$UAT/e1/scripts/eval.sh" --check=spawn-cap; echo "exit=$?"
   cat "$UAT/e1"/.writ/state/eval-*.md
   ```

**Expected Result:**
- `exit=1`.
- The report shows `## spawn-cap` `FAIL (1 finding(s))` with "`scripts/spawn-cap.py`: spawn-cap helper is missing." and `Findings: 1`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 24: A real `over_cap` is a blocking eval finding (scratch)

**Source:** Acceptance Criteria (AC-3.2, superseded by the 2026-09-25 fix; see Honest Note 4) — Story 3

**Preconditions:**
- `$UAT` set; `$UAT/over.md` from Scenario 20.

**Steps:**
1. Build a scratch root with the real helper and the over-cap command:
   ```
   mkdir -p "$UAT/e2/scripts" "$UAT/e2/commands"
   cp scripts/eval.sh scripts/spawn-cap.py "$UAT/e2/scripts/"
   cp "$UAT/over.md" "$UAT/e2/commands/implement-story.md"
   bash "$UAT/e2/scripts/eval.sh" --check=spawn-cap; echo "exit=$?"
   sed -n '/## spawn-cap/,/## Summary/p' "$UAT/e2"/.writ/state/eval-*.md
   ```

**Expected Result:**
- `exit=1`. `## spawn-cap` reads `FAIL (2 finding(s))`:
  - `scripts/spawn-cap.py`: "spawn-cap printed fail: commands/implement-story.md names more default-path spawn sites than the cap allows." Remediation: guard the extra marker with `--full-pipeline` or remove it.
  - `spawn-cap:over_cap`: "over_cap". Remediation: "Keep default-path spawns to coding-agent and evaluator-agent (cap 2)."
- One note remains: `NOTE [spawn-cap]: spawn-cap: fail (default spawn sites over cap)`. `Findings: 2`.
- `eval.sh` now stops a third default spawn from landing, in addition to the pytest guard `test_real_command_is_at_or_under_cap` (Scenario 26). Guarded `--full-pipeline` sites never reach this branch because the helper excludes them.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 25: Adapters no longer present no-flag `/implement-story` as the full SDLC

**Source:** Acceptance Criteria (AC-3.3) — Story 3

**Preconditions:**
- Full git history available.

**Steps:**
1. `git show --format= 38dfdcf -- adapters/ | grep "^[-+]"`
2. `grep -n -i "full SDLC\|five-agent\|six-gate" adapters/*.md`
3. `git show --format= 38dfdcf -- adapters/ | grep -i "^+.*goal"; echo "grep-exit=$?"`
4. `grep -rn -i "high-stakes\|high_stakes" adapters/ commands/implement-story.md; echo "grep-exit=$?"`

**Expected Result:**
- Step 1 (Story 3's commit): four files change. Headings become `implement-story --full-pipeline ...` in `claude-code.md`, `codex.md`, `openclaw.md`, each followed by one sentence naming the default as coder + evaluator + scripts. In that commit `cursor.md`'s quick-start line became `/implement-story --full-pipeline  # Build it with the full SDLC pipeline`; the 2026-09-25 fix replaced it (Step 2).
- Step 2: one hit, `adapters/cursor.md:263:/implement-story         # Build it (coding + evaluator; --full-pipeline opts into the full SDLC pipeline)`. The Cursor quick-start now points new users at the default path.
- Step 3: no match; `grep-exit=1`. No `/goal` section was added (the existing `/goal Stop Hook` section in `claude-code.md` predates this spec).
- Step 4: no match; `grep-exit=1`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — DEV-003: knowledge-loading lines in adapters still name architecture-check / review recipients (accepted; Honest Note 3)

**Notes:**

---

### Scenario 26: Spawn-cap and eval-wiring tests pass

**Source:** Acceptance Criteria (AC-3.4) — Story 3

**Preconditions:**
- `uv` installed.

**Steps:**
1. `uv run --python 3.9 pytest -q scripts/tests/test_spawn_cap.py -p no:cacheprovider`
2. `bash scripts/tests/test_eval_spawn_cap.sh; echo "exit=$?"`

**Expected Result:**
- Step 1: `19 passed`, including `test_real_command_is_at_or_under_cap` and the five scope cases added 2026-09-25 (`test_fail_marker_after_sentence_mentioning_flag`, `test_fail_flag_on_marker_line_is_not_scope`, `test_fail_scope_ends_at_blank_line`, `test_pass_multiline_scope_excluded`, `test_fail_real_command_plus_scenario_29_marker`).
- Step 2: includes `PASS: spawn-cap fail stub -> exit 1, add_finding` and ends with `All 6 spawn-cap eval-wiring assertions passed.`; `exit=0`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — Files: `scripts/tests/test_spawn_cap.py` (in-process `main()` import so coverage sees the helper; 98% line coverage), `scripts/tests/test_eval_spawn_cap.sh`

**Notes:**

---

### Scenario 27: Proof recorded, decision log written, full eval green, nothing emitted or merged

**Source:** Acceptance Criteria (AC-3.5) — Story 3

**Preconditions:**
- Run outside any sandbox. The full eval takes about 2 minutes.

**Steps:**
1. `sed -n '/^### Test Results/,/^### Review Outcome/p' .writ/specs/2026-09-09-phase11-stage4b-pipeline-demote/user-stories/story-3-eval-adapters-proof.md | head -12`
2. `grep -n "stage-4b:" .writ/decision-log.md`
3. `git show --stat --format= 38dfdcf | grep -E "implement-story.md|GOAL.md"; echo "grep-exit=$?"`
4. `bash scripts/eval.sh > "$UAT/eval.out" 2>&1; echo "exit=$?"; tail -1 "$UAT/eval.out"`

**Expected Result:**
- Step 1: Test Results lists `spawn-cap.py check --command commands/implement-story.md` → `pass`, the 14/6 test counts, `eval.sh` exit 0, and that `--full-pipeline` still names architecture-check, review, testing, visual-qa, documentation. The 14 is the count at Story 3 completion; the current count is 19 (Scenario 26, Honest Note 4).
- Step 2: three `2026-09-09 stage-4b:` lines; the last names evaluator, default spawn, and `spawn-cap.py` / eval spawn-cap.
- Step 3: no match; `grep-exit=1`. Story 3 did not change `implement-story.md` spawn logic and emitted no `GOAL.md`.
- Step 4: `exit=0`; the last line is `Eval report: .writ/state/eval-<timestamp>.md`, and that report's Summary reads `Findings: 0`, `Run errors: 0`. With spawn-cap `fail` now blocking, this also confirms the real command is at or under the cap.
- Story 3's Review Outcome (Boundary Compliance) reads "No emit / eight-run / yuss / merge / PR / release" (ADR-013).

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — optional spawn-cap pointer comment in `implement-story.md` was skipped to stay at 34063 bytes (Implementation Decision 2)

**Notes:**

---

### Scenario 28: A command with zero default spawn markers fails as `over_cap` (scratch)

**Source:** Shadow Path ("`spawn-cap.py check` — empty input") — Story 3

**Preconditions:**
- `$UAT` set.

**Steps:**
1. `printf '# empty command\n' > "$UAT/zero.md"; python3 scripts/spawn-cap.py check --command "$UAT/zero.md"; echo "exit=$?"`

**Expected Result:**
- `fail`, `reason: over_cap`, fail summary; `exit=1`. The technical spec allowed `fail` or `unverifiable` here; the implementation chose `fail` (Implementation Decision 1). The reason name `over_cap` is misleading for zero sites (Honest Note 5).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 29: An extra default marker after a sentence mentioning `--full-pipeline` is counted (scratch)

**Source:** Shadow Path ("`spawn-cap.py check` — upstream error: extra default Agent line → `fail` `over_cap`") — Story 3

**Preconditions:**
- `$UAT` set.

**Steps:**
1. Append a default-path marker preceded by an ordinary sentence that mentions the flag:
   ```
   printf '\nSee --full-pipeline for more.\n> **Agent:** `agents/testing-agent.md`\n' | cat commands/implement-story.md - > "$UAT/weak.md"
   python3 scripts/spawn-cap.py check --command "$UAT/weak.md"; echo "exit=$?"
   ```

**Expected Result:**
- `fail`, `reason: over_cap`, `spawn-cap: fail (default spawn sites over cap)`; `exit=1`. A sentence that mentions `--full-pipeline` does not open a scope; only the exact label line `**`--full-pipeline`:**` does.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — `scripts/spawn-cap.py` `_default_agent_markers` (2026-09-25: scope = the exact label line plus the contiguous `>` lines under it; pinned by `test_fail_marker_after_sentence_mentioning_flag` and `test_fail_real_command_plus_scenario_29_marker`)

**Notes:**

---

### Scenario 30: `--full-pipeline` still names six spawn sites and does not affect the cap

**Source:** Shadow Path ("`--full-pipeline`") — Story 3

**Preconditions:**
- None.

**Steps:**
1. `grep -n -A1 '^\*\*`--full-pipeline`:\*\*' commands/implement-story.md | grep "Agent:"`
2. `grep -n "^> \*\*Agent:\*\* \`agents/coding-agent.md\`" commands/implement-story.md`
3. `python3 scripts/spawn-cap.py check --command commands/implement-story.md | head -1`

**Expected Result:**
- Step 1: five guarded markers — `architecture-check-agent`, `review-agent`, `testing-agent`, `visual-qa-agent`, `documentation-agent`.
- Step 2: one `coding-agent` marker (Gate 1), shared by default and `--full-pipeline`. Together with Step 1 that is the six `--full-pipeline` sites.
- Step 3: `pass`. The five markers inside `--full-pipeline` scopes do not count against the cap.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Pending Stories

None. All three stories are Completed ✅.
