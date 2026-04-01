# Ralph CLI Pipeline Reference

> Purpose: Documents how the CLI story pipeline works — gate mapping to Cursor, back pressure mechanics, fix loop behavior, state update protocol, and context consumption.

## Pipeline Overview

The CLI pipeline is an autonomous version of Writ's Cursor-native `/implement-story` pipeline (see `commands/implement-story.md` for the full 9-gate Cursor version). State updates follow the schema in `.writ/docs/ralph-state-format.md`. It runs one story per Ralph iteration through five phases — orient, implement, validate, review (sub-agent), and commit — with test/lint and review back pressure.

```
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌───────────┐   ┌─────────────────┐
│ Phase 0 │──▶│ Phase 1 │──▶│ Phase 2 │──▶│Phase 2.5  │──▶│    Phase 3      │
│ ORIENT  │   │IMPLEMENT│   │VALIDATE │   │  REVIEW   │   │ STATE + COMMIT  │
│         │   │         │   │         │   │(sub-agent)│   │                 │
│ Read    │   │ Code    │   │ Test    │   │ AC verify │   │ Update JSON     │
│ state,  │   │ the     │   │ + Lint  │   │ Quality   │   │ Write WWB       │
│ story,  │   │ story   │   │ + Fix   │   │ Drift     │   │ git commit      │
│ spec    │   │         │   │ loop    │   │ Security  │   │ EXIT            │
└─────────┘   └─────────┘   └─────────┘   └───────────┘   └─────────────────┘
                                │               │
                           fail after 3?   FAIL (max 2)?
                                │          PAUSE (drift)?
                           mark failed,         │
                           EXIT            mark failed,
                                           EXIT
```

## Gate Mapping: Cursor vs. CLI

