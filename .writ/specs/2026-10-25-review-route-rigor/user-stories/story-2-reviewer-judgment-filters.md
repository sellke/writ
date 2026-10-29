# Story 2: Reviewer lead-judgment filters

> **Status:** Completed ✅ (2026-10-29)
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Gate 3 reviewer (`review-agent`, `evaluator-agent`, or `/review`)
**I want to** apply three lead-judgment filters before I set a verdict
**So that** nits and untraced hypotheticals do not drive a FAIL, security findings are not dismissed without a cited guard, and the maintainer can run the removal trial against an off arm that carries none of the filter text.

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [x] Given `skills/review-judgment-filters/SKILL.md` exists, when it is read, then it states the three filters (all nits means the code is fine; trace the call site before accepting a hypothetical; be slow to dismiss security findings), applies filter 3 before filter 2, and `bash scripts/lint-skill.sh skills/review-judgment-filters/SKILL.md` exits 0 `[AC-2.1]`
- [x] Given `.writ/config.md` has no `Reviewer Filters` line or `- **Reviewer Filters:** on`, when Gate 3 spawns `review-agent` or `evaluator-agent`, then the spawn receives `reviewer_filters: on`, and each agent body instructs it to read the skill before it sets the verdict `[AC-2.2]`
- [x] Given `- **Reviewer Filters:** off` in `.writ/config.md`, when Gate 3 runs, then no reviewer reads the filters skill, the spawn receives `reviewer_filters: off`, and the story report prints `reviewer-filters: off` `[AC-2.3]`
- [x] Given `/review` runs on a branch, when Step 3 resolves the `reviewer-filters` switch, then the report header records `> Reviewer filters: on` or `> Reviewer filters: off`, and with `on` the reviewer reads the skill before it assigns severities `[AC-2.4]`
- [x] Given the change is in the tree, when the pytest suite runs, then the distinctive filter sentences appear in `skills/review-judgment-filters/SKILL.md` and in none of `agents/*.md`, `commands/*.md`, or `claude-code/agents/*.md`, and `python3 scripts/gen-platform-trees.py --check` passes `[AC-2.5]`

## Implementation Tasks

- [x] 2.1 Write tests first in `scripts/tests/test_review_route_rigor.py`: skill exists and lints, manifest entry exists, filter sentences absent from every agent, command, and generated tree, `reviewer_filters` rows and conditional `Read` lines in both agents, switch and header lines in `commands/review.md`, switch and story-report lines in Gate 3. Tests fail before the rest of the story lands `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
- [x] 2.2 Create `skills/review-judgment-filters/SKILL.md` (`disable-model-invocation: true`, `status: candidate`, `status_evidence` naming its three consumers, description that passes `lint-skill.sh`). Body: Purpose, When to Use, How to Apply with the three filters, one example each. Apply filter 3 before filter 2 so a security finding is never dropped by the hypothetical rule (technical-spec § Filters Skill). Append the `review-judgment-filters` entry to `.writ/manifest.yaml` `skills:` (append only), add its row to the README `## Skills` table and update the live-skill count, and regenerate the root `SKILL.md` with `bash scripts/gen-skill.sh` `[AC-2.1]`
- [x] 2.3 Edit `agents/review-agent.md` and `agents/evaluator-agent.md`: add a `reviewer_filters` (`on`/`off`) input row to each, and one conditional line: when `{reviewer_filters}` is `on`, read `skills/review-judgment-filters/SKILL.md` and apply it before setting the verdict. No filter text in either body `[AC-2.2]`
- [x] 2.4 Edit `commands/review.md` Step 3: run `python3 scripts/review-override.py switch --name reviewer-filters`; on `on`, read the skill and apply it before severities are assigned and before the recommendation. Add `> Reviewer filters: on|off` to the Step 4 report header. No filter text in the command `[AC-2.4]`
- [x] 2.5 Edit `#### Gate 3` in `commands/implement-story.md` only: resolve the switch, pass `reviewer_filters` to every Gate 3 spawn (panel reviewers included), and print `reviewer-filters: <on|off>` in the story report. Run `wc -c commands/implement-story.md` before and after; Gate 2.5 and Gate 3 combined grow by at most 1,800 bytes net `[AC-2.2, AC-2.3]`
- [x] 2.6 Run `python3 scripts/gen-platform-trees.py` and commit the regenerated trees with the edits. Do not hand-edit `claude-code/agents/` `[AC-2.2, AC-2.5]`
- [x] 2.7 Verify acceptance criteria and tests: `uv run --python 3.9 pytest`, the bash test loop (`for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`), `python3 scripts/gen-platform-trees.py --check`, and `bash scripts/eval.sh` `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`

