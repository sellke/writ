# ADR-023: Decision Yield Supersedes the Byte Budget — and No Gauge Replaces It Yet

> **Date:** 2026-08-12
> **Status:** Proposed
> **Category:** Framework Architecture
> **Supersedes:** [ADR-021](adr-021-progressive-disclosure-token-budget.md) — its *premise* and its *binding instrument*, not its extraction work
> **Constrains:** [ADR-015](adr-015-leanness-self-governance.md), [ADR-019](adr-019-full-surface-leanness-measurement.md) — both retained, both demoted from architecture-driving to drift-detecting
> **Paired with:** [ADR-020](adr-020-component-contract.md) — `exit_criteria` becomes the measurement anchor rather than a documentation field
> **Deciders:** @AdamSellke
> **Research:** none topic-specific in `.writ/research/`. The decisive evidence is internal measurement of Writ's own corpus, not external comparison. Recorded so a reader knows the alternatives analysis rests on measured dogfooding rather than a literature survey.

## Decision

**Writ stops optimizing bytes. It does not adopt a replacement gauge, because none is currently derivable.**

1. **The byte budget stops driving architecture.** ADR-021's absolute per-command byte cap (24,960) and its 400-line tripwire are **retained as reported metrics and removed as design constraints**. No command is restructured to satisfy them.

2. **Progressive disclosure closes as a program.** The four remaining disclosure specs stay `Closed — Not Implemented`. No further command is extracted to reduce its file size.

3. **The pilot is kept exactly as shipped.** `commands/implement-story.md` is neither reverted nor corrected. §*The exchange-rate problem* explains why the obvious correction is not yet justified.

4. **Decision yield becomes the standing *diagnostic* for information decisions** — those of the form "should I load / fetch / consult this?" A decision point that never resolves differently across runs is not a decision; it is a step with a judgment attached. Yield is measured, reported, and reviewed. **It does not by itself authorize a change** (see 6).

5. **Safety gates are governed by a named failure mode, never by a count.** For gates of the form "is this correct?", zero yield is not evidence of uselessness — it may be insurance against a rare asymmetric event. Each gate must name the failure it catches and the cost of missing it. A gate that cannot name one is the candidate for removal; a gate that can, stays regardless of how rarely it fires. **No cap on gate counts is set, now or later.**

6. **No numeric threshold is adopted.** Not for decision points, not for steps, not for gates. Converting a yield diagnosis into an action requires an exchange rate between a decision and a byte, and no such rate is currently measurable. Setting one anyway would repeat ADR-021's error exactly. Until the rate exists, yield is recorded and acted on only where it is free to do so.

Bytes remain measured — the ratchet is cheap and catches genuine runaway growth. They simply stop being the thing Writ optimizes.

## Context

### What forced the decision

Phase 10 spent one pilot and six specs pursuing a smaller per-invocation byte load. The pilot shipped and was measured; five specs were then closed on its evidence. On review, the closure was sound but incidental. The deeper problem is that **the optimized quantity was never the quantity that matters.**

The maintainer's stated goal, recorded here because it appears in no prior ADR:

> we're trying to be economical with not only context, but with unnecessary ruminations and steps to reach a goal/exit criteria. This harness needs to guard against that sort of bloat, especially as models gain more autonomy/agency.

That is a goal about **agent behavior**. Bytes are a goal about **file size**. Where they diverge, the byte metric points the wrong way.

### The divergence, measured

The pilot's corrected figures (ADR-021 Amendment, 2026-08-12, `commands/implement-story.md`):

| Path | Before | After | Δ |
|---|---|---|---|
| Floor (paid every run) | 77,669 | **49,797** | **−27,872 (−35.9%)** |
| Full-path ceiling | 83,770 | 91,903 | +8,133 (+9.7%) |
| `--quick` ceiling | 83,770 | 82,223 | −1,547 (−1.8%) |
| `--quick`, dependency-free | 83,770 | 77,365 | −6,405 (−7.6%) |

**On bytes the pilot is a modest win** — a large unconditional floor reduction, gains on short paths, one regression on the maximal path (which carries a tracked exemption). The case for closing the program is *not* that it failed on bytes.

Now the same change under the behavioral frame. Each inline `Read skills/…` is a judgment the agent must make and a round trip it must spend:

| Command | Decision points | AskQuestion sites | Loop bound |
|---|---|---|---|
| `implement-story` | **9** (1 pre-existing + **8 added by extraction**) | 2 | 3 |
| `new-skill` | 3 | 5 | — |
| `create-spec` | 1 | **12** | — |
| `ship` / `release` / `refactor` / `research` | 1 each | 1–3 | — |

Extraction converted inert prose — which costs context but demands no judgment — into eight additional judgment-and-fetch cycles. `measure-invocation.py` is structurally blind to that trade: it counts what is *loaded*, never what must be *decided*.

