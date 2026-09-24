---
name: implement-phase-lean
description: "Lean variant of /implement-phase for WRIT_HARNESS_LEAN=1 baseline runs. Autonomously execute a whole roadmap phase - resolve features to specs, create missing ones, then loop implement-spec per spec in dependency order until the phase exit criteria are met."
problem: "A roadmap phase is delivered one spec at a time by hand, so cross-spec order is guessed, unspecced features are forgotten, and the exit criteria the phase declares go unchecked."
outcome: "Every spec the phase resolves to has been merged into the phase branch or quarantined off it, and the phase carries a terminal status backed by per-criterion evidence."
entry_level: high
exit_criteria:
  - "every spec resolved from the phase reached merged, quarantined, skipped_blocked, or closed_not_implemented in .writ/state/phase-execution-*.json, and failed work exists only on writ/quarantine/<spec-id> branches"
  - "each merged spec folder contains a populated uat-plan.md generated after that spec was implemented"
  - "each machine-checkable roadmap exit criterion is recorded pass or fail with its evidence, and human-judgment criteria are handed off rather than self-certified"
  - "the phase report ends in exactly one of COMPLETE, IMPLEMENTED pending human validation, or PARTIALLY COMPLETE"
loop:
  unit: "spec"
  max_iterations: 12
  on_exhaustion: halt_reported
  calibrated_against: "Counts distinct specs within one phase - the counter resets at each phase boundary under --all, and a transient retry does not increment it. Observed runs: .writ/state/phase-execution-20260719-121255.json (Phase 9, specOrder length 3, every spec attempts=1, zero retries, zero quarantines); .writ/state/phase-execution-20260811-2030.json (Phase 10, specOrder length 5 - the largest phase with a surviving state file); roadmap Phase 7, 4 specs, roadmap-attested with no surviving state file. Largest observed = 5, bound is 2.4x. Evidence: thin - three runs, one of them without a state file, and .writ/state/ is gitignored so the sample can only shrink."
  nested:
    - unit: "spec_attempt"
      max_iterations: 2
      on_exhaustion: quarantine
      calibrated_against: "scripts/phase-state.py cmd_classify (retries only while attempts < 2) and cmd_retry (raises retry_exhausted at >= 2). Evidence: strong - a transcription of code that already enforces this, changing nothing."
---

# Implement Phase Command (implement-phase, lean)

## Overview

Reads a roadmap phase from `.writ/product/roadmap.md`, resolves features to specs in `.writ/specs/` (creating missing ones via a decomposition pre-pass), then loops `/implement-spec` → `/create-uat-plan` per spec in dependency order. Maps results to the phase exit criteria and hands off manual UAT. Layering: roadmap → `/implement-phase` (cross-spec sequencing) → `/implement-spec` (story batching) → `/implement-story`.

**Question policy:** ask only when artifacts contain no answer (see § Question Policy).

## Required Artifacts

Verify per the preamble's **Artifact Integrity** rule before starting.

- **Required:** `.writ/product/roadmap.md` (the phase source). Missing → HALT + offer `/plan-product`.
- **Optional:** existing specs under `.writ/specs/`, phase execution state (`--resume`).

## Invocation

| Invocation | Behavior |
|---|---|
| `/implement-phase` | Interactive — select a phase from `roadmap.md` |
| `/implement-phase 1` | Executes Phase 1 |
| `/implement-phase --all` | Executes all remaining phases in roadmap order |
| `/implement-phase --quick` | Passes `--quick` through to each `/implement-spec` call |
| `/implement-phase --resume` | Resumes from last saved phase execution state |
| `/implement-phase --specs a,b` | No-roadmap fallback: treat the named specs as the phase |
| `/implement-phase --recommend` | End-to-end autonomous loop: auto-author missing specs (via `/create-spec --recommend`) and run `/implement-spec` per spec, without routine confirmations |

## Recommended Mode (`--recommend`)

`/implement-phase --recommend` runs the phase as a complete end-to-end loop with no routine confirmations. It is the only command that autonomously chains spec authoring into implementation (see [ADR-013](../.writ/decision-records/adr-013-recommended-autonomous-delivery.md)).

