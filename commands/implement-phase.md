# Implement Phase Command (implement-phase)

## Overview

Autonomous phase-level orchestrator. Reads a roadmap phase from `.writ/product/roadmap.md`, resolves its features to specs in `.writ/specs/` — proposing and creating any missing specs through a decomposition pre-pass — then loops `/implement-spec` → `/create-uat-plan` per spec — sequenced by cross-spec dependencies — until every spec in the phase is implemented and has a UAT plan. Ends by mapping results against the phase's exit criteria and handing off manual UAT execution.

This is the layer above `/implement-spec`: roadmap → **`/implement-phase`** → `/implement-spec` → `/implement-story`. It owns cross-spec sequencing; `/implement-spec` owns story batching within a spec.

**Question policy is the defining constraint:** the roadmap and specs already answered most questions. This command asks only when an answer genuinely doesn't exist in the artifacts.

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

`/implement-phase --recommend` runs the phase as a complete end-to-end loop with no routine confirmations. It is the **only** command that autonomously chains spec *authoring* into *implementation* (see [ADR-013](../.writ/decision-records/adr-013-recommended-autonomous-delivery.md)).

- **Auto-author missing specs.** When unspecced features exist, the decomposition pre-pass (Step 1.2b) runs without its approval gate, and each proposed spec is created with `/create-spec --recommend` — autonomous, evidence-backed contract authoring — instead of the collaborative `/create-spec`. Record each authoring decision in that spec's `recommendation-log.md`.
- **Auto-accept the execution plan.** The single Step 2.3 execution-plan confirmation is auto-accepted; the loop then runs exactly as in normal mode (isolated lanes → `/implement-spec` per spec → `/create-uat-plan`).
- **Terminal scope is unchanged.** The loop still ends at the honest completion report (Phase 4) and hands off manual UAT — it never ships, opens PRs, or releases. Those "bigger loops" are deferred.
- **Genuine pauses are retained** — the Question Policy conditions that are *not* routine confirmations still stop the loop: missing exit criteria that cannot be derived (never invent-and-self-certify, Step 2.2), an exit criterion that becomes unachievable mid-run (Step 4.3), and an ambiguous failure blast radius (Step 3.3).

`--recommend` composes with `--all` and `--specs`. It is incompatible with `--quick` — full story, review, testing, and documentation gates are mandatory when authoring and implementation run autonomously.

## Command Process

### Phase 1: Phase Resolution

#### Step 1.1: Load the Roadmap

Read `.writ/product/roadmap.md`. If it doesn't exist and `--specs` wasn't provided, report the gap and offer the fallback: the user names specs directly, and those specs *are* the phase (exit criteria then come from spec contracts only).

If no phase argument is given, present the roadmap's phases via AskQuestion — show each phase's status (how many of its specs are complete) so the choice is informed.

#### Step 1.2: Resolve Features to Specs

Map the selected phase's feature list to spec folders in `.writ/specs/`. Matching is by spec reference when the roadmap names one explicitly (preferred), otherwise by title similarity.

Classify each feature:

- **Specced** — a spec folder exists; include in the execution loop
- **Unspecced** — no spec exists; the phase cannot be fully completed by this command

**Unspecced features are an ask-worthy condition** (the exit criteria cannot be fully achieved). Ask once, upfront — not mid-loop:

```
AskQuestion: Phase N includes features without specs: [list].
  - Decompose now — propose a spec breakdown and create the specs (Step 1.2b), then continue
  - Proceed with specced features only (phase will end "partially complete")
  - Stop so I can run /create-spec myself first
```

**Decompose now** is the recommended default when two or more features are unspecced: turning a roadmap phase into the *right set* of specs is otherwise tacit judgment, made once and informally at the first `/create-spec`. For a single unspecced feature there is nothing to decompose — route it straight to one `/create-spec`.

#### Step 1.2b: Decomposition Pre-Pass (unspecced features → the right set of specs)

Runs only when the user chose **Decompose now**. This is the just-in-time seam between a roadmap phase and its specs — deliberately placed here, at implementation time, so boundaries are drawn against the *current* codebase rather than stale plan-time assumptions.

**Produce a decomposition proposal — one artifact, one confirmation:**

