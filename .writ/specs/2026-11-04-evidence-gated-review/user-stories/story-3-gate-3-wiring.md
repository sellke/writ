# Story 3: Gate 3 wiring for evidence-gated findings

> **Status:** Completed ✅ (2026-11-04)
> **Priority:** High
> **Dependencies:** Story 2

## User Story

**As a** developer running `/implement-story`
**I want to** block an agent FAIL only on executed evidence, and see one `evidence-gate:` line for each Gate 3 outcome
**So that** unbacked findings stop blocking stories, and a confirmed finding reaches the coder with its repro

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [x] Given an agent FAIL with `check` and `safety-fact` results in hand, when Gate 3 applies its decision, then the first matching row of spec.md → ## Business Rules (Expanded) → ### Gate 3 decision sets the result, and `evidence` runs on every agent FAIL. This story adds no `evidence` run on PASS or PAUSE; row 3a's `--prior` run on those verdicts is Story 4's. `[AC-3.1]`
- [x] Given Gate 3 has reached any state in spec.md → ## Experience Design → ### State Catalog, when the story report prints, then it contains exactly one `evidence-gate:` line that matches that state's row. `[AC-3.2]`
- [x] Given a Gate 2 run and an agent FAIL, when Gate 3 saves its inputs, then `.writ/state/gate2-checks-<story-stem>.txt` lists the lint and typecheck commands one per line, and the review output and recorded test results are saved to `gate3-review-<story-stem>.md` and `gate3-tests-<story-stem>.txt` whether or not `safety-fact` is on. `[AC-3.3]`
- [x] Given the `evaluator-agent` and `review-agent` source files, when the wiring is complete, then each has one conditional `Read skills/evidence-gated-findings/SKILL.md` line, one `**Evidence:**` field after `**Category:**` in its Issues Found format, Critical and Major severity text that blocks only with evidence, and unchanged `reviewer_filters` lines. `[AC-3.4]`
- [x] Given a saved evaluator FAIL whose Critical and Major findings carry no `Evidence:` block, when the replay runs `evidence` and applies the Gate 3 decision, then Gate 3 returns PASS and lists each finding as advisory. Given the same FAIL with one confirmed `test` repro, Gate 3 returns FAIL and names the confirmed finding. `[AC-3.5]`

## Implementation Tasks

