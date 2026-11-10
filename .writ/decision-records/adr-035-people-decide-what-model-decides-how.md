# ADR-035: People Decide What and Why; the Model Decides How; a Verifier Proves It

> **Date:** 2026-11-09
> **Status:** Accepted
> **Category:** Autonomy & Verification
> **Deciders:** @AdamSellke
> **Origin:** `/plan-product --reconcile` (2026-11-09). The maintainer's direction: give models as much control over the build as possible while still surfacing decisions to people at critical planning and direction points.
> **Supersedes:** [ADR-033](adr-033-doubt-gated-autonomy.md) (computed doubt, the supervisor agent, the decision log); what remained of [ADR-022](adr-022-autonomy-gate-classes.md), [ADR-013](adr-013-recommended-autonomous-delivery.md), and [ADR-010](adr-010-supervised-autonomy-ceiling.md); [ADR-028](adr-028-behavioral-verification-and-cross-family-panels.md) and [ADR-032](adr-032-evidence-gated-review.md) as mechanisms (their ideas carry into the verifier); [ADR-003](adr-003-context-engine-architecture.md); [ADR-017](adr-017-git-notes-audit-channel.md).
> **Amends:** [ADR-030](adr-030-contract-verifier-boundary-front-door.md): the contract stays, the verifier becomes proof of outcome, the boundary becomes one rule, and the front door stays.
> **Keeps:** [ADR-023](adr-023-stakes-proportional-diligence.md)'s principle that diligence follows stakes, now left to the model's judgment.
> **Evidence base:** [2026-11-09 surface audit](../research/2026-11-09-writ-1.0-surface-audit.md).

## Context

Writ 0.49 controlled the build with 42 mechanisms across three commands. The audit sorted them:

- 16 checked that the agent followed Writ's procedure. None has a recorded catch of a product defect.
- 9 checked the product. Four have recorded catches: a fresh reviewer that runs things, that reviewer naming the fact a change is safe because of, a pause on a large departure from the contract, and a check that a test can fail.
- Agents skipped the procedure anyway, and the procedure checker still passed them.

The boundary was meant to be computed: `jev-judge.py doubt` would decide each question. It never calibrated, so in practice it returned a fixed answer: ask on direction, design, merge, and release; act otherwise. About two-thirds of the ask sites in the commands were about method.

pstack went the other way on 2026-10-27: it deleted its orchestration scripts and kept a short list of principles.

## Decision Drivers

1. **A person's time goes to what only a person can decide.**
2. **Check the outcome, not the procedure.** Procedure checks did not stop skipped procedure and caught no defects.
3. **The author cannot be the verifier.** This is the one separation the evidence supports.
4. **Fewer parts.** Each mechanism removed is one that cannot drift, be worked around, or need its own tests.
5. **The person cannot review code** ([ADR-034](adr-034-product-manager-audience.md)), so proof must be something they can read and try.

## Considered Options

### Option A: Keep the gates, calibrate the doubt check

- **Pros:** No behaviour change. Enforcement stays in code.
- **Cons:** Ten overrides in 98 labels are too few to calibrate, and the code enforces procedure the evidence says does not matter.

### Option B: Remove the gates and trust the builder's report

- **Pros:** Smallest possible surface.
- **Cons:** The retro showed builders reporting done on work that was not reviewed. With a reader who cannot check the code, this is self-report all the way down.

### Option C: One rule for who decides, model-owned build, independent proof (chosen)

## Decision

**1. Who decides.** People decide what gets built and why. The model decides how. The person is asked about:

- direction: the problem, who has it, the objective and its measure, what comes first;
- the contract: scope, acceptance criteria, and any change to them after agreement;
- taste: which draft, and how anything users see looks, reads, or feels;
- acts that cannot be taken back or that speak for them: merging into the main branch, releasing, publishing, deleting data, sending a message as them.

Everything else the model decides, does, and reports. When running something would answer a question, it runs it. This is the fallback table `doubt` already returned, written as a rule.

**2. The build belongs to the model.** `writ-build` takes an agreed spec and names only what must hold: the smallest change that meets the contract, tests that fail without the change, one unit taken end to end before fan-out, and a stop when reality would change the contract. The plan, the design, the order, and the helpers are the model's. There are no gates, stories, lanes, state files, or loop counters.

**3. Nothing is done until someone other than its author has proved it.** `writ-verify` runs in a fresh context that has not seen the build. For each acceptance criterion it finds or writes the check that would fail if the criterion were false, runs it against the real product, keeps the evidence, and confirms that a passing test can fail. It names what the change relies on to be safe and tests that. Only a finding it reproduced blocks. Its verdict covers one commit. It writes the Proof into the spec in terms a person can follow, with steps to try it themselves.

**4. One file per agreement.** A spec is one `spec.md`: problem, outcome and measure, scope, acceptance criteria, decisions, proof. Changes after agreement go in its Decisions list, with the person's sign-off when they alter the contract.

**5. Merge and release are the person's word.** `writ-ship` opens the pull request without asking and works it to ready. It merges and releases when told.

## Consequences

**Positive**

- The three implement commands, nine agents, the pipeline skills, and the scripts behind them are replaced by two skills of about 60 lines each.
- Every question that reaches the person is one they can answer.
- The mechanisms with recorded catches all survive, inside the verifier.

**Negative**

- Enforcement moves from code to instruction. A verifier that does its job badly has nothing behind it. This is the largest risk in 1.0.
- Resumability relies on the spec, an optional `plan.md`, and git. There is no state machine to reconcile a crashed run.
- Rare failures that the old machinery had a net for (a failed spec polluting a shared branch) now rely on one branch per spec, merged only when proved.
- The autonomous merge built in Phase 16 is removed before it was ever exercised.

**Review triggers**

- A defect ships that the verifier marked `Proved`. Write the check that would have caught it, show that it fails on that case, and only then add it.
- A build finishes without a verifier verdict on its last commit. Add the one check that can be read from git: a proof whose commit matches the branch head.
- People report being asked about method, or not being asked about scope. Fix the rule's wording before adding machinery.
