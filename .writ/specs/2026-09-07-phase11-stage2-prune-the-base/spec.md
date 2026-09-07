# Phase 11 Stage 2a: Prune the Base

> **Status:** Not Started
> **Created:** 2026-09-07
> **Owner:** @unknown
> **Dependencies:** [2026-09-05-phase11-repair-and-baseline]
> **Origin:** Promoted from Goal Card [`2026-09-05-writ-contract-and-verifier-layer.md`](../../issues/goals/2026-09-05-writ-contract-and-verifier-layer.md) — Stage 2, first of two specs (this one prunes the shared base; gate mechanization for Gates 0, 0.5, 1, 2.5, 3, 5 is the second). Evidence: [`2026-09-05-goldilocks-assessment.md`](../../product/2026-09-05-goldilocks-assessment.md) §2.1, §3 Mechanism 1, §5 Step 2 and Governor; [`2026-09-05-goldilocks-harness-research.md`](../../research/2026-09-05-goldilocks-harness-research.md) (the constraint-vs-behavior-request test).
> **Loop:** unit `story` · `max_iterations: 8` · `on_exhaustion: halt_reported` · stalled 3 turns: stop and report (carried from the Goal Card's STOP-CAPS)

## Specification Contract

**Deliverable:** The shared base every Writ invocation loads (`system-instructions.md` + `commands/_preamble.md`) cut from 28,157 bytes to at most 10,000 by the constraint test, every removed line in an append-only ledger with a dated reason, every `implement-story` gate carrying an explicit verification marker, and the cut kept only because a full Fable 5.1 baseline re-run held the Stage 1 pass rate.

**Must Include:** A `compare` between the Stage 1 baseline (`.writ/eval/baselines/2026-09-06-claude-fable-5-1.json`) and a post-cut baseline that decides keep-or-revert with no human interpreting either side.

**Hardest Constraint:** Removing about 18 KB without touching a single environment fact or human boundary. The Prime Directive's hard constraints, ADR-013's production boundary, ADR-022's gate classes, and the Plan Mode integrity rules stay verbatim. Only behavior requests and documentation leave.

**Stories:**

1. **Pruning policy ADR and ledger tooling** — ADR-026 records the three-way test as the pruning rule; `scripts/prune-ledger.py check` verifies ledger coverage, reports bytes against the cap, flags re-added lines; `eval.sh` check `pruned-base`.
2. **Move documentation out** — Model Tiers, `required_skills`, Skill authoring, Startup Update Awareness, and the Recommendation Semantics tutorial move to `.writ/docs/` with one-line links; bytes measured and recorded before Story 3 begins.
3. **Cut behavior requests** — line-by-line classification of what remains; behavior requests removed with reasons; the Fable 5.1 batching line moves to `adapters/`; base lands at or under 10,000 bytes.
4. **Gate verification markers and provenance check** — `implement-story.md` frontmatter `gates:` block; `eval.sh` check `verdict-provenance`.
5. **Baseline re-run and keep-or-revert** — eight Fable 5.1 runs on the pruned base, `compare` against Stage 1, keep at 8/8 or revert Stories 2–3.

**Success Criteria** (Goal Card DONE WHEN line 3 verbatim, plus the QUALITY rule):

- `system-instructions.md` + `commands/_preamble.md` total at most 10,000 bytes, and every removed line appears in `.writ/decision-records/pruned-instructions-ledger.md` with a dated reason.
- Baseline exit-criteria pass rate on the yuss.app set after the cut is at or above the Stage 1 figure (8 of 8).
- `bash scripts/eval.sh` exits 0 at the end of every story.
- No file under `adapters/` gains more than one model-specific instruction line per model.

**Scope Boundaries:**

- **Included:** the two base files; the Prime Directive mirror in `cursor/writ.mdc`; new `.writ/docs/` targets; the `adapters/` batching line; `implement-story.md` frontmatter; two new `eval.sh` checks; ADR-026; the ledger; one eight-run baseline re-run and its committed JSON.
- **Excluded:** scripts for Gates 0, 0.5, 1, 2.5, 3, 5 (the second Stage 2 spec); pruning of command bodies (`create-spec`, `implement-phase`, `implement-story`) — Stage 2 names the base only; the decisions-per-run governor (lands with mechanization, where the forks change); `spec-analyze.py` (Stage 3); any run on a model other than Fable 5.1.

---

## 🎯 Experience Design

**Entry point.** A maintainer runs `/implement-spec` on this spec. Installed projects meet the result only after a human `/release`: a smaller `system-instructions.md`, new files under `.writ/docs/`, and an unchanged command surface.

**Happy path.** (1) Story 1 lands the ADR, the empty ledger, and a green `pruned-base` check that reports 28,157 bytes over the cap as a note, not a finding, because nothing has been removed yet. (2) Story 2 moves five documentation sections out, one commit per section, each commit carrying its ledger lines; the check reports bytes after each. (3) Story 3 classifies every remaining line and removes behavior requests until the check reports ≤ 10,000. (4) Story 4 declares each gate's verdict source. (5) Story 5 runs the eight replays and `compare` prints per-story deltas with exit criteria 2/2 on every row.

**Moment of truth.** The `compare` table after Story 5: exit criteria unchanged at 2/2 per story while the base is a third of its size. If tokens or wall clock also fell, that is the first measured evidence for Mechanism 1 in the assessment.

**Feedback model.** `prune-ledger.py check` prints one line per finding (`<file>:<line-text-hash>: removed line not in ledger`, `<file>: <bytes> bytes over 10000 cap`, `ledger line re-added: <text>`) and one summary line (`base: <bytes> bytes (cap 10000), ledger: <n> entries, re-added: <n>`). `eval.sh` relays findings; the summary is a note.

**Error experience.** A removal without a ledger line: `eval.sh` blocks naming the file and the missing text. A ledger line whose text reappears in the base: a finding naming the ledger date and the file it came back in; the Goal Card counts it toward the stall counter. A kept line accidentally reflowed: it shows as a removal without a ledger line, which is the intended behavior — kept lines stay byte-identical. Baseline re-run below 8/8: Story 5 re-runs the failed pair once via the resume path; if it still fails, the story reverts Stories 2–3 as one commit range and records the compare table under What Was Built; the ledger and the ADR survive the revert.

**State catalog.** Ledger empty (Story 1) / moves in progress (bytes falling, every commit green) / cuts in progress (classification table in the story file, bytes falling) / cap reached / re-run in progress (records flushed per run) / kept or reverted.

## 📋 Business Rules

1. **The constraint test is the rule; bytes are the finish line.** A line stays if it names a fact about the environment (paths, tools, formats, exit codes) or a human boundary (what the agent must never do without a person). A line leaves if it tells the model how to think or behave in a way Fable 5.1-class models do unprompted. ADR-026 records this; ADR-023 explains why bytes alone would be the wrong governor.
2. **The ledger is append-only.** Entries are never edited or deleted. A line removed then re-added to the base is a finding the check surfaces; the Goal Card counts it toward the stall counter.
3. **Removed includes moved.** Every line that leaves the base has a ledger entry, reason `moved: .writ/docs/<file>` or `behavior-request: <why>` or `duplicate: <where it survives>`.
4. **Ledger entries land in the same commit as the removal.** The check must be green at every commit on the branch, not only at story close.
5. **Kept lines stay byte-identical.** No reflow, rewrap, or reword of a line that stays; the check diffs against the pinned Stage 1 closeout commit (`cf84742`).
6. **Moves before cuts, measured between.** Story 2's closing record states the base byte count so Story 3 knows its depth before removing anything.
7. **One model-specific instruction line per model per adapter file.** The Fable 5.1 batching line is the whole model-specific surface this spec adds.
8. **Prime Directive mirror stays byte-identical.** `cursor/writ.mdc` is edited in the same commit as any Prime Directive change; `check_prime_directive_sync` stays green.
9. **Stage 1 selection is reused verbatim.** The re-run baseline file carries the identical `selection` block and `criteria` so `compare` never refuses.
10. **Keep-or-revert is mechanical.** Keep if `compare` shows exit criteria 2/2 on all four rows; otherwise revert. No partial keep.
11. **ADR-013 holds.** Nothing merges, opens a PR, or releases.
12. **Decision log.** Each story's closing commit appends one line: `{date} stage-2: {what changed and why}`.

## Detailed Requirements

### Story 1 — Pruning policy ADR and ledger tooling

- `.writ/decision-records/adr-026-constraint-test-pruning.md`: context (assessment §2.1, §3 Mechanism 1), decision (the three-way test), alternatives (byte target alone; per-model prompt tuning; do nothing), consequences including the negative one (a behavior request that turns out to be load-bearing costs a baseline re-run to discover).
- `.writ/decision-records/pruned-instructions-ledger.md`: header explaining the format, then one line per removed base line: `| YYYY-MM-DD | <source file> | <reason class> | <reason> | <removed text, verbatim, pipe-escaped> |`.
- `scripts/prune-ledger.py` (stdlib, Python 3.9): `check --repo . [--base-commit cf84742] [--cap 10000]` diffs the two base files against the pinned commit, treats every removed line (git line diff, whitespace-exact) as needing a ledger row with identical text; reports bytes; reports any ledger row whose text is present in either base file at HEAD. Exit 0 with no findings, 1 with findings, 2 on usage. A `measure` subcommand prints bytes per section for the maintainer.
- `eval.sh`: `check_pruned_base()` registered as `pruned-base`; relays findings; bytes-over-cap is a note until Story 3 closes, then a finding (the check takes `--cap-is-blocking` from an environment flag or a marker file the story flips; the story decides which and records it).
- Tests: pytest fixtures for each finding class; a bash fixture test for the eval wiring.

### Story 2 — Move documentation out

Sections that are documentation, not instruction (assessment §5 Step 2 candidates): `## Model Tiers` with `### entry_level` (4,519 bytes), `### required_skills: frontmatter convention` (2,809), `### Skill authoring` (458), `## Startup Update Awareness` (3,784), the tutorial portion of `### Recommendation Semantics` (rule kept, ~1,875 moved). Targets: `.writ/docs/model-tiers.md`, `.writ/docs/skills-convention.md`, `.writ/docs/startup-update-awareness.md`, `.writ/docs/recommendation-semantics.md` (or merged into existing docs where one already covers the topic; the story checks first). Each section leaves behind at most one line: what it is and where it went. Expected base after moves: about 15 KB. `check_referenced_paths` must resolve the new links. Any of these files that installed projects need at runtime (Startup Update Awareness is a procedure `update.sh` may read) keeps a pointer that the install path ships.

### Story 3 — Cut behavior requests

Classify every remaining line of both files into one of three classes; the classification table lives in the story's What Was Built. Cut candidates: `## Identity & Approach` prose, `## Command Execution Protocol` coaching, `### Judgment Principles`, `### Prose`, `## Interaction Tool Selection` beyond the rule that names the tools, `## Session Auto-Orientation`, the second `## File Organization` (duplicate of the preamble's), the preamble's `## Tool Selection`, `## Knowledge Context`, and `## Adapter Neutrality` where they restate adapter files. Keep verbatim: `## Prime Directive` → `### Hard Constraints`, the Recommended Delivery Exception's rule, `## Plan Mode Integrity`, `## User Challenge`'s four-part shape, `## Autonomy Gate Classes`, `## Artifact Integrity`. The Fable 5.1 batching line moves to each `adapters/*.md` as its single model-specific line. Stop when `prune-ledger.py check` reports ≤ 10,000 bytes; do not cut past the cap for its own sake. Flip the cap to blocking.