- **Auto-author missing specs.** When unspecced features exist, the decomposition pre-pass (Step 1.2b) runs without its approval gate, and each proposed spec is created with `/create-spec --recommend` (autonomous, evidence-backed contract authoring) instead of the collaborative `/create-spec`. Record each authoring decision in that spec's `recommendation-log.md`.
- **Auto-accept the execution plan.** The single Step 2.3 execution-plan confirmation is auto-accepted; the loop then runs exactly as in normal mode (isolated lanes → `/implement-spec` per spec → `/create-uat-plan`).
- **Terminal scope is unchanged.** The loop still ends at the completion report (Phase 4) and hands off manual UAT. It never ships, opens PRs, or releases.
- **Non-routine pauses are retained** — the Question Policy conditions that are not routine confirmations still stop the loop: missing exit criteria that cannot be derived (never invent-and-self-certify, Step 2.2), an exit criterion that becomes unachievable mid-run (Step 4.3), and an ambiguous failure blast radius (Step 3.3).

Validate the `--recommend` invocation matrix before any mutation (spec creation, lane creation, or state write): the forms below are the whole matrix, and an unsupported combination prints the supported forms and stops.

`--recommend` composes with `--all` and `--specs`. It is incompatible with `--quick`: full story, review, testing, and documentation gates are mandatory when authoring and implementation run autonomously.

## Command Process

### Phase 1: Phase Resolution

#### Step 1.1: Load the Roadmap

Read `.writ/product/roadmap.md`. If it doesn't exist and `--specs` wasn't provided, report the gap and offer the fallback: the user names specs directly, and those specs are the phase (exit criteria then come from spec contracts only).

If no phase argument is given, present the roadmap's phases via AskQuestion with each phase's status (how many of its specs are complete).

#### Step 1.2: Resolve Features to Specs

Map the phase's features to spec folders — by explicit spec reference in the roadmap when present, otherwise by title similarity. Classify each as **Specced** (in the loop) or **Unspecced** (the phase cannot be fully completed by this command).

**Unspecced features are ask-worthy.** Ask once, upfront, not mid-loop:

```
AskQuestion: Phase N includes features without specs: [list].
  - Decompose now — propose a spec breakdown and create the specs (Step 1.2b), then continue
  - Proceed with specced features only (phase will end "partially complete")
  - Stop so I can run /create-spec myself first
```

**Decompose now** is the default when two or more features are unspecced. A single unspecced feature routes to one `/create-spec`.

#### Step 1.2b: Decomposition Pre-Pass (unspecced features → the right set of specs)

Runs only when the user chose **Decompose now**. Draw boundaries against the current codebase:

1. **Analyze** the files, commands, and scripts each feature touches, and where they overlap.
2. **Propose specs** — independently shippable, independently testable; one spec per coherent deliverable.
3. **Draw the dependency graph** — the `> **Dependencies:** [...]` edges each spec will declare, so Step 2.1 can sequence them.
4. **Assign file ownership** — exactly one owning spec per shared file (single-writer-per-file keeps Step 3.2 lanes from colliding on merge).
5. **Name the seams** — the contracts between specs (shared schema, script signature, command flag) that must hold.

```
## Decomposition Proposal: Phase N — [name]

Proposed specs (from [M] unspecced features):
  1. {slug-a}  — [deliverable]        deps: []          owns: [files]
  2. {slug-b}  — [deliverable]        deps: [slug-a]    owns: [files]

Seams:
  - {slug-a} ⇄ {slug-b}: [shared contract that must hold]

Rationale: [why these boundaries]
```

Confirm with AskQuestion: create these specs / edit the breakdown / stop. This is Question Policy condition 4, distinct from and earlier than the Step 2.3 execution gate. **In `--recommend` mode this confirmation is auto-accepted** and recorded.

**On approval, create the specs** in dependency order with `/create-spec`, seeded with each spec's deliverable, files-in-scope, `dependencies:`, and ownership constraints. Each spec is still contract-locked (ADR-001); only implementation (Phase 3) runs autonomously. **In `--recommend` mode, run `/create-spec --recommend` instead**, with the same seed.

**Closing a spec instead of building it.** When evidence retires a resolved spec (premise disproved, subsumed, scope moved), record `phase-state.py close-spec --spec {id} --reason "{why}"` rather than leaving it `pending`. The reason is mandatory and printed in the completion report. Closure is **terminal** (no lane, no retry, no quarantine) and its declared dependents become `skipped_blocked`.

