---
name: implement-story
description: "Run a single user story through the full SDLC pipeline: architecture check, boundary map, TDD coding, lint, review, testing, documentation."
problem: "A story gets coded straight off its task list, so architecture fit, review, and coverage are skipped once the code looks right, and nothing records what was built for the stories downstream."
outcome: "One story file is closed out - status flipped, tasks and acceptance criteria checked, a What Was Built record appended, and the implementing commit SHA written into its header."
exit_criteria:
  - "the story file header reads Status: Completed and carries a > **Commit:** line holding the full SHA of the completion commit, written once rather than duplicated on re-runs"
  - "the story file ends with a ## What Was Built section naming files created, files modified, and test results, and user-stories/README.md progress counts match it"
  - "Gate 4 recorded a 100 percent test pass rate with at least 80 percent line coverage on new files, and no gate was skipped without the story being marked DEGRADED instead of Completed"
loop:
  unit: "review_cycle"
  max_iterations: 3
  on_exhaustion: escalate
  calibrated_against: "One shared counter across four increment sites - Gate 3 FAIL, Gate 3.5 Reject, Gate 3.5 Modify spec, Gate 4.5 FAIL - not four separate budgets. Transcribes the existing prose cap in this file: 'Review loop: Max 3 iterations across review and visual QA gates'. 42 'Iteration count' records across archived story What Was Built sections in .writ/specs/archive/: 39 at 1 iteration, 3 at 2, maximum ever observed = 2. A bound of 2 would sit at the observed maximum with zero headroom; 3 keeps one iteration and is the number already honored today. Evidence: strong - 42 real records."
  nested:
    - unit: "testing_cycle"
      max_iterations: 2
      on_exhaustion: escalate
      calibrated_against: "Transcribes the existing Gate 4 prose cap in this file: '2 fix iterations max (separate from the review loop's 3-iteration cap)'. No recorded run in .writ/specs/archive/ reports a testing-fix iteration above 1. Evidence: adequate - a faithful transcription, but the original derivation of the 2 is recorded nowhere, so do not read it as measured."
    - unit: "agent_self_fix"
      max_iterations: 3
      on_exhaustion: escalate
      calibrated_against: "Transcribes MAX_SELF_FIX_ITERATIONS = 3, declared in agents/coding-agent.md and agents/testing-agent.md and consumed by this file's STATUS: BLOCKED handlers at Gate 1 and Gate 4. Evidence: strong - two agent definitions already enforce it; this declaration must not drift from them."
---

# Implement Story Command (implement-story)

## Overview

Runs a single user story through the full SDLC pipeline — architecture check through documentation; the Pipeline table below is the stage list.

This is the **per-story execution engine**. For full spec execution with dependency resolution and parallel batching, use `/implement-spec`.

## Required Artifacts

Verify per the preamble's **Artifact Integrity** rule before starting.

- **Required:** active spec folder (`spec.md`, `user-stories/`).
- **Optional:** `.writ/context.md`, `.writ/knowledge/`, `spec-lite.md`, `mockups/`.

## Invocation

| Invocation | Behavior |
|---|---|
| `/implement-story` | Interactive — presents story selection |
| `/implement-story story-3` | Runs story 3 through the full pipeline |
| `/implement-story story-3 --quick` | Skips arch-check, review, and docs (prototyping) |
| `/implement-story story-3 --review-only` | Runs review + test + docs on existing code (no coding phase) |

## Pipeline

One row per stage, so the shape stays visible even when the detail does not. The **Skill** column *names* what a stage loads; the `Read` is issued inside that stage, never here.

| Stage | Name | Runs as | Skipped in | Skill |
|---|---|---|---|---|
| Step 2 | Load Context | inline | — | `story-context-assembly`; `dependency-context-loading` (dependency branch only) |
| Gate 0 | Architecture Check | `architecture-check-agent` — read-only | `--quick`, `--review-only` | — |
| Gate 0.5 | Boundary Map | inline — data transformation | `--quick`, `--review-only`, `/prototype` | `boundary-map-computation` |
| Gate 1 | Coding Agent | `coding-agent` — TDD | `--review-only` | `tdd-cycle` |
| Gate 2 | Lint, Typecheck, Format & Build Smoke | inline — auto | — | — |
| Gate 2.5 | Change Surface | inline | — | `change-surface-classification` |
| Gate 3 | Review Agent | `review-agent` — read-only | `--quick` | — |
| Gate 3.5 | Drift Response & WWB Extraction | inline — auto | `--quick` | `drift-triage` (§ A) |
| Gate 4 | Testing Agent | `testing-agent` — + coverage | — | — |
| Gate 4.5 | Visual QA | `visual-qa-agent` — read-only, optional | `--quick`; no visual references | — |
| Gate 5 | Documentation Agent | `documentation-agent` — adaptive | `--quick` | — |
| Step 4 | Story Completion | inline | — | `project-context-snapshot` (item 3); `what-was-built-authoring` (item 4); `story-commit-provenance` (item 7) |

