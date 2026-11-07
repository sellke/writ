---
name: implement-story
description: "Default: coding-agent + evaluator-agent and Stage 2b scripts. --full-pipeline is the six-agent hatch."
problem: "A story gets coded straight off its task list, so architecture fit, review, and coverage are skipped once the code looks right, and nothing records what was built for the stories downstream."
outcome: "One story file is closed out - status flipped, tasks and acceptance criteria checked, a What Was Built record appended, and the implementing commit SHA written into its header."
entry_level: high
exit_criteria:
  - "the story file header reads Status: Completed and carries a > **Commit:** line holding the full SHA of the completion commit, written once rather than duplicated on re-runs"
  - "the story file ends with a ## What Was Built section naming files created, files modified, and test results, and user-stories/README.md progress counts match it"
  - "Gate 4 recorded a 100 percent test pass rate with at least 80 percent line coverage on new files; designed default-path skips (Gates 0, 4.5 and 5 run only under --full-pipeline) are not DEGRADED; undesigned skips still are"
loop:
  unit: "review_cycle"
  max_iterations: 3
  on_exhaustion: escalate
  calibrated_against: "One shared counter across four increment sites - Gate 3 FAIL, Gate 3.5 Reject, Gate 3.5 Modify spec, Gate 4.5 script fail - not four separate budgets. Transcribes the prose cap in commands/implement-story.md: 'Review loop: Max 3 iterations across review and Gate 4.5'. When this bound was set, no Writ story run needed more than 2; 3 leaves one iteration of headroom."
  nested:
    - unit: "testing_cycle"
      max_iterations: 2
      on_exhaustion: escalate
      calibrated_against: "Transcribes the Gate 4 prose cap in commands/implement-story.md: '2 fix iterations max (separate from the review loop's 3-iteration cap)'. When this bound was set, no Writ story run needed a second testing fix. The original derivation of the 2 is not recorded, so do not read it as measured."
    - unit: "agent_self_fix"
      max_iterations: 3
      on_exhaustion: escalate
      calibrated_against: "Transcribes MAX_SELF_FIX_ITERATIONS = 3, declared in agents/coding-agent.md and agents/testing-agent.md and consumed by this file's STATUS: BLOCKED handlers at Gate 1 and Gate 4. Evidence: strong - two agent definitions already enforce it; this declaration must not drift from them."
