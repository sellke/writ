# Recommendation Log: Ship Watch and Merge

> Spec: [`spec.md`](spec.md)
> Mode: `/create-spec`, source mode `standard`, seeded by the Phase 16 orchestrator
> Authored: 2026-11-06, on branch `phase/16-verified-landing` at `3ddc8c8`

Each entry records one decision: what was decided, the evidence, the material alternatives, risk and reversibility, and the result. Entries with a doubt-log id were asked and answered by the maintainer; the id is the row in the orchestrator's `.writ/state/doubt-log.jsonl`.

## Decisions taken at the Phase 16 level

### R1. Two specs for Phase 16

- **Decision:** `2026-11-06-pr-ready-and-ledger` first (`pr-ready.py` and the ledger), then this spec (`/ship --watch` and the merge rule).
- **Evidence:** Roadmap Phase 16 lists four features; the two scripts are a dependency of the other two.
- **Alternatives:** One spec for all four features. Rejected: one spec would mix a script contract with command prose and the doubt rule.
- **Risk / reversibility:** Low. The seam sheet fixes the interface between them.
- **Result:** Answered as recommended. Doubt-log id `152a861a73d0`.

### R2. `/ship` fetches the snapshot; `pr-ready.py` makes no network call

- **Decision:** `pr-ready.py` judges a gh JSON snapshot file that `/ship` writes.
- **Evidence:** ADR-029's agent CLI contract: a default run makes no network call, and repeating work is the harness's job.
- **Alternatives:** `pr-ready.py` calls gh itself. Rejected: it would need a network allowance and could not be re-run by `jev-judge.py` without the network.
- **Risk / reversibility:** Low.
- **Result:** Answered as recommended. Doubt-log id `f24bdefa7c76`.

### R3. One exit code per blocker class

- **Decision:** 0 pass or unverifiable, 2 usage, 3 conflicts, 4 unresolved_threads, 5 failing_checks, 6 merge_gates; the code names the first class.
- **Evidence:** Roadmap Phase 16 Success Criteria ("distinct exit codes"); research F2 (pstack `watch-pr`).
- **Alternatives:** Plain check shape (exit 1 for every fail). Rejected: the harness loop could not tell blockers apart without parsing.
- **Risk / reversibility:** Low. This spec branches on reason codes, not the numbers.
- **Result:** Answered as recommended. Doubt-log id `743621d31cc5`.

### R4. What "verified" means

- **Decision:** The project's test and eval commands passed on that exact head; ledger rows record the commands and exit codes.
- **Evidence:** ADR-033 point 5; roadmap Phase 16 ("every verdict bound to the head it judged").
- **Alternatives:** Green CI as verification. Rejected: CI is a separate pr-ready blocker, and the ledger records what Writ ran.
- **Risk / reversibility:** Low.
- **Result:** Answered as recommended. Doubt-log id `84e3dd185e94`.

### R5. Contract A locked

- **Decision:** Lock `2026-11-06-pr-ready-and-ledger` as drafted, with its recommended answers.
- **Evidence:** The maintainer's "Lock as drafted", 2026-11-06.
- **Alternatives:** Edit before lock. Not taken.
- **Risk / reversibility:** Low; `/edit-spec` before its Story 1.
- **Result:** Answered as recommended. Doubt-log id `e92baa518105`.

### R6. This contract locked, with the seam reconciliations

- **Decision:** Lock this contract as drafted, with the reconciliations in spec.md → Reconciliations at lock: one `pr-ready.py --json` subprocess instead of two calls; contract A's gate tokens; `/ship` fetches thread comments itself; the CI run id from `detailsUrl`; Callers cells as the only `agent-cli-contract.md` edit; the real-PR run as a human UAT scenario.
- **Evidence:** The maintainer's "Lock as drafted", 2026-11-06, and the binding seam sheet.
- **Alternatives:** Keep the separate ledger call. Rejected in the seam sheet: a pr-ready `pass` already needs the ledger to read VERIFIED.
- **Risk / reversibility:** Low.
- **Result:** Answered as recommended. Doubt-log id `81015ad85fa8`.