**Control flow:** Gate 0 ABORT and Gate 3.5 PAUSE → ask user. Gate 3, Gate 4 and Gate 4.5 FAIL → back to Gate 1 (max 3 iterations total across review + visual QA).

## Command Process

### Step 1: Story Selection

If no argument provided, present story selection from current spec (not-started and in-progress stories).

### Step 2: Load Context

1. **Read `.writ/context.md`** (if present) — product mission, active spec state, recent drift, open issues. This is the **first** context item loaded; it primes all subsequent steps.
2. **Read the story file** — tasks, acceptance criteria, dependencies
3. **Read spec-lite.md** — overall spec context
4. **Parse context hints and fetch referenced content** — invoke the assembler below
5. **Load knowledge context** — grep `.writ/knowledge/` for entries matching story keywords; assemble optional `knowledge_context` (≤2KB) for architecture-check, coding, and review agents
6. **Extract agent-specific spec-lite sections** — parse spec-lite.md into per-role sections for targeted delivery
7. **Scan codebase** — identify patterns, related files, tech stack
8. **Check dependencies** — warn if upstream stories aren't complete
9. **Load "What Was Built" from dependencies** — only when the story declares dependencies
10. **Load visual references** — if the story has a `## Visual References` section: read linked mockup images via vision model; read `mockups/component-inventory.md` for component specs; read `.writ/docs/design-system.md` for design tokens; pass visual context to the coding agent alongside the story tasks

If dependencies are incomplete:
```
⚠️ Story 5 depends on Story 2 (not yet complete).
Proceeding anyway — some integration points may be unavailable.
```

**Context assembly (items 4–6).** Delegate hint parsing and fetching to `scripts/story-context.py`, the sole implementation — do not interpret `## Context for Agents` here:

```bash
python3 scripts/story-context.py assemble --story <story-file-path> --budget-bytes 21000
```

`Read skills/story-context-assembly/SKILL.md` for *how* the payloads are built. This step owns *when* assembly runs and who receives what (routing table below); the skill owns *how*. Outputs: `fetched_context`, `context_warnings`, `knowledge_context`, `spec_lite_for_coding` / `spec_lite_for_review` / `spec_lite_for_testing`.

**Routing table — what each agent receives:**

| Agent | Spec-Lite Section | Supplementary Context (from hints) |
|---|---|---|
| Architecture Check (Gate 0) | `spec_lite_for_coding` | `fetched_context` (all categories) + `knowledge_context` |
| Coding Agent (Gate 1) | `spec_lite_for_coding` | `fetched_context` (error maps, business rules) + `knowledge_context` + dependency WWB records |
| Review Agent (Gate 3) | `spec_lite_for_review` | `fetched_context` (business rules, experience) + `knowledge_context` |
| Testing Agent (Gate 4) | `spec_lite_for_testing` | `fetched_context` (shadow paths, edge cases) |
| Documentation Agent (Gate 5) | Full spec-lite content | `fetched_context` (all categories) |

**Dependency records (item 9).** **If — and only if — the story declares dependencies**, load the completed upstream stories' "What Was Built" records into `dependency_wwb_context`, which Gate 1 routes to the coding agent. Skip reverted records: one carrying a `> **Reverted:**` banner is not authoritative and is never loaded as live dependency context. A story with no dependencies skips this branch entirely.

`Read skills/dependency-context-loading/SKILL.md` for *how* those records are located, filtered, truncated and aggregated. This step owns *whether* the branch runs at all; the skill owns *how* the block is built.

### Step 3: Run Pipeline

> **Context refresh:** `.writ/context.md` is regenerated once at Story Completion (Step 4), not between gates. Each write replaces the entire file — do not append, merge, or patch.

