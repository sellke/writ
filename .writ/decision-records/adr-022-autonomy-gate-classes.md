# ADR-022: Autonomy Gate Classes — Where Humans Stay, and the Reversibility Precondition

> **Date:** 2026-08-11
> **Status:** Accepted
> **Category:** Autonomy & Governance
> **Extends:** [ADR-013](adr-013-recommended-autonomous-delivery.md) — classifies decisions within its evidence-based select-or-pause boundary; does not replace it
> **Origin:** `/plan-product` Phase 10 discovery (2026-08-11) — maintainer decision on human-gate placement

## Decision

Writ classifies every decision into one of five **gate classes**, recorded as a table in [`commands/_preamble.md`](../../commands/_preamble.md):

| Class | Behavior |
|---|---|
| **Product & spec direction** | **Human gate.** Contract lock (`/plan-product`, `/create-spec`, ADR decisions) stays an explicit human action |
| **Production boundary** | **Human gate.** No autonomous merge, PR open, release, tag, or publish — already a Prime Directive hard constraint |
| **Design & UX judgment** | **Human gate.** `/design`, visual QA, wireframe approval — taste is not evidence-decidable |
| **Destructive / irreversible** | **Autonomous, subject to a reversibility precondition** (below) |
| **Everything else** | **Autonomous** within ADR-013's evidence boundary, with audit rationale emitted |

### The reversibility precondition

A destructive-class operation may run unattended **only when both hold**:

1. Its effect is **provably git-revertable** — the mutation is confined to tracked files, with a resolvable revert target.
2. The **restore path is recorded before the mutation**, not after.

If either fails, the operation **pauses** with a bounded `AskQuestion`, exactly as ADR-013 specifies for material irreversible risk.

## Context

Phase 10's posture is "maximally autonomous except where taste and agency require humans." That requires naming *where*, because ADR-013 established the select-or-pause *mechanism* without enumerating which decision classes are categorically off-limits versus merely conditioned on evidence.

The maintainer was asked directly which classes must retain a human. They selected **product & spec direction**, **production boundary**, and **design & UX judgment** — and **deliberately did not select destructive / irreversible operations** (`/revert`, `/uninstall-writ`, `/reinstall-writ`, `/refactor` commits, force operations).

### The disagreement, recorded

A concern was raised at plan time that removing the human gate from destructive operations is a genuine safety regression, and the maintainer's choice was reaffirmed. Per the Prime Directive's rule that reversals require new evidence rather than pressure, the decision stands as the maintainer made it — but it is recorded here with the reasoning that makes it defensible rather than as an unexamined preference.

**The defensible reading:** under git, most of Writ's "destructive" operations are not actually irreversible.

- `/revert` produces revert *commits* — additive history, fully undoable.
- `/refactor` commits to a branch, one verified commit per concern, with tests green before and after.
- `/uninstall-writ` explicitly preserves everything under `.writ/` (specs, ADRs, research) by design.
- `/reinstall-writ` restores from upstream, and the manifest records baselines.

ADR-013 already permits autonomous selection for "low-risk, reversible choices with defensible evidence." Git-backed reversibility means these operations largely **qualify under the existing boundary** — they were being gated by category label rather than by risk assessment.

**What the precondition protects against:** the cases where that reading breaks. Untracked files, uncommitted work in the working tree, operations reaching outside the repo, and anything without a resolvable revert target are not git-revertable, and those are exactly the cases the precondition catches. The gate moves from *"is this command named something scary"* to *"is this specific invocation actually recoverable"* — which is both more permissive and more accurate.

### Why the three retained gates are retained

- **Product & spec direction** — contract-first is Writ's foundational design decision (ADR-001). A machine that picks the product defeats the layer's purpose.
- **Production boundary** — already a Prime Directive hard constraint and ADR-013's explicit "human production boundary." This ADR confirms rather than establishes it.
- **Design & UX judgment** — taste produces no observable evidence in ADR-013's sense. Its precedence chain (governance → locked artifacts → repo state → conventions → simplicity) has nothing to rank aesthetic options by, so ADR-013's own rule requires a pause: *"subjective taste without evidence"* is a listed pause condition.

## Considered Alternatives

**Keep destructive operations behind a human gate.**
The maintainer's choice was the opposite, and the concern is recorded above. Rejected on the maintainer's authority plus the git-reversibility argument. Honestly noted: this is the alternative to revisit first if an incident occurs.

**Gate by command name (a static blocklist).**
Rejected. Brittle and wrong in both directions — it blocks `/revert` on a clean tracked branch (safe) while permitting an "everything else" command that happens to write outside the repo (unsafe). Risk is a property of the invocation, not the name.

**No classification at all; let ADR-013's evidence boundary decide everything case by case.**
Rejected. ADR-013 supplies the mechanism but no categorical floor, so "taste" and "production boundary" would be re-litigated per invocation. Three hard gates plus one conditional class is cheap to state and cheap to check.

**Require human confirmation for anything touching untracked files.**
Folded into the precondition rather than adopted as a separate rule — this is precisely what "provably git-revertable" fails on.

## Consequences

**Positive**

- Autonomy expands measurably: destructive-class operations become available to autonomous execution without weakening ADR-013's actual risk standard.
- The gate test becomes verifiable (`is this git-revertable?`) rather than nominal (`is this command scary?`).
- The three retained gates are stated once in `_preamble.md` instead of implied across 31 command files.
- Aligns the framework's autonomy with the maintainer's stated preference — quality and autonomy by default, humans where taste and agency actually live.

**Negative**

- **This is a real reduction in safety margin, and it should be named as one.** A human gate catches mistakes that a reversibility check cannot — notably a *correct-and-reversible* operation performed on the *wrong target*. Git can undo the change; it cannot undo the lost time or the confusion.
- Reversibility is only as good as its proof. A bug in the precondition check converts a safety guarantee into a false assurance, and the check is now load-bearing in a way no prior Writ check has been.
- "Provably git-revertable" needs a concrete implementation. Until one exists, the precondition is prose, not enforcement — the same gap ADR-020 acknowledges for `exit_criteria`.
- Recording the restore path *before* mutating adds a write to every destructive operation, including a failure mode where recording succeeds and the mutation does not.

**Review trigger: 2026-11-11** (90 days post-ship). If any autonomous destructive operation has required manual recovery beyond `git revert` by that date, restore the human gate for that operation's class and record the incident here. A single such event is sufficient evidence to reverse this decision — which is the new evidence the Prime Directive requires.

## References

- Roadmap: [Phase 10 — Component Contract & Progressive Disclosure](../product/roadmap.md)
- Boundary being classified: [ADR-013](adr-013-recommended-autonomous-delivery.md) — evidence-based select-or-pause, human production boundary
- Contract-first foundation: [ADR-001](adr-001-askquestion-vs-plan-mode.md)
- Companion Phase 10 decisions: [ADR-020](adr-020-component-contract.md), [ADR-021](adr-021-progressive-disclosure-token-budget.md)
- Files: [`commands/_preamble.md`](../../commands/_preamble.md), [`system-instructions.md`](../../system-instructions.md) (Prime Directive), [`commands/revert.md`](../../commands/revert.md), [`commands/refactor.md`](../../commands/refactor.md)
