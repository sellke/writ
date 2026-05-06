# Story 2: Codex TOML Agent Translations & Parity Lint

> **Status:** Complete ✅
> **Priority:** High
> **Dependencies:** Story 1
> **Estimated Effort:** Medium

## User Story

**As a** Writ contributor,
**I want to** create native Codex TOML translations of all seven Writ agents and a parity lint that catches drift between platform variants,
**So that** Codex users get full multi-agent SDLC pipeline parity with Cursor and Claude Code (parallel spawning, sandbox enforcement) without depending on prompt-only role conventions, and contributors get an early signal when an agent edit lands in only one platform.

## Acceptance Criteria

### Scenario 1: Seven TOML files exist with required fields and correct sandbox modes
- **Given** the Writ source repo at HEAD has `agents/architecture-check-agent.md`, `agents/coding-agent.md`, `agents/review-agent.md`, `agents/testing-agent.md`, `agents/documentation-agent.md`, `agents/user-story-generator.md`, `agents/visual-qa-agent.md`
- **When** I list `codex/agents/*.toml`
- **Then** seven files exist (one per agent), each containing the required keys `name`, `description`, `developer_instructions`, plus a `sandbox_mode` value matching the spec's mapping table (`read-only` for architecture-check / review / visual-qa; `workspace-write` for coding / testing / documentation / user-story-generator)

### Scenario 2: `developer_instructions` content matches the source agent body
- **Given** a source file `agents/<name>.md` with optional YAML frontmatter
- **When** I extract the body (everything after the closing `---` of frontmatter, or the whole file if no frontmatter) and compare it against `developer_instructions` in `codex/agents/<name>.toml`
- **Then** the bodies are byte-equivalent (modulo TOML triple-quote escaping rules); no role drift, no paraphrasing, no truncation

### Scenario 3: `.codex/agents/` is symlinked to `codex/agents/` on the Writ repo
- **Given** the Writ repo's self-dogfooding pattern (`.cursor/` and `.claude/` symlink to product source)
- **When** I run `ls -la .codex/agents` from the repo root
- **Then** `.codex/agents` resolves to the repo-root `codex/agents/` directory, the seven `.toml` files are visible through the symlink, and `AGENTS.md` reflects this in its symlink table

### Scenario 4: Parity lint exits 0 on a complete agent set
- **Given** the full set of seven agents is present in `agents/`, `claude-code/agents/`, and `codex/agents/` (subject to the documented exclusion list for any legitimately platform-specific agents)
- **When** I run `/refresh-command --check-parity`
- **Then** the command reports `parity OK` (or equivalent), emits no warnings, and exits 0

### Scenario 5: Parity lint warns (but does not fail) when a counterpart is missing
- **Given** I temporarily delete `codex/agents/review-agent.toml` (and the agent is not on the exclusion list)
- **When** I run `/refresh-command --check-parity`
- **Then** the output contains a warning of the form `⚠️ agents/review-agent.md has no counterpart in codex/agents/`, the exit code is **0** (warning, not failure), and no other behavior of `/refresh-command` is affected when `--check-parity` is absent

### Scenario 6: Codex picker discovers the installed TOMLs
- **Given** a Codex CLI session opened in a project with `.codex/agents/*.toml` populated (manual smoke gate; not blocking CI)
- **When** the user runs `/agent` (or the equivalent picker invocation)
- **Then** the seven Writ agents appear by `name`, each with the correct `description` preview, and selecting one loads the `developer_instructions` content as the agent's role prompt

## Implementation Tasks

