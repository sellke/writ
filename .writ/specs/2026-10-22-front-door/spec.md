# Front Door

> **Status:** Complete
> **Created:** 2026-10-22
> **Owner:** @AdamSellke
> **Dependencies:** [2026-10-22-prompting-guide]
> **Phase:** 14 — Front Door and Distribution ([roadmap](../../product/roadmap.md), [ADR-030](../../decision-records/adr-030-contract-verifier-boundary-front-door.md))
> **Origin:** Phase 14 decomposition pre-pass (`/implement-phase 14`, 2026-10-22). Finding F1 in `.writ/research/2026-10-19-writ-vs-pstack-research.md`. Closes `.writ/issues/features/2026-10-13-in-your-own-words.md` (absorbed as the restate step) and absorbs the empirical-fork rule promoted from the roadmap parking lot on 2026-10-20.

## Specification Contract

**Deliverable:** `/writ "<request>"`: restates the request in Writ's own words (goal, problem, done check), classifies it, proposes one route, confirms once, then runs the routed command with its phases mirrored in the todo list.

**Must Include:**

1. Routes, from the roadmap: an unsettled idea → `/prototype`; a bug or a small change → `/prototype --no-diverge`; a feature → `/create-spec`; roadmap work → `/implement-phase`; a why or how question → `/research` until `/why` ships, with the swap recorded in the command; a fork that running something could answer → `/prototype`, never a question.
2. One AskQuestion after the restatement: the proposed route labeled `(Recommended)`, the two other routes closest to the request, and "Not what I meant" for a free-text correction, at most four options; the prompt names the routes left out (amended 2026-10-24, DEV-007). On confirm, read the routed command's file and follow it with the restated request as its input. `/writ` writes nothing beyond what the routed command writes.
3. Todo mirroring: the routed command's phase headings go onto the todo list before it runs; a phase the route skips shows `skip: <reason>`. Uses the `todo_write` capability where the adapter maps it to a native list; where the adapter maps it to a file, the checklist is printed in the reply instead and no file is written. The Claude Code adapter's `todo_write` row is corrected to `TodoWrite`.
4. The restate step names any missing part by the prompting guide's names (**Goal**, **Done check**, **Proof**) and links `.writ/docs/prompting-guide.md` § What a request carries. A missing part is reported, not demanded: routing proceeds unless the goal itself is missing.
5. Registration: `.writ/manifest.yaml` under a new first category `entry` ("Start here"); `SKILL.md` regenerated; `claude-code/CLAUDE.md` regenerated after its generator's template gains a "Start with `/writ`" line; `codex/AGENTS.md.template` row; `README.md` § Quick Start rewritten so `/writ` is the first thing a reader sees and the five-command table follows it; `adapters/cursor.md` directory tree (count 32 → 33); `commands/status.md` command list; `.writ/docs/model-tiers.md` entry-level table.
6. `entry_level: high` by the two-question derivation: it renders a routing judgment the user acts on.
7. The in-your-own-words issue gets a `## Resolution` and its `spec_ref` set to this spec.

**Hardest Constraint:** The command stays thin. It adds no classification machinery beyond one rule table and one confirmation, and ADR-030's review at Phase 14 close removes it if work still starts from direct commands.

**Success Criteria:** `commands/writ.md` passes `check_command_structure` and `check_referenced_paths`; manifest, `SKILL.md`, `claude-code/CLAUDE.md`, the Codex template, and `README.md` agree on the new command; a test pins the six routes in the rule table and every registration surface; `bash scripts/eval.sh` reports 0 findings.

**Scope out:** model routing (ADR-024 stands), new verification, any change to the routed commands' own workflows, `/why` (Phase 15), a `--recommend` flag on `/writ`.

## Technical Concerns

*Found while grounding the contract on 2026-10-22. None changes scope.*

