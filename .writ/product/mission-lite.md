# Writ — Product Mission (Lite)

> Source: .writ/product/mission.md
> Regenerated from mission.md on 2026-10-20
> Purpose: Efficient AI context for development sessions
> Last Updated: 2026-10-20

## Core Value

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns the durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics (context management, subagents, browsing, retrieval) to the platform underneath. As harnesses absorb mechanics natively, Writ sheds them and concentrates on what compounds: the negotiated contract layer no harness provides.

**Writ owns three things and delegates or deletes the rest** ([ADR-030](../decision-records/adr-030-contract-verifier-boundary-front-door.md)):

- **The contract:** spec, acceptance and exit criteria, and stakes.
- **The verifier:** scripts that re-derive verdicts about the code and the running app.
- **The boundary:** what an agent may not do without a human.

Users reach all three through one front door that restates, classifies, and routes each request.

> **"Thin" is measured per-invocation, not per-directory.** Phase 10 found the 516KB alarm was largely a measurement artifact — the worst real invocation is ~19.4k tokens, 7.2× smaller (`scripts/measure-invocation.py`). Per [ADR-023](../decision-records/adr-023-stakes-proportional-diligence.md), efficiency means economy of *steps and decisions*, governed by stakes-proportional diligence; there is deliberately **no mechanically enforced efficiency constraint**, and bytes are drift signal only. Subtraction is a standing practice instead: each phase opens by removing what no longer earns its place.

## Target Users

**Today:** Solo developers shipping real products with AI coding tools who need judgment and process, not more prompts, and who should not have to learn dozens of commands before the first task.

**Forward-compatible (claimed, not targeted):** Small teams adopting AI-assisted engineering — see [ADR-007](../decision-records/adr-007-team-audience-sequencing.md).

## Key Differentiators

1. **Non-degrading by construction** — Plain-text + git + adapter abstraction; the knowledge ledger consolidates (merge, never append) so context stays sharp ([ADR-006](../decision-records/adr-006-non-degrading-destination.md), [ADR-008](../decision-records/adr-008-spec-as-team-contract-moat.md))
2. **The contract layer, not another harness** — Rides on native memory, skills, and subagents. Interoperates with external second brains; GBrain via MCP is the worked example, being generalized to engine detection. Markdown is canonical and indexes are disposable ([ADR-011](../decision-records/adr-011-memory-interop-markdown-canonical.md)). Skill packs such as pstack make each agent rigorous. Writ keeps the project's intent and checks results against it, and the two can coexist.
3. **Observable autonomy, deliberately bounded**
   - Normal `/implement-phase` uses one confirmation, fresh context per spec, quarantine on failure, and an honest report.
   - `--recommend` adds evidence-backed autonomy on two commands: `/create-spec` authors and locks a spec package then stops, and `/implement-phase` runs the phase as an end-to-end loop, both ending short of merge/PR/release. Opaque unbounded loops and autonomous production delivery remain excluded ([ADR-013](../decision-records/adr-013-recommended-autonomous-delivery.md)).
   - The ceiling moves only on evidence; machine-verified UAT is the named precondition ([ADR-028](../decision-records/adr-028-behavioral-verification-and-cross-family-panels.md)). Phase 16 evaluates verified landing after Phase 12's UAT. Merge stays human unless its own ADR moves it.
