---
name: implement-story
description: "Default: coding-agent + evaluator-agent and Stage 2b scripts. --full-pipeline is the six-agent hatch."
problem: "A story gets coded straight off its task list, so architecture fit, review, and coverage are skipped once the code looks right, and nothing records what was built for the stories downstream."
outcome: "One story file is closed out - status flipped, tasks and acceptance criteria checked, a What Was Built record appended, and the implementing commit SHA written into its header."
entry_level: high
exit_criteria:
  - "the story file header reads Status: Completed and carries a > **Commit:** line holding the full SHA of the completion commit, written once rather than duplicated on re-runs"
  - "the story file ends with a ## What Was Built section naming files created, files modified, and test results, and user-stories/README.md progress counts match it"
  - "Gate 4 recorded a 100 percent test pass rate with at least 80 percent line coverage on new files; designed default-path agent skips (arch, visual-qa, docs — scripts still run) are not DEGRADED; undesigned skips still are"
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
gates:
  # One per #### Gate heading: `script` re-derives the verdict; `prose-only`
  # means the agent's own report is the verdict. scripts/verdict-provenance.py.
  - id: gate0_arch
    script: scripts/arch-check.py
  - id: gate0_5_boundary
    script: scripts/boundary-map.py
  - id: gate1_coding
    verification: prose-only
  - id: gate2_build
    script: scripts/build-smoke.py
  - id: gate2_5_surface
    script: scripts/change-surface.py
  - id: gate3_review
    script: scripts/review-override.py
  - id: gate3_5_drift
    script: scripts/drift-format.py
  - id: gate4_tests
    script: scripts/test-integrity.py
  - id: gate4_5_visual
    verification: prose-only
  - id: gate5_docs
    script: scripts/docs-check.py
---

# Implement Story Command (implement-story)

## Overview

Default is two Task spawns (`coding-agent`, `evaluator-agent`) plus Stage 2b scripts — not the six-agent path. `--full-pipeline` is that hatch. The Pipeline table is the stage list.

This is the **per-story execution engine**. For full spec execution with dependency resolution and parallel batching, use `/implement-spec`.

## Required Artifacts

Verify per the preamble's **Artifact Integrity** rule before starting.

- **Required:** active spec folder (`spec.md`, `user-stories/`).
- **Optional:** `.writ/context.md`, `.writ/knowledge/`, `spec-lite.md`, `mockups/`.

## Invocation

| Invocation | Behavior |
|---|---|
| `/implement-story` | Interactive — presents story selection |
| `/implement-story story-3` | Default: `coding-agent` + `evaluator-agent` + scripts |
| `/implement-story story-3 --full-pipeline` | Six spawn sites: architecture-check, coding, review, testing, optional visual-qa, documentation |
| `/implement-story story-3 --quick` | `coding-agent` only (+ scripts); no evaluator |
| `/implement-story story-3 --review-only` | `evaluator-agent` only (+ scripts); no coding. FAIL ends the run; no recode; no silent `--full-pipeline` |

## Pipeline

One row per stage. The **Skill** column names what a stage loads; the `Read` is issued inside that stage, never here.

| Stage | Name | Runs as | Skipped in | Skill |
|---|---|---|---|---|
| Step 2 | Load Context | inline | — | `story-context-assembly`; `dependency-context-loading` (dependency branch only) |
| Gate 0 | Architecture Check | `arch-check.py` on default; `architecture-check-agent` on `--full-pipeline` | `--quick`, `--review-only` (agent); default is script-only | — |
| Gate 0.5 | Boundary Map | inline — data transformation | `--quick`, `--review-only`, `/prototype` | `boundary-map-computation` |
| Gate 1 | Coding Agent | `coding-agent` — TDD | `--review-only` | `tdd-cycle` |
| Gate 2 | Lint, Typecheck, Format & Build Smoke | inline — auto | — | — |
| Gate 2.5 | Change Surface | inline | — | `change-surface-classification` |
| Gate 3 | Review Agent | `evaluator-agent` on default; `review-agent` on `--full-pipeline` | `--quick` | — |
| Gate 3.5 | Drift Response & WWB Extraction | inline — auto | `--quick` | `drift-triage` (§ A) |
| Gate 4 | Testing Agent | `test-integrity.py` on default (no testing-agent spawn); `testing-agent` on `--full-pipeline` | — | — |
| Gate 4.5 | Visual QA | `visual-qa-agent` on `--full-pipeline` only | `--quick`; no visual references; default (even with visual refs) | — |
| Gate 5 | Documentation Agent | `docs-check.py` on default; `documentation-agent` on `--full-pipeline` | `--quick` | — |
| Step 4 | Story Completion | inline | — | `project-context-snapshot` (item 3); `what-was-built-authoring` (item 4); `story-commit-provenance` (item 7) |