### Decision yield: which of those eight buy anything

Reconciling per-skill file sizes against the three measured paths partitions them exactly:

| Skill | Bytes | Fires on |
|---|---|---|
| `dependency-context-loading` | 4,858 | only when the story has dependencies — **matches the measured dependency-free delta of 4,858 B to the byte** |
| `drift-triage` + `what-was-built-authoring` | 9,021 | only on non-`--quick` runs — measured `--quick` delta 9,680 B (within 659 B) |
| `story-context-assembly`, `boundary-map-computation`, `project-context-snapshot`, `change-surface-classification`, `story-commit-provenance` | **22,126** | **every run, unconditionally** |
| `tdd-cycle` | 6,101 | every run — but **pre-dates Phase 10**, not extraction's doing |

**Five of the eight added decision points have zero yield.** They are not conditional loads. They are 22,126 bytes that load on every run anyway, plus five round trips and five judgment moments, buying nothing.

That is a rigorous, falsifiable finding — "show me a run where this did not fire" — and it needs no threshold to state.

### The exchange-rate problem

The obvious action is to inline the five dead reads. The arithmetic refuses to justify it:

| | floor | ceiling | decisions |
|---|---|---|---|
| Pre-extraction | 77,669 | 83,770 | 1 |
| Today, as shipped | **49,797** | 91,903 | 9 |
| Inline the 5 dead | 67,173 | 87,153 | 4 |

Inlining raises the floor by **17,376 bytes paid on every single run** to save 4,750 on the worst run and remove five decisions — roughly **3,475 bytes of permanent floor per decision removed**.

Whether that trade is good depends entirely on what one decision costs relative to 3,475 bytes. **Writ cannot currently answer that.** There is no tokenizer available to this project, and no instrument measures steps. The correction is not obviously right; it is *unevaluable*.

This is the ADR's central discipline. A diagnosis that cannot be priced does not become an action. Acting anyway — inlining because five decisions *feel* expensive — would be the same error as extracting six commands because 46 KB *felt* expensive.

### Why the existing governance could not catch any of this

ADR-015 and ADR-019 built real leanness governance, and ADR-021 correctly identified that a ratchet is not a budget. All three share one blind spot: **they are entirely *ex ante*.** They measure declared artifacts before any run happens.

Writ already declares the right things — `loop.max_iterations` and `on_exhaustion` on five commands, `exit_criteria` on all 31 (ADR-020), `attempts` in execution state. **Nothing observes whether a real run honored any of it.** Bounds are asserted and never verified; exit criteria are declared and adherence is never measured.

### The instrument was never validated

`measure-invocation.py` reports, in its own output:

> Tokens are **NOT** measured: no tokenizer was available… The chars/4 ratio… **has never been validated against a real tokenizer** — treat every `*_tokens_estimated` value as an order-of-magnitude figure.

ADR-021 listed this under its own Negative consequences and proceeded. Six specs were scoped against an uncalibrated proxy. **No tokenizer is available to this project**, so this cannot be fixed by calibration — an independent reason to stop treating estimated bytes-as-tokens as the governing number.

### The mission argument, restated honestly

ADR-021's actual driver was positioning, stated plainly in its own Context:

> `mission.md` positions Writ as *"the **thin**, portable methodology layer"*… 516KB of command prose falsifies "thin" by measurement. **Phase 10 is not a strategic pivot — it is the phase that makes the existing mission statement true.**

Legitimate, and not dismissed here. But "thin" is a claim about **what it costs to use Writ**, and that is dominated by how many steps and judgments a run takes, not by the size of a markdown file.

## Decision Drivers (force-ranked)

1. **Agent step economy under increasing autonomy.** Wasted steps do not merely cost tokens — they compound into drift. An autonomous agent that wanders produces wrong work, not just slow work.
2. **Instrument validity.** An optimization program must measure the quantity it optimizes, and must not adopt a gauge it cannot price. Bytes are measured accurately but proxy nothing anyone stated a goal about; tokens are an estimate that cannot be calibrated here.
3. **Mission honesty.** "Thin" should be measurable — subordinate, because it is satisfiable by either metric.

Explicitly *not* drivers: file readability (real, separate), context-window pressure (no overflow ever observed or recorded), and cost (no figure ever cited).

## Considered Options

### A. Status quo — continue the byte program, reopen the four closed specs

- **Pros:** Phase 10 completes; "thin" becomes literally true by the chosen measure; ~24,600 B floor reduction on `create-spec` alone; specs already authored and contract-locked, so design cost is sunk.
- **Cons:** Adds an estimated 20–30 further decision points across five commands — increasing the quantity the maintainer wants reduced. Optimizes an unvalidatable proxy. `create-spec` already stops for judgment 12 times; adding fetch decisions compounds the wrong thing.
- **Effort:** High. **Risk:** High and *invisible to the metric that would report success* — every check would pass while the real goal regressed.