gates:
  # One per #### Gate heading: `script` re-derives the verdict; `prose-only`
  # means the agent's own report is the verdict. scripts/verdict-provenance.py.
  - id: gate0_arch
    script: scripts/arch-check.py
    path: full-pipeline
    catches: "A story planned against files or layers that do not fit the design; cost: rework after the code exists"
    evidence: "none recorded"
    kill_when: "gate-evidence.md still reads none recorded for this gate on 2027-05-06"
  - id: gate0_5_boundary
    script: scripts/boundary-map.py
    path: default
    catches: "Edits outside the files a story owns; cost: parallel stories collide and the crossing reaches review unflagged"
    evidence: "none recorded"
    kill_when: "gate3_review leaves the default path; its risk route, which turns Safety Fact on, reads this map"
  - id: gate1_coding
    verification: prose-only
    path: default
    catches: "Story tasks coded with no failing test first; cost: untested code reaches review"
    evidence: "none recorded"
    kill_when: "every other gates entry leaves the default path, so no default check reads the code"
  - id: gate2_build
    script: scripts/build-smoke.py
    path: default
    catches: "Lint, type, or build errors in the changed code; cost: a broken build reaches review"
    evidence: "none recorded"
    kill_when: "gate3_review leaves the default path (its evidence gate reruns the check commands Gate 2 saves) and sole_catches == 0 over 20 default-path records"
  - id: gate2_5_surface
    script: scripts/change-surface.py
    path: default
    catches: "Risky diff reviewed by the light evaluator; cost: a cross-component defect ships unreviewed"
    evidence: "none recorded"
    kill_when: "gate3_review leaves the default path; Safety Fact reads this gate's risk route and blast radius"
  - id: gate3_review
    script: scripts/review-override.py
    path: default
    catches: "Code that misses an acceptance criterion or breaks a caller; cost: a Major defect ships"
    evidence: "lean-story-tasks trial (2026-11-06): evaluator failed a Major data-loss defect, fixed on recode; gate-upgrade trial (2026-11-04): Safety Fact 2 valid catches, Reviewer Filters 1"
    kill_when: "sole_catches == 0 over 20 default-path records for every gate3_review check"
  - id: gate3_5_drift
    script: scripts/drift-format.py
    path: default
    catches: "A departure from the spec with no recorded decision; cost: the spec and the code disagree unnoticed"
    evidence: "ci-and-update-integrity DEV-007 (2026-10-20): an evaluator Large-drift PAUSE was rejected at Gate 3.5 and recoded, so customized Cursor files are no longer overwritten"
    kill_when: "20 default-path stories log no drift-log.md Resolution of Pipeline paused — rejected or spec modified"
  - id: gate4_tests
    script: scripts/test-integrity.py
    path: default
    catches: "Coverage below threshold or a test that cannot fail; cost: a regression passes the suite"
    evidence: "Phase 15 retro (2026-10-30) F26: on 2026-10-26 authenticity blocked a test that imported no source, and the test was rewritten"
    kill_when: "sole_catches == 0 over 20 default-path records"
  - id: gate4_5_behavior
    script: scripts/app-verify.py
    path: full-pipeline
    catches: "A change that passes its tests but breaks the running app; cost: a user-visible failure ships"
    evidence: "none recorded"
    kill_when: "gate-evidence.md still reads none recorded for this gate on 2027-05-06"
  - id: gate5_docs
    script: scripts/docs-check.py
    path: full-pipeline
    catches: "Public exports changed without matching docs; cost: users follow stale docs"
    evidence: "none recorded"
    kill_when: "gate-evidence.md still reads none recorded for this gate on 2027-05-06"
---
<!-- generated by scripts/gen-platform-trees.py from commands/implement-story.md — do not hand-edit; regenerate -->

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
| `/implement-story story-3` | Default: `coding-agent` + `evaluator-agent` (or `review-agent` when Gate 2.5 routes it) + scripts |
| `/implement-story story-3 --full-pipeline` | Six spawn sites: architecture-check, coding, review, testing, optional visual-qa, documentation |
| `/implement-story story-3 --quick` | `coding-agent` only (+ scripts); no evaluator |
| `/implement-story story-3 --review-only` | `evaluator-agent` only (+ scripts); no coding. FAIL ends the run; no recode; no silent `--full-pipeline` |

`--full-pipeline`, `--quick`, `--review-only` are mutually exclusive: on a conflict, stop with a usage error before any gate; pick no winner. `--panel` stops: `--panel was removed (ADR-032)`.

## Pipeline

One row per stage. The **Skill** column names what a stage loads; the `Read` is issued inside that stage, never here.