1. **Analyze** the unspecced features against the codebase: the files, commands, and scripts each feature touches, and where those surfaces overlap.
2. **Propose specs** — group features into independently shippable, independently testable specs. Prefer one spec per coherent deliverable; split when a feature is large enough to stand alone, merge when two features are truly one deliverable. Avoid both grab-bag bundling and over-fragmentation.
3. **Draw the dependency graph** — the `> **Dependencies:** [...]` edges each proposed spec will declare, so Step 2.1 can sequence them deterministically.
4. **Assign file ownership** — name the single spec that owns each shared file (e.g., a command or script two features both touch). Single-writer-per-file is what keeps the concurrent lanes of Step 3.2 from colliding on merge; a shared surface with two owners is a planning defect to resolve here, not an implementation surprise to hit later.
5. **Name the seams** — the contracts *between* specs (shared schema, script signature, command flag) that must hold for the pieces to integrate.

**Present the proposal for one approval:**

```
## Decomposition Proposal: Phase N — [name]

Proposed specs (from [M] unspecced features):
  1. {slug-a}  — [deliverable]        deps: []          owns: [files]
  2. {slug-b}  — [deliverable]        deps: [slug-a]    owns: [files]
  3. {slug-c}  — [deliverable]        deps: []          owns: [files]

Seams:
  - {slug-a} ⇄ {slug-b}: [shared contract that must hold]

Rationale: [why these boundaries — coherence, independent testability, ownership]
```

Confirm with AskQuestion: create these specs / edit the breakdown / stop. **The decomposition plan is an ask-worthy condition** (condition 4) — the roadmap does not answer how many specs, where the seams fall, or who owns a shared file, and no artifact can derive it. This is a *planning* confirmation, distinct from and earlier than the Step 2.3 execution gate. **In `--recommend` mode this confirmation is auto-accepted** — the decomposition is treated as an evidence-backed autonomous decision and recorded.

**On approval, create the specs — contract-first is not bypassed.** For each proposed spec in dependency order, run `/create-spec` seeded with its deliverable, files-in-scope, `dependencies:`, and ownership constraints from the proposal. Each spec is still contract-locked (per ADR-001, specs are never created without agreement); the seed makes each discovery short and focused rather than starting cold. Specs are *authored* collaboratively in this pre-pass; only *implementation* (Phase 3) runs autonomously. **In `--recommend` mode, run `/create-spec --recommend` instead** — each spec's contract is auto-locked from evidence and its decisions recorded in `recommendation-log.md`; the seed still applies.

**After the specs exist, re-resolve** — return to Step 1.2 classification. The freshly created specs are now **Specced** and enter the normal inventory, sequencing, and execution flow.

> **`--all` boundary:** the pre-pass is never auto-entered in `--all` mode — creating specs requires human agreement. Unspecced features encountered under `--all` fall back to the "partially complete" path unless the phase is run interactively. **`--recommend` is the explicit exception:** it authorizes autonomous spec creation, so `--recommend` (with or without `--all`) auto-enters the pre-pass and authors missing specs via `/create-spec --recommend`.

#### Step 1.3: Inventory Prior Progress

For each specced feature, determine its actual state — this is what makes `--resume` and re-runs cheap:

1. **Story statuses** in `user-stories/story-*.md` — complete / in progress / not started
2. **Existing `uat-plan.md`** — a populated UAT plan (not a stub) signals the spec was implemented and its validation artifact exists; skip both implementation and UAT generation unless stories changed after the plan's generation date
3. **Prior execution state** in `.writ/state/phase-execution-*.json`

Specs that are fully complete with a current UAT plan are skipped and reported as such.

### Phase 2: Sequencing & The One Confirmation

#### Step 2.1: Validate and Order the Specs

Cross-spec order is determined from the **authoritative `> **Dependencies:** [...]` headers**, not prose. Build the graph first, then order it. Precedence:

1. **Valid explicit `Dependencies` graph** — parse each spec's `> **Dependencies:** [spec-folder-id, ...]` header (a legacy spec with no header is treated as `[]`), then **topological**ly order the resulting DAG. This explicit graph is binding.
2. **Roadmap order** — among otherwise independent specs (no dependency relationship), release them in **roadmap order** as the deterministic tie-break, so the plan is reproducible run to run.
3. **Shared-surface inference remains advisory** — if two specs with no declared relationship touch the same files/functions, *warn* in the phase plan and run them sequentially by roadmap order. Inference can never reorder or override a valid explicit graph.

The executable reference for parsing and ordering is `scripts/spec-deps.py validate --specs-dir .writ/specs --roadmap-order <phase spec order>`.

**Invalid explicit metadata is blocking.** If the graph has a malformed header, a missing reference, a self-reference, a duplicate entry, or a cycle, **stop before the confirmation gate** and present the affected spec plus the exact graph diagnostic (missing reference, self edge, duplicate, or cycle path). Do not guess an order around invalid metadata.

