# Story 3: The Front Door Routes Why Questions to `/why`

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** Story 2

## User Story

**As a** user who types `/writ "why is X like this?"`
**I want to** be routed to `/why`, and to `/research` only when the question is about something outside the project
**So that** project questions are answered from the project's own ledger, and the interim "when it ships" notes are gone

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.4

- [x] Given `commands/writ.md` § Routing Rules, when its table is read, then it still has six data rows, and the fifth row's Signal cell reads "Asks why something in this project is the way it is, or how it works" and its Route cell contains `/why` and names `/research` for a question about something outside the project `[AC-3.1]`
- [x] Given `commands/writ.md` § Step 2, when its "Why or how" bullet is read, then it routes `/why` and names `/research` for a question about a library, a standard, or a vendor, and the file no longer contains the text `when it ships` `[AC-3.2]`
- [x] Given `.writ/docs/prompting-guide.md` § A why or how question, when its `Route:` line is read, then it names `/why` first and `/research` for questions outside the project, and the guide no longer contains `when it ships` `[AC-3.3]`
- [x] Given the updated tests and regenerated trees, when `uv run --python 3.9 pytest`, `python3 scripts/gen-platform-trees.py --check`, and `bash scripts/eval.sh` run, then `scripts/tests/test_front_door.py` and `scripts/tests/test_prompting_guide.py` pass with `/why` as the fifth route, `--check` prints `pass`, and eval reports 0 findings `[AC-3.4]`

## Implementation Tasks

- [x] 3.1 Write the failing tests first. In `scripts/tests/test_front_door.py` set `ROUTES[4]` to `("/why", None)`, change the row-5 assertion to check `/research`, and add `test_why_route` per technical-spec.md → Tests. In `scripts/tests/test_prompting_guide.py` set the why-or-how recipe to `/why`, change its special-case assertion to `/research`, and assert the guide no longer contains `when it ships`. Run them and confirm they fail on the old route `[AC-3.1, AC-3.2, AC-3.3]`
- [x] 3.2 Grep `scripts/` for a fragment of each sentence you will change in `commands/writ.md` and the guide. Update any other pin in the same change `[AC-3.1, AC-3.2, AC-3.3]`
- [x] 3.3 Replace the fifth row of `commands/writ.md` § Routing Rules and its § Step 2 "Why or how" bullet with the text in technical-spec.md → `/writ` Route. Change no other row or step `[AC-3.1, AC-3.2]`
- [x] 3.4 Replace the `Route:` line under `.writ/docs/prompting-guide.md` § A why or how question with the text in technical-spec.md → `/writ` Route. Leave the Weak and Strong lines unchanged `[AC-3.3]`
- [x] 3.5 Regenerate the plugin trees with `python3 scripts/gen-platform-trees.py` and confirm `--check` prints `pass` `[AC-3.4]`
- [x] 3.6 Verify. Run `uv run --python 3.9 pytest` alone, then the bash test loop, then `bash scripts/eval.sh` outside any sandbox. Confirm 0 failures and 0 findings, and that `git diff --stat` shows edits only to the files this story names plus the regenerated trees `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`

## Notes

- **Six rows.** `scripts/tests/test_front_door.py` pins the row count and the row order. The `/research` route moves into the fifth row's cell; no row is added.
- **Mirroring needs no change.** `/writ` Step 4 already collects `### Step N` headings, and `commands/why.md` has six.
- **The completed front-door spec stays as written.** Its routing fixture expected `/research` for question 5, which was correct when it ran. Do not edit `.writ/specs/2026-10-22-front-door/`.
- **Stale count in `commands/writ.md` frontmatter.** `problem:` says "Writ ships 32 commands". It is out of this story's scope; leave it.
- **Parallel with Story 4.** Story 4 edits `commands/create-spec.md` and `scripts/tests/test_why_command.py`. This story touches neither.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** [Happy path]
- **Business rules:** [Front-door route, Generated files are regenerated]
- **Experience:** [Entry Point]

---

## What Was Built

**Implementation Date:** 2026-10-25

### Files Created

[None created]

### Files Modified

- **`commands/writ.md`** (§ Routing Rules fifth row; § Step 2 "Why or how" bullet) — the row and bullet now route `/why` and name `/research` for a question about something outside the project, text copied from technical-spec.md → `/writ` Route. The table keeps six rows; the "when it ships" notes are gone.
- **`.writ/docs/prompting-guide.md`** (§ A why or how question) — `Route: `/why` (`/research` for a question about something outside the project)`. Weak and Strong lines unchanged.
- **`scripts/tests/test_front_door.py`** — `ROUTES[4] = ("/why", None)`; the row-5 assertion checks `/research`; new `test_why_route` (Step 2 routes `/why`, names `/research`, no "when it ships"); docstring updated.
- **`scripts/tests/test_prompting_guide.py`** — the why-or-how recipe expects `/why`; the special case checks `/research`; asserts the guide no longer contains "when it ships".
- **`cursor/plugin/commands/writ.md`, `plugins/writ/commands/writ.md`** — regenerated by `python3 scripts/gen-platform-trees.py`.

### Implementation Decisions

1. **Pins grepped first** — no file under `scripts/` pinned the replaced sentences ("takes this route", "replaces it when", "The confirmation notes"), so only the two test files the story names moved.
2. **Front-door spec left as written** — `.writ/specs/2026-10-22-front-door/` still records `/research` for its routing-fixture question 5, which was correct when it ran.

### Test Results

**Verification:** Automated, test-first (`test_why_route` and `test_recipes` red on the old route; green after the edits).
**Coverage:** Not measured by the script (no coverage report; markdown and test changes only).

- ✅ Targeted: `uv run --python 3.9 pytest -q scripts/tests/test_front_door.py scripts/tests/test_prompting_guide.py` → 21 passed.
- ✅ Full run with Stories 3 and 4 in the tree: `uv run --python 3.9 pytest -q` → 3071 passed, 2 skipped; bash test loop → 0 FAIL; `bash scripts/eval.sh` → Findings 0, Run errors 0 (`.writ/state/eval-20261026-040947.md`).
- ✅ Gate 0 arch-check: pass (rederived proceed). Gate 2: no linter configured; arch-lint: none — see .writ/docs/architecture-lint.md; build-smoke unverifiable (unsupported_stack). Gate 2.5: cross-component, 2 crossings (the two regenerated plugin copies), route review-agent. Gate 3 review-override: pass. Gate 3.5 drift-format: pass. Gate 4 coverage: unverifiable (no_coverage_report); authenticity: pass. Gate 4.5 app-verify: unverifiable (no_recipe). Gate 5 docs-check: unverifiable (no_public_exports).

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** None
- **Security:** Clean (markdown and tests)
- **Boundary Compliance:** 2 crossings, both regenerated plugin copies
- gate3-route: review-agent (outside_boundary cursor/plugin/commands/writ.md; outside_boundary plugins/writ/commands/writ.md). Stories 3 and 4 were reviewed in one review-agent pass.