| Stage | Name | Runs as | Skipped in | Skill |
|---|---|---|---|---|
| Step 2 | Load Context | inline | — | `story-context-assembly`; `dependency-context-loading` (dependency branch only) |
| Gate 0 | Architecture Check | `architecture-check-agent`, then `arch-check.py` | all but `--full-pipeline` | — |
| Gate 0.5 | Boundary Map | inline — data transformation | `--quick`, `--review-only`, `/prototype` | `boundary-map-computation` |
| Gate 1 | Coding Agent | `coding-agent` — TDD | `--review-only` | `tdd-cycle` |
| Gate 2 | Lint, Typecheck, Format & Build Smoke | inline — auto | — | — |
| Gate 2.5 | Change Surface | inline | — | `change-surface-classification` |
| Gate 3 | Review Agent | `evaluator-agent` on default, or `review-agent` when Gate 2.5 routes it; `review-agent` on `--full-pipeline` | `--quick` | — |
| Gate 3.5 | Drift Response & WWB Extraction | inline — auto | `--quick` | `drift-triage` (§ A) |
| Gate 4 | Testing Agent | `test-integrity.py` on default (no testing-agent spawn); `testing-agent` on `--full-pipeline` | — | — |
| Gate 4.5 | Behavioral Verification | `app-verify.py`, then notes-only `visual-qa-agent` on visual refs | all but `--full-pipeline` | — |
| Gate 5 | Documentation Agent | `documentation-agent`, then `docs-check.py` | all but `--full-pipeline` | — |
| Step 4 | Story Completion | inline | — | `project-context-snapshot` (item 3); `what-was-built-authoring` (item 4); `story-commit-provenance` (item 7) |

**Control flow:** Gates 0, 4.5 and 5 run only under `--full-pipeline`, where Gate 0 ABORT asks the user (confirmed at anchor). Gate 3 emits **PAUSE** on Large drift; Gate 3.5 § A owns that pause and its three options (accept / reject / modify-spec) — stated once there. Gate 3, Gate 4 and (`--full-pipeline`) Gate 4.5 FAIL → back to Gate 1 (max 3 iterations total across review + Gate 4.5). `evaluator_fail_count` starts at 0 per story; Gate 3 FAIL (either agent) increments it; first FAIL → Gate 1 recode (counts toward review_cycle); second consecutive FAIL → print one notice that the remainder of this story runs as `--full-pipeline`, then Gate 1 recode as for any FAIL; the next Gate 3 spawns `review-agent` (do not restart Gate 0; do not AskQuestion); Reset the counter on Gate 3 PASS. `--quick` never escalates.

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
| Evaluator Agent (Gate 3, default) | `spec_lite_for_review` + `contract_content` (`spec.md` `## Specification Contract` verbatim; `""` if absent) | `knowledge_context` + AC + `recorded_test_results` |
| Review Agent (Gate 3) | `spec_lite_for_review` + `contract_content` | `fetched_context` (business rules, experience) + `knowledge_context` |
| Testing Agent (Gate 4) | `spec_lite_for_testing` | `fetched_context` (shadow paths, edge cases) |
| Documentation Agent (Gate 5) | Full spec-lite content | `fetched_context` (all categories) |

**Dependency records (item 9).** **If — and only if — the story declares dependencies**, load the completed upstream stories' "What Was Built" records into `dependency_wwb_context`, which Gate 1 routes to the coding agent. Skip reverted records: one carrying a `> **Reverted:**` banner is not authoritative and is never loaded as live dependency context. A story with no dependencies skips this branch entirely.

`Read skills/dependency-context-loading/SKILL.md` for how those records are located, filtered, truncated and aggregated. This step owns whether the branch runs at all; the skill owns how the block is built.

### Step 3: Run Pipeline

> **`--full-pipeline`:** Gate 0 (§ Full-Pipeline Gates) runs before Gate 0.5.

> **Context refresh:** `.writ/context.md` is regenerated once at Story Completion (Step 4), not between gates. Each write replaces the entire file — do not append, merge, or patch.

> **File creation discipline:** Agents must only create files listed in the story's implementation tasks. Analysis artifacts stay in structured output. Do not commit files outside the task list or known pipeline outputs (drift-log, context.md, story status).

> **Sub-agent completeness:** `Read skills/subagent-result-completeness/SKILL.md`
> for how to tell a complete verdict from a mid-task stop. This note owns when:
> every spawn (Gate 1 and Gate 3; `--full-pipeline` also Gate 0, 4, 4.5) checks
> completeness before advancing.

