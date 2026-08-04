# Story 4: Authoring & Lint Integration + Docs

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Stories 1, 2, 3
> **Estimated Effort:** Small

## User Story

**As a** Writ contributor scaffolding a new command, agent, or skill,
**I want** the authoring commands to scaffold an (appropriately advisory) `model_tier` field and the lint to validate tier values,
**So that** the convention is discoverable at authoring time and malformed tiers are caught before they ship — with a canonical explainer to point to.

## Acceptance Criteria

### Scenario 1: `/new-command` and `/new-skill` scaffold `model_tier`
- **Given** the `model_tier` convention exists
- **When** I scaffold a new command or skill
- **Then** the generated frontmatter includes a `model_tier:` field with an inline `# advisory only` comment (because commands/skills can't enforce a model)

### Scenario 2: Lint validates tier values
- **Given** `scripts/lint-skill.sh` (and the shared frontmatter validation)
- **When** a file declares `model_tier: banana`
- **Then** lint rejects it with: "model_tier 'banana' is invalid. Use 'orchestration', 'capability', or a reserved negative offset (e.g. -1)." — and accepts `orchestration`, `capability`, and `-1`

### Scenario 3: Canonical explainer exists
- **Given** the convention needs a user-facing home
- **When** I read `.writ/docs/model-tiers.md`
- **Then** it explains the two tiers, the agent-enforced / command-skill-advisory boundary, native relative resolution, graceful degradation, and reserved ordinal offsets — using the verb/noun/tool framing

### Scenario 4: Root docs reference the convention
- **Given** `README.md` and `AGENTS.md` describe agents and model behavior
- **When** I read them
- **Then** each references the `model_tier` convention / `.writ/docs/model-tiers.md` where model or agent behavior is discussed

### Scenario 5: Advisory framing is unmistakable
- **Given** command/skill tier is advisory
- **When** I read any scaffold output, the explainer, and the lint help
- **Then** "advisory only (commands/skills run at the session/caller model)" appears wherever command/skill tier is mentioned

## Implementation Tasks

- [ ] **`/new-skill` scaffold:** Add `model_tier:` (advisory) with inline comment to the generated skill frontmatter.
- [ ] **`/new-command` scaffold:** Add `model_tier:` (advisory) with inline comment to the generated command frontmatter.
- [ ] **Lint value check:** Extend `scripts/lint-skill.sh` (and shared frontmatter validation used by `/new-skill` / `/refresh-command` / `/new-command`) to validate `model_tier` against `^(orchestration|capability|-[0-9]+)$` with a clear remediation message.
- [ ] **Write `.writ/docs/model-tiers.md`:** Canonical explainer with verb/noun/tool framing, resolution/degradation summary, and reserved-offset note.
- [ ] **Root doc references:** Link the convention from `README.md` and `AGENTS.md` where agent/model behavior is described.
- [ ] **Advisory wording sweep:** Ensure the advisory framing is consistent across scaffolds, docs, and lint output.

## Definition of Done

- [ ] All five acceptance criteria pass
- [ ] `/new-command` and `/new-skill` scaffold an advisory `model_tier:` field
- [ ] Lint rejects invalid `model_tier` values and accepts valid ones (verified with a bad + good input)
- [ ] `.writ/docs/model-tiers.md` exists; `README.md` and `AGENTS.md` reference it
- [ ] Advisory framing consistent everywhere command/skill tier appears
- [ ] Self-review: lint change is minimal bash, no new dependency; explainer opens with the same verb/noun/tool words ADR-009 uses

## Technical Notes

- **Reuse, don't fork, the lint.** Add tier validation to the existing shared lint path so `/new-skill`, `/new-command`, and `/refresh-command` all get it. Mirror the skills-foundation approach (`scripts/lint-skill.sh` shared by `/new-skill` and `/refresh-command`).
- **Advisory comment is written, not lint-enforced.** `/new-*` always emits the `# advisory only` comment; lint doesn't fail if a hand-authored file omits it (it's documentation, not a hard rule).
- **Explainer mirrors `.writ/docs/skills.md`.** Same shape and tone as the skills explainer for consistency.

## Context for Agents

- **Coding agent context:** technical-spec.md → §5 (lint) and §6 (documentation surfaces). Existing patterns: `scripts/lint-skill.sh`, `commands/new-skill.md`, `commands/new-command.md`, `.writ/docs/skills.md`.
- **Review agent context:** spec.md → Success Criteria #5, #7. Verify advisory framing is unmistakable and lint covers the invalid-value path.
- **Testing agent context:** feed lint `model_tier: banana` (reject) and `model_tier: capability` / `-1` (accept); confirm `.writ/docs/model-tiers.md` exists and root docs link it (`rg "model-tiers" README.md AGENTS.md`).
