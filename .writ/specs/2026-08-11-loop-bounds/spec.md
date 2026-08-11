# Spec: Loop Bounds

> **Status:** Not Started
> **Owner:** @AdamSellke
> **Created:** 2026-08-11
> **Dependencies:** [2026-08-11-component-contract]
> **Origin:** `/plan-product` Phase 10 discovery (2026-08-11). A maintainer concern that Writ is "not deterministic enough" was measured rather than accepted; the determinism half measured worse than the token half, and its sharpest single number was **0 of 5 loop-bearing commands declare an iteration bound** (`.writ/product/roadmap.md` Phase 10, [ADR-020](../../decision-records/adr-020-component-contract.md)).

## Contract (Locked)

**Deliverable:** `loop.max_iterations` + `loop.on_exhaustion` on the five verified-unbounded loop-bearing commands: `implement-phase` (302 lines), `implement-spec` (264), `implement-story` (961), `refactor` (191), `verify-spec` (711).

**Must include:** `on_exhaustion` maps onto `scripts/phase-state.py`'s **existing** `retry` / `quarantine` verbs rather than inventing parallel failure handling. Each bound is derived from that loop's real semantics — `/implement-phase` bounds specs-per-phase, `/implement-story` bounds gate-retry cycles, `/verify-spec` bounds auto-fix passes — not a single global constant.

**Hardest constraint:** This is the sharpest determinism gap measured (**0 of 5** loop-bearing commands declare any bound), but a bound set too low turns a working loop into a spurious failure. Bounds must be calibrated against observed real runs (Phase 7's 4-spec and Phase 9's 3-spec executions are the available evidence), and `on_exhaustion` must always terminate with a *reported, recoverable* state — never a silent stop.

## Why This Exists

Writ has extensive deterministic tooling — roughly thirty `eval-*.py` scripts, a 155KB `eval.sh` harness, `lint-skill.sh`, `check-agent-parity.sh`, `phase-state.py` — and none of it asks whether a command that loops knows when to stop. The measurement in ADR-020 is exact: 32 of 32 commands carry `---` YAML frontmatter, and every one of them carries exactly two keys, `name:` and `description:`. Nothing structural is declared, so nothing structural can be checked.

The gap is not that Writ's loops run forever in practice. Two of the five commands already carry prose bounds, and those bounds work:

- `commands/implement-story.md:595` — *"Max 3 iterations across review and visual QA gates... Gate 4 testing failures have a separate 2-iteration cap."*
- `commands/implement-phase.md:201` — *"Writ permits exactly one transient retry"*, enforced in code by `scripts/phase-state.py` (`cmd_classify` retries only when `classification == "transient" and attempts < 2`; `cmd_retry` raises `retry_exhausted` at `attempts >= 2`).

So the honest statement of the problem is narrower and more actionable than "the loops are unbounded." **The bounds that exist are unenforceable prose, and the bounds that don't exist were never noticed missing.** A prose cap cannot fail a build, cannot be read by `yq`, and cannot stop a thirty-third command from shipping with a loop and no cap.

> **Note (2026-08-11):** an earlier draft of this paragraph cited ADR-020's `## Completion` finding as the same diagnosis. That parallel does not hold and the citation was removed. ADR-020's premise — that `commands/new-command.md` already mandated `## Completion` — was measured during Phase 10 spec authoring and found false; `## Completion` was an emergent convention that nothing ever required, so for *that* case the contract was genuinely missing. See the ADR-020 Amendments section, specified in `2026-08-11-component-contract` Story 1. The "unenforced, not missing" framing **is** accurate for loop bounds, on this spec's own evidence: `implement-story.md:595` and `implement-phase.md:201` carry real bounds that are honored today.

The counterweight is what makes this spec risky rather than mechanical. A bound is a tripwire, and a tripwire set too low converts a run that would have succeeded into a failure that costs a human a recovery cycle. The available calibration evidence is real but thin — two recorded phase runs, three recorded spec runs, forty-two recorded story review-iteration counts, and **zero** recorded `/refactor` runs. This spec therefore treats calibration as the primary deliverable and the frontmatter block as the carrier, not the other way around.

## 📋 Business Rules

1. **Every declared bound cites the run it was calibrated against.** `calibrated_against:` is a required key in every `loop:` block. Its value must name a real path under `.writ/state/`, a real artifact under `.writ/specs/`, or a roadmap phase — and must state the evidence quality in the same line. A bound with no citation is a defect, not a warning.

2. **No bound may be set below the highest value observed in a recorded historical run.** Before a number is written, it is checked against every run recorded in `.writ/state/` and every `Iteration count` record in archived story "What Was Built" sections. A bound that would have tripped any of those runs is rejected outright — it is not shipped with a caveat, and it is not shipped with an exemption.

3. **`on_exhaustion` produces a named, resumable state — never a bare halt.** Every exhaustion emits, at minimum: the loop's `unit`, the declared bound, the count reached, the last completed unit, and a literal command that resumes from there. A loop that stops without writing that record has failed this spec even if it stopped at the right iteration.