> **Sub-agent worktree integration:** `Read skills/subagent-worktree-integration/SKILL.md`
> for how to reconcile a spawned agent's isolated worktree (diff → copy →
> re-verify → cleanup, stale-worktree failure mode). This note owns when: every
> spawn (Gate 1 and Gate 3; `--full-pipeline` also Gate 0, 4, 4.5) reconciles
> before its output is trusted.

---

#### Gate 0.5: Boundary Computation (File Ownership Map)

> **Agent:** None — **inline orchestration step** (data transformation, not a judgment call)
> **Skip in:** `--quick` mode, `--review-only` mode, `/prototype` path

Before Gate 1, compute **`boundary_map`** (owned / readable / out-of-scope). **Advisory** — no hard file locking. Coding flags crossings; review verifies (Gate 3).

`Read skills/boundary-map-computation/SKILL.md` for how the map is derived, including where assess-spec Check 5 overlap data is persisted and how it degrades when absent. This gate owns when it is computed and that Gates 1 and 3 receive it as `boundary_map`; the skill owns how.

Run it; pass stdout onward (treat `blocker` as empty) and save it for pre-review:

```bash
mkdir -p .writ/state && python3 scripts/boundary-map.py compute --story <story-file> --repo . [--overlap <check-5-overlap>] | tee .writ/state/boundary-<story-stem>.json
```

---

#### Gate 1: Coding Agent (TDD Implementation)

> **Agent:** `agents/coding-agent.md`
> **Skip in:** `--review-only` mode

Spawns the coding agent to run the red → green → refactor loop via `Read skills/tdd-cycle/SKILL.md`, with full story context, optional `knowledge_context`, any arch-check warnings, and **`boundary_map`** from Gate 0.5. This gate owns when coding runs, the context it routes below, and `STATUS: BLOCKED` handling; the skill owns how the test-first cycle runs.

**Context routing:** Pass `spec_lite_for_coding` as `spec_lite_content` and relevant `fetched_context` (error maps, business rules). Pass `knowledge_context` after spec context and before dependency records when populated. If dependencies have completed "What Was Built" records (loaded in Step 2), pass aggregated `dependency_wwb_context` after knowledge context, before implementation tasks.

**When Gate 0.5 was skipped** (`--quick`, `--review-only`): pass **`boundary_map`** = the literal `(none)` and do **not** pass a boundary block — coding/review agents treat `(none)` as “no boundary checking”.

**Base:** record `git rev-parse HEAD` as `<base>` before the story's first Gate 1 spawn (`--review-only`: before the story's code); reuse it on recodes.

**Report:** files changed, tests written, deviations from plan, concerns.

**Bug path:** when the report's `### Repro` block names commits, post-review runs `repro-order.py check` from `<base>` after integration; print its check line as `repro-order:` in the Step 4 report. `fail` marks the story `⚠️ DEGRADED` with its `reason:` lines; `unverifiable`, or exit 2 with its stderr cause, prints and continues.

