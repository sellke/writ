# Story 3: Generated Codex Template

> **Status:** Completed ✅ (2026-10-23)
> **Commit:** bf407c58657c544c532fa55ed72a9a2a027e1b72
> **Priority:** High
> **Dependencies:** Story 2

## User Story

**As a** Codex user with Writ installed in my project
**I want to** have the Writ block in `AGENTS.md` list every command, agent, and skill, and map every capability to Codex, without pointing at any file my project does not have
**So that** I can find and run any Writ capability from the one file Codex loads every session

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.4

- [x] Given `.writ/manifest.yaml` (`categories:`, `commands:`, `agents:`) and every `skills/*/SKILL.md`, when the driver renders `codex/AGENTS.md.template`, then each `commands:` entry appears once in its category table with its manifest purpose and path `.codex/commands/<name>.md`, the `### Start here` table holding the `/writ` row is the first table under `## Available Commands`, each manifest agent appears under `## Available Agents` with path `.codex/agents/<name>.toml`, and each skill appears under `## Available Skills` with its frontmatter `description` and path `.agents/skills/<name>/SKILL.md` `[AC-3.1]`
- [x] Given the rendered template, when it is read, then line 1 is the merge-marker comment byte-identical to the hand-maintained file's line 1, a generator comment names `scripts/gen-platform-trees.py`, the file contains no `adapters/` substring, `## Writ on Codex` points at the Capability Map below, and the sections appear in this order: Writ on Codex, Available Commands, Available Agents, Available Skills, Built-in Codex slash commands vs Writ, Capability Map, Catalog source `[AC-3.2]`
- [x] Given the hand-maintained `codex/AGENTS.md.template` and the generator's output, when the two are diffed before the first write, then every dropped or changed sentence is recorded with its reason in a `## What Was Built` section of this story, and no sentence that is still true is missing from the generated file `[AC-3.3]`
- [x] Given the regenerated template, when its byte size is measured and the merge and install suites run, then the file is under 16384 bytes, `scripts/tests/test_merge_agents_md.sh` passes, and every `scripts/tests/test_install_update_*.sh` passes `[AC-3.4]`

## Implementation Tasks

- [x] 3.1 Write the failing `test_codex_template` in `scripts/tests/test_gen_platform_trees.py` (Python 3.9 stdlib): every `commands:` name, every manifest agent, and every `skills/*/SKILL.md` name appears in the rendered output; the `/writ` row sits under `### Start here`; no `adapters/` substring; size under 16384 bytes; the built-ins heading is present; line 1 equals the hand-maintained file's line 1. Run it and confirm it fails against today's hand-maintained template `[AC-3.1, AC-3.2, AC-3.4]`
- [x] 3.2 Add `render_codex_template` to `scripts/gen-platform-trees.py`. It returns the file text and writes nothing. Inputs: the manifest (categories in manifest order with `entry` first, purposes verbatim), the `skills/` directory (names and frontmatter descriptions), the built-ins section as a literal string, and the Codex capability map from Story 2's map function. Place the generator comment on line 2, directly after the merge-marker line. Follow the manifest reading in `scripts/gen-claude-md.py` and the category-table rendering in `scripts/gen-skill.sh` `[AC-3.1, AC-3.2]`
- [x] 3.3 Render to a temp file outside the repo and diff it against `codex/AGENTS.md.template`. In a new `## What Was Built` section of this story, record every dropped or changed sentence with its reason. Mark each as intended (stale command and skill lists, the `adapters/` clause, the purpose cuts) or a bug. Fix every bug and re-render. Do not write the repo file until this record exists `[AC-3.3]`
- [x] 3.4 Add the codex target to the driver's write mode, so `python3 scripts/gen-platform-trees.py` writes `codex/AGENTS.md.template` and prints `wrote codex/AGENTS.md.template`. Write nothing when any reason exists. Run it once; that output is the baseline `[AC-3.2, AC-3.3]`
- [x] 3.5 Rerun the 3.1 test until it passes. Confirm the generated file is under 16384 bytes (`wc -c`) and contains no `adapters/` (`grep -c 'adapters/'` returns 0) `[AC-3.1, AC-3.2, AC-3.4]`
- [x] 3.6 Run `bash scripts/tests/test_merge_agents_md.sh` and each `bash scripts/tests/test_install_update_*.sh`. All must pass with the generated template. These tests use temp directories; do not run `install.sh` or `update.sh` against this repo `[AC-3.4]`
- [x] 3.7 Run the full verification: `uv run --python 3.9 pytest`; `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done` with no `FAIL` lines; `bash scripts/eval.sh` outside any sandbox. Record the eval findings count. The eval stale check for this file belongs to Story 4 `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`

