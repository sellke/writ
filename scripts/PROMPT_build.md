# Ralph Build Iteration — PROMPT_build.md

> **Mode:** Build (single-story implementation)
> **State file:** .writ/state/ralph-{RALPH_STATE_ID}.json
> **Branch:** {RALPH_BRANCH}

You are executing a **single Ralph iteration**. Your job: pick the next eligible story, implement it through the CLI pipeline (code → test → lint → state update → commit), and exit. Fresh context — you have no memory of previous iterations.

---

## GUARDRAILS

```
GUARDRAILS: This iteration has exactly 1 story slot and 3 inner test-fix rounds.
If you cannot pass tests within 3 fix rounds, STOP, update state as failed, and EXIT.
Do NOT reorder the execution plan.
Do NOT attempt more than one story.
After successful commit + state write, EXIT immediately.
```

---

## Phase 0 — Orient

Before writing any code, understand the current state.

### 0.1 Read Ralph State

Read the active state file at `.writ/state/ralph-{RALPH_STATE_ID}.json`.

Extract:
- `plan.orderedStoryKeys` — the execution queue
- `stories` — per-story status and eligibility
- `iterations` — what has been attempted so far
- `escalations` — any active blockers
- `summary` — aggregate progress

### 0.2 Select Target Story

Pick the **first** `storyKey` in `plan.orderedStoryKeys` where:
1. `stories[storyKey].status` is `not-started` OR `attempted-failed`
2. `stories[storyKey].eligibility` is `eligible`
3. All entries in `stories[storyKey].dependsOn` have `status: "completed"`

If **no story qualifies**: set `summary.stopReason` to `"all-blocked"` or `"all-complete"` as appropriate, update `run.phase`, write state, and EXIT.

### 0.3 Load Story Context

1. Read the **story file** at `stories[storyKey].storyPath`:
   - Acceptance criteria — these define success
   - Implementation tasks — your work items
   - `## Context for Agents` — context hints (error maps, shadow paths, business rules)
   - Dependencies — what upstream stories produced

2. Read **spec-lite.md** for the story's spec (at `.writ/specs/{specId}/spec-lite.md`):
   - Extract the `## For Coding Agents` section only
   - This gives you the implementation approach, architecture, and key decisions

3. Read **technical-spec.md** if present (at `.writ/specs/{specId}/sub-specs/technical-spec.md`):
   - Schemas, formats, and contracts relevant to the story

4. Read **`.writ/config.md`** for project conventions:
   - `Test Runner` — the exact command to run tests
   - `Default Branch` — for git operations
   - Any Ralph-specific keys

5. Read **`AGENTS.md`** (or `CLAUDE.md` if present) for repo-level operational conventions.

6. If the story has dependencies with `status: "completed"`, check their story files for `## What Was Built` sections — these tell you what upstream work actually produced.

### 0.4 Mark In-Progress

Update `stories[storyKey].status` to `"in-progress"` and `stories[storyKey].phase` to `"orient"`. Write state file.

---

## Phase 1 — Implement

### 1.1 Plan Implementation

Review the story's implementation tasks. Follow them in order. If the story has acceptance criteria, ensure your implementation satisfies each one.

### 1.2 Write Code

Implement the story following established codebase patterns:
- Follow existing conventions (naming, structure, patterns)
- Write tests alongside implementation (TDD when the project supports it)
- Make small, logical changes
- Stay within the story's scope — do not fix unrelated issues

Update `stories[storyKey].phase` to `"implement"`.

### 1.3 Track Files Changed

Keep a list of all files you create or modify. This feeds into the state update.

---

## Phase 2 — Validate

### 2.1 Run Tests

```bash
{TEST_COMMAND}
```

If tests **pass**: proceed to 2.2.

If tests **fail**: enter the fix loop.

#### Fix Loop (max 3 iterations)

```
fix_attempt = 0
while tests fail AND fix_attempt < 3:
  1. Read test output — understand what failed
  2. Fix the implementation (prefer fixing code over changing tests)
  3. Re-run tests
  4. fix_attempt += 1
```

If tests still fail after 3 fix attempts:
- Set `stories[storyKey].status` to `"attempted-failed"`
- Set `stories[storyKey].lastError` to the test failure summary
- Set `stories[storyKey].fixLoopIterations` to 3
- Set `stories[storyKey].tests` to `"failed"`
- Append an iteration record with `result: "failed"`
- Write state file and **EXIT**

#### Environment vs. Code Failures

If test failure looks like an **environment issue** (not a code defect):
- Missing binary or tool
- Sandbox permission denied
- Database connection refused
- Node/Python/Rust not installed