- [x] **2.1 Parity-lint test fixture:** Create a small fixture (or document the manual reproduction steps) that exercises both states — full set passes, one-deleted state warns. Used to validate the lint logic implemented in 2.5.
- [x] **2.2 Author seven TOML files:** Write `codex/agents/architecture-check-agent.toml`, `coding-agent.toml`, `review-agent.toml`, `testing-agent.toml`, `documentation-agent.toml`, `user-story-generator.toml`, `visual-qa-agent.toml` per the schema in `sub-specs/technical-spec.md` (required fields + `sandbox_mode` from the mapping table). Lift `description` from `.writ/manifest.yaml`'s `agents[].purpose` to keep a single source-of-truth.
- [x] **2.3 Verify body equivalence:** Confirm each TOML's `developer_instructions` is byte-equivalent to the body of `agents/<name>.md` (excluding YAML frontmatter). Use a one-shot diff script if one already exists; otherwise eyeball-diff and document the technique used.
- [x] **2.4 Self-dogfood symlink:** Create `.codex/agents/` → `codex/agents/` on the Writ repo (relative symlink, mirroring `.cursor/` and `.claude/` patterns). Update `AGENTS.md`'s "Active installation" table to include `.codex/` alongside `.cursor/` and `.claude/`.
- [x] **2.5 Extend `commands/refresh-command.md`:** Add a `--check-parity` flag/mode that lints all three agent format folders (`agents/`, `claude-code/agents/`, `codex/agents/`) for cross-platform parity. Warnings only (exit 0). Document the exclusion list mechanism (where agents legitimately platform-specific — e.g., `visual-qa-agent` if it has no Claude variant — can be exempted with rationale). Existing `/refresh-command` behavior must be unchanged when `--check-parity` is absent.
- [x] **2.6 Run the lint:** Execute `/refresh-command --check-parity` against the full set, verify exit 0, and capture the output for the Definition of Done. Then temporarily delete one TOML, re-run, verify the warning appears and exit code remains 0; restore.
- [x] **2.7 Resolve `model: "fast"` IDs:** For agents whose source declares `model: "fast"`, look up Codex's current fast-tier model ID (via `codex --help`, the `/model` picker, or upstream docs at implementation time), document the chosen IDs in this story's "What Was Built" section, and add a note in `adapters/codex.md` (Story 3 will own that file; coordinate or stage the note). If the adapter file isn't yet authored, record the IDs here and pass them forward.
- [x] **2.8 Verify acceptance criteria:** Walk through Scenarios 1–5 explicitly; capture Scenario 6 as a manual smoke (deferred to Story 7 if no Codex CLI is locally available).

## Notes

- **Drift risk between three formats is structural, not eliminable.** `agents/*.md`, `claude-code/agents/*.md`, and `codex/agents/*.toml` are independent files describing the same role concept. The parity lint catches *missing* counterparts and surface-level naming drift; it cannot catch *content* drift where, e.g., the Cursor body says "iterate up to 3 times" and the Codex `developer_instructions` says "iterate up to 5 times". Writers must keep platform variants in sync manually. This is the cost of supporting platforms with genuinely different native formats — accepted in the spec's Technical Concerns section.
- **Sandbox-mode mapping is opinionated.** The decisions (architecture-check / review / visual-qa = `read-only`; coding / testing / documentation / user-story-generator = `workspace-write`) are documented in `sub-specs/technical-spec.md`'s Sandbox mode mapping table. If implementation reveals a problem (e.g., the documentation agent legitimately needs to install a doc-generator dependency and `workspace-write` is too restrictive), surface it as a story-level deviation rather than silently changing the mapping.
- **Model ID resolution is a moving target.** `model: "fast"` in Cursor is a tier alias; Codex requires concrete model IDs. The exact ID at the time of authoring (e.g., `gpt-5.4-mini` or whatever the current fast tier is) needs runtime verification. Document the chosen IDs and recommend users override based on their plan in `adapters/codex.md` once that file lands.
- **Claude variants use a `writ-` prefix naming convention.** As of HEAD, `claude-code/agents/` contains six files (`writ-architect.md`, `writ-coder.md`, `writ-reviewer.md`, `writ-tester.md`, `writ-documenter.md`, `writ-story-gen.md`) and notably no `writ-visual-qa.md`. The parity lint must understand the name-mapping (or rely on a manifest-driven mapping) and should either (a) flag `visual-qa-agent` as missing from Claude with a recommended exclusion-list addition, or (b) ship with `visual-qa-agent` already on the exclusion list. Pick the option that produces the clearest contributor signal; document the decision.
- **`--check-parity` is opt-in for this story.** The spec defers the question of whether parity should run by default until after a month of real-world drift signal (Open Implementation Question 2). Don't bake it into the default `/refresh-command` flow yet.

