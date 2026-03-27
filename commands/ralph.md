# Ralph Command (ralph)

## Overview

Ralph orchestration for autonomous multi-spec execution. Two modes:

- **`/ralph plan`** — Scans non-complete specs, resolves cross-spec and cross-story dependencies, assesses codebase state, and generates an execution plan with CLI handoff artifacts. Cursor-native (interactive planning).
- **`/ralph status`** — Reads Ralph state files and presents human-readable progress, blockers, escalation reports, and next-step guidance. Cursor-native (review and re-entry).

Ralph bridges Cursor's interactive planning with CLI-based autonomous execution. The developer plans in Cursor, hands off to a CLI loop (`./ralph.sh`), and returns to Cursor to review results.

### Three Nested Loops

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

### Relationship to Other Commands

| Command | Role |
|---------|------|
| `/plan-product` | Strategic: *what* to build. Produces roadmap. |
| `/create-spec` | Tactical: *what exactly* is this feature. Produces spec packages. |
| `/ralph plan` | Operational: *what order* to execute existing specs. Produces execution plan + CLI artifacts. |
| `/implement-story` | Supervised execution: runs one story with human **in** the loop (Cursor). |
| `./ralph.sh` (CLI) | Autonomous execution: runs stories with human **on** the loop (terminal). |
| `/ralph status` | Review: reads CLI execution state, presents results in Cursor. |

---

## Invocation

| Invocation | Behavior |
|---|---|
| `/ralph plan` | Scan specs, resolve dependencies, generate execution plan and handoff artifacts |
| `/ralph status` | Read state files, display progress dashboard (see Status section below) |

---

## `/ralph plan` — Cross-Spec Execution Planning

### Phase 1: Spec Discovery & Loading

#### Step 1.1: Find Non-Complete Specs

Scan `.writ/specs/*/spec.md` for specs whose status is **not** `Complete`.

```bash
ls -t .writ/specs/*/spec.md
```

For each spec found:
1. Read `spec.md` header — extract title, status, phase, dependencies
2. Skip specs with `Status: Complete` (or `Status: Completed`)
3. Read `user-stories/README.md` — overall progress, story count

If **no** non-complete specs found:
```
📋 No non-complete specs found under .writ/specs/
   Nothing to plan. Create specs first: /create-spec
```
Stop here — do not write an empty plan.

#### Step 1.2: Load Story Metadata

For each non-complete spec, enumerate `user-stories/story-*.md`:
1. Extract from each story file:
   - **Status** — from `> **Status:**` metadata line
   - **Priority** — from `> **Priority:**` metadata line
   - **Dependencies** — from `> **Dependencies:**` metadata line (parse story numbers and cross-spec references)
   - **Task count** — count lines matching `- [ ]` and `- [x]` in `## Implementation Tasks`
   - **AC count** — count lines matching `- [ ]` and `- [x]` in `## Acceptance Criteria`
2. Skip stories already marked `Completed ✅`

#### Step 1.3: Parse Cross-Spec Dependencies

Check each `spec.md` for a `## Dependencies` section or dependency metadata:
- If Spec B declares a dependency on Spec A, **all** stories in Spec A must complete before **any** story in Spec B is attempted
- Store as directed edges: `{ fromSpecId, toSpecId, reason }`

#### Step 1.4: Detect Circular Dependencies

Run cycle detection on the merged dependency graph (specs + stories).

If a cycle is found:
```
❌ Circular dependency detected — cannot generate plan.

   Cycle path: story-2 → story-4 → story-2

   Fix the dependency declarations in the story files before re-running /ralph plan.
```
Stop here — refuse to plan with a cycle.

### Phase 2: Dependency Resolution & Graph Construction

#### Step 2.1: Build Merged Dependency Graph

Construct a DAG combining:
- **Intra-spec story dependencies** — story N depends on story M within the same spec
- **Cross-spec dependencies** — all stories in Spec A before any story in Spec B

Nodes are `storyKey` values using the composite format:
```
{specFolderName}::story-{N}-{slug}
```

Example: `2026-03-27-ralph-loop-orchestration::story-1-ralph-plan-command`

