# ADR-023: Stakes-Proportional Diligence Replaces the Byte Budget

> **Date:** 2026-08-12
> **Status:** Proposed
> **Category:** Framework Architecture
> **Supersedes:** [ADR-021](adr-021-progressive-disclosure-token-budget.md) — its premise and its binding instrument, not its extraction work
> **Extends:** [ADR-022](adr-022-autonomy-gate-classes.md) — adds a second axis to a classifier that already ships
> **Constrains:** [ADR-015](adr-015-leanness-self-governance.md), [ADR-019](adr-019-full-surface-leanness-measurement.md) — retained, demoted from architecture-driving to drift-detecting
> **Deciders:** @AdamSellke
> **Research:** none topic-specific. The evidence is internal measurement of Writ's own corpus.

## Decision

**Writ stops optimizing a global quantity. Diligence is decided per decision, by stakes.**

1. **The byte budget stops driving architecture.** ADR-021's per-command byte cap (24,960) and 400-line tripwire are **retained as reported metrics, removed as design constraints**. No command is restructured to satisfy them.

2. **Progressive disclosure closes as a program.** The four remaining disclosure specs stay `Closed — Not Implemented`.

3. **No universal efficiency measure replaces it** — not bytes, not tokens, not step counts, not decision counts. §*Why no universal measure exists* records the attempt and why it failed.

4. **Every decision is triaged by two questions**, answered from what is already known, before diligence is spent on it:

   | Does the answer change what happens? | How bad if it's wrong? | Diligence |
   |---|---|---|
   | **No** | — | **Not a decision.** Remove it; don't route it. |
   | Yes | Reversible, contained | **Decide, act, record.** No verification step. |
   | Yes | Irreversible or wide blast radius | **Full rigor** — evidence, verification, and [ADR-022](adr-022-autonomy-gate-classes.md)'s gate class applies |

   ADR-022 already answers column 2 for autonomy decisions. This ADR adds column 1 and applies both to *all* decisions — reads, gates, questions, and verification steps alike.

5. **The triage must cost less than the decision it governs.** Two questions, answered from what you already know. **If answering them requires investigation, that is itself the answer** — the decision matters, so escalate.

6. **Safety gates are never capped by count.** For gates of the form "is this correct?", rarity is not irrelevance — a gate may be insurance against a rare asymmetric event. Each names the failure it catches and the cost of missing it; a gate that cannot name one is the candidate for removal.

## Context

### What forced the decision

Phase 10 spent a pilot and six specs pursuing a smaller per-invocation byte load. The pilot shipped, was measured, and five specs were closed on its evidence. The closure was sound but incidental — the deeper problem is that **the optimized quantity was never the quantity that matters.**

The maintainer's goal, recorded here because it appears in no prior ADR:

> we're trying to be economical with not only context, but with unnecessary ruminations and steps to reach a goal/exit criteria. This harness needs to guard against that sort of bloat, especially as models gain more autonomy/agency.

That is a goal about **agent behavior**. Bytes are a goal about **file size**.

### What extraction actually traded

Pilot figures, corrected (ADR-021 Amendment, `commands/implement-story.md`):

| Path | Before | After | Δ |
|---|---|---|---|
| Floor (every run) | 77,669 | **49,797** | −27,872 (−35.9%) |
| Full-path ceiling | 83,770 | 91,903 | +8,133 (+9.7%) |
| `--quick`, dependency-free | 83,770 | 77,365 | −6,405 (−7.6%) |

**On bytes the pilot is a modest win.** The case against the program is not that it failed on bytes.

Each inline `Read skills/…` is a judgment the agent makes and a round trip it spends. Extraction added **eight** such points to `implement-story` (a ninth, `tdd-cycle`, pre-dates Phase 10). Reconciling per-skill sizes against the three measured paths partitions them exactly:

- `dependency-context-loading` (4,858 B) fires only with dependencies — **matches the measured dependency-free delta to the byte**
- `drift-triage` + `what-was-built-authoring` (9,021 B) fire only on non-`--quick` runs — measured delta 9,680 B
- **Five reads (22,126 B) fire on every run, unconditionally**

Extraction converted inert prose — which costs context but demands no judgment — into five judgment-and-fetch cycles that buy nothing. `measure-invocation.py` is structurally blind to this: it counts what is *loaded*, never what must be *decided*.

### Why no universal measure exists

The obvious fix is to inline the five dead reads. The arithmetic refuses to justify it:

| | floor | ceiling | decisions |
|---|---|---|---|
| Pre-extraction | 77,669 | 83,770 | 1 |
| Today | **49,797** | 91,903 | 9 |
| Inline the 5 dead | 67,173 | 87,153 | 4 |

Inlining raises the floor **17,376 bytes on every run** to save 4,750 on the worst run and remove five judgments — roughly **3,475 bytes of permanent floor per decision removed**.

Is that a good trade? It requires an exchange rate between a decision and a byte. Writ has no tokenizer (none is available to this project) and no step measurement. **The rate is not merely unmeasured; it is not a stable quantity.** A decision's cost depends on what it is deciding — which is exactly the maintainer's finding:

> I'm not sure there's a universal measure here… we cannot universally weigh decision costs. It's a determination as to whether or not the answer is important and whether it's really, really important to get it right.

Searching harder for the rate was itself the error. There is no denominator that makes a load-a-skill decision commensurable with a merge-to-main decision.

### What ADR-022 already provides

ADR-022 classifies decisions into five gate classes and conditions destructive operations on a two-part reversibility precondition. That is **column 2 of the triage, already shipped and in force**. It routes on blast radius but never asks whether the answer matters at all. This ADR supplies the missing column rather than building a parallel system.

### Why the existing governance could not catch any of this

ADR-015 and ADR-019 built real leanness governance; ADR-021 correctly saw that a ratchet is not a budget. All three are **entirely *ex ante*** — they measure declared artifacts before any run. Writ already declares the right things (`loop.max_iterations` on five commands, `exit_criteria` on all 31, `attempts` in state). Nothing observes whether a run honored any of it. That gap remains open, and this ADR does not close it — it removes the wrong answer to it.

### The instrument was never validated

`measure-invocation.py` says so in its own output: *"Tokens are **NOT** measured… The chars/4 ratio has **never been validated** against a real tokenizer."* ADR-021 listed this under its own Negative consequences and proceeded. Six specs were scoped against an uncalibrated proxy that cannot be calibrated here.

## Decision Drivers (force-ranked)

1. **Diligence must be proportional to stakes.** Uniform rigor is waste at the low end and false comfort at the high end. Under rising autonomy the low end is where waste compounds.
2. **No gauge without a derivation linking it to harm.** 24,960 sounded principled and was arbitrary. Any replacement number would inherit the flaw.
3. **Mission honesty.** "Thin" should describe what Writ costs to *use*, not what it weighs.

Not drivers: file readability (real, separate), context-window pressure (no overflow ever observed), cost (no figure ever cited).

## Considered Options

### A. Continue the byte program; reopen the four closed specs
- **Pros:** Phase 10 completes; ~24,600 B floor cut on `create-spec`; specs already contract-locked, design cost sunk.
- **Cons:** Adds an estimated 20–30 decision points across five commands — increasing what the maintainer wants reduced. `create-spec` already stops for judgment 12 times.
- **Risk:** High, and *invisible to the metric that would report success*.

### B. Replace bytes with a step or decision-count threshold
- **Pros:** Keeps one enforceable number; operationally simple.
- **Cons:** No such threshold is derivable. The exchange-rate finding shows decision costs are not commensurable, so any number is arbitrary in the same way 24,960 was.
- **Risk:** High — ADR-021's exact failure in a new unit.

### C. Build an instrument to price decisions, then set a threshold
- **Pros:** Would make B defensible if it worked.
- **Cons:** Presumes a universal exchange rate exists. It does not — the cost of a decision is a function of its stakes, which is the thing being measured. Circular.
- **Risk:** High, and expensive to discover. *This is the option the previous draft of this ADR proposed.*

### D. Stakes triage; no universal measure — **chosen**
- **Pros:** Prices each decision by its own stakes, dissolving the exchange-rate problem instead of solving it. Extends a classifier already shipped (ADR-022) rather than inventing one. Costs nothing to operate — two questions from known information. Yields real findings immediately (five dead reads) without a threshold.
- **Cons:** Not mechanically enforceable — no check can verify a judgment was proportional. Leaves Writ with **no enforced efficiency constraint**. Relies on authors applying it honestly.
- **Risk:** Medium — the honest risk is that an unenforceable rule is ignored. *Mitigation:* it is cheap enough to actually use, which is more than the byte cap could claim.

### E. Abandon efficiency governance entirely
- **Pros:** Zero cost; ADR-021 named this "the honest null option."
- **Cons:** ADR-019's ratchet is cheap and has caught real drift; discarding working machinery to fix an unrelated problem.
- **Risk:** Medium — bloat returns unobserved.

## Decision Outcome

**Option D.**

Driver 1 rejects A. Driver 2 rejects B and C: both require a number nobody can derive, and C spends real effort discovering that. E is rejected because the ratchet works — the problem is what was built on top of it.

**What is explicitly NOT decided:** whether commands should be consolidated (ADR-021 deferred it; still deferred); any change to ADR-020's contract, ADR-022's classes, the Question Policy, or `required_skills:`.

## Worked Example — This Decision, Triaged

The triage is applied to the question that produced this ADR: *should the five dead reads be inlined?*

- **Does the answer change what happens?** Marginally — ~17K bytes of floor on one command.
- **How bad if wrong?** Trivial. Fully reversible, one command file, one `git revert`, no external effect.

→ **Row 2: decide, act, record. No verification step.**

**Ruling: leave them.** Revisit only if `implement-story.md` is edited for another reason. That is the whole analysis the question warranted.

**What actually happened instead:** an exchange-rate analysis, a rejected option, and a proposal to build `scripts/measure-run.py` to settle it. The diligence spent exceeded the stakes by a wide margin — which is precisely the bloat this ADR exists to prevent, generated while writing it.