Specs with no ordering relationship may be listed as independent, but execution is sequential by default — parallel spec execution multiplies conflict risk across a shared codebase for little gain at this scale.

#### Step 2.2: Verify Exit Criteria Exist

Read the phase's **Exit Criteria** and **Success Metrics** from the roadmap. Classify each:

- **Machine-checkable** — tests pass, files load, no external dependencies introduced, typecheck clean
- **Human-judgment** — "feels complete for daily use", UAT scenario passes

**If the phase has no exit criteria at all**, this is the command's core ask-worthy condition. Ask the user to state completion criteria before executing — never invent exit criteria and then self-certify against them.

#### Step 2.3: Present the Phase Execution Plan (single confirmation gate)

```
## Phase Execution Plan: Phase 1 — [name]

Specs: 3 total (0 complete, 3 remaining)

  1. 2026-07-07-timestamped-notes-stage-history  (2 stories) — must run first (cross-spec note)
  2. 2026-07-07-drag-and-drop-across-states       (1 story)  — after #1 (shared renderCard)
  3. 2026-07-07-contact-linkedin-website-fields   (1 story)  — after #1 (shared normalizeProspect)

Per spec: /implement-spec → /create-uat-plan

Exit criteria (from roadmap):
  ✓ machine-checkable: old JSON files load cleanly; no external deps introduced
  ⚑ human-judgment: UAT scenarios pass — handed off at the end

Pre-flight flags: [any /implement-spec sizing concerns, surfaced but non-blocking]
```

Confirm with AskQuestion: execute / edit spec list / abort. **This is the last routine question.** Everything after this runs autonomously except the failure and exit-criteria conditions below. **In `--recommend` mode this confirmation is auto-accepted** — the loop proceeds directly to Phase 3.

### Phase 3: The Loop

#### Step 3.1: Initialize Phase State

Initialize `.writ/state/phase-execution-{timestamp}.json` (schema `phase-execution-v2`) via `scripts/phase-state.py init`, recording the phase, phase branch, topologically ordered spec list, and per-spec record. This file is the **resume boundary** — the combination of state plus git reality is the only source of truth on `--resume`. It is updated after every transition using atomic writes (temp file + rename). The canonical contract is [`.writ/docs/phase-execution-state-format.md`](../.writ/docs/phase-execution-state-format.md).

#### Step 3.2: Per-Spec Iteration (Fresh Isolated Lanes)

The orchestrator owns lane creation, result validation, merge, and UAT handoff. Each spec runs in a **fresh subagent** inside its own isolated git lane — no accumulated conversational context reaches the spec. For each spec in order:

1. **Create the lane before any work** — `scripts/phase-state.py create-lane` verifies the phase branch is clean, then creates branch `writ/phase/{phase-id}/{spec-id}` and a dedicated worktree from the current phase-branch head. A dirty base or a branch collision **stops before launch** (`dirty_base` / `lane_collision`); isolation created only after a failure cannot prove the phase branch stayed clean.
2. **Spawn a fresh subagent** seeded only with artifact paths (spec path, phase-state path, lane branch/worktree, mode, inherited answer sources) and the expected `phase-spec-result-v1` schema. **No prior conversational transcript is forwarded** — required context is loaded from repository artifacts by path. The subagent runs `/implement-spec {spec}` inside the lane worktree and returns the structured result. Pass through `--quick` if set.
3. **Validate the result and merge only verified success** — `scripts/phase-state.py validate-result` gates the merge: **only a verified** `phase-spec-result-v1` with `status: succeeded`, a real commit, and non-empty verification evidence merges (`--no-ff`) into the phase branch (`integrate`), after which the worktree is removed and the merge commit recorded.
4. **Preserve anything else** — a missing, malformed, non-successful, or unverifiable result never touches the phase branch; its lane is preserved for Step 3.3 / Story 4 to classify, quarantine, and recover.
5. **On a merged success, run `/create-uat-plan {spec}`** — the UAT plan is the exit artifact of the iteration, generated *after* implementation so it reflects what was actually built. Update phase state and continue.

**Inherited-answer rule:** any question `/implement-spec` or its sub-pipeline would ask that is answered by the spec contract, story files, technical spec, or roadmap is answered from those artifacts without surfacing to the user. Only questions with no artifact-derivable answer bubble up.

#### Step 3.2b: User Challenge Handling