> **File creation discipline:** Agents must only create files explicitly listed in the story's implementation tasks. Verification results, validation reports, acceptance-criteria checklists, test plans and other analysis artifacts belong in the agent's **structured output** — never as new files on disk. The orchestrator must not commit any file that isn't in the story's task list or a known pipeline output (drift-log, context.md, story status updates).

> **Sub-agent completeness:** `Read skills/subagent-result-completeness/SKILL.md`
> for *how* to tell a spawned gate agent's complete verdict from a mid-task
> stop, and what to do about the latter. This note owns *when* every gate
> below that spawns a sub-agent (Gate 0, 1, 3, 4, 4.5) checks for
> completeness before advancing; the skill owns *how* to tell a complete
> verdict from a partial one.

> **Sub-agent worktree integration:** `Read skills/subagent-worktree-integration/SKILL.md`
> for *how* to reconcile a spawned agent's isolated worktree with the
> orchestrator's own checkout, including the stale-worktree failure mode.
> This note owns *when* every gate below that spawns a sub-agent (Gate 0, 1,
> 3, 4, 4.5) reconciles isolated output before trusting it; the skill owns
> *how* the diff → copy → re-verify → cleanup procedure runs.

---

#### Gate 0: Architecture Check (Pre-Implementation)

> **Agent:** `agents/architecture-check-agent.md`
> **Skip in:** `--quick` mode, `--review-only` mode

Spawns a **read-only** sub-agent to review the planned approach before any code is written: approach viability, integration risk, complexity assessment, missing considerations (migrations, env changes, error handling).

**Results:** **PROCEED** → continue to coding · **CAUTION** → continue, inject warnings into coding agent prompt · **ABORT** → present findings to user, ask whether to proceed/modify/skip

**Context routing:** Pass `spec_lite_for_coding` as `spec_lite_content`; if agent-specific sections are unavailable, pass full spec-lite. Also pass `fetched_context` when hints were parsed in Step 2, and `knowledge_context` when populated.

---

#### Gate 0.5: Boundary Computation (File Ownership Map)

> **Agent:** None — **inline orchestration step** (data transformation, not a judgment call)
> **Skip in:** `--quick` mode, `--review-only` mode, `/prototype` path

Before Gate 1, compute a **`boundary_map`** so the coding and review agents have explicit **owned / readable / out-of-scope** scope. Boundaries are **advisory**: the coding agent **flags** cross-boundary edits in its output; the review agent **verifies** compliance (Gate 3). There is no hard file locking.

**Not applicable — `/prototype`:** `commands/prototype.md` does not run `implement-story`; that path stays boundary-free. Gate 0.5 exists only on the full pipeline.

`Read skills/boundary-map-computation/SKILL.md` for *how* the map is derived, including where assess-spec Check 5 overlap data is persisted and how it degrades when absent. This gate owns *when* it is computed and that Gates 1 and 3 receive it as `boundary_map`; the skill owns *how*.

---

#### Gate 1: Coding Agent (TDD Implementation)

> **Agent:** `agents/coding-agent.md`
> **Skip in:** `--review-only` mode

Spawns the coding agent to run the red → green → refactor loop via `Read skills/tdd-cycle/SKILL.md`, with full story context, optional `knowledge_context`, any arch-check warnings, and **`boundary_map`** from Gate 0.5. This gate owns *when* coding runs, the context it routes below, and `STATUS: BLOCKED` handling; the skill owns *how* the test-first cycle runs.

**Context routing:** Pass `spec_lite_for_coding` as `spec_lite_content` and relevant `fetched_context` (error maps, business rules). Pass `knowledge_context` after spec context and before dependency records when populated. If dependencies have completed "What Was Built" records (loaded in Step 2), pass aggregated `dependency_wwb_context` — positioned after knowledge context, before implementation tasks.

**When Gate 0.5 was skipped** (`--quick`, `--review-only`): pass **`boundary_map`** = the literal `(none)` and do **not** pass a boundary block — coding/review agents treat `(none)` as “no boundary checking” (see `agents/coding-agent.md`).

**Report:** files changed, tests written, deviations from plan, concerns.

