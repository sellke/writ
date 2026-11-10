# ADR-033: Ask on Doubt, Not on Principle

> **Superseded 2026-11-09** by [ADR-035](adr-035-people-decide-what-model-decides-how.md). Kept as history.

> **Date:** 2026-11-05
> **Status:** Accepted
> **Amended:** 2026-11-05 — what the Phase 17 build changed; 2026-11-06 — merge acts under the ledger (see § Amendments)
> **Category:** Autonomy & Governance
> **Deciders:** @AdamSellke
> **Origin:** `/plan-product --reconcile` (2026-11-05). The maintainer's direction: a person's time and judgment are called on only when there is reasonable doubt about the right answer; the harness takes initiative and keeps itself honest; a supervisor checks subagent work; Jev makes the first-pass call on whether a person is needed.
> **Supersedes:** [ADR-022](adr-022-autonomy-gate-classes.md) § the gate-class table (the three categorical human gates: product and spec direction, the production boundary, design and UX judgment); [ADR-013](adr-013-recommended-autonomous-delivery.md) § `--recommend` as the only autonomous mode.
> **Keeps:** ADR-022's reversibility precondition; ADR-013's audit requirements (now the decision log every run writes) and its evidence precedence; [ADR-010](adr-010-supervised-autonomy-ceiling.md)'s accountability driver; [ADR-023](adr-023-stakes-proportional-diligence.md)'s stakes triage, of which this record is the gate side; [ADR-024](adr-024-model-delegation.md)'s family lock; [ADR-027](adr-027-optional-judgment-provider.md)'s double opt-in and cascade rule.
> **Amends:** [ADR-030](adr-030-contract-verifier-boundary-front-door.md) § Keeps and § Review: this is the ceiling ADR Phase 16 waited for. ADR-027 gains a third site, `doubt`; its promotion rule for the evaluator spawn is unchanged.
> **Evidence base:** the 2026-11-05 reconcile pass (roadmap Revision Log), the [Phase 15 retro](../retros/2026-10-30-phase-15.md), Phase 12's two UAT plans, the [removal trial](../specs/archive/2026-10-25-gate-upgrade-removal-measurement/trial-report.md) and [divergence trial](../specs/archive/2026-10-25-design-divergence/trial-report.md) reports, `python3 scripts/jev-judge.py shadow-report`.

## Decision

**Writ decides, acts, and records. It asks a person only when it is in reasonable doubt.**

1. **One rule replaces the gate-class table.** A decision is not routed to a person because of what category it falls in. It is routed when the harness cannot establish the answer to its own satisfaction. Doubt is derived from three things Writ already records:
   - the **evidence rung** behind the claim the decision rests on (`claimed`, `read`, `traced`, `tested`, `reproduced`, from `skills/blast-radius`), against a per-site floor;
   - **reversibility**, by ADR-022's precondition: the effect is git-revertable and the restore path is recorded before the mutation;
   - a **calibrated typed judgment** over the decision record (point 2).

   Any one of the three below its floor → stop and ask one bounded question. Otherwise act, and write the decision, its evidence, the alternatives, and the result to the run's decision log. No class is exempt. Product direction keeps most of its questions, because at discovery the evidence for "what the user wants" is the user; the rule produces the same question for a reason instead of a category.

2. **Jev makes the first-pass call.** `scripts/jev-judge.py` gains a `doubt` site: given the decision record (the question, the options, the recommended answer, the evidence rungs, the reversibility finding), it returns the probability that the recommended answer needs a person. Thresholds are calibrated per site against labeled outcomes, and the labels come from Writ's own history: `recommendation-log.md` files, the two recorded User Challenges, and transcript turns where a person answered an AskQuestion (did they take the `(Recommended)` option?). **With no provider configured, or an answer below its threshold, the fallback is today's ADR-022 table: ask.** Behavior never gets looser without the oracle. ADR-027's double opt-in, cascade rule, and privacy terms apply unchanged.