**Control flow:** Gate 0 ABORT ask-user is `--full-pipeline` only (confirmed at anchor). Default Gate 0 is script-only. Gate 3 emits **PAUSE** on Large drift; Gate 3.5 § A owns that pause and its three options (accept / reject / modify-spec) — stated once there. Gate 3, Gate 4 and Gate 4.5 FAIL → back to Gate 1 (max 3 iterations total across review + visual QA). `evaluator_fail_count` starts at 0 per story; evaluator FAIL increments it; first FAIL → Gate 1 recode (counts toward review_cycle); second consecutive FAIL → print one notice that the remainder of this story runs as `--full-pipeline` (current gate forward; do not restart Gate 0; do not AskQuestion); Reset the counter on evaluator PASS. `--quick` never escalates.

## Command Process

### Step 1: Story Selection

If no argument provided, present story selection from current spec (not-started and in-progress stories).

### Step 2: Load Context

1. **Read `.writ/context.md`** (if present) — product mission, active spec state, recent drift, open issues. First context item; primes later steps.
2. **Read the story file** — tasks, acceptance criteria, dependencies
3. **Read spec-lite.md** — overall spec context
4. **Parse context hints and fetch referenced content** — invoke the assembler below
5. **Load knowledge context** — grep `.writ/knowledge/` for story keywords; optional `knowledge_context` (≤2KB) for spawned agents
6. **Extract agent-specific spec-lite sections** — parse spec-lite.md into per-role sections
7. **Scan codebase** — patterns, related files, tech stack
8. **Check dependencies** — warn if upstream stories aren't complete
9. **Load "What Was Built" from dependencies** — only when the story declares dependencies
10. **Load visual references** — if `## Visual References`: read mockups, `mockups/component-inventory.md`, `.writ/docs/design-system.md`; pass to the coding agent

If dependencies are incomplete:
```
⚠️ Story 5 depends on Story 2 (not yet complete).
Proceeding anyway — some integration points may be unavailable.
```

**Context assembly (items 4–6).** Delegate hint parsing and fetching to `scripts/story-context.py`, the sole implementation — do not interpret `## Context for Agents` here:

```bash
python3 scripts/story-context.py assemble --story <story-file-path> --budget-bytes 21000
```

`Read skills/story-context-assembly/SKILL.md` for how the payloads are built. This step owns when assembly runs and who receives what (routing table below); the skill owns how. Outputs: `fetched_context`, `context_warnings`, `knowledge_context`, `spec_lite_for_coding` / `spec_lite_for_review` / `spec_lite_for_testing`.

**Routing table — what each agent receives:**

| Agent | Spec-Lite Section | Supplementary Context (from hints) |
|---|---|---|
| Architecture Check (Gate 0) | `spec_lite_for_coding` | `fetched_context` (all categories) + `knowledge_context` |
| Coding Agent (Gate 1) | `spec_lite_for_coding` | `fetched_context` (error maps, business rules) + `knowledge_context` + dependency WWB records |
| Review Agent (Gate 3) | `spec_lite_for_review` | `fetched_context` (business rules, experience) + `knowledge_context` |
| Testing Agent (Gate 4) | `spec_lite_for_testing` | `fetched_context` (shadow paths, edge cases) |
| Documentation Agent (Gate 5) | Full spec-lite content | `fetched_context` (all categories) |