#### Step 2.2: Topological Sort

Produce `orderedStoryKeys` — a valid topological ordering respecting all dependency edges.

**Tie-breaking rules** (when multiple stories are eligible):
1. Higher priority stories first (`High` > `Medium` > `Low`)
2. Within same priority, fewer dependencies first (less blocked downstream)
3. Within same priority and dependency count, alphabetical by storyKey

#### Step 2.3: Compute Story Metadata

For each story in the ordered queue, compute:

| Field | Source |
|-------|--------|
| `complexity` | `S` (≤3 tasks), `M` (4–5), `L` (6–7), `XL` (8+) |
| `complexitySignals` | `{ taskCount, acCount, flags }` |
| `eligibility` | `eligible` if all dependencies completed; `blocked-by-dependency` otherwise |

**Flag oversized stories** (per spec risk mitigation):
- `>7 tasks` → flag `context-risk`
- `>10 files in scope` (if detectable from tasks) → flag `context-risk`
- Set `complexity: "XL"` for flagged stories

### Phase 3: Codebase Assessment

Perform a Ralph-style codebase assessment — structured findings, not ad-hoc prose.

#### Step 3.1: Repository Scan

Inspect the following (fast, no full analysis):

| Signal | How to Check | What to Note |
|--------|-------------|--------------|
| **Package manager** | Look for `package.json`, `Cargo.toml`, `pyproject.toml`, `go.mod` | Runtime, language, dependency count |
| **Test infrastructure** | `scripts.test` in package.json, `pytest.ini`, `Cargo.toml [dev-dependencies]` | Test runner, framework |
| **CI/CD** | `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile` | Pipeline presence, key jobs |
| **Linting** | `.eslintrc*`, `ruff.toml`, `clippy`, `.prettierrc` | Lint tools configured |
| **TypeScript / Types** | `tsconfig.json`, type annotations | Strictness level |
| **Git state** | Branch, uncommitted changes, stash count | Working tree cleanliness |
| **Writ config** | `.writ/config.md` — Test Runner, Default Branch, etc. | Conventions already detected |

#### Step 3.2: Assessment Output

Present findings as structured bullets in the execution plan:

```
## Codebase Assessment

- **Language:** TypeScript (strict mode)
- **Test Runner:** jest (detected from package.json scripts.test)
- **Lint:** eslint + prettier
- **CI:** GitHub Actions (build, test, lint jobs)
- **Default Branch:** main (from .writ/config.md)
- **Git State:** Clean working tree on feat/current-branch
- **Conventions:** .writ/config.md present with Test Runner, Default Branch
- **Risk Flags:** None detected
```

Risk flags to check:
- No test runner detected → `⚠️ No test infrastructure — CLI pipeline back pressure will be limited`
- No lint tooling → `⚠️ No lint tools — code quality verification reduced`
- Dirty working tree → `⚠️ Uncommitted changes — commit or stash before CLI handoff`
- No `.writ/config.md` → `⚠️ No config file — CLI pipeline will need to detect conventions each iteration`

### Phase 4: Execution Plan Presentation

#### Step 4.1: Display the Plan

Present the execution plan with dependency visualization:

```
## Execution Plan: Ralph Run

Specs included: 3 (2 Not Started, 1 In Progress)
Stories to execute: 12 (3 already complete, 9 remaining)

### Dependency Graph

SPECS (cross-spec)
  2026-03-27-auth ──depends──► 2026-03-27-dashboard

STORIES (within 2026-03-27-auth)
  story-1 ──► story-2 ──► story-3
                │
                └──► story-4

ORDERED QUEUE (topological)
  1. auth::story-1 (High, M, eligible)
  2. auth::story-2 (High, L, blocked-by-dependency)
  3. auth::story-3 (Medium, M, blocked-by-dependency)
  4. auth::story-4 (Medium, S, blocked-by-dependency)
  5. dashboard::story-1 (High, L, blocked-by-dependency)
  ...

### Oversized Stories (context risk)
  ⚠️ dashboard::story-3 — 9 tasks, complexity XL
     Consider splitting before CLI execution.
```

#### Step 4.2: Confirm with User