### R7. Build before the roadmap gate

- **Decision:** Build Phase 16 although its gate (Phase 12 closed) is not met.
- **Evidence:** The maintainer's direction on 2026-11-06.
- **Alternatives:** Wait for Phase 12 to close.
- **Risk / reversibility:** Medium: Principle 8 (land before you add). The orchestrator records the exception in the roadmap at phase close; this spec does not edit the roadmap.
- **Result:** Adopted by the maintainer's direction.

## Open questions from the contract, answered as recommended

### R8. Eval command source (B-OQ1)

- **Decision:** An optional `- **Eval Command:**` line in `.writ/config.md`, with a row in `.writ/docs/config-format.md`. The Test Runner always runs; the eval command runs when configured.
- **Evidence:** No config key or detection chain named an eval command. The ledger row records exactly what ran, so a missing eval command is visible.
- **Alternatives:** Detect an eval command. Rejected: no convention exists to detect. Require one. Rejected: most projects have none.
- **Risk / reversibility:** Low.
- **Result:** Adopted (Story 2).

### R9. Landing method (B-OQ2)

- **Decision:** `Merge Strategy` when it is `merge`, `squash`, or `rebase`; otherwise `--merge`. No `--delete-branch`.
- **Evidence:** `config-format.md:48` documents `Merge Strategy` as base integration, yet its example sets `squash`. `ship.md` already defaults to merge.
- **Alternatives:** A new `Land Method` key. Rejected: a second key for most projects that already set one.
- **Risk / reversibility:** Low. GitHub refuses a disallowed method and the pass asks.
- **Result:** Adopted (Story 4).

### R10. Thread resolution (B-OQ3)

- **Decision:** Resolve a thread only after a pushed commit addresses it, with a reply naming the commit. Questions and disagreements get a reply or an ask, never a resolve.
- **Evidence:** No artifact said whether Writ may resolve a reviewer's thread. Research F2 says replies go through a JSON file.
- **Alternatives:** Never resolve. Rejected: pr-ready would block on every thread a fix addressed.
- **Risk / reversibility:** Low. A resolved thread can be reopened.
- **Result:** Adopted (Story 3).

### R11. Bound (B-OQ4)

- **Decision:** `watch_pass` max 24, every pass counts, `halt_reported`; nested `fix_commit` max 3, `escalate`.
- **Evidence:** No recorded run exists. `fix_commit` mirrors `implement-story`'s three-iteration review loop.
- **Alternatives:** Count only acting passes. Rejected: waiting passes would then be unbounded.
- **Risk / reversibility:** Low. Recalibrate from the first recorded runs.
- **Result:** Adopted (Story 3).

### R12. No script-held counter (B-OQ5)

- **Decision:** `ship.md` keeps the pass count in `.writ/state/ship/watch-pr-<n>.json`; no script enforces it.
- **Evidence:** The bound limits cost; merge safety rests on `pr-ready.py`, the ledger, the doubt check, and `--match-head-commit`.
- **Alternatives:** A small state script. Rejected for now: a new shipped script for a cost bound.
- **Risk / reversibility:** Low. Revisit if a recorded run overruns its bound.
- **Result:** Adopted (Story 3).

## Decisions made while writing the package

### R13. Story order 1 → 2 → 3 → 4

- **Decision:** Run the stories in sequence. Story 4 also depends on Story 1.
- **Evidence:** Stories 2–4 all edit `commands/ship.md`. Stories 1 and 2 both edit `.writ/docs/agent-cli-contract.md` and regenerate the platform trees.
- **Alternatives:** Run Story 1 beside Story 2. Rejected: a merge conflict in a shared file for little time saved.
- **Risk / reversibility:** Low.
- **Result:** Adopted (`user-stories/README.md`).

### R14. `ship.md` stays above the byte budget after every story

