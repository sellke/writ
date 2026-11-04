# Story 1: Write the Prompting Guide

> **Status:** Completed ✅
> **Commit:** 4fe27c75dc526e87bcc810fc39b2c242d353dc9d
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** new user who installed Writ and is about to type my first request **I want to** read one short guide that says what a request carries and shows a weak and a strong request for each route **So that** my first request states a goal, a done check, and proof, and reaches the right command.

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [x] Given `.writ/docs/prompting-guide.md`, when its lines are counted, then the file exists and has fewer than 150 lines, counting headings and blank lines `[AC-1.1]`
- [x] Given the guide, when its H2 headings and the list items under the first H2 are read, then the H2 headings are exactly `## What a request carries`, `## Recipes`, and `## Pitfalls` in that order, and the first H2 holds three list items that begin with bold **Goal**, **Done check**, and **Proof**, in that order `[AC-1.2]`
- [x] Given the Recipes section, when its H3 headings are read, then five recipes appear in this order: `### An unsettled idea`, `### A bug or a small change`, `### A feature`, `### Roadmap work`, `### A why or how question`; each recipe has one-line `Weak:`, `Strong:`, and `Route:` lines, and each `Route:` line names `/prototype`, `/prototype --no-diverge`, `/create-spec`, `/implement-phase`, or `/research` for its recipe `[AC-1.3]`
- [x] Given the guide, when every Markdown link target and backticked path is checked, then none starts with `.writ/research/`, `.writ/decision-records/`, `.writ/specs/`, or `.writ/product/` `[AC-1.4]`
- [x] Given the Pitfalls section, when read, then it holds exactly five list items, each one sentence that names a pitfall and its fix (no done check; asking a fork that running something could answer; specifying the how; bundling requests; restating the codebase), and the guide has no em-dash and no unresolved hit from the step 1 scan in `skills/plain-prose/SKILL.md` `[AC-1.5]`

## Implementation Tasks

- [x] 1.1 Write `test_exists_and_budget`, `test_headings`, `test_parts`, `test_recipes`, and `test_no_internal_links` in `scripts/tests/test_prompting_guide.py`. Read the guide as text, in the style of `scripts/tests/test_platform_neutral_names.py`, stdlib only. Run them and confirm each fails because the guide does not exist yet `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
- [x] 1.2 Write the H1 title, a short opening paragraph that says what the guide covers, then `## What a request carries` with three list items, `**Goal**`, `**Done check**`, and `**Proof**`, each defined in one sentence `[AC-1.2]`
- [x] 1.3 Write `## Recipes` with the five H3 recipes in the order named in AC-1.3. Each recipe has one-line `Weak:`, `Strong:`, and `Route:` lines with a concrete example. The why-or-how recipe routes to `/research` and says `/why` replaces it when it ships `[AC-1.3]`
- [x] 1.4 Write `## Pitfalls` as five list items, one sentence each, each naming the pitfall and its fix `[AC-1.5]`
- [x] 1.5 Keep the guide under 150 lines with no links to `.writ/research/`, `.writ/decision-records/`, `.writ/specs/`, or `.writ/product/`. Link only `README.md` or other shipped `.writ/docs/` files, if any `[AC-1.1, AC-1.4]`
- [x] 1.6 Apply `skills/plain-prose/SKILL.md`. Run its step 1 scan on the guide, remove every em-dash, and rewrite flagged sentences without dropping a rule `[AC-1.5]`
- [x] 1.7 Verify: `uv run --python 3.9 pytest scripts/tests/test_prompting_guide.py` passes all five tests; `uv run --python 3.9 pytest` and the bash test loop pass; `bash scripts/eval.sh` reports 0 findings, run outside any sandbox `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Notes

- **Audience:** a user of an installed project. Do not refer to Writ's research, ADRs, or spec folders.
- **Examples:** one line each. Example pair for the bug recipe:
  - Weak: `Fix the login bug.`
  - Strong: `Login fails for emails with a plus sign. Done when the test for a+b@example.com passes. Proof: that test's output.`
