# ADR-007: Speculative-but-Strategic Team-Audience Sequencing

> **Status:** Accepted
> **Date:** 2026-04-24
> **Deciders:** Product owner
> **Part of:** `/plan-product` strategic refresh (response to GStack rigor comparison)
> **Related:** [ADR-005](./adr-005-knowledge-substrate-markdown-over-database.md) (substrate enables team review), [ADR-006](./adr-006-non-degrading-destination.md) (destination), [ADR-008](./adr-008-spec-as-team-contract-moat.md) (positioning)

## Context

The recent strategic refresh ([research](../research/2026-04-24-writ-vs-gstack-rigor-comparison.md), particularly Findings 7-9 of the addendum) reframed Writ's audience trajectory: solo developers today, with small-team collaboration as a stated near-term goal. ADR-005's recorded dissent flagged a related concern explicitly: *"Is the knowledge ledger valuable enough to justify building it before any user has asked for it? It's an engineering investment based on extrapolation, not user research."*

The same question applies more broadly to the audience pivot. The research recommended six prioritized moves; some of them (knowledge ledger, SKILL.md generation, eval Tier 1) benefit solo work directly. Others (spec-as-team-contract enhancements, multi-developer drift reconciliation, cross-spec dependency tracking, `/review-spec`) only earn their effort if the team-collab event actually materializes within a useful window.

Building team affordances before they're needed wastes scarce solo-maintainer capacity now and leaves stale features cluttering the surface area later. Building them too late means scrambling to ship them when a teammate arrives, with the worst possible context-switching cost. The asymmetry of the two errors depends entirely on the timing window — and the timing window is not currently observable from any external signal.

**The question this ADR answers:** Given no concrete team-collab signal today, how should the timing of small-team-collaboration affordances be sequenced into the roadmap?

**Out of scope (decided elsewhere or later):**

- Whether the team-collab pivot is worth claiming in vision at all → Decided: yes ([ADR-006](./adr-006-non-degrading-destination.md), [ADR-008](./adr-008-spec-as-team-contract-moat.md))
- Specific team-affordance feature shapes (cross-dev drift reconciliation, `/review-spec` semantics) → Implementation specs when they ship
- Whether the substrate moves (knowledge ledger, owner field, dependency tracking) ship anyway → Yes; they pay off solo

## Decision Drivers

Force-ranked top three drivers:

1. **Solo-maintainer capacity is the binding constraint.** The [research addendum's](../research/2026-04-24-writ-vs-gstack-rigor-comparison.md) Risk #1 — "Solo-maintainer asymmetry: borrowing too much in one cycle stalls the maintainer" — is the most important risk to this entire refresh. Any roadmap decision that ignores capacity is wrong by construction.

2. **No concrete team-collab signal exists.** The persona is solo. No teammate is in motion. No inbound user has asked for team affordances. ADR-005's dissent generalizes: building for an unobserved demand is extrapolation, and extrapolation has cost.

3. **Asymmetry of being wrong.** Building team affordances early when teams don't arrive: wasted capacity, stale surface area, dilution of focus. Building them late when teams do arrive: a scramble, but the *substrate* is already in place from Phase 4 work that paid off solo. The cost asymmetry favors waiting.

Other relevant factors (real but lower-priority):

- **Vision-execution coherence** — the destination ([ADR-006](./adr-006-non-degrading-destination.md)) and the moat ([ADR-008](./adr-008-spec-as-team-contract-moat.md)) both name team-collab as part of the strategic claim. Execution sequencing must honor the vision claim without overcommitting capacity.
- **Forward compatibility** — substrate decisions made now should make the team-collab event cheap to absorb when it arrives, regardless of when that is
- **Honest evidence base** — limited to: the research addendum's hedged claims, ADR-005's dissent, and the maintainer's own assessment that team-collab is "speculative-but-strategic"

## Considered Options

The discovery surfaced five timing windows for the team-collab event (the moment a second human starts using Writ on a shared project). Each implies a different sequencing.

### Option 1: Already Happening / Imminent (<3 months)

**Approach:** Treat team-collab as live. Ship `/review-spec`, multi-developer drift reconciliation, cross-spec dependency tracking, and a status board within Phase 4-5.

**Pros:**

- No scramble when teammates arrive — affordances are already in place
- Vision and execution fully aligned

**Cons:**

- No actual signal supports this window
- ~3-5 days additional Phase 4-5 effort spent on features no one is using
- Solo dogfooding of team-only features is contrived; would not validate the design

**Verdict:** Rejected — no evidence supports this window

### Option 2: Near-Term (3-6 months)

**Approach:** Build substrate now (Phase 4), ship the simpler team affordances (owner field, dependency block, status board) in Phase 5. Defer the heavier ones (`/review-spec`, multi-dev drift reconciliation) to Phase 6.

**Pros:**

- Aggressive but staged
- Substrate pays off solo; simpler affordances are dual-use

**Cons:**

- The Phase 5 team-affordance items are not validated against any user; they're a guess at what teams will need
- Same concern as Option 1, scaled down: capacity spent on un-validated team work

**Verdict:** Considered, rejected — no signal supports the 3-6 month window either; the simpler affordances should still be in Phase 5 (per Option 4) but framed as substrate, not team-specific

### Option 3: Medium-Term (6-12 months)

**Approach:** Build substrate now (Phase 4), design team affordances on paper but don't ship them. When the 6-12 month signal arrives, the design exists.

**Pros:**

- Lower capacity cost than Options 1-2
- Some preparation for the team-collab event

**Cons:**

- "Designed on paper" is shelfware that decays; design done now without real users will be stale by the time it ships
- Still based on a hypothetical timing window

**Verdict:** Considered, rejected — design-without-users decays; better to design when a real signal arrives

### Option 4: Speculative-but-Strategic (12-18+ months) — Recommended

**Approach:** Claim the team-collab pivot in vision (per [ADR-006](./adr-006-non-degrading-destination.md), [ADR-008](./adr-008-spec-as-team-contract-moat.md)) but defer team-specific execution until a concrete signal arrives. Build only the substrate that is *dual-use* — pays off solo AND prepares for teams. Define an explicit trigger event for re-evaluation.

The dual-use test: every Phase 4-5 feature must answer "does this benefit solo work AND set up team-readiness?" Items that pass: knowledge ledger, SKILL.md generation, preamble enforcement, eval Tier 1, spec frontmatter `owner:` field, dependency block, status board, `/audit`, `/lessons`. Items that fail and are therefore deferred: cross-developer drift reconciliation, `/review-spec`, multi-repo orchestration.

**Pros:**

- **Driver 1 (capacity):** preserves solo-maintainer capacity for substrate work that has guaranteed solo value
- **Driver 2 (no signal):** doesn't extrapolate from absence of signal; waits for a real one
- **Driver 3 (asymmetry):** when teams do arrive, the substrate is in place — owner field, dependencies, status board, `/audit` all become immediately useful for teams without rework
- Vision (claim the moat) and execution (defer team-only work) stay coherent because the vision says *the substrate exists*, which it does, while team-specific affordances are honestly described as "designed-on-paper, deferred-on-shipping"
- Allows the dissent voiced in ADR-005 to remain honest: we're not building for users who haven't asked; we're building for users who *have* asked (the solo persona) in ways that *also* serve future teams

**Cons:**

- If team-collab event arrives sooner than 12 months, there is a brief scramble to ship `/review-spec` and multi-dev drift reconciliation
- The vision claim ("team-ready substrate") is partly aspirational until a real team validates it

**Effort:** Same as the destination decision — pure sequencing

**Risk:** Low — failure mode is "scramble when teams arrive," which is recoverable; the inverse failure mode (capacity wasted on un-needed features) is not recoverable

**Verdict:** Recommended

### Option 5: Indefinite — Solo-First, Team-Compatible

**Approach:** Drop the team-collab pivot from vision entirely. Position Writ as solo-only. If teams adopt it, that's incidental; the framework is "compatible-with" team use but not "targeted-for."

**Pros:**

- Maximum focus
- No vision-execution coherence concerns

**Cons:**

- **Throws away the strategic moat ([ADR-008](./adr-008-spec-as-team-contract-moat.md)).** Spec-as-team-contract is the wedge GStack structurally cannot enter; abandoning the team claim abandons the moat
- Reduces Writ's distinctiveness in the AI-dev framework space
- The substrate work that's worth doing for solo (knowledge ledger, owner field) does almost all of the team-readiness preparation anyway — so the "indefinite" framing is honest about the audience but misses the strategic positioning win

**Verdict:** Considered, rejected — sacrifices strategic positioning for marginal additional focus

## Decision

**Chosen: Option 4 — Speculative-but-Strategic. Vision claims the team-collab pivot; execution defers team-specific affordances until a concrete signal arrives. The substrate built now is dual-use (pays off solo, prepares for teams).**

### Rationale

The decision is determined by all three drivers:

- **Driver 1 (capacity)** rules out Options 1-2; both spend capacity on un-validated team work
- **Driver 2 (no signal)** rules out Option 3; designing for hypothetical 6-12 month windows produces shelfware
- **Driver 3 (asymmetry)** favors waiting because the inverse risk (over-building for unrealized demand) is irrecoverable, while the named risk (scramble when teams arrive) is recoverable given the substrate that Phase 4-5 will have built

Option 5 is rejected on strategic-positioning grounds, not capacity grounds — the substrate work for "team-readiness" is doing double duty for solo, so abandoning the vision claim costs nothing in capacity and loses the moat.

### Sequencing Principle (Operationalized)

Every Phase 4 and Phase 5 feature must pass the **dual-use test**:

> *Does this feature benefit solo work AND set up team-readiness later?*

- **Pass → ship in Phase 4 or Phase 5.** Examples: knowledge ledger, SKILL.md generation, eval Tier 1, owner field, dependency block, status board, `/audit`, `/lessons`.
- **Fail → defer to Phase 6+ when triggered by signal.** Examples: cross-developer drift reconciliation, `/review-spec`, multi-repo orchestration, `/audit`'s team-semantics extensions, multi-developer status board view.

The roadmap's Beyond Phase 5 parking lot already classifies these — see refreshed `roadmap.md`.

### Concrete-Signal Event (Trigger for Re-evaluation)

This ADR commits to re-evaluating the audience timing when **any one** of the following events occurs:

1. **Active team-on-shared-project signal:** A second human starts using Writ on a project the maintainer is also working on, OR the maintainer starts using Writ on a project owned by another developer.
2. **External team-adoption signal:** An organization, team, or pair of contributors files an issue, sends a message, or contributes a PR explicitly requesting team-collaboration features (cross-dev drift reconciliation, `/review-spec`, multi-developer status board, etc.).
3. **Public adoption signal:** A community thread, blog post, or external review explicitly cites Writ's team-collaboration story (positively or negatively) at sufficient signal volume to indicate the audience pivot is happening organically.

When any of these occurs, this ADR is re-opened and the deferred items in the Beyond Phase 5 parking lot are re-prioritized.

### What This Commits Writ To

- Phase 4-5 features must pass the dual-use test before being scoped
- Vision documents (`mission.md`, `mission-lite.md`) may *claim* team-readiness as a strategic property, with explicit reference to this ADR for the execution stance
- Every spec for a Phase 4-5 feature must briefly note whether the dual-use test passed and how
- The trigger events above are the only basis for accelerating team-specific work

### What This Does Not Commit Writ To

- A specific timeline beyond "wait for signal"
- A guarantee that team affordances will ship within any specific window after a signal arrives — the response will be sized to capacity at that time
- Refusing to discuss team affordances in design conversations — the *design* of team-only features can happen when a concrete signal triggers it; what's deferred is *shipping*, not thinking
- Removing the team-collab claim from vision; the claim stays, the timing softens

## Consequences

### Positive

- **Solo capacity preserved** for the substrate work that has guaranteed value
- **Vision integrity** — the team-collab claim is honest because the substrate genuinely is being built
- **Recoverable failure mode** — if signal arrives sooner than expected, the substrate is in place and team-specific features are an incremental layer
- **Composes with [ADR-008](./adr-008-spec-as-team-contract-moat.md)** — spec-as-team-contract is positioned as the moat in vision; the moat exists structurally even before team-specific affordances are shipped
- **Honest about uncertainty** — the ADR records that no signal exists today; future maintainers and contributors aren't misled

### Negative

- **Vision-execution gap is visible.** A reader of `mission.md` who is excited by the team-collab framing will discover that team-specific features aren't shipped yet. Mitigation: the mission and roadmap both link to this ADR, which is honest about the stance.
- **Risk of permanent deferral** if no signal ever arrives — the deferred items become permanent shelfware. Mitigation: the parking lot's "deferred" classification is a status, not a graveyard; periodic review of the trigger events catches any organic signal that's been missed.
- **The dual-use test can be gamed** — features that aren't actually dual-use can be rationalized as such. Mitigation: spec-creation discipline; this ADR's framing is the canonical reference.

### Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Team-collab event arrives sooner than 12 months and the response feels rushed | Low-Medium | Medium | The dual-use substrate (owner field, dependency block, status board, `/audit`) carries most of the load; team-specific features layer on cleanly |
| No signal ever arrives and the team-collab vision claim becomes empty | Medium | Medium | 90-day review (per the substrate ADR-005 timeline) checks for signals; if absent at 1-year mark, revise vision |
| Capacity savings get spent on something other than the destination | Medium | Low | Phase 4-5 sequencing is itself the answer to "what to spend capacity on"; the destination ([ADR-006](./adr-006-non-degrading-destination.md)) is the test |
| The dual-use test is misapplied and team-only features sneak into Phase 4-5 | Medium | Low | Spec-creation discipline; explicit dual-use note required in each spec |
| Honest dissent ("we're building for users who haven't asked") gets papered over | Low | High | This ADR records the dissent in its own Decision Drivers; ADR-005's recorded dissent makes the same point at the substrate level |

### Review Triggers

This ADR should be revisited if any of the following occur:

1. **Any of the three concrete-signal events fires.** Even one of them triggers a full re-evaluation.
2. **Phase 4 or Phase 5 ships and the dual-use test reveals it was too permissive or too strict** in classifying features. The criteria themselves may need refinement.
3. **A second ADR is proposed that depends on team-affordance availability** — e.g., a future research output that recommends team-only features as a primary roadmap direction. That would be a new evidence event.
4. **At the 1-year mark from this ADR's date (2027-04-24)** if no signal has fired, schedule a check: is the team-collab claim still credible, or should the vision retreat to solo-only?

## References

- [`.writ/research/2026-04-24-writ-vs-gstack-rigor-comparison.md`](../research/2026-04-24-writ-vs-gstack-rigor-comparison.md) — primary evidence base; Findings 7-9 and the addendum's "Spec-as-Team-Contract" framing
- [ADR-005](./adr-005-knowledge-substrate-markdown-over-database.md) — recorded dissent on extrapolation-without-user-research applies here
- [ADR-006](./adr-006-non-degrading-destination.md) — the destination this sequencing serves
- [ADR-008](./adr-008-spec-as-team-contract-moat.md) — the strategic moat that depends on the substrate this ADR commits to building
- [`.writ/product/roadmap.md`](../product/roadmap.md) — Phase 4-5 feature list and Beyond Phase 5 parking lot