- **Decision:** Each story keeps `commands/ship.md` above 24,960 bytes and re-pins its `KNOWN_OVER_BUDGET` entry exactly. Cuts that would cross the floor wait for Story 4.
- **Evidence:** `test_governor_enforcement.py` asserts the over-budget set equals the registry, and `test_harness_cuts.py` reads `recorded[SHIP]`. A file under the budget breaks both.
- **Alternatives:** Remove the entry if the file drops under budget. Rejected: Story 3 adds it back, so two stories would churn both tests.
- **Risk / reversibility:** Low.
- **Result:** Adopted (technical-spec § Byte Budget).

### R15. One state folder for `/ship`

- **Decision:** All `/ship` state under `.writ/state/ship/`, one writer, temp file then rename. The snapshot stays at the seam sheet's `.writ/state/pr-ready/pr-<n>.json`.
- **Evidence:** Agent CLI contract § State (one writer, atomic writes). `.writ/state/` is gitignored.
- **Alternatives:** Files scattered under `.writ/state/`. Rejected: harder to inspect and clean.
- **Risk / reversibility:** Low.
- **Result:** Adopted (technical-spec § `/ship` State Files).

### R16. Thread decision records never paste comment bodies

- **Decision:** A thread decision record states the request in Writ's words and names the thread id and `path:line`.
- **Evidence:** Comment bodies are untrusted (contract Business Rule 4), and Jev sees decision text (ADR-033 Consequences). Pasting a body would put reviewer-controlled text in the judgment request.
- **Alternatives:** Quote the body as evidence. Rejected for the reason above.
- **Risk / reversibility:** Low.
- **Result:** Adopted (Story 3).

### R17. Reply-only threads do not loop

- **Decision:** A thread replied to without a fix is recorded in `replied` and skipped on later passes; when only such threads remain, the pass is `waiting`.
- **Evidence:** pr-ready keeps reporting an unresolved thread, so without the record every pass would reply again.
- **Alternatives:** Ask after every reply. Rejected: a question the reviewer, not the developer, must answer.
- **Risk / reversibility:** Low. The bound ends a long wait.
- **Result:** Adopted (Story 3).

### R18. A failing `--watch` test run opens a draft and stops

- **Decision:** With `--watch`, a Step 3 failure that survives one fix pass opens the PR as a draft and ends at `asked`.
- **Evidence:** Without a passing run the ledger cannot read VERIFIED, so a watch would spend passes re-running the same failure.
- **Alternatives:** Keep watching. Rejected for the reason above.
- **Risk / reversibility:** Low. Re-running `/ship --watch` after a fix resumes.
- **Result:** Adopted (Story 3).

### R19. The config-persist offer is removed, not gated

- **Decision:** Step 1 prints the `.writ/config.md` lines and writes nothing.
- **Evidence:** Writing the file mid-run leaves an uncommitted change outside the PR. Stakes triage (`_preamble.md`): an answer that does not change the outcome is not a decision.
- **Alternatives:** A `site: choice` record recommending "Not now". Rejected: a logged decision that never does anything.
- **Risk / reversibility:** Low.
- **Result:** Adopted (Story 2).

### R20. No `Amends:` banner

- **Decision:** No `> **Amends:**` line. Story 4 updates `test_harness_cuts.py`'s AC-3.3 pins in place and cites ADR-033 point 5.
- **Evidence:** The contract names no spec it replaces. A banner would make Step 2.4b write a reverse pointer into `.writ/specs/2026-10-20-harness-cuts/spec.md`, outside this spec's folder.
- **Alternatives:** `Amends: 2026-10-20-harness-cuts`. Left to the orchestrator if it wants the pointer.
- **Risk / reversibility:** Low.
- **Result:** Adopted.

### R21. Stories written directly, not by generator spawns

- **Decision:** The four story files were written by the authoring agent, not by four floor-tier `user-story-generator` spawns (Step 2.6).
- **Evidence:** Each story needed the seam sheet, contract A's interface, and the byte-budget rule; the run was restricted to writing inside this folder.
- **Alternatives:** Spawn the generators with the full context. Not taken: four copies of the same context for the same output.
- **Risk / reversibility:** Low. `ac-trace.py check` and `spec-analyze.py check` ran on the result.
- **Result:** Adopted.