**Dependency records (item 9).** **If — and only if — the story declares dependencies**, load the completed upstream stories' "What Was Built" records into `dependency_wwb_context`, which Gate 1 routes to the coding agent. Skip reverted records: one carrying a `> **Reverted:**` banner is not authoritative and is never loaded as live dependency context. A story with no dependencies skips this branch entirely.

`Read skills/dependency-context-loading/SKILL.md` for how those records are located, filtered, truncated and aggregated. This step owns whether the branch runs at all; the skill owns how the block is built.

### Step 3: Run Pipeline

> **Context refresh:** `.writ/context.md` is regenerated once at Story Completion (Step 4), not between gates. Each write replaces the entire file — do not append, merge, or patch.

> **File creation discipline:** Agents must only create files listed in the story's implementation tasks. Analysis artifacts stay in structured output. Do not commit files outside the task list or known pipeline outputs (drift-log, context.md, story status).

> **Sub-agent completeness:** `Read skills/subagent-result-completeness/SKILL.md`
> for how to tell a spawned gate agent's complete verdict from a mid-task
> stop, and what to do about the latter. This note owns when every default
> spawn (Gate 1 and Gate 3) checks for completeness before advancing;
> `--full-pipeline` also Gate 0, 4, 4.5. The skill owns how to tell a complete
> verdict from a partial one.

> **Sub-agent worktree integration:** `Read skills/subagent-worktree-integration/SKILL.md`
> for how to reconcile a spawned agent's isolated worktree with the
> orchestrator's own checkout, including the stale-worktree failure mode.
> This note owns when every default spawn (Gate 1 and Gate 3) reconciles isolated
> output before trusting it; `--full-pipeline` also Gate 0, 4, 4.5. The skill owns
> how the diff → copy → re-verify → cleanup procedure runs.

---

#### Gate 0: Architecture Check (Pre-Implementation)

> **Skip in:** `--quick` mode, `--review-only` mode (agent). Default is script-only.

**Default:** do not spawn `architecture-check-agent`. Run the script only. If no `--planned` set from an architecture agent, pass story-task planned files or omit (script `unverifiable` continues; not DEGRADED).

**Verify the claim, don't trust it.** After an architecture-check agent returns PROCEED or CAUTION — never on ABORT; do not invoke this script on an ABORT-shaped result — and always on default, run:

```bash
python3 scripts/arch-check.py check --story <story-file> --repo . --planned <planned files> [--boundary <map.json>]
```

`--planned` is Gate 0's live pre-implementation set. `--changed` is replay / post-hoc only. The script never prints `abort`; the ABORT path and the ADR-024 floor→anchor re-run stay `--full-pipeline` only.