`/implement-phase` is the **sole presenter** of User Challenges (see [`_preamble.md`](_preamble.md) → User Challenge). When a nested `phase-spec-result-v1` returns `status: challenge_required` — or an audited evidence-backed selection:

1. **Validate** the challenge with `scripts/phase-state.py validate-challenge`. A malformed challenge (missing any of the four parts, bad trigger, or no options) is a **contract error** routed to normal failure handling — never rendered as a User Challenge.
2. **Present** a valid unresolved challenge through one explicit `AskQuestion` showing all four parts — *What the roadmap/spec said*, *What Writ recommends*, *What context may be missing*, *Cost if the recommendation is wrong* — and pause before any scope-changing action. An audited low-risk reversible selection proceeds automatically.
3. **Persist** the challenge, selected option, and decision timestamp via `record-challenge` / `resolve-challenge` so resume reconstructs the escalation exactly and never re-asks a decided question.

**ordinary failures use their normal** failure path (Step 3.3), and decisions already answered by artifacts are resolved from those artifacts — neither uses User Challenge framing.

#### Step 3.3: Failure Handling

When a lane returns a non-successful `phase-spec-result-v1`, classify and dispose of it via `scripts/phase-state.py` — the phase branch is never touched by failed work:

1. **Bounded retry.** `classify` decides retry vs quarantine. Writ permits exactly **one transient retry**: a `transient` first-attempt failure is retried once in the *same* isolated lane with a fresh subagent (`retry`), with no new routine confirmation. A `terminal` failure, or a transient failure after the retry, is terminal.
2. **Quarantine on terminal failure.** `quarantine` removes the lane worktree and preserves the lane as `writ/quarantine/{spec-id}` (deterministic suffix on collision, mapping recorded), guarantees the phase branch is clean of the failed lane, and records failure evidence, retry count, quarantine branch, and a recovery command.
3. **Block dependents, continue independents.** Direct and transitive dependents become `skipped_blocked` with `blockedBy` evidence; **specs independent of the failure continue** — don't hold finished work hostage to one failure.
4. **Ask only if ambiguous:** if the dependency relationship between the failed spec and a remaining spec is unclear (no explicit declaration, but shared surfaces), ask whether to proceed — condition (c) of the question policy.

On `--resume`, run `reconcile` first: it checks phase, lane, worktree, and quarantine branches against recorded state and continues only if they agree. On any discrepancy it reports the named mismatch and a recovery command and **does not guess or mutate git**.

#### Step 3.4: `--all` Mode

After a phase completes, advance to the next roadmap phase **only if** the completed phase's machine-checkable exit criteria all pass. Phases marked "Tentative" or "Not Committed" in the roadmap are never auto-entered — stop and report instead. Human-judgment criteria don't block advancement in `--all` mode, but they are accumulated into the final handoff.

### Phase 4: Exit Criteria Verification & Handoff

#### Step 4.1: Verify Machine-Checkable Criteria