4. **Self-improvement with evidence** — `/refresh-command` refinements cite transcripts and pass evals. `/retro` reads a run's agent transcripts and proposes environment fixes, never code changes, each cited to a transcript path (v0.41.0). Skills carry a candidate → proven → promoted lifecycle. Phase 15 gives `/retro` a fix ladder (architecture, types, lint, test, then docs) and a rule-to-enforcer table. Friction signals are retired ([ADR-030](../decision-records/adr-030-contract-verifier-boundary-front-door.md)).
5. **Adaptive ceremony** — Process is right-sized to the work:
   - `/prototype` is the exploration workflow (PR #59, v0.42.0): a few code-portable drafts on declared axes, a recorded choice, then the chosen direction built or handed to `/create-spec --from-prototype`.
   - Features get the gated pipeline.
   - Roadmap chunks get phase orchestration.

   Phase 14's front door picks the level for the user.
6. **Opinionated guidance** — Lead with the recommendation, challenge premises, push for the best version. Judgment, not menus.

## Success Definition

Code and methodology that score well on six production-grade criteria — auditable, versioned, reviewable, reproducible, onboarding-friendly, failure-isolatable — surfaced as a one-line health score in `/status`. Personal leverage in the meantime: less rework, fewer drift incidents, confidence to walk away from a running phase.

## Current Phase

**Phases 1–11:** Shipped and released. Phase 10 closed partially complete — the determinism half enforced, the byte goal withdrawn ([ADR-023](../decision-records/adr-023-stakes-proportional-diligence.md)). Phase 11 (Contract-and-Verifier Layer, v0.36.0) pruned the shared base under 10 KB, put scripts behind eight of ten `/implement-story` gates, and made the two-agent pipeline the default with `--full-pipeline` as the escalation.

**Phase 12 — Behavioral Verification (◐ implemented and released in v0.40.0, human UAT open):** a per-project verification recipe (`.writ/docs/app-verification.md`), drafted by `/create-uat-plan`, names the project's own checks against the running app; Gate 4.5 runs them through `scripts/app-verify.py` and records evidence, and `exit-criteria.py` checks that the cited evidence exists. The opt-in cross-family review panel stays: its trial found 6 valid of 8 panel-only findings on the Phase 11 baseline set ([ADR-028](../decision-records/adr-028-behavioral-verification-and-cross-family-panels.md)). All four success criteria are met; the phase's own UAT plan is unticked, so human UAT is the open item.

**Inter-phase work:**
- Model delegation (v0.34.0).
- Flagged harness cuts, the opt-in Jev judgment pilot, and drift and architecture guards (v0.37.0–v0.39.0).
- Product-check direction (v0.40.0).
- `/retro` as a transcript review, plus the `gbrain-interop` removal (v0.41.0).
- The agent CLI contract ([ADR-029](../decision-records/adr-029-agent-cli-contract.md)) and `/prototype` as the exploration workflow (PR #59), both in v0.42.0.

**Phases 13–16 committed (2026-10-20, [ADR-030](../decision-records/adr-030-contract-verifier-boundary-front-door.md)):**
- **13, Subtract and Repair:** every defect the 2026-10-19 research found, plus the cuts.
- **14, Front Door and Distribution:** one entry command, plugin installs, and generated per-platform trees with an adapter coverage check.
- **15, Code-Level Rigor:** `/why`, the `design-divergence` skill shared with Gate 0, blast radius, repro-first bug fixing, and `/retro`'s fix ladder.
- **16, Verified Landing:** a PR-readiness check and a ledger bound to the head SHA. Gated on Phase 12's UAT.

## What Writ Is Not Building

Opaque unbounded loop runners (Ralph deprecated), autonomous production delivery (recommended flows never merge, open PRs, or release), memory databases (markdown canonical, external indexes are consumers), velocity-first sprint flow, browser daemons (verification drives the app through the project's or platform's own tools), hosted SaaS, a personal style pack (one author's taste as universal rules), a cross-vendor model router by default (agents stay family-locked; other vendors only in the opt-in panel). See `mission.md` for full reasoning.

## Design Principles

1. Adaptive ceremony — every feature must justify its weight
2. Local-first — improvements land in the project, upstream is optional
3. Dogfood everything — use Writ to build Writ
4. Delegate mechanics, own contracts — if the harness does it natively, adapt to it; never re-implement it
5. Aplomb — agents handle complexity with grace, not checklists
6. Opinionated by default — lead with the recommendation, explain why, then offer alternatives
7. Subtract before you add — each phase opens by removing what no longer earns its place