**On `STATUS: BLOCKED`:** apply the shared [BLOCKED escalation](#blocked-agent-escalation) with agent `coding-agent`, restarting **Gate 1**; skip-with-warning marks the story `In Progress` with the note *"Gate 1 skipped after BLOCKED — review required."*

---

#### Gate 2: Lint, Typecheck, Format & Build Smoke

**Runs inline — no sub-agent needed.**

Auto-detect and run project linters — **Node/TS:** `tsc --noEmit`, `eslint`, `prettier --check` · **Python:** `mypy`, `ruff`, `black --check` · **Rust:** `cargo check`, `cargo clippy`, `cargo fmt --check`.

**On failure:** (1) auto-fix what's fixable (`eslint --fix`, `prettier --write`, `black`, `cargo fmt`); (2) re-run checks; (3) if typecheck still fails → send errors back to coding agent; (4) if still failing after auto-fix → flag for review agent.

**Build smoke.** When the story changed source, also run `python3 scripts/build-smoke.py check --project .` and surface its verdict in the story report. Typechecking cannot see framework-level structural errors — a route collision breaks every deployment and passes every unit test that imports handlers as plain functions.

- **`build_failed_source`** → blocking. Apply the shared [BLOCKED escalation](#blocked-agent-escalation) with agent `coding-agent`, restarting **Gate 2**. No new control flow, no iteration cap.
- **`build_failed_environment` or any `unverifiable` verdict** → the pipeline continues. Surface the reason verbatim; the story is **not** marked `⚠️ DEGRADED` on that basis. An unverifiable check is not a failed gate — DEGRADED means a gate could not be cleared, `unverifiable` means a check could not be run here.

---

#### Gate 2.5: Change Surface Classification

**Runs inline — no sub-agent needed.**

After lint/typecheck passes, classify the files the coding agent created or modified as **style-only**, **single-component**, **cross-component** or **full-stack** and pass it to Gate 3 as `change_surface`, which guides review depth. Optionally cross-check those paths against **`boundary_map`** (Gate 0.5) when present — an unexpected **full-stack** result for a file listed as Readable warrants a stricter review posture.

`Read skills/change-surface-classification/SKILL.md` for *how* the four classes are told apart. This gate owns *when* classification runs and who consumes `change_surface`; the skill owns *how* the class is decided.

---

#### Gate 3: Review Agent

> **Agent:** `agents/review-agent.md`

Spawns a **read-only** sub-agent for code review: acceptance criteria; code quality (patterns, errors, readability); security (injection, auth, secrets, vulnerable deps); test coverage (all AC covered? edge cases?); integration (breaking changes, circular deps, migrations); and **drift analysis** — implementation against the spec contract, classifying deviations.

**Input:** all standard review inputs plus `spec_lite_for_review` as `spec_lite_content` (extracted in Step 2) for drift analysis, optional `knowledge_context`, and `change_surface` (Gate 2.5) to guide review depth. Also **`boundary_map`** (the same block as Gate 0.5) and, if present, a one-line **`boundary_overlap_summary`** distilled from Readable lines carrying `overlap` or `high-overlap`. If agent-specific sections are unavailable (legacy spec-lite), pass full spec-lite content.

**Results:** **PASS** → continue to testing (may include Small or Medium drift) · **FAIL** → send feedback to coding agent for fixes · **PAUSE** → Large drift detected; surface conflict to user before continuing

**Review loop:** Max 3 iterations across review and visual QA gates (Gate 3 FAIL → recode, Gate 3.5 "Reject" → recode, Gate 3.5 "Modify spec" → re-review, Gate 4.5 FAIL → recode all count). Those four sites share **one** counter — they are not four independent budgets. Gate 4 testing failures have a separate 2-iteration cap. After either cap → escalate to user. Both caps are declared as `loop.max_iterations` and the nested `testing_cycle` entry in this file's frontmatter, with `on_exhaustion: escalate`: the existing `AskQuestion` escalations *are* the implementation, and no cap may be silently continued past.

#### Gate 3.5: Drift Response Handling & "What Was Built" Extraction

> **Format reference:** `.writ/docs/drift-report-format.md`, `.writ/docs/what-was-built-format.md`

After the review agent returns, perform two operations:

##### A. Drift Response

Inspect the `### Drift Analysis` section and handle by severity: **Small** (naming/cosmetic — auto-amend `spec-lite.md` only, log a `DEV-NNN` entry, PASS); **Medium** (scope/integration impact — ⚠️ warn, log, PASS); **Large** (fundamental deviation — **PAUSE**, present accept / reject / modify-spec, wait for the decision). `spec.md` is never auto-modified.

`Read skills/drift-triage/SKILL.md` for *how* each severity is handled, including the mixed-severity rule and the append-only `drift-log.md` rules. This gate owns *when* triage runs and that a Large drift pauses the pipeline and asks the user; the skill owns *how*.

##### B. "What Was Built" Data Extraction

Extract implementation data from the review agent's output into `what_was_built_data` and hold it in orchestrator state, parsing defensively with a fallback for every field. **Do NOT append to the story file yet.**

Data flow: **Gate 3.5** extracts and validates; **Gate 4** updates `what_was_built_data.test_results`; **Step 4 item 4** formats and appends. The extraction sources, their mandatory/best-effort semantics and their fallback values live in `what-was-built-authoring`, loaded once at Step 4 item 4 alongside the formatting rules they feed.

---

#### Gate 4: Testing Agent (with Coverage Enforcement)

> **Agent:** `agents/testing-agent.md`

**Context routing:** Pass `spec_lite_for_testing` as `spec_lite_content` — success criteria, shadow paths, and edge cases relevant to testing. If agent-specific sections not available, pass full spec-lite.

**Process:** (1) run story-specific tests; (2) run regression tests (related suites); (3) run coverage analysis; (4) fix failures, preferring to fix the implementation over changing tests; (5) add missing test coverage if needed.

**Requirements:** **100% test pass rate** — mandatory · **≥80% line coverage on new files** — mandatory · **coverage must not decrease on modified files**.

**On failure:** Send test output back to coding agent. 2 fix iterations max (separate from the review loop's 3-iteration cap), then escalate.

**On `STATUS: BLOCKED`:** apply the shared [BLOCKED escalation](#blocked-agent-escalation) with agent `testing-agent`, restarting **Gate 4**; skip-with-warning continues to Gate 5 with the story marked `⚠️ DEGRADED`.

**Verify the claim, don't trust it.** After the testing agent returns, run:

```bash
python3 scripts/test-integrity.py coverage --project . --new-files <story's new files>
python3 scripts/test-integrity.py authenticity --project . --tests <story's test files>
```

`Coverage threshold met: YES` is a field the agent types. The checker re-derives it from the coverage tool's own output, and **where they disagree the checker wins** — a run may report `TEST_RESULT: PASS` and still not close, exactly as `scripts/exit-criteria.py` lets a run report COMPLETE and be published `unmet`. Show both the claim and the measurement in the story report.

- **`coverage_below_threshold`, `coverage_regression`, or `test_imports_no_source`** → blocking. The story does not reach `Completed ✅`. The escape hatch is the shared [BLOCKED escalation](#blocked-agent-escalation) with its human decision, never a quiet downgrade.
- **Any `unverifiable` verdict** → the pipeline continues, the reason is surfaced verbatim, and the story is **not** marked `⚠️ DEGRADED` on that basis alone.

---

#### Gate 4.5: Visual QA (Optional)

> **Agent:** `agents/visual-qa-agent.md`
> **Skip in:** `--quick` mode, when no visual references exist for this story

**Auto-activates when:** the story has a `## Visual References` section, or the spec has a `mockups/` directory with files.

Spawns a **read-only** sub-agent that captures the current UI via browser/Playwright, compares against mockups linked in the story, and reports structural, spacing and styling matches/mismatches.

**Results:** **PASS** (≥85% match) → continue to docs · **SOFT PASS** (≥70% match, only cosmetic issues) → continue, log issues · **FAIL** (<70% match or high-priority mismatches) → send fixes back to coding agent

Failures count toward the shared review-loop cap declared at Gate 3.

---

#### Gate 5: Documentation Agent

> **Agent:** `agents/documentation-agent.md`
> **Skip in:** `--quick` mode

**Context routing:** Pass full spec-lite content as `spec_context` — documentation needs a cross-cutting view across all spec sections. Also pass `fetched_context` if available.

**Auto-detects the docs framework** (VitePress, Docusaurus, Nextra, MkDocs, Storybook, or plain README).

**Updates:** inline docs (JSDoc/docstrings) for new public APIs; README if user-facing features added; CHANGELOG entry; framework docs pages if detected; Mermaid diagrams where appropriate.

---

### Step 4: Story Completion

After all gates pass:

1. **Update story status** → `Completed ✅` with date
2. **Mark tasks and AC** as checked in story file
3. **Regenerate `.writ/context.md`** — full rewrite, never appended or patched, reflecting the newly completed story status and updated progress counts. The regenerated snapshot always carries an `## Artifact Map` whose **Integrity:** line always renders: `✅ all required present`, else `⚠️ missing required: <list>`.
4. **Append `## What Was Built`** to the story file
5. **Update `user-stories/README.md`** progress percentages
6. **Commit** with a descriptive message including story title, file counts, test results, and drift status
7. **Record the story commit SHA** into the story file header as `> **Commit:** <full-sha>`, beside `> **Status:**`
8. **Report** pipeline results: per-gate status, file counts, drift summary, and next action (`/ship`)

**Item 3 — the snapshot.** `Read skills/project-context-snapshot/SKILL.md` for *what* `.writ/context.md` contains. This step owns *when* regeneration happens — once, here, never between gates. `implement-spec` and `status` regenerate the same schema.

**Item 4 — the record.** `Read skills/what-was-built-authoring/SKILL.md` for *how* the record is extracted and formatted. A `--quick` run reaches this step with no `what_was_built_data` and **still writes the minimal record** — which is why the skill loads here, not at Gate 3.5.

**Item 7 — provenance.** `Read skills/story-commit-provenance/SKILL.md` for *how* the SHA is captured, placed idempotently, and landed without amending the commit it names. Written right after item 6's commit; `/revert` and `scripts/revert-resolve.py` consume it.

---

## Error Handling

- **Agent crash:** Retry once automatically. If retry fails, present error to user.
- **Review loop exceeded (3 iterations):** Surface remaining issues and offer: continue anyway (noted), manual intervention, or skip story.
- **Blocking issue during coding:** Surface the blocker, what was attempted, and partial progress. Offer: guidance + retry, or skip story.
- **`STATUS: BLOCKED` from coding or testing agent:** The agent hit `MAX_SELF_FIX_ITERATIONS = 3`. Parse the `FAILURE` and `PARTIAL_STATE` fields from the BLOCKED output and present the repair decision below at the relevant gate. Never silently continue past a BLOCKED result.

### BLOCKED Agent Escalation

One template for Gate 1 (`coding-agent`) and Gate 4 (`testing-agent`) — substitute the agent name and the gate to restart.

```
AskQuestion({
  title: "{Agent} Blocked",
  questions: [{
    id: "blocked_action",
    prompt: "The {agent} hit its iteration cap (3 attempts).\n\nAgent: {agent-name}\nFailure: [FAILURE from BLOCKED output]\nPartial state: [PARTIAL_STATE from BLOCKED output]\n\nHow do you want to proceed?",
    options: [
      { id: "retry", label: "Retry — restart {Gate} with fresh context" },
      { id: "skip", label: "Skip gate with warning — continue pipeline (story marked degraded)" },
      { id: "abort", label: "Abort pipeline — preserve current state" }
    ]
  }]
})
```

**Skip with warning:** continue the pipeline but add a visible `⚠️ DEGRADED` flag to the final story report. The story is **NOT** marked `Completed ✅` — it carries the gate-specific note above.

---

## Quick Mode (`--quick`)

**Skips:** Gate 0 (arch-check), **Gate 0.5 (boundary map)**, Gate 3 (review), Gate 3.5 (drift handling), Gate 5 (docs)
**Keeps:** Gate 1 (coding/TDD), Gate 2 (lint + build smoke), Gate 4 (testing + coverage re-derivation)

Use for prototyping, spikes, internal tools. Run full pipeline later:
```
/implement-story story-3 --review-only
```

## Completion

This command succeeds when the story file reads `Status: Completed`, carries the completion commit SHA in its header, and ends with a `## What Was Built` section whose file and test counts match `user-stories/README.md`.

A story that cannot clear every gate is marked DEGRADED rather than Completed. That is a valid terminal state and must not be relabelled to make a batch look clean.

**Terminal constraint:** This command closes out one story. Do not start the next story, merge the branch, or update the roadmap.

---

## References

- Standing instructions: [`commands/_preamble.md`](_preamble.md)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)
- Skills, each loaded at the stage the Pipeline table names: [story-context-assembly](../skills/story-context-assembly/SKILL.md), [dependency-context-loading](../skills/dependency-context-loading/SKILL.md), [boundary-map-computation](../skills/boundary-map-computation/SKILL.md), [tdd-cycle](../skills/tdd-cycle/SKILL.md), [change-surface-classification](../skills/change-surface-classification/SKILL.md), [drift-triage](../skills/drift-triage/SKILL.md), [project-context-snapshot](../skills/project-context-snapshot/SKILL.md), [what-was-built-authoring](../skills/what-was-built-authoring/SKILL.md), [story-commit-provenance](../skills/story-commit-provenance/SKILL.md)
