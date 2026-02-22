# Implement Story Command (implement-story)

## Overview

The primary execution command for Writ. Orchestrates the full SDLC pipeline for one story, multiple stories, or an entire specification using coordinated sub-agents with quality gates, feedback loops, and parallel execution.

## Modes

| Invocation | Mode | Behavior |
|---|---|---|
| `/implement-story` | Interactive | Presents story/spec selection |
| `/implement-story story-3` | Single story | Runs one story through the full pipeline |
| `/implement-story --all` | Full spec | Runs ALL stories with dependency resolution + parallelism |
| `/implement-story --from story-3` | Partial spec | Runs story 3 and all subsequent stories |
| `/implement-story --quick story-3` | Quick mode | Skips review + docs phases (prototyping) |

## Agent Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION AGENT                           │
│         (Dependency graph, parallel dispatch, gates)             │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼ Per story (parallel when independent)
┌─────────────────────────────────────────────────────────────────┐
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌─────────────┐ │
│  │ARCH CHECK│──▶│  CODING  │──▶│  LINT &  │──▶│   REVIEW    │ │
│  │  AGENT   │   │  AGENT   │   │TYPECHECK │   │   AGENT     │ │
│  │(pre-impl)│   │  (TDD)   │   │  (gate)  │   │(quality gate│ │
│  └──────────┘   └──────────┘   └──────────┘   └─────────────┘ │
│       │              ▲              │               │           │
│       │ ABORT?       │ fix          │ fail?         │           │
│       ▼              └──────────────┘               ▼           │
│                                              ┌─────────────┐   │
│                                   ┌──PASS───▶│  TESTING    │   │
│                                   │          │   AGENT     │   │
│                           FAIL────┘          │(+coverage)  │   │
│                           (max 3×)           └─────────────┘   │
│                                                     │          │
│                                                     ▼          │
│                                              ┌─────────────┐   │
│                                              │    DOCS      │   │
│                                              │   AGENT      │   │
│                                              │(adaptive)    │   │
│                                              └─────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Command Process

### Phase 0: Spec & Story Selection

#### Step 0.1: Discovery

**If no arguments provided, use AskQuestion:**
```
AskQuestion({
  title: "Implementation Target",
  questions: [
    {
      id: "mode",
      prompt: "What would you like to implement?",
      options: [
        { id: "single", label: "A single user story" },
        { id: "all", label: "All stories in a spec (full execution)" },
        { id: "remaining", label: "All remaining (not-started) stories in a spec" }
      ]
    }
  ]
})
```

Then present spec/story selection as appropriate.

#### Step 0.2: Load Spec Context

1. **Read spec files:** `spec.md`, `spec-lite.md`, `user-stories/README.md`
2. **Read all story files:** Parse status, dependencies, task counts
3. **Build dependency graph** from story dependency declarations
4. **Identify execution plan:**
   - Which stories to run (based on mode)
   - Which can run in parallel (no mutual dependencies)
   - Which must be sequenced (dependency chains)

**Present execution plan to user:**
```
## Execution Plan: 2026-02-22-feature-name

Stories to implement: 5

  Parallel batch 1:
    ├── Story 1: User Authentication (7 tasks) — no dependencies
    └── Story 3: API Endpoints (5 tasks) — no dependencies

  Parallel batch 2 (after batch 1):
    ├── Story 2: Session Management (6 tasks) — depends on Story 1
    └── Story 4: Rate Limiting (4 tasks) — depends on Story 3

  Sequential (after batch 2):
    └── Story 5: Integration Tests (5 tasks) — depends on Stories 2, 4

Estimated phases per story: arch-check → code → lint → review → test → docs
```

Then confirm:
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
        { id: "quick", label: "Execute in quick mode (skip review + docs)" }
      ]
    }
  ]
})
```

#### Step 0.3: Initialize State

```json
// .writ/state/execution-{timestamp}.json
{
  "spec": "2026-02-22-feature-name",
  "mode": "all",
  "startedAt": "2026-02-22T17:40:00Z",
  "plan": {
    "batches": [
      { "parallel": true, "stories": ["story-1-auth", "story-3-api"] },
      { "parallel": true, "stories": ["story-2-session", "story-4-rate-limit"] },
      { "parallel": false, "stories": ["story-5-integration"] }
    ]
  },
  "stories": {
    "story-1-auth": { "status": "pending", "phase": null },
    "story-3-api": { "status": "pending", "phase": null }
  }
}
```

### Phase 1: Per-Story Pipeline

For each story (run in parallel within batches, sequenced across batches):

---

#### Gate 0: Pre-Implementation Architecture Check

> **Agent Reference:** See `agents/architecture-check-agent.md`

**Purpose:** Catch design-level issues BEFORE any code is written. Cheaper to fix an approach than to fix an implementation.

```
Task({
  subagent_type: "generalPurpose",
  readonly: true,
  description: "Architecture pre-check for story N",
  prompt: `You are the Architecture Check Agent.

## Your Mission
Review the planned implementation approach for this story and flag any structural concerns BEFORE coding begins.

## Story Details
**Story file:** {story_file_path}
**Story content:** {full_story_content}

## Specification Context
{spec_lite_content}

## Current Codebase Analysis
**Architecture patterns found:** {codebase_patterns}
**Related existing code:** {related_files}
**Tech stack:** {tech_stack_content}

## Review Checklist

### 1. Approach Viability
- Does the story's task list make technical sense?
- Are there architectural patterns in the codebase this should follow?
- Will this approach scale appropriately?

### 2. Integration Risk
- Could this break existing functionality?
- Are there hidden dependencies not listed in the story?
- Does this touch shared code (auth, database, core utils)?

### 3. Complexity Assessment
- Are any tasks underestimated (should be split)?
- Are there simpler approaches worth considering?
- Any premature optimization or over-engineering?

### 4. Missing Considerations
- Error handling gaps?
- Migration needs?
- Environment/config changes required?

## Output Format

### ARCH_CHECK: [PROCEED/CAUTION/ABORT]

### Summary
[2-3 sentence assessment]

### Findings
- **Finding:** [description]
  **Risk:** [Low/Medium/High]
  **Recommendation:** [what to do]

### Suggested Modifications to Tasks (if any)
- Task N.X: [suggested change and why]

### Proceed with caution if:
[List any areas the coding agent should be especially careful about]
`
})
```

**Processing results:**
- **PROCEED** → Continue to coding phase
- **CAUTION** → Continue, but inject findings into coding agent prompt as warnings
- **ABORT** → Present findings to user, ask whether to proceed, modify story, or skip

---

#### Gate 1: Coding Agent

> **Agent Reference:** See `agents/coding-agent.md`

Launch the coding agent with full context + any architecture check warnings:

```
Task({
  subagent_type: "generalPurpose",
  description: "Implement story N code",
  prompt: `You are the Coding Agent for story implementation.

## Your Mission
Implement the code changes for the following user story, following TDD principles.

## Story Details
**Story file path:** {story_file_path}
**Story content:** {full_story_content}

## Specification Context
**Spec summary:** {spec_lite_content}
**Technical approach:** {technical_spec_summary}

## Codebase Context
**Relevant patterns found:** {codebase_patterns}
**Related files:** {related_files}

${arch_check_warnings ? `
## ⚠️ Architecture Check Warnings
The architecture review flagged these concerns. Address them during implementation:
${arch_check_findings}
` : ''}

## Implementation Requirements
1. **Follow TDD**: Write tests FIRST, then implement to make them pass
2. **Match patterns**: Follow existing codebase conventions
3. **Small commits**: Make logical, incremental changes
4. **Document as you go**: Add inline comments for complex logic

## Tasks to Complete
{story_implementation_tasks}

## Acceptance Criteria to Satisfy
{story_acceptance_criteria}

## Output Requirements
When complete, provide a summary:
- Files created/modified (with brief description of changes)
- Tests written (file paths and test names)
- Any deviations from the plan and why
- Any concerns or areas needing review attention

Do NOT mark the story as complete - the review and testing phases will handle that.
`
})
```

---

#### Gate 2: Lint, Typecheck & Format

**This gate runs inline (no sub-agent needed) — fast, deterministic.**

The orchestrator runs linting/typechecking directly:

```
run_terminal_cmd: detect and run project linters

