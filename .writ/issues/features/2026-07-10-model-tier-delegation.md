# Model-Tier Delegation Across Commands and Skills

> **Type:** Feature
> **Priority:** Normal
> **Effort:** Large
> **Created:** 2026-07-10
> **spec_ref:** .writ/specs/2026-07-10-model-tier-delegation/spec.md

## TL;DR

Align model capability with primitive role: higher-order models drive orchestration (commands), lower-order models handle tool utilization/knowledge (skills), so each layer runs on the cheapest model that still does its job well.

## Current State

- Model selection is per-agent, ad hoc: agents declare `model: default (inherits from parent)` or `model: "fast"` (e.g. `user-story-generator.md`), with the adapter mapping `"fast"` to a Haiku-class model (`adapters/cursor.md`).
- No convention ties model tier to the verb/noun/tool boundary (command = orchestration, skill = capability) from ADR-009.
- Commands and skills have no `model` / `model_tier` frontmatter contract; `required_skills:` exists but says nothing about which model a skill should run under.
- Result: everything tends to inherit the parent (often a top-tier model), even when a skill is a narrow, well-scoped capability that a cheaper model could execute reliably.

## Expected Outcome

- A declared tiering convention: **commands (orchestrations/playbooks/workflows) → higher-order model by default**, **skills (tool utilization/knowledge/specific capabilities) and other small, well-scoped tasks → lower-order model relative to the invoking command**.
- Commands *assume* a higher tier out of the box because of inherent orchestration demands (multi-step planning, cross-file reasoning, delegation). Authors opt down, not up.
- A **model hierarchy map** per supported platform (Cursor, Codex, OpenClaw): an ordered ranking of the models each exposes, so "higher" and "lower" resolve to concrete choices. This is the prerequisite — responsibilities can't be assigned until the relative ordering is known.
- Frontmatter contract (e.g. `model_tier: orchestration | capability`, or explicit `model:`) that expresses intent portably, with adapters translating tier → the concrete platform model via the hierarchy map.
- Relative, not absolute, semantics: a skill runs at a tier at or below its invoking command, so the boundary holds regardless of which specific models a platform exposes.
- Graceful degradation when a platform can't honor a requested tier (fall back to parent/default, warn rather than hard-fail — consistent with `required_skills:` handling).

## Relevant Files

- `.writ/manifest.yaml` - where a `model_tier` field would live per command/agent/skill
- `adapters/cursor.md` - existing `model: "fast"` → model mapping; needs tier translation (same pattern in `codex.md`, `openclaw.md`)
- `system-instructions.md` - documents the verb/noun/tool boundary and `required_skills:` convention this tiering would extend

## Notes

- **Prerequisite research:** establish the relative model hierarchy for each platform before assigning responsibilities. Platforms rename and reshuffle model lineups often, so the map needs a maintenance/refresh story (not a hardcoded snapshot that rots).
- Depends conceptually on the skills primitive (ADR-009); tiering only pays off once skills are actually extracted and invoked.
- Open question: absolute tiers (name specific model classes) vs. relative tiers (skill ≤ command). Relative is more portable across platforms with different model lineups; worth deciding in a spec. Leaning relative, anchored by the per-platform hierarchy map.
- Open question: is "tier" a two-level split (orchestration/capability) or a finer scale? Two levels is simpler and matches the command/skill boundary; start there unless evidence demands more.
- Cost/latency win is the motivation, but guardrail is quality — needs evidence that capability-tier skills don't regress on their narrow tasks.
