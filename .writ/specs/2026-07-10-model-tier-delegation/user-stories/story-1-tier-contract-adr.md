# Story 1: Tier Contract + ADR-014

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None
> **Estimated Effort:** Small

## User Story

**As a** Writ contributor authoring agents, commands, or skills,
**I want** a documented, portable `model_tier` frontmatter convention with a recorded architectural decision behind it,
**So that** I can express model-weight intent once, in one obvious place, and downstream adapters resolve it consistently without me hardcoding platform model names.

## Acceptance Criteria

### Scenario 1: `model_tier` convention documented in `system-instructions.md`
- **Given** ADR-009 defines the verb/noun/tool boundary but says nothing about model tiers
- **When** I read `system-instructions.md`
- **Then** there is a section documenting `model_tier` with: the two named tiers (`orchestration`, `capability`), the enforcement boundary (agents enforced; commands/skills advisory only), the reserved ordinal-offset form, and graceful-degradation semantics

### Scenario 2: Schema is unambiguous
- **Given** the convention is documented
- **When** I read the schema definition
- **Then** it specifies: (a) allowed values `orchestration` / `capability` / reserved negative ordinal, (b) unset = inherit parent/default, (c) explicit `model:` overrides `model_tier:`, (d) unknown/unhonorable tier warns and falls back (never hard-fails), (e) command/skill tier is advisory-only and cannot select a model

### Scenario 3: `cursor/writ.mdc` parity
- **Given** Phase 4 parity discipline requires the two root behavioral files to agree
- **When** I `diff` the tiering content between `system-instructions.md` and `cursor/writ.mdc`
- **Then** the tiering sections are byte-identical

### Scenario 4: ADR-014 records the decision
- **Given** the design corrects the originating issue's skill-carrier framing
- **When** I read `.writ/decision-records/adr-014-model-tier-delegation.md`
- **Then** it records the decision (agent-as-carrier, relative-not-absolute, staged 2-band-now/N-step-reserved resolver) and lists considered alternatives (skill-carrier, absolute tiers, full maintained ranking) with rejection rationale

### Scenario 5: Reserved ordinal offsets marked reserve-only
- **Given** the ordinal-offset form is documented but not resolved beyond 2 bands
- **When** I read the convention
- **Then** it is explicitly marked reserve-only with a review trigger, and states resolution is 2-band today (deeper steps clamp to floor)

## Implementation Tasks

- [ ] **Schema design:** Finalize the `model_tier` grammar (`orchestration` | `capability` | `-N`), precedence vs `model:`, unset behavior, and graceful-degradation contract.
- [ ] **`system-instructions.md` section:** Add a `## Model Tiers` section near the `required_skills:` convention documenting tiers, enforcement boundary, advisory-for-commands/skills, reserved ordinal offsets, and degradation.
- [ ] **`cursor/writ.mdc` mirror:** Insert byte-identical tiering content; verify via `diff`.
- [ ] **Write ADR-014:** `.writ/decision-records/adr-014-model-tier-delegation.md` with Decision, the three considered alternatives + rejection rationale, and Consequences.
- [ ] **Reserve-only note + review trigger:** Document ordinal offsets as reserve-only with a dated review trigger (mirror the `required_skills:` 90-day pattern).
- [ ] **Cross-reference ADR-009:** Cite the skills-don't-spawn-agents rule as the grounding for agent-as-carrier.

## Definition of Done

- [ ] All five acceptance criteria pass
- [ ] `model_tier` convention documented in `system-instructions.md` and `cursor/writ.mdc` (byte-identical tiering content, verified via `diff`)
- [ ] ADR-014 exists with decision + alternatives + consequences
- [ ] Zero agents/commands/skills modified in this story (contract + docs only; adoption is Story 2)
- [ ] Self-review: schema follows existing frontmatter discipline (additive, simple values, graceful degradation) and matches the `required_skills:` reserve-only precedent

## Technical Notes

- **Why agent-as-carrier:** the `model` parameter only exists at the agent spawn boundary (`Task({ model })`, `sessions_spawn`, Codex TOML). A skill is loaded text; a command runs at the user's session model. Enforced tier on either is inert. See spec.md → Technical Decisions.
- **Why reserve the ordinal form now:** the real 4-level orchestration nest (`/implement-phase` → spec-runner → `/implement-story` → agents) may eventually want per-level step-down, but platforms expose ~3 bands so deeper steps clamp. Declaring the vocabulary now (inert until the ranking story) mirrors `required_skills:`.
- **Keep it additive.** No breaking changes; unset `model_tier` = today's behavior.

## Context for Agents

- **Coding agent context:** spec.md → `## Implementation Approach → ### Frontmatter contract`; technical-spec.md → §1 (schema) and §3 (degradation). Model the reserve-only note on `2026-05-03-skills-foundation` Story 5.
- **Review agent context:** spec.md → Business Rules (enforcement boundary; advisory-only). Verify zero agent/command/skill files change in this story's diff. Confirm `diff` parity of the two root files.
- **Testing agent context:** `diff <(sed -n '/## Model Tiers/,/^## /p' system-instructions.md) <(sed -n '/## Model Tiers/,/^## /p' cursor/writ.mdc)` for parity; `rg "model_tier" agents/ commands/ skills/` must return zero this story.