## Notes

- **Front-door dependency.** The current `.writ/manifest.yaml` has no `entry` category and no `writ` command. The hand-maintained template has no `### Start here` table. All three arrive with `2026-10-22-front-door`, which is not yet committed. Do not start 3.1 to 3.5 until it lands, or the `/writ` assertion has nothing to render. This header lists only Story 2; add `2026-10-22-front-door` to Dependencies if the spec owner agrees.
- **Merge-marker line.** Line 1 is the contract that `install.sh` `merge_agents_md` and `update.sh` use to find `writ:start` and `writ:end`. Keep it byte-identical. Its "edit there, not by hand" wording still points maintainers at the template. With generation they should regenerate instead, and the generator comment on line 2 says so. Do not edit line 1.
- **Only `adapters/` mention.** The hand file mentions `adapters/` once, in the `## Writ on Codex` paragraph ("map tools via `adapters/codex.md`"). Replace that clause with "the Capability Map below". The Catalog source note has no `adapters/` reference.
- **Purpose text.** The hand file ends 19 table cells with `…`. The manifest holds the full purposes. Use the manifest text verbatim. Truncate only if the 16384-byte cap forces it; the technical spec estimates under 12 KiB. Each hand-file cut goes in the 3.3 record as an intended change.
- **Expected additions.** The hand file omits `create-goal`, `implement-phase`, `revert`, and `writ`. It lists 7 agents where the manifest lists 8. It lists 1 skill where `skills/` holds 16. The generated file adds these. They are not losses.
- **Skill source.** Skill names and descriptions come from `skills/*/SKILL.md`, not from the manifest's `skills:` list, which carries `status:` fields. The spec requires every `SKILL.md`.
- **Built-ins literal.** Copy the hand file's `## Built-in Codex slash commands vs Writ` section into the generator as a literal string, including its link. Change a sentence only when the 3.3 record gives a reason.
- **Size.** The cap is 16384 bytes (test). Codex's AGENTS.md budget is 32 KiB, so the cap is tighter than the platform limit on purpose.
- **Risks.** Dropping the built-ins section or a still-true sentence during the takeover (3.3 is the guard). Exceeding 16 KiB (the size test catches it). Moving the map above the built-ins section, which breaks the order in AC-3.2.
- **Integration.** Story 2 supplies the driver write path and the Codex map function. Story 4's `--check` will treat this file as generated, so the committed baseline from 3.4 must match a fresh render. `test_merge_agents_md.sh` pins the merge between the markers. The five `test_install_update_*.sh` files exercise install and update.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** `technical-spec.md → ## Shadow Paths` (Happy path, Nil input, Empty input)
- **Business rules:** `spec.md → ## Business Rules (Expanded)` (Rule 5 Capability Map section; Rule 8 Codex template composition and 16 KiB cap; Rule 12 generated-file comment; Rule 15 Python 3.9 stdlib only)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (`Clean tree`, `Installed Codex project`)

---

## What Was Built

**Implementation Date:** 2026-10-23

### Files Created

[None created]

### Files Modified