- **`rederived: caution`** → inject the script `reason` into the coding-agent warnings.
- **script `fail`** → apply the shared [BLOCKED escalation](#blocked-agent-escalation).
- **`rederived: proceed`** → continue.
- **any `unverifiable` verdict** → the pipeline continues, the reason is surfaced verbatim, and the story is **not** marked `⚠️ DEGRADED` on that basis alone.

**`--full-pipeline`:**
> **Agent:** `agents/architecture-check-agent.md`

Spawn a **read-only** sub-agent before code: viability, integration risk, complexity, gaps. **PROCEED** → code · **CAUTION** → inject warnings · **ABORT** → present findings, ask proceed/modify/skip.

**Context routing:** Pass `spec_lite_for_coding` as `spec_lite_content`; if agent-specific sections are unavailable, pass full spec-lite. Also pass `fetched_context` when hints were parsed in Step 2, and `knowledge_context` when populated.

**Anchor confirmation (ADR-024):** a `floor` **ABORT** is provisional. Before presenting anything, re-run `architecture-check-agent` once at `anchor` (platform `inherit`) with the identical prompt, `spec_lite_content`, `fetched_context`, and `knowledge_context`. The anchor verdict stands: PROCEED/CAUTION continue as that verdict with no AskQuestion and no user-visible line; ABORT presents findings and asks proceed/modify/skip as above. A floor PROCEED/CAUTION is never re-run; `--quick`/`--review-only` skip Gate 0, so no escalation path exists there; a spawn error follows the existing **Agent crash** handling (§ Error Handling), not this branch — escalation fires only on a returned verdict. On the re-run emit `(no-op until ADR-025 Story 1) escalated(agent=architecture-check-agent, site=implement-story.gate0, origin=<model>/<effort>@<platform>)`, stamping the origin captured at command entry (`system-instructions.md` § Model Tiers), never re-read or asked here. The line has no sink today: ADR-025 Story 1 has not shipped the recorder it names, so the emit is a printed line nothing reads — do not look for a `scripts/signal.py` or a `/retro --friction` consumer. Iteration accounting: the floor attempt and its anchor re-run count as one attempt against `loop.max_iterations`; Gate 0 runs before the `review_cycle` counter exists and does not consume an iteration.

---

#### Gate 0.5: Boundary Computation (File Ownership Map)

> **Agent:** None — **inline orchestration step** (data transformation, not a judgment call)
> **Skip in:** `--quick` mode, `--review-only` mode, `/prototype` path

Before Gate 1, compute **`boundary_map`** (owned / readable / out-of-scope). **Advisory** — no hard file locking. Coding flags crossings; review verifies (Gate 3).

**Not applicable — `/prototype`:** `commands/prototype.md` does not run `implement-story`; that path stays boundary-free. Gate 0.5 exists only on the full pipeline.

`Read skills/boundary-map-computation/SKILL.md` for how the map is derived, including where assess-spec Check 5 overlap data is persisted and how it degrades when absent. This gate owns when it is computed and that Gates 1 and 3 receive it as `boundary_map`; the skill owns how.

Run the checkable artifact and pass stdout onward — maps stay **advisory** (no hard file locking):

```bash
python3 scripts/boundary-map.py compute --story <story-file> --repo . [--overlap <check-5-overlap>]
```

---

#### Gate 1: Coding Agent (TDD Implementation)

> **Agent:** `agents/coding-agent.md`
> **Skip in:** `--review-only` mode

Spawns the coding agent to run the red → green → refactor loop via `Read skills/tdd-cycle/SKILL.md`, with full story context, optional `knowledge_context`, any arch-check warnings, and **`boundary_map`** from Gate 0.5. This gate owns when coding runs, the context it routes below, and `STATUS: BLOCKED` handling; the skill owns how the test-first cycle runs.

**Context routing:** Pass `spec_lite_for_coding` as `spec_lite_content` and relevant `fetched_context` (error maps, business rules). Pass `knowledge_context` after spec context and before dependency records when populated. If dependencies have completed "What Was Built" records (loaded in Step 2), pass aggregated `dependency_wwb_context` — positioned after knowledge context, before implementation tasks.

**When Gate 0.5 was skipped** (`--quick`, `--review-only`): pass **`boundary_map`** = the literal `(none)` and do **not** pass a boundary block — coding/review agents treat `(none)` as “no boundary checking” (see `agents/coding-agent.md`).

**Report:** files changed, tests written, deviations from plan, concerns.

**On `STATUS: BLOCKED`:** apply the shared [BLOCKED escalation](#blocked-agent-escalation) with agent `coding-agent`, restarting **Gate 1**; skip-with-warning marks the story `In Progress` with the note *"Gate 1 skipped after BLOCKED — review required."*

---

#### Gate 2: Lint, Typecheck, Format & Build Smoke

**Runs inline — no sub-agent needed.**

Auto-detect and run project linters — **Node/TS:** `tsc --noEmit`, `eslint`, `prettier --check` · **Python:** `mypy`, `ruff`, `black --check` · **Rust:** `cargo check`, `cargo clippy`, `cargo fmt --check`.

**On failure:** auto-fix (`eslint --fix`, `prettier --write`, `black`, `cargo fmt`); re-run; typecheck fail → coding agent; still failing → flag for review.

**Build smoke.** When the story changed source, also run `python3 scripts/build-smoke.py check --project .` and surface its verdict in the story report. Typechecking cannot see framework-level structural errors — a route collision breaks every deployment and passes every unit test that imports handlers as plain functions.

- **`build_failed_source`** → blocking. Apply the shared [BLOCKED escalation](#blocked-agent-escalation) with agent `coding-agent`, restarting **Gate 2**. No new control flow, no iteration cap.
- **`build_failed_environment` or any `unverifiable` verdict** → the pipeline continues. Surface the reason verbatim; the story is **not** marked `⚠️ DEGRADED` on that basis. An unverifiable check is not a failed gate — DEGRADED means a gate could not be cleared, `unverifiable` means a check could not be run here.

---

#### Gate 2.5: Change Surface Classification

**Runs inline — no sub-agent needed.**

After lint/typecheck, classify changed files as **style-only**, **single-component**, **cross-component** or **full-stack** and pass Gate 3 `change_surface`. Optionally cross-check against **`boundary_map`** (Gate 0.5) — **full-stack** warrants stricter review here.

`Read skills/change-surface-classification/SKILL.md` for how the four classes are told apart. This gate owns when classification runs and who consumes `change_surface`; the skill owns how the class is decided.

Run the path-heuristic classifier and pass stdout to Gate 3 as `change_surface`:

```bash
python3 scripts/change-surface.py classify --changed <files>
```

---

#### Gate 3: Review Agent

> **Agent:** `agents/evaluator-agent.md`
> **Skip in:** `--quick` mode
> **`--review-only`:** evaluator-only (+ scripts); FAIL ends the run; no recode; no silent hatch

Default spawn is `evaluator-agent` (AC + recorded tests). Verdict field: `EVALUATION_RESULT` or `REVIEW_RESULT`.

**`--full-pipeline`:**
> **Agent:** `agents/review-agent.md`

Spawn `review-agent` instead. Same inputs: `spec_lite_for_review` as `spec_lite_content`, optional `knowledge_context`, `change_surface` (Gate 2.5), **`boundary_map`**, optional `boundary_overlap_summary`.

**Results:** **PASS** → continue (Small/Medium drift ok) · **FAIL** → Gate 1 recode · **PAUSE** → Large drift; Gate 3.5 § A owns options. Two-fail: Pipeline control flow.

**Review loop:** Max 3 iterations across review and visual QA gates (Gate 3 FAIL → recode, Gate 3.5 "Reject" → recode, Gate 3.5 "Modify spec" → re-review, Gate 4.5 FAIL → recode all count). Those four sites share one counter — they are not four independent budgets. An escalated Gate 0 re-run (or `/create-spec` Step 2.6a regeneration) never increments it — the floor attempt and its anchor re-run are one attempt. Gate 4 testing failures have a separate 2-iteration cap. After either cap → escalate to user. Both caps are declared as `loop.max_iterations` and the nested `testing_cycle` entry in this file's frontmatter, with `on_exhaustion: escalate`: the existing `AskQuestion` escalations are the implementation, and no cap may be silently continued past.

**Verify the claim, don't trust it.** After the Gate 3 agent returns, run:

```bash
python3 scripts/review-override.py check --spec <spec-folder> --repo . --story <story-file> [--new-files <story's new files>] [--tests <story's test files>]
```

The agent's PASS/FAIL is a field the agent types. The checker re-derives a mechanical verdict from `ac-trace.py` and (when those path flags are present) `test-integrity.py`, and show both the claim and the measurement in the story report.

This override is **FAIL-only**: a script `fail` takes the existing review-loop recode path (Gate 3 FAIL → recode). A script `pass` or `unverifiable` leaves the evaluator FAIL or PAUSE standing — a mechanical pass does not force PASS and does not wash an evaluator FAIL. Residual architecture, security, and taste stay with `evaluator-agent` on default and `review-agent` on `--full-pipeline`.

- **script `fail`** (`untested_criterion` after the story would be complete, `untasked_criterion`, `dangling_reference`, `duplicate_id`, or `coverage_below_threshold` / `coverage_regression` / `test_imports_no_source`) → blocking. Take the existing review-loop recode path.
- **script `pass` or any `unverifiable` verdict** → the agent's FAIL or PAUSE stands. The pipeline continues on an agent PASS; the reason is surfaced verbatim, and the story is **not** marked `⚠️ DEGRADED` on that basis alone.

#### Gate 3.5: Drift Response Handling & "What Was Built" Extraction

> **Format reference:** `.writ/docs/drift-report-format.md`, `.writ/docs/what-was-built-format.md`

After the Gate 3 agent returns, perform two operations:

##### A. Drift Response

Inspect the `### Drift Analysis` section and handle by severity: **Small** (naming/cosmetic — auto-amend `spec-lite.md` only, log a `DEV-NNN` entry, PASS); **Medium** (scope/integration impact — ⚠️ warn, log, PASS); **Large** (fundamental deviation — the **PAUSE** Gate 3 emitted lands here: present accept / reject / modify-spec, wait for the decision; this is the only place those options are offered). `spec.md` is never auto-modified.

`Read skills/drift-triage/SKILL.md` for how each severity is handled, including the mixed-severity rule and the append-only `drift-log.md` rules. This gate owns when triage runs and that a Large drift pauses the pipeline and asks the user; the skill owns how.

**Verify the claim, don't trust it.** After the drift step, format-check only — this script never decides accept / reject / modify-spec:

```bash
python3 scripts/drift-format.py check --story <story-file> [--drift-log <spec>/drift-log.md] [--review-output <review-agent stdout>]
```

- **script `fail`** → apply the shared [BLOCKED escalation](#blocked-agent-escalation).
- **any `unverifiable` verdict** → the pipeline continues, the reason is surfaced verbatim, and the story is **not** marked `⚠️ DEGRADED` on that basis alone.

##### B. "What Was Built" Data Extraction

Extract implementation data from the Gate 3 agent's output into `what_was_built_data` and hold it in orchestrator state, parsing defensively with a fallback for every field. **Do NOT append to the story file yet.**

Data flow: **Gate 3.5** extracts and validates; **Gate 4** updates `what_was_built_data.test_results`; **Step 4 item 4** formats and appends. The extraction sources, their mandatory/best-effort semantics and their fallback values live in `what-was-built-authoring`, loaded once at Step 4 item 4 alongside the formatting rules they feed.

---

#### Gate 4: Testing Agent (with Coverage Enforcement)

**Default:** do not spawn `testing-agent`. Run the scripts below.

**`--full-pipeline`:**
> **Agent:** `agents/testing-agent.md`

**Context routing:** Pass `spec_lite_for_testing` as `spec_lite_content` — success criteria, shadow paths, and edge cases relevant to testing. If agent-specific sections not available, pass full spec-lite.

**Process:** (1) run story-specific tests; (2) run regression tests (related suites); (3) run coverage analysis; (4) fix failures, preferring to fix the implementation over changing tests; (5) add missing test coverage if needed.

**Requirements:** **100% test pass rate** — mandatory · **≥80% line coverage on new files** — mandatory · **coverage must not decrease on modified files**.

**On failure:** Send test output back to coding agent. 2 fix iterations max (separate from the review loop's 3-iteration cap), then escalate.

**On `STATUS: BLOCKED` (`--full-pipeline`):** apply the shared [BLOCKED escalation](#blocked-agent-escalation) with agent `testing-agent`, restarting **Gate 4**; skip-with-warning continues to Gate 5 with the story marked `⚠️ DEGRADED`.

**Verify the claim, don't trust it.** After scripts (and the testing agent on `--full-pipeline`) return, run:

```bash
python3 scripts/test-integrity.py coverage --project . --new-files <story's new files>
python3 scripts/test-integrity.py authenticity --project . --tests <story's test files>
```

`Coverage threshold met: YES` is a field the agent types. The checker re-derives it from the coverage tool's own output, and where they disagree the checker wins — a run may report `TEST_RESULT: PASS` and still not close, as `scripts/exit-criteria.py` lets a run report COMPLETE and be published `unmet`. Show both the claim and the measurement in the story report.

- **`coverage_below_threshold`, `coverage_regression`, or `test_imports_no_source`** → blocking. The story does not reach `Completed ✅`. `test-integrity.py` `fail`: default uses [BLOCKED escalation](#blocked-agent-escalation) with agent `coding-agent`, restarting **Gate 1**; `--full-pipeline` keeps `testing-agent`, restarting **Gate 4**. Do not downgrade the story silently.
- **Any `unverifiable` verdict** → the pipeline continues, the reason is surfaced verbatim, and the story is **not** marked `⚠️ DEGRADED` on that basis alone.

---

#### Gate 4.5: Visual QA (Optional)

**Default:** skip — no `visual-qa-agent` spawn even with visual refs.

**`--full-pipeline`:**
> **Agent:** `agents/visual-qa-agent.md`
> **Skip in:** `--quick` mode, when no visual references exist for this story

**Auto-activates when:** the story has a `## Visual References` section, or the spec has a `mockups/` directory with files.

`--full-pipeline` spawn: read-only UI capture vs story mockups; report structural, spacing, styling mismatches.

**Results:** **PASS** (no mismatches, or none the agent rates above low) → continue to docs · **SOFT PASS** (only cosmetic, medium-or-low mismatches) → continue, log issues · **FAIL** (any high-priority mismatch, or structural drift from the mockup) → send fixes back to coding agent

The former match-percentage thresholds are gone: no pixel or DOM diff produced the number, so the verdict rests on the agent's per-aspect mismatch list, and the `gates:` frontmatter records this gate as `prose-only`.

Failures count toward the shared review-loop cap declared at Gate 3.

---

#### Gate 5: Documentation Agent

> **Skip in:** `--quick` mode

**Default:** do not spawn `documentation-agent`. Run the script only.

**`--full-pipeline`:**
> **Agent:** `agents/documentation-agent.md`

**Context routing:** Pass full spec-lite content as `spec_context`. Also pass `fetched_context` if available.

**Auto-detects the docs framework** (VitePress, Docusaurus, Nextra, MkDocs, Storybook, or plain README). Updates inline docs, README, CHANGELOG, framework pages, diagrams as needed.

**Verify the claim, don't trust it.** After the documentation agent returns (or immediately on default), run:

```bash
python3 scripts/docs-check.py check --repo . [--changed <story's changed files>]
```

- **script `fail`** → apply the shared [BLOCKED escalation](#blocked-agent-escalation) with agent `documentation-agent`, restarting **Gate 5**.
- **any `unverifiable` verdict** → the pipeline continues, the reason is surfaced verbatim, and the story is **not** marked `⚠️ DEGRADED` on that basis alone.

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

**Item 3 — the snapshot.** `Read skills/project-context-snapshot/SKILL.md` for what `.writ/context.md` contains. This step owns when regeneration happens — once, here, never between gates. `implement-spec` and `status` regenerate the same schema.

**Item 4 — the record.** `Read skills/what-was-built-authoring/SKILL.md` for how the record is extracted and formatted. A `--quick` run reaches this step with no `what_was_built_data` and still writes the minimal record, which is why the skill loads here, not at Gate 3.5.

**Item 7 — provenance.** `Read skills/story-commit-provenance/SKILL.md` for how the SHA is captured, placed idempotently, and landed without amending the commit it names. Written right after item 6's commit; `/revert` and `scripts/revert-resolve.py` consume it.

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

**Skip with warning:** continue the pipeline but add a visible `⚠️ DEGRADED` flag to the final story report. The story is not marked `Completed ✅` — it carries the gate-specific note above.

---

## Quick Mode (`--quick`)

**Skips:** Gate 0 agent, **Gate 0.5 (boundary map)**, Gate 3 (evaluator), Gate 3.5 (drift handling), Gate 5 agent. `--quick` never escalates.
**Keeps:** Gate 1 (`coding-agent` + scripts), Gate 2 (lint + build smoke), Gate 4 scripts, Gate 0/5 scripts

Use for prototyping, spikes, internal tools. Hatch later via `--full-pipeline`:
```
/implement-story story-3 --full-pipeline
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
