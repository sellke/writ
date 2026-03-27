# Ralph Loop Orchestration Specification

> **Status:** Complete
> **Created:** 2026-03-27
> **Priority:** High
> **Phase:** 3b

## Contract Summary

**Deliverable:** Ralph loop orchestration — epic-level autonomous execution across multiple Writ specs, with Cursor-based planning, CLI-based execution via an adapted story pipeline, and file-based state management enabling "plan it, walk away, come back to PRs"

**Must Include:** Cross-spec execution planning command (dependency-aware, Ralph-style codebase assessment), CLI-adapted story pipeline for autonomous execution, file-based state persistence across loop iterations, planning/building mode separation, and handoff artifacts bridging Cursor→CLI→Cursor

**Hardest Constraint:** Adapting Writ's structured 9-gate story pipeline to work inside a CLI agent's context window as a single Ralph loop iteration — maintaining quality back pressure (tests, lint, review) without Cursor-specific tools (Task, AskQuestion, SwitchMode)

## Background

### The Ralph Wiggum Technique

[Ralph Wiggum](https://ghuntley.com/ralph/) is an autonomous AI development technique created by Geoffrey Huntley. In its purest form, it's a bash loop:

```bash
while :; do cat PROMPT.md | claude-code ; done
```

Each iteration gets a fresh context window, loads specs and a plan from disk, picks one task, implements it with back pressure (tests/lint/build), commits, and exits. State persists entirely in files — `IMPLEMENTATION_PLAN.md`, `AGENTS.md`, specs, and git history. The [Ralph Playbook](https://github.com/ghuntley/how-to-ralph-wiggum) formalizes the pattern with two modes (planning and building), structured prompt templates, and work-scoped branches.

### Why Ralph for Writ

Writ's pipeline already follows many of Ralph's principles — fresh subagent context per gate, file-based state (execution JSONs, drift logs), specs as source of truth. But the current pipeline is **human-in-the-loop** at every level: the developer invokes each spec, approves each story, monitors each gate.

Phase 3b moves the human **on the loop** — monitoring state files and intervening on escalation — while Ralph orchestrates across multiple specs autonomously. The developer plans interactively in Cursor, hands off to a CLI loop for execution, and returns to review results.

### Architecture: Three Nested Loops

```
┌─────────────────────────────────────────────────────────┐
│ RALPH LOOP (epic level)                                 │
│ Fresh context per iteration. Picks next story across    │
│ all specs. Manages cross-spec state. CLI-native.        │
│                                                         │
│   ┌─────────────────────────────────────────────────┐   │
│   │ STORY PIPELINE (story level)                    │   │
│   │ One story through code → test → lint → commit.  │   │
│   │ CLI-adapted gates with back pressure.           │   │
│   │                                                 │   │
│   │   ┌─────────────────────────────────────────┐   │   │
│   │   │ FIX LOOP (gate level)                   │   │   │
│   │   │ Tests fail → fix → retest. Max 3 iters. │   │   │
│   │   └─────────────────────────────────────────┘   │   │
│   └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

- **Ralph loop (outer):** Each iteration loads state from disk, picks the next story (dependency-aware, codebase-assessed), invokes the story pipeline, updates state, commits, exits. Fresh context.
- **Story pipeline (middle):** CLI-adapted version of Writ's gate pipeline. Code → test → lint → commit. Back pressure from tests and type system. Single iteration = one story.
- **Fix loop (inner):** Within the story pipeline, if tests fail, retry with fix. Max 3 iterations before the story is marked failed.

### Platform Split

| Phase | Platform | Why |
|---|---|---|
| Planning | Cursor | Interactive discovery, visual context, AskQuestion for decisions |
| Execution | CLI (Claude Code) | Fresh context per iteration (native), headless, overnight runs |
| Review | Cursor | State file review, drift assessment, plan adjustment |

## 🎯 Experience Design

### Entry Point

Developer runs `/ralph plan` in Cursor after specs exist. The command scans all specs, resolves dependencies, assesses the codebase, and generates a cross-spec execution plan with CLI handoff artifacts.

### Happy Path Flow

1. Developer has 2-3 specs created via `/create-spec` (stories defined, dependencies documented)
2. Developer runs `/ralph plan` in Cursor
3. Command scans all non-complete specs, reads dependency metadata, assesses codebase state
4. Command generates: cross-spec execution plan, PROMPT files tailored to the project, loop script
5. Developer reviews the plan, adjusts if needed, confirms
6. Developer switches to terminal: `./ralph.sh` (or `./ralph.sh 20` for max 20 iterations)
7. CLI loop starts: fresh context each iteration, picks next story, runs pipeline, commits, loops
8. Developer monitors by checking state files or git log when convenient
9. Loop completes (all stories done) or escalates (blocker hit)
10. Developer returns to Cursor: `/ralph status` shows what happened, what's left, any blockers

### Moment of Truth

Developer walks away Friday evening, comes back Monday morning to find stories implemented across multiple specs with clean git history, structured state files showing exactly what happened at each iteration, and PRs ready for review.

### Feedback Model

- `.writ/state/ralph-{timestamp}.json` updated after every iteration with: story attempted, result (success/fail/skip), files changed, test results, blockers encountered
- Git commits as progress markers — one commit per successful story iteration
- `/ralph status` in Cursor presents human-readable progress dashboard
- No push notifications in v1 — developer checks when they choose (human *on* the loop, not *in* it)

### Error Experience

- **Story fails once:** Ralph logs the failure reason, marks the story as "attempted-failed," and moves to the next eligible story. On a later iteration, Ralph may retry if the blocker might be resolved (e.g., a dependency story completed in the interim).
- **Story fails repeatedly (3+ attempts):** Ralph marks it "blocked," records detailed diagnostics, and stops attempting it. Continues with other eligible stories.
- **All remaining stories are blocked:** Ralph logs a summary escalation report and stops the loop cleanly. State files preserve everything for developer review.
- **Build/test environment broken:** If back pressure (tests, lint) fails in a way that indicates environment issues (not code issues), Ralph stops to prevent wasted iterations.

### State Catalog

- **Empty state:** No Ralph state files exist. `/ralph plan` creates the initial state.
- **Planned:** Execution plan generated, handoff artifacts ready, CLI loop not yet started.
- **Executing:** CLI loop is running. State file updates on each iteration.
- **Paused:** Developer stopped the loop manually (Ctrl+C). State preserved. Resume by running `./ralph.sh` again.
- **Escalated:** Ralph hit blockers it can't resolve. State file contains escalation report.
- **Complete:** All eligible stories completed. State file shows final results.

## 📋 Business Rules

### Execution Ordering

- **Dependency graph provides hard constraints:** If Story B depends on Story A, A must complete successfully before B is attempted. Dependencies are read from story file metadata.
- **Cross-spec dependencies:** If Spec B depends on Spec A (declared in spec.md), all of Spec A's stories must complete before any of Spec B's stories are attempted.
- **Ralph assesses within constraints:** Among eligible (unblocked) stories, Ralph evaluates codebase state to pick the most valuable next story. This isn't random — it's informed by what's already been built.

### One Story Per Iteration

- Each Ralph loop iteration = one story through the full CLI pipeline.
- The story either completes (all gates pass, committed) or fails (logged, state updated).
- No partial stories — if the pipeline can't finish, the iteration is a failure.
- Fresh context on the next iteration ensures no accumulated cruft.

### Platform Separation

- `/ralph plan` is Cursor-native — it uses interactive features (AskQuestion for plan confirmation, visual spec review).
- `/ralph status` is Cursor-native — it reads state files and presents human-readable results.
- The Ralph loop script and PROMPT files are CLI-native — they work with Claude Code (primary target), with future support for other CLI agents.
- `/implement-story` remains unchanged — it's the Cursor-native pipeline for supervised execution. Ralph's CLI pipeline is a parallel execution path.

### Plan Disposability

- The execution plan is a working document, not a contract.
- If the plan goes stale (unexpected complexity, dependency changes, codebase divergence), the developer can regenerate it by running `/ralph plan` again.
- `/ralph plan` always scans current codebase reality, not cached assumptions.

### State as Single Source of Truth

- State files (`.writ/state/ralph-*.json`) are the authoritative record of execution progress.
- The CLI loop reads and writes state files every iteration.
- State survives context window resets, process crashes, and manual stops.
- State files are human-readable JSON — developers can inspect them directly.

### Relationship to Other Commands

- **`/plan-product`** is strategic: "What should we build?" Produces roadmap.
- **`/create-spec`** is tactical: "What exactly is this feature?" Produces spec packages.
- **`/ralph plan`** is operational: "Given these specs, what's the execution order?" Produces execution plan.
- **`/implement-story`** is supervised execution: runs one story with human in the loop (Cursor).
- **`/ralph` (CLI loop)** is autonomous execution: runs stories with human on the loop (CLI).

## Implementation Approach

### Architecture

The feature has four distinct concerns:

1. **Planning (Cursor):** Scan specs, resolve dependencies, assess codebase, generate execution plan and handoff artifacts. This is the `/ralph plan` command.

2. **CLI Pipeline:** A PROMPT template that instructs a CLI agent how to execute a single Writ story through a simplified gate pipeline with back pressure. This is the building-mode prompt.

3. **Loop Orchestration:** The `ralph.sh` script and state management that picks the next story, invokes the CLI agent, reads results, and loops. Plus configuration for stop conditions.

4. **Review (Cursor):** The `/ralph status` command that reads state files and presents progress to the developer.

### Key Design Decisions

**Why fresh context per iteration (Ralph-style), not resumed context:**

Research (`.writ/research/2026-03-16-ai-workflow-best-practices-research.md`, Finding 6) found that "fresh-context-per-iteration agents outperform continuous agents because each iteration allocates full cognitive budget to the current state." The current `/implement-story` fix loop resumes the coding agent (context accumulation). Ralph's outer loop avoids this — each iteration starts clean with only the plan and specs loaded.

**Why CLI for execution, not Cursor:**

Cursor's interaction model is designed for human-AI collaboration — modal UI, interactive tools, visual context. The Ralph loop needs headless, automated execution with fresh context per iteration. CLI agents (Claude Code) provide this natively. The platform split plays to each tool's strengths.

**Why one story per iteration, not one task:**

Writ's stories are the natural unit of shippable value. Each story has acceptance criteria, a definition of done, and maps to a commit. Breaking below story-level would fragment commits and lose the "each commit is a coherent increment" property.

**Why dependency graph + assessment, not pure Ralph "choose the most important thing":**

Pure Ralph works for greenfield where ordering mistakes are recoverable. Writ targets existing codebases where wrong ordering can break production code. The dependency graph provides safety rails. Ralph-style assessment provides adaptability within those rails.

### Integration Points

**With `/create-spec`:**
- `/ralph plan` reads spec packages created by `/create-spec`
- Spec metadata (dependencies, status) informs execution ordering
- Context hints and spec-lite sections are available for the CLI pipeline

**With `.writ/config.md`:**
- Ralph configuration (max iterations, stop conditions, CLI agent) stored here
- Project conventions (test runner, default branch) used by the CLI pipeline

**With Claude Code adapter (`adapters/claude-code.md`):**
- The CLI PROMPT templates leverage Claude Code capabilities (subagents, tool use)
- `AGENTS.md` or `CLAUDE.md` provides project operational context

**With `.writ/state/`:**
- Execution state files live here (gitignored)
- State format shared between Cursor planning, CLI execution, and Cursor review

### Files in Scope

**Created:**
- `commands/ralph.md` — The `/ralph` command (plan + status modes in Cursor)
- `scripts/ralph.sh` — Loop script template for CLI execution
- `.writ/docs/ralph-state-format.md` — State file format reference
- `.writ/docs/ralph-cli-pipeline.md` — CLI story pipeline reference

**Modified:**
- `.writ/docs/config-format.md` — Add Ralph configuration section
- `adapters/claude-code.md` — Add Ralph-specific CLI execution guidance

## Success Criteria

1. **Autonomous multi-spec execution:** Developer can plan across 3+ specs in Cursor, hand off to CLI, and get completed stories without intervention.

2. **Quality back pressure:** CLI pipeline produces code that passes tests, lint, and type checks autonomously. Review quality parity with supervised runs is not required for v1 but should be measurable.

3. **Resilient state management:** State files enable resume after any interruption — crash, manual stop, context reset. No work is lost.

4. **Smart escalation:** Genuine blockers trigger escalation (<10% of iterations). Solvable issues are handled by retrying or moving on.

5. **Seamless round-trip:** State files from CLI execution are readable in Cursor via `/ralph status`. The Cursor→CLI→Cursor handoff feels like one continuous workflow, not three disconnected tools.

## Risks and Mitigations

### Risk: CLI pipeline quality is significantly worse than supervised Cursor runs

**Impact:** Developer comes back to code that compiles but is poorly structured, misses business rules, or has subtle bugs.

**Mitigation:**
- Phase 3a (Context Engine) ensures agents receive targeted spec context — error maps, business rules, shadow paths — even in CLI mode
- Back pressure (tests, lint, type checks) catches functional issues
- v1 explicitly sets expectations: autonomous mode prioritizes coverage over perfection
- Developer reviews output in Cursor before merging

### Risk: Stories exhaust CLI agent's context window

**Impact:** Iteration fails mid-pipeline, wasting work and producing partial changes.

**Mitigation:**
- `/ralph plan` flags oversized stories during planning (heuristic: >7 tasks, >10 files in scope)
- Ralph loop treats failed iterations as atomic — git reset to last commit, log failure, move on
- Story sizing guidance added to `/create-spec` documentation

### Risk: Dependency graph is wrong or incomplete

**Impact:** Ralph attempts a story whose dependencies aren't truly met, producing broken code.

**Mitigation:**
- Ralph's per-iteration codebase assessment catches dependency assumptions that don't match reality
- Failed stories are logged and retried later (the dependency may be met by then)
- `/ralph plan` validates dependency graph against codebase state during planning

### Risk: Overnight runs produce divergent codebase

**Impact:** After 20+ iterations, the codebase has drifted so far from the developer's mental model that review is overwhelming.

**Mitigation:**
- Each iteration produces one commit with a descriptive message — git log tells the story
- State file tracks every decision and result — developer can trace execution
- `/ralph status` provides summary view with attention drawn to failures and drift
- Developer can limit iterations (`./ralph.sh 10`) to keep batches reviewable

### Risk: CLI agent selection (Claude Code) becomes outdated or deprecated

**Impact:** Loop script and PROMPT templates stop working.

**Mitigation:**
- PROMPT templates are markdown — portable across CLI agents with minimal adaptation
- Loop script is a thin bash wrapper — the intelligence is in the PROMPT, not the script
- Adapter pattern (`adapters/claude-code.md`) isolates platform-specific details

## Dependencies

- Phase 3a (Context Engine) complete — provides agent-specific spec views, context hints, and "What Was Built" records that the CLI pipeline consumes
- Claude Code adapter exists (`adapters/claude-code.md`) — provides baseline CLI integration patterns
- `.writ/config.md` format established — configuration infrastructure ready

## Out of Scope

- Modifications to the existing Cursor-native `/implement-story` pipeline
- General-purpose CLI adapter for all Writ commands (only Ralph-specific CLI pipeline)
- Notification integrations (Slack, email, webhooks) for escalation
- Cross-project learning or corpus building
- Multi-repo orchestration
- Automatic PR creation from CLI (developer creates PRs in Cursor review phase)