```
AskQuestion({
  title: "Ralph Execution Plan",
  questions: [
    {
      id: "proceed",
      prompt: "Proceed with this plan? The next step generates CLI handoff artifacts.",
      options: [
        { id: "yes", label: "Generate handoff artifacts and state file" },
        { id: "edit", label: "Edit the plan (add/remove specs or stories)" },
        { id: "reorder", label: "Change execution order" },
        { id: "cancel", label: "Cancel — don't generate anything" }
      ]
    }
  ]
})
```

On **edit**: Switch to Plan Mode for collaborative adjustment, then return to Phase 4.
On **reorder**: Allow manual reordering (must still respect dependency constraints).
On **cancel**: Stop without writing any files.

### Phase 5: State File & Handoff Artifact Generation

#### Step 5.1: Initialize Ralph State File

Create `.writ/state/ralph-{timestamp}.json` per the schema documented in `.writ/docs/ralph-state-format.md`.

Set initial values:
- `run.phase` → `"planned"`
- `run.planGeneratedBy` → `"cursor:/ralph plan"`
- `run.cliBranch` → current git branch
- `configUsed` → snapshot of Ralph-relevant keys from `.writ/config.md`
- `specsIndex` → normalized list of included specs
- `plan` → full execution plan with `orderedStoryKeys`, `graph`, `storyMeta`
- `stories` → one entry per story, all `status: "not-started"`, eligibility computed
- `iterations` → empty array
- `escalations` → empty array
- `summary` → zeroed counters

#### Step 5.2: Generate `PROMPT_build.md`

Create (or overwrite) `scripts/PROMPT_build.md` — the CLI agent's single-iteration instruction set. Tailor to the project:

- Fill in the actual test command from `.writ/config.md` (`Test Runner`)
- Fill in lint commands based on detected tooling
- Reference the active Ralph state file path
- Include the project's `AGENTS.md` / `CLAUDE.md` reference if present

Template structure (detailed content defined in Story 2):
1. **Header** — run id, branch, state file path
2. **Phase 0 — Orient** — load state, story, spec-lite, config
3. **Phase 1 — Select and implement** — pick next eligible story, code it
4. **Phase 2 — Validate** — run tests, lint, typecheck (back pressure)
5. **Phase 3 — Update state and commit** — write state, git commit
6. **Guardrails** — single story, max 3 fix rounds, stop after commit

> **Story 1 scope:** Generate a skeleton `PROMPT_build.md` with project-specific values filled in. Story 2 authors the full template content.

#### Step 5.3: Generate Loop Script

Create (or overwrite) `scripts/ralph.sh` — the outer loop script. Tailor to the project:

- Set the CLI agent command from `.writ/config.md` (`Ralph CLI Agent`, default: `claude`)
- Set the model flag (`Ralph CLI Model`, default: `opus`)
- Set max iterations from config or leave as parameter
- Reference the correct PROMPT file path

> **Story 1 scope:** Generate a functional skeleton `ralph.sh`. Story 3 authors the full script with mode selection, stop conditions, and config integration.

#### Step 5.4: Output Summary

```
✅ Ralph plan generated

   State file: .writ/state/ralph-{timestamp}.json
   PROMPT:     scripts/PROMPT_build.md
   Loop script: scripts/ralph.sh

   Stories queued: 9 (across 3 specs)
   Estimated iterations: 9 (1 per story)

   Next steps:
   1. Review the generated artifacts
   2. Switch to terminal: ./ralph.sh (or ./ralph.sh 20 for max 20 iterations)
   3. Monitor with /ralph status when convenient
```

### Phase 6: Plan Regeneration

**The plan is disposable.** Running `/ralph plan` again:
1. Re-scans all specs from disk (current reality, not cached)
2. Rebuilds the dependency graph from scratch
3. Regenerates all handoff artifacts
4. Creates a **new** state file (previous state files remain for history)

Does not attempt to merge with previous plans — regeneration is the norm.

---

## `/ralph status` — Monitoring & Cursor Re-entry

Read Ralph state files and present human-readable progress, blockers, escalation reports, and next-step guidance. This closes the Cursor→CLI→Cursor loop.

