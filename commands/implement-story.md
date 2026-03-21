# Implement Story Command (implement-story)

## Overview

Runs a single user story through the full SDLC pipeline: architecture check → **boundary map (Gate 0.5)** → coding (TDD) → lint/typecheck → review → drift handling → testing → documentation.

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
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  GATE 0  │──▶│ GATE 0.5 │──▶│  GATE 1  │──▶│  GATE 2  │──▶│  GATE 3  │──▶│ GATE 3.5 │──▶│  GATE 4  │──▶│ GATE 4.5 │──▶│  GATE 5  │
│ ARCH     │   │ BOUNDARY │   │ CODING   │   │ LINT &   │   │ REVIEW   │   │  DRIFT   │   │ TESTING  │   │ VISUAL QA│   │  DOCS    │
│ CHECK    │   │   MAP    │   │ AGENT    │   │TYPECHECK │   │ AGENT    │   │ RESPONSE │   │ AGENT    │   │(optional)│   │ AGENT    │
│(readonly)│   │ (inline) │   │ (TDD)    │   │ (auto)   │   │(readonly)│   │ (auto)   │   │(+coverage│   │(readonly)│   │(adaptive)│
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
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

1. **Read `.writ/context.md`** (if present) — product mission, active spec state, recent drift, open issues. This is the **first** context item loaded; it primes all subsequent steps.
2. **Read the story file** — tasks, acceptance criteria, dependencies
3. **Read spec-lite.md** — overall spec context
4. **Scan codebase** — identify patterns, related files, tech stack
5. **Check dependencies** — warn if upstream stories aren't complete
6. **Load visual references** — if the story has a `## Visual References` section:
   - Read linked mockup images via vision model
   - Read `mockups/component-inventory.md` for component specs
   - Read `.writ/docs/design-system.md` for design tokens
   - Pass visual context to the coding agent alongside the story tasks

If dependencies are incomplete:
```
⚠️ Story 5 depends on Story 2 (not yet complete).
Proceeding anyway — some integration points may be unavailable.
```

### `.writ/context.md` — Format & Regeneration

`.writ/context.md` is the running project context snapshot. It is **always fully regenerated** (never patched or appended) by `implement-story`, `implement-spec`, and `status`. The file lives at `.writ/context.md` (project root, not inside a spec folder).

**Schema:**

```markdown
# Writ Project Context

> Last Updated: {ISO 8601 timestamp}

## Product Mission

{1–3 sentences from `.writ/product/mission-lite.md` — omit section if file is absent}

## Active Spec

- **Spec:** {spec-folder-id} — {spec title}
- **Status:** {spec status}
- **Story:** {N} of {M} — {current story title} ({story status})
- **Progress:** {X}/{Y} tasks complete ({Z}%)

## Recent Drift

{Last 3 entries from `.writ/specs/{spec}/drift-log.md` — omit section if absent or empty}

## Open Issues

{Count of files in `.writ/issues/` subdirectories — omit section if `.writ/issues/` absent}
```

**Fallbacks when sources are missing:**
- `mission-lite.md` absent → omit "Product Mission" section entirely
- No active spec → omit "Active Spec" section
- `drift-log.md` absent or empty → omit "Recent Drift" section
- `.writ/issues/` absent → omit "Open Issues" section

---

### Step 3: Run Pipeline

> **Context refresh:** `.writ/context.md` is regenerated once at Story Completion (Step 4), not between gates. Each write replaces the entire file — do not append, merge, or patch.

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

#### Gate 0.5: Boundary Computation (File Ownership Map)

> **Agent:** None — **inline orchestration step** (data transformation, not a judgment call)
> **Skip in:** `--quick` mode, `--review-only` mode, `/prototype` path (see below)

Before Gate 1, compute a **`boundary_map`** so the coding and review agents have explicit **owned / readable / out-of-scope** scope. Boundaries are **advisory**: the coding agent **flags** cross-boundary edits in its output; the review agent **verifies** compliance (Gate 3). There is no hard file locking.

**Not applicable — `/prototype`:** The `/prototype` command (`commands/prototype.md`) does not run `implement-story`; that path stays boundary-free. Gate 0.5 exists only on the full `implement-story` pipeline.

##### `boundary_map` schema (markdown block)

Pass this block as the `boundary_map` parameter to the coding agent and review agent. Use **file paths or globs** (e.g. `src/auth/*.ts`). Annotate entries when needed.

```markdown
### File Ownership Boundaries

**Owned** (create or modify):
- `path/to/owned.ts`
- `path/to/owned.test.ts`

**Readable** (import/reference; do not modify unless you emit a BOUNDARY_DEVIATION):
- `path/to/types.ts` _(imported by owned files)_
- `path/to/shared.ts` _(overlap: also touched by Story N — READABLE unless tasks above explicitly modify this path)_
- `path/to/hot.ts` _(⚠️ high-overlap: assess-spec Check 5 warn — extra scrutiny at review)_

**Out-of-scope** (do not modify; if you must, emit BOUNDARY_VIOLATION):
- Everything not listed above as Owned or Readable
```

**Flags (annotations):**
- **`(overlap: …)`** — File area appears in **assess-spec Check 5** as shared between stories; still **Owned** if the current story’s tasks explicitly name that path; otherwise prefer **Readable** with this note.
- **`(⚠️ high-overlap: …)`** — Check 5 severity was **warn** (e.g. three+ stories share the area). Review agent should treat as **higher scrutiny** for boundary compliance and integration.

##### Computation algorithm (orchestrator)

Run in order:

1. **Collect candidate OWNED paths**
   - From the **story file** `## Implementation Tasks` (and inline task bullets): extract paths matching common phrasing — `` `path` ``, "Modify `path`", "Create `path`", "Update `path`", "Add to `path`", file paths in fenced or inline code that look like project paths (contain `/` or `.\`).
   - From **`sub-specs/technical-spec.md`** (or `technical-spec.md` in the spec folder): **File Map** / architecture sections — if a row ties a file to **this story**, treat as OWNED; if tied to **another** story, treat as **overlap hint** (see step 5).

2. **Normalize**
   - Deduplicate; preserve globs as written.
   - If a path is listed as both owned and readable, **Owned wins** unless step 3 or 4 demotes it.

3. **Import graph (depth 1)**
   - For each **existing** OWNED file in the repo, list **direct** imports/references the orchestrator can resolve (language-aware scan: `import`, `require`, `#include`, etc.).
   - Imported files not already OWNED → add to **Readable** with `_(imported by owned files)_`.

4. **Gate 0 overrides**
   - Parse **Architecture Check** output section **### Warnings for Coding Agent**.
   - For each path the warning says **not** to modify (e.g. "Do NOT modify `src/middleware/auth.ts`"), **demote** that path: if it was OWNED → move to **Readable** and append `_(arch-check: do not modify — boundary override)_`; if it must not even be edited with deviation → mark as **out-of-scope** in the narrative (list under Readable with strong wording, or exclude from Owned and treat as readable-only for review). Prefer matching explicit `` `...` `` paths from warnings.

5. **Assess-spec Check 5 (optional)**
   - If **persisted overlap data** exists (see **Check 5 persistence** below), merge:
     - Paths/areas flagged as shared: if **not** explicitly OWNED by this story’s tasks → classify as **Readable** with `_(overlap: …)_`.
     - Items with **warn** / “three+ stories” / **⚠️** from assess-spec → add `_(⚠️ high-overlap: …)_` on the **Readable** line (or on Owned if tasks own the path but overlap remains).
   - If **no** persisted data → skip this step; baseline map from steps 1–4 only.

6. **Fallback — no extractable paths**
   - If steps 1–2 yield **no** OWNED paths:
     - Infer **approximate** directories from task wording (e.g. “auth”, “billing module”) and list **candidate Owned** globs such as `src/auth/**` **only** if the story clearly implies that directory.
     - Emit a visible warning in pipeline output: **`⚠️ boundary_map approximate — no concrete file paths in tasks; review agent should use extra caution.`**

7. **Readable / out-of-scope**
   - **Readable** = union of step 3, 4, 5 additions plus any tech-spec “other story” files, minus anything still OWNED.
   - **Out-of-scope** is **implicit** (everything else); do not enumerate the whole tree — the schema sentence is enough.

**Performance:** Heuristic string extraction + shallow import scan only; target **&lt; 10 seconds** pre–Gate 1.

##### Check 5 persistence (for Gate 0.5 step 5)

Assess-spec output is often **chat-only**. To feed Check 5 into Gate 0.5, persist overlap data in either place:

1. **Recommended:** `.writ/specs/{spec-folder}/assessment-report.md`  
   Include a section headed exactly:

   `## Check 5 — File overlap`

   Use a **table** optional for tooling:

   | File / area | Stories sharing | Severity (note / warn) |
   |-------------|-----------------|-------------------------|
   | `src/lib/utils.ts` | 1, 2, 3 | warn |

   **warn** → maps to **high-overlap** annotations on the boundary map.

2. **Optional:** Embed the same `## Check 5 — File overlap` section in `user-stories/README.md` or `spec.md` / `spec-lite.md` notes after the user applies assess-spec recommendations — same parsing rules.

If **no** such section exists in the active spec folder, Gate 0.5 proceeds without Check 5 data (graceful degradation).

---

#### Gate 1: Coding Agent (TDD Implementation)

> **Agent:** `agents/coding-agent.md`
> **Skip in:** `--review-only` mode

Spawns the coding agent with full story context, any arch-check warnings, and **`boundary_map`** from Gate 0.5.

**When Gate 0.5 was skipped** (`--quick`, `--review-only`): pass **`boundary_map`** = the literal `(none)` and do **not** pass a boundary block — coding/review agents treat `(none)` as “no boundary checking” (see `agents/coding-agent.md`).

**Report:** files changed, tests written, deviations from plan, concerns.

**On `STATUS: BLOCKED`:** If the coding agent returns a `STATUS: BLOCKED` result (hit `MAX_SELF_FIX_ITERATIONS = 3`), surface to the user immediately:

```
AskQuestion({
  title: "Coding Agent Blocked",
  questions: [{
    id: "blocked_action",
    prompt: "The coding agent hit its iteration cap (3 attempts).\n\nAgent: coding-agent\nFailure: [FAILURE from BLOCKED output]\nPartial state: [PARTIAL_STATE from BLOCKED output]\n\nHow do you want to proceed?",
    options: [
      { id: "retry", label: "Retry — restart Gate 1 with fresh context" },
      { id: "skip", label: "Skip gate with warning — continue pipeline (story marked degraded)" },
      { id: "abort", label: "Abort pipeline — preserve current state" }
    ]
  }]
})
```

**Skip with warning:** Continue the pipeline but add a visible `⚠️ DEGRADED` flag to the final story report. The story is NOT marked `Completed ✅` — it is marked `In Progress` with a note: *"Gate 1 skipped after BLOCKED — review required."*

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

After lint/typecheck passes, classify the change surface based on files the coding agent created or modified. This classification determines how the review agent allocates its attention. Optionally cross-check those paths against **`boundary_map`** (Gate 0.5) when present — e.g. unexpected **full-stack** classification for a file listed as Readable may warrant a stricter review posture.

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

**Input:** Pass all standard review inputs plus `spec_lite_content` (loaded from the spec folder's `spec-lite.md` in Step 2) for drift analysis, and `change_surface` (from Gate 2.5) to guide review depth allocation. Also pass **`boundary_map`** (same markdown block as Gate 0.5) and, if present, a one-line **`boundary_overlap_summary`** distilled from Readable lines that carry `overlap` or `high-overlap` — so the review agent can calibrate scrutiny.

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

**On `STATUS: BLOCKED`:** If the testing agent returns a `STATUS: BLOCKED` result (hit `MAX_SELF_FIX_ITERATIONS = 3`), surface to the user:

```
AskQuestion({
  title: "Testing Agent Blocked",
  questions: [{
    id: "blocked_action",
    prompt: "The testing agent hit its iteration cap (3 attempts).\n\nAgent: testing-agent\nFailure: [FAILURE from BLOCKED output]\nPartial state: [PARTIAL_STATE from BLOCKED output]\n\nHow do you want to proceed?",
    options: [
      { id: "retry", label: "Retry — restart Gate 4 with fresh context" },
      { id: "skip", label: "Skip gate with warning — continue to docs (story marked degraded)" },
      { id: "abort", label: "Abort pipeline — preserve current state" }
    ]
  }]
})
```

**Skip with warning:** Continue to Gate 5 but mark the story `⚠️ DEGRADED` in the final report. Do NOT mark `Completed ✅`.

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
3. **Regenerate `.writ/context.md`** — full rewrite using the schema defined in Step 2, reflecting the newly completed story status and updated progress counts.
4. **Append `## What Was Built`** to the story file: implementation date, files created/modified counts, key decisions made during implementation, and deviation references (if any). This is the "system spec" — implementation reality alongside the original plan.
5. **Update `user-stories/README.md`** progress percentages
6. **Commit** with a descriptive message including story title, file counts, test results, and drift status
7. **Report** pipeline results: per-gate status, file counts, drift summary, and next action (`/ship`)

---

## Error Handling

- **Agent crash:** Retry once automatically. If retry fails, present error to user.
- **Review loop exceeded (3 iterations):** Surface remaining issues and offer: continue anyway (noted), manual intervention, or skip story.
- **Blocking issue during coding:** Surface the blocker, what was attempted, and partial progress. Offer: guidance + retry, or skip story.
- **`STATUS: BLOCKED` from coding or testing agent:** The agent hit `MAX_SELF_FIX_ITERATIONS = 3`. Parse the `FAILURE` and `PARTIAL_STATE` fields from the BLOCKED output and present the AskQuestion repair decision at the relevant gate (see Gate 1 and Gate 4 above). Never silently continue past a BLOCKED result.

---

## Quick Mode (`--quick`)

**Skips:** Gate 0 (arch-check), **Gate 0.5 (boundary map)**, Gate 3 (review), Gate 3.5 (drift handling), Gate 5 (docs)
**Keeps:** Gate 1 (coding/TDD), Gate 2 (lint), Gate 4 (testing)

Use for prototyping, spikes, internal tools. Run full pipeline later:
```
/implement-story story-3 --review-only
```