- `scripts/gen-claude-md.py` lists commands from the manifest without categories (no category handling in the file), so `/writ` would sort last in `claude-code/CLAUDE.md`'s table. The template gains a one-line "Start with `/writ "<what you want>"`." above the table. `scripts/gen-skill.sh` reads `.categories[]`, so the new `entry` category renders first in `SKILL.md` without a generator change.
- Under a Claude Code plugin (`2026-10-22-plugin-distribution`), commands are namespaced, so the front door reads `/writ:writ`. Accepted at discovery on 2026-10-22; the plugin spec documents it.
- `commands/prototype.md` says an ambiguous input gets "a single clarifying question in natural language rather than presenting a menu". The front door's one confirmation is a bounded choice over known routes, which ADR-001 assigns to AskQuestion. The two are consistent: `/writ` asks once about the route; `/prototype` may still ask once about the change.
- "Writes nothing" and file-based todo mappings conflict on Codex and OpenClaw (`todo_write` → `Write(".writ/state/...json")`). Resolved by Must Include 3: print the checklist there.
- The empirical-fork rule needs a test the agent can apply: "could a throwaway run answer this in under the time it takes to ask?" If yes, the route is `/prototype` with the fork named as the thing to try, and the confirmation says so.

## Experience Design

### Who uses it

- **A new user** who has read the prompting guide and types one command.
- **A returning user** who does not want to decide between `/prototype` and `/create-spec`.
- **The maintainer** reviewing at phase close whether work starts here.

### Journey

1. Entry: `/writ "users can't paste into the search box on Safari"`.
2. Restate: *Goal: pasting into the search box works on Safari. Problem: the paste handler drops the event on WebKit. Done check: a paste on Safari fills the field. Proof: none given; a browser check on Safari would do.*
3. Route: *This is a bug with one obvious shape → `/prototype --no-diverge`.* AskQuestion: `/prototype --no-diverge (Recommended)` · `/prototype` (explore options) · `/create-spec` · Not what I meant; the prompt lists `/research` as another route.
4. Mirror: the todo list shows `Context Scan`, `Diverge + Choose — skip: --no-diverge, bug with one obvious shape`, `Coding Agent`, `Lint & Typecheck`, `Summary`.
5. Run: `/prototype --no-diverge` runs with the restated request. Its output is the first thing written.

### State Catalog

| State | What the user sees |
|---|---|
| Request has goal, done check, proof | Restatement, route, confirmation. No remark about the request's shape. |
| Request lacks a done check or proof | Restatement names the missing part, links the guide section, proposes a route anyway. |
| Request lacks a goal | Restatement says so and asks one natural-language question before routing. No menu. |
| Request names a roadmap phase or feature | Route `/implement-phase <N>`; the confirmation shows the matched phase. `roadmap.md` absent → route not offered; the restatement says the roadmap is missing and `/plan-product` creates it. |
| Request is a why or how question | Route `/research`; the confirmation notes `/why` will take this route when it ships. |
| Request is a fork ("should we use A or B?") | Route `/prototype` with the fork named; the confirmation says a throwaway run answers it faster than the user can. |
| User picks another route | The chosen route runs; the restatement is unchanged. |
| User picks "Not what I meant" | One free-text follow-up, then restate and route again. |
| Routed command has phases | Each phase heading on the todo list before the routed command's first phase runs. |
| Route skips a phase | `skip: <reason>` on that item. |
| Platform maps `todo_write` to a file | The checklist is printed in the reply; nothing is written. |
| `/writ` with no request and no context | One natural-language question: what do you want to do? |

### Interaction Patterns

- One restatement, one question, then the routed command owns the conversation.
- The restatement is in Writ's words, not the user's: it names the problem the request implies, not just the request.
- Flags travel with the route (`--no-diverge`, `--from-issue <path>` when the request is an issue file).

## Business Rules (Expanded)