### Differentiation from `/status`

| Command | Scope | Purpose |
|---------|-------|---------|
| `/status` | Project-wide | Specs, issues, git position, health signals |
| `/ralph status` | Ralph execution only | Loop progress, story outcomes, blockers, next steps |

They complement each other — `/status` shows overall project health; `/ralph status` shows autonomous execution details.

### Step 1: Discover State Files

```bash
ls -t .writ/state/ralph-*.json
```

If **no** Ralph state files found:
```
📋 No Ralph execution found.
   Run /ralph plan to create an execution plan and start.
```
Stop here — do not claim false progress.

If **multiple** state files found: use the most recently modified by default. If the user needs a specific run, present selection:

```
AskQuestion({
  title: "Multiple Ralph Runs Found",
  questions: [{
    id: "run",
    prompt: "Which Ralph run do you want to review?",
    options: [
      { id: "latest", label: "Latest: ralph-20260327-143022 (executing, 5/9 stories)" },
      { id: "previous", label: "Previous: ralph-20260325-091500 (complete, 12/12 stories)" }
    ]
  }]
})
```

### Step 2: Parse State File

Read the selected `.writ/state/ralph-*.json`. Parse per `.writ/docs/ralph-state-format.md`:

1. **Schema version check** — warn if `schemaVersion` is newer than expected
2. **Run metadata** — `run.phase`, timestamps, branch
3. **Stories** — group by status: `completed`, `in-progress`, `attempted-failed`, `blocked`, `not-started`
4. **Iterations** — extract results, durations, errors
5. **Escalations** — active blockers
6. **Summary** — aggregate statistics

### Step 3: Classify Phase

Determine the current Ralph phase from state:

| Detected Condition | Phase | Display |
|---|---|---|
| State file exists, `run.phase` = `"planned"`, no iterations | **Planned** | Plan ready, CLI not started |
| `run.phase` = `"executing"`, recent `lastUpdatedAt` (< 30 min) | **Executing** | Loop actively running |
| `run.phase` = `"executing"`, stale `lastUpdatedAt` (> 30 min) | **Paused** | Loop stopped (Ctrl+C or crash) |
| All remaining stories `blocked`, `escalations` present | **Escalated** | Blockers need human attention |
| All stories `completed` or `run.phase` = `"complete"` | **Complete** | All work done |
| `run.phase` = `"aborted"` | **Aborted** | Manually stopped |

### Step 4: Render Progress Dashboard

```
⚡ Ralph Status Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 RUN: ralph-20260327-143022
   Phase: Executing (loop running)
   Branch: feat/ralph-epic
   Started: 2026-03-27 14:30 (3.5 hours ago)
   Last update: 2026-03-27 18:02

📊 PROGRESS
   ████████████░░░░░░░░ 7/12 stories (58%)
   Iterations: 9 total (7 completed, 1 failed, 1 skipped)
   Success rate: 78%

   ✅ COMPLETED (7)
      • auth::story-1 — User authentication setup
      • auth::story-2 — Session management
      • auth::story-3 — Password reset flow
      • dashboard::story-1 — Dashboard layout
      • dashboard::story-2 — Widget system
      • dashboard::story-3 — Data visualization
      • api::story-1 — REST endpoints

   ❌ FAILED (1)
      • api::story-2 — WebSocket integration
        Last error: "Test timeout — WebSocket mock not connecting"
        Attempts: 2/3
        → May retry on next iteration

   🔒 BLOCKED (1)
      • api::story-3 — Rate limiting
        Blocked by: api::story-2 (not completed)

   ⏳ REMAINING (3)
      • api::story-2 — WebSocket integration (will retry)
      • api::story-3 — Rate limiting (blocked)
      • api::story-4 — API documentation (blocked by story-3)
```

### Step 5: Surface Blockers & Escalations

If escalation records exist in `escalations[]`:

```
🚨 ESCALATIONS

   ESC-001: Environment — Test runner crash
   Raised: 2026-03-27 17:45
   Story: api::story-2
   Type: environment
   Attempts: 3
   Diagnostics:
     Command: npm test
     Exit code: 137 (OOM killed)
     Stderr: "FATAL ERROR: Reached heap limit..."
   Resolution: open

   → Fix: Increase Node memory limit or split test suites
```

