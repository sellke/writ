# Story 2: Reviewer lead-judgment filters

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Gate 3 reviewer (`review-agent`, `evaluator-agent`, or `/review`)
**I want to** apply three lead-judgment filters before I set a verdict
**So that** nits and untraced hypotheticals do not drive a FAIL, security findings are not dismissed without a cited guard, and the maintainer can run the removal trial against an off arm that carries none of the filter text.

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [ ] Given `skills/review-judgment-filters/SKILL.md` exists, when it is read, then it states the three filters (all nits means the code is fine; trace the call site before accepting a hypothetical; be slow to dismiss security findings), applies filter 3 before filter 2, and `bash scripts/lint-skill.sh skills/review-judgment-filters/SKILL.md` exits 0 `[AC-2.1]`
- [ ] Given `.writ/config.md` has no `Reviewer Filters` line or `- **Reviewer Filters:** on`, when Gate 3 spawns `review-agent` or `evaluator-agent`, then the spawn receives `reviewer_filters: on`, and each agent body instructs it to read the skill before it sets the verdict `[AC-2.2]`
- [ ] Given `- **Reviewer Filters:** off` in `.writ/config.md`, when Gate 3 runs, then no reviewer reads the filters skill, the spawn receives `reviewer_filters: off`, and the story report prints `reviewer-filters: off` `[AC-2.3]`
- [ ] Given `/review` runs on a branch, when Step 3 resolves the `reviewer-filters` switch, then the report header records `> Reviewer filters: on` or `> Reviewer filters: off`, and with `on` the reviewer reads the skill before it assigns severities `[AC-2.4]`
- [ ] Given the change is in the tree, when the pytest suite runs, then the distinctive filter sentences appear in `skills/review-judgment-filters/SKILL.md` and in none of `agents/*.md`, `commands/*.md`, or `claude-code/agents/*.md`, and `python3 scripts/gen-platform-trees.py --check` passes `[AC-2.5]`

## Implementation Tasks

- [ ] 2.1 Write tests first in `scripts/tests/test_review_route_rigor.py`: skill exists and lints, manifest entry exists, filter sentences absent from every agent, command, and generated tree, `reviewer_filters` rows and conditional `Read` lines in both agents, switch and header lines in `commands/review.md`, switch and story-report lines in Gate 3. Tests fail before the rest of the story lands `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
- [ ] 2.2 Create `skills/review-judgment-filters/SKILL.md` (`disable-model-invocation: true`, `status: candidate`, `status_evidence` naming its three consumers, description that passes `lint-skill.sh`). Body: Purpose, When to Use, How to Apply with the three filters, one example each. Apply filter 3 before filter 2 so a security finding is never dropped by the hypothetical rule (technical-spec § Filters Skill). Append the `review-judgment-filters` entry to `.writ/manifest.yaml` `skills:` (append only), add its row to the README `## Skills` table and update the live-skill count, and regenerate the root `SKILL.md` with `bash scripts/gen-skill.sh` `[AC-2.1]`
- [ ] 2.3 Edit `agents/review-agent.md` and `agents/evaluator-agent.md`: add a `reviewer_filters` (`on`/`off`) input row to each, and one conditional line: when `{reviewer_filters}` is `on`, read `skills/review-judgment-filters/SKILL.md` and apply it before setting the verdict. No filter text in either body `[AC-2.2]`
- [ ] 2.4 Edit `commands/review.md` Step 3: run `python3 scripts/review-override.py switch --name reviewer-filters`; on `on`, read the skill and apply it before severities are assigned and before the recommendation. Add `> Reviewer filters: on|off` to the Step 4 report header. No filter text in the command `[AC-2.4]`
- [ ] 2.5 Edit `#### Gate 3` in `commands/implement-story.md` only: resolve the switch, pass `reviewer_filters` to every Gate 3 spawn (panel reviewers included), and print `reviewer-filters: <on|off>` in the story report. Run `wc -c commands/implement-story.md` before and after; Gate 2.5 and Gate 3 combined grow by at most 1,800 bytes net `[AC-2.2, AC-2.3]`
- [ ] 2.6 Run `python3 scripts/gen-platform-trees.py` and commit the regenerated trees with the edits. Do not hand-edit `claude-code/agents/` `[AC-2.2, AC-2.5]`
- [ ] 2.7 Verify acceptance criteria and tests: `uv run --python 3.9 pytest`, the bash test loop (`for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`), `python3 scripts/gen-platform-trees.py --check`, and `bash scripts/eval.sh` `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`

## Notes

- Panel reviewers get "the same prompt and inputs" (Gate 3), so they receive `reviewer_filters` and read the skill too. The verifier runs only on the primary reviewer's output; this story adds no verifier.
- `/review` mapping: "nit" maps to Low, "Major or above" maps to High or above. This mapping lives in the skill, not in `commands/review.md`.
- Edit only the owned sections. Do not touch Gate 0, `commands/why.md`, `commands/writ.md`, `commands/prototype.md`, `skills/design-divergence/`, `skills/tdd-cycle/`, `agents/coding-agent.md`, `commands/retro.md`, or `commands/refresh-command.md`. In `commands/implement-story.md`, Step 4 (item 8 report-line list) stays unchanged; the Gate 3 text states the new line. The Step 4 header edit in `commands/review.md` is in scope.
- `.writ/manifest.yaml` is shared with the design-divergence spec. Append only.
- Byte budget: `commands/implement-story.md` is 36,226 bytes, over the 24,960-byte per-invocation budget. Gate 2.5 and Gate 3 may grow by 1,800 bytes net across the whole spec. Put the how in the skill; keep the gate text to the when and the routing.
- Removal trial: the off arm must contain no filter text. Filter text in any agent body or command breaks this. The pytest in task 2.1 enforces it.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** [Filter 1 (all nits means the code is fine; nits go under recommendations), Filter 2 (trace the call site before accepting a hypothetical; the finding stands only when the reviewer cites a caller `path:line` that can produce the input), Filter 3 (overrides filter 2 for security; dismissed only by a cited guard)] — from spec.md → Business Rules (Expanded) → Filters
- **Experience:** [reviewer-filters off row (report line `reviewer-filters: off`; no reviewer reads the skill)] — from spec.md → Experience Design → State Catalog
- Agent and command edit scope, skill body, and removal steps — from technical-spec.md → Agent and Command Changes, Filters Skill, Clean Removal
