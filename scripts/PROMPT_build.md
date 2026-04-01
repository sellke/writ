# Ralph Build Iteration — PROMPT_build.md

> **Mode:** Build (single-story implementation)
> **State file:** .writ/state/ralph-{RALPH_STATE_ID}.json
> **Branch:** {RALPH_BRANCH}

You are executing a **single Ralph iteration**. Your job: pick the next eligible story, implement it through the CLI pipeline (code → test → lint → review → state update → commit), and exit. Fresh context — you have no memory of previous iterations.

---

## GUARDRAILS

```
GUARDRAILS: This iteration has exactly 1 story slot, 3 inner test-fix rounds, and 2 review retries.
If you cannot pass tests within 3 fix rounds, STOP, update state as failed, and EXIT.
If review fails, you get 2 fix-and-re-review attempts. After 3 total reviews (1 initial + 2 retries) with no PASS, STOP and EXIT.
If review detects Large drift, STOP, update state as failed, and EXIT.
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
   - Extract the `## For Coding Agents` section — implementation approach, architecture, key decisions
   - Also extract the `## For Review Agents` section — acceptance criteria focus, business rules, experience design (feeds Phase 2.5)
   - If no agent-specific sections exist (legacy spec), store the full spec-lite content for both

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

If lint/typecheck **passes**: proceed to Phase 2.5 (Review).

If lint/typecheck **fails**:
1. Auto-fix what's possible (formatter, auto-fixable lint rules)
2. Re-run checks
3. If still failing: treat as a fix-loop iteration (counts toward the 3-iteration cap)

Update `stories[storyKey].phase` to `"validate"`.

---

## Phase 2.5 — Review

After tests and lint pass, spawn a **read-only review sub-agent** to verify the implementation meets spec requirements. This is the primary quality gate — tests prove the code runs, review proves the code is *right*.

Update `stories[storyKey].phase` to `"review"` before proceeding. This ensures crash recovery can distinguish a review-phase crash from a validate-phase crash.

### 2.5.1 Prepare Review Context

Gather the following for the review sub-agent:

1. **Acceptance criteria** — from the story file (loaded in Phase 0.3)
2. **Spec-lite review section** — the `## For Review Agents` section extracted in Phase 0.3 (or full spec-lite if section not available)
3. **Code changes** — stage all changes, then diff:
   ```bash
   git add -A
   git diff --cached HEAD
   ```
   This captures both modifications to existing files AND newly created files. Without staging, `git diff HEAD` misses untracked files — which are often the majority of a story's implementation. After review completes, the staged state carries forward to Phase 3's commit.
4. **Test results** — pass/fail summary and coverage output from Phase 2
5. **Implementation summary** — your own summary of what you built: files created/modified, decisions made, any deviations from the task list

### 2.5.2 Spawn Review Sub-Agent

Delegate to a **read-only** review sub-agent. Use the `writ-reviewer` agent if available in `.claude/agents/`, otherwise spawn an inline sub-agent. The sub-agent MUST NOT modify any files.

**Sub-agent prompt (pass all gathered context):**

```
You are the Review Agent for a Ralph CLI iteration. You verify that an implementation meets its spec contract before the story is marked complete.

## Story Acceptance Criteria

{acceptance_criteria from story file}

## Spec Contract (for Drift Analysis)

{spec-lite review section}

## Code Changes

{git diff output}

## Test Results

{test/lint output summary}

## Implementation Summary

{your implementation summary}

## Review Categories

### 1. Acceptance Criteria Verification (primary gate)
Walk through EACH acceptance criterion. For each one:
- State the criterion
- Identify the code/test that satisfies it
- Mark VERIFIED or UNVERIFIED
- If UNVERIFIED, explain what is missing

Every criterion must map to working code and a passing test. A single UNVERIFIED criterion means FAIL.

### 2. Code Quality
Pattern consistency with existing codebase. Proper error handling (no swallowed errors, no bare catch). No debug artifacts (console.log, commented-out code). Reasonable function size and single responsibility.

### 3. Security
Input validation, parameterized queries, injection prevention, auth checks, no hardcoded secrets, sensitive data not in logs. Security issues are always Major or Critical — never Minor.

### 4. Test Coverage
Tests for all acceptance criteria. Error/failure paths covered. Edge cases (empty, null, boundary). No vacuous assertions. Mocks are appropriate.

### 5. Drift Analysis
Compare the implementation against the Spec Contract. For each deviation:

- **Small** (naming, cosmetic — spec intent preserved): note it, propose spec amendment
- **Medium** (scope/integration impact — spec intent met with notable changes): flag with ⚠️
- **Large** (fundamental deviation — spec intent NOT met or constraints violated): PAUSE

When severity is ambiguous → default to Medium.

## Output Format (STRICT — follow exactly)

### REVIEW_RESULT: [PASS/FAIL/PAUSE]

### AC Verification
- [ ] or [x] {criterion} — {evidence or gap}
(one line per criterion)

**Verified: {N}/{M}**

### Summary
[2-3 sentence review summary]

### Security Assessment
**Risk Level:** [Clean/Low/Medium/High]
[Brief findings if any]

### Issues Found (if FAIL)
For each issue:
- **Issue:** [specific description]
- **Location:** [file path and line if applicable]
- **Severity:** [Critical/Major/Minor]
- **Suggested Fix:** [concrete steps]

### Drift Analysis
**Overall Drift:** [None/Small/Medium/Large]

[If deviations found, for each:]
#### [DEV-001] [Brief description]
- **Severity:** Small / Medium / Large
- **Spec said:** [what the spec expected]
- **Implementation did:** [what actually happened]
- **Resolution:** Auto-amend proposed / Flagged for review / Pipeline paused
```

