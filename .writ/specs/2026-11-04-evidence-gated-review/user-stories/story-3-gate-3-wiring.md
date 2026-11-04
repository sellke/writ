# Story 3: Gate 3 wiring for evidence-gated findings

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 2

## User Story

**As a** developer running `/implement-story`
**I want to** block an agent FAIL only on executed evidence, and see one `evidence-gate:` line for each Gate 3 outcome
**So that** unbacked findings stop blocking stories, and a confirmed finding reaches the coder with its repro

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [ ] Given an agent FAIL with `check` and `safety-fact` results in hand, when Gate 3 applies its decision, then the first matching row of spec.md → ## Business Rules (Expanded) → ### Gate 3 decision sets the result, and `evidence` runs on every agent FAIL. This story adds no `evidence` run on PASS or PAUSE; row 3a's `--prior` run on those verdicts is Story 4's. `[AC-3.1]`
- [ ] Given Gate 3 has reached any state in spec.md → ## Experience Design → ### State Catalog, when the story report prints, then it contains exactly one `evidence-gate:` line that matches that state's row. `[AC-3.2]`
- [ ] Given a Gate 2 run and an agent FAIL, when Gate 3 saves its inputs, then `.writ/state/gate2-checks-<story-stem>.txt` lists the lint and typecheck commands one per line, and the review output and recorded test results are saved to `gate3-review-<story-stem>.md` and `gate3-tests-<story-stem>.txt` whether or not `safety-fact` is on. `[AC-3.3]`
- [ ] Given the `evaluator-agent` and `review-agent` source files, when the wiring is complete, then each has one conditional `Read skills/evidence-gated-findings/SKILL.md` line, one `**Evidence:**` field after `**Category:**` in its Issues Found format, Critical and Major severity text that blocks only with evidence, and unchanged `reviewer_filters` lines. `[AC-3.4]`
- [ ] Given a saved evaluator FAIL whose Critical and Major findings carry no `Evidence:` block, when the replay runs `evidence` and applies the Gate 3 decision, then Gate 3 returns PASS and lists each finding as advisory. Given the same FAIL with one confirmed `test` repro, Gate 3 returns FAIL and names the confirmed finding. `[AC-3.5]`

## Implementation Tasks

- [ ] 3.1 Write `scripts/tests/test_evidence_gate_wiring.py` first. Wiring assertions: the Gate 3 block orders `check`, then `safety-fact`, then `evidence`; the nine decision rows and the State Catalog report lines are present; the Gate 2 save line exists; both agent files carry the Read line, the `**Evidence:**` field, and the severity text. Replay: feed two saved evaluator FAIL outputs through `evidence`, one with no Evidence blocks and one with one confirmed `test` repro. Run it in a temporary `git init` copy of a fixture project under `scripts/tests/fixtures/review-override/evidence/`, with `Test Runner` set in its `.writ/config.md`. Before any edit, record `wc -c commands/implement-story.md`. Confirm the wiring assertions fail on the current tree. `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`
- [ ] 3.2 In `#### Gate 2`, after the linters, save the lint and typecheck commands that ran to `.writ/state/gate2-checks-<story-stem>.txt`, one per line. In `#### Gate 3`, on every agent FAIL, save the agent output to `.writ/state/gate3-review-<story-stem>.md` and `recorded_test_results` to `.writ/state/gate3-tests-<story-stem>.txt`, whether or not `safety-fact` is on. `[AC-3.3]`
- [ ] 3.3 In `#### Gate 3`, after `check` and `safety-fact`, run `review-override.py evidence` on every agent FAIL, with the arguments in technical-spec.md → ## Gate 3 Wiring. Pass `--changed` as the list Gate 2.5 classified. Omit `--prior` and `--manifest-out`; Story 4 adds them. Apply all nine rows of the Gate 3 decision in order. Print one `evidence-gate:` line for each State Catalog row. Map `reason: switch_off` to `evidence-gate: off`, and line 1 `fail` with `repro_mutated_tree` to `blocked (...)`. Print downgraded findings under `evidence-gate advisory:`. An `unverifiable` result never sets `⚠️ DEGRADED`. Do not edit the reviewer-filters or panel paragraphs. `[AC-3.1, AC-3.2]`
- [ ] 3.4 In `agents/evaluator-agent.md` and `agents/review-agent.md`, add an `evidence_gate` input row. Add one conditional `Read skills/evidence-gated-findings/SKILL.md` line: after the `reviewer_filters` Read line in the evaluator, and after the safety-fact Read line in the review agent. Add `**Evidence:**` after `**Category:**` in the Issues Found format (technical-spec.md → ## Evidence Block Grammar). Rewrite the Critical and Major rows of Severity Definitions so they block only when the issue carries an Evidence block. Align the "When to FAIL" bullets that name Critical or Major with that text. Keep every `reviewer_filters` row and line. `[AC-3.4]`
- [ ] 3.5 Run `python3 scripts/gen-platform-trees.py` and include the regenerated trees in the same change as the sources. Run `scripts/tests/test_evidence_gate_wiring.py` green on Python 3.9 (`uv run --isolated --python 3.9 --with pytest pytest scripts/tests/test_evidence_gate_wiring.py`), then on 3.14. `[AC-3.4, AC-3.5]`
- [ ] 3.6 Verify each AC against the diff and the test output. Run the full pytest suite on 3.9 and 3.14, one at a time, with nothing else writing to the checkout. Run the bash suite in the background. Run `python3 scripts/gen-platform-trees.py --check` and `bash scripts/eval.sh`. Record `wc -c commands/implement-story.md` after the edits, and the before and after counts with the delta, in What Was Built. `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`

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

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Read the review output, Resolve the runner, Run the repro] — from technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [Happy, Nil, Empty, Upstream error] — from technical-spec.md → ## Shadow Paths
- **Business rules:** [Gate 3 decision (nine rows, first match wins), Switch (Evidence Gate off restores agent blocking)] — from spec.md → ## Business Rules (Expanded) → ### Gate 3 decision and ### Switch
- **Experience:** [State Catalog (one evidence-gate line per state), Interaction patterns (advisory lines for downgraded findings)] — from spec.md → ## Experience Design → ### State Catalog and ### Interaction patterns
