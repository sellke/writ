---
name: implement-spec
description: "Execute one full spec end-to-end - dependency-aware plan, parallel story batches, calling implement-story per story uninterrupted."
problem: "Stories inside one spec get run in whatever order someone notices them, so a dependency cycle surfaces mid-run and cross-story breakage is found long after several stories landed."
outcome: "One spec has no unexecuted story left in its batch plan, and the stories are proven to work together by a single check run after the last of them landed."
exit_criteria:
  - "scripts/story-deps.py validate returned status ok for the full story graph before the first story ran"
  - "no story remains pending in .writ/state/execution-<timestamp>.json - each is complete, skipped with its blocking chain, or failed with a reason"
  - "one typecheck plus full test suite ran after the final story, separate from the targeted per-story Gate 4 runs, and .writ/context.md was rewritten to the post-run story counts"
loop:
  unit: "story"
  max_iterations: 12
  on_exhaustion: halt_reported
  calibrated_against: "Counts stories dispatched to /implement-story, not the human-selected retry offered on story failure, which stays unbounded because a user's choices are not this bound's business. Largest story count across the 41 archived specs under .writ/specs/archive/ = 9 (2026-03-19-command-suite-evolution). Recorded runs: .writ/state/execution-20260718-1101.json = 4 stories, execution-20260803T193200Z.json = 4, execution-20260804205617.json = 4; stories_total in .writ/state/phase9-result-*.json and phase-spec-result-*.json = 4, 4, 3. Bound = all-time authored maximum plus 3. Evidence: strongest of the five bounds - 41 authored specs plus 6 recorded runs."
---

# Implement Spec Command (implement-spec)

## Overview

End-to-end specification execution. Reads a spec, builds a dependency-aware execution plan with parallel batches, then calls `/implement-story` for each story — sequenced correctly, uninterrupted.

This is the **top-level orchestrator**. It owns the plan. `/implement-story` owns the per-story pipeline.

## Required Artifacts

Verify per the preamble's **Artifact Integrity** rule before starting.

- **Required:** target spec folder (`spec.md`, `user-stories/`).
- **Optional:** `.writ/context.md`, `.writ/knowledge/`, execution state (`--resume`).

## Invocation

| Invocation | Behavior |
|---|---|
| `/implement-spec` | Interactive — presents spec selection |
| `/implement-spec 2026-02-22-feature` | Executes named spec |
| `/implement-spec --from story-3` | Starts from story 3 onward |
| `/implement-spec --quick` | Passes `--quick` to each `/implement-story` call |
| `/implement-spec --resume` | Resumes from last saved execution state |

`/implement-spec` is an explicit execute command: invoking it *is* the instruction to run. It builds the plan, presents it for visibility, and executes — there is no execution-plan confirmation gate.

## Command Process

### Phase 1: Spec Discovery & Loading

#### Step 1.1: Find Specs

If no spec argument provided:

Build the option list from `.writ/specs/*/` folders that **contain `spec.md`** — the same single-level glob shape `commands/status.md` and `commands/verify-spec.md` use. This excludes `.writ/specs/archive/<name>/spec.md` by construction (one path segment deeper than the shape matches) — never list bare subfolder names without checking for `spec.md`, since that would surface `archive` itself as a bogus selectable "spec." See [`.writ/docs/spec-lifecycle.md`](../.writ/docs/spec-lifecycle.md) for why this is sufficient.

```
AskQuestion({
  title: "Select Specification",
  questions: [
    {
      id: "spec",
      prompt: "Which specification do you want to implement?",
      options: [list of specs found in .writ/specs/*/ containing spec.md]
    }
  ]
})
```

#### Step 1.2: Load Spec Context

1. **Read spec files:** `spec.md`, `spec-lite.md`, `user-stories/README.md`
2. **Read all story files:** Parse status, dependencies, task counts
3. **Identify already-completed stories** (skip them unless `--force`)

### Phase 2: Dependency Resolution & Planning

#### Step 2.1: Validate the Story Graph (Blocking Gate)

Story order is determined from the **authoritative `> **Dependencies:** ...` headers** on each story file, not agent-interpreted DAG inspection. The executable reference for parsing and ordering is `scripts/story-deps.py validate --spec-dir <spec-folder>` — mirroring how `implement-phase.md` Step 2.1 defers cross-spec ordering to `spec-deps.py` at the spec level.

Run it against the **full** story graph before any pruning — even when `--from story-N` will narrow the plan afterward, a cycle downstream of the entry point is still a cycle:

```bash
python3 scripts/story-deps.py validate --spec-dir .writ/specs/<spec-id>
```

Parse the JSON result:

- **Success** — `{"schema": "story-graph/v1", "status": "ok", "batches": [[...]], "graph": {...}}`, exit 0. Carry the `batches` array unchanged into Step 2.2 — it is already topologically ordered with a numeric story-number tie-break.
- **Blocker** — `{"blocker": {"code": ..., "summary": ...}}`, exit 1. The code names one of `malformed_dependencies`, `missing_reference`, `self_reference`, `duplicate_reference`, or `dependency_cycle` (the summary includes the full cycle path for cycles). **Invalid explicit metadata is blocking.** Stop before Step 2.2 and present the affected story plus the exact diagnostic. Do not guess an order around invalid metadata.
- **Script missing or crashes** — a different failure than a blocker: the graph was never verified at all. Report "cannot verify story graph" (not a named diagnostic code) and stop before Step 2.2 — an unverifiable graph is not a verified graph.

#### Step 2.2: Compute Parallel Batches (from script output)

Batches are the script's `batches` array, consumed directly — not re-derived by agent-interpreted DAG inspection:

```
Batch 1 (parallel):   batches[0] → Story 1, Story 3    — no dependencies
Batch 2 (parallel):   batches[1] → Story 2, Story 4    — dependencies satisfied by batch 1
Batch 3 (sequential): batches[2] → Story 5             — depends on batch 2
```

If `--from story-N` is specified, prune the **already-validated** `batches` array to story N and everything at or after its batch. Validation in Step 2.1 already ran against the full graph, so pruning here never re-opens a graph question — it only narrows which validated batches execute.

#### Step 2.3: Estimate Scope

For each story, count:
- Implementation tasks
- Acceptance criteria
- Estimated complexity (task count × avg)

#### Step 2.3b: Pre-Flight Assessment

Run lightweight sizing checks against remaining stories. Flag if: >8 stories, >50 tasks, dependency depth >3, bottleneck story with >3 dependents, or any story with >7 tasks / >8 AC. Estimate per-story context cost (task count × change surface breadth).

**If no flags:** Proceed silently. **If flags found:** Show concerns above the execution plan and note that `/assess-spec` is available for a full analysis. Pre-flight is advisory — never blocks execution.

#### Step 2.4: Present Execution Plan

Present the plan for visibility, then proceed directly to Phase 3 — there is no confirmation gate.

```
## Execution Plan: 2026-02-22-feature-name

Stories to implement: 5 (2 already complete, 3 remaining)
Estimated phases per story: arch-check → code → lint → review → test → docs

  Batch 1 (parallel):
    ├── Story 3: API Endpoints (5 tasks, 4 AC) — no dependencies
    └── Story 4: Rate Limiting (4 tasks, 3 AC) — no dependencies

  Batch 2 (sequential):
    └── Story 5: Integration Tests (5 tasks, 6 AC) — depends on 3, 4

Skipping (already complete): Story 1, Story 2
```

### Phase 3: Execution

#### Step 3.1: Initialize State

```json
// .writ/state/execution-{timestamp}.json
{
  "spec": "2026-02-22-feature-name",
  "startedAt": "2026-02-22T17:40:00Z",
  "preflight": { "storyDepsValidated": true, "at": "2026-02-22T17:40:00Z" },
  "plan": {
    "batches": [
      { "parallel": true, "stories": ["story-3-api", "story-4-rate-limit"] },
      { "parallel": false, "stories": ["story-5-integration"] }
    ]
  },
  "stories": {
    "story-3-api": { "status": "pending", "phase": null },
    "story-4-rate-limit": { "status": "pending", "phase": null },
    "story-5-integration": { "status": "pending", "phase": null }
  }
}
```

`preflight.storyDepsValidated` / `.at` record the Step 2.1 `story-deps.py validate` result already computed — never re-run it here — closing `implement-spec.c1`'s "before the first story ran" criterion for a post-hoc filesystem read.

#### Step 3.2: Execute Batches

For each batch in order:

**If parallel batch:**
- Spawn `/implement-story {story-id}` for each story in the batch concurrently
- Wait for all to complete before proceeding to next batch
- If any story fails, decide: continue with independent stories or halt

**Platform note:** on a harness where invoking `/implement-story` loads its
instructions into the *current* context rather than running it as a
backgrounded subagent, "spawn ... concurrently" means the orchestrator issues
one parallel tool-call per story (each running that story's own Gate
0/1/3/4/4.5 sequence) — not a nested command call the harness
auto-parallelizes. Confirm which behavior your platform's invocation gives
before assuming concurrency is free.

**If sequential batch:**
- Run `/implement-story {story-id}` one at a time

