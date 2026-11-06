# Story 2: Lean task rules in the story generator and Step 2.6a

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** spec author running `/create-spec`, and the coding agent that later reads the stories
**I want to** get stories whose tasks name files and external contracts, stay under 50 words each, and fail generation when they do not
**So that** stories read in less space, a mechanical check catches long tasks, and the coding agent decides internal structure

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.4

- [ ] Given the updated `agents/user-story-generator.md` task rules, when a story is generated, then each task names every file it creates or changes and any external contract it fixes, and no task prescribes internal function names, signatures, or step order `[AC-2.1]`
- [ ] Given the updated task rules, when they are read, then they cap each task at 50 words, excluding the task number and AC tag, and direct gotchas and constraints to Notes `[AC-2.2]`
- [ ] Given a generated story with a task over 50 words, when Step 2.6a runs, then the story counts as failing and is regenerated once at `anchor`, and a second failure lists its over-long task numbers and word counts in Step 2.9 `[AC-2.3]`
- [ ] Given the changes are complete, when `python3 scripts/gen-platform-trees.py --check` runs, then it reports `pass`, and the byte change to `commands/create-spec.md` is zero or recorded in `KNOWN_OVER_BUDGET` `[AC-2.4]`

## Implementation Tasks

- [ ] 2.1 Write tests in `scripts/tests/test_harness_cuts.py` that pin the new generator task rules and the Step 2.6a `oversized_task` clause. Run them and confirm they fail before the edits `[AC-2.2, AC-2.3]`
- [ ] 2.2 Edit the Implementation Tasks rules and quality guideline in `agents/user-story-generator.md`: name files and external contracts only, a 50-word cap, gotchas in Notes. Cite Business Rules 1, 2, 3, and 6 by number `[AC-2.1, AC-2.2]`
- [ ] 2.3 Edit Step 2.6a item 2 in `commands/create-spec.md` so any `oversized_task` finding fails its story. Item 3 regenerates once at `anchor`. Step 2.9 lists a second failure's task numbers and word counts `[AC-2.3]`
- [ ] 2.4 Regenerate the platform copies with `python3 scripts/gen-platform-trees.py`, which rewrites `claude-code/agents/writ-story-gen.md` and the `cursor/plugin/` copies `[AC-2.4]`
- [ ] 2.5 Keep `commands/create-spec.md` net-zero in bytes, or record its new overage in `KNOWN_OVER_BUDGET` in `scripts/tests/test_governor_enforcement.py` with a dated comment `[AC-2.4]`
- [ ] 2.6 Verify: run `uv run --isolated --python 3.9 --with pytest pytest`, then the 3.14 variant, each alone. Then run `bash scripts/eval.sh` and `python3 scripts/gen-platform-trees.py --check` `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`

## Notes

- **Depends on Story 1.** `ac-trace.py check` must emit `oversized_task` before Step 2.6a can use it. This story cites that finding and does not implement it. Count words the way `technical-spec.md` → `## oversized_task finding` specifies.
- **Byte budget.** `commands/create-spec.md` is already over its command budget. `scripts/tests/test_governor_enforcement.py` fails if the overage grows past the recorded value, and it pins that entry to the exact overage. Target net-zero bytes.
- **Generated trees.** `claude-code/agents/writ-story-gen.md` and `cursor/plugin/**` come from `scripts/gen-platform-trees.py`. Do not hand-edit them.
- **Run pytest alone.** `eval.sh` and the bash tests write under `.writ/state/`. Running them in the same checkout as pytest breaks `test_smoke_leaves_repo_unchanged` and the `app-verify` tests.
- **Python 3.9 floor.** Test code must run on Python 3.9 (`pyproject.toml`). Do not rely on 3.10+ stdlib behavior.
- **Keep the Definition of Done** in the generator template for this story. Story 3 removes it.
- **Step 2.6a item 3 is unchanged in shape.** One regeneration at `anchor`, no loop. A passing story is never regenerated.
- **Step 2.9 is outside the spec's Scope Boundaries list.** The Step 2.6a change needs its second-failure line, so this story edits it.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Step 2.6a regenerate] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [Happy: all tasks ≤50 words] — technical-spec.md → ## Shadow Paths
- **Business rules:** [Business Rule 1, Business Rule 2, Business Rule 3, Business Rule 6] — spec.md → ## Specification Contract → Business Rules
- **Experience:** [State "A task over 50 words, first attempt", State "A task over 50 words after retry"] — spec.md → ## 🎯 Experience Design → ### State Catalog
- **Technical:** technical-spec.md → ## Step 2.6a change; spec.md → ## Detailed Requirements
