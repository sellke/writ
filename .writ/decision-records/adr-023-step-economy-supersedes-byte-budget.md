# ADR-023: Step Economy Supersedes the Byte Budget as Writ's Efficiency Goal

> **Date:** 2026-08-12
> **Status:** Proposed
> **Category:** Framework Architecture
> **Supersedes:** [ADR-021](adr-021-progressive-disclosure-token-budget.md) — its *premise* and its *binding instrument*, not its extraction work
> **Constrains:** [ADR-015](adr-015-leanness-self-governance.md), [ADR-019](adr-019-full-surface-leanness-measurement.md) — both retained, both demoted from architecture-driving to drift-detecting
> **Paired with:** [ADR-020](adr-020-component-contract.md) — `exit_criteria` becomes the measurement anchor rather than a documentation field
> **Deciders:** @AdamSellke
> **Research:** none topic-specific in `.writ/research/`. The decisive evidence is internal measurement of Writ's own corpus (the Phase 10 pilot, `measure-invocation.py`, and the decision-point census below), not external comparison. Recorded so a reader knows the alternatives analysis rests on measured dogfooding rather than a literature survey.

## Decision

**Writ's efficiency goal is the number of steps and decisions an agent takes to reach a command's declared exit criteria — not the number of bytes it loads.**

1. **The byte budget stops driving architecture.** ADR-021's absolute per-command byte cap (24,960) and its 400-line tripwire are **retained as reported metrics and removed as design constraints**. No command is restructured to satisfy them.

2. **Progressive disclosure is closed as a program.** The four remaining disclosure specs stay `Closed — Not Implemented`. No further command is extracted to reduce its file size.

3. **The pilot is kept, not reverted.** `commands/implement-story.md` retains its extraction. Its floor win is real and unconditional; its costs are real and now measurable. It becomes the baseline case for the new instrument rather than a regression to undo.

4. **The governing measurement becomes steps-to-exit-criteria**, observed from real runs: steps taken, overrun past the point exit criteria were satisfiable, bound adherence against declared `loop.max_iterations`, gate iterations consumed, repeat reads of one artifact, and questions asked against those the Question Policy sanctions.

5. **Decisiveness of instruction replaces terseness of prose as the authoring virtue.** A command is improved by removing ambiguity, not by removing words. "Do X" is better than a shorter sentence that leaves the agent to decide.

Bytes remain measured — the ratchet is cheap and catches genuine runaway growth. They simply stop being the thing Writ optimizes.

## Context

### What forced the decision

Phase 10 spent one pilot and six specs pursuing a smaller per-invocation byte load. The pilot shipped and was measured. Five specs were then closed on the pilot's evidence. On review, the closure reasoning was sound but incidental: the deeper problem is that **the quantity being optimized was never the quantity that matters**.

The maintainer's stated goal, recorded here because it appears in no prior ADR:

> we're trying to be economical with not only context, but with unnecessary ruminations and steps to reach a goal/exit criteria. This harness needs to guard against that sort of bloat, especially as models gain more autonomy/agency.

That is a goal about **agent behavior**. Bytes are a goal about **file size**. They are related but not the same, and where they diverge, the byte metric points the wrong way.

### The divergence, measured

The pilot's corrected figures (ADR-021 Amendment, 2026-08-12, `commands/implement-story.md`):

| Path | Before | After | Δ |
|---|---|---|---|
| Floor (paid every run) | 77,669 | **49,797** | **−27,872 (−35.9%)** |
| Full-path ceiling | 83,770 | 91,903 | +8,133 (+9.7%) |
| `--quick` ceiling | 83,770 | 82,223 | −1,547 (−1.8%) |
| `--quick`, dependency-free | 83,770 | 77,365 | −6,405 (−7.6%) |

**On bytes the pilot is a modest win**, not a failure: a large unconditional floor reduction, small conditional gains on short paths, one regression on the maximal path (which already carries a tracked exemption).

Now the same change under the step frame — a census of inline `Read skills/…` directives, each of which is a decision the agent must make and a round trip it must spend:

| Command | Decision points | AskQuestion sites | Declared loop bound |
|---|---|---|---|
| `implement-story` | **9** | 2 | 3 |
| `new-skill` | 3 | 5 | — |
| `create-spec` | 1 | **12** | — |
| `ship` / `release` / `refactor` / `research` | 1 each | 1–3 | — |