3. **A supervisor agent checks every subagent result before an orchestrator accepts it.** Fresh context, read-only, floor tier. It re-runs the checkers that apply (`exit-criteria.py`, `spec-status.py`, `drift-format.py`, `ac-trace.py`, `repro-order.py`), compares each claim in the report to the diff and the disk, and returns `ACCEPT`, `RERUN`, or `ESCALATE` with a claims table (`claim`, `evidence`, `verified` / `unverified` / `false`). It does no gate's work and writes no code. It replaces the orchestrator's inline trust in `/implement-spec` and `/implement-phase` and the `subagent-result-completeness` prose, so it is a consolidation, not a new layer. It is kept only if a removal measurement on the Phase 15 transcripts shows it catching a report that `exit-criteria.py` passed.

4. **`--recommend` retires as a flag.** Initiative is the default posture of every command. The recommendation log becomes the decision log every run writes, under one schema. The recommend-mode branches, the invocation matrices, the "narrow recommended-delivery exception" in `commands/_preamble.md`, and the Recommended Delivery Exception block in `system-instructions.md` go. The `eval.sh` pins that hold that prose in place are updated in the same spec.

5. **The production boundary is re-read under the rule, not exempted from it.** Merge to the default branch is git-revertable, and Phase 16 gives it a verification ledger bound to the PR head SHA and patch-id. With that ledger green and doubt below the floor, `/ship` merges and tells the person; otherwise it stops at merge-ready and asks. Release, tag, and publish are outward-facing and not revertable, so they stay asks until a site measurement says otherwise. Opening a PR is reversible and asks nothing.

6. **The loop that keeps it honest.** Every override of an autonomous decision, and every answer to an ask, is a labeled example. Thresholds recalibrate from them. `/retro` reads the decision log beside the transcripts. A site whose asks are answered "as recommended" above its threshold is an autonomy candidate; a site with an override on an irreversible act tightens to always-ask until re-measured.

## Context and Problem Statement

What holds on 2026-11-05:

- ADR-022 places humans by category: product and spec direction, the production boundary, and design and UX judgment are human gates regardless of evidence. ADR-013 confines autonomy to two commands behind `--recommend`. `commands/` carries 86 `AskQuestion` sites. Every phase run so far recorded 2 User Challenges and 9 recommendation logs: asks are many, challenges are rare.
- The human-validation queue is where work stalls. Design Principle 8 (land before you add) exists because Phases 12, 14, and 15 all sat finished and unvalidated. When the queue was worked, the gated steps were handed back to agents at the maintainer's request: Phase 12's 89 UAT scenarios were run by an agent on 2026-10-31 (82 pass, 1 fail, 6 not run); the removal trial's labels were the assistant's (drift-log DEV-012); the divergence trial's blind ratings were an agent's (DEV-012). Phase 14 merged with its five person checks unticked, and Phase 15's 201 UAT scenarios are unrun. A gate the person delegates back to the model was never a human gate; it was a delay.
- Subagent reports are trusted unchecked. The Phase 15 retro found lanes that wrote code without spawning the coding agent while `exit-criteria.py` still said `met` (F6), Gate 3 verifiers scoring hand-typed excerpts instead of the reviewer's output (F8), specs stating counts nobody ran (F16), a lane brief and result that lived only in conversation (F22), and a coder that reported without running Gate 4's checks (F26). Scripts catch what they are pointed at; nothing re-derives the report as a whole.
- The opposite failure also occurs. In Phase 12's UAT a headless `/implement-story` asked the user at a Gate 4.5 `fail` where the command says never ask ([issue](../issues/bugs/2026-10-31-gate-4-5-fail-asked-instead-of-recoding.md)). Asking is the habit, not the rule.
- ADR-023 already prices diligence per decision by stakes, and names "no mechanically enforced efficiency constraint" as its accepted cost, with a review due 2026-11-11 on whether an unenforceable rule is indistinguishable from none. ADR-022 itself moved destructive operations from "is this command named something scary" to "is this invocation recoverable". This record finishes that move for the three classes ADR-022 left categorical, and gives ADR-023's triage an oracle and a log.
- The Jev pilot (ADR-027) calibrated spec-findings thresholds on 24 fixtures with zero clean false positives. Its Gate 3 shadow log holds 2 stories against a promotion rule of 30, so the evaluator-skip is not decided here and stays under ADR-027's rule.
- pstack's autopilot proceeds without asking on reversible work and lands PRs unattended; its merge gating is prose. ADR-030 declined that for the right reason (ADR-022's classes). The right reason is now a derived doubt, enforced in code, not a category.

