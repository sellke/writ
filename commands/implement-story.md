# Implement Story Command (implement-story)

## Overview

Runs a single user story through the full SDLC pipeline: architecture check → coding (TDD) → lint/typecheck → review → drift handling → testing → documentation.

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
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  GATE 0  │──▶│  GATE 1  │──▶│  GATE 2  │──▶│  GATE 3  │──▶│ GATE 3.5 │──▶│  GATE 4  │──▶│ GATE 4.5 │──▶│  GATE 5  │
│ ARCH     │   │ CODING   │   │ LINT &   │   │ REVIEW   │   │  DRIFT   │   │ TESTING  │   │ VISUAL QA│   │  DOCS    │
│ CHECK    │   │ AGENT    │   │TYPECHECK │   │ AGENT    │   │ RESPONSE │   │ AGENT    │   │(optional)│   │ AGENT    │
│(readonly)│   │ (TDD)    │   │ (auto)   │   │(readonly)│   │ (auto)   │   │(+coverage│   │(readonly)│   │(adaptive)│
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
     │              ▲              │               │               │                             │
     │ ABORT?       │ fix loop     │ fail?         │ FAIL?         │ PAUSE?                      │ FAIL?
     ▼              └──────────────┘               │               ▼                             │
  ask user                                    back to Gate 1  ask user                      back to Gate 1
                                              (max 3 iterations total across review + visual QA)
```

## Command Process

### Step 1: Story Selection

If no argument provided, present story selection from current spec (not-started and in-progress stories).

### Step 2: Load Context

1. **Read the story file** — tasks, acceptance criteria, dependencies
2. **Read spec-lite.md** — overall spec context
3. **Scan codebase** — identify patterns, related files, tech stack
4. **Check dependencies** — warn if upstream stories aren't complete
5. **Load visual references** — if the story has a `## Visual References` section:
   - Read linked mockup images via vision model
   - Read `mockups/component-inventory.md` for component specs
   - Read `.writ/docs/design-system.md` for design tokens
   - Pass visual context to the coding agent alongside the story tasks

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

**Report:** files changed, tests written, deviations from plan, concerns.

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

#### Gate 2.5: Change Surface Classification

**Runs inline — no sub-agent needed.**

After lint/typecheck passes, classify the change surface based on files the coding agent created or modified. This classification determines how the review agent allocates its attention.

| Classification | Criteria | Examples |
|---|---|---|
| **style-only** | Only CSS/SCSS/Tailwind files changed, or only `className`/`style` props modified in component files | Adding `max-h-[85vh]`, changing colors, responsive tweaks, CSS module changes |
| **single-component** | Changes scoped to one component file (state, handlers, props, JSX) | Adding a form field, fixing a handler bug, new local state |
| **cross-component** | Shared code changed: hooks, utils, context, types used by multiple components | Refactoring a shared hook, changing a context shape, updating a utility |
| **full-stack** | API routes, schema, migrations, auth, middleware, or multiple system layers | New CRUD endpoint, auth changes, database migration, new middleware |

**Classification heuristic:**
1. List all files created/modified from the coding agent output
2. If ALL changes are `.css`, `.scss`, `.module.css`, Tailwind config, or only `className`/`style` prop changes in `.tsx`/`.jsx` → **style-only**
3. If changes touch exactly one component file (plus its test file) → **single-component**
4. If changes touch shared code (files in `hooks/`, `utils/`, `context/`, `lib/`, or files imported by >3 other files) → **cross-component**
5. If changes touch API routes, database schema, migrations, auth, or middleware → **full-stack**
6. When ambiguous, classify UP one level (prefer more scrutiny over less)

---

#### Gate 3: Review Agent

> **Agent:** `agents/review-agent.md`

Spawns a **read-only** sub-agent for code review.

**Input:** Pass all standard review inputs plus `spec_lite_content` (loaded from the spec folder's `spec-lite.md` in Step 2) for drift analysis, and `change_surface` (from Gate 2.5) to guide review depth allocation.

**Reviews:**
- Acceptance criteria verification
- Code quality (patterns, errors, readability)
- Security (injection, auth, secrets, vulnerable deps)
- Test coverage (all AC covered? edge cases?)
- Integration (breaking changes, circular deps, migrations)
- **Drift analysis** — compare implementation against spec contract, classify deviations

**Results:**
- **PASS** → continue to testing (may include Small or Medium drift)
- **FAIL** → send feedback to coding agent for fixes
- **PAUSE** → Large drift detected; surface conflict to user before continuing

**Review loop:** Max 3 iterations across review and visual QA gates (Gate 3 FAIL → recode, Gate 3.5 "Reject" → recode, Gate 3.5 "Modify spec" → re-review, Gate 4.5 FAIL → recode all count). Gate 4 testing failures have a separate 2-iteration cap. After either cap → escalate to user.

#### Gate 3.5: Drift Response Handling

> **Format reference:** `.writ/docs/drift-report-format.md`

After the review agent returns, inspect the `### Drift Analysis` section. Handle by severity:

**Small drift** (naming, cosmetic — spec intent preserved):
- Auto-amend `spec-lite.md` with the proposed changes
- Log to `drift-log.md`
- Continue PASS
- Always include spec-lite changes in pipeline summary

**Medium drift** (scope/integration impact — spec intent met with notable changes):
- Flag with ⚠️ warning in pipeline output
- Log to `drift-log.md`
- Continue PASS

**Large drift** (fundamental deviation — spec intent NOT met or constraints violated):
- PAUSE pipeline
- Present to user with options: accept deviation, reject (send back to coding agent), or modify spec
- Wait for user decision before continuing

**Principles:**
- Overall drift = highest severity present. Mixed runs pause for Large while still auto-amending Small deviations.
- Only `spec-lite.md` is auto-modified. Full `spec.md` is never auto-modified — it remains the human-approved contract.
- Log all drift to `.writ/specs/[spec-folder]/drift-log.md` — append-only, never modify existing entries. Continue DEV-ID numbering from the highest existing entry.

**Drift-log entry format:**

```markdown
#### [DEV-003] Used shared hook instead of local state
- **Severity:** Small
- **Spec said:** Local useState for form validation
- **Implementation did:** Extracted to shared useFormValidation hook
- **Resolution:** Auto-amended
- **Spec-lite updated:** Yes
```

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

**On failure:** Send test output back to coding agent. 2 fix iterations max (separate from the review loop's 3-iteration cap), then escalate.

---

#### Gate 4.5: Visual QA (Optional)

> **Agent:** `agents/visual-qa-agent.md`
> **Skip in:** `--quick` mode, when no visual references exist for this story

**Auto-activates when:**
- The story file has a `## Visual References` section
- The spec has a `mockups/` directory with files

Spawns a **read-only** sub-agent that:
1. Captures the current UI via browser/Playwright
2. Compares against mockups linked in the story
3. Reports structural, spacing, and styling matches/mismatches

**Results:**
- **PASS** (≥85% match) → continue to docs
- **SOFT PASS** (≥70% match, only cosmetic issues) → continue, log issues
- **FAIL** (<70% match or high-priority mismatches) → send fixes back to coding agent

Failures count toward the shared 3-iteration review loop cap.

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
3. **Append `## What Was Built`** to the story file: implementation date, files created/modified counts, key decisions made during implementation, and deviation references (if any). This is the "system spec" — implementation reality alongside the original plan.
4. **Update `user-stories/README.md`** progress percentages
5. **Commit** with a descriptive message including story title, file counts, test results, and drift status
6. **Report** pipeline results: per-gate status, file counts, drift summary, and next action (`/ship`)

---

## Error Handling

- **Agent crash:** Retry once automatically. If retry fails, present error to user.
- **Review loop exceeded (3 iterations):** Surface remaining issues and offer: continue anyway (noted), manual intervention, or skip story.
- **Blocking issue during coding:** Surface the blocker, what was attempted, and partial progress. Offer: guidance + retry, or skip story.

---

## Quick Mode (`--quick`)

**Skips:** Gate 0 (arch-check), Gate 3 (review), Gate 3.5 (drift handling), Gate 5 (docs)
**Keeps:** Gate 1 (coding/TDD), Gate 2 (lint), Gate 4 (testing)

Use for prototyping, spikes, internal tools. Run full pipeline later:
```
/implement-story story-3 --review-only
```

