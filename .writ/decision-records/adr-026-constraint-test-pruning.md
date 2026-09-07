# ADR-026: Constraint-Test Pruning of the Shared Base

> **Date:** 2026-09-07
> **Status:** Accepted
> **Category:** Framework Architecture
> **Extends:** [ADR-023](adr-023-stakes-proportional-diligence.md) — bytes stay a reported metric; this ADR supplies the rule that decides what leaves, so the byte finish line is never the reason a line is cut
> **Constrains:** [ADR-024](adr-024-model-delegation.md) — model-specific instruction lives in `adapters/`, one line per model, never in the base
> **Deciders:** @AdamSellke
> **Research:** [`.writ/product/2026-09-05-goldilocks-assessment.md`](../product/2026-09-05-goldilocks-assessment.md) §2.1, §3 Mechanism 1, §5 Step 2; [`.writ/research/2026-09-05-goldilocks-harness-research.md`](../research/2026-09-05-goldilocks-harness-research.md) F2

## Decision

**Every line of `system-instructions.md` and `commands/_preamble.md` is classified by a three-way test, and only the first two classes stay.**

| Class | Definition | Fate |
|---|---|---|
| **Environment fact** | Names something about the environment the model cannot infer: a path, a tool name, a file format, an exit code, a state file, a command's contract | **Stays**, byte-identical |
| **Human boundary** | Names something the agent must never do without a person: merge, push, release, delete a spec, mark a story complete on its own word | **Stays**, byte-identical |
| **Behavior request** | Tells the model how to think or work in a way Fable 5.1-class models already do unprompted: judgment heuristics, prose style, tutorials, worked examples, coaching | **Leaves** — to `.writ/docs/` when it is documentation, or to the ledger alone when it is coaching |

Three rules make the test enforceable rather than aspirational:

1. **Every line that leaves gets a ledger row.** `.writ/decision-records/pruned-instructions-ledger.md` is append-only: `| date | file | class | reason | verbatim text |`, with class one of `moved`, `behavior-request`, `duplicate`. The row lands in the same commit as the removal.
2. **`scripts/prune-ledger.py check` is the gate.** It diffs both base files against the pinned Stage 1 closeout commit `cf84742`, requires a row with identical text for every removed line, and flags any row whose text is back in its file. `eval.sh` runs it as `pruned-base` on every commit.
3. **Bytes are the finish line, not the rule.** The Goal Card's 10,000-byte cap is reported as a note until the cut reaches it, then flips to blocking (the ledger carries `<!-- cap: blocking -->`). No line is removed *because* of the cap; a line is removed because it fails the test, and the cap says when to stop.

The cut is provisional until the Stage 1 baseline is re-run on the pruned base. If exit-criteria pass rate falls, the moves and cuts revert as a commit range; the ADR, the ledger, and the tooling survive.

## Context

### What forced the decision

The assessment measured the shared base at **28,157 bytes**, loaded on every invocation before any command runs, carrying 61 imperative rules (`system-instructions.md` 45, `_preamble.md` 16) against a research ceiling where all-rules compliance falls sharply around 40 rules (§2.1). The base alone crosses the first threshold. §3 names the mechanism: **behavior-request debt** — every release since March added instruction about how the model should work, calibrated to that month's model, and Writ has no process for removing any of it. Vendor guidance now says this class of instruction "can degrade output quality" on current models.

§2.2 confirms the pattern at the agent level: the coaching-heavy agents are the ones the research says degrade output; the constraint-heavy ones are the ones the dogfooding study found load-bearing. The base is where both kinds are mixed together with no marker telling them apart.

### Why a test and not a target

ADR-023 already ruled that a byte cap is the wrong governor: it optimizes a quantity nobody has a goal about and says nothing about *which* bytes. Reaching 10,000 bytes by rewording or compressing kept lines would satisfy the number and change nothing about compliance — and would break Business Rule 5 (kept lines byte-identical), which is what makes the ledger check meaningful. The constraint test is a rule about *content class*; the cap is only the stopping condition.

### Why a ledger and a check

§5 Step 2's exit criterion is "every removed line appears in the ledger with a reason." Without a mechanical check, the ledger is a courtesy that drifts on the second commit. With one, three failure modes become findings: a removal with no row (`removed_not_in_ledger`), a row whose text crept back (`ledger_text_reappeared` — the Goal Card's stall signal), and a hand-edited row that no longer parses (`malformed_row`). The check reads git's own line diff, never a re-implementation, and normalizes nothing, so a kept line that was accidentally reflowed shows up as a removal — the intended way to catch a Business Rule 5 violation.

## Considered Options

### A. Byte target alone
- **Pros:** One number; `measure-invocation.py` already reports it; no classification work.
- **Cons:** ADR-023's finding stands — a number with no derivation linking it to harm invites the wrong cuts (compress what is easy, keep what is coaching). Cannot tell a moved doc from a deleted constraint. No record of what left, so re-adding is archaeology.
- **Risk:** High. The base could hit 10 KB with every behavior request still in it.