## Decision Drivers

1. **A person's time is the scarce input.** A question the harness could have answered costs the person twice: once to answer, once to re-enter the context that was dropped while waiting.
2. **Accountability by record, not by permission.** ADR-010's driver stands: output must hold up. A decision log, a supervisor's re-derivation, and a head-bound verification ledger make work reviewable after the fact at the rate it is produced, which a permission prompt never did.
3. **Prove the artifact, then prove the report.** ADR-028 and ADR-032 moved verdicts from readings to runs. The same move applies to what an orchestrator believes about a subagent's work.
4. **Subtract before you add.** The class table, the recommend branches, and the confirm-every-time steps are the surface this record removes. The supervisor and the `doubt` site are what it adds.
5. **Never looser without evidence.** The fallback with no oracle is today's behavior. Thresholds start at "ask" and loosen only on labeled outcomes.

## Alternatives Considered

### Option A — Keep the class table; add Jev as an advisor

- **Pros:** No change to the boundary. The oracle's accuracy gets measured in shadow first.
- **Cons:** Every ask the maintainer would have delegated back still fires. The shadow adds cost and changes nothing until a later decision, which is the position ADR-027 already holds for the evaluator.
- **Effort:** S. **Risk:** Low change risk; the queue problem stays.

### Option B — Doubt-gated autonomy: derived doubt with Jev first pass, a supervisor, `--recommend` retired (chosen)

- **Pros:** One rule where there were a table, a flag, and an exception. The ask count falls where the record shows it can. Subagent reports get re-derived. Merge lands under a ledger instead of a prompt.
- **Cons:** "Reasonable doubt" is a judgment; without the oracle it is unenforceable, and with it, it is only as good as the calibration set. One more spawn per subagent result. Jev sees decision text.
- **Effort:** M to L across seven features. **Risk:** Medium. Mitigations under Consequences.

### Option C — Remove the gates; the person reviews the PR

- **Pros:** Simplest rule. It is what pstack does.
- **Cons:** It moves every question to the PR, after the work, where a wrong contract costs the most. It removes the contract-first behavior users come to Writ for, and it keeps no record of why a choice was made.
- **Effort:** S. **Risk:** High.

### Option D — Keep the class table; let `--recommend` cover every command

- **Pros:** Autonomy stays opt-in per invocation.
- **Cons:** It doubles the recommend-mode surface instead of deleting it, and the class table still asks by category inside every recommended run.
- **Effort:** M. **Risk:** Medium; grows the surface ADR-030 said to subtract.

## Decision Outcome

**Option B.** Driver 1 rules out A and D: both keep the asks the record shows nobody needed. Driver 3 rules out C: it drops the contract and the record. B is the only option that removes surface (driver 4) while adding a check on the thing that was unchecked (driver 3), and its fallback meets driver 5.