**Pass-through flags:**
- `--quick` → each `/implement-story` runs in quick mode

#### Step 3.3: Update State After Each Story

After each `/implement-story` completes:
- **Update execution state file with result** — this is a required disk
  write, not a mental note: update the story's `stories.{id}` entry in
  `.writ/state/execution-{timestamp}.json` immediately, before dispatching
  the next story. It is the only artifact `--resume` reads; tracking
  progress solely in conversation state does not substitute for it and will
  not survive a restart.
- Log: pass/fail, review iterations, test count, coverage
- **Regenerate `.writ/context.md`** — full rewrite using the schema defined in `implement-story.md` Step 2 (including the `## Artifact Map` + Integrity line), reflecting the updated story progress. Each write replaces the entire file.

**On story failure:** Present remaining issues and offer: retry, skip (continue with independent stories), skip with all dependents, or abort.

**On dependency blocked:** Present the dependency chain and offer: skip, attempt anyway (dependencies incomplete), retry failed dependency, or abort.

**Iteration bound:** dispatch is bounded at `loop.max_iterations` (12) **stories**. The retry above is human-selected and deliberately outside the bound — `max_iterations` counts stories dispatched, not choices a user makes. On exhaustion, `loop.on_exhaustion: halt_reported` applies: stop dispatching and report the unit (`story`), the bound, the count reached, the last completed story, the `.writ/state/execution-*.json` path whose `stories.{id}.status` / `phase` fields already hold the resume position, and the literal resume command `/implement-spec --resume`. Remaining stories stay `pending`; nothing is skipped, marked complete, or self-certified to get past the bound.

### Phase 4: Completion

#### Step 4.1: Integration Verification

After all stories complete, run a single integration check to catch cross-story breakage. Per-story tests already ran in each `/implement-story` Gate 4 — this step only verifies that the stories work *together*.

```bash
# 1. Typecheck — catches cross-story type conflicts (always fast)
npx tsc --noEmit

# 2. Full test suite — catches integration breakage between stories
npm test    # or equivalent (pytest, cargo test, go test ./...)
```

If integration failures: identify which story likely broke it, report to user.

> **Why not proportional?** Each story's Gate 4 already ran targeted tests and coverage. At the spec level, multiple stories have landed — the risk of cross-story breakage justifies one full-suite run regardless of individual change surfaces.

Record the result on `.writ/state/execution-{timestamp}.json` as `postRun: {typecheck, testSuite, contextRewritten, at}` — `typecheck` and `testSuite` hold `pass`/`fail`, `contextRewritten` is a boolean confirming Step 3.3's rewrite ran with the final story counts. This closes `implement-spec.c3`'s "after the final story" criterion, which a post-hoc filesystem read cannot otherwise recover.

**Only after `postRun` is written**, run the exit-criteria checker against the now-current state file — sequencing matters because `implement-spec.c1` and `.c3` read `preflight`/`postRun` directly, so a checker run before `postRun` exists would read it absent and correctly, but unhelpfully, report `unknown` instead of the true verdict:

```bash
python3 scripts/exit-criteria.py check --command implement-spec --spec <spec-dir> --state .writ/state/execution-{timestamp}.json
```

Carry its overall verdict and each criterion's evidence into the Step 4.2 report.

#### Step 4.2: Summary Report

```
✅ Specification Complete: feature-name

| Story | Status | Review Iterations | Tests | Coverage | Docs |
|-------|--------|-------------------|-------|----------|------|
| 3: API | ✅ | 1 | 15/15 | 91% | Updated |
| 4: Rate Limit | ✅ | 2 | 8/8 | 87% | Updated |
| 5: Integration | ✅ | 1 | 12/12 | 94% | Updated |

Execution Stats:
- Total time: ~X minutes
- Stories: 3/3 complete
- Total tests: 35 passing
- Average coverage: 91%
- Review iterations: 4 total (1.3 avg)
- Integration tests: ✅ passing

Checker verdict: met
  ✅ implement-spec.c1 — met — story graph validated ok at 2026-02-22T17:40:00Z, before batch 1
  ✅ implement-spec.c2 — met — 3/3 stories terminal
  ✅ implement-spec.c3 — met — typecheck+test suite ran after the final story at 2026-02-22T18:05:00Z; context.md rewritten

Next steps:
- Optional: `/verify-spec` if you want a standalone metadata pass
- Run `/security-audit` for a security review
- `/ship` to open a PR, then `/release --dry-run` → `/release` when ready to publish
```

**Checker verdict governs the banner (AC4).** `implement-spec` carries no `terminalStatus` field to defer to, so here "governs" means the `✅ Specification Complete` banner itself is gated on the checker's verdict, not on the run's own account of story completion:

- **`met`** — the `✅ Specification Complete` banner stands as shown.
- **`unmet`** — the banner is replaced with the checker's verdict and the unmet criterion's reason instead of `✅ Specification Complete`, even if every story in this run's own account finished — e.g. `⚠️ Specification: implement-spec.c2 unmet — story-5-integration still pending`.
- **`impossible`** — same substitution, naming the fired trigger from the checker's `reason` (e.g. an unreadable state file or a criterion whose own inputs could not be read) rather than presenting `✅ Specification Complete`.

**Spec header sync.** When the checker verdict is `met` and every story is
`Completed ✅`, update `spec.md`'s own `> **Status:**` line to `Complete
(<date>)` — the same completion status story files and `README.md` already
receive at Step 3.3 / Step 4 of `implement-story.md`. This header is easy to
leave stale, since nothing else in this file writes it; `/verify-spec`
Check 5b is otherwise the first thing to notice.

---

## Phase-Orchestrated Lane Mode

When `/implement-phase` invokes this command inside an isolated per-spec lane, `/implement-spec` is a **nested worker, not an orchestrator**. In this mode:

- It executes **only inside the supplied lane** worktree and branch that the orchestrator created (`writ/phase/{phase-id}/{spec-id}`). It **must not mutate the parent checkout**, create its own lanes, or make merge/quarantine decisions — those belong to `/implement-phase`.
- It receives a fresh, artifact-seeded context (spec path, phase-state path, lane branch/worktree, mode) with **no prior conversational transcript**, and loads what it needs from repository artifacts by path.
- On completion it returns a single structured `phase-spec-result-v1` result (see [`.writ/docs/phase-execution-state-format.md`](../.writ/docs/phase-execution-state-format.md)) reporting status, story counts, verification evidence, changed files, the lane commit, and any failure or challenge — and then exits. The orchestrator validates that result (`scripts/phase-state.py validate-result`) and decides whether to merge, retry, or quarantine.
- On failure it sets `failure.classification` to **`transient`** (e.g. a flaky check that a single retry may clear) or **`terminal`** (a genuine, non-recoverable failure). It never renames branches, quarantines, or blocks dependents itself — the orchestrator owns retry and quarantine decisions based on this classification.

**Scope-degradation escalation (User Challenge).** If, inside a lane, a choice would weaken roadmap scope, the locked spec contract, or exit criteria, apply the evidence-based **select-or-pause** boundary (see [`_preamble.md`](_preamble.md) → User Challenge). A defensible low-risk reversible choice may be selected locally **only** when returned with the structured four-part challenge and durable audit evidence; missing evidence, critical ambiguity, or material irreversible risk returns `status: challenge_required` with the four-part challenge and selectable options for the orchestrator to present. Ordinary progress, transient failures, and decisions already answered by artifacts are **not** challenges and use normal handling.

Normal direct `/implement-spec` invocation (outside a phase) is unchanged and follows Phases 1–4 and Resume Support.

## Resume Support

If a session is interrupted mid-execution:

```
/implement-spec --resume
```

1. Finds most recent execution state file in `.writ/state/`
2. Identifies last completed story/phase
3. Picks up from next pending story
4. Re-runs current story from the beginning of its pipeline (idempotent)

---

## Integration with Writ Ecosystem

| Command | Relationship |
|---------|-------------|
| `/create-spec` | Creates the spec that `/implement-spec` executes |
| `/implement-phase` | Calls `/implement-spec` once per spec inside an isolated lane; owns cross-spec sequencing |
| `/assess-spec` | Pre-flight sizing check runs automatically in Step 2.3b; full assessment available on demand |
| `/implement-story` | Called per-story by `/implement-spec` for the 6-gate pipeline |
| `/verify-spec` | Optional metadata diagnostic anytime (especially after `/implement-spec`) — not a release prerequisite |
| `/ship` / `/release` | `/ship` opens the PR; `/release` cuts the version with its own inline gate |
| `/status` | Shows progress of in-flight executions |

## Completion

This command succeeds when no story in the batch plan remains pending in `.writ/state/execution-<timestamp>.json` — each is complete, skipped with its blocking chain recorded, or failed with a reason — and the post-batch typecheck and full test suite have run.

A run ending with stories skipped or failed is a completed run, not a broken one, provided each carries its reason and `.writ/context.md` reflects the real counts.

**Terminal constraint:** This command implements one spec's stories. Do not advance to the next spec in the phase, open a PR, or cut a release.

---

## References

- Standing instructions: [`commands/_preamble.md`](_preamble.md)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)
