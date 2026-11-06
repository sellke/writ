# Writ — Product Mission (Lite)

> Source: .writ/product/mission.md
> Regenerated from mission.md on 2026-11-06
> Purpose: Efficient AI context for development sessions
> Last Updated: 2026-11-06

## Core Value

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns the durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics (context management, subagents, browsing, retrieval) to the platform underneath. As harnesses absorb mechanics natively, Writ sheds them and concentrates on what compounds: the negotiated contract layer no harness provides.

**Writ owns three things and delegates or deletes the rest** ([ADR-030](../decision-records/adr-030-contract-verifier-boundary-front-door.md)):

- **The contract:** spec, acceptance and exit criteria, and stakes.
- **The verifier:** scripts that re-derive verdicts about the code and the running app.
- **The boundary:** when an agent stops and asks a person: on reasonable doubt, not on principle ([ADR-033](../decision-records/adr-033-doubt-gated-autonomy.md)).

Users reach all three through one front door, `/writ`, that restates, classifies, and routes each request.

> **"Thin" is measured per-invocation, not per-directory.** Phase 10 found the 516KB alarm was largely a measurement artifact — the worst real invocation is ~19.4k tokens, 7.2× smaller (`scripts/measure-invocation.py`). Per [ADR-023](../decision-records/adr-023-stakes-proportional-diligence.md), efficiency means economy of *steps and decisions*, governed by stakes-proportional diligence; there is deliberately **no mechanically enforced efficiency constraint**, and bytes are drift signal only. Subtraction is a standing practice instead: each phase opens by removing what no longer earns its place.

## Target Users

**Today:** Solo developers shipping real products with AI coding tools who need judgment and process, not more prompts, and who should not have to learn dozens of commands before the first task.

**Forward-compatible (claimed, not targeted):** Small teams adopting AI-assisted engineering — see [ADR-007](../decision-records/adr-007-team-audience-sequencing.md).

## Key Differentiators

1. **Non-degrading by construction** — Plain-text + git + adapter abstraction; the knowledge ledger consolidates (merge, never append) so context stays sharp ([ADR-006](../decision-records/adr-006-non-degrading-destination.md), [ADR-008](../decision-records/adr-008-spec-as-team-contract-moat.md))
2. **The contract layer, not another harness** — Rides on native memory, skills, and subagents. Interoperates with external second brains; GBrain via MCP is the worked example, being generalized to engine detection. Markdown is canonical and indexes are disposable ([ADR-011](../decision-records/adr-011-memory-interop-markdown-canonical.md)). Skill packs such as pstack make each agent rigorous. Writ keeps the project's intent and checks results against it, and the two can coexist.
3. **Initiative, with a decision log**
   - Normal `/implement-phase` uses one confirmation, fresh context per spec, quarantine on failure, and an honest report.
   - Until Phase 17, `--recommend` adds evidence-backed autonomy on two commands: `/create-spec` authors and locks a spec package then stops, and `/implement-phase` runs the phase as an end-to-end loop, both ending short of merge/PR/release ([ADR-013](../decision-records/adr-013-recommended-autonomous-delivery.md)).
   - [ADR-033](../decision-records/adr-033-doubt-gated-autonomy.md) (2026-11-05), built in Phase 17 and merged 2026-11-05: every question is a decision that `jev-judge.py doubt` settles. Rules first (merge and release always ask; an act that is not git-revertable, or a recommendation without evidence, asks), then Jev ([ADR-027](../decision-records/adr-027-optional-judgment-provider.md)), then the decision's kind: scope and taste reach a person, method choices do not. A supervisor agent re-derives every story and lane report. `--recommend` is an accepted no-op.
   - Jev shadows for now: it scores its confidence that a recommendation is right, and on 98 past answers about 2 to 3% of its acts would have been overridden, but the 95% bound sits at the 10% cap, so no threshold was written. Answered questions become labels that refit it. Opaque unbounded loops stay excluded.
