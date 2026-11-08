---
name: implement-phase
description: "Autonomously execute a whole roadmap phase - resolve features to specs, create missing ones, then loop implement-spec per spec in dependency order until the phase exit criteria are met."
problem: "A roadmap phase is delivered one spec at a time by hand, so cross-spec order is guessed, unspecced features are forgotten, and the exit criteria the phase declares go unchecked."
outcome: "Every spec the phase resolves to has been merged into the phase branch or quarantined off it, and the phase carries a terminal status backed by per-criterion evidence."
entry_level: high
exit_criteria:
  - "every spec resolved from the phase reached merged, quarantined, skipped_blocked, or closed_not_implemented in .writ/state/phase-execution-*.json, and failed work exists only on writ/quarantine/<spec-id> branches"
  - "when UAT plans were requested, each merged spec folder contains a populated uat-plan.md generated after that spec was implemented"
  - "each machine-checkable roadmap exit criterion is recorded pass or fail with its evidence, and human-judgment criteria are handed off rather than self-certified"
  - "the phase report ends in exactly one of COMPLETE, IMPLEMENTED pending human validation, or PARTIALLY COMPLETE"
loop:
  unit: "spec"
  max_iterations: 12
  on_exhaustion: halt_reported
  calibrated_against: "Counts distinct specs within one phase; the counter resets at each phase boundary under --all, and a transient retry does not increment it. Set from Writ's own phase runs: the largest had 5 specs, and 12 is 2.4 times that. Recalibrate against this project's .writ/state/phase-execution-*.json records once they exist."
  nested:
    - unit: "spec_attempt"
      max_iterations: 2
      on_exhaustion: quarantine
      calibrated_against: "scripts/phase-state.py cmd_classify (retries only while attempts < 2) and cmd_retry (raises retry_exhausted at >= 2). Evidence: strong - a transcription of code that already enforces this, changing nothing."
---

# Implement Phase Command (implement-phase)
## Overview
Reads a roadmap phase from `.writ/product/roadmap.md`, resolves features to specs in `.writ/specs/` (creating missing ones via a decomposition pre-pass), then loops `/implement-spec` per spec in dependency order until each spec is implemented, adding `/create-uat-plan` per spec only under `--uat`. Maps results to the phase exit criteria and hands off manual UAT. Layer above `/implement-spec`: roadmap → `/implement-phase` → `/implement-spec` → `/implement-story`. Owns cross-spec sequencing; `/implement-spec` owns story batching. The reasons behind the lane, retry, halt, and closure rules are in [`.writ/docs/phase-execution-state-format.md`](../.writ/docs/phase-execution-state-format.md) → Why.

## Required Artifacts
Verify per the preamble's **Artifact Integrity** rule before starting.

- **Required:** `.writ/product/roadmap.md` (the phase source). Missing → HALT + offer `/plan-product`.
- **Optional:** existing specs under `.writ/specs/`, phase execution state (`--resume`).

## Invocation
| Invocation | Behavior |
|---|---|
| `/implement-phase [N]` | Executes Phase N; without N, select a phase from `roadmap.md` interactively |
| `/implement-phase --all` | Executes all remaining phases in roadmap order; passes `--uat` through to each phase |
| `/implement-phase --quick` | Passes `--quick` through to each `/implement-spec` call |
| `/implement-phase --uat` | Generates a UAT plan per merged spec and records `uatRequested: true`; without it no plan is generated and the report names `/create-uat-plan {spec}` per merged spec |
| `/implement-phase --resume` | Resumes from last saved phase execution state |
| `/implement-phase --specs a,b` | No-roadmap fallback: treat the named specs as the phase |
| `/implement-phase --recommend` | Accepted for older scripts and Goal Cards; prints `--recommend is the default now (Doubt Rule)` once and runs as above |

## Initiative and Question Policy
Ask a person only under these conditions:
1. **Missing exit criteria** — the phase (or `--specs` set) defines none and the spec contracts yield none. Ask before executing; never invent-and-self-certify.
2. **Unachievable exit criterion** (unspecced feature skipped, spec failed, criterion unmeasurable) — found mid-run with degrading scope and aborting both defensible: ask which. Found at the end: report it, never ask retroactive permission. Either way the report names the criterion and why, and the status is `PARTIALLY COMPLETE`.
3. **Ambiguous failure blast radius** — a spec failed and a remaining spec has no declared dependency on it but shares surfaces.
4. **Decomposition approval** — the Step 1.2b breakdown, seams, and file ownership.