Then classify as `environment-error`, append an escalation record, set `summary.stopReason` to `"environment-error"`, write state, and **EXIT**. Do not spin the fix loop on environment failures.

### 2.2 Run Lint / Typecheck

```bash
{LINT_COMMAND}
```

If lint/typecheck **passes**: proceed to Phase 3.

If lint/typecheck **fails**:
1. Auto-fix what's possible (formatter, auto-fixable lint rules)
2. Re-run checks
3. If still failing: treat as a fix-loop iteration (counts toward the 3-iteration cap)

Update `stories[storyKey].phase` to `"validate"`.

---

## Phase 3 — Update State and Commit

### 3.1 Update Story Record

```json
stories[storyKey] = {
  ...existing,
  "status": "completed",
  "phase": "commit",
  "lastCompletedAt": "{current ISO 8601}",
  "attemptCount": existing.attemptCount + 1,
  "fixLoopIterations": {actual count},
  "tests": "passed",
  "lint": "passed",
  "filesTouched": ["{list of files}"],
  "commitSha": "{will be set after commit}"
}
```

### 3.2 Append Iteration Record

```json
iterations.push({
  "iteration": summary.totalIterations + 1,
  "startedAt": "{iteration start ISO 8601}",
  "endedAt": "{now ISO 8601}",
  "durationSeconds": {elapsed},
  "storyKey": "{storyKey}",
  "result": "completed",
  "summary": "{one-line description of what was built}",
  "filesChanged": ["{list}"],
  "testCommand": "{TEST_COMMAND}",
  "testResult": "passed",
  "lintResult": "passed",
  "fixLoopIterations": {count},
  "commitSha": "{set after commit}"
})
```

### 3.3 Update Summary

```json
summary = {
  ...existing,
  "totalIterations": existing.totalIterations + 1,
  "completedStories": existing.completedStories + 1,
  "remainingEligible": {recompute from stories},
  "successRate": {recompute},
  "lastStoryKey": "{storyKey}"
}
```

### 3.4 Update Eligibility

After completing a story, re-evaluate eligibility for all `blocked-by-dependency` stories:
- If all `dependsOn` entries now have `status: "completed"`, set `eligibility` to `"eligible"`

### 3.5 Update Run Metadata

```json
run.lastUpdatedAt = "{now ISO 8601}"
run.phase = {all complete ? "complete" : "executing"}
```

### 3.6 Write "What Was Built"

Append a `## What Was Built` section to the story file with:
- Implementation date
- Files created/modified
- Implementation decisions
- Test results
- Review outcome (in CLI mode: tests + lint passed)

This enables downstream stories to understand what was actually produced.

### 3.7 Write State File

Write the complete updated state to `.writ/state/ralph-{RALPH_STATE_ID}.json`.

### 3.8 Git Commit

```bash
git add -A
git commit -m "ralph: complete {storyKey}

Story: {story title}
Files: {count} changed
Tests: passed
Lint: passed"
```

Update `stories[storyKey].commitSha` and the latest `iterations[]` entry's `commitSha` with the actual SHA.

Write state file again (with commit SHA populated).

### 3.9 Exit

You are done. **EXIT immediately.** The shell loop will restart with fresh context for the next iteration.

---

## Failure Protocol

| Situation | Action |
|-----------|--------|
| Tests fail after 3 fix attempts | Mark `attempted-failed`, record error, EXIT |
| Lint fails after fix attempts | Mark `attempted-failed`, record error, EXIT |
| Environment error (binary missing, permissions) | Mark `environment-error`, add escalation, EXIT |
| No eligible stories found | Set stop reason, EXIT |
| Story too large for context | Mark `attempted-failed` with `lastError: "context/size exceeded"`, EXIT |
| Merge conflict | Mark `attempted-failed` with `lastError: "merge conflict"`, EXIT |

**On any failure:** Do not leave the repository in a dirty state. If you've made changes that can't be committed:
```bash
git checkout -- .
git clean -fd
```

---

## Context Reference Checklist

| Artifact | Where | What to Extract |
|----------|-------|-----------------|
| Ralph state | `.writ/state/ralph-*.json` | Plan, story statuses, iterations |
| Story file | Path from `stories[storyKey].storyPath` | AC, tasks, context hints, dependencies |
| Spec-lite | `.writ/specs/{specId}/spec-lite.md` | `## For Coding Agents` section |
| Technical spec | `.writ/specs/{specId}/sub-specs/technical-spec.md` | Schemas, contracts |
| Config | `.writ/config.md` | Test Runner, Default Branch, Ralph keys |
| Repo conventions | `AGENTS.md` or `CLAUDE.md` | Operational context |
| Upstream WWB | Dependency story files → `## What Was Built` | What upstream stories produced |