### B. Per-model prompt tuning
- **Pros:** Matches vendor guidance directly — tune the instruction set to each model's defaults.
- **Cons:** Multiplies the base by the number of supported models; every model release reopens every line; the exact growth mechanism §3 diagnoses, with more files. ADR-024 already confines model-specific text to `adapters/`.
- **Risk:** High. Trades one drifting base for four.

### C. Do nothing
- **Pros:** Zero cost; the base works today on the Stage 1 baseline (8/8).
- **Cons:** 8/8 was measured with a base already past the compliance threshold; the pass rate says the model recovers from noise, not that noise is free. Growth continues at +79% per five months with no removal process.
- **Risk:** Medium now, rising with every release.

### D. Constraint test with an append-only ledger and a mechanical check — **chosen**
- **Pros:** Classifies by content, not size; every removal is one commit to reverse; the check runs on every commit so the ledger cannot drift; the re-run makes the cut falsifiable.
- **Cons:** Classification is a judgment per line — the test is stated but the call is human. A behavior request that turns out to be load-bearing is only discovered by the baseline re-run.
- **Risk:** Low–Medium. The re-run and the revert path bound the downside to one spec's cost.

## Decision Outcome

**Option D.** A rejects itself on ADR-023's reasoning; B recreates the disease; C lets it compound. D is the only option whose failure mode is visible (the re-run) and cheap to unwind (a `git revert` of a named commit range).

**Not decided here:** which specific lines fail the test — that is Story 2's move table and Story 3's classification table, both recorded in the story files; whether agent prompts get the same treatment (a later spec; §2.2 says they should).

## Consequences

**Positive**

- The base stops being the place where coaching accumulates; a new line must name an environment fact or a human boundary to land.
- Every removal is reversible in one commit with its reason attached — no archaeology.
- The stall signal (a line removed then re-added) is a finding, not a feeling.
- Docs that were living in the base become linkable files under `.writ/docs/`, where they cost nothing until read.

**Negative**

- **A behavior request later found load-bearing costs a baseline re-run to discover.** The constraint test cannot see which coaching lines the model still needs; only an eight-run re-run (about $190 and 5.5 hours at Stage 1 rates) can. *Mitigation:* the re-run is a story in the same spec, and Business Rule 10 makes keep-or-revert mechanical so the discovery is acted on rather than argued about.
- **Kept lines cannot be improved while the cut is open.** Business Rule 5 freezes them byte-identical so the diff is exact; a real wording fix waits for the cut to close. *Mitigation:* the freeze is against one pinned commit and ends when the re-run decides.
- **The ledger is one more file to keep honest.** *Mitigation:* `check` runs on every commit; a hand-edit that breaks a row is a finding.
- **Whitespace-only lines and in-file moves are exempt from the ledger** so the check stays satisfiable — a blank line has no instruction to account for, and a row for one would read as re-added wherever another blank line exists. This is a small hole in "every line": a section deleted in full loses its blank lines silently. *Mitigation:* the non-blank lines around them are ledgered, which is where the content was.

## Implementation Notes

1. `scripts/prune-ledger.py check --repo . [--base-commit cf84742] [--cap 10000] [--cap-blocking]` and `measure --repo .` — Story 1.
2. `.writ/decision-records/pruned-instructions-ledger.md` — created empty in Story 1; rows land with Stories 2 and 3.
3. `scripts/eval.sh` `check_pruned_base()` registered as `pruned-base` — Story 1; it passes `--cap-blocking` when the ledger contains `<!-- cap: blocking -->`, which Story 3 appends on reaching the cap.
4. Re-run and keep-or-revert — Story 5 of the same spec.

**Success criteria:** every commit on the spec branch has `pruned-base` green; the base reaches ≤ 10,000 bytes with no kept line changed; the re-run holds 8/8 or the cut reverts.

**Review date:** at the close of Stage 2's second spec (gate mechanization), when the same test is considered for agent prompts.

## References

- [ADR-023](adr-023-stakes-proportional-diligence.md) — why bytes are the wrong rule and an acceptable finish line
- [ADR-024](adr-024-model-delegation.md) — where model-specific text lives
- [`.writ/product/2026-09-05-goldilocks-assessment.md`](../product/2026-09-05-goldilocks-assessment.md) — §2.1 load, §3 Mechanism 1, §5 Step 2
- [`.writ/issues/goals/2026-09-05-writ-contract-and-verifier-layer.md`](../issues/goals/2026-09-05-writ-contract-and-verifier-layer.md) — the Goal Card whose Stage 2 this executes
- `.writ/specs/2026-09-07-phase11-stage2-prune-the-base/` — the spec carrying Stories 1–5