`implement-story` had **zero** decision points before extraction. Progressive disclosure converted inert prose — which costs context but demands no judgment — into **nine** judgment-and-fetch cycles.

**That is the finding.** Extraction trades a quantity the maintainer does not care much about (floor bytes) for a quantity the maintainer explicitly wants minimized (decisions and steps). The byte instrument is structurally blind to the trade: `measure-invocation.py` counts what is loaded, never what must be decided.

### Why the existing governance could not catch this

ADR-015 and ADR-019 built real leanness governance, and ADR-021 correctly identified that a ratchet is not a budget. All three share one blind spot: **they are entirely *ex ante*.** They measure declared artifacts before any run happens.

Writ already declares the right things — `loop.max_iterations` and `on_exhaustion` on five commands, `exit_criteria` on all 31 (ADR-020), `attempts` recorded in execution state. **Nothing observes whether a real run honored any of it.** The single instrument in the repository, `measure-invocation.py`, measures bytes.

So the governance loop has never closed. Bounds are asserted and never verified; exit criteria are declared and adherence is never measured.

### The instrument was never validated

`measure-invocation.py` reports, in its own output:

> Tokens are **NOT** measured: no tokenizer was available… The chars/4 ratio… **has never been validated against a real tokenizer** — treat every `*_tokens_estimated` value as an order-of-magnitude figure.

ADR-021 lists this under its own Negative consequences and proceeded. Six specs were scoped against an uncalibrated proxy. **No tokenizer is available to this project**, so this cannot be fixed by calibration — which is an additional, independent reason to stop treating estimated tokens as the governing number.

### The mission argument, restated honestly

ADR-021's actual driver was positioning, stated plainly in its own Context:

> `mission.md` positions Writ as *"the **thin**, portable methodology layer"*… 516KB of command prose falsifies "thin" by measurement. **Phase 10 is not a strategic pivot — it is the phase that makes the existing mission statement true.**

That is a legitimate concern, and this ADR does not dismiss it. But "thin" is a claim about **what it costs to use Writ**, and cost-to-use is dominated by how many steps a run takes, not by the size of a markdown file. Under this ADR, "thin" becomes provable in the dimension users actually feel.

## Decision Drivers (force-ranked)

1. **Agent step economy under increasing autonomy.** Wasted steps do not merely cost tokens — they compound into drift, and an autonomous agent that wanders produces wrong work, not just slow work. This is the driver that tips the decision.
2. **Instrument validity.** An optimization program must measure the quantity it optimizes. Byte counts are measured accurately but are a proxy for nothing anyone stated a goal about; token counts are an unvalidated estimate that cannot be calibrated here.
3. **Mission honesty.** "Thin" should be measurable. Subordinate to the above because it is satisfiable by either metric — and better satisfied by the one users experience.

Explicitly *not* drivers: file readability (real, but a separate concern), context-window pressure (no overflow has ever been observed or recorded), and cost (no figure was ever cited).

## Considered Options

### A. Status quo — continue the byte program, reopen the four closed specs

Finish what Phase 10 started: extract `create-spec`, `verify-spec`, `implement-phase`, `release`, `ship` to thin contracts.

- **Pros:** Phase 10 completes as planned; mission's "thin" claim becomes literally true by the measure already chosen; ~24,600 B floor reduction on `create-spec` alone; the specs are already authored, contract-locked, and carry pinned-literal inventories, so most design cost is sunk.
- **Cons:** Adds an estimated 20–30 further decision points across five commands — directly increasing the quantity the maintainer wants reduced. Optimizes an unvalidatable proxy. `create-spec` carries 12 `AskQuestion` sites already; adding fetch decisions to a command that already stops for judgment 12 times compounds the wrong thing.
- **Effort:** High — five specs, each with extraction, no-drift inventory, and measurement.
- **Risk:** High and *invisible to the metric that would report success*. Every check would pass while the real goal regressed.

### B. Close the byte program; make step economy the governing goal — **chosen**

Retain bytes as reported drift signal; stop restructuring commands to satisfy them; build an instrument that observes real runs against declared bounds and exit criteria.