- **`scripts/gen-platform-trees.py`** (new section "codex/AGENTS.md.template" between `render_writ_mdc` and `GENERATED`; docstring)
  - Constants `MANIFEST_REL`, `SKILLS_DIR`, `CODEX_TEMPLATE_CAP = 16384`, `CODEX_MARKER` (line 1, byte-identical to the hand file), `CODEX_SOURCES = ".writ/manifest.yaml, skills/*/SKILL.md, and the Codex adapter tool table"` (phrased without `adapters/` so the generator comment cannot violate AC-3.2), `CODEX_INTRO`, `CODEX_BUILTINS` and `CODEX_CATALOG_SOURCE` (the hand paragraphs verbatim), table-header pairs; `Manifest(categories, commands, agents)`; `parse_value` (copied from `gen-claude-md.py`, not imported); `manifest_entries`; `read_manifest(root)` (line-based; `ValueError("manifest <detail>")` for a missing section, an empty list, a category without `id`/`label`, a command without `name`/`category`/`purpose`, an undeclared category, a duplicate command, an agent without `purpose`; a missing file is the `OSError`); `read_skills(root)` (every `skills/*/SKILL.md` sorted by directory, frontmatter `description`; `ValueError("skill <name> missing description")`; a missing `skills/` directory is an `OSError`); `escape_cell`; `render_codex_template(root)` (pure; AC-3.2 section order; one blank line between blocks; raises `ValueError("codex template <n> bytes exceeds 16384")` at 16384 bytes or more and `ValueError("codex template mentions adapters/")`). `GENERATED` now ends with `("codex/AGENTS.md.template", render_codex_template)`, so write mode writes 19 files.
- **`codex/AGENTS.md.template`** (generated; first write replaces the hand-maintained file — see Takeover Record)
  - 145 lines, 12478 bytes (hand file 117 lines, 7127 bytes). Line 1 the merge-marker comment, line 2 the generator comment, `## Writ on Codex`, `## Available Commands` (`### Start here` with the `/writ` row first, then one table per manifest category with commands, manifest order, purposes verbatim), `## Available Agents` (8), `## Available Skills` (16, descriptions from each `SKILL.md`), `## Built-in Codex slash commands vs Writ` (verbatim), `## Capability Map` (10 Codex rows), `## Catalog source` (verbatim). `grep -c 'adapters/'` → 0.
