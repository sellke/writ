# Story 1: Write the Prompting Guide

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** new user who installed Writ and is about to type my first request **I want to** read one short guide that says what a request carries and shows a weak and a strong request for each route **So that** my first request states a goal, a done check, and proof, and reaches the right command.

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [ ] Given `.writ/docs/prompting-guide.md`, when its lines are counted, then the file exists and has fewer than 150 lines, counting headings and blank lines `[AC-1.1]`
- [ ] Given the guide, when its H2 headings and the list items under the first H2 are read, then the H2 headings are exactly `## What a request carries`, `## Recipes`, and `## Pitfalls` in that order, and the first H2 holds three list items that begin with bold **Goal**, **Done check**, and **Proof**, in that order `[AC-1.2]`
- [ ] Given the Recipes section, when its H3 headings are read, then five recipes appear in this order: `### An unsettled idea`, `### A bug or a small change`, `### A feature`, `### Roadmap work`, `### A why or how question`; each recipe has one-line `Weak:`, `Strong:`, and `Route:` lines, and each `Route:` line names `/prototype`, `/prototype --no-diverge`, `/create-spec`, `/implement-phase`, or `/research` for its recipe `[AC-1.3]`
- [ ] Given the guide, when every Markdown link target and backticked path is checked, then none starts with `.writ/research/`, `.writ/decision-records/`, `.writ/specs/`, or `.writ/product/` `[AC-1.4]`
- [ ] Given the Pitfalls section, when read, then it holds exactly five list items, each one sentence that names a pitfall and its fix (no done check; asking a fork that running something could answer; specifying the how; bundling requests; restating the codebase), and the guide has no em-dash and no unresolved hit from the step 1 scan in `skills/plain-prose/SKILL.md` `[AC-1.5]`

## Implementation Tasks

- [ ] 1.1 Write `test_exists_and_budget`, `test_headings`, `test_parts`, `test_recipes`, and `test_no_internal_links` in `scripts/tests/test_prompting_guide.py`. Read the guide as text, in the style of `scripts/tests/test_platform_neutral_names.py`, stdlib only. Run them and confirm each fails because the guide does not exist yet `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
- [ ] 1.2 Write the H1 title, a short opening paragraph that says what the guide covers, then `## What a request carries` with three list items, `**Goal**`, `**Done check**`, and `**Proof**`, each defined in one sentence `[AC-1.2]`
- [ ] 1.3 Write `## Recipes` with the five H3 recipes in the order named in AC-1.3. Each recipe has one-line `Weak:`, `Strong:`, and `Route:` lines with a concrete example. The why-or-how recipe routes to `/research` and says `/why` replaces it when it ships `[AC-1.3]`
- [ ] 1.4 Write `## Pitfalls` as five list items, one sentence each, each naming the pitfall and its fix `[AC-1.5]`
- [ ] 1.5 Keep the guide under 150 lines with no links to `.writ/research/`, `.writ/decision-records/`, `.writ/specs/`, or `.writ/product/`. Link only `README.md` or other shipped `.writ/docs/` files, if any `[AC-1.1, AC-1.4]`
- [ ] 1.6 Apply `skills/plain-prose/SKILL.md`. Run its step 1 scan on the guide, remove every em-dash, and rewrite flagged sentences without dropping a rule `[AC-1.5]`
- [ ] 1.7 Verify: `uv run --python 3.9 pytest scripts/tests/test_prompting_guide.py` passes all five tests; `uv run --python 3.9 pytest` and the bash test loop pass; `bash scripts/eval.sh` reports 0 findings, run outside any sandbox `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

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