### Step 6: Optional Git Correlation

If the project uses the Ralph commit message convention (`ralph: complete {storyKey}`), optionally correlate recent commits with state:

```bash
git log --oneline --grep="ralph:" -20
```

Display as supplementary confidence signal — state files remain the source of truth.

```
📝 RECENT RALPH COMMITS
   abc1234 ralph: complete auth::story-3
   def5678 ralph: complete dashboard::story-1
   ghi9012 ralph: complete dashboard::story-2
```

### Step 7: Next-Step Guidance

Based on the phase and state, provide actionable next steps:

| Phase | Guidance |
|-------|----------|
| **Planned** | `→ Switch to terminal: ./ralph.sh` (or `./ralph.sh N` for bounded run) |
| **Executing** | `→ Loop is running. Check back later or monitor git log.` |
| **Paused** | `→ Resume: ./ralph.sh` (picks up from last state). Or re-plan: `/ralph plan` |
| **Escalated** | `→ Review blockers above. Fix environment/config issues, then resume: ./ralph.sh` |
| **Complete** | `→ Review changes: git log --oneline -N`. Then `/ship` to open a PR. |
| **Aborted** | `→ Re-plan with /ralph plan if specs changed, or resume ./ralph.sh` |

Additional guidance based on state:
- If stories have `attempted-failed` status: suggest reviewing the error, potentially splitting the story
- If drift is detected in completed stories: suggest running `/verify-spec`
- If coverage is low: note for manual review
- If all specs are done: suggest `/ship` followed by `/release`

```
🎯 NEXT STEPS
   1. Review api::story-2 failure — WebSocket mock issue may need manual fix
   2. Consider splitting api::story-2 if context window is the problem
   3. Resume loop: ./ralph.sh (will retry story-2, then unblock story-3 and story-4)
   4. After completion: /ship to open PR for review

⚡ QUICK COMMANDS
   ./ralph.sh           # Resume CLI loop
   /ralph plan          # Regenerate plan from current state
   /verify-spec         # Check spec integrity after Ralph run
   /ship                # Open PR when all stories complete
```

---

## State Catalog

| Phase | Meaning | Entry Condition |
|-------|---------|-----------------|
| **Empty** | No Ralph state files exist | Default — never planned |
| **Planned** | Execution plan generated, handoff artifacts ready | `/ralph plan` completed |
| **Executing** | CLI loop is running, state updating each iteration | `./ralph.sh` started |
| **Paused** | Developer stopped the loop (Ctrl+C) | Manual interruption; state preserved |
| **Escalated** | Ralph hit blockers it can't resolve | All remaining stories blocked |
| **Complete** | All eligible stories completed | Loop finished naturally |

---

## Integration with Writ Ecosystem

| Command | Relationship |
|---------|-------------|
| `/plan-product` | Strategic planning → produces roadmap that informs specs |
| `/create-spec` | Creates the spec packages that `/ralph plan` reads |
| `/implement-story` | Supervised per-story pipeline (Cursor) — parallel path to Ralph's CLI pipeline |
| `/implement-spec` | Supervised spec execution (Cursor) — uses same dependency resolution concepts |
| `/verify-spec` | Optional metadata diagnostic after Ralph execution |
| `/status` | Project-wide overview; `/ralph status` is Ralph-specific execution view |
| `/ship` | Opens PR after Ralph execution completes |
| `/release` | Cuts version after PR merged |

---

## References

- **State file format:** `.writ/docs/ralph-state-format.md`
- **CLI pipeline:** `.writ/docs/ralph-cli-pipeline.md`
- **Config keys:** `.writ/docs/config-format.md` → Ralph section
- **PROMPT template:** `scripts/PROMPT_build.md`
- **Loop script:** `scripts/ralph.sh`
- **Technical spec:** `.writ/specs/2026-03-27-ralph-loop-orchestration/sub-specs/technical-spec.md`
- **Claude Code adapter:** `adapters/claude-code.md` → Ralph subsection