**After the specs exist, re-resolve** (Step 1.2); the new specs enter the normal flow.

> **`--all` boundary:** the pre-pass is never auto-entered in `--all` mode; creating specs requires human agreement, so unspecced features under `--all` take the "partially complete" path. **`--recommend` is the explicit exception:** with or without `--all`, it auto-enters the pre-pass and authors specs via `/create-spec --recommend`.

#### Step 1.3: Inventory Prior Progress

For each specced feature, determine its actual state so `--resume` and re-runs skip finished work:

1. **Story statuses** in `user-stories/story-*.md`
2. **Existing `uat-plan.md`** — a populated plan (not a stub) means implemented and validated; skip both unless stories changed after the plan's generation date
3. **Prior execution state** in `.writ/state/phase-execution-*.json`

Fully complete specs with a current UAT plan are skipped and reported as such.

#### Step 1.4: Emit Goal files when origin is a Goal Card

When a spec `Origin:` or issue `spec_ref` resolves to a Goal Card, emit paste-ready `/goal` files. Do not register a `/goal` hook, AskQuestion on emit notes, or change `/implement-story` spawn.

1. No path → `add_note` `unverifiable` and continue. Do not invent a card.
2. Missing `scripts/goal-emit.py` → `add_finding` and continue.
3. Else run:

```bash
python3 scripts/goal-emit.py emit --card <path>
```

4. On `pass`, print the invoke line after the helper summary.
5. `pass` / `fail` / `unverifiable` → `add_note`; helper exit 2 → `add_finding`. Notes never fail the phase.

### Phase 2: Sequencing & The One Confirmation

#### Step 2.1: Validate and Order the Specs

Order comes from the **authoritative `> **Dependencies:** [...]` headers**, not prose:

1. **Valid explicit `Dependencies` graph** — parse each header (no header = `[]`), then **topological**ly order the DAG. Binding.
2. **Roadmap order** — tie-break among independent specs, so the plan is reproducible.
3. **Shared-surface inference is advisory** — unrelated specs touching the same files: *warn* and run them sequentially by roadmap order. Inference never reorders a valid explicit graph.

Executable reference: `scripts/spec-deps.py validate --specs-dir .writ/specs --roadmap-order <phase spec order>`.

**Invalid explicit metadata is blocking.** A malformed header, missing reference, self-reference, duplicate entry, or cycle → **stop before the confirmation gate** and present the affected spec plus the exact graph diagnostic. Do not guess an order around invalid metadata.

Independent specs still run sequentially.

#### Step 2.2: Verify Exit Criteria Exist

Read the phase's **Exit Criteria** and **Success Metrics** from the roadmap. Classify each as **machine-checkable** (tests pass, files load, no external dependencies, typecheck clean) or **human-judgment** ("feels complete for daily use", UAT scenario passes).

**If the phase has no exit criteria**, ask the user to state them before executing; never invent-and-self-certify.

#### Step 2.3: Present the Phase Execution Plan (single confirmation gate)

```
## Phase Execution Plan: Phase 1 — [name]

Specs: 3 total (0 complete, 3 remaining)

  1. {spec-a}  (2 stories) — must run first (cross-spec note)
  2. {spec-b}  (1 story)   — after #1 (shared surface)

Per spec: /implement-spec → /create-uat-plan

Exit criteria (from roadmap):
  ✓ machine-checkable: [...]
  ⚑ human-judgment: [...] — handed off at the end

Pre-flight flags: [any /implement-spec sizing concerns, surfaced but non-blocking]
```

Confirm with AskQuestion: execute / edit spec list / abort. This is the last routine question; everything after runs autonomously except the failure and exit-criteria conditions below. **In `--recommend` mode this confirmation is auto-accepted.**

### Phase 3: The Loop

#### Step 3.1: Initialize Phase State

Initialize `.writ/state/phase-execution-{timestamp}.json` (schema `phase-execution-v2`) via `scripts/phase-state.py init`, recording the phase, phase branch, topologically ordered spec list, and per-spec record.