Conditions 2–4 and the Step 2.3 plan go through the preamble's **Doubt Rule** first; condition 1 always reaches a person. Any other question, including one `/implement-spec` or its sub-pipeline would ask, is answered from artifacts (roadmap → spec contract → technical spec → story files) or the downstream command's default, without surfacing; a lane question no artifact answers returns as `challenge_required` (Step 3.2b). The loop ends at the completion report: it never merges the phase branch, opens PRs, or releases.

## Command Process
### Phase 1: Phase Resolution
#### Step 1.1: Load the Roadmap
Read `.writ/product/roadmap.md`. If it doesn't exist and `--specs` wasn't provided, report the gap and offer the fallback: the user names specs directly, and those specs are the phase (exit criteria then come from spec contracts only). With no phase argument, present the roadmap's phases via AskQuestion, each with its status (how many of its specs are complete).

#### Step 1.2: Resolve Features to Specs
Map the phase's features to spec folders in `.writ/specs/`: by the spec reference the roadmap names (preferred), otherwise by title similarity. A feature is **Specced** (a spec folder exists; it enters the loop) or **Unspecced** (the phase cannot be fully completed). Unspecced features are asked about once, upfront. **Decompose now** is the default when two or more are unspecced; a single unspecced feature routes to one `/create-spec`.

```
AskQuestion: Phase N includes features without specs: [list].
  - Decompose now — propose a spec breakdown and create the specs (Step 1.2b), then continue
  - Proceed with specced features only (phase will end "partially complete")
  - Stop so I can run /create-spec myself first
```

#### Step 1.2b: Decomposition Pre-Pass
Runs only on **Decompose now**. Draw boundaries against the current codebase: independently shippable, testable specs; exactly one owning spec per shared file; named seams. Produce one proposal:

```
## Decomposition Proposal: Phase N — [name]
Proposed specs (from [M] unspecced features):
  1. {slug-a}  — [deliverable]        deps: []          owns: [files]
  2. {slug-b}  — [deliverable]        deps: [slug-a]    owns: [files]
Seams:
  - {slug-a} ⇄ {slug-b}: [shared contract that must hold]
Rationale: [why these boundaries — coherence, independent testability, ownership]
```

Run the Doubt Rule on the proposal (`site: direction`; evidence: the files each spec owns, the dependency edges, the seams). A passing check adopts and records it; otherwise AskQuestion: create these specs / edit the breakdown / stop. On approval, run `/create-spec` per proposed spec in dependency order, seeded with its deliverable, files in scope, `dependencies:`, and ownership. Each spec is still contract-locked; `/create-spec`'s Doubt Rule decides whether the lock reaches a person, and its decisions go in that spec's `recommendation-log.md`. Then return to Step 1.2: the new specs are **Specced**.

A spec that should never be built (premise retired by evidence, subsumed by another spec, scope moved) is closed, not left `pending`: `phase-state.py close-spec --spec {id} --reason "{why}"`. The reason is mandatory and printed in the report; closure is terminal and its dependents become `skipped_blocked`.

> **`--all` boundary:** unspecced features go through the same Doubt Rule as an interactive run; a question that cannot reach a person (no question tool) ends that phase on the "partially complete" path.

#### Step 1.3: Inventory Prior Progress
For each specced feature, determine its actual state so `--resume` and re-runs skip finished work, in this order:
1. **Phase state** in `.writ/state/phase-execution-*.json` (`--resume`): `integrated`, `quarantined`, `skipped_blocked`, and `closed_not_implemented` are terminal; skip the spec.
2. **Story statuses** in `user-stories/story-*.md`: every story `Completed ✅` → skip implementation. Any incomplete story → not skipped.
3. **Under `uatRequested`**, an integrated spec with no populated `uat-plan.md` still gets `/create-uat-plan` (Step 3.2 item 6).

