# Story 6: Remove the reviewer filters and raise the Safety Fact floor

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 4, Story 5

## User Story

**As a** Writ maintainer
**I want to** remove the reviewer judgment filters and raise the Safety Fact floor from `traced` to `tested`
**So that** a Safety Fact claim and a Gate 3 block rest on a test from the recorded run, not on a reviewer's filter

## Acceptance Criteria

> **AC IDs assigned through:** AC-6.5

- [ ] Given `.writ/specs/2026-10-25-gate-upgrade-removal-measurement/spec.md` still lists Safety Fact or Reviewer Filters among the upgrades under test, when Story 6 starts, then the run stops with a blocker that names `/edit-spec` and changes no file. `[AC-6.1]`
- [ ] Given the filter surfaces are removed and the trees are regenerated, when the scan test runs over `commands/`, `agents/`, `skills/`, `adapters/`, `claude-code/`, `cursor/`, `plugins/`, `codex/`, `README.md`, and `SKILL.md`, then it passes, and it fails when a planted `review-judgment-filters` or `reviewer-filters` appears in any of those paths. `[AC-6.2]`
- [ ] Given a Safety Fact section whose highest accepted rung is `traced`, when `review-override.py safety-fact` runs, then its output includes `reason: safety_fact_below_floor traced`. `[AC-6.3]`
- [ ] Given a Safety Fact section whose highest accepted rung is `tested`, when `review-override.py safety-fact` runs, then its output has no `safety_fact_below_floor` reason line and no other reason line changes from before the floor change. `[AC-6.4]`
- [ ] Given the listed tests are updated, when pytest runs on Python 3.9 and 3.14, then no test asserts on the reviewer filters or the `traced` floor, and the trial-record checks in `test_gate_upgrade_trial.py` and `test_gate_upgrade_trial_outcome.py` still run and pass. `[AC-6.5]`

## Implementation Tasks

- [ ] 6.1 Check the precondition. Read `.writ/specs/2026-10-25-gate-upgrade-removal-measurement/spec.md`. If it still lists Safety Fact or Reviewer Filters as upgrades under test, stop and report a blocker that names `/edit-spec`. Otherwise run `wc -c commands/implement-story.md` and record the count as the before value in the story's What Was Built section `[AC-6.1]`
- [ ] 6.2 Write the failing tests first. In `scripts/tests/test_review_route_rigor.py`, add a scan test over the listed paths that skips `.writ/`. Take the root as an argument so a temp fixture can plant a token and prove the failure. In `scripts/tests/test_review_override.py`, add `safety-fact` cases: a `traced`-only section returns `safety_fact_below_floor traced`, and a `tested` section does not. Name the spec in a comment above the cases `[AC-6.2, AC-6.3, AC-6.4]`
- [ ] 6.3 Update the listed tests so none asserts on the reviewer filters or the `traced` floor: `test_review_route_rigor.py`, `test_review_override.py`, `test_repro_first_wiring.py`, `test_governor_enforcement.py`, `test_gate_upgrade_trial.py`, `test_gate_upgrade_trial_outcome.py`. Keep the trial-record checks in the two `test_gate_upgrade_trial*.py` files. `[AC-6.5]`
- [ ] 6.4 Remove the reviewer filters. Delete `skills/review-judgment-filters/`. Remove its entries from `.writ/manifest.yaml`, the `README.md` Skills table, and root `SKILL.md`. Remove the `Reviewer Filters` row and section from `.writ/docs/config-format.md`. Remove the `reviewer-filters` entry from `SWITCH_LINES` and from the usage text in `scripts/review-override.py`. Remove the agents' input row and conditional `Read` line from `agents/evaluator-agent.md` and `agents/review-agent.md`. Remove Gate 3's paragraph and report mention from `commands/implement-story.md`. Remove the Step 3 switch line from `commands/review.md` `[AC-6.2]`
- [ ] 6.5 Set `FLOOR = "tested"` in `scripts/review-override.py`. Update the docstring floor text, including the `Floor:` line and the `floor traced` output example. Apply the three `skills/blast-radius/SKILL.md` changes listed in the technical spec, and change any other `traced` floor wording in that file to `tested` `[AC-6.3, AC-6.4]`
- [ ] 6.6 Regenerate the platform trees with `python3 scripts/gen-platform-trees.py`. Confirm that no `review-judgment-filters` directory remains under `cursor/plugin/skills/` or `plugins/writ/skills/`, and that no filter line remains in the generated copies. Remove any stale directory the generator leaves. Run `wc -c commands/implement-story.md` and record the count as the after value `[AC-6.2]`
- [ ] 6.7 Verify with nothing else running in the checkout. Run `uv run --isolated --python 3.9 --with pytest pytest`, then the same with `--python 3.14`. Run `python3 scripts/gen-platform-trees.py --check` and `bash scripts/eval.sh`. Start the bash suite last, in the background, and wait for its completion notice. `[AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5]`