### 2.5.3 Handle Review Result

Parse the sub-agent's output. Extract `REVIEW_RESULT`, `AC Verification` counts, `Drift Analysis`, and any issues.

**PASS** → Proceed to Phase 3. Store the full review output for "What Was Built" extraction.

**FAIL** → Enter the review fix loop:

```
review_iteration = 0
while REVIEW_RESULT == FAIL AND review_iteration < 2:
  1. Parse issues from review output (Critical and Major first)
  2. Fix the implementation
  3. Re-run tests + lint (Phase 2 validation — must still pass)
     If tests/lint fail: apply the standard Phase 2 fix loop (max 3 attempts).
     If tests cannot be fixed: mark story attempted-failed with
     lastError: "review-fix-broke-tests: {test failure summary}", EXIT.
  4. Re-stage changes: git add -A
  5. Re-gather review context (updated cached diff, summary)
  6. Re-spawn review sub-agent
  review_iteration += 1

if still FAIL after 2 review iterations:
  Mark stories[storyKey].status = "attempted-failed"
  Set stories[storyKey].lastError = "review-failed: {summary of unresolved issues}"
  Set stories[storyKey].reviewResult = "failed"
  Set stories[storyKey].reviewIterations = 2
  Append iteration record with result: "failed"
  Write state file, clean working tree, EXIT
```

**PAUSE** (Large drift detected) → Cannot resolve autonomously. Preserve the working code for developer inspection.
- Commit to a quarantine branch so the implementation is preserved:
  ```bash
  git checkout -b ralph/quarantine/{storyKey}
  git add -A
  git commit -m "ralph: quarantine {storyKey} — large drift detected

  Drift: {DEV-ID and description}
  Tests: passed, Lint: passed
  Quarantined for developer review — implementation works but deviates from spec."
  git checkout -    # return to the original branch
  ```
- Mark `stories[storyKey].status` = `"attempted-failed"`
- Set `stories[storyKey].lastError` = `"large-drift: {DEV-ID and description}"`
- Set `stories[storyKey].reviewResult` = `"paused"`
- Set `stories[storyKey].drift` = `"large"`
- Set `stories[storyKey].quarantineBranch` = `"ralph/quarantine/{storyKey}"`
- Append escalation record with `type: "drift"` and the deviation details (include quarantine branch name)
- Write state file, **EXIT**

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
  "reviewIterations": {actual review iteration count},
  "reviewResult": "passed",
  "tests": "passed",
  "lint": "passed",
  "drift": "{from review: none|small|medium}",
  "acVerified": "{N}/{M} from review AC Verification",
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
  "reviewResult": "passed",
  "drift": "{from review: none|small|medium}",
  "acVerified": "{N}/{M}",
  "fixLoopIterations": {count},
  "reviewIterations": {count},
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

Append a `## What Was Built` section to the story file. The Review Outcome and Deviations sections are sourced from the **review sub-agent output** (Phase 2.5) — third-party verified. Files and decisions come from your own implementation summary.

```markdown
---

## What Was Built

**Implementation Date:** {current date YYYY-MM-DD}

### Files Created
{list files you created, with one-line descriptions}

### Files Modified
{list files you modified, with change summaries}

### Implementation Decisions
{key decisions made during implementation — approach choices, trade-offs}

### Test Results
**Verification:** {test runner}: {pass count} passing
**Coverage:** {coverage % if available}

### Review Outcome
**Result:** PASS
- **Review iterations:** {count}
- **Drift:** {from review sub-agent: None/Small/Medium}
- **Security:** {from review sub-agent: Clean/Low/Medium/High}
- **AC Verified:** {N}/{M} acceptance criteria verified

### Deviations from Spec
{From review sub-agent drift analysis. If None: "None"}
{If deviations found, include DEV-IDs and descriptions from review output}
```

This enables downstream stories to understand what was actually produced, with review-verified data.

### 3.7 Write State File

Write the complete updated state to `.writ/state/ralph-{RALPH_STATE_ID}.json`.

### 3.8 Git Commit

```bash
git add -A
git commit -m "ralph: complete {storyKey}

Story: {story title}
Files: {count} changed
Tests: passed
Review: passed ({N}/{M} AC verified, drift: {none|small|medium})
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
| Review FAIL after 2 iterations | Mark `attempted-failed` with `lastError: "review-failed: {issues}"`, EXIT |
| Review PAUSE (Large drift) | Mark `attempted-failed` with `lastError: "large-drift: {description}"`, quarantine branch, add escalation, EXIT |
| Review sub-agent crash or unparseable output | Retry once. If retry fails, mark `attempted-failed` with `lastError: "review-agent-error"`, EXIT |
| Tests break during review fix | Apply Phase 2 fix loop (max 3). If unfixable, mark `attempted-failed` with `lastError: "review-fix-broke-tests"`, EXIT |
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
| Spec-lite (coding) | `.writ/specs/{specId}/spec-lite.md` | `## For Coding Agents` section |
| Spec-lite (review) | `.writ/specs/{specId}/spec-lite.md` | `## For Review Agents` section (feeds Phase 2.5) |
| Technical spec | `.writ/specs/{specId}/sub-specs/technical-spec.md` | Schemas, contracts |
| Config | `.writ/config.md` | Test Runner, Default Branch, Ralph keys |
| Repo conventions | `AGENTS.md` or `CLAUDE.md` | Operational context |
| Upstream WWB | Dependency story files → `## What Was Built` | What upstream stories produced |
