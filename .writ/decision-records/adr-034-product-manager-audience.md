# ADR-034: Writ Is Built for the Semi-Technical Product Manager

> **Date:** 2026-11-09
> **Status:** Accepted
> **Category:** Product & Audience
> **Deciders:** @AdamSellke
> **Origin:** `/plan-product --reconcile` (2026-11-09). The maintainer's direction: tailor Writ to the semi-technical product manager who wants to discover solutions to problems and help a business reach its objectives by building great products.
> **Supersedes:** the primary and secondary personas in `mission.md` (the Ambitious Solo Builder, the Framework Tinkerer).
> **Keeps:** [ADR-006](adr-006-non-degrading-destination.md) (plain files in git that outlast tools), [ADR-008](adr-008-spec-as-team-contract-moat.md) (the spec as the contract), [ADR-007](adr-007-team-audience-sequencing.md) (team features wait for a concrete signal).
> **Evidence base:** [2026-11-09 surface audit](../research/2026-11-09-writ-1.0-surface-audit.md).

## Context

Writ 0.x was written for a developer working alone. Its commands spoke in gates, stories, lanes, coverage thresholds, and commit SHAs, and its questions were mostly about method: retry or skip, which route, how to resolve a blocked agent. A developer can answer those. A product manager cannot, and should not have to.

Two things changed. Current models can own the build end to end when they are given a clear contract and an honest check. And the person with the scarcest knowledge in a product effort is the one who knows the user, the business objective, and what "good" looks like. That person is usually not the one who can review a diff.

No product manager has used Writ. This decision rests on the maintainer's judgment of where the leverage is, not on user research.

## Decision Drivers

1. **Put the person where only a person can decide.** The problem, the objective, the scope, taste, and the decision to ship.
2. **Let the model do what it is good at.** Design, code, tests, and fixing what breaks, without a procedure written for weaker models.
3. **Trust without code review.** The person must be able to believe the result from evidence stated in their own terms.
4. **One audience, served well.** A tool that speaks to both the builder and the owner ends up speaking builder.

## Considered Options

### Option A: Stay with the solo developer

- **Pros:** The existing users. No rewrite of language or reports.
- **Cons:** The developer needs Writ least as models improve; much of 0.x re-implemented what the harness now does. The audit found four commands carrying 62% of use.

### Option B: Serve both, with a developer mode and a product mode

- **Pros:** Nobody is left behind.
- **Cons:** Two vocabularies, two report formats, and a switch to maintain. The surface grows again.

### Option C: The semi-technical product manager (chosen)

Someone who can read a summary of a change and run a product locally, who thinks in users, objectives, and scope, and who does not review code.

- **Pros:** One vocabulary. Every question Writ asks is one this person can answer. The contract and the proof become the whole interface.
- **Cons:** Unproven demand. A developer who wants gate-level control loses it. Existing 0.x projects break.

## Decision

Writ's user is the semi-technical product manager. Every skill is written so that:

- the only questions put to the person concern direction, the contract, taste, and acts that cannot be taken back;
- reports lead with what changed for the product's users and what waits on the person, in plain words;
- the product plan is stated as an objective, a measure, and bets, not as phases of engineering work.

A developer can still use Writ. It will not speak to them differently.

## Consequences

**Positive**

- The surface shrinks to what one audience needs.
- The contract (`spec.md`) and the proof become the two documents a person decides from, which gives the verifier and Jev a clear place to work ([ADR-035](adr-035-people-decide-what-model-decides-how.md), [ADR-037](adr-037-jev-second-reader.md)).

**Negative**

- No evidence yet that product managers want this. Until one uses it unaided, the audience is a bet.
- The person cannot catch a bad build by reading it. All trust rests on the proof.
- 0.x commands, reports, and habits are gone. Projects mid-flight must uninstall 0.x and adopt the new spec format for new work.

**Review triggers**

- A product manager cannot get from a problem to a shipped change without a developer translating: revisit the vocabulary, then the audience.
- Verified work fails in users' hands more than once: revisit ADR-035's verifier before anything else.
- A second person joins a Writ project: ADR-007's trigger for team features.