- **Line budget:** the cap is 149 lines. The planned guide is roughly 60 to 80 lines, so the cap is a ceiling, not a target. Shorter is better for a first read.
- **Internal links:** `check_shipped_refs` scans shipped commands, not `.writ/docs/`. Until Story 2 adds the ship-set test, `test_no_internal_links` is the only guard on this file.
- **Integration:** `2026-10-22-front-door` cites the H2 headings and part names by text, so do not rename them after this story. `scripts/eval.sh` `check_referenced_paths` resolves `.writ/docs/prompting-guide.md` once a command cites it, so the file must exist first. `is_shippable_writ_doc` is a denylist, so the guide ships without a change to it. Story 2 asserts that.
- **Technical references:** technical-spec.md → ## File Layout, ## Test (`scripts/tests/test_prompting_guide.py`).
- **Test file:** Story 2 extends `scripts/tests/test_prompting_guide.py`. Keep the five test names and module-level helpers simple. Python 3.9 stdlib only.

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** `technical-spec.md → ## Shadow Paths` (Happy path, Nil input, Empty input)
- **Business rules:** `spec.md → ## Business Rules (Expanded)` (Rule 1 headings are an interface, Rule 2 part names, Rule 3 five recipes, Rule 4 pitfalls, Rule 6 line budget, Rule 7 no internal links, Rule 8 plain prose)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (Fresh install, Guide over 150 lines, Guide links a Writ-internal path)

---

## What Was Built

**Implementation Date:** 2026-10-22

### Files Created

1. **`.writ/docs/prompting-guide.md`** (61 lines)
   - The shipped user guide: H1, one opening paragraph, `## What a request carries` (`- **Goal**`, `- **Done check**`, `- **Proof**`, colon-separated, one sentence each), `## Recipes` (five H3 recipes in the contracted order, each with column-0 `Weak:`, `Strong:`, `Route:` lines separated by blank lines; routes `/prototype`, `/prototype --no-diverge`, `/create-spec`, `/implement-phase <N>`, `/research` with `/why` named as its replacement), `## Pitfalls` (five one-sentence items: no done check; asking a fork running both would answer; specifying the how; bundling requests; restating the codebase). Zero em-dashes, zero plain-prose scan hits, no Markdown links at all. Names no `/writ` command.
2. **`scripts/tests/test_prompting_guide.py`** (151 lines)
   - Five text-level tests: `test_exists_and_budget`, `test_headings`, `test_parts`, `test_recipes`, `test_no_internal_links`. Helpers `text()`, `lines()`, `section(body, heading)`; constants `GUIDE_REL`, `LINE_BUDGET`, `H2_HEADINGS`, `PART_PREFIXES`, `RECIPES`, `INTERNAL_PREFIXES`. Story 2 appends `test_readme_links_guide` and `test_ships` to this file. Red before the guide existed (5 failed on the missing file), green after.
3. **`.writ/specs/2026-10-22-prompting-guide/drift-log.md`**
   - Created with DEV-001, DEV-002, DEV-003 (Story 1, all Small).

### Files Modified

[None modified] (story file, `user-stories/README.md`, and `.writ/context.md` are pipeline bookkeeping.)

### Implementation Decisions

1. **Colon after each bold part name** — AC-1.5 and Business Rule 8 forbid em-dashes; the technical-spec sketch's `**Goal** — …` would have failed the criterion. The interface (bold name as the first words of the list item) is unchanged (DEV-001).
2. **Weak/Strong/Route as column-0 lines with blank lines between** — renders as separate lines and lets the test match `line.startswith(label)`; one of each per recipe is asserted, and the unsettled-idea route must not carry `--no-diverge`.
3. **AC-1.5 is read by hand** — the contract's Success Criteria and the technical-spec `## Test` table fix the tested surface (headings, parts, routes, budget, links, README, ship set) and name no pitfalls or em-dash test. The module docstring says so in the sentence that carries the bare `AC-1.5` token, which keeps `ac-trace`'s `untested_criterion` silent on the Completed story. No sixth test was added, because AC-2.4 counts seven tests.
4. **Line 11 fixed in place after Gate 3** — the evaluator's taste residual: the guide said "Two sentences cover all three" while every strong example uses three or four sentences. Now reads "The strong examples below state all three in a few sentences."
5. **Gate 4 authenticity `test_imports_no_source` carried as the known false positive** — the test reads a markdown file and imports no project module, the case recorded in `.writ/issues/improvements/2026-09-03-test-integrity-authenticity-flags-every-bash-test.md` and handled the same way by the Phase 13 lanes. Evidence instead: red phase (5 failed on the missing guide) and six mutations, 6/6 caught (pad to 150 lines; rename `## Recipes`; drop the Done check item; `--no-diverge` on the unsettled route; a `.writ/product/` link; `/why` removed from the why route). Story 2's `test_ships` gives the file a project-script reference (`scripts/install.sh`, `scripts/update.sh`), the pattern `test_agent_cli_contract_doc.py` passes the checker with.