# Auto-detect and run:
# Node/TS projects:
npx tsc --noEmit 2>&1                    # typecheck
npx eslint {changed_files} 2>&1          # lint
npx prettier --check {changed_files} 2>&1 # format check

# Python projects:
python -m mypy {changed_files} 2>&1
python -m ruff check {changed_files} 2>&1
python -m black --check {changed_files} 2>&1

# Rust projects:
cargo check 2>&1
cargo clippy 2>&1
cargo fmt --check 2>&1
```

**On failure:**
- Auto-fix what's fixable: `eslint --fix`, `prettier --write`, `black`, `cargo fmt`
- Re-run checks
- If typecheck still fails → send errors back to coding agent for fix (counts as a review iteration)
- If lint/format still fails after auto-fix → flag as issue for review agent

**On pass:** Continue to review.

---

#### Gate 3: Review Agent

> **Agent Reference:** See `agents/review-agent.md`

```
Task({
  subagent_type: "generalPurpose",
  readonly: true,
  description: "Review implementation for story N",
  prompt: `You are the Review Agent for story implementation validation.

## Your Mission
Review the implementation completed by the Coding Agent and determine if it meets quality standards.

## Story Being Implemented
**Story file path:** {story_file_path}
**Story content:** {full_story_content}

## Implementation Summary from Coding Agent
{coding_agent_output}

## Lint/Typecheck Results
{lint_results}

## Review Checklist

### 1. Acceptance Criteria Verification
For each acceptance criterion, verify the implementation satisfies it:
{acceptance_criteria_with_checkboxes}

### 2. Code Quality Review
- [ ] Follows existing codebase patterns
- [ ] No obvious bugs or logic errors
- [ ] Proper error handling
- [ ] Code is readable and maintainable
- [ ] No hardcoded secrets, tokens, or credentials
- [ ] No commented-out code left behind
- [ ] Appropriate logging (not over/under-logging)

### 3. Security Review
- [ ] User inputs are validated/sanitized
- [ ] No SQL injection, XSS, or injection vulnerabilities
- [ ] Authentication/authorization checks where needed
- [ ] Sensitive data not exposed in logs or responses
- [ ] Dependencies used are not known-vulnerable (check if new deps added)

### 4. Test Coverage Review
- [ ] Tests exist for all acceptance criteria
- [ ] Tests cover edge cases and error paths
- [ ] Tests follow project conventions
- [ ] Test names are descriptive
- [ ] No tests that always pass (assert nothing)

### 5. Integration Review
- [ ] No breaking changes to existing functionality
- [ ] Proper imports and exports
- [ ] No circular dependencies
- [ ] Database migrations included if schema changed

## Output Format
You MUST output your review in this exact format:

### REVIEW_RESULT: [PASS/FAIL]

### Summary
[2-3 sentence summary of the review]

### Checklist Results
[Complete checklist with findings]

### Issues Found (if FAIL)
For each issue:
- **Issue:** [Clear description]
- **Location:** [File and line if applicable]
- **Severity:** [Critical/Major/Minor]
- **Suggested Fix:** [How to resolve]

### Security Assessment
[Brief security posture summary — clean/concerns noted]

### Recommendations (optional)
[Any non-blocking improvements for future]
`
})
```

**Review loop:**
- **PASS** → Continue to testing
- **FAIL** → Resume coding agent with feedback (max 3 iterations total across all gates)
- **3 failures** → Escalate to user

---

#### Gate 4: Testing Agent (with Coverage)

> **Agent Reference:** See `agents/testing-agent.md`

```
Task({
  subagent_type: "generalPurpose",
  description: "Run and verify tests for story N",
  prompt: `You are the Testing Agent for story verification.

## Your Mission
Run all tests related to the implemented story, ensure 100% pass rate, and verify adequate test coverage.

## Story Context
**Story file path:** {story_file_path}
**Acceptance criteria:** {acceptance_criteria}

## Files Modified by Coding Agent
{modified_files}

## Test Files to Run
{test_files}

## Testing Process

### Step 1: Run Story-Specific Tests
Run tests for the newly implemented functionality.
Capture all output including failures.

### Step 2: Run Regression Tests
Run related test suites to ensure no breaking changes.

### Step 3: Run Coverage Analysis
Run tests with coverage enabled:

**Node/TS:** \`npx c8 --reporter=text --reporter=json npm test\` or \`npx vitest --coverage\`
**Python:** \`python -m pytest --cov={module} --cov-report=term\`
**Go:** \`go test -coverprofile=coverage.out ./...\`

**Coverage Requirements:**
- New files: minimum 80% line coverage
- Modified files: coverage must not decrease
- Overall: report but don't block on project-wide coverage

### Step 4: Analyze Failures (if any)
For each failing test:
- Determine if it's a test issue or implementation issue
- Fix the issue (prefer fixing implementation over changing tests)
- Re-run to verify fix

### Step 5: Expand Test Coverage (if needed)
If acceptance criteria aren't fully covered by tests:
- Add missing test cases
- Ensure edge cases are covered

## Output Format

### TEST_RESULT: [PASS/FAIL]

### Test Summary
- Total tests run: X
- Passed: X
- Failed: X
- Skipped: X

### Coverage Report
- New files average: X% line coverage
- Modified files: [file: before% → after%]
- Coverage threshold met: [YES/NO]

### Test Details
[List of test files and their results]

### Failures Addressed (if any)
[Description of any failures and how they were fixed]

### Coverage Assessment
[Are all acceptance criteria covered by tests?]

## Critical Requirements
- **100% pass rate is MANDATORY before reporting PASS.**
- **80% line coverage on new files is MANDATORY.**
- **Coverage must not decrease on modified files.**
If any test fails and cannot be fixed, report FAIL with detailed explanation.
`
})
```

**On FAIL:**
- Test failures → Resume coding agent with test output
- Coverage gaps → Testing agent adds tests (it has write access)
- Still failing after 2 fix iterations → Escalate

---

#### Gate 5: Documentation Agent (Framework-Adaptive)

> **Agent Reference:** See `agents/documentation-agent.md`

**Skip in `--quick` mode.**

```
Task({
  subagent_type: "generalPurpose",
  description: "Update documentation for story N",
  prompt: `You are the Documentation Agent.

## Your Mission
Create or update developer documentation for the implemented story.

## Documentation Framework Detection
First, detect what documentation system this project uses:

1. **Check for frameworks:**
   - \`docs/.vitepress/\` → VitePress
   - \`docs/docusaurus.config.*\` or \`docusaurus.config.*\` → Docusaurus
   - \`docs/next.config.*\` with nextra → Nextra
   - \`.storybook/\` → Storybook (component docs)
   - \`mkdocs.yml\` → MkDocs
   - None of the above → README + inline docs only

2. **Adapt your output accordingly:**
   - If framework found: Create/update docs in that framework's format
   - If no framework: Update project README.md sections + add JSDoc/docstrings

## Story Implemented
**Story file path:** {story_file_path}
**Story content:** {full_story_content}

## Implementation Summary
**Files created/modified:** {files_changed}
**New functionality:** {functionality_summary}

## Documentation Tasks

### For ANY project:
1. **Inline documentation** — Add JSDoc/docstrings to new public functions/classes
2. **README updates** — If the story adds user-facing features, update README.md
3. **CHANGELOG entry** — Add entry to CHANGELOG.md (create if needed)

### If documentation framework detected:
4. **Feature docs** — Create/update feature documentation page
5. **Component docs** — Document new reusable components
6. **Architecture updates** — Update architecture diagrams if major changes
7. **Navigation/sidebar** — Add new pages to navigation config

### Mermaid Diagrams (where appropriate):
Use Mermaid for architecture, data flow, and state diagrams.

## Output Format

### DOCS_UPDATED: [YES/NO]
### Framework Detected: [VitePress/Docusaurus/Nextra/Storybook/MkDocs/None]

### Documentation Changes
#### Files Created
- **File:** [path] — **Purpose:** [description]

#### Files Updated
- **File:** [path] — **Change:** [description]

#### Inline Documentation Added
- **File:** [source file] — **Added:** [what was documented]

### Summary
[Brief summary of documentation changes]
`
})
```

---

### Phase 2: Story Completion

After all gates pass for a story:

#### Step 2.1: Update Story Status

```markdown
# Story N: [Title]