This example is recorded because it implicates the process rather than flattering it, and because it is the clearest demonstration in the repository of why the rule is needed: **the failure mode is not laziness, it is unbounded rigor on a question that never warranted it.**

## Consequences

**Positive**

- Writ stops optimizing a quantity nobody had a goal about.
- Diligence becomes proportional, which is what "economical with ruminations" actually means.
- One whole class of waste gets a free test — a decision whose answer never changes anything is not a decision — with a real finding already in hand.
- The safety-gate carve-out protects verification from being argued away by that same test.
- Command authoring gains an actionable virtue: **decisiveness**. "Does this sentence make the agent choose, or does it say what to do?" is a better review question than a byte count.

**Negative**

- **Nothing is mechanically enforced.** No check verifies proportional judgment. *Mitigation:* none available. Accepted as the cost of not inventing a false gauge — an unenforceable true rule beats an enforceable wrong one.
- **A known defect ships.** Five decision points are demonstrably dead and stay. *Mitigation:* ruled on above by the triage itself, not deferred indefinitely.
- **Writ has no enforced efficiency constraint.** *Mitigation:* bytes are still measured and reported; only their authority is removed. The ratchet still catches runaway growth.
- **The mission loses a quotable number.** *Mitigation:* an absent number beats a wrong one.

## Implementation Notes

**Prerequisites:** none. No tooling is built. That is the point.

1. Add the two-question triage to [`commands/_preamble.md`](../../commands/_preamble.md), beside ADR-022's gate-class table. **Done 2026-08-12 — and the file's 95-line cap forced it from a table into one dense paragraph.** That is the cap working as designed: shared surface is paid on every invocation, so a new rule must earn its lines by displacing prose or compressing itself. The preamble now sits at exactly 95/95; the next addition must cut something.
2. Record this reversal in `.writ/product/roadmap.md` Phase 10, whose success criteria still cite byte targets.
3. Verify (do not tighten) that `scripts/eval-leanness.py`'s byte cap emits a warning, not a finding; document the demotion.

**Success criteria:**

- No command file is restructured to satisfy a byte target after this date.
- No numeric threshold on steps, decisions, or gates is introduced without a recorded derivation linking it to measured harm.
- The triage stays within `_preamble.md`'s existing cap — **met**, at 95/95, by compression rather than by raising the cap. If it ever needs more room than one paragraph, it has become the thing it replaced.

**Review date:** **2026-11-11**, aligned to ADR-021's trigger and the `required_skills:` review so all three resolve together. The review question is not "did we build the instrument" but **"has any decision been visibly over- or under-diligenced, and did the triage catch it?"**

## Dissent and Corrections

**Recorded because the reasoning path matters more than the conclusion.**

- The four disclosure specs were closed **2026-08-12 under the spec set's Business Rule 1**, before this ADR and on different reasoning. This ADR ratifies that outcome on stronger grounds; it does not claim the closure waited for it.
- **Six claims were made in argument and withdrawn against evidence** during this review: (1) the eager `required_skills:` pre-load justified the closures — it does not, the specs use inline reads and never adopt the field; (2) `/create-spec` is a sequential pipeline with little to skip — false, 25.7% is three mutually-exclusive mode blocks; (3) the pilot regressed 18% with its exemption ungranted — it regressed **9.7%** on the full path only, improved on `--quick`, and the exemption **was** granted; (4) extraction added nine decision points — **eight**, `tdd-cycle` pre-dates Phase 10; (5) inlining the dead reads beats both endpoints — it does not, it raises the floor 17,376 B; (6) that an instrument could price a decision — it cannot, the cost is a function of the stakes being measured.
- Corrections (5) and (6) each arrived one step before the recommendation they refuted would have shipped. **Two prior drafts of this ADR proposed measurement programs** — first steps-to-exit-criteria, then decision yield with a pricing instrument. Both were the same error the ADR diagnoses: reaching for a universal gauge. That the ADR needed three drafts to stop doing the thing it forbids is itself the strongest argument for the rule.
- **The strongest case against this ADR** is that an unenforceable rule is indistinguishable from no rule, and Writ now has no mechanical efficiency guard at all. That case is not answered here. It is deferred to 2026-11-11, with Option E named in advance as the honest fallback.

## References

- [ADR-022](adr-022-autonomy-gate-classes.md) — the gate classes and reversibility precondition this ADR extends
- [ADR-021](adr-021-progressive-disclosure-token-budget.md) — superseded premise and instrument; its 2026-08-12 amendments carry the pilot's corrected figures
- [ADR-020](adr-020-component-contract.md) — `exit_criteria`, the anchor a decision's stakes are judged against
- [ADR-019](adr-019-full-surface-leanness-measurement.md), [ADR-015](adr-015-leanness-self-governance.md) — the retained ratchet
- `skills/error-rescue-mapping/SKILL.md` — the `[UNPLANNED]` discipline the safety-gate rule mirrors
- `scripts/measure-invocation.py` — the byte instrument, retained and demoted
- `.writ/specs/archive/2026-08-12-disclosure-*` — five specs, archived intact and unexecuted as design records