4. **`on_exhaustion` composes with `phase-state.py`'s existing retry rule; it never re-implements or widens it.** `retry` is *not* a legal `on_exhaustion` value. Retry is what happens before exhaustion, governed today by `cmd_classify` / `cmd_retry` (`attempts < 2`, one transient retry, quarantine thereafter). `on_exhaustion` fires only once that budget is spent, and the `quarantine` value invokes `scripts/phase-state.py quarantine` rather than any new disposition path.

5. **Exhaustion never degrades scope and never self-certifies.** Per [ADR-013](../../decision-records/adr-013-recommended-autonomous-delivery.md) and [ADR-022](../../decision-records/adr-022-autonomy-gate-classes.md), an exhausted loop may not skip a story, drop an exit criterion, relax an acceptance criterion, or mark anything Complete to get itself unstuck. Where continuing past exhaustion would change scope, the only legal `on_exhaustion` is `escalate`.

6. **`loop:` is reserved in the ADR-020 frontmatter schema and restructures nothing.** It is a sibling key to `problem:` / `outcome:` / `exit_criteria:` in the same `---` block that `2026-08-11-component-contract` is adding those three to. This spec adds one key; it does not reorder, rename, or re-carrier anything that spec defines, and it does not introduce a second frontmatter block or a sidecar file.

7. **Existing prose bounds are transcribed, not re-derived.** Where a command or agent already states a number — `implement-story.md`'s 3 and 2, `coding-agent.md:232` / `testing-agent.md:225`'s `MAX_SELF_FIX_ITERATIONS = 3`, `phase-state.py`'s `attempts < 2` — the `loop:` block carries that exact number. Changing an existing enforced number is a separate decision requiring its own evidence, and is out of scope here.

8. **A bound with thin evidence says so in the file.** `/refactor` has zero recorded runs anywhere in `.writ/state/`. Its bound is a runaway guard chosen against a single advisory sentence in the command file, and `calibrated_against:` must say exactly that rather than cite a proxy. Inventing precision that the evidence does not support is the specific failure this rule exists to prevent.

## Detailed Requirements

### The `loop:` frontmatter block

Added to the same `---` YAML block ADR-020 extends. Shape:

```yaml
loop:
  unit: "spec"                  # what one iteration counts
  max_iterations: 12
  on_exhaustion: halt_reported  # one of: quarantine | escalate | halt_reported
  calibrated_against: "..."     # evidence citation + evidence quality
  nested:                       # optional; same four keys per entry
    - unit: "spec_attempt"
      max_iterations: 2
      on_exhaustion: quarantine
      calibrated_against: "..."
```

`max_iterations` and `on_exhaustion` are required at the top level of `loop:`, satisfying the contract path literally. `nested:` exists because `/implement-story` carries three distinct, already-enforced caps that a single integer cannot represent; single-loop commands omit it entirely and cost four lines.

The roadmap's feature line names three fields — `loop.bound` / `max_iterations` / `on_exhaustion`. `unit:` is this spec's name for what that line called `bound`: the thing being counted. That rename is deliberate — "bound" reads as the number, and the number is `max_iterations`.

### The `on_exhaustion` vocabulary

Exactly three values. No others are legal.

| Value | What it does | Where it is legal |
|---|---|---|
| `quarantine` | Invokes `scripts/phase-state.py quarantine` for the current spec: removes the lane worktree, preserves the lane as `writ/quarantine/{spec-id}`, proves the phase branch is clean of it, records failure evidence + attempt count + recovery command, and marks transitive dependents `skipped_blocked` with `blockedBy` evidence. | Only where a `phase-execution-*.json` record for the unit exists. |
| `escalate` | Pauses and presents one bounded `AskQuestion` naming the loop, the bound, the count reached, and the partial state — the shape `/implement-story` already uses at Gate 1 and Gate 4 for `STATUS: BLOCKED`. | Anywhere. Mandatory wherever continuing would change scope (Business Rule 5). |
| `halt_reported` | Stops without asking, and writes a named terminal record: `unit`, bound, count reached, last completed unit, resume command. | Anywhere a durable state file or report section exists to write into. |

`retry` is deliberately absent (Business Rule 4). So is any value meaning "continue anyway."

### The five bounds

Each number below is proposed with its evidence and its evidence quality stated plainly.