**On `STATUS: BLOCKED`:** apply the shared [BLOCKED escalation](#blocked-agent-escalation) with agent `coding-agent`, restarting **Gate 1**; skip-with-warning marks the story `In Progress` with the note *"Gate 1 skipped after BLOCKED — review required."*

---

#### Gate 2: Lint, Typecheck, Format & Build Smoke

**Runs inline — no sub-agent needed.**

Auto-detect and run project linters — **Node/TS:** `tsc --noEmit`, `eslint`, `prettier --check` · **Python:** `mypy`, `ruff`, `black --check` · **Rust:** `cargo check`, `cargo clippy`, `cargo fmt --check`. Save the lint and typecheck commands that ran, not the auto-fixes, to `<checks>` = `.writ/state/gate2-checks-<story-stem>.txt`, one per line.

**On failure:** auto-fix (`eslint --fix`, `prettier --write`, `black`, `cargo fmt`); re-run; typecheck fail → coding agent; still failing → flag for review.

**Pre-review.** After the linters, in every mode, run:

```bash
python3 scripts/story-gate.py run --phase pre-review --story <story-file> --spec <spec-folder> --base <base>
```

It runs build smoke (`build-smoke.py`, when source changed), the architecture ruleset (`arch-lint.py`, then each `command:` line; a failing one is advisory: flag it for review), then Gate 2.5. Report its `arch-lint:` line and build-smoke verdict. **`build_failed_source`** prints `restart: gate2` (no iteration cap). Any `unverifiable` verdict continues, surfaced verbatim, **not** `⚠️ DEGRADED`: DEGRADED means a gate could not be cleared, `unverifiable` means a check could not be run here.

---

#### Gate 2.5: Change Surface Classification

Classify changed files as **style-only**, **single-component**, **cross-component** or **full-stack** and pass Gate 3 `change_surface`.

`Read skills/change-surface-classification/SKILL.md` for how the classes are told apart. This gate owns when classification runs and who consumes `change_surface`; the skill owns how.

Pre-review runs `change-surface.py classify` (`change_surface:`), then `boundary-map.py crossings` on the Gate 0.5 map, if any (`route:` = `gate3_route`). An `unverifiable` verdict, or a helper that cannot run, routes `review-agent` with reason `unverifiable: <reason>`.

**Blast radius.** When `gate3_route` names `review-agent` and the `safety-fact` switch is `on`, pre-review runs `change-surface.py blast-radius`; pass its `blast_radius:` file to Gate 3. Otherwise `blast_radius` is `(none)`.

---

#### Gate 3: Review Agent

> **Agent:** `agents/evaluator-agent.md`
> **Skip in:** `--quick` mode
> **`--review-only`:** evaluator-only (+ scripts); FAIL ends the run; no recode; no silent hatch

Default spawn is `evaluator-agent` (AC, recorded tests, `contract_content`). `recorded_test_results` = the orchestrator's run (`command:`, `exit code: N`, output tail) of the story's tests and each path in `<manifest>` = `.writ/state/evidence-<story-stem>.json`, not the coding agent's report. Verdict field: `EVALUATION_RESULT` or `REVIEW_RESULT`.

**Reviewer filters.** Pass pre-review's `reviewer_filters:` value as `reviewer_filters` to every Gate 3 spawn: the evaluator or `review-agent` and any re-review. The story report prints `reviewer-filters: <on|off>`.

**Evidence gate.** Likewise pass its `evidence_gate:` value as `evidence_gate` to every Gate 3 spawn.

**Risk route:** when `gate3_route` names `review-agent`, spawn `review-agent` in its place — a swap, not a third spawn — with the inputs below and the `reasons` as `boundary_overlap_summary`. `--review-only` has no map, so the evaluator runs; `--full-pipeline` always runs `review-agent`. The story report prints `gate3-route: <agent> (<reasons joined by "; ">)`, parentheses omitted when there are none.

A `Review Panel` config line prints only `review-panel: removed (ADR-032)` once per story.

**`--full-pipeline`:**
> **Agent:** `agents/review-agent.md`

Spawn `review-agent` instead. Same inputs: `spec_lite_for_review` as `spec_lite_content`, `contract_content`, optional `knowledge_context`, `change_surface` (Gate 2.5), **`boundary_map`**, optional `boundary_overlap_summary`, `recorded_test_results`, `blast_radius`, `safety_fact` (`on` unless `blast_radius` is `(none)`).

**Results:** **PASS** → continue (Small/Medium drift ok) · **FAIL** → Gate 1 recode · **PAUSE** → Large drift; Gate 3.5 § A owns options. Two-fail: Pipeline control flow.

**Review loop:** Max 3 iterations across review and Gate 4.5. Gate 3 FAIL → recode, Gate 3.5 "Reject" → recode, Gate 3.5 "Modify spec" → re-review, and Gate 4.5 script fail → recode share one counter. An escalated Gate 0 re-run (or `/create-spec` Step 2.6a regeneration) never increments it. Gate 4 testing failures have a separate 2-iteration cap. After either cap → escalate to user via the existing `AskQuestion` escalations; no cap may be silently continued past (`loop.max_iterations`, nested `testing_cycle`, `on_exhaustion: escalate`).

Save the review to `<review>` = `.writ/state/gate3-review-<story-stem>.md` (re-save on re-spawn) and `recorded_test_results` to `<tests>` = `.writ/state/gate3-tests-<story-stem>.txt`.

**Verify the claim, don't trust it.** After Gate 3.5 § A, run post-review (`--quick`: no output flags):

```bash
python3 scripts/story-gate.py run --phase post-review --story <story-file> --spec <spec-folder> --base <base> --review-output <review> --tests-output <tests>
```

It runs Gate 3's `review-override.py` checks, then Gates 3.5, 4 and 1 (bug path) and the Jev shadow; applies Gate 3's first-match decision (`gate3:`); and records the head SHA, which must be the final code commit. Show the agent's claim and the runner's measurement in the story report. A check `pass` or any `unverifiable` verdict → no override; print the reason; never `⚠️ DEGRADED`.

**Act on line 1.** `pass` → continue. `fail` → by `restart:`:

| `restart:` | Then |
|---|---|
| `gate1` | recode (one review-loop increment) with the failing lines |
| `gate2` | [BLOCKED escalation](#blocked-agent-escalation) (`coding-agent`, restart **Gate 2**) |
| `gate3` | the safety-fact re-spawn below |
| `gate3-blocked` | BLOCKED escalation (Gate 3 agent, restart Gate 3) |
| `gate4` | Gate 4's integrity rule |
| none | `⚠️ DEGRADED` with the `reason:` lines |

**Safety fact (`safety_fact` on).** On `restart: gate3` (`safety_fact_missing` or `safety_fact_below_floor`), re-spawn `review-agent` once, appending the `rung:`/`reason:` lines, and rerun post-review (same Gate 3 attempt, no `review_cycle` increment). Still missing → BLOCKED escalation (`review-agent`, restart Gate 3). Still below floor → Gate 3 FAIL; the coder gets the `fact:`/`rung:` lines to add a test that exercises the fact.

Recode briefs add `## Evidence repros`: each `confirmed` `test` repro's (row 4a: from `<manifest>`) finding, path, fenced content, and "Create it exactly; do not edit it. Make it pass."

The story report quotes post-review's `safety-fact:` and `evidence-gate:` lines, then `evidence-gate advisory: F<n> <Issue> (<reason>)` per advisory finding.

**Jev shadow (opt-in).** Post-review runs `jev-judge.py ac-shadow` only when its `status` prints `pass`. Its verdict is one story-report note: it never changes PASS/FAIL/PAUSE, never counts toward the review loop, and never marks the story `⚠️ DEGRADED`.

#### Gate 3.5: Drift Response Handling & "What Was Built" Extraction

> **Format reference:** `.writ/docs/drift-report-format.md`, `.writ/docs/what-was-built-format.md`

After the Gate 3 agent returns, perform two operations:

##### A. Drift Response

Inspect the `### Drift Analysis` section and handle by severity: **Small** (naming/cosmetic — auto-amend `spec-lite.md` only, log a `DEV-NNN` entry, PASS; the check below fails `auto_amend_unapplied` if `spec-lite.md` is left unchanged); **Medium** (scope impact — ⚠️ warn, log, PASS); **Large** (fundamental deviation — the **PAUSE** Gate 3 emitted lands here: present accept / reject / modify-spec, wait for the decision; this is the only place those options are offered). `spec.md` is never auto-modified.

`Read skills/drift-triage/SKILL.md` for how each severity is handled, including the mixed-severity rule and the append-only `drift-log.md` rules. This gate owns when triage runs and that a Large drift pauses the pipeline and asks the user; the skill owns how.

**Verify the claim, don't trust it.** § A runs before post-review, whose `drift-format.py` check is format-only — it never decides accept / reject / modify-spec.

- **script `fail`** → `restart: gate3-blocked`, the shared [BLOCKED escalation](#blocked-agent-escalation).
- **any `unverifiable` verdict** → the pipeline continues, the reason is surfaced verbatim, and the story is **not** marked `⚠️ DEGRADED` on that basis alone.

##### B. "What Was Built" Data Extraction

Extract implementation data from the Gate 3 agent's output into `what_was_built_data` and hold it in orchestrator state, parsing defensively with a fallback for every field. **Do NOT append to the story file yet.**

Data flow: **Gate 3.5** extracts and validates; **Gate 4** updates `what_was_built_data.test_results`; **Step 4 item 4** formats and appends. The extraction sources, their mandatory/best-effort semantics and their fallback values live in `what-was-built-authoring`, loaded once at Step 4 item 4 alongside the formatting rules they feed.

---

#### Gate 4: Testing Agent (with Coverage Enforcement)

**Default:** do not spawn `testing-agent`.

**`--full-pipeline`:**
> **Agent:** `agents/testing-agent.md`

**Context routing:** Pass `spec_lite_for_testing` as `spec_lite_content` — success criteria, shadow paths, and edge cases relevant to testing. If agent-specific sections not available, pass full spec-lite.

**Process:** (1) run story-specific tests; (2) run regression tests (related suites); (3) run coverage analysis; (4) fix failures, preferring to fix the implementation over changing tests; (5) add missing test coverage if needed.

**Requirements:** **100% test pass rate** — mandatory · **≥80% line coverage on new files** — mandatory · **coverage must not decrease on modified files**.

**On failure:** Send test output back to coding agent. 2 fix iterations max (separate from the review loop's 3-iteration cap), then escalate.

**On `STATUS: BLOCKED` (`--full-pipeline`):** apply the shared [BLOCKED escalation](#blocked-agent-escalation) with agent `testing-agent`, restarting **Gate 4**; skip-with-warning continues to Gate 5 with the story marked `⚠️ DEGRADED`.

**Verify the claim, don't trust it.** Post-review runs `test-integrity.py coverage` on the story's new files and `authenticity` on its test files; on `--full-pipeline`, rerun post-review after the testing agent returns.

The checker re-derives the agent's `Coverage threshold met: YES` from the coverage tool's own output; where they disagree the checker wins. Show both the claim and the measurement in the story report.

- **`coverage_below_threshold`, `coverage_regression`, or `test_imports_no_source`** (`restart: gate4`) → blocking. The story does not reach `Completed ✅`. `test-integrity.py` `fail`: default uses [BLOCKED escalation](#blocked-agent-escalation) with agent `coding-agent`, restarting **Gate 1**; `--full-pipeline` keeps `testing-agent`, restarting **Gate 4**. Do not downgrade the story silently.
- **Any `unverifiable` verdict** → the pipeline continues, the reason is surfaced verbatim, and the story is **not** marked `⚠️ DEGRADED` on that basis alone.

---

### Full-Pipeline Gates (`--full-pipeline` only)

The default path, `--quick` and `--review-only` skip these gates, agent and script: a designed skip, not `⚠️ DEGRADED`. `--full-pipeline` runs each at its Pipeline-table position: Gate 0 before Gate 0.5, Gates 4.5 and 5 after Gate 4.

#### Gate 0: Architecture Check (Pre-Implementation)

**`--full-pipeline`:**
> **Agent:** `agents/architecture-check-agent.md`

Spawn a **read-only** sub-agent before code: viability, integration risk, complexity, gaps. **PROCEED** → code · **CAUTION** → inject warnings · **ABORT** → present findings, ask proceed/modify/skip.

**Context routing:** Pass `spec_lite_for_coding` as `spec_lite_content`; if agent-specific sections are unavailable, pass full spec-lite. Also pass `fetched_context` when hints were parsed in Step 2, and `knowledge_context` when populated.

**Anchor confirmation (ADR-024):** a `floor` **ABORT** is provisional. Before presenting anything, re-run `architecture-check-agent` once at `anchor` (platform `inherit`) with the identical prompt, `spec_lite_content`, `fetched_context`, and `knowledge_context`. The anchor verdict stands: PROCEED/CAUTION continue as that verdict with no AskQuestion and no user-visible line; ABORT presents findings and asks proceed/modify/skip as above. A floor PROCEED/CAUTION is never re-run; a spawn error follows the existing **Agent crash** handling (§ Error Handling), not this branch — escalation fires only on a returned verdict. Iteration accounting: the floor attempt and its anchor re-run count as one attempt against `loop.max_iterations`; Gate 0 runs before the `review_cycle` counter exists and does not consume an iteration.

**Verify the claim, don't trust it.** After an architecture-check agent returns PROCEED or CAUTION (never on ABORT; do not invoke this script on an ABORT-shaped result), run:

```bash
python3 scripts/arch-check.py check --story <story-file> --repo . --planned <planned files> [--boundary <map.json>]
```

`--planned` is Gate 0's live pre-implementation set. `--changed` is replay / post-hoc only. The script never prints `abort`; the ABORT path and the ADR-024 floor→anchor re-run belong to the agent.

- **`rederived: caution`** → inject the script `reason` into the coding-agent warnings.
- **script `fail`** → apply the shared [BLOCKED escalation](#blocked-agent-escalation).
- **`rederived: proceed`** → continue.
- **any `unverifiable` verdict** → the pipeline continues, the reason is surfaced verbatim, and the story is **not** marked `⚠️ DEGRADED` on that basis alone.

---

#### Gate 4.5: Behavioral Verification

Gate 4.5 never asks a question; a script decides, no Task spawn:

```bash
python3 scripts/app-verify.py touched --recipe .writ/docs/app-verification.md --changed <story's changed files>
python3 scripts/app-verify.py run --recipe .writ/docs/app-verification.md --spec <spec-folder> --run-label story-N --features <touched ids, comma-joined>
```

- Line 1 **`pass`** → continue.
- **`fail`** (check, launch, or readiness failed) → Gate 1 recode on the shared review-loop cap (Gate 3).
- **`unverifiable`** (no recipe, invalid recipe, refused), or `touched` printed no `feature:` line (skip `run`; its line says `no mapped features`) → relay the `app-verify:` line and continue; **not** marked `⚠️ DEGRADED`.

**`--full-pipeline`:**
> **Agent:** `agents/visual-qa-agent.md`

With `## Visual References` or spec `mockups/`, spawn it after the script; its mismatches are story-report notes that never fail the gate or count toward the review loop.

---

#### Gate 5: Documentation Agent

**`--full-pipeline`:**
> **Agent:** `agents/documentation-agent.md`

**Context routing:** Pass full spec-lite content as `spec_context`. Also pass `fetched_context` if available.

**Auto-detects the docs framework** (VitePress, Docusaurus, Nextra, MkDocs, Storybook, or plain README). Updates inline docs, README, CHANGELOG, framework pages, diagrams as needed.

**Verify the claim, don't trust it.** After the documentation agent returns, run:

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
8. **Report** pipeline results: per-gate status, file counts, drift summary, both `story-gate:` lines, the `gate3-route:` and `arch-lint:` lines, and next action (`/ship`)

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

**Skips:** Gates 0, 4.5 and 5 (as on default), **Gate 0.5 (boundary map)**, Gate 3 (evaluator), Gate 3.5 (drift handling). `--quick` never escalates.
**Keeps:** Gate 1 (`coding-agent` + scripts), Gate 2 (lint + build smoke), Gate 4 scripts

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
