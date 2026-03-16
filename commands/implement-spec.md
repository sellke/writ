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

Run a lightweight subset of `/assess-spec` checks (1, 2, 3, and 6) against the remaining stories. This catches sizing and context problems before the user commits to execution.

**Checks to run (inline — no subagent needed):**

1. **Spec sizing** — Flag if >8 remaining stories or >50 remaining tasks
2. **Dependency depth** — Flag if max depth >3 or any bottleneck story has >3 dependents
3. **Story sizing** — Flag any story with >7 tasks or >8 acceptance criteria
4. **Context cost** — Estimate per-story context weight (task count × change surface breadth), sum across remaining stories

**If no flags:** Proceed silently to Step 2.4. No output.

**If flags found:** Insert an assessment block above the execution plan:

```
⚠️ Pre-Flight Assessment: 2 concerns detected

 STORY SIZING        🛑  Story 3 has 9 tasks (limit: 7)
 CONTEXT BUDGET      ⚠️  Score 18 — moderate-high accumulation risk

 Recommendation: Run /assess-spec for full analysis with decomposition options.
 Or proceed — these are risks, not blockers.
```

The flags are shown *above* the execution plan so the user sees them before being asked to confirm. The confirmation step (Step 2.5) gains an additional option when flags are present:

```
{ id: "assess", label: "Run /assess-spec for full analysis first" }
```

If the user selects "assess," hand off to `/assess-spec` with the current spec pre-selected. After assessment completes (with or without decomposition), the user can re-invoke `/implement-spec` to get a fresh execution plan.

**Pre-flight does NOT block execution.** The user can always select "Execute the plan" despite warnings. The assessment is advisory — the user may have good reasons to proceed (e.g., tight deadline, the oversized story is straightforward despite its task count).

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

**On story failure:**
```
⚠️ Story 4 failed after 3 review iterations.

Remaining issues:
{issues}

Options:
1. Retry Story 4
2. Skip Story 4, continue with independent stories
3. Skip Story 4, skip all dependents (Story 5)
4. Abort spec execution
```

**On dependency blocked:**
```
⚠️ Story 5 depends on Story 4, which failed.

Options:
1. Skip Story 5
2. Attempt Story 5 anyway (dependencies incomplete)
3. Retry Story 4 first
4. Abort
```

### Phase 4: Completion

#### Step 4.1: Integration Verification

After all stories complete, choose a verification strategy proportional to the change surface:

**Assess the change surface before running anything:**

| Change Surface | Verification | Examples |
|---|---|---|
| **Style-only** (CSS classes, className props, Tailwind utilities) | Typecheck only | Adding `max-h-[85vh]`, changing colors, responsive tweaks |
| **Single-component logic** (state, handlers, props in one component) | Typecheck + targeted test file (if one exists) | Adding a form field, fixing a handler bug |
| **Cross-component / shared** (utils, hooks, context, API routes) | Typecheck + targeted test files + related integration tests | Refactoring a shared hook, changing an API response shape |
| **Full-stack / multi-story** (new features, schema changes, migrations) | Full test suite (`npm test`), typecheck, lint | New CRUD feature, auth changes, data model migration |

**Rules:**
- Default to the **lightest verification that covers the risk**. Err toward less, not more.
- Never run a multi-minute E2E suite for changes that don't touch logic, state, or data flow.
- Typecheck (`tsc --noEmit`) is always fast and always worth running — it's the universal baseline.
- If tests exist that directly exercise the changed component, run those specifically (`npx playwright test [file]`) rather than the full suite.

If integration failures: identify which story likely broke it, report to user.

#### Step 4.2: Auto-run verify-spec

Execute `/verify-spec` to confirm spec integrity, README sync, and story status consistency.

#### Step 4.3: Summary Report

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
- Run `/release` when ready to ship
- Run `/security-audit` for a security review
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
| `/verify-spec` | Auto-runs after spec completion |
| `/release` | Ship after spec is verified |
| `/status` | Shows progress of in-flight executions |
