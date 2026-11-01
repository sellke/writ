> Regenerated from spec.md on 2026-10-25

# Front Door (Lite)

> Source: .writ/specs/2026-10-22-front-door/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** `/writ "<request>"` restates the request in Writ's own words (goal, problem, done check), classifies it, proposes one route, confirms once, then runs the routed command with its phases mirrored in the todo list.

**Implementation Approach:**
- Routes, one rule table in `## Routing Rules`, exactly six rows in order: unsettled idea → `/prototype`; bug or small change → `/prototype --no-diverge`; feature → `/create-spec`; roadmap work → `/implement-phase`; why or how → `/research` until `/why` ships; empirical fork → `/prototype`, never a question. No other classification logic.
- Tie-break: when `/prototype --no-diverge` and `/create-spec` cues both fire, `/prototype`'s escalation signals decide (over 5 files, schema change, new dependency, core architecture, low coverage → `/create-spec`).
- Restatement: labeled `Goal:`, `Problem:`, `Done check:` lines, plus `Proof:` when the request names evidence. A missing part is named by the prompting guide's names and links `.writ/docs/prompting-guide.md` § What a request carries. It is reported, not demanded.
- Routing proceeds unless the goal is missing, or the request names a file, function, or system that a search of the project does not find. Either case gets one natural-language question, no menu (amended 2026-10-24, DEV-009).
- One AskQuestion: the proposed route labeled `(Recommended)`, the two other routes closest to the request, and "Not what I meant" last, at most four options. The prompt names the routes left out (amended 2026-10-24, DEV-007).
- Mirroring: the routed command's `### Phase N:` headings (or `### Step N:`) go on the todo list before it runs; a skipped phase shows `skip: <reason>`. Use `todo_write`; where the adapter maps it to a file, print the checklist and write nothing.
- Handoff: read the routed command file and follow it top to bottom with the restatement as the request. Add no step and remove none. Flags travel with the route (`--no-diverge`, `--from-issue <path>`, `@file`).
- `entry_level: high`. The command file targets under 200 lines.
- Registration: manifest `entry` category ("Start here") first, `writ` between `verify-spec` and `writ-design`; `SKILL.md` via `gen-skill.sh`; `claude-code/CLAUDE.md` after the template gains a "Start with `/writ`" line; Codex template row; README Quick Start opens with `/writ`, then the guide pointer, then the five-command table under "What `/writ` routes to"; `adapters/cursor.md` tree count 33; `commands/status.md` list; `.writ/docs/model-tiers.md` high row (16); Claude Code adapter `todo_write` → `TodoWrite`.
- Edit markdown by section heading, never by line number. Regenerate generated files.

**Files in Scope:**
- Story 1: `commands/writ.md`, `scripts/tests/test_front_door.py` (command section).
- Story 2: `.writ/manifest.yaml`, `SKILL.md`, `scripts/gen-claude-md.py` template, `claude-code/CLAUDE.md`, `codex/AGENTS.md.template`, `README.md`, `adapters/cursor.md`, `adapters/claude-code.md`, `commands/status.md`, `.writ/docs/model-tiers.md`, `scripts/tests/test_front_door.py` (registration section).
- Story 3: `scripts/eval-command-structure.py` rows, `.writ/issues/features/2026-10-13-in-your-own-words.md`, `sub-specs/technical-spec.md` § Routing Fixture.

**Error Handling:**
- No request and no context → one question: what do you want to do?
- Request names something the project does not contain → restatement, what was searched for and not found, then one question about where it lives, before routing.
- Roadmap absent and the request names a phase → the route is not offered; say the roadmap is missing and `/plan-product` creates it.
- Routed command file missing → name the file and `/update-writ`; do not improvise the workflow.

**Integration Points:**
- Depends on `2026-10-22-prompting-guide`: the guide file and its headings must exist.
- Under a Claude Code plugin the command reads `/writ:writ`; the plugin spec documents it.
- ADR-030's review at Phase 14 close removes the command if work still starts from direct commands.

---

## For Review Agents

**Acceptance Criteria:**
1. `commands/writ.md` has the contracted frontmatter (`entry_level: high`, four exit criteria) and the six-row rule table in order.
2. Step 3 is one AskQuestion with at most four options, `(Recommended)` on the proposed route and "Not what I meant" last; Step 4 names `skip:`; the guide is cited by path.
3. Manifest, `SKILL.md`, `claude-code/CLAUDE.md`, the Codex template, and `README.md` agree on the new command, and every registration surface is pinned by a test.
4. `check_command_structure` and `check_referenced_paths` pass for `commands/writ.md`.
5. The in-your-own-words issue has `## Resolution` and `spec_ref`; the routing fixture's eight requests route as the table says.

**Business Rules:**
- The rule table is the only classifier. The command stays thin: one rule table, one confirmation.
- `/writ` creates nothing under `.writ/` and keeps no state; resume is the routed command's concern.
- The handoff adds no step and removes none.

**Experience Design:**
- Entry: `/writ "<request>"`, `/writ` with conversation context, or `/writ @file`.
- Happy path: restatement → proposed route → one confirmation → phases on the todo list → routed command runs.
- Moment of truth: the routed command's first output matches the restatement.
- Error: a missing goal, or something the project lacks, gets one plain question; a missing done check is named, not demanded.

---

## For Testing Agents

**Success Criteria:**
1. `commands/writ.md` passes `check_command_structure` and `check_referenced_paths`.
2. A test pins the six routes in the rule table and every registration surface.
3. `bash scripts/eval.sh` reports 0 findings.

**Scope out:** model routing (ADR-024 stands), new verification, changes to the routed commands' own workflows, `/why` (Phase 15), a `--recommend` flag on `/writ`.

**Test Strategy:**
- Python 3.9 standard library; static text tests over the command, manifest, catalogs, README, adapters, and docs; subprocess calls to the generator `--check`s.
- Run `uv run --python 3.9 pytest`, the bash test loop, and `bash scripts/eval.sh` after every story.
