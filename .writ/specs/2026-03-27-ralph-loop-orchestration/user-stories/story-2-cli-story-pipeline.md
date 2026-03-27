# Story 2: CLI-Adapted Story Pipeline

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ developer
**I want** a `PROMPT_build.md` template and supporting docs that tell a CLI agent (Claude Code) how to run one Writ story through a simplified gate pipeline (code → test → lint → state update → commit) with test/lint back pressure and a clear state-write protocol
**So that** after planning in Cursor I can hand off autonomous execution to the CLI and still get shippable increments, traceable state, and Phase 3a-style continuity (spec-lite, context hints, “What Was Built”) within a single agent context per iteration

## Acceptance Criteria

- [ ] **Given** a targeted story file and project `.writ/config.md`, **when** a CLI agent follows `PROMPT_build.md`, **then** it loads the story and relevant spec context (including spec-lite and context hints from Phase 3a) before writing code
- [ ] **Given** implementation work in progress, **when** the CLI pipeline runs, **then** it enforces **code → test → lint → state update → commit** in that order, and does not commit until tests and lint (including typecheck if configured as lint) succeed
- [ ] **Given** failing tests or lint, **when** the inner fix loop runs, **then** the agent fixes and retries up to **3** attempts; on exhaustion it stops without a success commit, records failure per the state protocol (Story 1), and does not mask environment-level failures as ordinary code defects
- [ ] **Given** a completed story iteration, **when** the pipeline finishes successfully, **then** the agent appends or updates the story file with a **“What Was Built”** record consistent with Phase 3a expectations, updates the Ralph state file per the documented protocol, and creates a **single** descriptive commit for that story
- [ ] **Given** `.writ/docs/ralph-cli-pipeline.md`, **when** a maintainer reads it, **then** they can map CLI gates to the Cursor-native `/implement-story` gates, understand back pressure and the fix loop, and wire commands from `.writ/config.md` without reading the full spec

## Implementation Tasks

- [x] 2.1 Define a **verification matrix** (Given/When/Then scenarios) for `PROMPT_build.md`: gate order, max-3 fix loop, no-commit-on-failure, state write ordering, WWB generation, and environment-failure stop — use it as the acceptance test for this story (no automated test suite in repo)
- [x] 2.2 Author **`scripts/PROMPT_build.md`** (build-mode template): numbered instructions, Ralph-style **“999…”** guardrails, explicit loads (story, spec-lite, technical spec if present, `.writ/config.md` test/lint commands), inner fix loop cap, and final **state update → commit** sequence; align tone and structure with `adapters/claude-code.md` (subagents, YAML frontmatter, worktrees) where applicable
- [x] 2.3 Document the **state update protocol** in **`/.writ/docs/ralph-cli-pipeline.md`**: which iteration fields to set, atomicity expectations, how to merge with existing `ralph-*.json` from Story 1’s format doc (`/.writ/docs/ralph-state-format.md`), and what to log on success vs. attempted-failed vs. blocked paths (cross-link spec **Error Experience**)
- [x] 2.4 In **`/.writ/docs/ralph-cli-pipeline.md`**, add a **gate mapping table**: Cursor pipeline (arch-check → … → docs) vs. CLI pipeline (code → test → lint → state → commit), plus how Context Engine artifacts (spec-lite sections, context hints, WWB) are consumed in CLI mode
- [x] 2.5 Update **`adapters/claude-code.md`** with a **Ralph / CLI story pipeline** subsection: when to use `PROMPT_build.md`, how it differs from supervised `/implement-story`, and pointers to `ralph-cli-pipeline.md` and `ralph-state-format.md`
- [x] 2.6 Add **Story sizing and context** guidance to `ralph-cli-pipeline.md` (or a short subsection): staying within one CLI context window per story; reference spec risks (oversized stories) and `.writ/config.md` conventions
- [x] 2.7 **Verify** using the matrix from 2.1: dry-walk a sample story through the written prompt and docs; confirm cross-links, command placeholders, and Story 1 state field names match; update `spec-lite.md` or command references only if required for consistency (minimal diff)

## Notes

**Technical considerations:**

- **Single context window:** The prompt must batch loads and avoid redundant full-spec dumps; prefer spec-lite + resolved context hints over pasting entire `spec.md` unless the hint requires it.
- **Back pressure:** Treat typecheck as part of “lint” when `.writ/config.md` defines it that way; the prompt should instruct the agent to run the **exact** commands from config, not invented shortcuts.
- **Atomic story:** Match spec **Business Rules → One Story Per Iteration** — partial application without state update is a failure mode to describe explicitly in the prompt.
- **WWB:** Phase 3a records should be produced after success; align section headings with `commands/implement-story.md` / existing story examples so downstream tooling can find them.

**Integration points:**

- **Story 1:** State file JSON shape and field semantics are authoritative; this story only defines *when* and *how* the CLI writes them during the pipeline.
- **`/ralph plan` (later stories):** May materialize or copy `PROMPT_build.md` into the project root or handoff folder; keep the template self-contained so generation is trivial string substitution.
- **Context Engine:** Consume `spec-lite.md` and story **Context for Agents** the same way the Cursor orchestrator conceptually does, without requiring Cursor tools.

**Risks:**

- **Prompt drift:** Mitigate with numbered steps, guardrails, and the verification matrix.
- **Environment vs. code failures:** Misclassification can cause infinite retries or premature block — document heuristics (e.g., missing binary, sandbox denial) in `ralph-cli-pipeline.md`.
- **Oversized stories:** Spec already flags risk; the prompt should tell the agent to fail fast with a clear “context/size exceeded” diagnostic if it cannot complete within one iteration.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Verification matrix executed (dry-walk or equivalent) with no blocking gaps
- [ ] `PROMPT_build.md`, `ralph-cli-pipeline.md`, and `adapters/claude-code.md` cross-reference each other and Story 1 state docs
- [ ] Documentation reviewed for consistency with `spec.md` (nested loops, back pressure, error experience)
- [ ] Ready for Story 3+ to wire `ralph.sh` and loop orchestration against the same artifacts

## Context for Agents

- **Error map rows:** Story failure once → “attempted-failed,” continue eligible work — see `spec.md` → **Experience Design → Error Experience** (story fails once). Story fails repeatedly (3+) → “blocked” + diagnostics — same section. Environment broken → stop loop — same section. Inner fix loop cap — **Architecture: Three Nested Loops** (fix loop, max 3).
- **Shadow paths:** CLI happy path — **Experience Design → Happy Path Flow** steps 6–8 (CLI loop, state updates, monitoring). Story pipeline success — **Architecture** diagram (story level: code → test → lint → commit). Failure path — **Error Experience** (failed iteration, skip/defer, escalation).
- **Business rules:** One story per iteration; story atomic success/fail — **Business Rules → One Story Per Iteration**. Back pressure from tests/lint/type — **Architecture** (story pipeline) and **Contract Summary / Must Include**. CLI vs. Cursor separation — **Business Rules → Platform Separation** and **Relationship to Other Commands**. State as source of truth — **Business Rules → State as Single Source of Truth**.
- **Experience:** Feedback via state file + git commits — **Experience Design → Feedback Model**. Moment of truth (walk away, return to review) — **Moment of Truth**. State catalog for empty/planned/executing — **State Catalog**.