4. **Self-improvement with evidence** — `/refresh-command` refinements cite transcripts and pass evals. `/retro` reads a run's agent transcripts and proposes environment fixes, never code changes, in a fixed order (architecture, types, lint, test, docs) with a rule-to-enforcer table. Skills carry a candidate → proven → promoted lifecycle. Friction signals are retired ([ADR-030](../decision-records/adr-030-contract-verifier-boundary-front-door.md)); Phase 17 adds the decision log as a third channel: overrides recalibrate the doubt thresholds.
5. **Adaptive ceremony** — Process is right-sized to the work:
   - `/prototype` is the exploration workflow (PR #59, v0.42.0): a few code-portable drafts, a recorded choice, then the chosen direction built or handed to `/create-spec --from-prototype`.
   - Features get the gated pipeline.
   - Roadmap chunks get phase orchestration.

   `/writ` (merged 2026-11-04) picks the level; since Phase 17 it confirms the route only on doubt.
6. **Opinionated guidance** — Lead with the recommendation, challenge premises, push for the best version. Judgment, not menus.

## Success Definition

Code and methodology that score well on six production-grade criteria — auditable, versioned, reviewable, reproducible, onboarding-friendly, failure-isolatable — surfaced as a one-line health score in `/status`. Personal leverage in the meantime: less rework, fewer drift incidents, confidence to walk away from a running phase.

## Current Phase

**Phases 1–11:** Shipped and released. Phase 10 closed partially complete — the determinism half enforced, the byte goal withdrawn ([ADR-023](../decision-records/adr-023-stakes-proportional-diligence.md)). Phase 11 (Contract-and-Verifier Layer, v0.36.0) pruned the shared base under 10 KB, put scripts behind eight of ten `/implement-story` gates, and made the two-agent pipeline the default with `--full-pipeline` as the escalation.

**Phase 12 — Behavioral Verification (◐ implemented and released in v0.40.0; UAT run by an agent 2026-10-31, 82 of 89 pass):** a per-project verification recipe (`.writ/docs/app-verification.md`), drafted by `/create-uat-plan`, names the project's own checks against the running app; Gate 4.5 runs them through `scripts/app-verify.py` and records evidence, and `exit-criteria.py` checks that the cited evidence exists. The cross-family review panel shipped opt-in, was kept by its trial, and was removed on 2026-11-04 by [ADR-032](../decision-records/adr-032-evidence-gated-review.md). Open: one failed scenario (an orchestrator asked at a Gate 4.5 `fail` instead of recoding) and one real-project `app-verify.py` run.

**Inter-phase work:**
- Model delegation (v0.34.0).
- Flagged harness cuts, the opt-in Jev judgment pilot, and drift and architecture guards (v0.37.0–v0.39.0).
- Product-check direction (v0.40.0).
- `/retro` as a transcript review, plus the `gbrain-interop` removal (v0.41.0).
- The agent CLI contract ([ADR-029](../decision-records/adr-029-agent-cli-contract.md)) and `/prototype` as the exploration workflow (PR #59), both in v0.42.0.
- `claude-agent-generator`: Claude Code agents generated from the canonical `agents/` (v0.43.0, with Phase 13).

**Phase 13 — Subtract and Repair (✅ shipped in v0.43.0, closed 2026-10-22):** Claude Code installs carry the Prime Directive, and the `CLAUDE.md` block is generated. Install, update, and uninstall keep the user's own and customized files, including `CLAUDE.md`. CI runs `pytest` and the bash tests. `/design` is renamed `/writ-design`. The lean siblings, the dormant staging machinery, and internal links in shipped commands are gone. All nine machine criteria pass, and 173 of 176 human UAT scenarios pass. One failure is tracked as an issue, two need OpenClaw, and the one regression UAT found is fixed on PR #62, merged 2026-11-01.

**Phases 14–17 ([ADR-030](../decision-records/adr-030-contract-verifier-boundary-front-door.md), [ADR-033](../decision-records/adr-033-doubt-gated-autonomy.md)):**
- **14, Front Door and Distribution (✅ merged in PR #63, 2026-11-04; unreleased):** one entry command, plugin installs, and generated per-platform trees with an adapter coverage check. Open: five unrecorded person checks, and the keep-or-remove review of `/writ` (recommendation: keep, confirm only on doubt).
- **15, Code-Level Rigor (◐ merged in PR #64, 2026-11-05; unreleased):** `/why`, the Gate 2.5 safety fact (floor `tested`), repro-first bug fixing, reviewer filters, `/retro`'s fix ladder, and evidence-gated review ([ADR-032](../decision-records/adr-032-evidence-gated-review.md)). The `design-divergence` skill lost its blind trial and is removed.
- **17, Doubt-Gated Autonomy (◐ merged in PR #65, 2026-11-05; unreleased):** one rule replaces the gate classes; Jev runs first and shadows until calibrated; a supervisor agent checks every story and lane report; `--recommend` is a no-op and every `doubt` call is logged.
- **16, Verified Landing (📋 committed, after Phase 12 closes):** a PR-readiness check, a ledger bound to the head SHA, and a `/ship` watch mode that merges on a green ledger with doubt low. Gated on Phase 12's close.

**Current focus (2026-11-06):** release and close. `main` carries Phases 14, 15, and 17 and Phase 13's two fixes, all unreleased; v0.43.0 is the last tag. PR #64 (Phase 15) and PR #65 (Phase 17) merged on 2026-11-05. The queue, in order: release v0.44.0; close Phase 12 on its agent UAT run, the Gate 4.5 issue, and one real-project run; record or strike Phase 14's five person checks and decide the front door; Phase 15's held Repro First and Phase 17's three open criteria; ADR-023's review on 2026-11-11. Phase 16 follows Phase 12's close.

## What Writ Is Not Building

Opaque unbounded loop runners (Ralph deprecated; autonomy is session-started, logged, and supervised), memory databases (markdown canonical, external indexes are consumers), velocity-first sprint flow, browser daemons (verification drives the app through the project's or platform's own tools), hosted SaaS, a personal style pack (one author's taste as universal rules), a cross-vendor model router by default (agents stay family-locked; the review panel is gone; Jev answers typed questions and runs no agent), a wrapper over platform design tools (`/writ-design` stays separate from Claude Code's native `/design`; neither delegates to the other). See `mission.md` for full reasoning.

## Design Principles

1. Adaptive ceremony — every feature must justify its weight
2. Local-first — improvements land in the project, upstream is optional
3. Dogfood everything — use Writ to build Writ
4. Delegate mechanics, own contracts — if the harness does it natively, adapt to it; never re-implement it
5. Aplomb — agents handle complexity with grace, not checklists
6. Opinionated by default — lead with the recommendation, explain why, then offer alternatives
7. Subtract before you add — each phase opens by removing what no longer earns its place
8. Land before you add — no new phase starts while two or more finished phases wait on human validation or merge
9. Ask on doubt, not on principle — a person is asked only when evidence, reversibility, or a calibrated judgment says the answer is in doubt
