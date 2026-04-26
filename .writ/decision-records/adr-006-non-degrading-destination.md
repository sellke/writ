# ADR-006: Non-Degrading Code & Methodology as Destination

> **Status:** Accepted
> **Date:** 2026-04-24
> **Deciders:** Product owner
> **Part of:** `/plan-product` strategic refresh (response to GStack rigor comparison)
> **Related:** [ADR-005](./adr-005-knowledge-substrate-markdown-over-database.md) (substrate decision), [ADR-007](./adr-007-team-audience-sequencing.md) (audience sequencing), [ADR-008](./adr-008-spec-as-team-contract-moat.md) (positioning)

## Context

Writ has shipped through Phases 1, 2, 3a, and 3b without an explicitly stated *destination* — the existing `mission.md` describes the framework's mechanics ("discipline layer," "adaptive ceremony," "self-correcting pipeline") but does not name the durable property those mechanics serve. This was tolerable while Writ was small enough that the maintainer's intent could be inferred from the artifacts. At 29 commands, 7 agents, and 5 prior ADRs, the absence of a stated destination has begun to cost coherence: every new feature has to be re-justified from first principles rather than tested against a clear thesis.

The recent strategic refresh ([research](../research/2026-04-24-writ-vs-gstack-rigor-comparison.md), particularly the addendum) surfaced this gap and forced a choice: what is Writ's actual destination?

The question was put as three hypotheses during the `/plan-product` discovery, each a coherent product but pointing at a different roadmap:

- **Hypothesis A — Production-grade output is the destination.** Discipline is the means; auditability, reviewability, reproducibility are the tests.
- **Hypothesis B — Shipping quality faster is the destination.** Velocity matters; discipline serves it. (This is GStack's framing.)
- **Hypothesis C — Survivable methodology is the destination.** Plain-text + git + adapter abstraction means Writ outlives any AI platform.

Choosing among these is consequential because the existing architecture (9-gate pipeline, contract-first specs, drift logs, ADR-005's markdown-over-database choice, multi-platform adapter abstraction) optimizes for some hypotheses and against others. Choosing wrong means either reversing recent decisions (e.g., ADR-005) or compounding the misalignment.

**The question this ADR answers:** Which destination does Writ commit to as the root claim that all roadmap items, ADRs, and feature specs are evaluated against?

**Out of scope (decided elsewhere or later):**

- The audience question (solo vs. small-team) — see [ADR-007](./adr-007-team-audience-sequencing.md)
- The strategic moat / positioning — see [ADR-008](./adr-008-spec-as-team-contract-moat.md)
- Specific Phase 4 and 5 features — covered in the refreshed `roadmap.md`

## Decision Drivers

Force-ranked top three drivers — these are what tip the decision:

1. **Coherence with existing architectural commitments.** Reversing ADR-005 (markdown over database), the 9-gate pipeline, the contract-first specs, or the adapter abstraction would be hugely expensive. The destination chosen must compose with these, not contradict them.

2. **Strategic differentiation from competing frameworks.** GStack and similar velocity-first AI dev frameworks are well-established. Writ has limited surface area to differentiate; the destination chosen must define a position those frameworks structurally cannot enter without rebuilding.

3. **Solo-maintainer cost ceiling.** A destination that requires building or maintaining infrastructure beyond markdown + git + shell scripts is infeasible at current resourcing. The chosen destination must be reachable with the existing substrate.

Other relevant factors (real but lower-priority):

- **Persona alignment** — the existing user persona (the Ambitious Solo Builder) speaks of shipping with confidence and avoiding rework, not enterprise audit compliance. The destination's user-facing framing must respect persona vocabulary.
- **Forward compatibility with the team-collab trajectory** ([ADR-007](./adr-007-team-audience-sequencing.md))
- **Honest evidence base** — limited to: existing artifacts, the research doc, ADR-005's recorded dissent. No external user research has been conducted. This is acknowledged in the dissent below.

## Considered Options

### Option 1 (Hypothesis A): Production-Grade Output as the Destination

**Approach:** Writ produces code and methodology that is auditable, reviewable, reproducible, onboarding-friendly, failure-isolatable. These are the six criteria from the [research addendum](../research/2026-04-24-writ-vs-gstack-rigor-comparison.md#production-grade-criteria-the-lens-used-below). Discipline is the means; production-grade output is the test.

**Pros:**

- Coheres with every existing architectural choice — ADR-005, the gate pipeline, contract-first specs, drift logs, ADR-004's context-first phasing all serve this destination directly
- Operationalizable via a `/audit` command (Phase 5) that scores projects against the six criteria — making the destination falsifiable
- Distinguishable from GStack's velocity-first framing without overlap

**Cons:**

- "Production-grade" is enterprise-sounding language; the persona doesn't talk that way
- Risks reading as "rigor for rigor's sake" if the connection to user value isn't explicit
- No external user has asked for "production-grade output" in those words — extrapolation from the persona's stated goals (ship with confidence, avoid rework)

**Effort:** Pure framing — no implementation cost beyond the refresh of mission/mission-lite/roadmap

**Risk:** Medium — if the framing is too enterprise-y, persona alignment suffers

### Option 2 (Hypothesis B): Shipping Quality Faster as the Destination

**Approach:** Writ exists to compress the time between idea and shipped quality. Discipline serves velocity; the gates exist because they catch problems faster than rework does. This is GStack's framing.

**Pros:**

- Closer to what most AI-dev users explicitly request ("make AI shipping faster")
- Aligns with the broader market signal (GStack at 82.4k stars suggests velocity-framed AI tools have larger audiences)
- Simpler vision pitch

**Cons:**

- **Invalidates ADR-005.** A markdown ledger is slower retrieval than a database; if velocity is the goal, the database might be right after all. ADR-005 was decided three weeks ago on production-grade reasoning; reversing it now requires new evidence (which doesn't exist).
- **Contradicts the 9-gate pipeline.** Gates trade velocity for quality; a velocity-first framing would rationalize reducing or removing them.
- **Already a crowded position.** GStack, Cursor's native flows, and others compete here directly. Writ's smaller surface area would be a disadvantage rather than a differentiator.
- **Persona mismatch is more subtle but real.** The Ambitious Solo Builder wants to ship with confidence — confidence is a *quality* word, not a velocity word. "Faster shipping with same quality" is GStack; "same shipping with higher confidence" is Writ.

**Effort:** Massive — would require reversing ADR-005, redesigning the gate pipeline, repositioning the framework end-to-end

**Risk:** High — would convert Writ into a less-resourced competitor in a market where the leader has 5+ years of head start

**Verdict:** Rejected — incompatible with existing commitments and strategically inverted

### Option 3 (Hypothesis C): Survivable Methodology as the Destination

**Approach:** Writ exists because AI platforms come and go, and methodology + plain-text artifacts are the only durable substrate. Production-grade and team-readiness are *expressions* of this; the deeper bet is on substrate stability across platform churn (Cursor → Claude Code → next-generation agent runtime).

**Pros:**

- True structural property of Writ's existing architecture — adapters, markdown artifacts, git as the substrate are all consequences of this principle
- More ambitious framing than A; opens doors to claims like "specs written in 2026 still work in 2031"
- Differentiates from any AI-tool-specific framework, not just GStack

**Cons:**

- Doesn't tell users *why* they should care today. Survivability is a future benefit; users want present value.
- Most of the existing architecture's choices (gates, drift logs, contract-first specs) aren't primarily about survivability — they're about quality. C frames C-style mechanisms but *under-claims* the quality dimension.
- Hard to operationalize — there's no `/audit-survivability` analog to the production-grade criteria

**Effort:** Pure framing

**Risk:** Medium — risks framing Writ as a long-term infrastructure bet that loses the present-value pitch

**Verdict:** Considered — captures a true structural property but is incomplete as a standalone destination

### Option 4: Hybrid A + C (Recommended)

**Approach:** Writ produces production-grade output (Hypothesis A — the destination) on a substrate that survives AI platform churn (Hypothesis C — the structural property that makes A defensible long-term). C is not a separate destination; it is A's structural payoff. The user-facing framing emphasizes the *outcome*: code and methodology that doesn't degrade as projects, teams, and AI platforms churn around them.

**Pros:**

- **Composes with all existing architectural commitments.** Every prior ADR, the gate pipeline, the markdown substrate, the adapter abstraction — all serve this destination directly
- **Persona-aligned framing.** "Doesn't degrade" is a quality-and-confidence word, the language the Ambitious Solo Builder actually uses
- **Operationalizable.** The six production-grade criteria become measurable via `/audit` (Phase 5). The survivability claim is testable via adapter coverage and platform-portability checks.
- **Strategic differentiation.** A position GStack and velocity-first frameworks structurally cannot take without rebuilding from scratch — see [ADR-008](./adr-008-spec-as-team-contract-moat.md)
- **Honest about the moat.** C is named as the structural reason A is defensible; the framework's choices aren't accidents, they serve a coherent thesis

**Cons:**

- Slightly more complex to communicate than a single-pillar destination ("non-degrading" requires a sentence of explanation)
- Risk of being read as two separate goals if the relationship between A (the destination) and C (the structural property) isn't kept clear

**Effort:** Same as Options 1 and 3 — pure framing

**Risk:** Low — coheres with existing system; refines rather than reverses

**Verdict:** Recommended

### Option 5 (Hypothesis B blended with A): Equal Pillars (Production-Grade AND Velocity)

**Approach:** Production-grade IS the goal, but velocity is a near-equal constraint. Refuse to optimize one at the expense of the other.

**Pros:**

- Honest about the tension that exists in real shipping
- Less polarizing than Option 4

**Cons:**

- **No real choice means no real direction.** "We want both" is a non-answer that lets every roadmap conflict re-litigate the priority
- Loses the strategic differentiation Option 4 offers
- Adaptive ceremony (existing Writ feature) already addresses the velocity-when-appropriate concern; elevating velocity to a co-equal pillar would over-correct

**Verdict:** Rejected — destinations require a primary; co-equal pillars are a planning anti-pattern

## Decision

**Chosen: Option 4 — Production-grade output as the destination, on a substrate that survives AI platform churn.**

User-facing framing: *"Code and methodology that doesn't degrade as projects, teams, and AI platforms churn around them."*

### Rationale

The decision is determined by Drivers 1 and 2:

**Driver 1 (coherence) makes Options 2 and 5 infeasible.** Option 2 (velocity-first) requires reversing recent commitments — most acutely [ADR-005](./adr-005-knowledge-substrate-markdown-over-database.md), which was decided this same month on production-grade reasoning. Option 5 (equal pillars) leaves every roadmap conflict unresolved.

**Driver 2 (differentiation) makes Option 1 alone insufficient.** Production-grade output is a defensible position, but without naming the structural reason it's defensible (C — the substrate), the framework reads as "another AI-dev framework that emphasizes quality." Option 4 names the moat: GStack and velocity-first frameworks *cannot* claim non-degradation because their substrate (per-skill state, browser daemons, database-backed memory) doesn't survive platform churn. Writ's substrate does, by construction. This is a position the competition structurally cannot enter — see [ADR-008](./adr-008-spec-as-team-contract-moat.md).

**Driver 3 (cost) supports Option 4.** No new infrastructure is required. The destination is a framing change plus a Phase 5 `/audit` command (~2-3 days) to make it falsifiable.

**Persona alignment:** "Doesn't degrade" is the right user-facing word. It's a quality-and-confidence framing, not an enterprise-compliance framing. It speaks to the Ambitious Solo Builder's stated pain (specs becoming fiction, returning to a feature six months later and not understanding it) without sounding like SOC 2.

### What This Commits Writ To

- The **non-degradation test** is the primary lens for evaluating new features. Every roadmap item must answer: "Does this strengthen non-degradation across project, team, and platform churn?"
- The **six production-grade criteria** (auditable, versioned, reviewable, reproducible, onboarding-friendly, failure-isolatable) are operationalized via the `/audit` command in Phase 5
- The **substrate (markdown + git + adapter abstraction)** is preserved; future ADRs that would compromise it require explicit rejection of this ADR
- The **roadmap parking lot** drops items that don't pass the non-degradation test (notification integrations, cross-AI parallel orchestration) — see refreshed `roadmap.md`

### What This Does Not Commit Writ To

- Specific feature implementations — those are decided in Phase 4/5 specs
- An "enterprise" or "compliance" framing in marketing or docs — the user-facing language is "doesn't degrade," not "production-grade audit trail"
- Abandoning velocity entirely — adaptive ceremony continues to right-size process for change scope; velocity is *constrained by* the destination, not eliminated

## Consequences

### Positive

- **Roadmap coherence:** every Phase 4 and Phase 5 feature traces to the destination; no orphan features
- **Strategic clarity:** GStack-style borrowings get a clean accept/reject test ("does this strengthen non-degradation?"); the borrowings the [research addendum](../research/2026-04-24-writ-vs-gstack-rigor-comparison.md) recommended all pass; the ones it rejected (browser daemon, database memory, parallel sprint flow) all fail
- **Persona-aligned framing:** "doesn't degrade" speaks to a real pain the user has named, in their own vocabulary
- **Composes with existing ADRs:** ADR-002 (evolution over fork), ADR-003 (context engine), ADR-004 (context-first phasing), ADR-005 (markdown over database) all become expressions of this destination

### Negative

- **Vision-language change has switching cost.** "Production-grade" and "non-degrading" are new vocabulary; existing community / documentation / blog posts (such as they are) will reference older framings
- **The framing requires a sentence to explain.** "Non-degrading" is not as immediately understandable as "ship faster" or "write better code"
- **`/audit` becomes load-bearing.** If `/audit` doesn't ship in Phase 5 or doesn't produce useful output, the destination claim becomes hand-wavy

### Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Vision-language drift over time as new contributors interpret "non-degrading" differently | Medium | Medium | This ADR is the canonical definition; mission.md cites it; Phase 5 `/audit` operationalizes the six criteria |
| `/audit` ships but produces unhelpful scorecards | Medium | High | Phase 5 spec must define concrete remediation actions per criterion; backfill against the Writ repo itself before declaring done |
| Persona pain doesn't actually map to "non-degrading" — users want speed and "non-degrading" reads as out-of-touch | Low-Medium | High | Watch for adoption signals; if the framing isn't resonating after 90 days, revise the user-facing language while preserving the architectural commitment |
| The "AND survivable substrate" half of the destination becomes invisible — only the production-grade part registers | Medium | Low | [ADR-008](./adr-008-spec-as-team-contract-moat.md) explicitly names the substrate as the moat; Phase 4 features (knowledge ledger, SKILL.md generation) make survivability concrete |

### Review Triggers

This ADR should be revisited if any of the following occur:

1. **`/audit` ships and reveals the six criteria don't actually capture what matters.** The criteria are the addendum's proposal, not gospel. Real usage may surface that 4 of 6 matter and 2 are noise, or that a 7th is missing.
2. **An external user articulates a destination Writ should serve that doesn't fit non-degradation.** Strong adoption signal in a different direction is new evidence.
3. **The substrate-survivability claim breaks empirically.** If a major AI platform shift happens and Writ doesn't, in fact, port cleanly, the C half of the destination needs reassessment.
4. **The team-collab event lands ([ADR-007](./adr-007-team-audience-sequencing.md))** and reveals that team-readiness needs a different vision frame than non-degradation provides.

## Recorded Dissent

Two genuine counter-positions worth recording:

**Dissent 1 — "No external user has asked for non-degrading output."** This is true. The decision is an extrapolation from the persona's stated pain (specs becoming fiction, returning to features and being unable to reconstruct decisions) to a destination claim. ADR-005's recorded dissent flagged the same pattern for the knowledge ledger. The honest answer: this destination is a bet on what the persona *would* recognize as their actual problem if asked the right way. The bet is small (framing only, no infrastructure cost) and the review triggers above will catch it if wrong.

**Dissent 2 — "Choosing A over B closes off the larger market."** GStack-style velocity-first AI dev frameworks have larger surface adoption signals (stars, contributor counts). Choosing the production-grade destination explicitly takes Writ further from that market. The honest answer: Writ's existing architecture is already aligned with A, not B. A maintainer with one person of capacity competing in a velocity-first market with limited differentiation would not win. Choosing A doubles down on a position where the architecture itself is the moat; choosing B would be running a different race with a much harder-to-defend position.

Both dissents are noted for the 90-day review.

## References

- [`.writ/research/2026-04-24-writ-vs-gstack-rigor-comparison.md`](../research/2026-04-24-writ-vs-gstack-rigor-comparison.md) — primary evidence base; especially the addendum's "Production-Grade Criteria" and Findings 7-9
- [ADR-005: Knowledge Substrate](./adr-005-knowledge-substrate-markdown-over-database.md) — the substrate decision this destination depends on
- [ADR-007: Team-Audience Sequencing](./adr-007-team-audience-sequencing.md) — the audience consequence of this destination
- [ADR-008: Spec-as-Team-Contract as Strategic Moat](./adr-008-spec-as-team-contract-moat.md) — the positioning consequence of this destination
- [`.writ/product/mission.md`](../product/mission.md) — the user-facing expression of this decision