> **Status:** Completed ✅
> **Completed:** [DATE]
```

Mark all tasks and acceptance criteria as checked.

#### Step 2.2: Update README Progress

Update `user-stories/README.md` with new completion percentages.

#### Step 2.3: Commit

```bash
git add -A
git commit -m "feat: complete story N - [title]

- [summary of changes]
- Tests: X passing, Y% coverage
- Review: passed (iteration 1)
- Docs: updated"
```

---

### Phase 3: Spec Completion (--all mode)

After all stories in the spec are complete:

#### Step 3.1: Integration Verification

Run the full test suite (not just per-story tests):
```bash
npm test          # or equivalent
npm run typecheck # full project typecheck
npm run lint      # full project lint
```

If failures: identify which story broke integration, report to user.

#### Step 3.2: Spec-Level Summary

```
✅ Specification Complete: [feature-name]

## Results
| Story | Status | Review | Tests | Coverage | Docs |
|-------|--------|--------|-------|----------|------|
| 1: Auth | ✅ | Passed (1 iteration) | 12/12 | 94% | Updated |
| 2: Session | ✅ | Passed (2 iterations) | 8/8 | 87% | Updated |
| 3: API | ✅ | Passed (1 iteration) | 15/15 | 91% | Updated |

## Execution Stats
- Total time: ~X minutes
- Stories: 3/3 complete
- Total tests: 35 passing
- Average coverage: 91%
- Review iterations: 4 total (1.3 avg per story)
- Integration tests: ✅ passing

