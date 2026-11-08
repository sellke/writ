# Prompting Guide

> **Status:** Complete
> **Created:** 2026-10-22
> **Owner:** @AdamSellke
> **Dependencies:** []
> **Phase:** 14 — Front Door and Distribution ([roadmap](../../product/roadmap.md), [ADR-030](../../decision-records/adr-030-contract-verifier-boundary-front-door.md))
> **Origin:** Phase 14 decomposition pre-pass (`/implement-phase 14`, 2026-10-22). Roadmap feature "Prompting guide" (Effort XS); pstack research Recommendation 3, "Write a short prompting guide."

## Specification Contract

**Deliverable:** `.writ/docs/prompting-guide.md`, a shipped user document: what a request carries (goal, done check, proof), one recipe per front-door route, and the pitfalls.

**Must Include:**

1. Three named parts a request carries: **Goal** (what should be true afterwards, in the user's terms), **Done check** (how anyone could tell it is done), **Proof** (what evidence the result must show: a test, a screenshot, a command's output). The front door (`2026-10-22-front-door`) reports which parts a request is missing by these exact names.
2. Recipes, one per route the front door takes: an unsettled idea (`/prototype`), a bug or small change (`/prototype --no-diverge`), a feature (`/create-spec`), roadmap work (`/implement-phase`), a why-or-how question (`/research` until `/why` ships). Each recipe shows a weak request and a strong one, and names the route.
3. Pitfalls: no done check; asking a fork that running something could answer; specifying the how instead of the what; bundling several requests into one; restating the codebase to the agent instead of pointing at files.
4. `README.md` § Quick Start links the guide. The guide is under 150 lines. It ships to installed projects by the existing `.writ/docs/` rule (`is_shippable_writ_doc` is a denylist); if that rule ever becomes an allowlist, this file must be on it.

**Hardest Constraint:** Short enough to read before the first request and specific enough that the front door can point at one section by heading.

**Success Criteria:** the file exists with the headings the front door will cite (`## What a request carries`, `## Recipes`, `## Pitfalls`); `README.md` links it; a test pins the headings, the three part names, the five recipe routes, and the line budget; `bash scripts/eval.sh` reports 0 findings.

**Scope out:** platform-specific prompting, model choice, Writ-internal workflows (the guide is written for a user of an installed project, not a Writ maintainer).

## Technical Concerns

- `scripts/eval.sh` `check_referenced_paths` treats every backticked `*.md` token in `commands/*.md` as a claim that the file exists. The front door will cite `.writ/docs/prompting-guide.md`; the token resolves against the repo root, so the file must exist before that command lands. This spec therefore precedes `2026-10-22-front-door` in the phase order.
- `.writ/docs/` is also where dev-only records live, and `2026-10-21-dev-only-docs-ship-to-users` proposes narrowing the ship set by pattern. The guide's name does not match the proposed exclusion patterns (`leanness-audit-2*.md`, `swot-*.md`). Business Rule 5 records the allowlist obligation.
- The guide must not name a Writ-internal path a user's project will not have (research files, ADRs, spec folders of this repo). `check_shipped_refs` already scans shipped commands for such links; it does not scan `.writ/docs/`. The test in Story 2 adds that scan for this one file.

## Experience Design

### Who uses it

- **A new user** who installed Writ and is about to type their first request.
- **The front door**, which links a section when a request is missing a part.
- **A returning user** who got a poor result and wants to know what to change in the request.

### Journey

1. Entry: the README's Quick Start says "Read the prompting guide, then run `/writ`"; or the front door says "Your request has no done check (see prompting-guide.md § What a request carries)."
2. Happy path: the user reads the three parts, finds the recipe for their situation, rewrites the request, and runs it.
3. Moment of truth: the front door restates the request without asking for anything that was missing.
4. Feedback: the routed command's first output matches what the user asked for.

### State Catalog

| State | What the user sees |
|---|---|
| Fresh install, README Quick Start | A one-line pointer to the guide before the first command. |
| Request missing a part | The front door names the part and links the guide section. |
| Request has all three parts | The front door restates and routes without a prompt about the request's shape. |
| Guide over 150 lines | `test_prompting_guide` fails with the line count. |
| Guide links a Writ-internal path | `test_prompting_guide` fails naming the link. |

## Business Rules (Expanded)

1. **Headings are an interface.** `## What a request carries`, `## Recipes`, `## Pitfalls` are the three H2 headings, in that order, spelled exactly so. The front door cites them by text.
2. **Part names are an interface.** `Goal`, `Done check`, `Proof`, bold, as the first words of three list items under the first heading.
3. **Five recipes, by route.** `### An unsettled idea`, `### A bug or a small change`, `### A feature`, `### Roadmap work`, `### A why or how question`. Each has a "Weak:" line, a "Strong:" line, and a "Route:" line naming the command and flags.
4. **Pitfalls are a list**, each item one sentence naming the pitfall and the fix.
5. **Ships.** Lives at `.writ/docs/prompting-guide.md`. If `is_shippable_writ_doc` becomes an allowlist, the file is on it; the Story 2 test asserts the function admits the filename.
6. **Line budget:** under 150 lines including headings and blank lines.
7. **No internal links.** The guide links nothing under `.writ/research/`, `.writ/decision-records/`, `.writ/specs/`, or `.writ/product/`. It may link `README.md` and other shipped `.writ/docs/` files.
8. **Plain prose.** Follows `skills/plain-prose/SKILL.md`: no mannered prose, no marketing, no em-dashes.

## Detailed Requirements

### Story 1: Write the guide

- Author `.writ/docs/prompting-guide.md` per Business Rules 1–4, 6–8. Weak and strong examples are concrete and short (one line each).
- The "A why or how question" recipe names `/research` and says `/why` replaces it when it ships.

### Story 2: Ship, link, and pin

- `README.md` § Quick Start gains a line pointing to the guide before the five-command table.
- New `scripts/tests/test_prompting_guide.py`: file exists; the three H2 headings in order; the three bold part names; the five H3 recipe headings; every recipe has Weak, Strong, and Route lines; line count under 150; no link to the excluded internal paths; `is_shippable_writ_doc prompting-guide.md` returns 0 in both `scripts/install.sh` and `scripts/update.sh` (source the function from each script in a bash subprocess).

## Implementation Approach

- **Order.** Story 1, then Story 2.
- **Tests read markdown as text**, matching `scripts/tests/test_platform_neutral_names.py`'s style. For the ship-set assertion, run `bash -c 'source <(sed -n "/^is_shippable_writ_doc()/,/^}/p" scripts/install.sh); is_shippable_writ_doc prompting-guide.md'` and expect exit 0.
- **Verification.** `uv run --python 3.9 pytest`, the bash test loop, and `bash scripts/eval.sh` after each story.
