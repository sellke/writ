# ADR-008: Spec-as-Team-Contract as Strategic Moat

> **Status:** Accepted
> **Date:** 2026-04-24
> **Deciders:** Product owner
> **Part of:** `/plan-product` strategic refresh (response to GStack rigor comparison)
> **Related:** [ADR-005](./adr-005-knowledge-substrate-markdown-over-database.md) (substrate enables review), [ADR-006](./adr-006-non-degrading-destination.md) (destination), [ADR-007](./adr-007-team-audience-sequencing.md) (audience timing)

## Context

The [research addendum](../research/2026-04-24-writ-vs-gstack-rigor-comparison.md) (Findings 7-9) identified a structural property of Writ that competing AI-dev frameworks — GStack and similar velocity-first frameworks — cannot replicate without rebuilding from scratch: Writ's specs are not just task lists, they are negotiated, versioned contracts that humans agree on *before* agents begin work. This contract surface is enabled by three architectural commitments already in place:

1. **Plain-text + git substrate** ([ADR-005](./adr-005-knowledge-substrate-markdown-over-database.md)) — specs are reviewable in PRs, diffable across versions, version-controlled with the code
2. **Contract-first command discipline** — `/create-spec`, `/edit-spec`, `/plan-product` all use Plan Mode + AskQuestion to lock contracts before any file is created
3. **Drift logs** — drift between spec intent and shipped reality is a first-class artifact, surfaced and reconciled rather than silently absorbed

This combination — *negotiated, versioned, reviewable, with deviations explicit* — is structurally absent from frameworks built on per-skill state, browser daemons, or database-backed agent memory. Those substrates trade reviewability for speed by design. Adding a contract layer to them would mean rebuilding the substrate.

The strategic question raised by the refresh: should Writ position around this property explicitly as the strategic moat, or treat it as one differentiator among several?

The risk of *not* claiming the moat: Writ continues to compete on the explicit attributes ("adaptive ceremony," "self-correcting pipeline," "clear steps") in a market where larger, better-resourced frameworks claim adjacent attributes. Without naming the structural advantage, Writ reads as "another methodology" rather than "the framework with a position the competition cannot enter."

The risk of claiming it: positioning around team-collab when the audience is solo today (per [ADR-007](./adr-007-team-audience-sequencing.md)) creates a vision-execution gap that requires explicit handling.

**The question this ADR answers:** Should Writ claim spec-as-team-contract as the explicit strategic moat, and if so, how does that positioning compose with the solo-first audience reality?

**Out of scope (decided elsewhere or later):**

- The destination — see [ADR-006](./adr-006-non-degrading-destination.md)
- The audience timing — see [ADR-007](./adr-007-team-audience-sequencing.md)
- The substrate that enables this property — see [ADR-005](./adr-005-knowledge-substrate-markdown-over-database.md)
- The specific shape of team-collaboration features — Phase 6+ implementation specs

## Decision Drivers

Force-ranked top three drivers:

1. **Strategic differentiation in a crowded market.** Writ has limited surface area to compete with established AI-dev frameworks. The position chosen must define a place those frameworks structurally cannot enter without restructuring.

2. **Coherence with existing architectural commitments.** The moat claim must be true *because of the architecture that already exists*, not aspirational. Claiming a moat that requires unbuilt infrastructure is hand-waving.

3. **Honest composability with the audience timing decision.** Per [ADR-007](./adr-007-team-audience-sequencing.md), team-collab is speculative-but-strategic — claimed in vision, deferred in execution. The moat positioning must be honest about this without hollowing out the claim.

Other relevant factors (real but lower-priority):

- **Solo-developer benefit** — even if the team-collab framing motivates the position, the solo developer has to get value from the same property today; otherwise it's marketing-only
- **Defensibility against pivots** — if a competing framework added contract-first specs tomorrow, would Writ's moat survive? (The answer must be yes, structurally.)
- **Honest evidence base** — limited to: research addendum's structural argument, ADR-005's substrate decision, observation of what GStack and similar frameworks have shipped publicly. No competitive interview data; no team-collab user signal.

## Considered Options

### Option 1: Claim the Moat Explicitly (Spec-as-Team-Contract) — Recommended