## Definition of Done

- [x] Seven `codex/agents/*.toml` files exist, each with required fields and the spec's sandbox_mode value
- [x] `developer_instructions` content is byte-equivalent to source agent bodies (verified per agent)
- [x] `.codex/agents/` symlink exists on the Writ repo and resolves to `codex/agents/`
- [x] `AGENTS.md` symlink table updated to include `.codex/`
- [x] `commands/refresh-command.md` extended with `--check-parity` flag; existing flow unchanged when flag absent
- [x] Documented exclusion-list mechanism (in `commands/refresh-command.md` or a referenced doc) for legitimately platform-specific agents
- [x] `/refresh-command --check-parity` exits 0 on the full set; exits 0 with a clear warning when one TOML is removed
- [x] All Scenario 1–5 acceptance criteria pass; Scenario 6 captured as a deferred smoke gate (or executed if Codex CLI is locally available)
- [x] Self-review: TOML files diff-clean against source bodies; lint code is purely additive to `/refresh-command`; no regressions to commands or agents fanout

## What Was Built (Story 2)

- **Fast-tier model IDs in TOML:** `gpt-5-mini` for `architecture-check-agent` and `user-story-generator` (manifest `model: fast`). Confirm via `/model` on your Codex CLI and override in TOML if your workspace uses different IDs.
- **Claude parity gap:** `visual-qa-agent` is exempt from requiring `claude-code/agents/` (documented in `commands/refresh-command.md` Phase 6).
- **Regeneration:** `python3 scripts/gen-codex-agent-tomls.py` reproduces all `codex/agents/*.toml` bodies from canonical `agents/*.md`.

## Context for Agents

- **Coding agent context:**
  - **Error map rows:** `/refresh-command --check-parity → Missing TOML for an agents/*.md agent` row from `sub-specs/technical-spec.md` (warning, exit 0).
  - **Shadow paths:** None — this story does not touch install/update flows.
  - **Business rules:** "Codex agent source-of-truth" (sandbox-mode mapping, required TOML fields, optional `model` and `nickname_candidates`); "Self-dogfooding" (`.codex/agents/` symlink); "Drift sanity check" (warnings-only, exclusion list); "No command renames" (do not rename `/refresh-command` or its existing flags).
  - **Experience:** None — this story is contributor-facing, not user-facing.
  - **Reference files:** `agents/*.md` (source bodies), `.writ/manifest.yaml` (`agents[].purpose` → TOML `description`), `claude-code/agents/*.md` (frontmatter reference for what fields translate to Codex equivalents), `commands/refresh-command.md` (extension target).

- **Review agent context:**
  - **Spec sections:** spec.md → `## Specification Contract → Business Rules → Codex agent source-of-truth, Self-dogfooding, Drift sanity check`. spec.md → `## Success Criteria` items 2 (TOML count + sandbox values), 7 (parity lint active and verifiable).
  - **Boundary check:** This story owns `codex/agents/*.toml`, `.codex/agents/` (symlink), `commands/refresh-command.md` extension, and the symlink-table line in `AGENTS.md`. Should *not* touch `scripts/install.sh`, `adapters/codex.md`, or any other Story 3+ files.

- **Testing agent context:**
  - **Spec sections:** sub-specs/technical-spec.md → `## TOML Translation Schema` (verify field mapping per row), `## Error & Rescue Map` (lint row: warning, exit 0), `## Test Plan → Regression coverage` (parity lint full set + missing TOML).
  - **Test focus:** Acceptance Scenarios 1, 2, 4, 5 are mechanically verifiable; Scenario 3 is filesystem-level; Scenario 6 is a manual smoke gate. No new bash unit tests required for this story (those land in Story 4 with the install script changes).

- **Documentation agent context:**
  - **Spec sections:** spec.md → `## Detailed Requirements` (file inventory). When `adapters/codex.md` is authored in Story 3, the model ID resolutions captured in this story's "What Was Built" must propagate forward.