### Story 4 — Gate verification markers and provenance check

`implement-story.md` frontmatter gains:

```yaml
gates:
  - id: gate0_arch
    verification: prose-only
  - id: gate2_build
    script: scripts/build-smoke.py
  - id: gate4_tests
    script: scripts/test-integrity.py
  ...
```

One entry per gate heading in Step 3 (0, 0.5, 1, 2, 2.5, 3, 3.5, 4, 4.5, 5). Truthful today: two `script`, eight `prose-only`. `scripts/verdict-provenance.py check --command commands/implement-story.md` parses the headings and the block; a heading without an entry, an entry without a heading, an entry with neither key, or a `script:` path that does not exist is a finding; prose-only count over 2 is a note carrying the Goal Card's cap (the mechanization spec flips it to a finding). `eval.sh` check `verdict-provenance`. Gate 4.5 loses its percentage thresholds in the body text (the assessment: "an actual pixel or DOM diff or drop the percentage"); the verdict vocabulary stays.

### Story 5 — Baseline re-run and keep-or-revert

`python3 scripts/pipeline-baseline.py select` is not re-run; the new file is created by copying the Stage 1 file's header, `criteria`, `selection`, `excluded`, and `rejection_tally` with `runs: []` and `runs_per_story: null`, named `.writ/eval/baselines/<date>-claude-fable-5-1.json` (Business Rule 4 of Stage 1 allows sibling files by date). `run --model claude-fable-5-1 --runs 2` outside the sandbox, detached from the session (`nohup`), `--keep` into a scratch directory. `compare <stage1> <new>`: keep if every `exit_criteria` row reads `2/2`; else re-run the failed pair once, compare again, and if still short revert Stories 2–3 with `/revert` and record the table. Record tokens, wall clock, `cost_usd` sum, and the compare table in What Was Built. Decision-log line states keep or revert and the numbers.