`uat-plan.md` never decides a skip. **`--resume --uat` on a run started without `--uat`** sets `uatRequested: true` in phase state from then on (temp file + rename), so item 3 covers the integrated specs that lack a plan. Skipped specs are reported as such.

### Phase 2: Sequencing & The One Confirmation
#### Step 2.1: Validate and Order the Specs
Order comes from each spec's `> **Dependencies:** [...]` header, not prose:
1. **Valid explicit `Dependencies` graph** — parse each header (no header is `[]`) and order the DAG topologically. This graph is binding.
2. **Roadmap order** — breaks ties among independent specs, so the plan is reproducible.
3. **Shared-surface inference remains advisory** — two unrelated specs touching the same files get a warning and run in roadmap order; inference never reorders a valid graph.

Run `scripts/spec-deps.py validate --specs-dir .writ/specs --roadmap-order <phase spec order>`. An archived dependency is satisfied: listed in `archived_dependencies`, not ordered. **Invalid metadata is blocking:** on a `blocker`, stop before the confirmation gate and show its exact diagnostic; never guess an order. Independent specs still run sequentially.

#### Step 2.2: Verify Exit Criteria Exist
Read the phase's **Exit Criteria** and **Success Metrics** from the roadmap and classify each as **machine-checkable** (tests pass, files load, no external dependencies, typecheck clean) or **human-judgment** ("feels complete for daily use", UAT scenario passes). No exit criteria → Question Policy condition 1.

#### Step 2.3: Present the Phase Execution Plan (single confirmation gate)
```
## Phase Execution Plan: Phase 1 — [name]
Specs: 2 total (0 complete, 2 remaining)
  1. 2026-07-07-timestamped-notes-stage-history  (2 stories) — must run first (cross-spec note)
  2. 2026-07-07-drag-and-drop-across-states       (1 story)  — after #1 (shared renderCard)
Per spec: /implement-spec
UAT: not requested (pass --uat to generate plans per spec)
Exit criteria (from roadmap):
  ✓ machine-checkable: old JSON files load cleanly; no external deps introduced
  ⚑ human-judgment: UAT scenarios pass — handed off at the end
Pre-flight flags: [any /implement-spec sizing concerns, surfaced but non-blocking]
```

Under `--uat` the two lines read `Per spec: /implement-spec → /create-uat-plan` and `UAT: requested`. Run the Doubt Rule on the plan (`site: plan`; evidence: the validated dependency graph and the roadmap order). A passing check prints the plan and proceeds; otherwise AskQuestion: execute / edit spec list / abort. Everything after this runs autonomously except the Question Policy conditions.

### Phase 3: The Loop
#### Step 3.1: Initialize Phase State
Run `scripts/phase-state.py init` (with `--uat` when the run has it, which records `uatRequested`) to create `.writ/state/phase-execution-{timestamp}.json` (schema `phase-execution-v2`): the phase, phase branch, topologically ordered spec list, and per-spec records. State plus git is the **resume boundary**; every transition writes it atomically (temp file + rename). Contract: [`.writ/docs/phase-execution-state-format.md`](../.writ/docs/phase-execution-state-format.md). Name the phase branch `phase/{N}-{slug}` (e.g. `phase/8-memory-interop`), never under `writ/phase/`.

