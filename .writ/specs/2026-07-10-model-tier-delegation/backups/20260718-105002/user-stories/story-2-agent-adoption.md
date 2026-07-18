# Story 2: Agent Adoption

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1
> **Estimated Effort:** Small

## User Story

**As a** Writ maintainer,
**I want** all 7 agents to declare an explicit `model_tier` in frontmatter and `manifest.yaml`, mapped from today's ad-hoc `model:` settings,
**So that** model intent is portable and consistent across agents — without changing the concrete model any agent actually runs on.

## Acceptance Criteria

### Scenario 1: Every agent declares a tier
- **Given** the `model_tier` convention from Story 1
- **When** I run `rg "model_tier:" agents/`
- **Then** all 7 agents return exactly one `model_tier` value, each `orchestration` or `capability`

### Scenario 2: Frontmatter and manifest agree
- **Given** each agent has a frontmatter tier and a `manifest.yaml` entry
- **When** I compare the two per agent
- **Then** every agent's frontmatter `model_tier` matches its `manifest.yaml` `model_tier`

### Scenario 3: No behavioral regression
- **Given** the mapping (`fast` → `capability`, `default`/`inherit` → `orchestration`)
- **When** I resolve each agent's tier through the adapter table
- **Then** each agent resolves to the **same concrete model it runs today**: `architecture-check-agent` and `user-story-generator` at the floor/fast model; the other five at inherit/anchor

### Scenario 4: Concrete overrides preserved
- **Given** Codex requires concrete model IDs for some agents
- **When** I inspect the manifest / adapter mapping
- **Then** any concrete `model:` override is preserved and documented as taking precedence over `model_tier:`

## Implementation Tasks

- [ ] **Map tiers:** Apply the spec's mapping table — `capability`: `architecture-check-agent`, `user-story-generator`; `orchestration`: `coding`, `review`, `testing`, `documentation`, `visual-qa`.
- [ ] **Update agent frontmatter:** Add `model_tier:` to each of the 7 `agents/*.md` files.
- [ ] **Update `manifest.yaml`:** Add `model_tier:` to each agent entry; decide per-agent whether to retain `model:` (keep only where a concrete override is genuinely needed, e.g. Codex IDs) or drop it in favor of the tier.
- [ ] **Document precedence:** Where both `model:` and `model_tier:` remain, add a note that `model:` wins.
- [ ] **Regression check:** Produce the tier→concrete-model resolution walkthrough proving no agent changes its effective model.
- [ ] **Consistency check:** Verify frontmatter tier == manifest tier for all 7 agents.

## Definition of Done

- [ ] All four acceptance criteria pass
- [ ] All 7 agents declare `model_tier` in both frontmatter and `manifest.yaml`, values consistent
- [ ] Documented resolution walkthrough shows zero change in each agent's concrete model vs. today
- [ ] No adapter files modified in this story (resolution tables are Story 3; this story consumes today's mapping semantics)
- [ ] Self-review: mapping is conservative (rename-to-portable), no agent silently upgraded/downgraded

## Technical Notes

- This is a **rename-to-portable, not a behavior change.** The whole point is that the resolved model is identical to today — only the vocabulary becomes portable.
- `visual-qa-agent` is `inherit` today; `orchestration` maps to inherit/anchor, so it keeps its behavior.
- If Story 3 runs in parallel, coordinate on the resolution table: this story asserts the *mapping intent*; Story 3 documents the *platform resolution*. They must agree.

## Context for Agents

- **Coding agent context:** spec.md → `## Implementation Approach → ### Agent adoption mapping`; current values in `.writ/manifest.yaml` (lines defining each agent's `model:`).
- **Review agent context:** spec.md → Success Criteria #1, #2. The critical check is Scenario 3 (no regression) — verify every agent resolves to its current model.
- **Testing agent context:** `rg "model_tier:|model:" agents/ .writ/manifest.yaml`; build the 7-row tier→model table and confirm against the "today" column in spec.md's mapping table.