**Approach:** Position Writ around spec-as-team-contract as the explicit strategic moat. Frame it in `mission.md` and `mission-lite.md` as the differentiator that the competition cannot match without rebuilding their substrate. Cite the structural reasons. Acknowledge the solo-dev benefit (specs as a contract with future-self) so the framing serves today's audience.

**Pros:**

- **Driver 1 (differentiation):** Names a position that GStack and velocity-first frameworks structurally cannot enter — they would need to rebuild on plain-text + git, which contradicts their design philosophy
- **Driver 2 (coherence):** True today. The substrate ([ADR-005](./adr-005-knowledge-substrate-markdown-over-database.md)), the contract-first commands, and the drift logs all already exist; the claim doesn't require new infrastructure
- **Driver 3 (audience honesty):** Composes cleanly with [ADR-007](./adr-007-team-audience-sequencing.md) by framing the moat as "designed-on-paper, deferred-on-shipping" — the *substrate* exists today; team-specific affordances ship when triggered
- Solo-developer benefit is real: a spec is also a contract with the future self who returns to the project six months later. The moat framing extends to this case naturally.
- Aligns with [ADR-006's](./adr-006-non-degrading-destination.md) destination — non-degradation requires reviewable artifacts, which is what specs-as-contracts provide

**Cons:**

- Requires explanation. "Spec-as-team-contract" is not an immediately understandable phrase; needs a paragraph of context to land
- Vision-execution gap is visible. A reader excited by the moat framing will discover that team-specific features aren't shipped yet. Mitigation: explicit reference to [ADR-007](./adr-007-team-audience-sequencing.md) for the execution stance.
- Risk of being read as "team feature first" by solo readers — must keep the solo-future-self framing prominent

**Effort:** Pure framing — no implementation cost beyond the refresh

**Risk:** Low — the structural property exists today; the claim is verifiable

### Option 2: Don't Claim the Moat — Compete on Explicit Attributes

**Approach:** Continue to position Writ around the existing differentiators (adaptive ceremony, self-correcting pipeline, clear steps, methodology-not-tooling). Treat spec-as-team-contract as an emergent property, not a positioned one.

**Pros:**

- No vision-execution gap to manage
- Existing positioning continues unchanged
- No risk of being misread as team-first

**Cons:**

- **Driver 1 (differentiation) fails.** The existing differentiators are real but not structurally defensible — competitors can claim "adaptive ceremony" or "structured pipelines" with relatively minor positioning changes. Writ's biggest structural advantage stays invisible.
- Misses the chance to operationalize the substrate decisions ([ADR-005](./adr-005-knowledge-substrate-markdown-over-database.md), the gate pipeline) into a strategic claim
- Leaves the destination ([ADR-006](./adr-006-non-degrading-destination.md)) under-specified about *why* non-degradation is achievable; spec-as-contract is the structural answer

**Verdict:** Rejected — under-claims a real, defensible position

### Option 3: Claim a Different Moat (e.g., Adapter Abstraction)

**Approach:** Position Writ around platform-portability as the moat. The adapter abstraction means a Writ project survives Cursor → Claude Code → next-generation runtime transitions; competitors that bind to a specific platform structurally cannot match this.

**Pros:**

- True structural property
- No team-collab vision-execution gap
- Clean differentiation against AI-tool-specific frameworks

**Cons:**

- Adapter abstraction is real but its strategic value depends on actually-occurring platform churn. Without a platform-shift event, the moat is hypothetical.
- Less immediately actionable for users than the spec-as-contract framing — "your project survives platform churn" matters when churn happens; "your specs are reviewable contracts" matters every PR
- Composes weakly with [ADR-006's](./adr-006-non-degrading-destination.md) destination at the *coordination* level — most of the destination's six production-grade criteria are about reviewability and reproducibility, which spec-as-contract addresses more directly than adapter abstraction does

**Verdict:** Considered, rejected — true property but lower strategic leverage than Option 1

### Option 4: Claim Multiple Moats

**Approach:** Position Writ around both spec-as-team-contract AND adapter abstraction (and possibly markdown substrate) as a portfolio of moats.

**Pros:**

- Honest about the layered architecture
- Each moat is real

**Cons:**

- **Strategic anti-pattern.** Multiple moats dilutes positioning. A reader retains one moat at most; presenting three means none of them lands.
- The other "moats" (adapter abstraction, markdown substrate) are *enablers* of the spec-as-contract moat, not separate moats. Naming them as parallel moats obscures the real structural argument.

**Verdict:** Rejected — dilutes the position; the other layers are better framed as the *reasons* the primary moat is defensible

## Decision

**Chosen: Option 1 — Claim spec-as-team-contract explicitly as the strategic moat. Frame the substrate (plain-text + git, contract-first commands, drift logs) as the structural reasons the moat is defensible. Frame the solo-developer benefit (specs as future-self contract) as the today-value that earns the framing for the current audience.**

### Rationale

The decision is determined by Drivers 1 and 2:

- **Driver 1 (differentiation)** rules out Options 2 and 4. Not claiming the moat (Option 2) misses the strategic opportunity; claiming multiple moats (Option 4) dilutes any single one.
- **Driver 2 (coherence)** rules out Option 3 in favor of Option 1. Adapter abstraction is real but lower-leverage; spec-as-contract directly serves the destination ([ADR-006](./adr-006-non-degrading-destination.md))'s six production-grade criteria.
- **Driver 3 (audience honesty)** is satisfied by the framing rather than the choice — the moat is *claimed* in vision and *executed-via-substrate* today; team-specific affordances are deferred per [ADR-007](./adr-007-team-audience-sequencing.md). The vision claim is honest because the substrate is genuinely in place.

### Why GStack and Similar Frameworks Structurally Cannot Catch Up

Naming the structural reasons explicitly so the moat claim is auditable:

1. **Per-skill state in browser daemons (or database-backed agent memory) is not git-reviewable.** Adding a contract surface on top of these requires either replicating the substrate (not a small change) or accepting that the contract isn't reviewable in the same way (which negates the property).

2. **Velocity-first command flows skip the negotiation step.** Their command catalog is built around "agent does the work, human reviews after." Adding a "human negotiates the contract first" step contradicts the design philosophy and would slow shipping speed in a way the audience doesn't want.

3. **Drift between spec intent and shipped reality is invisible without explicit logs.** Frameworks without first-class drift artifacts can add per-spec drift tracking, but the reconciliation discipline is a cultural property of the framework, not a feature flag.

4. **Adapter abstraction means the contract substrate is portable across AI platforms.** A framework bound to a single platform cannot make the same survivability claim about the contracts; if the platform changes, the contract surface changes.

The point is not that competitors *cannot* address each property in isolation. The point is that the *combination*, with consistent semantics across the entire workflow, requires a coherent substrate decision they did not make. Catching up means rebuilding.

### Solo-Developer Benefit (Today-Value That Earns the Framing)

For the current solo audience, the moat translates to:

- **Specs as a contract with future-self.** Returning to a feature six months later, the spec, drift log, and ADRs reconstruct *why* decisions were made. This is the persona's stated pain ("Six months later... struggles to reconstruct why a decision was made") addressed directly.
- **PR-reviewable architecture decisions.** Even solo, the practice of writing reviewable artifacts produces better thinking. The "negotiation" is with one's own future self.
- **Drift-as-honesty.** When implementation diverges from spec, the drift log preserves the *honest* version of what was built, not the wishful version. This matters whether the audience is one person or a team.

These benefits exist today, with no team-specific features required. The team-collab framing is the *strategic* layer; the solo-future-self framing is the *immediate-value* layer. Both are honest.

### What This Commits Writ To

- `mission.md` and `mission-lite.md` name spec-as-team-contract as the strategic moat with explicit reference to this ADR for full reasoning
- The substrate decisions ([ADR-005](./adr-005-knowledge-substrate-markdown-over-database.md), contract-first command discipline, drift logs) are treated as load-bearing for the moat — future ADRs that would compromise them require explicit rejection of this ADR
- The solo-developer benefit (specs-as-future-self-contract) must be visible in the user-facing framing, not buried as a footnote
- The "designed-on-paper, deferred-on-shipping" stance from [ADR-007](./adr-007-team-audience-sequencing.md) is referenced in the vision so the execution timing is honest

### What This Does Not Commit Writ To

- Building team-specific features ahead of [ADR-007's](./adr-007-team-audience-sequencing.md) trigger events
- Marketing the moat in adversarial terms ("GStack can't do this") in user-facing docs — the structural argument lives in this ADR; the user-facing framing emphasizes what Writ *does*, not what competitors don't
- Removing the existing differentiators (adaptive ceremony, self-correcting pipeline, etc.) — those remain real differentiators; they are *expressions* of the underlying moat

## Consequences

### Positive

- **Strategic clarity** — Writ has a named, defensible position that ties the destination ([ADR-006](./adr-006-non-degrading-destination.md)) to a structural argument
- **Vision-execution coherence** — the substrate genuinely exists, so the moat claim is verifiable today
- **Composes with [ADR-007's](./adr-007-team-audience-sequencing.md) timing decision** — claiming the moat in vision while deferring team-specific features in execution is honest because the substrate is the moat, not the features
- **Solo audience served honestly** — the future-self framing extracts value from the same architecture that serves teams later
- **Roadmap coherence** — Phase 4-5 features become explicit substrate-strengthening (knowledge ledger, owner field, dependency block, status board) rather than miscellaneous improvements

### Negative

- **Vision-execution gap is visible.** A reader excited by the team-collab moat framing will discover that team-specific features aren't shipped yet. Mitigation: explicit citation of [ADR-007](./adr-007-team-audience-sequencing.md) at every team-collab claim.
- **Moat framing requires explanation.** Cannot be one-liner; needs a paragraph of context. Mitigation: `mission-lite.md` keeps the framing terse with a pointer to the full reasoning here.
- **Risk of being read as competitive marketing.** If the structural-comparison framing leaks into user-facing docs, it sounds defensive. Mitigation: keep adversarial framing in this ADR; user-facing docs describe positive properties.

### Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| A competing framework genuinely closes the moat by adding contract-first specs to a velocity-first substrate | Low | High | The structural argument relies on substrate, not feature presence; closing the gap requires substrate change, which would change the framework's identity. Watch for: any major AI-dev framework adopting markdown-in-git as primary substrate. |
| The team-collab framing dominates and the solo-future-self framing gets lost | Medium | Medium | Mission documents lead with the solo benefit; team framing is the strategic property. Quarterly review of framing balance. |
| The "spec-as-team-contract" phrase doesn't land with users — too jargony | Medium | Medium | Test framing in user-facing copy; if it doesn't resonate at 90 days, revise the user-facing language while preserving the structural claim |
| ADR-007 trigger never fires and the moat claim becomes hollow | Low-Medium | Medium | Per [ADR-007](./adr-007-team-audience-sequencing.md), the 1-year mark schedules a check; if no signal at that point, vision retreats and this ADR is re-evaluated |
| Substrate ADRs that would compromise the moat get proposed without referencing this ADR | Low | High | This ADR is in the canonical decision-records; future ADRs touching substrate must reference it |

### Review Triggers

This ADR should be revisited if any of the following occur:

1. **A competitor ships contract-first specs on a substrate that genuinely matches Writ's reviewability properties.** This would require evaluating whether the moat closes or whether the structural argument still holds (e.g., because the competitor's audience doesn't actually use the contract surface).
2. **An ADR-007 trigger fires** and team-affordance shipping reveals the moat framing was right or wrong about what teams actually want from the contract surface.
3. **User research surfaces that "spec-as-team-contract" framing doesn't communicate the value** — if the framing fails to land, revise the user-facing language while preserving the structural claim.
4. **A future research output identifies a more defensible moat** (e.g., a property of the architecture not currently named that has stronger differentiation). New evidence reopens the choice.
5. **At the 1-year mark from this ADR's date (2027-04-24)** — coordinated review with [ADR-007](./adr-007-team-audience-sequencing.md) on whether the moat-positioning is still earning its claim.

## References

- [`.writ/research/2026-04-24-writ-vs-gstack-rigor-comparison.md`](../research/2026-04-24-writ-vs-gstack-rigor-comparison.md) — primary evidence base; Findings 7-9 and the addendum's "Spec-as-Team-Contract: Writ's Wedge" section
- [ADR-005](./adr-005-knowledge-substrate-markdown-over-database.md) — substrate decision that enables the moat
- [ADR-006](./adr-006-non-degrading-destination.md) — destination this moat serves
- [ADR-007](./adr-007-team-audience-sequencing.md) — audience timing stance the moat positioning composes with
- [`.writ/product/mission.md`](../product/mission.md) — user-facing expression of the moat (Non-Degrading by Construction differentiator)
- [`.writ/product/roadmap.md`](../product/roadmap.md) — Phase 4-5 substrate-strengthening features