#### Step 3.2: Per-Spec Iteration (Fresh Isolated Lanes)
The orchestrator owns lane creation, result validation, merge, and UAT handoff. Each spec runs in a **fresh subagent** inside its own isolated git lane. For each spec in order:
1. **Create the lane before any work** — `scripts/phase-state.py create-lane` verifies the phase branch is clean, then creates branch `writ/phase/{phase-id}/{spec-id}` and a dedicated worktree from the phase-branch head. A dirty base or a branch collision **stops before launch** (`dirty_base` / `lane_collision`).
2. **Spawn a fresh subagent** with [`_lane-brief.md`](_lane-brief.md) as its prompt, the placeholders filled from artifact paths: spec path, absolute phase-state path, lane branch, worktree, mode (pass through `--quick` if set), `{result_path}` (the lane's `resultPath` from `create-lane`; a state file without one uses `<repo>/.writ/state/lane-result-<phase>-<spec>.json`), and inherited answer sources. Change nothing else in the brief; a lane problem is fixed in the template. **No prior conversational transcript is forwarded.** The subagent runs `/implement-spec {spec}` inside the lane worktree, writes its `phase-spec-result-v1` to `{result_path}`, and replies with the path. Delete any file at `{result_path}` before spawning; a retry reuses the path.

   **Read the result from the file:** `scripts/phase-state.py validate-result --input {result_path}`. On `result_missing` or `invalid_result`, resume the same lane agent once to write the file; do not re-run the lane. If the file is still missing or does not parse, write a `failed` result with `failure.classification: transient` to `{result_path}` and `classify` it (Step 3.3).
3. **Supervise the result** — once the file validates and before anything acts on it, spawn `supervisor-agent` (fresh context, read-only) with `report` set to the contents of `{result_path}` (the lane's whole report, verbatim), plus the spec path, the lane branch, and its base commit. It re-derives each claim from git, the spec's files, and Writ's checkers, and returns `SUPERVISOR_RESULT: ACCEPT | RERUN | ESCALATE` with a claims table. `ACCEPT` → step 4. `RERUN` → a `transient` failure (Step 3.3; the `spec_attempt` cap applies) with the claims table as evidence. `ESCALATE` → a `terminal` failure with the same evidence. A missing result line is a mid-task stop: resume the supervisor once and ask for its result.
4. **Merge only verified success** — `scripts/phase-state.py integrate --result {result_path}` validates again: **only a verified** `phase-spec-result-v1` with `status: succeeded`, a real commit, and non-empty verification evidence merges (`--no-ff`) into the phase branch; the worktree is then removed and the merge commit recorded.
5. **Preserve anything else** — a missing, malformed, non-successful, or unverifiable result never touches the phase branch; its lane is preserved for Step 3.3.
6. **On a merged success, when `uatRequested` is true, run `/create-uat-plan {spec}`** — generated after implementation so it reflects what was built. When it is false, generate nothing. Update phase state and continue.

**Iteration bound:** at most 12 distinct specs per phase (`loop.max_iterations`; a Step 3.3 retry is the same iteration; `--all` resets the count per phase). On exhaustion quarantine nothing: unstarted specs stay `pending`, run `scripts/phase-state.py record-halt --unit spec --bound 12 --reached <n> --last-integrated <spec-id>` (writes `haltReported`, never `terminalStatus`), and report the bound, the count, the last integrated spec, the state path, and `/implement-phase --resume`.

**Lane briefs carry context, never new scope.** Work that no spec's acceptance criteria cover goes through `/edit-spec` before the lane opens, or is recorded as a gap; never into a brief.

#### Step 3.2b: User Challenge Handling
`/implement-phase` is the **sole presenter** of User Challenges (see [`_preamble.md`](_preamble.md) → User Challenge); **ordinary failures use their normal** path (Step 3.3), and decisions answered by artifacts come from those artifacts, neither with User Challenge framing. When a nested `phase-spec-result-v1` returns `status: challenge_required`, or an audited evidence-backed selection:
1. **Validate** with `scripts/phase-state.py validate-challenge`. A malformed challenge (missing any of the four parts, bad trigger, or no options) is a **contract error** routed to Step 3.3, never rendered as a User Challenge.
2. **Present** a valid unresolved challenge in one `AskQuestion` showing all four parts (*What the roadmap/spec said*, *What Writ recommends*, *What context may be missing*, *Cost if the recommendation is wrong*) and pause before any scope-changing action. An audited low-risk reversible selection proceeds automatically.
3. **Persist** the challenge, selected option, and decision timestamp via `record-challenge` / `resolve-challenge`, so resume never re-asks a decided question.

#### Step 3.3: Failure Handling
Failed work never touches the phase branch. Each event maps to one `scripts/phase-state.py` subcommand:

| Event | Subcommand | Effect |
|---|---|---|
| A non-successful `phase-spec-result-v1` (or supervisor `RERUN` / `ESCALATE`) | `classify` | Decides retry or quarantine; Writ permits exactly **one transient retry** |
| `transient` on the first attempt | `retry` | Same isolated lane, fresh subagent, no new confirmation |
| `terminal`, or `transient` after the retry | `quarantine` | Removes the worktree, keeps the lane as `writ/quarantine/{spec-id}` (deterministic suffix on collision, mapping recorded), confirms the phase branch is clean, records failure evidence, retry count, branch, and a recovery command. Direct and transitive dependents become `skipped_blocked` with `blockedBy`; independent specs continue |
| Decision that a spec should never be built | `close-spec --reason "{why}"` | No `classify`, retry, quarantine, or recovery command. Frees the worktree, keeps the lane branch under `writ/phase/…`; dependents become `skipped_blocked` |
| `--resume` | `reconcile`, first | Checks phase, lane, worktree, and quarantine branches against state; continue only when they agree; on a mismatch, reports it with a recovery command and **does not guess or mutate git** |

An unclear dependency between a failed spec and a remaining one is Question Policy condition 3. `blockedBy` means the upstream ended without delivering, by quarantine or closure; say which when reporting a blocked spec (`progress` supplies the cause).

#### Step 3.4: `--all` Mode
After a phase completes, advance to the next roadmap phase **only if** the completed phase's machine-checkable exit criteria all pass. Phases marked "Tentative" or "Not Committed" are never auto-entered; stop and report instead. Human-judgment criteria don't block advancement in `--all` mode; they accumulate into the final handoff.

### Phase 4: Exit Criteria Verification & Handoff
#### Step 4.1: Verify Machine-Checkable Criteria
Run each machine-checkable exit criterion from the roadmap (plus `/implement-spec`'s own integration verification, which already ran per spec). Record pass/fail per criterion with evidence, not assertion, persisting each as it is produced with `scripts/phase-state.py record-exit-criterion --id <criterion-id> --source roadmap --class machine|human --verdict pass|fail|unachievable|handed_off --evidence "<evidence>"`, so `exitCriteria[]` in phase state carries the same facts the report narrates.

#### Step 4.1b: Evidence-Bound Knowledge Writeback
Collect candidate lessons from the phase report and per-spec drift logs and run `scripts/phase-state.py knowledge-writeback`. It applies the **evidence-bound** D6 gates (generalizes beyond one spec, cites an artifact or repeated drift, not duplicated in `.writ/knowledge/`, below ADR blast radius), writes qualifying lessons to `.writ/knowledge/lessons/`, and records each in `knowledgeWritten` so resume never double-writes. With no qualifying candidate it is a silent no-op; rejected candidates get a terse reason in the report. Architectural decisions belong in ADRs, never in an auto-written lesson.

#### Step 4.1c: Phase Progress and Production Health
Before writing the report, capture the phase's **progress**, **production health**, and **exit-criteria verdict** from local evidence only, never a probe of production or the network, and carry all three into the report (the same reducers back `/status`, so an interrupted phase reports identically on resume):

```bash
python3 scripts/phase-state.py progress --state .writ/state/phase-execution-{timestamp}.json
python3 scripts/phase-state.py health   --state .writ/state/phase-execution-{timestamp}.json --repo . \
  [--eval <eval-summary>] [--drift <spec-drift-log> ...]
python3 scripts/exit-criteria.py check  --command implement-phase --state .writ/state/phase-execution-{timestamp}.json --repo .
```

- `progress` reports the current spec/lane, per-status counts, quarantine branches, each closed spec with its reason, and each blocked spec with its cause.
- `health`: pass `--drift` once per merged spec whose `drift-log.md` exists and `--eval` only when this phase ran `eval.sh`; never `--verification`, which no step produces. An omitted source is `not_requested`. The result is categorical (`Healthy` / `Warning` / `Attention`), never a score: a passed source that is missing or stale is `Warning`, and `Attention` needs an affirmative current failure (eval findings, failing verification, unresolved material drift, or a `phase-state`/git mismatch).
- `exit-criteria.py check` re-derives `implement-phase.c1`–`c4` from the state file, read-only (`met`/`unmet`/`impossible` overall plus each criterion's verdict and evidence). Step 4.3 defers to it, not to the run's self-assessment. It is not a harness `/goal` Stop hook.

#### Step 4.2: The Honest Completion Report
```
## Phase 1 Report: [name]

| Spec | Implemented | UAT Plan | Notes |
|------|-------------|----------|-------|
| timestamped-notes-stage-history | ✅ 2/2 stories | not requested | — |
| drag-and-drop-across-states     | ✅ 1/1 stories | not requested | — |

Closed by decision:
  ✖ disclosure-release — pilot measured ~1,017 B irreducible overhead per extracted skill

Exit criteria:
  ✅ Old JSON files load cleanly — verified (integration check)
  ⚑ UAT scenarios pass — handed off. UAT: not requested. To validate, run:
      /create-uat-plan 2026-07-07-timestamped-notes-stage-history
      /create-uat-plan 2026-07-07-drag-and-drop-across-states

Checker verdict: met
  ✅ implement-phase.c1 — met — 3/3 specs terminal; 0 quarantine branches off phase
  ✅ implement-phase.c2 — met — UAT not requested
  ✅ implement-phase.c3 — met — 2 roadmap criteria recorded in exitCriteria[]
  ⚑ implement-phase.c4 — unknown — declared unobservable: report is transcript-only

Phase status: IMPLEMENTED — pending human validation
Product docs may lag what shipped — run /verify-spec --product.
```

The `Product docs may lag` line appears only when `.writ/product/` exists; omit it otherwise. Under `--uat`, the UAT Plan column shows each plan's scenario count (`✅ 14 scenarios`) and the handoff reads `⚑ UAT scenarios pass — 29 scenarios awaiting manual execution`, with no `/create-uat-plan` lines.

**The command never declares a phase "complete" when human-judgment criteria remain.** The status is then `IMPLEMENTED — pending human validation`, with the UAT plans (under `--uat`) or the `/create-uat-plan {spec}` lines as the handoff. If every exit criterion is machine-checkable and passing, the status may be `COMPLETE`. **A `Closed by decision` section is mandatory whenever any spec is `closed_not_implemented`**: one line per spec with its `closure` reason, from `progress`'s `closed` map. A phase whose specs are all `integrated` or `closed_not_implemented` may report `COMPLETE` only with this section.

#### Step 4.3: Terminal Status
**Checker verdict governs (AC4).** Branch on Step 4.1c's verdict before persisting anything. `met` and `unmet` persist with `scripts/phase-state.py set-terminal-status --status COMPLETE|IMPLEMENTED_PENDING_HUMAN_VALIDATION|PARTIALLY_COMPLETE`, the same write that clears any stale `haltReported`:
- **`impossible`** — name the fired trigger from the checker's `reason` in the Checker verdict line and do not call `set-terminal-status`.
- **`unmet`** — the status cannot be `COMPLETE`; state the disagreement (e.g. "run assessment: COMPLETE; checker: unmet on implement-phase.c2; reporting per checker") and persist whichever of `IMPLEMENTED_PENDING_HUMAN_VALIDATION` / `PARTIALLY_COMPLETE` the unmet criterion supports.
- **`met`** — the run's own terminal-status determination stands.

## Integration with Writ
`/plan-product` writes the roadmap. `/create-spec` creates the specs (Step 1.2b or by hand). `/implement-spec` runs once per lane and has no confirmation gate: invoking it executes. `/create-uat-plan` runs per merged spec under `--uat`; otherwise the report names it. `/assess-spec` is the remedy for a pre-flight flag in the plan. `/status` reads the state file. `/ship` follows the report, one PR per phase or per spec.

## Completion
This command succeeds when every specced feature in the phase is implemented (or reported failed/skipped with reasons); under `--uat` every implemented spec has a `uat-plan.md` generated after it was built, and without it the report names `/create-uat-plan {spec}` per merged spec; machine-checkable exit criteria are verified with evidence and human-judgment criteria are handed off, not self-certified; and the report ends in a terminal status: `COMPLETE`, `IMPLEMENTED — pending human validation`, or `PARTIALLY COMPLETE`.

**Suggested next step:** Run the `/create-uat-plan` lines the report names, or under `--uat` execute the human scenarios the plans hand off; then `/ship`.

**Terminal constraint:** After the phase report, stop. Do not offer to execute UAT scenarios on the human's behalf, auto-advance into uncommitted roadmap phases, or open PRs unprompted.

## References
- Standing instructions: [`commands/_preamble.md`](_preamble.md)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)