## Files Changed
[Aggregate list across all stories]

## Next Steps
- Run `/verify-spec` for final validation
- Run `/refresh-docs` to sync all documentation
- Consider `/release` when ready to ship
```

#### Step 3.3: Auto-run verify-spec

Automatically execute the verify-spec workflow to confirm README is in sync with all story statuses.

---

## Error Handling

### Agent Failure Recovery

**Any agent crashes:**
- Capture error details
- Retry once automatically
- If retry fails, present to user with options

**Review Loop Exceeded (3 iterations):**
```
⚠️ Review loop exceeded maximum iterations for Story N

**Remaining Issues:**
{remaining_issues}

Options:
1. Continue to testing anyway (issues noted but not blocking)
2. Manual intervention needed
3. Skip this story, continue with others
4. Abort spec execution

How would you like to proceed?
```

**Dependency Blocked:**
```
⚠️ Story 4 depends on Story 2, which failed

Options:
1. Skip Story 4 and continue with independent stories
2. Retry Story 2
3. Abort remaining execution
```

### State Persistence & Recovery

State is persisted to `.writ/state/execution-{timestamp}.json` after every phase transition. If the session is interrupted:

```
/implement-story --resume

# Detects most recent execution state file
# Picks up from the last completed phase
# Re-runs the current phase (idempotent)
```

---

## Quick Mode (`--quick`)

Skips: Architecture check, Review agent, Documentation agent
Keeps: Coding agent (TDD), Lint/typecheck gate, Testing agent

Use for: Prototyping, spikes, internal tools, "just get it working" situations.

The full pipeline can be run later on quick-mode code:
```
/implement-story story-3 --review-only   # Run review + test + docs on existing code
```

---

## Integration with Writ Ecosystem

| Command | Relationship |
|---------|-------------|
| `/create-spec` | Creates the stories that implement-story executes |
| `/verify-spec` | Auto-runs after --all completion |
| `/refresh-docs` | Run after spec completion for full sync |
| `/status` | Shows progress of in-flight executions |
| `/create-adr` | Use when architecture check reveals major decisions |

## Deprecation Note

**`/execute-task` is deprecated.** Use `/implement-story` instead:
- `/execute-task story-1` → `/implement-story story-1`
- For quick TDD without review: `/implement-story story-1 --quick`