**What is explicitly not decided:** skipping the Gate 3 evaluator spawn (ADR-027's promotion rule stands); autonomous release, tag, or publish; any change to ADR-024's family lock; command consolidation (parking lot, measured after Phase 17); whether the front door stays (ADR-030's review, open; the recommendation on record is keep, with its confirm step doubt-gated by this rule).

## Consequences

**Positive**

- One rule, stated once in `_preamble.md`, replaces the gate-class table, the recommend exception, and the per-command confirm steps.
- The ask count becomes a measured quantity per site, with a log that says why each ask fired.
- A subagent's report is re-derived before it is trusted. The F6-class shortcut gets caught at the lane, not at the retro.
- A verified PR lands without a prompt. The person reads a record instead of answering a question.
- ADR-023's "unenforceable rule" gains an enforcer: the doubt judgment and the decision log are what a reviewer reads to see whether diligence matched stakes.

**Negative, with mitigations**

- **"Reasonable doubt" can decay into "never ask".** *Mitigation:* without a configured provider the fallback is today's class table; thresholds start at "ask" and loosen only on labeled outcomes; every autonomous decision is logged and git-revertable; an override on an irreversible act resets its site to always-ask.
- **The calibration set is small and self-generated.** Nine recommendation logs and two User Challenges are the seed. *Mitigation:* transcript AskQuestion turns widen it; the `doubt` site ships uncalibrated-as-ask and is promoted per site, the way ADR-027 promoted spec-findings.
- **One more spawn per subagent result.** *Mitigation:* floor tier, read-only, script-first; it replaces the inline re-verification prose; the review panel's up-to-three spawns per story are already gone (ADR-032); kept only on a removal measurement.
- **Jev sees decision text.** *Mitigation:* ADR-027's double opt-in and secret-path filter; the decision record is built by code from fields the run already wrote, not from raw transcripts.
- **Merge without a prompt is new.** *Mitigation:* it needs Phase 16's ledger green for the exact head and patch-id, and the doubt judgment below the floor; a `/revert` by logical unit already exists; release, tag, and publish stay asks.
- **The Prime Directive text changes.** The "Retain the human production boundary" bullet in `system-instructions.md` becomes a rule about release, tag, and publish, and the `--recommend` bullets go. *Mitigation:* the hard constraints on evidence (never confirm without verifying, never reverse without new evidence) are untouched; they are what the supervisor enforces.
- **Eval pins that hold the old posture in place break.** *Mitigation:* the pins in `check_autonomy_governance` are updated in Phase 17's first spec, in the same commits as the prose they pin.

## Implementation

Roadmap Phase 17, Doubt-Gated Autonomy, in this order:

1. The rule into `commands/_preamble.md` and `system-instructions.md`, replacing the class table and the recommend exception; eval pins updated. *Subtract first.*
2. `jev-judge.py doubt`: the decision-record schema, the site, calibration from decision logs and transcripts, the fallback table.
3. `agents/supervisor-agent.md` and its Claude Code twin; wiring in `/implement-spec` and `/implement-phase`; `subagent-result-completeness` retired; removal measurement on the Phase 15 transcripts.
4. `--recommend` retired; one decision-log schema; `recommendation-semantics.md` folded into it.
5. `/writ` confirms only on doubt.
6. `/create-uat-plan` hands a person only the scenarios no check decides.
7. The override-to-recalibration loop; `/retro` reads the decision log.

**Success criteria:** asks per phase run fall against the Phase 15 transcripts as the baseline; a script finds zero autonomous decisions without a log entry; the supervisor catches at least one F6-class shortcut on a Phase 15 transcript replay; the bytes retired from `_preamble.md`, `system-instructions.md`, and the recommend branches are counted in the phase close; `bash scripts/eval.sh` passes with its pins updated.

**Review:** at Phase 17 close, per site: ask rate before and after, overrides, and any autonomous decision later reverted. Reopen this record if an autonomous decision on an irreversible act is overridden, or if the fallback table fires on most decisions in a project (the oracle is unconfigured there, and the rule is doing nothing).

## Amendments

### 2026-11-05 — The Phase 17 build

Phase 17 was built the same day on `phase/17-doubt-gated-autonomy`, ahead of the Principle 8 queue at the maintainer's direction. Four points of the decision changed in the build:

1. **Jev shadows until its own record says otherwise.** Point 2 expected Jev to make the first-pass call. On 98 of the maintainer's past answers to bounded questions in this repository (88 taken as recommended, 10 overridden), Jev's score did not separate them: the threshold fitted on the dev half (0.38, zero overrides acted on) acted on 2 overrides in 16 on the held-out half, no better than the 10% base rate. `doubt-calibrate` therefore writes a threshold only when the held-out half shows no override it would have acted on, and it refused here ([report](../eval/doubt-calibration/report.md)). Jev still runs first on every decision the rules pass, and its score is logged; the decision's kind decides until the labels support it. Five of the ten overrides were scope or direction calls, which the fallback asks; five were reversible method choices, which it acts on and logs.
2. **The fallback site for scope is `direction`, not "contract".** Point 1's three ADR-022 classes became sites: `direction` (scope, priorities, what gets built, a contract lock) and `design` (taste) ask without a calibrated judgment; `merge` and `release` always ask; `choice`, `route`, `plan`, and `destructive` act when the rules pass. Decisions about method, not scope, were where the labeled data said a person was not needed.
3. **The supervisor runs at the anchor tier, and `subagent-result-completeness` stays.** Point 3 said floor tier. `.writ/docs/model-tiers.md` puts any agent that judges another agent's output at `anchor`, as the evaluator is. The completeness skill checks the verdict shape of gate agents inside a story at no spawn cost; the supervisor checks story and lane reports, so the two do not overlap. The supervisor runs once per story in `/implement-spec` and once per lane in `/implement-phase`, never both for one story. Removal measurement on Phase 15's lane 1: replayed blind on the lane report Phase 15's orchestrator merged (`exit-criteria.py`: `met`), it returned `ESCALATE`, naming the missing coding-agent run, two stories sharing one Gate 3 review, and three verify tasks ticked over a failed run ([trial](../eval/supervisor-trial/report.md)). It stays. The trial cost about 141k tokens, mostly a full-suite and `eval.sh` re-run in a clone; the prompt now re-runs only targeted checks.
4. **`--recommend` is an accepted no-op, not an error.** Goal Cards and scripts that pass it keep working; it prints one line and runs the default. Without a configured judgment provider, a seeded `/create-spec` now asks at the contract lock where `--recommend` used to lock silently. That is the fallback this record chose, and the price of not acting looser without evidence.

### 2026-11-05 — Jev scores confidence in the recommendation

Point 2 had Jev answer whether a decision needs a person. That question asks two things at once: whether the recommendation is right, and whether the choice is the person's to make. The calibration labels record only whether the person took the recommendation. Jev now answers that directly: its p is its confidence that the recommended option is right, sound on the evidence and the option the person would choose. A score above the calibrated threshold acts; at or below it, Writ asks. The maintainer's five confidence bands map onto that one cut: high and medium-high act, medium and below ask, and the labels place the line between them.

On the same 98 answers, with the person's request and the assistant's reasoning attached as evidence, the confidence score ranked overrides as more doubtful than accepted decisions 80% of the time, against 66% for the first question with no evidence ([report](../eval/doubt-calibration/report.md)). It passed the held-out check once (20 of 47 acted on, no override) and failed on an identical repeat (27 acted on, 1 override): Jev's scores moved by up to 0.11 between runs. No threshold is written, and Jev still shadows. Two changes follow:

- **Scores carry the question's name.** Log rows, scored files, and thresholds record `judgment: recommendation_holds`. A score or threshold from another question is ignored, so a reworded question never calibrates on its predecessor's scale.
- **Evidence includes the request.** A decision record's `evidence` names what the person asked for when it bears on the choice, because the calibration data carried it.

Open: the calibration rule fits a threshold to one scoring, and a live decision is scored again with the same noise. A threshold that holds has to clear that noise.

### 2026-11-05 — Calibration bounds the false-act share over repeated scores

The held-out rule was a coin flip by construction: with 10 overrides split 6 and 4, it passed exactly when the highest-scoring override landed in the dev half, 50% of the time over 20,000 random splits of one run's scores. `doubt-calibrate` now uses one rule on all labels:

- **Each decision is scored 3 times**, and the threshold is the highest draw of any override, rounded up to 0.01. Jev acts only above it.
- **Leave one out.** An override slips when any of its draws is above the threshold fitted to the other overrides.
- **The false-act share is bounded.** Overrides × slip rate, against accepted decisions × the share of their draws above the threshold, estimates the share of Jev's acts the person would have overridden. A threshold is written only when that share is at most 10% with the slip rate at its one-sided 95% upper bound. The maintainer set the 10% cap.

On the 98 answers, two runs agree on the estimate (1 of 10 overrides slips; 2 to 3% of acts would be overrides) and split on the verdict: one passed with a 7.8% bound, one refused at 10.4%, and all six draws pooled refuse at 10.4% ([report](../eval/doubt-calibration/report.md)). One override's occasional high draw (0.57 against a mean of 0.48) decides whether the threshold sits at 0.49 or 0.57. No threshold is written, and Jev still shadows. With these data no rule can show the share under 10%; more overrides can. A threshold from each override's mean plus a margin from noise pooled over all decisions is steadier on these scores, but it was found after seeing them, so it waits for new labels.

### 2026-11-06 — Merge acts under the ledger (Phase 16)

Point 5 needed a verification ledger before `/ship` could merge. Phase 16 built it (`scripts/verify-ledger.py`) and a readiness check over a saved `gh` snapshot (`scripts/pr-ready.py`), whose `pass` requires the ledger to read VERIFIED for the snapshot's exact head. The merge site changes:

- **`merge` leaves always-ask.** A `site: merge` record must name `pr`, `head_sha`, and `snapshot`. `jev-judge.py doubt` re-runs `pr-ready.py check --json` on that snapshot, locally, with no network, and asks unless it passes for that PR and head. A missing field asks (`no_verification_ledger`); a missing, crashed, timed-out, or unreadable pr-ready asks (`merge_unverifiable`); a different PR or head asks (`merge_head_mismatch`); a `not_verified` gate asks (`merge_not_verified`); any other verdict asks (`merge_not_ready`). The record's claims are not trusted: the rule re-derives them from the files.
- **`merge` joins the fallback-ask sites.** After the rules pass, Jev scores the decision as on every site. Without a provider or a calibrated threshold the merge asks (`fallback_merge`), so no merge acts until `doubt-calibrate --write` succeeds with merge labels in the log. Today every merge still asks.
- **The remote binding is `--match-head-commit`.** `/ship --watch` takes the snapshot in the same pass as the decision, and `gh pr merge --match-head-commit <head_sha>` makes GitHub refuse the merge if the head moved.
- **Release, tag, and publish stay always-ask** (`outward`). Opening a PR asks nothing.

## References

- [ADR-010](adr-010-supervised-autonomy-ceiling.md), [ADR-013](adr-013-recommended-autonomous-delivery.md), [ADR-022](adr-022-autonomy-gate-classes.md): the records this one supersedes in part
- [ADR-023](adr-023-stakes-proportional-diligence.md): the triage this record gives an oracle and a log; its 2026-11-11 review
- [ADR-027](adr-027-optional-judgment-provider.md): the judgment provider, its cascade rule, and the shadow log (2 of 30 stories)
- [ADR-028](adr-028-behavioral-verification-and-cross-family-panels.md), [ADR-032](adr-032-evidence-gated-review.md): verdicts from runs, not readings
- [ADR-030](adr-030-contract-verifier-boundary-front-door.md): the boundary as one of the three things Writ owns; the front-door review
- [`2026-10-30-phase-15.md`](../retros/2026-10-30-phase-15.md): findings F6, F8, F16, F22, F26
- [`2026-10-31-gate-4-5-fail-asked-instead-of-recoding`](../issues/bugs/2026-10-31-gate-4-5-fail-asked-instead-of-recoding.md)
- [`2026-09-25-jev-typed-judgments-for-harness-gates`](../issues/improvements/2026-09-25-jev-typed-judgments-for-harness-gates.md): the candidate sites beyond the pilot
- `.writ/specs/archive/2026-10-01-behavioral-verification/uat-plan.md`, `.writ/specs/archive/2026-10-01-cross-family-review-panel/uat-plan.md`: the 2026-10-31 agent run
