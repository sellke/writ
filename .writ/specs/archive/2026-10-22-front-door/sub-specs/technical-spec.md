# Technical Spec: Front Door

> Spec: [`../spec.md`](../spec.md) · Issue: [`in-your-own-words`](../../../issues/features/2026-10-13-in-your-own-words.md) · Research: [`2026-10-19-writ-vs-pstack-research.md`](../../../research/2026-10-19-writ-vs-pstack-research.md) F1

## Current State (audit, 2026-10-22)

- 33 files in `commands/` (32 commands plus `_preamble.md`). No command classifies a request. `README.md` § Quick Start: "Writ ships 32 commands, but you only need five."
- Registration surfaces for a new command (from the `/writ-design` rename inventory, 2026-10-20): `.writ/manifest.yaml` (`commands:` sorted by name; `categories:` list), `SKILL.md` (generated, `scripts/gen-skill.sh`, category-aware), `claude-code/CLAUDE.md` (generated, `scripts/gen-claude-md.py`, flat table), `codex/AGENTS.md.template` (hand-maintained category tables), `README.md` § Commands table, `adapters/cursor.md` § Directory Structure tree (count in the comment), `commands/status.md:249` comma-separated list, `.writ/docs/model-tiers.md` § Deriving a Command's `entry_level` table.
- `scripts/eval.sh`: `check_manifest` (every `commands/*.md` registered), `check_command_structure` (`scripts/eval-command-structure.py` ROWS), `check_referenced_paths` (backticked `*.md` tokens must resolve), `check_entry_level` (note when missing), `check_preamble`, `check_required_sections`.
- Capability rows: `todo_write` → Cursor `todo_write` (native); Claude Code `Write(".writ/state/tracking.json")` (stale; `TodoWrite` exists); Codex `Write(".writ/state/...json")`; OpenClaw `Write({ path: ".writ/state/tracking.json" })`.
- `commands/prototype.md` escalation signals: over 5 files, schema change, new dependency, core architecture, low existing coverage.

## `commands/writ.md` Skeleton

```markdown
---
name: writ
description: "Restate a request in Writ's own words, pick the command whose ceremony fits, confirm once, and run it with its phases on the todo list. The one command a new user needs."
problem: "Writ ships 32 commands and a user has to know which one fits before typing anything, so work starts at the wrong level of ceremony or not at all."
outcome: "The request is restated as goal, problem, and done check, routed to exactly one existing command at the fitting ceremony, and that command runs with its phases mirrored in the todo list; nothing is written beyond what the routed command writes."
entry_level: high
exit_criteria:
  - "the restatement names a goal, a problem, and a done check, or names which of them the request lacks by the prompting guide's part names"
  - "exactly one route from the rule table was proposed, confirmed through one AskQuestion, and the routed command's file was read and followed"
  - "the todo list carries the routed command's phase headings before its first phase runs, and every skipped phase reads skip: <reason>"
  - "no file under .writ/ was created by this command itself"
---

# Writ Command (writ)

## Overview
## Invocation
## Required Artifacts
## Command Process
### Step 1: Restate
### Step 2: Classify
### Step 3: Confirm
### Step 4: Mirror the Route's Phases
### Step 5: Run the Route
## Routing Rules
## Completion
## References
```

### Routing Rules table (exact rows, in order)

| Signal | Route |
|---|---|
| The request names a goal rather than a change, asks for options, or the direction is unsettled | `/prototype` |
| A bug, or a change with one obvious shape (see tie-break) | `/prototype --no-diverge` |
| A capability users will rely on, or any `/prototype` escalation signal: over 5 files, schema change, new dependency, core architecture, low existing coverage | `/create-spec` |
| Names a phase or feature in `.writ/product/roadmap.md` | `/implement-phase <N>` |
| Asks why something is the way it is, or how something works | `/research` (`/why` takes this route when it ships) |
| A fork that a throwaway run could answer faster than a question | `/prototype`, with the fork named as the thing to try |

### Step 3 AskQuestion

```
AskQuestion({
  title: "Route",
  questions: [{
    id: "route",
    prompt: "<restatement>\n\nProposed: <route> — <one-line reason>",
    options: [
      { id: "proposed", label: "<route> (Recommended)" },
      { id: "alt-1", label: "<other route>" }, …,
      { id: "other", label: "Not what I meant" }
    ]
  }]
})
```

### Step 4 mirroring