### B. Close the byte program; adopt a step/decision metric as the new binding gauge

Replace the byte cap with a threshold on steps or decision points.

- **Pros:** Measures something closer to the stated goal; keeps a single enforceable number, which is operationally simple.
- **Cons:** **No such threshold is derivable today.** Any number would be as arbitrary as 24,960 was — and would be arbitrary in the same specific way: a figure with no measured link to harm. The exchange-rate analysis above shows even a *correct* yield diagnosis cannot be priced.
- **Effort:** Low to declare, high to justify. **Risk:** High — repeats ADR-021's precise failure with a new unit.

### C. Close the byte program; adopt decision yield as a diagnostic, set no threshold — **chosen**

Retain bytes as drift signal; stop restructuring for them; measure yield; act only where action is free; explicitly refuse a numeric gauge until one can be priced.

- **Pros:** Measures the right mechanism. Uses primitives Writ already has (`exit_criteria`, `loop.max_iterations`, `attempts`). Closes the ex-ante/ex-post gap. **Refuses to invent a gauge it cannot justify** — the specific discipline whose absence produced Phase 10. Yield is falsifiable per item, so it produces real findings without a threshold.
- **Cons:** Leaves Writ with **no enforced efficiency constraint** for an indefinite period. Diagnoses problems it cannot authorize fixing, which is uncomfortable and may read as inaction. Requires an instrument that does not exist.
- **Effort:** Medium. **Risk:** Medium — the honest risk is that yield proves unpriceable indefinitely, leaving the diagnostic permanently advisory. *Mitigation:* named in advance as an acceptable outcome; see Option E and the review trigger.

### D. Option C, plus inline the five zero-yield reads now

- **Pros:** Removes five judgment moments and five round trips; restores prose to the file where it is read anyway.
- **Cons:** Raises the floor **17,376 B on every run** to save 4,750 on the worst path. Justified only if a decision is worth >3,475 bytes — **unknown**. Costs real work to undo real work on an unpriced belief.
- **Effort:** Medium. **Risk:** Medium-high. **This is the option the ADR most wants to take and specifically declines**, because taking it would mean acting on exactly the kind of unmeasured intuition that produced ADR-021.

### E. Abandon measured efficiency governance entirely

- **Pros:** Zero instrument cost; honest about what is unmeasurable; ADR-021 named this as "the honest null option."
- **Cons:** ADR-019's ratchet is cheap and has caught real drift — discarding working machinery to fix an unrelated problem. Leaves no answer to "is Writ getting heavier?"
- **Effort:** Trivial. **Risk:** Medium — bloat returns unobserved, the exact condition ADR-021 documented ("four unjustified-growth warnings… live right now and have been ignored").

### F. Revert the pilot

- **Pros:** Removes the largest concentration of decision points; one consistent authoring style.
- **Cons:** Discards a measured **−35.9% floor reduction** paid on every run, plus `--quick` gains. Destroys the only real-world dataset the yield diagnostic has. Same unpriced-belief error as D, at larger scale.
- **Effort:** Medium. **Risk:** Medium-high.

## Decision Outcome

**Option C.**

Driver 1 rejects A: it actively worsens the primary goal. Driver 2 rejects B: adopting an unpriceable threshold is ADR-021's failure repeated in a new unit, and the exchange-rate analysis proves the price is currently unavailable. E is rejected because the ratchet works — the problem is what was built on top of it, not the ratchet.

**D and F are rejected on the same principle, and it is the principle this ADR exists to install:** a diagnosis that cannot be priced does not become an action. Both would trade measured bytes for unmeasured decisions on the strength of an intuition. That the intuition is probably *correct* is not sufficient — ADR-021's intuition was also plausible, and it cost six specs.

**What is explicitly NOT decided:**

- Whether the five zero-yield reads should eventually be inlined — awaits a price.
- Whether `implement-story` keeps its extraction long-term — same.
- Whether commands should be consolidated or removed (ADR-021 deferred this; it stays deferred).
- Any change to ADR-020's contract, ADR-022's gate classes, the Question Policy, or `required_skills:` (which has no consumer and its own 2026-11-11 trigger).

## Consequences

**Positive**

- Writ stops optimizing a quantity nobody had a goal about.
- Decision yield gives a rigorous, threshold-free test for one whole class of waste, with a real finding already in hand (5 dead reads).
- The information/safety split protects verification from being argued away by the same test — a gate's rarity is not its irrelevance.
- Command authoring gains an actionable virtue: **decisiveness**. "Does this sentence make the agent choose, or does it say what to do?" is a better review question than "is this file under 24,960 bytes?"
- The refusal to set a gauge is itself the durable lesson. It is the guardrail Phase 10 lacked.