- [x] 3.1 Write `scripts/tests/test_evidence_gate_wiring.py` first. Wiring assertions: the Gate 3 block orders `check`, then `safety-fact`, then `evidence`; the nine decision rows and the State Catalog report lines are present; the Gate 2 save line exists; both agent files carry the Read line, the `**Evidence:**` field, and the severity text. Replay: feed two saved evaluator FAIL outputs through `evidence`, one with no Evidence blocks and one with one confirmed `test` repro. Run it in a temporary `git init` copy of a fixture project under `scripts/tests/fixtures/review-override/evidence/`, with `Test Runner` set in its `.writ/config.md`. Before any edit, record `wc -c commands/implement-story.md`. Confirm the wiring assertions fail on the current tree. `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`
- [x] 3.2 In `#### Gate 2`, after the linters, save the lint and typecheck commands that ran to `.writ/state/gate2-checks-<story-stem>.txt`, one per line. In `#### Gate 3`, on every agent FAIL, save the agent output to `.writ/state/gate3-review-<story-stem>.md` and `recorded_test_results` to `.writ/state/gate3-tests-<story-stem>.txt`, whether or not `safety-fact` is on. `[AC-3.3]`
- [x] 3.3 In `#### Gate 3`, after `check` and `safety-fact`, run `review-override.py evidence` on every agent FAIL, with the arguments in technical-spec.md → ## Gate 3 Wiring. Pass `--changed` as the list Gate 2.5 classified. Omit `--prior` and `--manifest-out`; Story 4 adds them. Apply all nine rows of the Gate 3 decision in order. Print one `evidence-gate:` line for each State Catalog row. Map `reason: switch_off` to `evidence-gate: off`, and line 1 `fail` with `repro_mutated_tree` to `blocked (...)`. Print downgraded findings under `evidence-gate advisory:`. An `unverifiable` result never sets `⚠️ DEGRADED`. Do not edit the reviewer-filters or panel paragraphs. `[AC-3.1, AC-3.2]`
- [x] 3.4 In `agents/evaluator-agent.md` and `agents/review-agent.md`, add an `evidence_gate` input row. Add one conditional `Read skills/evidence-gated-findings/SKILL.md` line: after the `reviewer_filters` Read line in the evaluator, and after the safety-fact Read line in the review agent. Add `**Evidence:**` after `**Category:**` in the Issues Found format (technical-spec.md → ## Evidence Block Grammar). Rewrite the Critical and Major rows of Severity Definitions so they block only when the issue carries an Evidence block. Align the "When to FAIL" bullets that name Critical or Major with that text. Keep every `reviewer_filters` row and line. `[AC-3.4]`
- [x] 3.5 Run `python3 scripts/gen-platform-trees.py` and include the regenerated trees in the same change as the sources. Run `scripts/tests/test_evidence_gate_wiring.py` green on Python 3.9 (`uv run --isolated --python 3.9 --with pytest pytest scripts/tests/test_evidence_gate_wiring.py`), then on 3.14. `[AC-3.4, AC-3.5]`
- [x] 3.6 Verify each AC against the diff and the test output. Run the full pytest suite on 3.9 and 3.14, one at a time, with nothing else writing to the checkout. Run the bash suite in the background. Run `python3 scripts/gen-platform-trees.py --check` and `bash scripts/eval.sh`. Record `wc -c commands/implement-story.md` after the edits, and the before and after counts with the delta, in What Was Built. `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`

## Notes

- **Story 2 comes first.** This story calls `review-override.py evidence`, uses `switch --name evidence-gate`, and reads `skills/evidence-gated-findings/SKILL.md`. None of these exist yet.
- **Open choice: the agent Read condition.** The spec says the agents get a "conditional" Read line but does not name the condition. This story uses an `evidence_gate` input. Gate 3 resolves it once per story with `review-override.py switch --name evidence-gate` and passes it to every Gate 3 spawn. Confirm before task 3.4.
- **Re-review rows wait for Story 4.** The `repro_removed`, `repro_modified`, and `repro_still_failing` states need `--prior`. This story maps the `fail (<reason>)` line. Its tests do not assert those rows.
- **Placement pin.** `scripts/tests/test_review_route_rigor.py` (`test_conditional_line_follows_filters_line`) requires the safety-fact Read line to sit two lines after the reviewer-filters Read line. Put the evidence Read after the safety-fact line in `review-agent.md`, or that test fails. The pin stays, because the filters stay (spec.md → Amendment).
- **Row 3 re-spawns.** A `review-agent` re-spawn can change the agent output. Run `evidence` on the output Gate 3 holds after row 3 resolves.
- **Gate 2 scope.** The spec names lint and typecheck commands only. Gate 2 also runs arch-lint commands. Those are not saved, so a `check` repro cannot run them.
- **Scope of the "When to FAIL" edit.** Task 3.4 aligns those bullets with the new severity text. The spec names only the Severity Definitions. Without this, the agent gets two conflicting rules.
- **Test isolation.** The replay must not run in the live checkout. A repro writes into the repo, and the tree snapshot would see it. Do not run pytest while `eval.sh` or other writes to `.writ/state/` run in the same checkout.
- **Byte budget.** `commands/implement-story.md` measured 40759 bytes at authoring (2026-11-04). This story adds bytes. The stories that edit it (3, 4, and 7) must net to zero or less (spec.md → ## Implementation Approach → Byte budget). Story 7 carries the cuts. Re-measure before task 3.1.
- **Overlap.** `2026-10-25-design-divergence` also edits `commands/implement-story.md`, in Gate 0 only. If it has landed, rebase on it (spec.md → ## Specification Contract → Cross-Spec Overlap).

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Read the review output, Resolve the runner, Run the repro] — from technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [Happy, Nil, Empty, Upstream error] — from technical-spec.md → ## Shadow Paths
- **Business rules:** [Gate 3 decision (nine rows, first match wins), Switch (Evidence Gate off restores agent blocking)] — from spec.md → ## Business Rules (Expanded) → ### Gate 3 decision and ### Switch
- **Experience:** [State Catalog (one evidence-gate line per state), Interaction patterns (advisory lines for downgraded findings)] — from spec.md → ## Experience Design → ### State Catalog and ### Interaction patterns

---

## What Was Built

**Implementation Date:** 2026-11-04

### Files Created

1. **`scripts/tests/test_evidence_gate_wiring.py`** (679 lines)
   - A Story 3 header naming `2026-11-04-evidence-gated-review` and `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`.
   - 30 tests in 7 classes: `Gate2SaveTest` (2), `Gate3SaveTest` (4), `Gate3OrderTest` (4), `Gate3DecisionTest` (2), `Gate3ReportLineTest` (6), `AgentEvidenceWiringTest` (9), `ReplayTest` (3).
   - Test-local mirrors of the decision table (`gate3_decision`) and the report line (`gate3_report_line`). Row numbers and terms tie them to the markdown.
   - `ReplayTest` parses the one documented `evidence` command out of `commands/implement-story.md`, fills its placeholders, and runs it with real pytest in a temp `git init` copy of `scripts/tests/fixtures/review-override/evidence/pytest-project/`, with `Test Runner` set in the copy's `.writ/config.md`. Nothing runs in the Writ checkout.

### Files Modified

- **`commands/implement-story.md`** (`#### Gate 2`; `#### Gate 3`) — 40759 → 41939 bytes, +1180
  - Gate 2: save the lint and typecheck commands that ran, not the auto-fixes, to `.writ/state/gate2-checks-<story-stem>.txt`, one per line.
  - Gate 3: an **Evidence gate** paragraph after **Reviewer filters**. It resolves `switch --name evidence-gate` once and passes line 1 as `evidence_gate` to every Gate 3 spawn.
  - Gate 3: the save line moved out of the safety-fact paragraph. "On an agent FAIL or with `safety_fact` on", it saves the review to `<review>` = `.writ/state/gate3-review-<story-stem>.md` (re-save on re-spawn) and `recorded_test_results` to `<tests>` = `.writ/state/gate3-tests-<story-stem>.txt`.
  - Gate 3: an **Evidence.** paragraph. On an agent FAIL, after `check`, `safety-fact`, and any re-spawn, it runs `review-override.py evidence --review-output <review> --changed <files> --tests-output <tests> --checks .writ/state/gate2-checks-<story-stem>.txt --timeout 60`. Then comes the nine-row decision table ("First match wins, on any verdict"), the `evidence-gate:` report line, and `evidence-gate advisory:` lines.
  - Five cuts: the check bullet shortened to "→ no override; print the reason; never `⚠️ DEGRADED`"; `--repo .` dropped from the command; the `safety_fact_contradicts_verdict` bullet moved into table row 2; the FAIL-only sentence dropped; the stale architecture/security/taste sentence dropped.
- **`agents/evaluator-agent.md`** (Inputs; Prompt Template; Issues Found format; Severity Definitions; On FAIL example; When to FAIL)
  - `evidence_gate` input row.
  - Conditional Read line two lines after the `reviewer_filters` Read line. It ends "Still set FAIL; Gate 3 makes unbacked issues advisory."
  - `**Evidence:**` after `**Category:**`.
  - Critical and Major rows: "FAIL; with `evidence_gate` `on`, it blocks only with an `**Evidence:**` field". The When to FAIL bullet carries the same text.
  - The FAIL example's Category reads `criterion [AC-1.2]`.
  - Every `reviewer_filters` row and line unchanged.
- **`agents/review-agent.md`** (same sections)
  - The same changes. The Read line follows the safety-fact Read line, so `test_conditional_line_follows_filters_line` stays green.
- **12 generated trees** (`scripts/gen-platform-trees.py`)
  - `claude-code/agents/writ-evaluator.md`, `claude-code/agents/writ-reviewer.md`, `codex/agents/evaluator-agent.toml`, `codex/agents/review-agent.toml`, `cursor/plugin/agents/evaluator-agent.md`, `cursor/plugin/agents/review-agent.md`, `cursor/plugin/commands/implement-story.md`, `plugins/writ/agents/evaluator-agent.md`, `plugins/writ/agents/review-agent.md`, `plugins/writ/agents/writ-evaluator.md`, `plugins/writ/agents/writ-reviewer.md`, `plugins/writ/commands/implement-story.md`.
- **Test pins**, each following a sentence this story removed or moved
  - `scripts/tests/test_governor_enforcement.py`: `KNOWN_OVER_BUDGET["commands/implement-story.md"]` re-pinned 15799 → 16979, with a dated comment carrying the byte arithmetic.
  - `scripts/tests/test_implement_story_default_path.py::test_ac24_override_and_gate4_fail`: "FAIL-only", "does not force PASS", and "does not wash" replaced by "→ no override". The line holding "→ no override" must also hold "never `⚠️ DEGRADED`".
  - `scripts/tests/test_review_override.py::Gate3WiringTests.test_implement_story_has_fail_only_verify_block`: the same replacement.
  - `scripts/tests/test_review_route_rigor.py`: `test_unverifiable_is_not_degraded` slices to `**Evidence.**`, not `**Jev shadow`; `test_contradicts_routes_before_re_review` checks the table (row 2 before row 3).
- **`.writ/specs/2026-11-04-evidence-gated-review/spec-lite.md`** (For Review Agents)
  - The `--timeout 60` and `--repo .` default line (DEV-011).
- **`.writ/specs/2026-11-04-evidence-gated-review/drift-log.md`** (Story 3 section)
  - DEV-010 and DEV-011 appended. Existing entries untouched.

### Implementation Decisions

1. **The agent Read condition is an `evidence_gate` input** — Gate 3 resolves it once per story with `switch --name evidence-gate` and passes it to every Gate 3 spawn. The story left this open; the orchestrator confirmed it before task 3.4.
2. **`off` follows the switch, not `reason: switch_off`** — task 3.3 said to map `reason: switch_off` to `evidence-gate: off`, but `evidence` only runs on an agent FAIL, so an agent PASS or PAUSE with the switch off printed `not run (...)`. Row 5 now keys on `evidence_gate` `off` and the report prints `off` on any verdict, as contract Business Rule 7 and the State Catalog "Switch off" row require. This came from Gate 3 iteration 1, Issue 1. The spec was not amended.
3. **The table applies on any verdict** — the opener reads "First match wins, on any verdict", so rows 1 to 4 (`check` `fail`, contradicts, missing or below floor, agent PASS or PAUSE) route a PASS too. `evidence` itself runs only on an agent FAIL.
4. **The save line is its own paragraph** — it binds `<review>` and `<tests>`, keeps the `safety_fact` condition, and re-saves on re-spawn, so `evidence` reads the output Gate 3 holds after row 3 resolves.
5. **The FAIL-only sentence was cut** — row 9 now washes an agent FAIL, so "does not wash an evaluator FAIL" became false. The check bullet's "→ no override" carries the rule for `check`.
6. **The agents still set FAIL** — both Read lines end "Still set FAIL; Gate 3 makes unbacked issues advisory." Without it an agent could read "blocks only with evidence" as "PASS", and `evidence` would never run (iteration 1, Issue 3).
7. **FAIL examples cite an AC ID** — `criterion [AC-1.2]`, because `evidence` labels a criterion with no AC ID `advisory (no_claim)` even with valid evidence.
8. **Gate 3 passes `--timeout 60`** — five runs fit the Bash tool's 600 s limit (DEV-011).

### Test Results

**Verification:** Automated, test-first.
**Coverage:** unverifiable (no coverage report)

- ✅ Red first: the first Gate 1 run failed 23 and passed 3, then went green. Recode 1: red at 8 failed, then 30 passed.
- ✅ `uv run --isolated --python 3.9 --with pytest pytest scripts/tests/test_evidence_gate_wiring.py` → 30 passed
- ✅ Same on `--python 3.14` → 30 passed
- ⚠️ Full suite on 3.9 → 4271 passed, 2 failed. Full suite on 3.14 → 4271 passed, 1152 subtests, 2 failed. The same two fail on both:
  - `test_divergence_trial_outcome.py::test_repo_matches_the_committed_verdict` predates this story. Commit `6a00b56` recorded the design-divergence verdict and the repo has not acted on it. Design-divergence Story 6 owns it.
  - `test_evaluator_agent_contract.py::test_review_agent_not_in_story_edit_set` fails on any uncommitted edit to `agents/review-agent.md`. Task 3.4 requires that edit. The test passes once this commit lands.
- ✅ Bash suite → all green
- ✅ `python3 scripts/gen-platform-trees.py --check` → pass
- ✅ `bash scripts/eval.sh` → exit 0
- ✅ Test authenticity: pass
- ✅ Review-agent mutation probes, iteration 2: 7 probes, 5 killed. Both iteration-1 survivors are killed. The 2 survivors ("on any verdict" dropped from the table opener; "never `⚠️ DEGRADED`" dropped from the check bullet) are pinned by the orchestrator's two assertions after the re-review.

### Byte count

`wc -c commands/implement-story.md`: before 40759, after 41939, delta +1180. The first Gate 1 version was +1419 (42178); the iteration-1 cuts took it to +1180.

### Review Outcome

**Result:** PASS

- **Iteration count:** 2 iteration(s)
- **Drift:** Medium (DEV-010, logged); DEV-011 Small, auto-amended
- **Security:** Low
- **Boundary Compliance:** Every change outside the Owned list is a file the tasks name, a regenerated tree, or a test pin that follows a deliberate text cut. No unjustified violation.

### Gate record

**REVIEW_RESULT:** FAIL

Iteration 1, `review-agent`, saved at `.writ/state/gate3-review-story-3-gate-3-wiring-iter1.md`.

- Major: with the switch off, an agent PASS or PAUSE printed `evidence-gate: not run (PASS|PAUSE)`, not `evidence-gate: off`. The report line and row 5 were keyed on `reason: switch_off`, which only an agent FAIL reaches.
- Minor: the save line's "or with `safety_fact` on" clause was unpinned; dropping it passed every test.
- Minor: the agent Read lines did not say to keep FAIL.
- Byte cuts and recommendations 1, 2, 3, 4, and 7 applied in recode 1.

**REVIEW_RESULT:** PASS

Iteration 2, `review-agent`, saved at `.writ/state/gate3-review-story-3-gate-3-wiring.md`. Both iteration-1 mutation survivors killed. Two Minor unpinned phrases, fixed by the orchestrator: "First match wins, on any verdict" in `test_evidence_gate_wiring.py`, and "never `⚠️ DEGRADED`" on the `→ no override` line in `test_implement_story_default_path.py`.

- **Gate 0:** arch-check pass (rederived proceed). `gate0-divergence: skip (usage locked by spec.md § Gate 3 decision and § State Catalog)`. Orchestrator choice: the agent Read condition is an `evidence_gate` input, resolved once per story by `switch --name evidence-gate`.
- **Gate 0.5:** boundary map computed (`.writ/state/boundary-story-3-gate-3-wiring.json`)
- **Gate 1:** coding-agent, test-first. Red at 23 failed, 3 passed, then green. Recode 1 after the Gate 3 FAIL: red at 8 failed, then 30 passed. Two pin assertions added by the orchestrator after the re-review.
- **Gate 2:** no linters. `arch-lint: none — see .writ/docs/architecture-lint.md`. `build-smoke: unverifiable (unsupported_stack)`
- **Gate 2.5:** cross-component. `gate3-route: review-agent (outside_boundary commands/implement-story.md, test pins, generated trees)`
- **Gate 3:** `reviewer-filters: on`. 2 iterations: FAIL, then PASS. `review-override check`: pass. Authenticity: pass. `safety-fact: traced (claimed traced) — the Issues Found **Evidence:** field and the Safety Fact section are parsed apart`. `review-panel: skipped — platform cannot spawn other vendors`. Jev shadow: pass, criteria=3 agree=3 false_pass=0 false_block=0.
- **Gate 3.5:** Overall Medium. DEV-010 Medium: logged, PASS. DEV-011 Small: spec-lite auto-amended. drift-format: `fail large_drift_without_pause`. This is the known false positive: the only Large signal is Story 1's DEV-001 section, and the checker does not scope the spec-wide log by story. Story 3 had no Large drift, so no PAUSE line was added.
- **Gate 4:** 30/30 targeted on 3.9 and 3.14. Full suite 4271 passed, 2 failed on both interpreters (named above). Bash suite green. `gen-platform-trees.py --check` pass. `eval.sh` exit 0. Coverage unverifiable (no report).
- **Gate 4.5:** `app-verify: unverifiable (no_recipe)`
- **Gate 5:** `docs-check: unverifiable (no public exports in the changed set)`

### Deviations from Spec

- **[DEV-010] Byte budget: Story 4 has about 170 bytes left** — Severity: Medium
  - Spec said: spec.md → Implementation Approach → Byte budget: the net change to `commands/implement-story.md` across Stories 3, 4, and 7 is ≤ 0.
  - Reality: Story 3 is +1180 (40759 → 41939). Story 7's measured panel removals free about 1,500 bytes gross, about 1,350 net after its two removal messages. That leaves Story 4 about 170 bytes. Story 4's minimum additions are about 450 to 500 bytes, so the projected spec total is about +300.
  - Resolution: ⚠️ Medium — logged, PASS. Carried to Stories 4 and 7; if the net is still above 0 at Story 7, the user decides.
  - Spec amendment: None yet. If Stories 4 and 7 cannot reach net ≤ 0, the user decides whether to amend spec.md → Implementation Approach → Byte budget.
- **[DEV-011] Gate 3 passes `--timeout 60`** — Severity: Small
  - Spec said: technical-spec § Gate 3 Wiring's command has no `--timeout`, so the default is 120 s.
  - Reality: `--timeout 60`, so five runs fit the 600 s tool limit. `--repo .` is dropped because `.` is the default.
  - Resolution: Auto-amended spec-lite.md
  - Spec amendment: technical-spec § Gate 3 Wiring: drop `--repo .` from the command and add `--timeout 60`. Add "`--repo` defaults to `.`; Gate 3 passes `--timeout 60` so five runs fit a 600 s tool call."

### Notes for Downstream Stories

- **Story 4: byte budget.** About 170 bytes of headroom. Apply the reviewer's binding cuts:
  - Bind `<manifest>` once, so `--manifest-out` and `--prior` do not repeat the path (about −45).
  - Bind `<checks>` in the Gate 2 sentence and use it in the command (about −24).
  - Consider making the Gate 3 save unconditional, so the Jev shadow paragraph reuses `<review>` and `<tests>` (about −150). The "targeted run" and "not the full suite" pins in `test_jev_shadow_hooks.sh` move with it.
  - Record the cumulative Story 3 + 4 byte total against Story 7's measured 1,350, so Story 7 knows its target.
- **Story 4: what already exists.** The `fail (<reason>)` re-review form is already in the report line. Row 3a is not in the table.
- **Leftovers, not fixed:**
  - `scripts/eval.sh:4121` still says "Gate 3 is FAIL-only" in a hint about `check`. That is still true of `check`.
  - `test_evaluator_agent_contract.py::test_review_agent_not_in_story_edit_set` should be retired or scoped. Every story that edits `agents/review-agent.md` leaves Gate 4 red until commit. Out of scope here.
  - `scripts/review-panel.py` `_issue_entries` does not track fences, so an unindented `test` repro with a column-0 `# comment` cuts its Issues Found scan short. Story 7 removes the panel; the trial harness keeps the parser.