| Command | `unit` | `max_iterations` | `on_exhaustion` | Evidence | Quality |
|---|---|---|---|---|---|
| `implement-phase` | `spec` | **12** | `halt_reported` | Phase 9 = 3 specs (`.writ/state/phase-execution-20260719-121255.json`, `specOrder` length 3, every spec `attempts: 1`, zero retries, zero quarantines). Phase 7 = 4 specs (roadmap-attested; no state file survives). Phase 10 as planned = 6 features. Largest observed = **4**. | Thin — two runs, one of them without a surviving state file. 12 is 3× the largest observed. |
| `implement-phase` (nested) | `spec_attempt` | **2** | `quarantine` | Already enforced in code: `scripts/phase-state.py` `cmd_classify` (`attempts < 2`) and `cmd_retry` (`retry_exhausted` at `>= 2`). | Strong — transcription of enforced code, changes nothing. |
| `implement-spec` | `story` | **12** | `halt_reported` | Largest story count across all 41 archived specs = **9** (`2026-03-19-command-suite-evolution`). Recorded runs: `execution-20260718-1101.json` = 4, `execution-20260803T193200Z.json` = 4, `execution-20260804205617.json` = 4. Phase 9 spec results = 4 / 4 / 3 stories. | Strongest of the five — 41 authored specs plus 6 recorded runs. 12 = all-time max + 3. |
| `implement-story` | `review_cycle` | **3** | `escalate` | 42 `Iteration count` records in archived story "What Was Built" sections: **38 at 1 iteration, 4 at 2**. Max ever observed = **2**. Already declared in prose at `commands/implement-story.md:595`. | Strong — 42 real records. A bound of 2 would sit at the observed limit with zero headroom, and is rejected under Business Rule 2's spirit. |
| `implement-story` (nested) | `testing_cycle` | **2** | `escalate` | Already declared at `commands/implement-story.md:732`. No recorded run reports a testing-fix iteration count above 1. | Adequate — transcription; the underlying evidence for the original 2 is not recorded anywhere. |
| `implement-story` (nested) | `agent_self_fix` | **3** | `escalate` | `MAX_SELF_FIX_ITERATIONS = 3` in `agents/coding-agent.md:232` and `agents/testing-agent.md:225`, consumed by `implement-story.md:513/734/942`. | Strong — transcription of a value two agents already enforce. |
| `refactor` | `change` | **10** | `halt_reported` | **Zero recorded runs.** The only quantitative anchor in the repo is `commands/refactor.md:100` — *"For large plans (7+ changes), recommend splitting into sessions."* 10 sits above that existing advisory threshold so the bound cannot fire before the advice that already exists. | **Weak, and labelled as such.** A runaway guard, not a plan-size policy. Recalibrate after the first recorded run. |
| `verify-spec` | `autofix_pass` | **1** | `halt_reported` | The command is single-pass by construction: Phase 3 runs checks 1–8, Phase 4 applies fixes 4.1–4.4, Phase 5 writes the report. `commands/verify-spec.md` contains no re-check, re-run, or re-verify step (the sole `again` at line 698 describes `/release` invoking checks 1–8 through its own entry point). | Strong by construction — declaring 1 codifies what the file already does and can break no run. |

### The honest note on `/verify-spec`

`/verify-spec` has no runaway loop to bound. Its auto-fix is a single linear pass. Including it in the "0 of 5 unbounded" figure is defensible as a *missing declaration*, but calling it a missing *bound* overstates the risk for that one command. This spec declares `max_iterations: 1` because the declaration is the deliverable and the number is free — not because a real `/verify-spec` runaway has ever been observed. That distinction is recorded here so a future reader does not infer evidence that does not exist.

### Coordination with `2026-08-11-component-contract`

That spec owns the frontmatter block and adds `problem:` / `outcome:` / `exit_criteria:` to all 31 commands. This spec adds `loop:` to five of them. Both edit the same `---` block in the same five files. The coordination rule is one-directional: **this spec appends `loop:` and touches nothing else in the block.** It does not define, reorder, or validate the three ADR-020 fields, and if the two land out of order, `loop:` must be additive to whatever block exists at the time.

## Out of Scope

- **Changing any existing enforced number.** The 3, the 2, the `MAX_SELF_FIX_ITERATIONS = 3`, and `phase-state.py`'s `attempts < 2` are transcribed as-is (Business Rule 7). Re-deriving any of them is separate work with its own evidence burden.
- **New failure-handling machinery.** No new disposition verb, no parallel quarantine path, no new state schema. `on_exhaustion: quarantine` calls the existing `scripts/phase-state.py quarantine` subcommand.
- **Bounds on the other 26 commands.** Only the five verified loop-bearing commands are in scope. A sixth command acquiring a loop later is the eval check's problem, not this spec's.
- **Presence checking of `loop.max_iterations` / `loop.on_exhaustion`.** `2026-08-11-governor-instrumentation` Check 3 already owns this and already names the same five commands (expected findings today: 10). This spec's check asserts **correctness** — enum closure, integer type, citation quality, unit uniqueness, historical-run non-regression, and transcription drift — and skips any file with no `loop:` block, letting Check 3 report the absence. Presence and correctness are checked once each, by one owner each.
- **The generic `structural` finding machinery.** Roadmap Phase 10's "Make the governor bite" feature owns the blocking-`structural` classification, the `check_length` 2000 → 400 change, and the absolute `per_surface` cap. This spec's check must degrade to a non-blocking report if that machinery has not landed yet.
- **`problem:` / `outcome:` / `exit_criteria:` themselves.** Owned by `2026-08-11-component-contract`.
- **Progressive disclosure / command decomposition.** `implement-story` is 961 lines and will be restructured by the ADR-021 work. This spec adds four lines to its frontmatter and must survive that restructuring, but does not participate in it.
- **Runtime enforcement of bounds by an executor.** Writ commands are markdown read by a model; `loop:` is a declared, lintable contract that the model follows and `eval.sh` verifies is present and calibrated. Nothing here builds an interpreter that counts iterations at runtime.