**Negative**

- **Writ has no enforced efficiency constraint after this ADR**, possibly for a long time. *Mitigation:* bytes continue to be measured and reported; only their authority is removed. The ratchet still catches runaway growth.
- **A known defect is being left in place.** Five decision points are demonstrably dead and stay shipped. *Mitigation:* recorded here explicitly so it is a documented deferral, not an oversight; it is the first thing to revisit once a price exists.
- **Yield may never be priceable**, leaving the diagnostic permanently advisory. *Mitigation:* Option E is named in advance as the honest fallback at the review date.
- **Step counts are platform-dependent** — tool-call granularity differs across harnesses, cutting against adapter neutrality. *Mitigation:* measure from Writ's own state files (`attempts`, story statuses, gate iterations), platform-neutral by construction, before any harness-native telemetry.
- **The mission loses a quotable number.** *Mitigation:* replace it only when a real one exists. An absent number beats a wrong one.

## Implementation Notes

**Prerequisites:** none. Closing the byte program requires no code change — only the removal of its authority, recorded here.

**Steps:**

1. Record this reversal in `.writ/product/roadmap.md` Phase 10, whose success criteria still cite byte targets.
2. Verify (do not tighten) that the byte cap in `scripts/eval-leanness.py` emits a warning rather than a finding, and document its demotion.
3. Build `scripts/measure-run.py`: from an execution state file, report steps taken, bound adherence against declared `loop.max_iterations`, gate iterations consumed, and repeat reads.
4. Backfill it against the runs already recorded in `.writ/state/` — measurement before governance.
5. Record decision yield per command from real runs, starting with the five known-dead reads.
6. **Attempt to price a decision.** If a defensible bytes-per-decision exchange rate emerges, revisit Option D. If it does not, say so plainly and keep yield advisory.

**Success criteria:**

- No command file is restructured to satisfy a byte target after this date.
- No numeric threshold on steps, decisions, or gates is introduced without a recorded derivation linking it to measured harm.
- `measure-run.py` reports for at least three recorded runs.
- The yield partition for `implement-story` is confirmed or refuted against real runs.

**Review date:** **2026-11-11**, aligned to ADR-021's trigger and the `required_skills:` review so all three resolve together. If `measure-run.py` does not exist by then, this ADR failed, and the honest response is Option E — not another instrument and certainly not another number.

## Dissent and Corrections

**Recorded because the reasoning path matters more than the conclusion.**

- The four disclosure specs were closed **2026-08-12 under the originating spec set's Business Rule 1** — before this ADR and on different reasoning. This ADR ratifies that outcome on stronger grounds; it does not claim the closure waited for it.
- Five claims were made in argument during this review and **withdrawn against evidence**: (1) that the eager `required_skills:` pre-load justified closing the specs — it does not, the specs use inline reads and never adopt the field; (2) that `/create-spec` is a sequential pipeline with little to skip — false, 25.7% of it is three mutually-exclusive mode blocks; (3) that the pilot regressed 18% with its prescribed exemption ungranted — it regressed **9.7%** on the full path only, improved on `--quick` paths, and the exemption **was** granted in ADR-021's amendment; (4) that extraction added nine decision points — it added **eight**, since `tdd-cycle` pre-dates Phase 10; (5) that inlining the dead reads beats both endpoints — **it does not**, it raises the floor 17,376 B and its ceiling stays 3,383 B worse than the pre-extraction monolith. Correction (5) is why Option D is rejected rather than adopted, and it arrived one step before that recommendation would have shipped.
- **The strongest case against this ADR** is that refusing a gauge is indistinguishable in practice from having no governance, and that a known-dead defect is being left in place to honor a principle. That case is not answered here. It is deferred to 2026-11-11 with Option E named in advance.

## References

- [ADR-021](adr-021-progressive-disclosure-token-budget.md) — superseded premise and instrument; its two 2026-08-12 amendments carry the pilot's corrected figures
- [ADR-020](adr-020-component-contract.md) — `exit_criteria`, the anchor measurement is taken against
- [ADR-019](adr-019-full-surface-leanness-measurement.md), [ADR-015](adr-015-leanness-self-governance.md) — the retained ratchet
- [ADR-022](adr-022-autonomy-gate-classes.md) — the autonomy context that makes step waste compounding rather than merely costly
- `skills/error-rescue-mapping/SKILL.md` — the `[UNPLANNED]` discipline this ADR's safety-gate rule mirrors
- `.writ/docs/phase-execution-state-format.md` — `attempts` and gate records, the platform-neutral substrate for measurement
- `scripts/measure-invocation.py` — the byte instrument, retained and demoted
- `.writ/specs/archive/2026-08-12-disclosure-*` — five specs, archived intact and unexecuted as design records