- **Pros:** Measures the stated goal. Uses primitives Writ already has (`exit_criteria`, `loop.max_iterations`, `attempts` in state files) rather than inventing governance. Closes the ex-ante/ex-post gap — the first instrument that observes behavior rather than artifacts. Directly aligned with rising autonomy, where step waste compounds.
- **Cons:** The instrument does not exist and must be built. Step counting is harder to measure than bytes and is partly platform-dependent (tool-call granularity differs across harnesses, which cuts against Writ's adapter neutrality). Loses the mission's simple, quotable byte number. Some prior Phase 10 work becomes sunk cost.
- **Effort:** Medium — one instrument, plus a schema addition to existing state files.
- **Risk:** Medium. The main risk is that step counts prove as hard to attribute as tokens, leaving Writ with no working efficiency metric at all. **Mitigation:** the first deliverable is a measurement of existing recorded runs, not a new governance rule — if attribution fails, that is learned before anything depends on it.

### C. Keep both — byte budget *and* step economy

Run the two metrics side by side; require a command to satisfy both.

- **Pros:** No prior work is discarded; each metric catches what the other misses.
- **Cons:** The two are in **direct opposition** for the extraction decision — extraction improves bytes and worsens steps. A rule requiring both to improve forbids extraction *and* forbids consolidation, freezing the corpus. Two metrics with no stated precedence means every conflict is re-litigated per file, which is precisely the "spend steps deciding" failure mode.
- **Effort:** Medium-high — build the new instrument *and* maintain the old constraint.
- **Risk:** High. Unranked competing metrics reliably produce paralysis or arbitrary local rulings.

### D. Abandon measured efficiency governance entirely

Delete the byte cap and the ratchet; rely on review judgment.

- **Pros:** Zero instrument cost; honest about what is genuinely unmeasurable today; ADR-021 named this as "the honest null option" in its own alternatives.
- **Cons:** ADR-019's ratchet is cheap and has caught real drift — discarding it loses working machinery to fix an unrelated problem. Leaves no answer to "is Writ getting heavier?" Contradicts ADR-015's dogfooding posture.
- **Effort:** Trivial.
- **Risk:** Medium — bloat returns unobserved, which is the exact condition ADR-021 documented ("four unjustified-growth warnings… live right now and have been ignored").

### E. Option B, plus revert the pilot

As B, but also restore `commands/implement-story.md` to its monolithic form to remove its 9 decision points.

- **Pros:** Removes the largest single concentration of decision points in the corpus; leaves one consistent authoring style.
- **Cons:** Discards a measured **−35.9% floor reduction** paid on every single `implement-story` run, plus measured gains on `--quick` paths. Costs real work to undo work. Destroys the only real-world data point the new instrument will have. The 9 decision points are a *hypothesis* about cost under the new frame — reverting before measuring repeats exactly the error this ADR exists to correct.
- **Effort:** Medium — revert plus re-verification against the 281-row no-drift inventory.
- **Risk:** Medium-high. **Acting on an unmeasured belief is the failure mode being corrected.**

## Decision Outcome

**Option B.**

Driver 1 (step economy) decides it: Option A actively worsens the primary goal, and Option C cannot resolve the two metrics' direct opposition without a precedence rule that is just Option B with extra ceremony.

Option E is rejected on the strength of driver 2. Reverting the pilot because 9 decision points *look* expensive would be the same category of error as extracting six commands because 46 KB *looked* expensive — acting on an intuition about cost before the instrument that measures it exists. The pilot stays and becomes the first thing measured.

Option D is rejected because ADR-019's ratchet works; the problem is what was built *on top of it*, not the ratchet.

**What is explicitly NOT decided here:**

- Whether `implement-story` should ultimately keep its extraction — that awaits measurement, and this ADR's review trigger is its destination.
- Whether commands should be consolidated or removed (ADR-021 deferred this; it stays deferred).
- Any change to ADR-020's component contract, ADR-022's gate classes, or the Question Policy.
- Any change to `required_skills:`, which already has no consumer and carries its own 2026-11-11 review trigger.

## Consequences

**Positive**

- Writ measures what it says it cares about, for the first time.
- The governance loop closes: declared bounds and exit criteria become verifiable against real runs instead of being asserted and forgotten.
- Command authoring gains a clear virtue — *decisiveness* — that is actionable in review. "This sentence makes the agent choose; can it just say what to do?" is a better review question than "is this file under 24,960 bytes?"
- Directly serves rising autonomy: the metric degrades visibly as an agent wanders, which is when it matters most.
- Four closed specs stop being ambiguous. They are closed because the program is closed, not merely because one pilot regressed.

**Negative**

- **The new instrument does not exist.** Until it does, Writ has *no* enforced efficiency metric — the byte cap is demoted before its replacement ships. *Mitigation:* bytes continue to be measured and reported throughout; only their authority is removed. The ratchet still catches runaway growth.
- **Step counts are platform-dependent.** Tool-call granularity differs across Cursor, Claude Code, and Codex, which cuts against Writ's adapter-neutrality constraint. *Mitigation:* measure from Writ's own state files (`attempts`, story statuses, gate iterations), which are platform-neutral by construction, before considering any harness-native telemetry.
- **Some Phase 10 work becomes sunk cost.** Five contract-locked specs with pinned-literal inventories will not be executed. *Mitigation:* they are archived intact and unexecuted as design records; ADR-021's extraction *technique* remains valid if the economics ever change.
- **The mission loses a quotable number.** "516KB of command prose" was rhetorically effective. *Mitigation:* replace it with a step figure once measured — a stronger claim, because it describes what using Writ costs rather than what Writ weighs.
- **This ADR is itself unvalidated.** The claim that 9 decision points cost more than 27,872 floor bytes is *reasoned, not measured*. *Mitigation:* it is written as the hypothesis the first instrument must test, not as a settled finding. If measurement contradicts it, this ADR is the thing to supersede.

## Implementation Notes

**Prerequisites:** none. No code change is required to close the byte program — only the removal of its authority, recorded here.

**Steps:**

1. Record this reversal in `.writ/product/roadmap.md` Phase 10, whose success criteria still cite byte targets.
2. Demote the byte cap in `scripts/eval-leanness.py` from constraint to reported metric (it already emits a *warning*, not a finding — verify and document, do not tighten).
3. Build `scripts/measure-run.py`: given an execution state file, report steps-to-exit-criteria, overrun, bound adherence, gate iterations, and repeat reads.
4. Backfill it against the recorded runs already in `.writ/state/` (`phase-execution-20260719-121255`, `-20260811-2030`, `-20260812-0200`) — measurement before governance.
5. Only then decide whether any threshold should bind.

**Success criteria:**

- No command file is restructured to satisfy a byte target after this date.
- `measure-run.py` reports steps-to-exit-criteria for at least three recorded runs.
- The `implement-story` extraction is measured under the new instrument and its disposition recorded.

**Review date:** **2026-11-11**, aligned to ADR-021's own trigger and to the `required_skills:` review, so all three resolve together. If `measure-run.py` does not exist by then, this ADR failed and the honest response is Option D, not another instrument.

## Dissent and Corrections

**Recorded because the reasoning path matters more than the conclusion.**

- The four disclosure specs were closed on **2026-08-12 under the originating spec set's Business Rule 1** ("a pilot regression is a signal about the approach rather than a per-file exemption") — *before* this ADR, and on different reasoning. This ADR ratifies that outcome on stronger grounds; it does not claim the closure waited for it.
- During the review that produced this ADR, three claims were made in argument and then **withdrawn against evidence**: that the eager `required_skills:` pre-load justified closing the specs (it does not — the specs use inline reads and never adopt the field); that `/create-spec` is a sequential pipeline with little to skip (false — 25.7% of it is three mutually-exclusive mode blocks); and that the pilot regressed 18% with its prescribed exemption ungranted (it regressed **9.7%** on the full path only, improved on `--quick` paths, and the exemption **was** granted in ADR-021's amendment). Each correction moved the argument *toward* keeping the pilot and *away* from a bytes-based case. The surviving argument rests on the decision-point census alone.
- **The strongest case against this ADR** is that step economy may prove as unmeasurable as tokens, leaving Writ with no metric at all. That case is not answered here — it is deferred to the 2026-11-11 review, with Option D named in advance as the honest fallback.

## References

- [ADR-021](adr-021-progressive-disclosure-token-budget.md) — superseded premise and binding instrument; its two 2026-08-12 amendments carry the pilot's corrected figures
- [ADR-020](adr-020-component-contract.md) — `exit_criteria`, the anchor the new measurement is taken against
- [ADR-019](adr-019-full-surface-leanness-measurement.md), [ADR-015](adr-015-leanness-self-governance.md) — the retained ratchet
- [ADR-022](adr-022-autonomy-gate-classes.md) — the autonomy context that makes step waste compounding rather than merely costly
- `.writ/docs/phase-execution-state-format.md` — `attempts` and gate records, the platform-neutral substrate for step measurement
- `scripts/measure-invocation.py` — the byte instrument, retained and demoted
- `.writ/specs/archive/2026-08-12-disclosure-*` — five specs, archived intact and unexecuted as design records
