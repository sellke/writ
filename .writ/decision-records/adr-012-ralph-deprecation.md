# ADR-012: Ralph Deprecation

> Status: Accepted
> Date: 2026-07-09
> Deciders: Adam (product owner)
> Part of: 2026-07-09 strategic refresh (`/plan-product` audit vs. current harnesses, GStack, GBrain)
> Implements: Ralph retirement from [ADR-010](adr-010-supervised-autonomy-ceiling.md), reconciled by [ADR-013](adr-013-recommended-autonomous-delivery.md)

## Context

Ralph (Phase 3b, v0.10.0) is Writ's fully autonomous execution mode: `/ralph plan` generates a cross-spec execution plan in Cursor, then `scripts/ralph.sh` runs a CLI bash loop — fresh context per iteration, one story per iteration, file-based state (`ralph-*.json`), quarantine branching for large drift, `/ralph status` for monitoring and re-entry. It was built on the "Ralph Wiggum" research finding that fresh-context agents outperform continuous agents.

ADR-010 originally set Writ's autonomy ceiling at supervised phase-level execution. ADR-013 later superseded its contract-level gate while preserving the rationale against opaque unbounded loops. This ADR records the mechanics and rationale of retiring Ralph specifically; it does not prohibit bounded single-spec `--recommend` delivery.

## Decision Drivers

1. ADR-010's preserved accountability driver: opaque unbounded loops produce more output than a solo maintainer can meaningfully review
2. Platform absorption: background agents, cloud agents, and scheduled automations now ship natively in the harnesses; a Writ-owned bash loop is depreciating infrastructure
3. Surface cost: ~550 lines (`commands/ralph.md`) + `scripts/ralph.sh` + `PROMPT_build.md` template + `ralph-cli-pipeline.md` docs + 5 config keys + adapter sections
4. Ralph's real inventions are separable from its loop mechanism

## Considered Options

**Option A — Deprecate and archive; migrate durable inventions to `/implement-phase`. (Chosen)**
**Option B — Keep Ralph frozen (no maintenance, no removal).** Rejected: frozen autonomous-execution code is worse than none — it drifts against evolving commands/agents silently, and an autonomy mode is the last place to tolerate silent drift.
**Option C — Rebuild Ralph on native cloud agents.** Rejected: an opaque unbounded loop lacks ADR-013's observable, resumable state and immutable production approval. Recorded as the shape a future revisit would take only if those boundaries can be preserved.

## Decision

**Option A.** In Phase 6:

1. **Archive, don't delete:** `commands/ralph.md`, `scripts/ralph.sh`, `PROMPT_build.md`, and `.writ/docs/ralph-cli-pipeline.md` move to an `archive/` location; git history preserves everything.
2. **Migrate the durable inventions into `/implement-phase`:** fresh context per spec (subagent per `/implement-spec`), quarantine branching (`writ/quarantine/{spec}`), state schema rigor (`phase-execution-*.json` as the resume/monitoring anchor), escalation semantics surfaced via `/status`.
3. **Clean the surface:** remove ralph entries from `.writ/manifest.yaml`, SKILL.md regeneration, README, adapter docs, `/status` allowlist, and config format docs.
4. **Ship a migration note:** users with in-flight `ralph-*.json` state finish or abandon those runs before upgrading; ongoing work moves to `/implement-phase`.
5. **Changelog:** deprecation recorded with pointer to this ADR and `/implement-phase`.

## Consequences

**Positive:** Autonomy hardening concentrates on one model; the roadmap's Phase 3b legacy is honestly accounted for (its research finding survives, its mechanism retires); the harness sheds its largest single non-core surface.

**Negative:** Ralph-style overnight unattended execution is no longer possible with Writ alone. Anyone who built workflow around `ralph.sh` must migrate. Bounded single-spec recommended delivery is a separate ADR-013 workflow, not a compatibility successor.

**Review trigger:** Revisit a Ralph-like mechanism only if native platform loops can preserve ADR-013's observable state, finite scope, safe resumption, and exact-SHA production approval while Writ owns no execution infrastructure.
