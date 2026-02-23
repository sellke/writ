# Implement Story Command (implement-story)

## Overview

Runs a single user story through the full 6-gate SDLC pipeline: architecture check → coding (TDD) → lint/typecheck → review → testing → documentation.

This is the **per-story execution engine**. For full spec execution with dependency resolution and parallel batching, use `/implement-spec`.

## Invocation

| Invocation | Behavior |
|---|---|
| `/implement-story` | Interactive — presents story selection |
| `/implement-story story-3` | Runs story 3 through the full pipeline |
| `/implement-story story-3 --quick` | Skips arch-check, review, and docs (prototyping) |
| `/implement-story story-3 --review-only` | Runs review + test + docs on existing code (no coding phase) |

## Agent Pipeline

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  GATE 0  │──▶│  GATE 1  │──▶│  GATE 2  │──▶│  GATE 3  │──▶│  GATE 4  │──▶│  GATE 5  │
│ ARCH     │   │ CODING   │   │ LINT &   │   │ REVIEW   │   │ TESTING  │   │  DOCS    │
│ CHECK    │   │ AGENT    │   │TYPECHECK │   │ AGENT    │   │ AGENT    │   │ AGENT    │
│(readonly)│   │ (TDD)    │   │ (auto)   │   │(readonly)│   │(+coverage│   │(adaptive)│
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
     │              ▲              │               │
     │ ABORT?       │ fix loop     │ fail?         │ FAIL?
     ▼              └──────────────┘               │
  ask user                                    back to Gate 1
                                              (max 3 iterations)
```

## Command Process

### Step 1: Story Selection

**If no argument provided:**

```
AskQuestion({
  title: "Select Story",
  questions: [
    {
      id: "story",
      prompt: "Which user story do you want to implement?",
      options: [list of not-started/in-progress stories from current spec]
    }
  ]
})
```

### Step 2: Load Context

1. **Read the story file** — tasks, acceptance criteria, dependencies
2. **Read spec-lite.md** — overall spec context
3. **Scan codebase** — identify patterns, related files, tech stack
4. **Check dependencies** — warn if upstream stories aren't complete

If dependencies are incomplete:
```
⚠️ Story 5 depends on Story 2 (not yet complete).
Proceeding anyway — some integration points may be unavailable.
```

### Step 3: Run Pipeline

---

#### Gate 0: Architecture Check (Pre-Implementation)

> **Agent:** `agents/architecture-check-agent.md`
> **Skip in:** `--quick` mode, `--review-only` mode

Spawns a **read-only** sub-agent to review the planned approach before any code is written.

**Reviews:**
- Approach viability (does the task list make sense?)
- Integration risk (could this break existing code?)
- Complexity assessment (anything underestimated?)
- Missing considerations (migrations, env changes, error handling?)

**Results:**
- **PROCEED** → continue to coding
- **CAUTION** → continue, inject warnings into coding agent prompt
- **ABORT** → present findings to user, ask whether to proceed/modify/skip

---

#### Gate 1: Coding Agent (TDD Implementation)

> **Agent:** `agents/coding-agent.md`
> **Skip in:** `--review-only` mode

Spawns the coding agent with full story context + any arch-check warnings.

**Requirements:**
1. Write tests first (TDD)
2. Match existing codebase patterns
3. Implement all tasks in the story
4. Satisfy all acceptance criteria
5. Report: files changed, tests written, deviations, concerns

**Output:** Structured implementation summary.

---

#### Gate 2: Lint, Typecheck & Format

**Runs inline — no sub-agent needed.**

Auto-detect and run project linters:
- **Node/TS:** `tsc --noEmit`, `eslint`, `prettier --check`
- **Python:** `mypy`, `ruff`, `black --check`
- **Rust:** `cargo check`, `cargo clippy`, `cargo fmt --check`

**On failure:**
1. Auto-fix what's fixable (`eslint --fix`, `prettier --write`, `black`, `cargo fmt`)
2. Re-run checks
3. If typecheck still fails → send errors back to coding agent
4. If still failing after auto-fix → flag for review agent

---

#### Gate 3: Review Agent

> **Agent:** `agents/review-agent.md`

Spawns a **read-only** sub-agent for code review.

**Reviews:**
- Acceptance criteria verification
- Code quality (patterns, errors, readability)
- Security (injection, auth, secrets, vulnerable deps)
- Test coverage (all AC covered? edge cases?)
- Integration (breaking changes, circular deps, migrations)

**Results:**
- **PASS** → continue to testing
- **FAIL** → send feedback to coding agent for fixes

**Review loop:** Max 3 iterations across all gates. After 3 failures → escalate to user.

---

#### Gate 4: Testing Agent (with Coverage Enforcement)

> **Agent:** `agents/testing-agent.md`

**Process:**
1. Run story-specific tests
2. Run regression tests (related suites)
3. Run coverage analysis
4. Fix failures (prefer fixing implementation over changing tests)
5. Add missing test coverage if needed

**Requirements:**
- **100% test pass rate** — mandatory
- **≥80% line coverage on new files** — mandatory
- **Coverage must not decrease on modified files**

**On failure:** Send test output back to coding agent. 2 fix iterations max, then escalate.

---

#### Gate 5: Documentation Agent

> **Agent:** `agents/documentation-agent.md`
> **Skip in:** `--quick` mode

**Auto-detects documentation framework** (VitePress, Docusaurus, Nextra, MkDocs, Storybook, or plain README).

**Updates:**
- Inline docs (JSDoc/docstrings) for new public APIs
- README if user-facing features added
- CHANGELOG entry
- Framework-specific docs pages if detected
- Mermaid diagrams where appropriate

---

### Step 4: Story Completion

After all gates pass:

1. **Update story status** → `Completed ✅` with date
2. **Mark tasks and AC** as checked in story file
3. **Update `user-stories/README.md`** progress percentages
4. **Commit:**

```bash
git add -A
git commit -m "feat: complete story N - [title]

- Files: X created, Y modified
- Tests: N passing, X% coverage
- Review: passed (iteration count)
- Docs: updated"
```

5. **Report results:**

```
✅ Story 3: API Endpoints — Complete

Pipeline: arch-check ✅ → code ✅ → lint ✅ → review ✅ (1 iter) → test ✅ (15/15, 91%) → docs ✅
Files changed: 8 (3 created, 5 modified)
```

---

## Error Handling

**Agent crash:** Retry once automatically. If retry fails, present error to user.

**Review loop exceeded (3 iterations):**
```
⚠️ Review loop exceeded for Story N.

Remaining issues:
{issues}

Options:
1. Continue to testing anyway (issues noted)
2. Manual intervention needed
3. Skip this story
```

**Blocking issue during coding:**
```
⚠️ Implementation blocked.

Blocker: {description}
Attempted: {what was tried}
Partial progress: {what's done}

Options:
1. Provide guidance and retry
2. Skip this story
```

---

## Quick Mode (`--quick`)

**Skips:** Gate 0 (arch-check), Gate 3 (review), Gate 5 (docs)
**Keeps:** Gate 1 (coding/TDD), Gate 2 (lint), Gate 4 (testing)

Use for prototyping, spikes, internal tools. Run full pipeline later:
```
/implement-story story-3 --review-only
```

---

## Deprecation Note

**`/execute-task` is deprecated.** Use `/implement-story` instead:
- `/execute-task story-1` → `/implement-story story-1`

**Spec-level execution has moved to `/implement-spec`:**
- `/implement-story --all` → `/implement-spec`
- `/implement-story --from story-3` → `/implement-spec --from story-3`