## Notes

- Panel reviewers get "the same prompt and inputs" (Gate 3), so they receive `reviewer_filters` and read the skill too. The verifier runs only on the primary reviewer's output; this story adds no verifier.
- `/review` mapping: "nit" maps to Low, "Major or above" maps to High or above. This mapping lives in the skill, not in `commands/review.md`.
- Edit only the owned sections. Do not touch Gate 0, `commands/why.md`, `commands/writ.md`, `commands/prototype.md`, `skills/design-divergence/`, `skills/tdd-cycle/`, `agents/coding-agent.md`, `commands/retro.md`, or `commands/refresh-command.md`. In `commands/implement-story.md`, Step 4 (item 8 report-line list) stays unchanged; the Gate 3 text states the new line. The Step 4 header edit in `commands/review.md` is in scope.
- `.writ/manifest.yaml` is shared with the design-divergence spec. Append only.
- Byte budget: `commands/implement-story.md` is 36,226 bytes, over the 24,960-byte per-invocation budget. Gate 2.5 and Gate 3 may grow by 1,800 bytes net across the whole spec. Put the how in the skill; keep the gate text to the when and the routing.
- Removal trial: the off arm must contain no filter text. Filter text in any agent body or command breaks this. The pytest in task 2.1 enforces it.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** [Filter 1 (all nits means the code is fine; nits go under recommendations), Filter 2 (trace the call site before accepting a hypothetical; the finding stands only when the reviewer cites a caller `path:line` that can produce the input), Filter 3 (overrides filter 2 for security; dismissed only by a cited guard)] — from spec.md → Business Rules (Expanded) → Filters
- **Experience:** [reviewer-filters off row (report line `reviewer-filters: off`; no reviewer reads the skill)] — from spec.md → Experience Design → State Catalog
- Agent and command edit scope, skill body, and removal steps — from technical-spec.md → Agent and Command Changes, Filters Skill, Clean Removal

## What Was Built

**Implementation Date:** 2026-10-29

### Files Created

- **`skills/review-judgment-filters/SKILL.md`** — `status: candidate`, `disable-model-invocation: true`, three consumers in `status_evidence`. How to Apply checks each finding security first (filter 3), then nits (filter 1), then hypotheticals (filter 2), and states that filter 3 is applied before filter 2; one example per filter; `/review` severity mapping (nit = Low, Major or above = High or above; a moved finding stays in the registry as Low); evaluator lists moved findings under Residual as taste.
- **`scripts/tests/test_review_route_rigor.py`** — 29 tests (skill frontmatter, lint, body, registration, agent wiring, Gate 3 wiring, `/review` wiring, filter-text isolation).
- Generated skill copies: `plugins/writ/skills/review-judgment-filters/SKILL.md`, `cursor/plugin/skills/review-judgment-filters/SKILL.md`.

### Files Modified