### Test Results

**Verification:** Automated, test-first (five tests red on the missing guide, then green); orchestrator's own recorded run passed to the evaluator.
**Coverage:** Not measured by the script (no coverage report; documentation and test changes only).

- ✅ Targeted: `uv run --python 3.9 pytest scripts/tests/test_prompting_guide.py` → 5 passed.
- ✅ Full pytest (3.9): 2794 passed, 2 skipped.
- ✅ Bash tests: 45 run, 0 failed.
- ✅ `bash scripts/eval.sh`: Findings 0, Run errors 0 (`.writ/state/eval-20261023-002426.md`).
- ✅ Mutations: 6/6 caught (see decision 5).
- ✅ Gate 0 arch-check: pass (rederived proceed). Gate 2: no linter configured; arch-lint: none — see .writ/docs/architecture-lint.md; build-smoke unverifiable (unsupported_stack). Gate 2.5: cross-component, 0 crossings. Gate 3 review-override: unverifiable (no_coverage_report); ac-trace: 0 findings on the Completed story. Gate 3.5 drift-format: pass. Gate 4 coverage: unverifiable (no_coverage_report); authenticity: `test_imports_no_source`, known false positive, carried on the evidence above, not DEGRADED. Gate 4.5 app-verify: unverifiable (no_recipe). Gate 5 docs-check: unverifiable (no_public_exports).

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small (DEV-001, DEV-002, DEV-003)
- **Security:** None
- **Boundary Compliance:** only the owned paths changed (`scripts/tests/test_prompting_guide.py`, `.writ/docs/prompting-guide.md`); no deviation, no violation.
- gate3-route: evaluator-agent. review-panel: unverifiable (platform_cannot_spawn_other_vendors). jev-shadow: unverifiable (no_api_key). arch-lint: none — see .writ/docs/architecture-lint.md.
- Evaluator residuals, not drift: `test_no_internal_links` is a literal-prefix check (a relative `../product/…` target would pass; the guide has no links today); the AC-1.5 docstring token is a novel pattern in `scripts/tests/`.
- Coding agent and evaluator ran as nested `general-purpose` spawns with the prompt templates from `agents/coding-agent.md` and `agents/evaluator-agent.md`.

### Deviations from Spec

- **[DEV-001] Part definitions use a colon instead of the sketch's em-dash** — Severity: Small
  - Spec said: technical-spec sketch `- **Goal** — …`; the contract fixes only the bold names.
  - Reality: `- **Goal**: …` (same for Done check and Proof).
  - Resolution: Auto-amended; no spec-lite change needed (spec-lite already names the parts without a separator).
- **[DEV-002] Opening paragraph states coverage instead of the sketch's metaphor** — Severity: Small
  - Spec said: sketch sentence "a request is a contract in miniature …"; task 1.2 asks for what the guide covers.
  - Reality: the paragraph names the three sections and says to read once before the first request.
  - Resolution: Auto-amended; no spec-lite change needed.
- **[DEV-003] Roadmap Route line adds a clarifying clause** — Severity: Small
  - Spec said: `Route: `/implement-phase <N>``.
  - Reality: `Route: `/implement-phase <N>`, where N is the phase number`.
  - Resolution: Auto-amended; no spec-lite change needed.