Read the routed command file. Collect headings matching `^### Phase \d+` (fallback `^### Step \d+`). For each, one todo item with the heading text. A phase the chosen flags skip gets ` — skip: <reason>` appended (`--no-diverge` skips `/prototype` Step 2.5; `--quick` skips gates per the routed command's own table). Capability: `todo_write`. If the adapter maps it to a file write, print the list as a markdown checklist in the reply instead.

## Registration Edits (Story 2)

| File | Edit |
|---|---|
| `.writ/manifest.yaml` | `categories:` first entry `- id: entry` / `label: "Start here"`; `commands:` entry `name: writ`, `file: commands/writ.md`, `category: entry`, `purpose: "Restate a request, route it to the fitting command, and run it with its phases on the todo list."`, `tags: [entry, routing]`, inserted after `verify-spec`. |
| `SKILL.md` | `bash scripts/gen-skill.sh`; `--check` prints `pass`. |
| `scripts/gen-claude-md.py` | TEMPLATE: one line above the Commands table: `Start with `/writ "<what you want>"`: it restates the request and routes it to the right command.` Then `python3 scripts/gen-claude-md.py`; `--check` prints `pass`. |
| `codex/AGENTS.md.template` | New first table `### Start here` with the `/writ` row, above Planning & Specification. |
| `README.md` | § Quick Start rewritten (spec.md Business Rule 10); § Commands gains a `### Start here` table with the `/writ` row. |
| `adapters/cursor.md` | Directory tree: `writ.md  # /writ` in sorted position (after `verify-spec.md`, before `writ-design.md`); comment count 32 → 33. |
| `adapters/claude-code.md` | § Tool Mapping → Quick Reference, `todo_write` row: second cell `` `TodoWrite` ``, Notes `Native todo list; phases mirror here`. |
| `commands/status.md` | Line 249 list: add `` `/writ` `` first. |
| `.writ/docs/model-tiers.md` | `high` row: add `writ` in sorted position; count 15 → 16. |

## Tests (`scripts/tests/test_front_door.py`)

| Test | Assertion |
|---|---|
| `test_command_file` | `commands/writ.md` exists; frontmatter has `name: writ`, `entry_level: high`, `problem`, `outcome`, `exit_criteria`. |
| `test_routing_rules` | § Routing Rules first table has six data rows whose Route cells, in order, contain `/prototype`, `/prototype --no-diverge`, `/create-spec`, `/implement-phase`, `/research`, `/prototype`; the fifth mentions `/why`. |
| `test_confirmation_step` | § Step 3 contains `(Recommended)` and `Not what I meant`. |
| `test_mirroring_step` | § Step 4 contains `skip:` and `todo_write`. |
| `test_guide_cited` | File contains `.writ/docs/prompting-guide.md` and `What a request carries`. |
| `test_manifest` | `name: writ` with `file: commands/writ.md`, `category: entry`; `categories[0].id == entry`; commands sorted. |
| `test_catalogs` | `SKILL.md` and `claude-code/CLAUDE.md` contain a `` `/writ` `` row; `gen-skill.sh --check` and `gen-claude-md.py --check` first line `pass`; `codex/AGENTS.md.template` has the row. |
| `test_readme` | § Quick Start: `/writ` appears before the first table; a `What `/writ` routes to` heading exists. |
| `test_surfaces` | cursor tree line, count 33; `status.md` list has `/writ`; `model-tiers.md` `high` row has `writ` and `(16)`; Claude Code adapter `todo_write` row contains `TodoWrite`. |

## Routing Fixture (Story 3 applies Steps 1–3 to each; What Was Built records the outcome)

| # | Request | Expected route |
|---|---|---|
| 1 | "users can't paste into the search box on Safari" | `/prototype --no-diverge` |
| 2 | "a settings page where people can manage API keys" | `/create-spec` |
| 3 | "something to make onboarding feel less empty" | `/prototype` |
| 4 | "do Phase 15" | `/implement-phase 15` |
| 5 | "why does the importer skip rows with empty emails?" | `/research` |
| 6 | "should we use Postgres full-text search or Meilisearch for this?" | `/prototype` (empirical fork) |
| 7 | "rename `getUser` to `fetchUser` everywhere" | `/prototype --no-diverge` |
| 8 | "add multi-tenant billing with per-seat pricing" | `/create-spec` |

## Shadow Paths

- **Happy path:** restate → route → confirm → mirror → run.
- **Nil input:** `/writ` alone with no context → one natural-language question.
- **Empty input:** request with no goal → one natural-language question before routing.
- **Upstream error:** routed command file missing (partial install) → say which file is missing and name `/update-writ`; do not improvise the workflow.

## Error & Rescue Map

Not required: no data flow; the command reads files and asks one question.