> **The phase branch must not sit under `writ/phase/{phase-id}`:** lanes are `writ/phase/{phase-id}/{spec-id}`, and git cannot hold a ref as both file and directory, so every `create-lane` would fail. Name it `phase/{N}-{slug}` (e.g. `phase/10-component-contract`). This file is the **resume boundary**: state plus git reality is the only source of truth on `--resume`. Update it after every transition with atomic writes (temp file + rename). Contract: [`.writ/docs/phase-execution-state-format.md`](../.writ/docs/phase-execution-state-format.md).

#### Step 3.2: Per-Spec Iteration (Fresh Isolated Lanes)

The orchestrator owns lane creation, result validation, merge, and UAT handoff. For each spec in order:

1. **Create the lane before any work** — `scripts/phase-state.py create-lane` verifies the phase branch is clean, then creates branch `writ/phase/{phase-id}/{spec-id}` and a dedicated worktree from the phase-branch head. A dirty base or branch collision **stops before launch** (`dirty_base` / `lane_collision`).
2. **Spawn a fresh subagent** seeded only with artifact paths (spec path, phase-state path, lane branch/worktree, mode, inherited answer sources) and the expected `phase-spec-result-v1` schema. **No prior conversational transcript is forwarded.** The subagent runs `/implement-spec {spec}` inside the lane worktree and returns the structured result. Pass through `--quick` if set.

   **A truncated or dropped result is not a failure; re-request it.** Before classifying any result, confirm it parses as `phase-spec-result-v1`; if it does not, resume the same agent and ask it to restate its report verbatim rather than re-running the lane.
3. **Validate the result and merge only verified success** — `scripts/phase-state.py validate-result` gates the merge: **only a verified** `phase-spec-result-v1` with `status: succeeded`, a real commit, and non-empty verification evidence merges (`--no-ff`) into the phase branch (`integrate`); then the worktree is removed and the merge commit recorded.
4. **Preserve anything else** — a missing, malformed, non-successful, or unverifiable result never touches the phase branch; its lane is preserved for Step 3.3.
5. **On a merged success, run `/create-uat-plan {spec}`** — generated after implementation so it reflects what was built. Update phase state and continue.

**Iteration bound:** `loop.max_iterations` (12) **distinct specs per phase**; the counter resets at each phase boundary in `--all` mode, and a Step 3.3 retry is the same iteration (bounded separately by `spec_attempt`). On exhaustion, `loop.on_exhaustion: halt_reported` applies: **do not quarantine anything** — nothing has failed. Unstarted specs stay `pending` and the phase stays `status: executing`; report the unit (`spec`), the bound, the count reached, the last integrated spec, the `phase-execution-*.json` path, and the resume command `/implement-phase --resume`. Persist with `scripts/phase-state.py record-halt --unit spec --bound 12 --reached <n> --last-integrated <spec-id>`, which writes `haltReported` and never sets `terminalStatus`.

**Inherited-answer rule:** any question `/implement-spec` or its sub-pipeline would ask that the spec contract, story files, technical spec, or roadmap answers is answered from those artifacts without surfacing to the user.

**Lane briefs carry context, never new scope.** Work no spec's acceptance criteria cover is not added to a brief: amend the spec (`/edit-spec`) before opening the lane, or record the gap and leave it.

#### Step 3.2b: User Challenge Handling

`/implement-phase` is the **sole presenter** of User Challenges (preamble → User Challenge). When a nested `phase-spec-result-v1` returns `status: challenge_required`, or an audited evidence-backed selection:

1. **Validate** with `scripts/phase-state.py validate-challenge`. A malformed challenge (missing any of the four parts, bad trigger, or no options) is a **contract error** routed to normal failure handling — never rendered as a User Challenge.
2. **Present** a valid unresolved challenge through one explicit `AskQuestion` showing all four parts (*What the roadmap/spec said*, *What Writ recommends*, *What context may be missing*, *Cost if the recommendation is wrong*) and pause before any scope-changing action. An audited low-risk reversible selection proceeds automatically.
3. **Persist** the challenge, selected option, and decision timestamp via `record-challenge` / `resolve-challenge` so resume never re-asks a decided question.

Ordinary failures use their normal failure path (Step 3.3); decisions answered by artifacts are resolved from those artifacts. Neither uses User Challenge framing.

#### Step 3.3: Failure Handling

A non-successful `phase-spec-result-v1` is classified and disposed of via `scripts/phase-state.py`; failed work never touches the phase branch:

1. **Bounded retry.** `classify` decides retry vs quarantine. Exactly **one transient retry**: a `transient` first-attempt failure is retried once in the *same* lane with a fresh subagent (`retry`), with no new routine confirmation. A `terminal` failure, or a transient failure after the retry, is terminal.
2. **Quarantine on terminal failure.** `quarantine` removes the lane worktree, preserves the lane as `writ/quarantine/{spec-id}` (deterministic suffix on collision, mapping recorded), guarantees the phase branch is clean of it, and records failure evidence, retry count, quarantine branch, and a recovery command.
3. **Block dependents, continue independents.** Direct and transitive dependents become `skipped_blocked` with `blockedBy` evidence; **independent specs continue**.
4. **Ask only if ambiguous:** if the relationship between the failed spec and a remaining spec is unclear (no explicit declaration, but shared surfaces), ask whether to proceed — Question Policy condition 3.

**Mid-run closure is not failure handling.** A spec that should never be built uses `close-spec --reason "{why}"`: no `classify`, retry, `quarantine`, or recovery command. It frees the lane worktree but **keeps the lane branch** under its `writ/phase/…` name. Dependents still become `skipped_blocked`; when reporting a blocked spec, say whether the upstream was quarantined or closed (`progress` supplies the cause).

On `--resume`, run `reconcile` first: it checks phase, lane, worktree, and quarantine branches against recorded state and continues only if they agree. On any discrepancy it reports the named mismatch and a recovery command and **does not guess or mutate git**.

#### Step 3.4: `--all` Mode

Advance to the next roadmap phase **only if** the completed phase's machine-checkable exit criteria all pass. Phases marked "Tentative" or "Not Committed" are never auto-entered; stop and report. Human-judgment criteria don't block advancement but accumulate into the final handoff.

### Phase 4: Exit Criteria Verification & Handoff

#### Step 4.1: Verify Machine-Checkable Criteria