## Implementation Approach

Python 3.9 stdlib scripts under `scripts/` with pytest under `scripts/tests/`, mirroring `pipeline-baseline.py`'s shape (subcommands, exit codes 0/1/2, `--repo`). Line diffs use `git diff --no-color -U0 <base-commit> -- <file>` parsed for `-` lines, never a Python reimplementation of diff. The ledger is markdown so it is readable in a PR and greppable; the check parses it with a fixed regex and refuses malformed rows. Byte counts use `os.path.getsize` on the working tree files.

## ⚠️ Technical Concerns

- **8/8 with no tolerance.** Stage 1 recorded one DEGRADED self-report that still re-derived `met`, and cache-read varied 59% between identical runs. One flaky failure forces a revert of real work. Mitigation is the single retry of the failed pair, then a mechanical revert; the ADR, ledger, and Story 4 survive.
- **Bytes are the wrong governor** (ADR-023). This spec honors the byte cap because the Goal Card sets it; ADR-026 frames the test as the rule and the cap as the finish line.
- **Diffing against a moving base.** The check pins `cf84742`. Reflowing a kept line reads as a removal; Business Rule 5 makes that the intended signal.
- **Cost.** One re-run at about $190 and 5.5 hours, plus one retry pair at about $50 worst case.

## 💡 Recommendations

- Moves before cuts, measured between (Business Rule 6).
- Ledger entries in the removal commit (Business Rule 4).
- Reuse the Stage 1 `selection` verbatim (Business Rule 9).
- One commit per moved section in Story 2 so a single bad move is a single revert.

## Approved Scope Additions

_None yet. Additions agreed after lock are recorded here with date, approver, and the story they land in; the contract above is unchanged._