| Cursor Gate | CLI Phase | Differences |
|-------------|-----------|-------------|
| **Gate 0: Arch Check** (read-only subagent) | Phase 0: Orient | CLI loads context and self-assesses; no separate architecture agent. Risk is managed by single-story scope and dependency ordering. |
| **Gate 0.5: Boundary Map** (inline) | — (not in CLI) | CLI relies on story task lists for scope. No boundary enforcement — story isolation provides implicit boundaries. |
| **Gate 1: Coding Agent** (TDD, worktree) | Phase 1: Implement | Same goal (implement story tasks). CLI agent does this inline rather than delegating to a subagent. No worktree isolation. |
| **Gate 2: Lint & Typecheck** (inline) | Phase 2: Validate | Equivalent — runs same commands from `.writ/config.md`. |
| **Gate 3: Review Agent** (read-only subagent) | Phase 2.5: Review | **Read-only review sub-agent** spawned by CLI agent. Verifies AC, code quality, security, and spec drift. Same PASS/FAIL/PAUSE contract. Max 2 review iterations (vs Cursor's 3 shared with visual QA). |
| **Gate 3.5: Drift Response** (inline) | Phase 2.5: Review | Drift analysis performed by the review sub-agent. Small/Medium drift → PASS with record. Large drift → PAUSE → mark failed and escalate (no human prompt in CLI). |
| **Gate 4: Testing Agent** (coverage enforcement) | Phase 2: Validate | Tests run in Phase 2. Coverage enforcement is project-dependent (from config). No separate testing agent. |
| **Gate 4.5: Visual QA** (optional subagent) | — (not in CLI) | Visual QA requires browser — not available in headless CLI. |
| **Gate 5: Documentation Agent** (adaptive docs) | — (not in CLI) | Documentation deferred to developer review. Story's `## What Was Built` (enriched by review sub-agent data) serves as the primary record. |

### Quality Parity

The CLI pipeline uses sub-agents to maintain review quality while trading architecture checks and documentation for throughput:

| Quality Mechanism | Cursor | CLI | Parity |
|-------------------|--------|-----|--------|
| Tests pass | ✅ Gate 4 | ✅ Phase 2 | Full |
| Lint/typecheck pass | ✅ Gate 2 | ✅ Phase 2 | Full |
| Acceptance criteria verified | Review agent (Gate 3) | Review sub-agent (Phase 2.5) | Full |
| Code review | Dedicated agent (Gate 3) | Read-only sub-agent (Phase 2.5) | Near-full |
| Drift detection | Gate 3.5 automated | Review sub-agent (Phase 2.5) | Near-full |
| Security scan | Review agent (Gate 3) | Review sub-agent (Phase 2.5) | Near-full |
| Coverage enforcement | ≥80% mandatory (Gate 4) | Project-dependent | Variable |
| Architecture check | Dedicated agent (Gate 0) | Omitted — single-story scope | Reduced |
| Boundary enforcement | Gate 0.5 computed | Omitted — implicit via story scope | Reduced |
| Visual QA | Optional agent (Gate 4.5) | Omitted — headless CLI | N/A |
| Documentation | Dedicated agent (Gate 5) | Deferred — WWB record only | Reduced |

**Near-full** means the same categories are checked by a sub-agent, but without Cursor's dedicated multi-agent depth (e.g., no boundary compliance cross-check, no change surface classification tuning review depth). The review sub-agent receives the same spec-lite review section and acceptance criteria as the Cursor review agent.

## Back Pressure

Back pressure keeps the CLI pipeline from producing broken code. Three mechanisms:

### Test Back Pressure

Tests are the primary quality gate. The CLI agent runs the project's test command (from `.writ/config.md` `Test Runner` or detected at orient time) after implementation.

```
if tests fail:
  fix_attempt = 0
  while fix_attempt < 3:
    analyze failure → fix code → re-run tests
    fix_attempt++
  if still failing: mark failed, EXIT
```

The fix loop cap (3 iterations) prevents infinite retries and wasted context.

### Lint/Typecheck Back Pressure

After tests pass, lint and typecheck run. Auto-fixable issues are resolved automatically. Non-auto-fixable failures count toward the fix loop cap.

Treat typecheck as part of "lint" when `.writ/config.md` defines it that way. The PROMPT instructs the agent to run the **exact** commands from config — no invented shortcuts.

### Review Back Pressure

After tests and lint pass, a **read-only review sub-agent** verifies the implementation against the spec contract. The review sub-agent checks acceptance criteria, code quality, security, and spec drift.

```
if review FAIL:
  review_iteration = 0
  while review_iteration < 2:
    parse issues → fix code → re-run tests/lint → re-review
    review_iteration++
  if still FAIL: mark failed, EXIT

if review PAUSE (Large drift):
  mark failed, add escalation, EXIT
```

The review retry cap (2) is separate from the test/lint fix loop cap (3). A story that passes tests but fails review gets 2 fix-and-re-review attempts (3 total reviews: 1 initial + 2 retries). This matches Cursor's 3-iteration cap for Gate 3. Large drift is non-recoverable in autonomous mode — the code is committed to a quarantine branch and the developer resolves it in Cursor via `/ralph status`.

## Fix Loop

| Parameter | Value |
|-----------|-------|
| Test/lint fix loop max | 3 |
| Review retries max | 2 (3 total reviews: 1 initial + 2 retries) |
| Test/lint scope | Tests + lint combined |
| Review scope | AC verification, code quality, security, drift |
| On test/lint exhaustion | Mark story `attempted-failed`, record diagnostics, EXIT |
| On review exhaustion | Mark story `attempted-failed` with `lastError: "review-failed"`, EXIT |
| On Large drift | Mark story `attempted-failed` with `lastError: "large-drift"`, add escalation, EXIT |
| Fix strategy | Prefer fixing implementation over changing tests |

### Environment vs. Code Failures

The fix loop should **not** spin on environment failures. Heuristics for environment detection:

| Signal | Classification |
|--------|---------------|
| Binary not found (e.g. `jest: command not found`) | Environment |
| Permission denied on file/socket | Environment |
| Database connection refused | Environment |
| Network timeout (dependency fetch) | Environment |
| Import/module not found (installed dep) | Environment |
| Test assertion failure | Code defect |
| Type error in source code | Code defect |
| Lint rule violation | Code defect |
| Runtime exception in application code | Code defect |

On environment failure: classify as `environment-error`, add an escalation record to state, and EXIT. Do not retry — the environment needs human intervention.

## State Update Protocol

The CLI agent updates `ralph-*.json` at specific points during each iteration. Updates are full file writes (read → modify → write) — not patches.

### When to Write State

| Event | What Changes |
|-------|-------------|
| Story selected (Phase 0) | `stories[key].status` → `"in-progress"`, `.phase` → `"orient"` |
| Implementation starts (Phase 1) | `stories[key].phase` → `"implement"` |
| Validation starts (Phase 2) | `stories[key].phase` → `"validate"` |
| Review starts (Phase 2.5) | `stories[key].phase` → `"review"` |
| Story completes (Phase 3) | Full update: status, phase, tests, lint, reviewResult, drift, acVerified, files, commit SHA |
| Story fails (tests/lint) | `stories[key].status` → `"attempted-failed"`, error details |
| Story fails (review) | `stories[key].status` → `"attempted-failed"`, `.reviewResult` → `"failed"`, error details |
| Large drift detected | `stories[key].status` → `"attempted-failed"`, `.drift` → `"large"`, escalation record |
| Environment error | Escalation record + `summary.stopReason` |

### Atomicity

State writes are not atomic (no filesystem transactions). If the process crashes mid-write:
- The state file may be corrupted or partially written
- On next iteration, `ralph.sh` detects and handles (fall back to git state + spec state to reconstruct)
- `in-progress` status on a story with no matching running process indicates a crash — eligible for retry

### Merging with State File

The CLI agent **reads** the full state file at the start of each iteration and **writes** the full file on each update. It does not merge — it owns the current state for its iteration duration. Concurrent writes are prevented by the outer loop being sequential.

### Success Path

```
1. Read state → select story → write state (in-progress)
2. Implement story
3. Run tests + lint → pass
4. Spawn review sub-agent → PASS (or fix → re-review, max 2 iterations)
5. Update stories[key] (completed, with review data), append iterations[], update summary
6. Append "What Was Built" to story file (enriched with review sub-agent data)
7. Write state
8. git add + commit
9. Update commitSha in state
10. Write state (final)
11. EXIT
```

### Failure Paths

**Test/lint failure:**
```
1. Read state → select story → write state (in-progress)
2. Implement story
3. Run tests → fail → fix loop (3 attempts) → still failing
4. Update stories[key] (attempted-failed), append iterations[] (failed), update summary
5. Write state
6. git checkout -- . && git clean -fd  (clean up partial changes)
7. EXIT
```

**Review failure:**
```
1. Read state → select story → write state (in-progress)
2. Implement story
3. Run tests + lint → pass
4. Spawn review sub-agent → FAIL → fix → re-review → still FAIL (2 iterations)
5. Update stories[key] (attempted-failed, reviewResult: "failed"), append iterations[], update summary
6. Write state
7. git checkout -- . && git clean -fd
8. EXIT
```

**Large drift:**
```
1-3. Same as above
4. Spawn review sub-agent → PAUSE (Large drift detected)
5. Commit to quarantine branch (ralph/quarantine/{storyKey}) — preserves working code
6. Return to original branch
7. Update stories[key] (attempted-failed, drift: "large", quarantineBranch), append escalation (type: "drift")
8. Write state
9. EXIT
```

## Context Engine Consumption (CLI Mode)

The CLI pipeline consumes Phase 3a Context Engine artifacts differently from Cursor:

| Artifact | Cursor Consumption | CLI Consumption |
|----------|-------------------|-----------------|
| `spec-lite.md` | Agent-specific sections routed to each gate agent | `## For Coding Agents` section loaded in Phase 0 |
| Context hints | Parsed, fetched from source files, routed per category | Loaded from story file `## Context for Agents`; agent reads referenced sections inline |
| "What Was Built" | Loaded from dependency stories, passed to coding agent | Same — loaded in Phase 0.3 from dependency story files |
| Technical spec | Loaded as supplementary context per gate | Loaded in Phase 0.3 if present |

The key difference: Cursor has multiple agents receiving tailored context slices. CLI has one agent loading everything relevant upfront.

## Story Sizing and Context Window

Each Ralph iteration runs one story in a single CLI agent context window. Stories that exceed the context window will fail — the agent cannot complete them.

### Sizing Guidance

| Metric | Safe | Risky | Likely to Fail |
|--------|------|-------|---------------|
| Tasks | ≤5 | 6–7 | 8+ |
| Files in scope | ≤8 | 9–12 | 13+ |
| AC count | ≤5 | 6–8 | 9+ |

`/ralph plan` flags oversized stories with `complexity: "XL"` and `complexitySignals.flags: ["context-risk"]`. Consider splitting these before CLI execution.

### What to Do if a Story is Too Large

If the CLI agent cannot complete a story within its context window:
1. Mark `attempted-failed` with `lastError: "context/size exceeded"`
2. The developer sees this in `/ralph status` and can split the story via `/edit-spec`
3. Re-run `/ralph plan` to regenerate the queue with smaller stories

## Commit Message Convention

CLI pipeline commits use a consistent format for git log readability:

```
ralph: complete {specId}::{storySlug}

Story: {story title}
Files: {N} changed
Tests: passed
Review: passed ({N}/{M} AC verified, drift: {level})
Lint: passed
```

This pattern enables `/ralph status` to optionally correlate commits with state records.
