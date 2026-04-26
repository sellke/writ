# Writ — Product Mission (Lite)

> Source: .writ/product/mission.md
> Purpose: Efficient AI context for development sessions

## Core Value

Writ is an elegant development workflow for AI-assisted software development built so that code, methodology, and accumulated knowledge don't degrade as projects, teams, and AI platforms churn around them. It gives solo builders the engineering discipline of a great team — clear steps, firm boundaries, quality gates, and adaptive ceremony that right-sizes process to the work. Plain-text artifacts in git mean specs, decisions, and lessons stay reviewable and survivable. Methodology-first, platform-agnostic, pure open-source.

## Target Users

**Today:** Solo developers shipping real products with AI coding tools who've hit the quality ceiling of unstructured AI development. They need judgment and process, not more prompts.

**Forward-compatible (claimed, not targeted):** Small teams adopting AI-assisted engineering. The substrate is built so the audience pivot requires no architectural change when it arrives — see [ADR-007](../decision-records/adr-007-team-audience-sequencing.md).

## Key Differentiators

1. **Non-degrading by construction** — Plain-text + git + adapter abstraction means specs, decisions, knowledge, and the methodology itself survive sessions, contributors, and AI platform churn ([ADR-006](../decision-records/adr-006-non-degrading-destination.md), [ADR-008](../decision-records/adr-008-spec-as-team-contract-moat.md))
2. **Adaptive ceremony** — Right-sized process for the size of the change, not one-size-fits-all
3. **Self-correcting pipeline** — Tiered spec-healing when reality diverges from plan (auto-heal small, flag medium, pause large)
4. **Clear steps, firm boundaries** — Every command has explicit phases, defined handoffs, and predictable outcomes. Agents know exactly what they're responsible for.
5. **Methodology, not tooling** — Markdown-as-instructions works on any AI platform without lock-in
6. **Opinionated guidance** — Commands lead with recommendations, challenge premises, and push for the best version of every idea. Judgment, not menus.

## Success Definition

**Test of the destination:** code and methodology that score well on six production-grade criteria — auditable, versioned, reviewable, reproducible, onboarding-friendly, failure-isolatable. Operationalized via the `/audit` command (Phase 5).

**Personal leverage in the meantime:** Writ makes projects dramatically better as measured by less rework, fewer drift incidents, and the confidence to ship without manual verification of everything.

## Current Phase

**Phase 1 — Foundation:** `/prototype`, tiered spec-healing, `/refresh-command`. *Implemented and materially dogfooded; ongoing dogfood continues as an operating practice.*

**Phase 2 — Reach:** `/ship`, `/review`, `/retro`, enhanced error mapping. *Implemented; awaiting dogfood.*

**Phase 3a — Context Engine:** Per-story context hints, "What Was Built" records, agent-specific spec views, UAT plan generation. ✅ Complete (v0.9.0).

**Phase 3b — Ralph Loop Orchestration:** `/ralph plan`, CLI loop, fresh-context iterations, quarantine branching. ✅ Complete (v0.10.0).

**Phase 4 — Production-Grade Substrate (next):** Knowledge ledger, `SKILL.md` generation, preamble enforcement, eval Tier 1, spec `owner:` frontmatter. Foundations for the destination claim.

**Phase 5 — Operationalize the Destination:** `/audit` command, spec-as-team-contract substrate, `/lessons`, production-grade scorecards in `/status` and per-story completion, drift-to-lesson promotion.

## What Writ Is Not Building

Velocity-first sprint flow, persistent-database knowledge layer, browser daemon, cross-AI orchestration layer, hosted SaaS. See `mission.md` for full reasoning.

## Design Principles

1. Adaptive ceremony — every feature must justify its weight
2. Local-first — improvements land in the project, upstream is optional
3. Dogfood everything — use Writ to build Writ
4. Commands are the unit — learning, improvement, distribution all operate on commands
5. Aplomb — agents handle complexity with grace, not checklists
6. Opinionated by default — lead with the recommendation, explain why, then offer alternatives
