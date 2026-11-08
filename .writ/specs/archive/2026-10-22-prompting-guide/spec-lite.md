# Prompting Guide (Lite)

> Source: .writ/specs/2026-10-22-prompting-guide/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** `.writ/docs/prompting-guide.md`, a shipped user doc under 150 lines: the three parts a request carries (Goal, Done check, Proof), five route recipes with weak and strong examples, and the pitfalls; linked from README Quick Start and pinned by a test.

**Implementation Approach:**
- H2 headings, exact and in order: `## What a request carries`, `## Recipes`, `## Pitfalls`. The front door cites them by text.
- Parts as list items `- **Goal**`, `- **Done check**`, `- **Proof**`.
- Recipes as H3: `### An unsettled idea` (`/prototype`), `### A bug or a small change` (`/prototype --no-diverge`), `### A feature` (`/create-spec`), `### Roadmap work` (`/implement-phase <N>`), `### A why or how question` (`/research`, replaced by `/why` when it ships). Each has `Weak:`, `Strong:`, `Route:` lines.
- Pitfalls: one-sentence list items (no done check; asking a fork you could run; specifying the how; bundling requests; restating the codebase).
- No links to `.writ/research/`, `.writ/decision-records/`, `.writ/specs/`, `.writ/product/`. Plain prose per `skills/plain-prose/SKILL.md`.
- README § Quick Start gains one pointer line before the five-command table (the `/writ` clause is added by the front-door spec).

**Files in Scope:**
- `.writ/docs/prompting-guide.md` (S1)
- `README.md` § Quick Start, `scripts/tests/test_prompting_guide.py` (S2)

**Error Handling:**
- Over 150 lines → test fails with the count; cut examples first.
- Internal link → test names it; replace with prose.
- `is_shippable_writ_doc` restructured → fix the test's extraction, not the guide.

**Integration Points:**
- `2026-10-22-front-door` cites `.writ/docs/prompting-guide.md` and its headings; `check_referenced_paths` needs the file to exist first.
- Ship set is a denylist today; if it becomes an allowlist, add this file.

---

## For Review Agents

**Acceptance Criteria:**
1. Guide exists with the three H2 headings in order and the three bold part names `[AC-1.1, AC-1.2]`
2. Five H3 recipes in order, each with Weak, Strong, and Route lines naming the contracted command `[AC-1.3]`
3. Pitfalls section lists the five pitfalls as one-sentence items `[AC-1.5]`
4. Under 150 lines; no internal-history links; plain prose `[AC-1.1, AC-1.4, AC-1.5]`
5. README Quick Start links the guide before the five-command table `[AC-2.1]`
6. `test_prompting_guide.py` pins headings, parts, recipes, budget, links, README, and ship-set admission; eval.sh 0 findings `[AC-2.2, AC-2.3, AC-2.4, AC-2.5]`

**Business Rules:**
- Headings and part names are an interface for the front door; spelling is fixed.
- Written for a user of an installed project, never for a Writ maintainer.
- Ships by the existing `.writ/docs/` rule; must stay in any future allowlist.

**Experience Design:**
- Entry: README Quick Start, or the front door naming a missing part.
- Happy path: read, rewrite the request, run.
- Moment of truth: the front door restates without asking for a missing part.
- Feedback: the routed command's first output matches the ask.
- Error: a missing part is named with the guide section to read.

---

## For Testing Agents

**Success Criteria:**
1. `uv run --python 3.9 pytest scripts/tests/test_prompting_guide.py` passes.
2. Full pytest, bash test loop, and `bash scripts/eval.sh` (0 findings) pass.

**Shadow Paths to Verify:**
- **Happy path:** all seven tests green.
- **Nil input:** recipe without `Route:` → `test_recipes` fails naming it.
- **Empty input:** no H2s → `test_headings` fails.
- **Upstream error:** ship-set function extraction fails → `test_ships` fails on extraction.

**Edge Cases:**
- Exactly 150 lines → fails (`< 150`).
- A `Route:` line with extra flags → passes if the contracted command is named.

**Test Strategy:**
- Static text tests over the guide and README; a bash subprocess per script for `is_shippable_writ_doc`.