1. **Rule table is the classifier.** `commands/writ.md` carries one table, `## Routing Rules`, with exactly six rows in this order: unsettled idea → `/prototype`; bug or small change → `/prototype --no-diverge`; feature → `/create-spec`; roadmap work → `/implement-phase`; why or how → `/research` (until `/why`); empirical fork → `/prototype`. Each row has a Signal column with the observable cues. No other classification logic.
2. **Tie-break.** When cues for `/prototype --no-diverge` and `/create-spec` both fire, `/prototype`'s own escalation signals decide: over 5 files, a schema change, a new dependency, core architecture, or low existing coverage → `/create-spec`. Otherwise `/prototype --no-diverge`.
3. **Restatement shape.** Three labeled lines, `Goal:`, `Problem:`, `Done check:`, and a fourth, `Proof:`, when the request names evidence. A missing part reads `Goal: (not stated — see prompting-guide.md § What a request carries)`.
4. **One confirmation.** Exactly one AskQuestion, with the proposed route labeled `(Recommended)` per `system-instructions.md` § Recommendation Semantics, the two other routes closest to the request, and "Not what I meant" last: at most four options, because Claude Code's question tool takes two to four. The prompt names the routes left out (amended 2026-10-24, DEV-007).
5. **Phase mirroring.** Read the routed command file; collect its `### Phase N:` headings (or `### Step N:` headings when it has no phases); put them on the todo list in order; mark a phase the chosen flags skip with `skip: <reason>`. Use the `todo_write` capability per the adapter. On an adapter whose mapping is a file write, print the checklist and write nothing.
6. **Handoff.** After the confirmation, `/writ` reads the routed command file and follows it top to bottom with the restatement as the request. It adds no step and removes none.
7. **No artifacts.** `/writ` creates nothing under `.writ/` and keeps no state. Resume is the routed command's concern.
8. **Registration order.** Manifest `commands:` stays sorted by name (`writ` after `verify-spec`, before `writ-design`); `categories:` gains `- id: entry` / `label: "Start here"` as its first entry; `writ`'s category is `entry`.
9. **Generated files are regenerated.** `SKILL.md` via `bash scripts/gen-skill.sh`; `claude-code/CLAUDE.md` via `python3 scripts/gen-claude-md.py` after the template edit. `codex/AGENTS.md.template` is hand-maintained today and gets a hand edit (`2026-10-22-generated-platform-trees` puts it under a generator later).
10. **README.** § Quick Start opens with `/writ` and a two-line example, then the prompting-guide pointer (from `2026-10-22-prompting-guide`) with its `/writ` clause completed, then the five-command table under the heading "What `/writ` routes to".
11. **Entry level.** `entry_level: high`; `.writ/docs/model-tiers.md`'s `high` row adds `writ` and its count becomes 16.
12. **Runtime.** Python 3.9 standard library for tests. Markdown edits by section heading, never by line number.

## Detailed Requirements

### Story 1: The `/writ` command file

- `commands/writ.md` with frontmatter (`name`, `description`, `problem`, `outcome`, `entry_level: high`, `exit_criteria` ×4), `## Overview`, `## Invocation` (`/writ "<request>"`, `/writ` with conversation context, `/writ @file`), `## Required Artifacts` (none required; roadmap and guide optional with degradation), `## Command Process` with Steps 1–5 (Restate, Classify, Confirm, Mirror, Run), `## Routing Rules` (the table), `## Completion`, `## References`.
- `scripts/tests/test_front_door.py` (command section): file exists; frontmatter keys and `entry_level: high`; the six rule rows in order with their routes; the AskQuestion step names `(Recommended)` and "Not what I meant"; the mirroring step names `skip:`; the guide path is cited.

### Story 2: Registration and catalogs

- Manifest category and command entry; `SKILL.md` regenerated; `gen-claude-md.py` template line and `claude-code/CLAUDE.md` regenerated; Codex template row; README Quick Start; cursor adapter tree; `status.md` list; `model-tiers.md` row; Claude Code adapter `todo_write` → `TodoWrite`.
- `test_front_door.py` (registration section) pins each surface. `bash scripts/gen-skill.sh --check` and `python3 scripts/gen-claude-md.py --check` print `pass`.

### Story 3: Structure rows, issue resolution, and routing fixture

- `scripts/eval-command-structure.py` ROWS: `writ.md` heading `## Routing Rules` and frontmatter `entry_level`.
- `## Resolution` on the in-your-own-words issue; `spec_ref` set.
- Routing fixture: `sub-specs/technical-spec.md` § Routing Fixture lists eight sample requests with the expected route; the lane applies Steps 1–3 to each (stopping before the confirmation) and records the proposed route in the story's What Was Built. Any mismatch is a rule-table fix, not a fixture edit.

## Implementation Approach

- **Order.** Story 1, then 2, then 3. Story 2 touches generated files and must run after `2026-10-22-prompting-guide` lands (README pointer line).
- **Thin by construction.** The command file targets under 200 lines. If it grows past that, something that belongs to a routed command has leaked in.
- **Verification.** `uv run --python 3.9 pytest`, the bash test loop, and `bash scripts/eval.sh` after every story.
