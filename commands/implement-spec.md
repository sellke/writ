# Implement Spec Command (implement-spec)

## Overview

End-to-end specification execution. Reads a spec, builds a dependency-aware execution plan with parallel batches, confirms with the user, then calls `/implement-story` for each story — sequenced correctly, uninterrupted.

This is the **top-level orchestrator**. It owns the plan. `/implement-story` owns the per-story pipeline.

## Invocation

| Invocation | Behavior |
|---|---|
| `/implement-spec` | Interactive — presents spec selection |
| `/implement-spec 2026-02-22-feature` | Executes named spec |
| `/implement-spec --from story-3` | Starts from story 3 onward |
| `/implement-spec --quick` | Passes `--quick` to each `/implement-story` call |
| `/implement-spec --resume` | Resumes from last saved execution state |

## Command Process

### Phase 1: Spec Discovery & Loading

#### Step 1.1: Find Specs

If no spec argument provided:

```
AskQuestion({
  title: "Select Specification",
  questions: [
    {
      id: "spec",
      prompt: "Which specification do you want to implement?",
      options: [list of specs found in .writ/specs/]
    }
  ]
})
```

#### Step 1.2: Load Spec Context

1. **Read spec files:** `spec.md`, `spec-lite.md`, `user-stories/README.md`
2. **Read all story files:** Parse status, dependencies, task counts
3. **Identify already-completed stories** (skip them unless `--force`)

### Phase 2: Dependency Resolution & Planning

#### Step 2.1: Build Dependency Graph

Parse each story's dependency declarations and construct a DAG:

```
Stories: 1(none), 2(→1), 3(none), 4(→3), 5(→2,4)

Graph:
  1 ──→ 2 ──→ 5
  3 ──→ 4 ──↗
```

#### Step 2.2: Compute Parallel Batches

Topological sort into batches of independent stories:

```
Batch 1 (parallel): Story 1, Story 3    — no dependencies
Batch 2 (parallel): Story 2, Story 4    — dependencies satisfied by batch 1
Batch 3 (sequential): Story 5           — depends on batch 2
```

If `--from story-3` is specified, prune the graph to story 3 and all downstream stories.

#### Step 2.3: Estimate Scope

For each story, count:
- Implementation tasks
- Acceptance criteria
- Estimated complexity (task count × avg)

#### Step 2.3b: Pre-Flight Assessment

Run lightweight sizing checks against remaining stories. Flag if: >8 stories, >50 tasks, dependency depth >3, bottleneck story with >3 dependents, or any story with >7 tasks / >8 AC. Estimate per-story context cost (task count × change surface breadth).

**If no flags:** Proceed silently. **If flags found:** Show concerns above the execution plan and add `{ id: "assess", label: "Run /assess-spec for full analysis first" }` to the confirmation options. Pre-flight is advisory — never blocks execution.

#### Step 2.4: Present Execution Plan

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

#### Step 2.5: Confirm

```
AskQuestion({
  title: "Confirm Execution Plan",
  questions: [
    {
      id: "proceed",
      prompt: "Proceed with this execution plan?",
      options: [
        { id: "yes", label: "Execute the plan" },
        { id: "edit", label: "Change which stories to include" },
        { id: "reorder", label: "Change execution order" },
        { id: "quick", label: "Execute in quick mode (skip review + docs)" },
        // Include only when Step 2.3b found flags:
        { id: "assess", label: "Run /assess-spec for full analysis first" }
      ]
    }
  ]
})
```

If the user selects "assess," run `/assess-spec` with this spec pre-selected. After assessment completes, the user re-invokes `/implement-spec` for a fresh plan.

### Phase 3: Execution

#### Step 3.1: Initialize State

```json
// .writ/state/execution-{timestamp}.json
{
  "spec": "2026-02-22-feature-name",
  "startedAt": "2026-02-22T17:40:00Z",
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

#### Step 3.2: Execute Batches

For each batch in order:

**If parallel batch:**
- Spawn `/implement-story {story-id}` for each story in the batch concurrently
- Wait for all to complete before proceeding to next batch
- If any story fails, decide: continue with independent stories or halt

**If sequential batch:**
- Run `/implement-story {story-id}` one at a time

**Pass-through flags:**
- `--quick` → each `/implement-story` runs in quick mode

#### Step 3.3: Update State After Each Story

After each `/implement-story` completes:
- Update execution state file with result
- Log: pass/fail, review iterations, test count, coverage

**On story failure:** Present remaining issues and offer: retry, skip (continue with independent stories), skip with all dependents, or abort.

**On dependency blocked:** Present the dependency chain and offer: skip, attempt anyway (dependencies incomplete), retry failed dependency, or abort.

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

Next steps:
- Optional: `/verify-spec` if you want a standalone metadata pass
- Run `/security-audit` for a security review
- `/ship` to open a PR, then `/release --dry-run` → `/release` when ready to publish
```

---

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
| `/assess-spec` | Pre-flight sizing check runs automatically in Step 2.3b; full assessment available on demand |
| `/implement-story` | Called per-story by `/implement-spec` for the 6-gate pipeline |
| `/verify-spec` | Optional metadata diagnostic anytime (especially after `/implement-spec`) — not a release prerequisite |
| `/ship` / `/release` | `/ship` opens the PR; `/release` cuts the version with its own inline gate |
| `/status` | Shows progress of in-flight executions |
