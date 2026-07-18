# Writ — Product Mission (Lite)

> Source: .writ/product/mission.md
> Regenerated from mission.md on 2026-07-17
> Purpose: Efficient AI context for development sessions
> Last Updated: 2026-07-17

## Core Value

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns the durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics (context management, subagents, browsing, retrieval) to the platform underneath. As harnesses absorb mechanics natively, Writ sheds them and concentrates on what compounds: the negotiated contract layer no harness provides.

## Target Users

**Today:** Solo developers shipping real products with AI coding tools who need judgment and process, not more prompts.

**Forward-compatible (claimed, not targeted):** Small teams adopting AI-assisted engineering — see [ADR-007](../decision-records/adr-007-team-audience-sequencing.md).

## Key Differentiators

1. **Non-degrading by construction** — Plain-text + git + adapter abstraction; the knowledge ledger consolidates (merge, never append) so context stays sharp ([ADR-006](../decision-records/adr-006-non-degrading-destination.md), [ADR-008](../decision-records/adr-008-spec-as-team-contract-moat.md))
2. **The contract layer, not another harness** — Rides on native memory/skills/subagents; interoperates with external brains (GBrain via MCP); markdown canonical, indexes disposable ([ADR-011](../decision-records/adr-011-memory-interop-markdown-canonical.md))
3. **Observable autonomy, deliberately bounded** — Normal `/implement-phase` uses one confirmation, fresh context per spec, quarantine on failure, and an honest report. `--recommend` adds evidence-backed autonomy on two commands — `/create-spec` authors and locks a spec package then stops, and `/implement-phase` runs the phase as an end-to-end loop — both ending short of merge/PR/release; opaque unbounded loops and autonomous production delivery remain excluded ([ADR-013](../decision-records/adr-013-recommended-autonomous-delivery.md))
4. **Self-improvement with evidence** — `/refresh-command` refinements cite transcripts and pass evals; skills carry a candidate → proven → promoted lifecycle
5. **Adaptive ceremony** — Right-sized process: `/prototype` for spikes, gated pipeline for features, phase orchestration for roadmap chunks
6. **Opinionated guidance** — Lead with the recommendation, challenge premises, push for the best version. Judgment, not menus.

## Success Definition

Code and methodology that score well on six production-grade criteria — auditable, versioned, reviewable, reproducible, onboarding-friendly, failure-isolatable — surfaced as a one-line health score in `/status`. Personal leverage in the meantime: less rework, fewer drift incidents, confidence to walk away from a running phase.

## Current Phase

**Phases 1–4 + 3a/3b:** Shipped (prototype/spec-healing/refresh, ship/review/retro, context engine, Ralph, knowledge ledger/evals/SKILL.md generation). **Phase 5:** Closed — spirit met by eval Tier 1 CI gate, `/verify-spec`, and drift logs.

**Phase 6 — Autonomy Ceiling (✅ shipped, v0.19.0):** `/implement-phase` hardening (fresh context per spec, quarantine branching, User Challenge framing, `dependencies:` frontmatter, knowledge writeback), Ralph deprecation, `/status` health line.

**Phase 7 — Compounding Layer (✅ shipped, v0.19.0):** Skill lifecycle + extractions, evidence-bound `/refresh-command`, knowledge consolidation.

**Phase 8 — Memory Interop (✅ implemented):** GBrain compatibility recipe, native-memory guidance per adapter.

**Next horizon:** No committed phase in flight — the 2026 harness-audit strategy (Phases 6–8) is delivered. Next candidates live in the roadmap parking lot (cross-project learning corpus, `/design` modernization, eval Tier 2), pulled forward on concrete signal.

## What Writ Is Not Building

Opaque unbounded loop runners (Ralph deprecated), autonomous production delivery (recommended flows never merge, open PRs, or release), memory databases (markdown canonical, external indexes are consumers), velocity-first sprint flow, browser daemons, hosted SaaS. See `mission.md` for full reasoning.

## Design Principles

1. Adaptive ceremony — every feature must justify its weight
2. Local-first — improvements land in the project, upstream is optional
3. Dogfood everything — use Writ to build Writ
4. Delegate mechanics, own contracts — if the harness does it natively, adapt to it; never re-implement it
5. Aplomb — agents handle complexity with grace, not checklists
6. Opinionated by default — lead with the recommendation, explain why, then offer alternatives
