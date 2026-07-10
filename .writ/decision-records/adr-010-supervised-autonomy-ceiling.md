# ADR-010: Supervised Autonomy Ceiling at the Phase Level

> Status: Accepted
> Date: 2026-07-09
> Deciders: Adam (product owner)
> Part of: 2026-07-09 strategic refresh (`/plan-product` audit vs. current harnesses, GStack, GBrain)

## Context

Writ shipped two autonomy models. Ralph (Phase 3b, v0.10.0) is a fully autonomous bash loop: fresh-context CLI iterations against a file-based state contract, running unattended for hours. `/implement-phase` is a supervised orchestrator: one confirmation gate, then it loops `/implement-spec` → `/create-uat-plan` across a roadmap phase within a session, with a bounded question policy and an honest completion report.

The 2026 landscape changed the calculus. Harnesses natively ship background agents, cloud agents, and scheduled automations — the bash-loop mechanism Ralph owns is being absorbed by platforms. Meanwhile the audit surfaced the deeper issue: unattended loops produce work faster than a solo maintainer can meaningfully review it. Velocity-first frameworks (GStack: 10–15 parallel sprints) celebrate this; Writ's destination is non-degrading quality, where unreviewed volume is a liability, not an asset.

The decision: where is Writ's autonomy ceiling?

## Decision Drivers

1. **Accountability over volume** — Writ's differentiator is output that holds up; autonomy that outruns review capacity undermines the destination
2. **Maintenance cost** — Ralph is ~550 command lines + shell script + prompt templates + state docs, all owned by Writ; native platform loops make this depreciating infrastructure
3. **Actual usage** — the supervised pipeline (`/create-spec` → implement family) is the proven essential surface; the unattended loop is not
4. **Preserve the good inventions** — Ralph's fresh-context finding, state schema rigor, and quarantine branching are valuable regardless of the loop mechanism

## Considered Options

**Option A — Keep both; reposition Ralph as one adapter of a platform-neutral loop contract.**
Pros: preserves the walk-away-overnight capability; hedges against future demand. Cons: continues owning loop infrastructure the platforms are absorbing; splits hardening effort across two autonomy models; keeps an unreviewable-volume mode in the product against the accountability driver. Effort: M (ongoing).

**Option B — Deprecate Ralph; make `/implement-phase` the deliberate ceiling and harden it. (Chosen)**
Pros: one autonomy model to harden; supervised shape matches the accountability driver; Ralph's durable inventions migrate rather than die; lightest harness. Cons: loses the unattended-overnight capability; users who wanted it must wait for a future revisit. Effort: S for deprecation + M for hardening.

**Option C — Double down on autonomy; extend Ralph toward native cloud agents and parallelism.**
Pros: competitive with GStack on velocity. Cons: directly contradicts the destination; solo-maintainer cannot review the output volume; largest surface growth. Effort: L–XL.

## Decision

**Option B.** `/implement-phase` — supervised, session-bound, single confirmation gate — is Writ's deliberate autonomy ceiling: human *on the loop* at phase level, *in the loop* at contract level. Ralph is deprecated (see ADR-012). Its durable inventions migrate into `/implement-phase` in Phase 6:

- **Fresh context per spec** — each `/implement-spec` runs in a fresh subagent; the orchestrator holds only state, sequencing, escalation
- **Quarantine branching** — failed spec work isolates on `writ/quarantine/{spec}`
- **State rigor** — `phase-execution-*.json` remains the resume/monitoring anchor
- **User Challenge framing** — mid-run scope decisions surface as: what the roadmap said / what we recommend / what context we might be missing / cost if we're wrong; never auto-decided

Fully autonomous loops are recorded as an explicit non-goal in `mission.md`.

## Consequences

**Positive:** One hardened autonomy model; ~1,000+ lines of owned loop infrastructure retired; the accountability story becomes a nameable differentiator against velocity-first frameworks; hardening effort concentrates on the surface users actually run.

**Negative:** The "plan it, walk away overnight, come back to PRs" capability is gone until revisited. Users who adopted Ralph must migrate to `/implement-phase` (migration note ships with the deprecation).

**Review trigger:** Revisit if (a) a concrete accountability mechanism emerges that makes unattended output reviewable at the rate it's produced (e.g., trustworthy machine-verifiable UAT), or (b) platform-native background agents mature to where the loop contract could be expressed purely as Writ state files with zero owned execution infrastructure.
