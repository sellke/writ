# Story 2: Agent Adoption

> **Status:** Completed ✅ (2026-07-18)
> **Priority:** High
> **Dependencies:** Story 1
> **Estimated Effort:** Small

## User Story

**As a** Writ maintainer,
**I want** all 7 agents to declare an explicit `model_tier` in their Agent Configuration block and `manifest.yaml`, mapped from today's ad-hoc `model:` settings,
**So that** model intent is portable and consistent across agents — without changing the concrete model any agent actually runs on.

## Acceptance Criteria

### Scenario 1: Every agent declares a tier
- **Given** the `model_tier` convention from Story 1
- **When** I run `rg "model_tier:" agents/`
- **Then** all 7 agents return exactly one `model_tier` value, each `orchestration` or `capability`

### Scenario 2: Agent Configuration block and manifest agree
- **Given** each agent has a tier declared in its Agent Configuration block and a `manifest.yaml` entry
- **When** I compare the two per agent
- **Then** every agent's Agent Configuration `model_tier` matches its `manifest.yaml` `model_tier`

### Scenario 3: No behavioral regression
- **Given** the mapping (`fast` → `capability`, `default`/`inherit` → `orchestration`)
- **When** I resolve each agent's tier through the adapter table
- **Then** each agent resolves to the **same concrete model it runs today**: `architecture-check-agent` and `user-story-generator` at the floor/fast model; the other five at inherit/anchor

### Scenario 4: Concrete overrides preserved
- **Given** Codex requires concrete model IDs for some agents
- **When** I inspect the manifest / adapter mapping
- **Then** any concrete `model:` override is preserved and documented as taking precedence over `model_tier:`

## Implementation Tasks

- [x] **Map tiers:** Apply the spec's mapping table — `capability`: `architecture-check-agent`, `user-story-generator`; `orchestration`: `coding`, `review`, `testing`, `documentation`, `visual-qa`.
- [x] **Update agent config:** Add `model_tier:` as a new line in the existing Agent Configuration fenced block (alongside `subagent_type:` / `model:` / `readonly:`) in each of the 7 `agents/*.md` files — no new `---` frontmatter header.
- [x] **Update `manifest.yaml`:** Add `model_tier:` to each agent entry; decide per-agent whether to retain `model:` (keep only where a concrete override is genuinely needed, e.g. Codex IDs) or drop it in favor of the tier.
- [x] **Document precedence:** Where both `model:` and `model_tier:` remain, add a note that `model:` wins.
- [x] **Regression check:** Produce the tier→concrete-model resolution walkthrough proving no agent changes its effective model.
- [x] **Consistency check:** Verify Agent Configuration block tier == manifest tier for all 7 agents.

## Definition of Done

- [x] All four acceptance criteria pass
- [x] All 7 agents declare `model_tier` in both their Agent Configuration block and `manifest.yaml`, values consistent
- [x] Documented resolution walkthrough shows zero change in each agent's concrete model vs. today
- [x] No adapter files modified in this story (resolution tables are Story 3; this story consumes today's mapping semantics)
- [x] Self-review: mapping is conservative (rename-to-portable), no agent silently upgraded/downgraded

## Technical Notes

- This is a **rename-to-portable, not a behavior change.** The whole point is that the resolved model is identical to today — only the vocabulary becomes portable.
- `visual-qa-agent` is `inherit` today; `orchestration` maps to inherit/anchor, so it keeps its behavior.
- If Story 3 runs in parallel, coordinate on the resolution table: this story asserts the *mapping intent*; Story 3 documents the *platform resolution*. They must agree.

## Context for Agents

- **Coding agent context:** spec.md → `## Implementation Approach → ### Agent adoption mapping`; current values in `.writ/manifest.yaml` (lines defining each agent's `model:`).
- **Review agent context:** spec.md → Success Criteria #1, #2. The critical check is Scenario 3 (no regression) — verify every agent resolves to its current model.
- **Testing agent context:** `rg "model_tier:|model:" agents/ .writ/manifest.yaml`; build the 7-row tier→model table and confirm against the "today" column in spec.md's mapping table.

---

## What Was Built

**Implementation Date:** 2026-07-18

### Files Modified

- **`agents/architecture-check-agent.md`** — Added `model_tier: capability` to the Agent Configuration block; annotated the literal `model: "fast"` in its `## Prompt Template` `Task({...})` sample with `# mirrors model_tier: capability — see Agent Configuration above`.
- **`agents/coding-agent.md`**, **`agents/documentation-agent.md`**, **`agents/review-agent.md`**, **`agents/testing-agent.md`** — Added `model_tier: orchestration` to each Agent Configuration block.
- **`agents/user-story-generator.md`** — Added `model_tier: capability`; annotated all 5 literal `model: "fast"` occurrences (main template + 4 numbered examples) with the same cross-reference comment.
- **`agents/visual-qa-agent.md`** — Added `model_tier: orchestration` as a new yaml key inside its `## Agent Specification` block (differs from the other 6: yaml-fenced, not a plain fence).
- **`.writ/manifest.yaml`** — Added `model_tier:` to all 7 agent entries. **Retained every existing `model:` field** — an architecture-check pass discovered `scripts/gen-skill.sh` hard-requires `.agents[].model` (exit 1 if absent) and is exercised in CI, so dropping `model:` (as the story's original task wording allowed) would have broken the build. `model_tier:` was added alongside, not instead of, `model:`.

### Implementation Decisions

1. **Keep `model:` on all 7 manifest entries** — discovered via architecture-check (Gate 0) that `scripts/gen-skill.sh` requires it; this overrides the story task's original "decide whether to drop it" framing with a definitive "always keep it."
2. **Sync the second model carrier in two files** — `architecture-check-agent.md` and `user-story-generator.md` each embed a literal `model: "fast"` in their Prompt Template code samples, independent of the Agent Configuration block. Annotated (not changed) so the two carriers don't silently drift apart.

### Test Results

**Verification:** Manual `rg`/`git diff`/cross-check walkthrough; also ran `scripts/gen-skill.sh --dry-run` (exit 0) as an executable proof the manifest still parses.
- ✅ 7/7 agents declare exactly one `model_tier` (`orchestration` or `capability`)
- ✅ 7/7 manifest entries declare `model_tier`, matching their agent file
- ✅ 7/7 original `model:` values in manifest unchanged
- ✅ Zero adapter files touched by this story (confirmed no overlap with parallel Story 3)

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** None
- **Security:** None (docs/config only)
- **Boundary Compliance:** 8/8 owned files touched (7 agents + manifest.yaml), 0 unowned files touched

### Deviations from Spec

None — the `model:` retention decision was already anticipated as an open question in the story's own task wording ("decide per-agent whether to retain `model:`") and resolved conservatively via direct evidence (`gen-skill.sh`), not a deviation from intent.
