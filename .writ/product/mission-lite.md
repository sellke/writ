# Writ — Product Mission (Lite)

> Source: .writ/product/mission.md
> Regenerated from mission.md on 2026-10-01
> Purpose: Efficient AI context for development sessions
> Last Updated: 2026-10-01

## Core Value

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns the durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics (context management, subagents, browsing, retrieval) to the platform underneath. As harnesses absorb mechanics natively, Writ sheds them and concentrates on what compounds: the negotiated contract layer no harness provides.

> **"Thin" is measured per-invocation, not per-directory.** Phase 10 found the 516KB alarm was largely a measurement artifact — the worst real invocation is ~19.4k tokens, 7.2× smaller (`scripts/measure-invocation.py`). Per [ADR-023](../decision-records/adr-023-stakes-proportional-diligence.md), efficiency means economy of *steps and decisions*, governed by stakes-proportional diligence; there is deliberately **no mechanically enforced efficiency constraint**, and bytes are drift signal only.

## Target Users

**Today:** Solo developers shipping real products with AI coding tools who need judgment and process, not more prompts.

**Forward-compatible (claimed, not targeted):** Small teams adopting AI-assisted engineering — see [ADR-007](../decision-records/adr-007-team-audience-sequencing.md).

## Key Differentiators

1. **Non-degrading by construction** — Plain-text + git + adapter abstraction; the knowledge ledger consolidates (merge, never append) so context stays sharp ([ADR-006](../decision-records/adr-006-non-degrading-destination.md), [ADR-008](../decision-records/adr-008-spec-as-team-contract-moat.md))
2. **The contract layer, not another harness** — Rides on native memory/skills/subagents; interoperates with external brains (GBrain via MCP); markdown canonical, indexes disposable ([ADR-011](../decision-records/adr-011-memory-interop-markdown-canonical.md))
3. **Observable autonomy, deliberately bounded** — Normal `/implement-phase` uses one confirmation, fresh context per spec, quarantine on failure, and an honest report. `--recommend` adds evidence-backed autonomy on two commands — `/create-spec` authors and locks a spec package then stops, and `/implement-phase` runs the phase as an end-to-end loop — both ending short of merge/PR/release; opaque unbounded loops and autonomous production delivery remain excluded ([ADR-013](../decision-records/adr-013-recommended-autonomous-delivery.md)). The ceiling moves only on evidence; machine-verified UAT is the named precondition ([ADR-028](../decision-records/adr-028-behavioral-verification-and-cross-family-panels.md))
4. **Self-improvement with evidence** — `/refresh-command` refinements cite transcripts and pass evals; skills carry a candidate → proven → promoted lifecycle
5. **Adaptive ceremony** — Right-sized process: `/prototype` for spikes, gated pipeline for features, phase orchestration for roadmap chunks
6. **Opinionated guidance** — Lead with the recommendation, challenge premises, push for the best version. Judgment, not menus.

## Success Definition

Code and methodology that score well on six production-grade criteria — auditable, versioned, reviewable, reproducible, onboarding-friendly, failure-isolatable — surfaced as a one-line health score in `/status`. Personal leverage in the meantime: less rework, fewer drift incidents, confidence to walk away from a running phase.

## Current Phase

**Phases 1–11:** Shipped and released (through v0.39.0). Phase 10 closed partially complete — the determinism half enforced, the byte goal withdrawn ([ADR-023](../decision-records/adr-023-stakes-proportional-diligence.md)). Phase 11 (Contract-and-Verifier Layer, v0.36.0) pruned the shared base under 10 KB, put scripts behind eight of ten `/implement-story` gates, and made the two-agent pipeline the default with `--full-pipeline` as the escalation. Inter-phase work since: model delegation (v0.34.0), flagged harness cuts, the opt-in Jev judgment pilot, drift and architecture guards (v0.37.0–v0.39.0).

**Phase 12 — Behavioral Verification (📋 committed, not started):** a generated project `verify-<app>` skill and feature map that drive the running app; UAT scenarios bound to captured evidence so Gate 4.5 leaves `prose-only`; an opt-in cross-family review panel for high-stakes stories, kept only if it catches what the single-vendor evaluator misses ([ADR-028](../decision-records/adr-028-behavioral-verification-and-cross-family-panels.md)).

## What Writ Is Not Building

Opaque unbounded loop runners (Ralph deprecated), autonomous production delivery (recommended flows never merge, open PRs, or release), memory databases (markdown canonical, external indexes are consumers), velocity-first sprint flow, browser daemons (verification drives the app through the project's or platform's own tools), hosted SaaS. See `mission.md` for full reasoning.

## Design Principles

1. Adaptive ceremony — every feature must justify its weight
2. Local-first — improvements land in the project, upstream is optional
3. Dogfood everything — use Writ to build Writ
4. Delegate mechanics, own contracts — if the harness does it natively, adapt to it; never re-implement it
5. Aplomb — agents handle complexity with grace, not checklists
6. Opinionated by default — lead with the recommendation, explain why, then offer alternatives