- **`scripts/tests/test_gen_platform_trees.py`** (docstring cites AC-3.1 to AC-3.4; Story 2's `test_write_mode_shape` and `test_write_ignores_stale_outputs` cover the 19th file; new Story 3 section)
  - `test_read_manifest`, `test_read_manifest_errors` ×11, `test_read_errors_name_the_missing_file` (AC-3.1); `test_codex_template` (AC-3.1, AC-3.2, AC-3.4: line 1 equals the marker constant, line 2 names the generator, no `adapters/`, no blank-line runs, `## ` headings in AC-3.2 order, the intro verbatim, `### Start here` first with the `/writ` row, every category table equal to the manifest rows in order, each command once, agents and skills tables equal to the sources, built-ins paragraph and link, the map equal to `capability_map("codex", REPO_ROOT)`, Catalog source verbatim, under 16384 bytes); `test_codex_template_matches_committed` (AC-3.2, AC-3.3: a fresh render equals the committed file byte for byte — Story 4's stale check depends on this baseline); `test_codex_template_fails_closed` ×4 (missing purpose, undeclared category, missing skill description, an `adapters/` mention injected into a Codex mapping cell → write mode `fail`, one reason, exit 1, nothing written); `test_codex_template_size_guard` (AC-3.4). The test's manifest and skills readers are independent of the driver's. 63 tests in the file.
- **`.writ/specs/2026-10-22-generated-platform-trees/spec-lite.md`** — the generated-files line names the two render-time guards (DEV-007).
- **`.writ/specs/2026-10-22-generated-platform-trees/drift-log.md`** — Story 3 section (DEV-007).

### Takeover Record (AC-3.3)

Rendered to a scratch file and diffed against the hand-maintained file before the first write; the written file is `cmp`-identical to that render. `git show HEAD:codex/AGENTS.md.template | diff - codex/AGENTS.md.template` (hand file `<`, generated `>`):

```
1a2
> <!-- generated by scripts/gen-platform-trees.py from .writ/manifest.yaml, skills/*/SKILL.md, and the Codex adapter tool table — do not hand-edit; regenerate -->
5c6
< Writ uses `.writ/` for specs and artifacts, `.codex/commands/*.md` for workflows, `.codex/agents/*.toml` for subagents, `.agents/skills/` for AgentSkills-format capabilities. Read bundled `system-instructions.md` for Writ identity; map tools via `adapters/codex.md`.
---
> Writ uses `.writ/` for specs and artifacts, `.codex/commands/*.md` for workflows, `.codex/agents/*.toml` for subagents, `.agents/skills/` for AgentSkills-format capabilities. Read bundled `system-instructions.md` for Writ identity; map tools with the Capability Map below.
7,8d7
< 
< 
15c14
< | `/writ` | `.codex/commands/writ.md` | Restate a request, route it to the fitting command, and run it with its … |
---
> | `/writ` | `.codex/commands/writ.md` | Restate a request, route it to the fitting command, and run it with its phases on the todo list. |
21c20
< | `/assess-spec` | `.codex/commands/assess-spec.md` | Analyze a specification for implementability risks before committing to … |
---
> | `/assess-spec` | `.codex/commands/assess-spec.md` | Analyze a specification for implementability risks before committing to build it. |
22a22
> | `/create-goal` | `.codex/commands/create-goal.md` | Interview for a recurring task and write a Goal Card with a checkable finish line, or record that a loop is the wrong tool. |
24,27c24,27
< | `/create-spec` | `.codex/commands/create-spec.md` | Create contract-first feature specifications with stories and verificati… |
< | `/edit-spec` | `.codex/commands/edit-spec.md` | Safely modify existing specifications while preserving contract integrit… |
< | `/knowledge` | `.codex/commands/knowledge.md` | Capture durable project knowledge as decisions, conventions, glossary te… |
< | `/plan-product` | `.codex/commands/plan-product.md` | Shape product strategy and roadmap artifacts through contract-first disc… |
---
> | `/create-spec` | `.codex/commands/create-spec.md` | Create contract-first specifications; --recommend autonomously authors and locks one package from evidence, then stops (does not implement). |
> | `/edit-spec` | `.codex/commands/edit-spec.md` | Safely modify existing specifications while preserving contract integrity. |
> | `/knowledge` | `.codex/commands/knowledge.md` | Capture durable project knowledge as decisions, conventions, glossary terms, or lessons. |
> | `/plan-product` | `.codex/commands/plan-product.md` | Shape product strategy and roadmap artifacts through contract-first discovery. |
29c29
< | `/verify-spec` | `.codex/commands/verify-spec.md` | Validate spec integrity, status sync, completion evidence, and contract … |
---
> | `/verify-spec` | `.codex/commands/verify-spec.md` | Validate spec integrity, status sync, completion evidence, and contract drift. |
36,38c36,39
< | `/create-uat-plan` | `.codex/commands/create-uat-plan.md` | Generate human-readable UAT plans from completed story details. |
< | `/implement-spec` | `.codex/commands/implement-spec.md` | Execute a specification through dependency-aware story batches. |
< | `/implement-story` | `.codex/commands/implement-story.md` | Run the full story SDLC pipeline from architecture check through documen… |
---
> | `/create-uat-plan` | `.codex/commands/create-uat-plan.md` | Generate deterministic implementation-derived UAT plans. |
> | `/implement-phase` | `.codex/commands/implement-phase.md` | Execute all specs in a roadmap phase — resolves features to specs, sequences by dependency, loops /implement-spec → /create-uat-plan per spec, and verifies exit criteria; --recommend runs it as an end-to-end loop that also autonomously authors missing specs. |
> | `/implement-spec` | `.codex/commands/implement-spec.md` | Execute dependency-aware story batches through the per-story pipeline; explicit execute command with no confirmation gate. |
> | `/implement-story` | `.codex/commands/implement-story.md` | Run the full story SDLC pipeline from architecture check through documentation. |
40a42
> | `/revert` | `.codex/commands/revert.md` | Safely unwind a story or spec via a layered commit resolver with plan-before-mutate guards. |
53c55
< | `/ship` | `.codex/commands/ship.md` | Take a green branch through merge preparation, commit intelligence, and … |
---
> | `/ship` | `.codex/commands/ship.md` | Take a green branch through commit intelligence and PR creation. |
59c61
< | `/security-audit` | `.codex/commands/security-audit.md` | Audit dependencies, secrets, code patterns, and infrastructure for secur… |
---
> | `/security-audit` | `.codex/commands/security-audit.md` | Audit dependencies, secrets, code patterns, and infrastructure for security risks. |
65c67
< | `/migrate` | `.codex/commands/migrate.md` | Migrate Code Captain projects to Writ while preserving existing artifact… |
---
> | `/migrate` | `.codex/commands/migrate.md` | Migrate Code Captain projects to Writ while preserving existing artifacts. |
73c75
< | `/new-skill` | `.codex/commands/new-skill.md` | Scaffold new Writ skills with the role convention enforced via boundary … |
---
> | `/new-skill` | `.codex/commands/new-skill.md` | Scaffold new Writ skills with the role convention enforced via boundary lint. |
76c78
< | `/status` | `.codex/commands/status.md` | Report current project state, active specs, in-flight work, and next act… |
---
> | `/status` | `.codex/commands/status.md` | Report current project state, active specs, in-flight work, and next actions. |
78c80
< | `/update-writ` | `.codex/commands/update-writ.md` | Update Writ from upstream with per-file control over local customization… |
---
> | `/update-writ` | `.codex/commands/update-writ.md` | Update Writ from upstream with per-file control over local customizations. |
84c86
< | `/retro` | `.codex/commands/retro.md` | Review agent transcripts and propose ranked environment fixes, never code. |
---
> | `/retro` | `.codex/commands/retro.md` | Review agent transcripts from a run and propose ranked fixes to the agent environment, never the code. |
86d87
< 
91,95c92,97
< | architecture-check-agent | `.codex/agents/architecture-check-agent.toml` | Pre-implementation design review that catches architecture risks bef… |
< | coding-agent | `.codex/agents/coding-agent.toml` | TDD implementation agent that writes code, follows conventions, and … |
< | documentation-agent | `.codex/agents/documentation-agent.toml` | Framework-adaptive documentation agent for feature, component, and a… |
< | review-agent | `.codex/agents/review-agent.toml` | Quality gate agent that verifies acceptance criteria, code quality, … |
< | testing-agent | `.codex/agents/testing-agent.toml` | Test and coverage agent that verifies pass rate, regressions, and co… |
---
> | architecture-check-agent | `.codex/agents/architecture-check-agent.toml` | Pre-implementation design review that catches architecture risks before coding. |
> | coding-agent | `.codex/agents/coding-agent.toml` | TDD implementation agent that writes code, follows conventions, and self-verifies. |
> | documentation-agent | `.codex/agents/documentation-agent.toml` | Framework-adaptive documentation agent for feature, component, and architecture docs. |
> | evaluator-agent | `.codex/agents/evaluator-agent.toml` | Fresh-context rubric agent that adjudicates acceptance criteria and recorded test results; residual architecture, security, and taste; never applies a patch. |
> | review-agent | `.codex/agents/review-agent.toml` | Quality gate agent that verifies acceptance criteria, code quality, tests, and drift. |
> | testing-agent | `.codex/agents/testing-agent.toml` | Test and coverage agent that verifies pass rate, regressions, and coverage thresholds. |
97c99
< | visual-qa-agent | `.codex/agents/visual-qa-agent.toml` | Optional UI validation gate that compares implementation screenshots… |
---
> | visual-qa-agent | `.codex/agents/visual-qa-agent.toml` | Optional UI validation gate that compares implementation screenshots against visual references. |
99d100
< 
103a105,107
> | `boundary-map-computation` | `.agents/skills/boundary-map-computation/SKILL.md` | Compute an owned / readable / out-of-scope file ownership map from tasks, imports, and overlap data. |
> | `change-surface-classification` | `.agents/skills/change-surface-classification/SKILL.md` | Classify a change set as style-only, single-component, cross-component, or full-stack. |
> | `code-explanation` | `.agents/skills/code-explanation/SKILL.md` | Explain existing code — its purpose, mechanics, context, and complexity — at a depth proportional to the target. |
104a109,120
> | `dependency-context-loading` | `.agents/skills/dependency-context-loading/SKILL.md` | Load, filter, and truncate upstream stories' implementation records into dependency context. |
> | `drift-triage` | `.agents/skills/drift-triage/SKILL.md` | Triage implementation deviations by severity and route each to amend, warn, or pause. |
> | `error-rescue-mapping` | `.agents/skills/error-rescue-mapping/SKILL.md` | Map a data-flow feature's failure modes into Error & Rescue, Shadow Path, and edge-case tables, flagging unplanned handling explicitly. |
> | `plain-prose` | `.agents/skills/plain-prose/SKILL.md` | Detect and rewrite mannered prose in instructional markdown — commands, agents, skills, adapters — into plain, direct text that keeps every rule, literal, and structure the file carries. |
> | `project-context-snapshot` | `.agents/skills/project-context-snapshot/SKILL.md` | Regenerate a whole-file project context snapshot from product, spec, drift, and issue sources. |
> | `safe-refactor-loop` | `.agents/skills/safe-refactor-loop/SKILL.md` | Change code structure without changing behavior — one verified, independently revertable commit per concern under a continuously green baseline. |
> | `story-commit-provenance` | `.agents/skills/story-commit-provenance/SKILL.md` | Record a completion commit SHA into a story file header idempotently and without amending it. |
> | `story-context-assembly` | `.agents/skills/story-context-assembly/SKILL.md` | Assemble the targeted context payload each pipeline agent receives — parsed hints, knowledge entries, and role-specific spec-lite sections. |
> | `subagent-result-completeness` | `.agents/skills/subagent-result-completeness/SKILL.md` | Tell a spawned gate agent's complete verdict apart from a mid-task stop, and recover when it stops early. |
> | `subagent-worktree-integration` | `.agents/skills/subagent-worktree-integration/SKILL.md` | Reconcile a spawned agent's isolated git worktree with the orchestrator's own checkout, and detect when that worktree is stale. |
> | `tdd-cycle` | `.agents/skills/tdd-cycle/SKILL.md` | Grow code test-first through the red → green → refactor cycle, one small unit of behavior at a time. |
> | `what-was-built-authoring` | `.agents/skills/what-was-built-authoring/SKILL.md` | Extract implementation facts from agent output and format them into a What Was Built record. |
106d121
< 
110a126
> ## Capability Map
111a128
> Commands name capabilities; this table maps them to this platform.
112a130,141
> | Capability | On this platform | When unavailable |
> |---|---|---|
> | `Task` | Subagent spawn with matching `sandbox_mode` | — |
> | `AskQuestion` | Structured numbered options in prose | — |
> | `codebase_search` | `Grep` / `Glob` / ripgrep via `Bash` | — |
> | `file_search` | `Glob("**/pattern*")` | — |
> | `read_file` | `Read(path)` | — |
> | `run_terminal_cmd` | `Bash(command)` | — |
> | `list_dir` | `Glob("pattern")` or `Bash("ls")` | — |
> | `todo_write` | `Write(".writ/state/...json")` | — |
> | `canvas-preview` | CLI: `Write` one self-contained HTML file per draft to `.writ/prototypes/<date>-<slug>/`. Desktop: the app's docs say it opens workspace files and has a browser, and do not document rendering an HTML draft; write the same files. | No renderer: write a structural description of each draft and say the drafts were not rendered. |
> | `Plan Mode` | No agent-side mode: run discovery as a read-only conversation and say so; Codex's `/plan` is user-side | If the platform has no toggle, say so and proceed read-only. |
```

Every dropped or changed sentence of the hand file, with its reason and verdict:

- Line 2 generator comment added (Rule 12) — intended.
- `## Writ on Codex`: "map tools via `adapters/codex.md`" → "map tools with the Capability Map below" (Rule 8, AC-3.2) — intended.
- Blank-line runs collapsed (hand lines 7–8, 86, 99, 106, and the four blank lines at 110–113 that now hold the map) — one blank line between sections — intended.
- 20 `…`-truncated cells (14 commands, 6 agents) replaced by the manifest purpose verbatim: 18 whose visible stem matched the manifest (`/writ`, `/assess-spec`, `/edit-spec`, `/knowledge`, `/plan-product`, `/verify-spec`, `/implement-story`, `/security-audit`, `/migrate`, `/new-skill`, `/status`, `/update-writ`; architecture-check-agent, coding-agent, documentation-agent, review-agent, testing-agent, visual-qa-agent) and 2 whose stem had also drifted from the manifest (`/create-spec`: "Create contract-first feature specifications with stories and verificati…" → the manifest's "--recommend" purpose; `/ship`: "…through merge preparation, commit intelligence, and …" → "…through commit intelligence and PR creation.") — the manifest is the source of truth and `SKILL.md` and `claude-code/CLAUDE.md` already carry the new text — intended.
- 3 complete hand sentences replaced because the manifest purpose changed after the hand edit: `/create-uat-plan` ("Generate human-readable UAT plans from completed story details." → "Generate deterministic implementation-derived UAT plans."), `/implement-spec` ("Execute a specification through dependency-aware story batches." → "Execute dependency-aware story batches through the per-story pipeline; explicit execute command with no confirmation gate."), `/retro` ("Review agent transcripts and propose ranked environment fixes, never code." → "Review agent transcripts from a run and propose ranked fixes to the agent environment, never the code.") — superseded purpose text, not still-true prose — intended.
- Additions, not losses: `/create-goal`, `/implement-phase`, `/revert`; `evaluator-agent`; 15 skills; the `## Capability Map` section — intended.
- Kept verbatim: line 1 (the merge-marker contract `install.sh`/`update.sh` read), the `## Writ on Codex` paragraph apart from the clause above, all 14 headings and table headers, the `conventional-commits` row, the built-ins paragraph (hand line 109) with its link, and the Catalog source paragraph (hand line 116).
- Bugs: none. No sentence that was still true is missing; nothing had to be re-rendered.

### Implementation Decisions

1. **Manifest read by a line-based reader mirrored from `gen-claude-md.py`** — copied `parse_value`, generalized to `categories:`, `commands:`, and `agents:`; every shape problem is a `manifest <detail>` `ValueError` so write mode fails closed. The driver therefore holds a second reader of the manifest; `scripts/_archival_hook_model.py` is the precedent if a shared module is wanted later.
2. **Skills from `skills/*/SKILL.md`, not the manifest's `skills:` list** — the spec requires every `SKILL.md`; the manifest list carries `status:` render mirrors.
3. **Generator comment names the Codex adapter tool table, not its path** — the only way to satisfy Rule 12 and AC-3.2's "no `adapters/` substring" together.
4. **Render-time guards** — an `adapters/` mention anywhere in the text or a render of 16384 bytes or more raises, so write mode prints `fail` and writes nothing instead of shipping a file an installed project cannot follow or Codex may truncate (DEV-007).
5. **Reason ownership when a manifest purpose is missing** — `gen-claude-md --check` reads the same manifest before `GENERATED` renders, so write mode reports `gen-claude-md: manifest <name> missing purpose`; the driver's own reader is exercised by the undeclared-category case, which only it detects.
6. **The Codex map has 10 rows** — `Task({ prompt, readonly })` is a single row in the Codex table, so the map carries no `Task` sub-row there.

### Test Results

**Verification:** Automated, test-first (`uv run --python 3.9 pytest scripts/tests/test_gen_platform_trees.py -q` red: 22 failed, 41 passed — `AttributeError` on the missing renderer and readers, the Story 2 write-shape assertions on the 18-file output; after implementation and before the first write: 62 passed, 1 failed (`test_codex_template_matches_committed`, hand file ≠ render), as designed; green: 63 passed).
**Coverage:** Not measured by the script (`test-integrity.py coverage`: unverifiable, no_coverage_report).

- ✅ Targeted: `uv run --python 3.9 pytest scripts/tests/test_gen_platform_trees.py scripts/tests/test_front_door.py scripts/tests/test_platform_neutral_names.py scripts/tests/test_gen_claude_md.py -q` → 159 passed (orchestrator's own run).
- ✅ Real tree: `python3 scripts/gen-platform-trees.py` → `pass`, `wrote cursor/writ.mdc`, `wrote codex/AGENTS.md.template`, 16 agent `wrote` lines, `wrote claude-code/CLAUDE.md`, `gen-platform-trees: pass (19 written, 0 reasons)`; only `codex/AGENTS.md.template` changed among generated files; a second run is byte-identical. `wc -c codex/AGENTS.md.template` → 12478; `grep -c 'adapters/'` → 0; `grep -ci ralph` → 0.
- ✅ Full pytest (3.9): 2876 passed, 2 skipped (144s).
- ✅ Bash tests: 45 run, 0 failed, including `test_merge_agents_md.sh`, the five `test_install_update_*.sh`, `test_manifest_shipped_baselines.sh`, and `test_update_codex_config_baseline.sh` (temp projects only; `install.sh`/`update.sh` never run against the repo).
- ✅ `bash scripts/eval.sh` (outside the sandbox): Findings 0, Run errors 0 (`.writ/state/eval-20261023-053327.md`); `check_ralph_retirement` and `check_broken_refs` pass on the generated template. The eval stale check for this file belongs to Story 4.
- ✅ `python3 scripts/ac-trace.py check --spec .writ/specs/2026-10-22-generated-platform-trees` → 0 findings.
- ✅ Gate 0 arch-check: pass (rederived proceed). Gate 2: no linter configured; arch-lint: none — see .writ/docs/architecture-lint.md; build-smoke unverifiable (unsupported_stack). Gate 2.5: cross-component, 0 crossings, route evaluator-agent. Gate 3 review-override: pass. Gate 3.5 drift-format: pass. Gate 4 coverage: unverifiable (no_coverage_report); authenticity: pass. Gate 4.5 app-verify: unverifiable (no_recipe). Gate 5 docs-check: unverifiable (no_public_exports).

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small (DEV-007)
- **Security:** None (reads repo files only; atomic temp-file write preserving mode; no network)
- **Boundary Compliance:** the three changed files are owned; no deviation, no violation.
- gate3-route: evaluator-agent. review-panel: unverifiable (platform_cannot_spawn_other_vendors). jev-shadow: unverifiable (no_api_key). arch-lint: none — see .writ/docs/architecture-lint.md.
- Evaluator reproduced the takeover diff line by line against this record, confirmed line 1 byte-identical to HEAD (`cmp`), re-ran the 159 targeted tests and `test_merge_agents_md.sh`. Residuals, not drift: the driver's manifest reader duplicates `gen-claude-md.py`'s (two readers of one file with different error surfaces); the size guard's message says "exceeds" at exactly 16384 bytes; the `adapters/` guard is a whole-text match whose message names no source line; `adapters/codex.md:416` still says the template should stay at or under 8192 bytes (adapter prose outside the tool tables is scoped out of this spec; Story 5 edits only the install sections — left for an issue if it matters).
- Coding agent and evaluator ran as nested `general-purpose` spawns with the prompt templates from `agents/coding-agent.md` and `agents/evaluator-agent.md`, working directly in the lane worktree.

### Deviations from Spec

- **[DEV-007] Render-time guards beyond the spec's shadow paths** — Severity: Small
  - Spec said: "no `adapters/` mention" and "under 16 KiB" are output properties enforced by `test_codex_template`; the shadow paths list only the nil, empty, and upstream cases.
  - Reality: the renderer raises on either condition so write mode fails closed and writes nothing; a missing `skills/` directory is `unverifiable`.
  - Resolution: Auto-amended; spec-lite.md generated-files line names the guards.
