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

> **Format reference:** `.writ/docs/drift-report-format.md` — canonical drift report structure, field definitions, DEV-ID numbering, parsing guide, and validation rules.

After the review agent returns, inspect the `### Drift Analysis` section of the review output.

##### Drift-Log Write Procedure

All drift writes target **`.writ/specs/[spec-folder]/drift-log.md`** where `[spec-folder]` is the spec folder loaded in Step 2 (e.g., `.writ/specs/2026-02-27-phase1-foundation/drift-log.md`).

**DEV-ID continuation:** Before writing, scan the existing `drift-log.md` for the highest `DEV-XXX` number. The next deviation starts at highest + 1. If the file doesn't exist, start at `DEV-001`.

**File creation (first drift):**
```markdown
# Drift Log

> Spec: .writ/specs/[spec-folder]/
> Created: YYYY-MM-DD
> ⚠️ Append-only — do not modify existing entries.

---

[story section goes here]
```

**File append (subsequent drift):** Read existing content, append `\n---\n\n` followed by the new story section. Do not modify existing entries.

**Atomic write:** Write to `drift-log.md.tmp`, then rename to `drift-log.md`. This prevents partial writes if interrupted.

##### Handling by Overall Drift Level

**On `Overall Drift: None`** — no write to drift-log.md. Continue pipeline.

**On `Overall Drift: Small`** — pipeline continues PASS:
1. Parse each `Small` deviation from the review output's drift report
2. Format a story section per the canonical format:

```markdown
## Story N: [Story Title] — Drift Report

> Run: YYYY-MM-DD
> Overall Drift: Small

### Deviations

#### [DEV-XXX] [Brief description]
- **Severity:** Small
- **Spec said:** [what spec expected]
- **Implementation did:** [what actually happened]
- **Reason:** [why the deviation occurred]
- **Resolution:** Auto-amended
- **Spec amendment:** [proposed spec change text from review agent]
- **Spec-lite updated:** Yes
```

3. Write/append to `drift-log.md` using the procedure above
4. **Auto-apply amendments to spec-lite.md:**
   - Read the current `spec-lite.md` from the spec folder
   - For each Small deviation's `**Spec amendment:**` text, interpret the proposed change and apply it to the relevant section of `spec-lite.md`
   - The amendment text is a plain-language description (e.g., "Update spec to reference `validateRegistrationData` instead of `validateUserInput`") — find the relevant passage and make the described substitution
   - If multiple Small deviations exist, apply all amendments in a single read-modify-write cycle
   - Write the updated `spec-lite.md`
5. Update each drift-log entry for auto-amended deviations to include: `Spec-lite updated: Yes`
6. Include in pipeline summary: `drift: N small (auto-amended, spec-lite updated)`

> **Important:** Only `spec-lite.md` is auto-modified. The full `spec.md` is never auto-modified — it remains the human-approved contract.

**On `Overall Drift: Medium`** — pipeline continues PASS with warning:
1. Parse each deviation from the review output's drift report
2. Surface warning to user in pipeline output:

```
⚠️ Spec drift detected (Medium):
- [DEV-XXX] [description] — flagged for post-implementation review
```

3. Format and write/append to `drift-log.md` — Medium deviations use:
   - **Resolution:** `Flagged for review`
   - **Spec amendment:** `N/A — flagged for post-implementation review` (or amendment text if the review agent proposed one)
4. Any Small deviations in the same run are also logged with their own entries
5. Include in pipeline summary: `drift: N medium ⚠️, M small (auto-amended)`
6. Continue to Gate 4

**On `Overall Drift: Large`** — pipeline PAUSES:
1. Parse each deviation from the review output's drift report
2. Log all Small and Medium deviations to `drift-log.md` immediately (they don't depend on user decision)
3. Surface Large deviations to user:

```
🛑 Large spec drift detected — pipeline paused.

[DEV-XXX] [Brief description]
  Spec said:          [what spec expected]
  Implementation did: [what actually happened]
  Why it matters:     [impact assessment]

Options:
1. Accept deviation — continue pipeline, log as accepted drift
2. Reject deviation — send back to coding agent with spec constraints
3. Modify spec — update spec.md to reflect new approach, then continue
```

4. Wait for user response via `AskQuestion`
5. **On "Accept":** Append Large deviation entry to `drift-log.md` with:
   - **Resolution:** `Pipeline paused — accepted by user`
   - **Spec amendment:** `N/A — deviation accepted as-is` (or amendment text if user provided one)
   - Continue pipeline to Gate 4
6. **On "Reject":** Append Large deviation entry to `drift-log.md` with:
   - **Resolution:** `Pipeline paused — rejected, sent back to coding agent`
   - **Spec amendment:** `N/A — implementation revised to match spec`
   - Send review feedback + spec constraints back to coding agent (counts as review iteration)
7. **On "Modify spec":** User updates `spec.md`, append Large deviation entry with:
   - **Resolution:** `Pipeline paused — spec modified by user`
   - **Spec amendment:** [description of spec change]
   - Regenerate `spec-lite.md` from the updated `spec.md`, reload both, then re-run from Gate 3 (counts as review iteration)

**Mixed severities:** The overall drift level is the **highest** severity present. If the report contains 1 Small + 1 Large, the pipeline PAUSES for the Large deviation. Small and Medium amendments are still logged immediately — only Large entries wait for user decision. Small deviations still get their spec-lite auto-amendments applied regardless of the overall drift level.

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
3. **Append "What Was Built" record** to the story file (see below)
4. **Update `user-stories/README.md`** progress percentages
#### "What Was Built" Record (Step 3)

Before committing, append a `## What Was Built` section to the story file after the `## Definition of Done` section. This creates the "system spec" — a record of implementation reality alongside the original plan.

**Source the content from:**
- Coding agent output summary (files created/modified, key decisions)
- Drift log entries for this story (deviation IDs, if any)
- Git diff stats (`git diff --stat` for file counts)

**Format:**

```markdown
## What Was Built

**Implemented:** YYYY-MM-DD
**Files:** N created, M modified

**Key decisions made during implementation:**
- [Decision 1 — e.g., "Used `useLocalStorage` hook instead of context (simpler, story-scoped state)"]
- [Decision 2 — e.g., "Added debounce to search input (not in spec, but UX required it)"]
- [Or "None — implementation followed the plan exactly"]

**Deviations from plan:** None | See drift-log.md DEV-XXX, DEV-YYY
```

If the coding agent reported no deviations and the drift log has no entries for this story, use "None" for the deviations line. If key decisions are routine, write "None — implementation followed the plan exactly."

5. **Commit:**

```bash
git add -A
git commit -m "feat: complete story N - [title]

- Files: X created, Y modified
- Tests: N passing, X% coverage
- Review: passed (iteration count)
- Drift: none | N small (auto-amended), M medium ⚠️ — see drift-log.md
- Docs: updated
- What Was Built: recorded"
```

6. **Report results:**

```
✅ Story 3: API Endpoints — Complete

Pipeline: arch-check ✅ → code ✅ → lint ✅ → review ✅ (1 iter) → test ✅ (15/15, 91%) → docs ✅
Files changed: 8 (3 created, 5 modified)
Drift: 1 small (auto-amended), 1 medium ⚠️ — see drift-log.md
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

**Skips:** Gate 0 (arch-check), Gate 3 (review), Gate 3.5 (drift handling), Gate 5 (docs)
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
