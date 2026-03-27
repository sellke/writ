# Ralph CLI Pipeline Reference

> Purpose: Documents how the CLI story pipeline works — gate mapping to Cursor, back pressure mechanics, fix loop behavior, state update protocol, and context consumption.

## Pipeline Overview

The CLI pipeline is a simplified, autonomous version of Writ's Cursor-native `/implement-story` pipeline (see `commands/implement-story.md` for the full 9-gate Cursor version). State updates follow the schema in `.writ/docs/ralph-state-format.md`. It runs one story per Ralph iteration through four phases with test/lint back pressure.

```
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────────────┐
│ Phase 0 │──▶│ Phase 1 │──▶│ Phase 2 │──▶│    Phase 3      │
│ ORIENT  │   │IMPLEMENT│   │VALIDATE │   │ STATE + COMMIT  │
│         │   │         │   │         │   │                 │
│ Read    │   │ Code    │   │ Test    │   │ Update JSON     │
│ state,  │   │ the     │   │ + Lint  │   │ Write WWB       │
│ story,  │   │ story   │   │ + Fix   │   │ git commit      │
│ spec    │   │         │   │ loop    │   │ EXIT            │
└─────────┘   └─────────┘   └─────────┘   └─────────────────┘
                                │
                           fail after 3?
                                │
                           mark failed,
                           EXIT
```

## Gate Mapping: Cursor vs. CLI

| Cursor Gate | CLI Phase | Differences |
|-------------|-----------|-------------|
| **Gate 0: Arch Check** (read-only subagent) | Phase 0: Orient | CLI loads context and self-assesses; no separate architecture agent. Risk is managed by single-story scope and dependency ordering. |
| **Gate 0.5: Boundary Map** (inline) | — (not in CLI) | CLI relies on story task lists for scope. No boundary enforcement — story isolation provides implicit boundaries. |
| **Gate 1: Coding Agent** (TDD, worktree) | Phase 1: Implement | Same goal (implement story tasks). CLI agent does this inline rather than delegating to a subagent. No worktree isolation. |
| **Gate 2: Lint & Typecheck** (inline) | Phase 2: Validate | Equivalent — runs same commands from `.writ/config.md`. |
| **Gate 3: Review Agent** (read-only subagent) | — (not in CLI v1) | CLI relies on test + lint back pressure instead of a separate review agent. Developer reviews in Cursor after loop completes. |
| **Gate 3.5: Drift Response** (inline) | — (not in CLI v1) | Drift detection deferred to developer review in Cursor. |
| **Gate 4: Testing Agent** (coverage enforcement) | Phase 2: Validate | Tests run in Phase 2. Coverage enforcement is project-dependent (from config). No separate testing agent. |
| **Gate 4.5: Visual QA** (optional subagent) | — (not in CLI) | Visual QA requires browser — not available in headless CLI. |
| **Gate 5: Documentation Agent** (adaptive docs) | — (not in CLI v1) | Documentation deferred to developer review. Story's `## What Was Built` serves as the primary record. |

### Quality Parity

The CLI pipeline intentionally trades review depth for throughput:

| Quality Mechanism | Cursor | CLI | Parity |
|-------------------|--------|-----|--------|
| Tests pass | ✅ | ✅ | Full |
| Lint/typecheck pass | ✅ | ✅ | Full |
| Acceptance criteria checked | Agent verifies | Agent verifies | Similar |
| Code review | Dedicated agent | Deferred | Reduced |
| Drift detection | Automated | Deferred | Reduced |
| Coverage enforcement | ≥80% mandatory | Project-dependent | Variable |
| Documentation | Automated | WWB only | Reduced |

This is by design — autonomous mode prioritizes coverage over perfection. Developer reviews output in Cursor before merging.

## Back Pressure

Back pressure keeps the CLI pipeline from producing broken code. Two mechanisms:

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

## Fix Loop

| Parameter | Value |
|-----------|-------|
| Max iterations | 3 |
| Scope | Tests + lint combined |
| On exhaustion | Mark story `attempted-failed`, record diagnostics, EXIT |
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
| Story completes (Phase 3) | Full update: status, phase, tests, lint, files, commit SHA |
| Story fails | `stories[key].status` → `"attempted-failed"`, error details |
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
4. Update stories[key] (completed), append iterations[], update summary
5. Append "What Was Built" to story file
6. Write state
7. git add + commit
8. Update commitSha in state
9. Write state (final)
10. EXIT
```

### Failure Path

```
1. Read state → select story → write state (in-progress)
2. Implement story
3. Run tests → fail → fix loop (3 attempts) → still failing
4. Update stories[key] (attempted-failed), append iterations[] (failed), update summary
5. Write state
6. git checkout -- . && git clean -fd  (clean up partial changes)
7. EXIT
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
Lint: passed
```

This pattern enables `/ralph status` to optionally correlate commits with state records.