## Notes

**Codebase facts (verify at implementation)**
- Filter references at authoring: `scripts/review-override.py` (usage line 13, `SWITCH_LINES` at line 85, `FLOOR` at line 276), `skills/review-judgment-filters/`, `skills/blast-radius/SKILL.md`, `commands/implement-story.md`, `commands/review.md`, the two evaluator and review agents, and generated copies under `cursor/`, `plugins/writ/`, `claude-code/agents/`, and `codex/`. Re-grep before editing, since line numbers drift.
- The file-by-file change list is `technical-spec.md` → `### Reviewer Filters (Story 6)`. The precondition and the full list of removals are in `spec.md` → `## Business Rules (Expanded)` → `### Removals`.
- `codex/` ships generated agent TOMLs and `codex/AGENTS.md.template`. Both name the filters today, so the scan covers `codex/`.
- Generated trees are rebuilt, never hand-edited. `gen-platform-trees.py` writes `cursor/`, `plugins/writ/`, `claude-code/agents/`, and `codex/`.
- Python 3.9 floor: stdlib only, no `match` statements.

**Scope limits**
- Do not edit `pruned-instructions-ledger.md`. It covers only `system-instructions.md` and `commands/_preamble.md` (`spec.md` → `### Corrections made at authoring`, item 1).
- Do not edit ADRs, specs, or other `.writ/` history. The scan skips `.writ/`, so history keeps the old names.
- Do not touch the review panel. Story 7 owns it. Story 7 also edits `test_governor_enforcement.py`, so this story runs first.
- Keep the trial-record checks. Remove only the assertions about the filters and the `traced` floor.

**Ordering and gates**
- Task 6.1 is a gate that reads a spec, so it cannot be a test. Tests start at 6.2. The gate runs first so a blocked run changes nothing.
- Story 6 follows Stories 4 and 5 (`spec.md` → `## Implementation Approach` → Story order). It edits Gate 3 of `commands/implement-story.md`, so Story 4's edits must land first.
- `2026-10-25-design-divergence` also edits `commands/implement-story.md`, in Gate 0. Land this story after it, or rebase on it (`spec.md` → `## Specification Contract` → Cross-Spec Overlap).

**Byte budget**
- Baseline at 6.1, after at 6.6. Story 6 removes the Gate 3 filter paragraph. The net change across Stories 3, 4, 6, and 7 must be zero or less (`spec.md` → `## Implementation Approach` → Byte budget; `technical-spec.md` → `## Byte Budget`).

**Assumptions**
- `user_type` was not supplied. "Writ maintainer" is inferred from the spec owner and the repo's purpose.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** [Reviewer Filters removed, Safety Fact floor is `tested`, Safety Fact routing unchanged] — `spec.md` → `## Business Rules (Expanded)` → `### Removals`; `spec.md` → `## Specification Contract` → Business Rules item 4; success criteria in `spec.md` → `## Specification Contract` → Success Criteria