Run each machine-checkable exit criterion from the roadmap (plus `/implement-spec`'s per-spec integration verification). Record pass/fail per criterion with evidence, persisting each with `scripts/phase-state.py record-exit-criterion --id <criterion-id> --source roadmap --class machine|human --verdict pass|fail|unachievable|handed_off --evidence "<evidence>"`.

#### Step 4.1b: Evidence-Bound Knowledge Writeback

Collect candidate lessons from the phase report and per-spec drift logs and run `scripts/phase-state.py knowledge-writeback`. It applies the **evidence-bound** D6 gates (generalizes beyond one spec, cites an artifact or repeated drift, not duplicated in `.writ/knowledge/`, below ADR blast radius), writes only qualifying lessons to `.writ/knowledge/lessons/`, and records each in `knowledgeWritten` so resume never double-writes. No qualifying candidate → a silent no-op. Note rejected candidates in the phase report with a reason. Architectural decisions belong in ADRs, never auto-written lessons.

#### Step 4.1c: Phase Progress and Production Health

Before writing the report, capture progress, production health, and the exit-criteria verdict from local evidence only (no probe of production or the network):

```bash
python3 scripts/phase-state.py progress --state .writ/state/phase-execution-{timestamp}.json
python3 scripts/phase-state.py health   --state .writ/state/phase-execution-{timestamp}.json --repo . \
  --eval <latest-eval-summary> --verification <latest-verification-report> --drift <drift-log>
python3 scripts/exit-criteria.py check  --command implement-phase --state .writ/state/phase-execution-{timestamp}.json --repo .
```

`progress`: current spec/lane, per-status counts, quarantine branches, closed specs with reasons, blocked specs with causes. `health`: **categorical** `Healthy` / `Warning` / `Attention`, never a score; missing or stale evidence degrades to `Warning`, and `Attention` requires an affirmative current failure. `exit-criteria.py check`: an independent, read-only re-derivation of `implement-phase.c1`–`c4` (`met`/`unmet`/`impossible`, plus per-criterion verdicts and evidence) that Step 4.2 defers to over the run's self-assessment. Carry all three into the report.

#### Step 4.2: The Honest Completion Report

```
## Phase 1 Report: [name]

| Spec | Implemented | UAT Plan | Notes |
|------|-------------|----------|-------|
| {spec-a} | ✅ 2/2 stories | ✅ 14 scenarios | — |

Closed by decision:
  ✖ {spec-x} — [reason from closure]

Exit criteria:
  ✅ [criterion] — verified ([evidence])
  ⚑ UAT scenarios pass — N scenarios awaiting manual execution

Checker verdict: unmet
  ✅ implement-phase.c1 — met — [evidence]
  ❌ implement-phase.c2 — unmet — [evidence]

Phase status: IMPLEMENTED — pending human validation
```

**Never declare a phase "complete" while human-judgment criteria remain.** The terminal status is then `IMPLEMENTED — pending human validation`, with the UAT plans as the handoff. `COMPLETE` only when every exit criterion is machine-checkable and passing.

**A `Closed by decision` section is mandatory whenever any spec is `closed_not_implemented`**: one line per spec with the reason from `progress`'s `closed` map. A phase whose specs are all `integrated` or `closed_not_implemented` may report `COMPLETE` only when this section names what was dropped and why.

**Checker verdict governs (AC4); branch on Step 4.1c's result before persisting anything:**

- **`impossible`** — name the fired trigger from the checker's `reason` (`haltReported` present, an unresolved `challenge_required`, a criterion recorded `unachievable`, a `reconcile` state/git mismatch, or unreadable criterion inputs) in the Checker verdict line, and **do not call `set-terminal-status` at all**.
- **`unmet`** — the terminal status **cannot be `COMPLETE`**, even if the run believes it is. State the disagreement explicitly, e.g. "run assessment: COMPLETE; checker: unmet on implement-phase.c2; reporting per checker — checker verdict governs." Persist whichever of `IMPLEMENTED_PENDING_HUMAN_VALIDATION` / `PARTIALLY_COMPLETE` the unmet criterion supports.
- **`met`** — the run's own terminal-status determination stands.

Only `met` and `unmet` reach a terminal status; persist it with `scripts/phase-state.py set-terminal-status --status COMPLETE|IMPLEMENTED_PENDING_HUMAN_VALIDATION|PARTIALLY_COMPLETE`. That write also clears any stale `haltReported`; a phase must not carry both fields.

#### Step 4.3: Partial Completion Honesty

If any exit criterion **cannot be fully achieved** (unspecced feature skipped, spec failed, criterion unmeasurable), the report states exactly which and why, and the phase status is `PARTIALLY COMPLETE`. Discovered mid-run with a real choice between degrading scope and aborting → ask (Question Policy condition 2). Discovered at the end → report; do not ask retroactive permission.

---

## Question Policy (Core Rules)

Questions are bounded to exactly these conditions:

1. **Missing exit criteria** — none defined and none derivable from spec contracts. Ask before executing; never invent-and-self-certify.
2. **Unachievable exit criteria discovered mid-run** — and both degrading scope and aborting are defensible. Ask which.
3. **Ambiguous failure blast radius** — a spec failed and it's unclear whether a remaining spec is safe to run.
4. **Decomposition approval** — the breakdown into specs, the seams, and file ownership (Step 1.2b). Ask once, upfront, before creating specs.

Everything else is answered from artifacts (roadmap → spec contract → technical spec → story files, in that precedence order) or accepted as the downstream command's default. The Step 2.3 execution-plan confirmation is the only routine interaction; the condition-4 decomposition confirmation precedes it when it applies.

## Completion

This command succeeds when:

1. **Every specced feature in the phase is implemented** (or explicitly reported as failed/skipped with reasons)
2. **Every implemented spec has a generated `uat-plan.md`** reflecting what was built
3. **Machine-checkable exit criteria are verified with evidence** and human-judgment criteria are handed off, not self-certified
4. **The phase report was presented** with a terminal status: `COMPLETE`, `IMPLEMENTED — pending human validation`, or `PARTIALLY COMPLETE`

**Suggested next step:** Execute the UAT plans manually; then `/ship` (one PR per phase or per spec, per team convention).

**Production boundary:** lane merges go into the phase branch only. Do not merge the phase branch, push, open a PR, release, tag, or publish; `/ship` and `/release` are human-invoked.

**Terminal constraint:** After the phase report, stop. Do not offer to execute UAT scenarios on the human's behalf, auto-advance into uncommitted roadmap phases, or open PRs unprompted.

---

## References

- Standing instructions: [`commands/_preamble.lean.md`](_preamble.lean.md) (the `WRIT_HARNESS_LEAN=1` sibling of `commands/_preamble.md`)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)
