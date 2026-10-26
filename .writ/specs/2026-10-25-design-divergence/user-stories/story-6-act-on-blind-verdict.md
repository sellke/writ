# Story 6: Act on the Blind Verdict (Human-Gated)

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 2, Story 3, Story 5

## User Story

**As a** Writ maintainer
**I want to** run `report` on the human-rated trial, commit its output with the trial file, and then keep or remove the divergence skill and its Gate 0 wiring as the verdict decides
**So that** the skill stays only if declared axes beat the naive prompt on the blind ratings, and in both outcomes the repo state, ADR-030, roadmap Phase 15, and spec status agree with a committed record

## Acceptance Criteria

> **AC IDs assigned through:** AC-6.5

- [ ] Given a sheet the human filled and recorded with `rate --rated-by <human name>`, when `python3 scripts/divergence-trial.py report --trial <file>` runs, then its output is committed verbatim as `.writ/specs/2026-10-25-design-divergence/trial-report.md` together with the rated trial file, in a commit that precedes any removal commit, and the trial file's `rated_by` names a person, not an agent `[AC-6.1]`
- [ ] Given a `keep` verdict, when the story closes, then the skill, both `Read skills/design-divergence/SKILL.md` lines, the Gate 0 block, and the `Gate 0 Divergence` switch all remain; ADR-030 § Review records the result (date, wins out of 6, distinct counts, the small-sample caveat, the render-only tally); roadmap Phase 15's "Divergence trial" criterion is marked met with a link to trial-report.md; and spec.md reads `> **Status:** Complete` `[AC-6.2]`
- [ ] Given a `remove` verdict, when the story closes, then `skills/design-divergence/` and its manifest entry, README row, and generated copies are gone; the Gate 0 block, its Pipeline cell, Overview clause, and References entry are gone from commands/implement-story.md; the config-format.md `Gate 0 Divergence` entry is gone; /prototype Step 2.5 reads "Ask for up to three drafts and state what each commits to" and its exit criterion says "what it commits to"; the implement-story.md ratchet is re-pinned downward with a dated disclosure; an improvement issue is filed for create-spec.md Step 0's "declared axes" wording; ADR-030 and roadmap Phase 15 record the removal; `rg -n 'design-divergence|Gate 0 Divergence' commands adapters README.md SKILL.md .writ/manifest.yaml .writ/docs plugins` returns no hits; and spec.md reads `> **Status:** Closed — Not Implemented` `[AC-6.3]`
- [ ] Given an `unverifiable` report, when the story is attempted, then nothing is added or removed, trial-report.md is not committed as a verdict, and spec.md's status names the blocking reason from the report's `reason:` lines `[AC-6.4]`
- [ ] Given either acted-on verdict, when the story closes, then scripts/divergence-trial.py, scripts/tests/test_divergence_trial.py, and scripts/tests/fixtures/divergence-trial/ are deleted after the report commit, `uv run pytest scripts/tests/test_divergence_trial_outcome.py` passes, and `uv run pytest`, `uv run --python 3.9 pytest`, the bash tests, `python3 scripts/gen-platform-trees.py --check`, and `bash scripts/eval.sh` all pass with 0 findings `[AC-6.5]`

## Implementation Tasks

- [ ] 6.1 Confirm the human gate: `rating-sheet.md` is filled, and the trial file has `rated_by` and complete ratings recorded by the human. If not, stop and report that the story is waiting on the rater `[AC-6.1, AC-6.4]`
- [ ] 6.2 Run `report`, write its output verbatim to `trial-report.md`, and commit it with the trial file before touching any wiring `[AC-6.1]`
- [ ] 6.3 On `keep`: add the ADR-030 result note, mark the roadmap "Divergence trial" criterion met, and set spec status to Complete. Use targeted edits only `[AC-6.2]`
- [ ] 6.4 On `remove`: make the deletions and edits listed in AC-6.3, regenerate SKILL.md and the platform trees, re-pin the ratchet, file the issue, record ADR-030 and roadmap, and set the spec status `[AC-6.3]`
- [ ] 6.5 On `unverifiable`: set the spec status to the blocking reason from the report and stop `[AC-6.4]`
- [ ] 6.6 Delete `scripts/divergence-trial.py`, `scripts/tests/test_divergence_trial.py`, and `scripts/tests/fixtures/divergence-trial/`, then confirm `scripts/tests/test_divergence_trial_outcome.py` passes `[AC-6.5]`
- [ ] 6.7 Verify all tests pass: `uv run pytest`, `uv run --python 3.9 pytest`, the bash tests, `python3 scripts/gen-platform-trees.py --check`, and `bash scripts/eval.sh` (outside the sandbox) with 0 findings `[AC-6.5]`

## Notes

- **Dev-only cleanup (D25):** when deleting `scripts/divergence-trial.py`, also remove its entries from the dev-only script lists Story 4 added.

- **Human-gated.** The implementing agent never fills `rating-sheet.md` and never runs `rate`. If `/implement-spec` reaches this story before the rating exists, it must stop at task 6.1 and report. It must not mark the story complete or blocked-and-skipped.
- **Commit order is load-bearing.** The trial file and `trial-report.md` are committed before any removal commit. On `remove`, the harness is deleted only after that record exists.
- **Outcome test independence.** `scripts/tests/test_divergence_trial_outcome.py` does not import the harness, so it survives the deletion in task 6.6.
- **Shared files.** `.writ/product/roadmap.md` and ADR-030 are edited by sibling Phase 15 specs. Use targeted edits only. Do not rewrite whole files.
- **Ratchet.** `2026-10-25-gate-upgrade-removal-measurement` may already have removed the Gate 0 upgrade or toggled the switch. If it has, a `keep` verdict keeps the skill with `/prototype` as its one caller, and the ADR note must say so. Re-pin the ratchet from the value present at execution time and cite it in the disclosure.
- **Small sample.** Six briefs with one rater is a weak sample. The ADR note and the report both carry the caveat. A `keep` must not be cited later as proof of a general result.
- **Blinding is honor-system.** The report states this. The rater opens only the sheet.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Story 6 (report `unverifiable` → spec stays open, status names the reason, nothing removed), `report` (`key_missing`, `key_changed`, `unrated`)] — from technical-spec.md → Error & Rescue Map
- **Shadow paths:** [Trial report (no ratings → `unverifiable`; key missing → `unverifiable`)] — from technical-spec.md → Shadow Paths
- **Business rules:** [Switch and keep rule (rule 11, trial verdict), Human-gated verdict (rule 12), Removal on `remove` (rule 13)] — from spec.md → 📋 Business Rules (Expanded)
- **Experience:** []
- **Technical:** technical-spec.md → ## Verdict Execution (Story 6) (repo state per verdict, commit order, `remove` extras); technical-spec.md → ## Files in Scope (Story 6 rows); spec.md → 💡 Recommendations (delete the harness after the report commit)