- **`agents/review-agent.md`**, **`agents/evaluator-agent.md`** — `reviewer_filters` input row; one conditional line above `## Output Format`: "When `{reviewer_filters}` is `on`, `Read skills/review-judgment-filters/SKILL.md` and apply it before you set REVIEW_RESULT." (EVALUATION_RESULT for the evaluator). No filter text.
- **`commands/review.md`** — Step 3 opens with the switch and the conditional Read (before Technique 4 severities and the Recommendation); Step 4 header gains `> Reviewer filters: on|off`.
- **`commands/implement-story.md`** (`#### Gate 3` only) — "Reviewer filters." paragraph: resolve once per story, pass line 1 as `reviewer_filters` to every Gate 3 spawn (evaluator or review-agent, panel reviewers, re-reviews), print `reviewer-filters: <on|off>`. File 38,434 → 38,729 bytes (+295).
- **`scripts/tests/test_governor_enforcement.py`** — `KNOWN_OVER_BUDGET["commands/implement-story.md"]` 13474 → 13769, dated (DEV-004).
- **`.writ/manifest.yaml`** — `review-judgment-filters` entry (DEV-007). **`README.md`** — Skills row; live count 16 → 18 (DEV-006). **`SKILL.md`** — regenerated by `gen-skill.sh`.
- **`.writ/docs/agent-cli-contract.md`** — `review-override.py` Callers cell gains `commands/review.md` (DEV-005).
- Regenerated: `claude-code/agents/writ-reviewer.md`, `writ-evaluator.md`; `codex/agents/review-agent.toml`, `evaluator-agent.toml`, `codex/AGENTS.md.template`; `cursor/plugin/` and `plugins/writ/` agent and command copies.

### Implementation Decisions

1. **Gate 0 divergence chose sketch A** — the orchestrator resolves the switch once and passes it as an input; sketch B (each reviewer runs the switch itself) dropped the spawn input AC-2.2/2.3 require.
2. **Per-finding application, security first** — the skill checks filter 3 before filter 1 and filter 2, so no security finding is dropped as a nit or a hypothetical.
3. **Post-review wording** — after Gate 3 PASS, two sentences were added to the skill's `/review` mapping (Gate 3 recommendations 1 and 2): a moved finding stays in the `/review` registry as Low, and the evaluator lists moved findings under Residual as taste. Lint, the 29 story tests, and `gen-platform-trees.py --check` re-run green.

### Test Results

**Verification:** `uv run --python 3.9 pytest scripts/tests/test_review_route_rigor.py -q` → 29 passed; targeted run of 7 files → 403 passed, 1 failed (`test_review_agent_not_in_story_edit_set`, which fails only while `agents/review-agent.md` is uncommitted); coding agent's full 3.9 suite → 3321 passed, 1 failed (same), 3 skipped; bash tests 0 FAIL; `bash scripts/eval.sh` → 0 findings; `gen-platform-trees.py --check` → pass; `lint-skill.sh` → pass.
- ✅ test-integrity authenticity: pass
- coverage: unverifiable (no_coverage_report) — markdown skill and unittest file

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small
- **Security:** Clean
- **Boundary Compliance:** eight owned files; README, root SKILL.md, generated trees, governor pin, and contract Callers cell justified
- **gate3-route:** review-agent (outside_boundary for agent-cli-contract.md, README.md, SKILL.md, test_governor_enforcement.py, and 15 generated copies)
- **reviewer-filters:** on
- **gate0-divergence:** chose A (orchestrator-resolved input × per-finding application) — B dropped the Gate 3 spawn input AC-2.2/2.3 require
- **review-panel:** skipped — platform cannot spawn other vendors
- **review-override check:** pass (no blocking helper finding)
- **jev shadow:** pass (judged) criteria=5 agree=0 false_block=5 — advisory only

### Deviations from Spec

- **[DEV-004] Governor budget pin raised for the Gate 3 paragraph** — Severity: Small — Resolution: Auto-amended
- **[DEV-005] Agent CLI contract Callers cell names `commands/review.md`** — Severity: Small — Resolution: Auto-amended
- **[DEV-006] README live-skill count corrected from a stale value** — Severity: Small — Resolution: Auto-amended
- **[DEV-007] Manifest entry inserted in alphabetical position** — Severity: Small — Resolution: Auto-amended