Run each machine-checkable exit criterion from the roadmap (plus `/implement-spec`'s own integration verification, which already ran per spec). Record pass/fail per criterion — with evidence, not assertion.

#### Step 4.1b: Evidence-Bound Knowledge Writeback

At phase close, collect candidate lessons from the phase report and per-spec drift logs and run `scripts/phase-state.py knowledge-writeback`. It applies the **evidence-bound** D6 gates — generalizes beyond one spec, cites an artifact or repeated drift, is not substantively duplicated in `.writ/knowledge/`, and is below ADR blast radius — and writes only qualifying lessons to `.writ/knowledge/lessons/`, recording each in `knowledgeWritten` so resume never double-writes. **When there is no qualifying candidate this is a silent no-op** that changes no knowledge file; rejected candidates are noted in the phase report with a terse reason. This step never downgrades an architectural decision into an auto-written lesson — those belong in ADRs.

#### Step 4.1c: Phase Progress and Production Health

Before writing the report, capture the phase's **progress** and **production health** from local evidence only — never a heavyweight probe of production or the network:

```bash
python3 scripts/phase-state.py progress --state .writ/state/phase-execution-{timestamp}.json
python3 scripts/phase-state.py health   --state .writ/state/phase-execution-{timestamp}.json --repo . \
  --eval <latest-eval-summary> --verification <latest-verification-report> --drift <drift-log>
```

`progress` reports the current spec/lane, per-status spec counts, and quarantine branches. `health` returns a **categorical** disposition (`Healthy` / `Warning` / `Attention`), never a score: missing or stale evidence degrades to `Warning` (never a silent pass), and `Attention` requires an affirmative current failure (eval findings, failing verification, unresolved material drift, or a `phase-state`/git mismatch). Carry both into the completion report so the maintainer sees phase progress and production health with the evidence behind each. The same reducers back `/status`, so an interrupted phase reports identically on resume.

#### Step 4.2: The Honest Completion Report

```
## Phase 1 Report: [name]

| Spec | Implemented | UAT Plan | Notes |
|------|-------------|----------|-------|
| timestamped-notes-stage-history | ✅ 2/2 stories | ✅ 14 scenarios | — |
| drag-and-drop-across-states     | ✅ 1/1 stories | ✅ 9 scenarios  | — |
| contact-linkedin-website-fields | ✅ 1/1 stories | ✅ 6 scenarios  | — |

Exit criteria:
  ✅ Old JSON files load cleanly — verified (integration check)
  ✅ No external dependencies introduced — verified (no network refs in file)
  ⚑ UAT scenarios pass — 29 scenarios awaiting manual execution

Phase status: IMPLEMENTED — pending human validation
```

**The command never declares a phase "complete" when human-judgment criteria remain.** The terminal status is `IMPLEMENTED — pending human validation`, with the UAT plans as the handoff. If every exit criterion is machine-checkable and passing, the status may be `COMPLETE`.

#### Step 4.3: Partial Completion Honesty

If any exit criterion **cannot be fully achieved** (unspecced feature skipped, spec failed, criterion unmeasurable), the report states exactly which and why, and the phase status is `PARTIALLY COMPLETE`. This is condition (b) of the question policy: when discovered mid-run and a choice exists between degrading scope and aborting, ask; when discovered at the end, report — don't ask retroactive permission.

---

## Question Policy (Core Rules)

The command's value is autonomy. Questions are the exception, bounded to exactly these conditions:

1. **Missing exit criteria** — the phase (or fallback spec set) defines no completion criteria and none can be derived from spec contracts. Ask before executing; never invent-and-self-certify.
2. **Unachievable exit criteria discovered mid-run** — a criterion cannot be met (unspecced feature, failed spec, unmeasurable metric) and both degrading scope and aborting are defensible. Ask which.
3. **Ambiguous failure blast radius** — a spec failed and it's unclear whether a remaining spec is safe to run.
4. **Decomposition approval** — unspecced features exist and the user chose to decompose; the breakdown into specs, the seams, and file ownership cannot be derived from any artifact. Ask once, upfront (Step 1.2b), before creating specs.

Everything else is answered from artifacts (roadmap → spec contract → technical spec → story files, in that precedence order) or accepted as the downstream command's default. The single upfront execution-plan confirmation is the only routine interaction — preceded, when unspecced features are decomposed, by the one decomposition confirmation of condition 4.

## Integration with Writ

| Command | Relationship |
|---------|-------------|
| `/plan-product` | Creates `roadmap.md`, the source of phases and exit criteria |
| `/create-spec` | Creates the specs a phase resolves to; invoked per proposed spec by the Step 1.2b decomposition pre-pass (or run manually) to remedy unspecced features |
| `/implement-spec` | Called once per spec inside an isolated lane; owns story batching (it has no confirmation gate — invoking it executes) |
| `/create-uat-plan` | Called after each spec completes; produces the per-spec validation artifact and the resume signal |
| `/assess-spec` | Pre-flight flags from `/implement-spec` are surfaced in the phase plan; run this first for flagged specs if concerned |
| `/ship` | Natural next step after the phase report — one PR per phase or per spec, per team convention |
| `/status` | Reads `.writ/state/phase-execution-*.json` to show in-flight phase progress |

## Completion

This command succeeds when:

1. **Every specced feature in the phase is implemented** (or explicitly reported as failed/skipped with reasons)
2. **Every implemented spec has a generated `uat-plan.md`** reflecting what was built
3. **Machine-checkable exit criteria are verified with evidence** and human-judgment criteria are handed off, not self-certified
4. **The phase report was presented** with an honest terminal status: `COMPLETE`, `IMPLEMENTED — pending human validation`, or `PARTIALLY COMPLETE`

**Suggested next step:** Execute the UAT plans manually; then `/ship`.

**Terminal constraint:** After the phase report, stop. Do not offer to execute UAT scenarios on the human's behalf, auto-advance into uncommitted roadmap phases, or open PRs unprompted.

---

## References

- Standing instructions: [`commands/_preamble.md`](_preamble.md)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)
