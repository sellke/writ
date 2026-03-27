# Ralph Loop Orchestration — Technical Sub-Spec

> **Parent:** `.writ/specs/2026-03-27-ralph-loop-orchestration/spec.md`  
> **Purpose:** Machine- and human-readable contracts for state, plans, prompts, script behavior, config, failure handling, and shadow paths.  
> **Deliverable type:** Markdown instructions and JSON schemas — no application runtime.

---

## 1. State File Format

### 1.1 File naming and location

| Rule | Value |
|------|--------|
| Path | `.writ/state/ralph-{timestamp}.json` |
| `{timestamp}` | ISO 8601 compact or filesystem-safe variant (e.g. `2026-03-27T143022Z` or `20260327-143022`) — **must sort lexicographically for “latest run” discovery** |
| Active run | The **most recently modified** `ralph-*.json` in `.writ/state/` is the default target for `/ralph status` and `ralph.sh` unless overridden |
| Git | `.writ/state/` remains gitignored (ephemeral) |

### 1.2 Relationship to `execution-*.json`

`/implement-spec` writes `.writ/state/execution-{timestamp}.json` with single-spec `plan.batches`, per-story `phase`, `reviewIterations`, etc. Ralph state **reuses naming patterns** (`startedAt`, `plan`, `stories`) but **must not overload** execution files. Ralph runs are **cross-spec**; story keys are **globally unique** (see §1.4).

### 1.3 Top-level schema

```json
{
  "schemaVersion": "1.0",
  "run": { },
  "configUsed": { },
  "specsIndex": [ ],
  "plan": { },
  "stories": { },
  "iterations": [ ],
  "escalations": [ ],
  "summary": { }
}
```

| Key | Purpose |
|-----|---------|
| `schemaVersion` | Forward compatibility for parsers (`"1.0"` initial) |
| `run` | Run metadata (§1.4) |
| `configUsed` | Snapshot of Ralph-relevant keys from `.writ/config.md` at plan time (and last refresh) |
| `specsIndex` | Normalized list of specs included in this Ralph run |
| `plan` | Cross-spec execution plan (§2); persisted so CLI iterations need not re-scan specs |
| `stories` | Per-story status and last-known pipeline metrics |
| `iterations` | Append-only per-iteration log |
| `escalations` | Structured blocker records |
| `summary` | Rolling aggregates for dashboards and stop conditions |

### 1.4 Run metadata (`run`)

```json
"run": {
  "id": "ralph-20260327-143022",
  "startedAt": "2026-03-27T14:30:22Z",
  "lastUpdatedAt": "2026-03-27T18:12:01Z",
  "phase": "planned | executing | complete | escalated | aborted",
  "cliBranch": "feature/ralph-epic-xyz",
  "planGeneratedBy": "cursor:/ralph plan",
  "notes": "optional free text from planner"
}
```

| Field | Description |
|-------|-------------|
| `id` | Stable id matching filename stem (without path) |
| `phase` | High-level lifecycle; `escalated` when loop stops on unblockable set |
| `cliBranch` | Branch the CLI loop is expected to use; validated by `ralph.sh` |

### 1.5 Story identity (`storyKey`)

Stories are keyed by a **composite string** to avoid collisions across specs:

```text
{specFolderName}::{storySlug}
```

Example: `2026-03-27-ralph-loop-orchestration::story-1-ralph-plan-command`

- `specFolderName`: directory name under `.writ/specs/` (same convention as `execution-*.json`’s `spec` field style).
- `storySlug`: stem of `story-*.md` (e.g. `story-1-ralph-plan-command`).

### 1.6 Per-story record (`stories[storyKey]`)

Extends the spirit of `execution-*.json`’s `stories` map with Ralph lifecycle and CLI pipeline fields.

```json
"stories": {
  "2026-03-27-foo::story-2-bar": {
    "specId": "2026-03-27-foo",
    "storySlug": "story-2-bar",
    "storyPath": ".writ/specs/2026-03-27-foo/user-stories/story-2-bar.md",
    "status": "not-started | in-progress | completed | attempted-failed | blocked",
    "eligibility": "eligible | blocked-by-dependency | blocked-by-config | superseded",
    "phase": "orient | implement | validate | commit | null",
    "attemptCount": 0,
    "lastAttemptAt": null,
    "lastCompletedAt": null,
    "fixLoopIterations": 0,
    "reviewIterations": null,
    "drift": "none | small | notable | unknown",
    "tests": "passed | failed | skipped | error | unknown",
    "lint": "passed | failed | skipped | error | unknown",
    "coverage": null,
    "lastError": null,
    "filesTouched": [],
    "commitSha": null,
    "dependsOn": ["2026-03-27-foo::story-1-baz"]
  }
}
```

| `status` | Meaning |
|----------|---------|
| `not-started` | Never picked for an iteration |
| `in-progress` | Current iteration claimed this story (crash-safe marker; may be stale if process died) |
| `completed` | Story pipeline finished; commit recorded |
| `attempted-failed` | Pipeline failed; may retry later if eligibility returns |
| `blocked` | Hard stop for this story (e.g. max attempts, environment); excluded until human clears |

### 1.7 Per-iteration log (`iterations[]`)

Append **one object per Ralph outer-loop iteration** (one story attempt).

```json
{
  "iteration": 7,
  "startedAt": "2026-03-27T17:55:00Z",
  "endedAt": "2026-03-27T18:02:18Z",
  "durationSeconds": 438,
  "storyKey": "2026-03-27-foo::story-2-bar",
  "result": "completed | failed | skipped | environment-error",
  "summary": "one-line outcome for humans",
  "filesChanged": ["src/a.ts", "tests/a.test.ts"],
  "testCommand": "npm test",
  "testResult": "passed | failed | error",
  "lintResult": "passed | failed | error",
  "fixLoopIterations": 1,
  "commitSha": "abc1234",
  "agentLogRef": "optional path or excerpt id"
}
```

### 1.8 Escalation records (`escalations[]`)

```json
{
  "id": "esc-20260327-001",
  "raisedAt": "2026-03-27T18:10:00Z",
  "storyKey": "2026-03-27-foo::story-2-bar",
  "type": "dependency | environment | merge | policy | unknown",
  "title": "short label",
  "description": "blocker narrative for human",
  "attemptsMade": 3,
  "diagnostics": {
    "commandsRun": ["npm test"],
    "lastExitCodes": [1],
    "stderrExcerpt": "..."
  },
  "resolution": "open | cleared-manually | deferred"
}
```

### 1.9 Summary statistics (`summary`)

```json
"summary": {
  "totalIterations": 12,
  "completedStories": 5,
  "remainingEligible": 2,
  "blockedStories": 1,
  "attemptedFailedStories": 1,
  "successRate": 0.71,
  "lastStoryKey": "2026-03-27-foo::story-2-bar",
  "stopReason": null
}
```

- `successRate`: `completedIterations / totalIterations` where **completed** iterations are those with `result: "completed"` (define precisely in command docs).
- `stopReason`: e.g. `"max-iterations"`, `"all-complete"`, `"all-blocked"`, `"stop-on-failure"`, `"environment-error"`, `null` while running.

### 1.10 Minimal example (truncated)

```json
{
  "schemaVersion": "1.0",
  "run": {
    "id": "ralph-20260327-143022",
    "startedAt": "2026-03-27T14:30:22Z",
    "lastUpdatedAt": "2026-03-27T14:35:00Z",
    "phase": "planned",
    "cliBranch": "main"
  },
  "configUsed": {
    "Ralph Max Iterations": "0",
    "Ralph CLI Agent": "claude",
    "Ralph CLI Model": "opus"
  },
  "specsIndex": [
    { "id": "2026-03-27-foo", "path": ".writ/specs/2026-03-27-foo", "status": "In Progress" }
  ],
  "plan": { "version": 1, "orderedStoryKeys": [], "graph": { "nodes": [], "edges": [] } },
  "stories": {},
  "iterations": [],
  "escalations": [],
  "summary": {
    "totalIterations": 0,
    "completedStories": 0,
    "remainingEligible": 0,
    "blockedStories": 0,
    "attemptedFailedStories": 0,
    "successRate": null,
    "lastStoryKey": null,
    "stopReason": null
  }
}
```

---

## 2. Execution Plan Format

The cross-spec execution plan is stored under `plan` in the Ralph state file (and may be mirrored to a human-readable artifact such as `RALPH_PLAN.md` by `/ralph plan` — product decision). This section defines the **canonical structure** inside JSON.

### 2.1 `plan` object

```json
"plan": {
  "version": 1,
  "generatedAt": "2026-03-27T14:30:22Z",
  "specs": [ ],
  "crossSpecEdges": [ ],
  "orderedStoryKeys": [ ],
  "storyMeta": { },
  "graph": { "nodes": [], "edges": [] },
  "assessmentNotes": "optional narrative from planner"
}
```

### 2.2 Specs included (`plan.specs[]`)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Spec folder name under `.writ/specs/` |
| `path` | string | Relative path to spec root |
| `title` | string | From spec frontmatter or H1 |
| `status` | string | e.g. Not Started, In Progress, Complete — **stories under Complete specs are excluded** |
| `dependsOnSpecIds` | string[] | **Hard edges**: no story from this spec before all stories in dependency specs are `completed` |
| `storyFiles` | string[] | Relative paths to `user-stories/story-*.md` |

### 2.3 Cross-spec edges (`plan.crossSpecEdges[]`)

Explicit optional list for tooling and visualization (redundant with per-spec `dependsOnSpecIds` if fully normalized):

```json
{ "fromSpecId": "2026-03-27-b", "toSpecId": "2026-03-27-a", "reason": "spec.md Dependencies section" }
```

Meaning: **`b` depends on `a`** (finish `a` before `b`).

### 2.4 Ordered stories (`plan.orderedStoryKeys`)

- **Topological order** of all `storyKey` values respecting:
  - intra-spec story dependencies (from story metadata / content)
  - inter-spec dependencies (`dependsOnSpecIds`)
- **Tie-breaking**: planner may use complexity estimate or codebase assessment — order still must be a **valid** topological sort.

### 2.5 Per-story metadata (`plan.storyMeta[storyKey]`)

```json
"2026-03-27-foo::story-2-bar": {
  "specId": "2026-03-27-foo",
  "storySlug": "story-2-bar",
  "title": "Readable title",
  "dependsOnStoryKeys": ["2026-03-27-foo::story-1-baz"],
  "complexity": "S | M | L | XL",
  "complexitySignals": { "taskCount": 5, "scopedFileCount": 8, "flags": ["many-files"] },
  "eligibility": "eligible | blocked-by-dependency | blocked-by-config | superseded",
  "eligibilityReason": null
}
```

- **`eligibility`** is planning-time **prediction**; runtime truth lives in `stories[storyKey].status` / `eligibility`.
- **Oversized stories** (per parent spec risk mitigation): set `complexity: "XL"` and `flags` including `context-risk` so PROMPT/cli can refuse or split.

### 2.6 Dependency graph (`plan.graph`)

Machine-friendly parallel to visualization:

```json
"graph": {
  "nodes": [
    { "id": "2026-03-27-foo::story-1-baz", "specId": "2026-03-27-foo", "label": "story-1-baz" }
  ],
  "edges": [
    { "from": "2026-03-27-foo::story-1-baz", "to": "2026-03-27-foo::story-2-bar", "kind": "story-depends-on-story" },
    { "from": "spec:2026-03-27-a", "to": "spec:2026-03-27-b", "kind": "spec-depends-on-spec" }
  ]
}
```

### 2.7 ASCII visualization (human artifact)

Commands may render the following pattern into docs or stdout (edges show **blocker → blocked**):

```text
SPECS (cross-spec)
  2026-03-27-a ──depends──► 2026-03-27-b

STORIES (within spec 2026-03-27-b)
  story-1 ──► story-2 ──► story-3
                │
                └──► story-4 (depends on story-2)

ORDERED QUEUE (topological)
  [a::story-1, a::story-2, b::story-1, b::story-2, ...]
```

---

## 3. PROMPT Template Specifications (`PROMPT_build.md`)

`PROMPT_build.md` is the **single-iteration** instruction set piped or passed to the CLI agent. It implements one pass through the **story pipeline** inside one **Ralph outer iteration**.

### 3.1 Document structure (required sections)

| Section | Purpose |
|---------|---------|
| **Header** | Run id, iteration number, branch, path to active `ralph-*.json` |
| **Phase 0 — Orient** | Study specs, read state, understand codebase |
| **Phase 1 — Select and implement** | Pick next story from plan; implement with subagents/tools |
| **Phase 2 — Validate** | Tests, lint, typecheck — **back pressure** |
| **Phase 3 — Update state and commit** | Mutate `ralph-*.json`, `git add`, `git commit`, ensure push per loop policy |
| **Guardrails** | Hard limits (§3.4) |

### 3.2 Phase 0 — Orient

Agent **must**:

1. Read the active `.writ/state/ralph-*.json` — `plan.orderedStoryKeys`, `stories`, `iterations`, `escalations`, `summary`.
2. Read **this iteration’s target story** (selected by script or self-selected per command rules — must match state update in Phase 3).
3. Load **spec-lite** for the story’s spec — **only** the **## For Coding Agents** section (Phase 3a Context Engine: agent-specific spec views).
4. Load full **story file** — acceptance criteria, tasks, **Context for Agents** / context hints, dependencies.
5. Skim repo layout; read `.writ/config.md` for test/lint commands and Ralph keys.
6. Read **`AGENTS.md`** and, if present, **`CLAUDE.md`** (or project’s Claude Code entry doc) for operational conventions.

### 3.3 Phase 1 — Select and implement

- **Input queue:** first `storyKey` in `plan.orderedStoryKeys` that is `eligible` and `status` in `not-started` or `attempted-failed` (and not `blocked`), with all `dependsOnStoryKeys` `completed`.
- **Implementation:** follow story tasks; use subagents per `adapters/claude-code.md` Ralph guidance.
- **Inner fix loop:** on test failure, fix and retest — **max 3** fix iterations; then mark story failed and record diagnostics.

### 3.4 Phase 2 — Validate

- Run test command from `.writ/config.md` (or detection fallback documented in `ralph-cli-pipeline.md`).
- Run lint/typecheck as required by project norms (from config or `AGENTS.md`).
- If failures indicate **environment** misconfiguration (runner missing, binary not found), classify as `environment-error` and **do not** spin the fix loop indefinitely.

### 3.5 Phase 3 — Update state and commit

- Update `stories[storyKey]`, append to `iterations`, adjust `summary`, set `run.lastUpdatedAt` and `run.phase`.
- Commit message convention: e.g. `ralph: complete {storyKey}` or project standard + story id.
- **Do not** leave repo dirty after success; on unrecoverable failure, follow error map (§6) for rollback semantics.

### 3.6 Guardrails (Ralph Playbook “budget line” pattern)

Include a **numeric guardrail block** in the PROMPT (Playbook-style **“you have N units of work”** / **single-focus** discipline). Recommended concrete rules:

| Guardrail | Rule |
|-----------|------|
| **Single story** | Exactly **one** `storyKey` per invocation |
| **Iteration ceiling** | PROMPT must state the **max fix-loop iterations (3)** |
| **Token/time honesty** | If story cannot finish in one outer iteration, **fail closed**: record `attempted-failed`, narrow scope note |
| **No plan mutation** | Do not reorder `plan.orderedStoryKeys`; planners change plans in Cursor |
| **Stop after commit** | After successful commit + state write, **exit** — shell loop restarts fresh context |

Optional Playbook-style **literal budget line** (example text for implementers):

```text
GUARDRAILS: This iteration has exactly 1 story slot and 3 inner test-fix rounds.
If you cannot pass tests within 3 fix rounds, STOP, update state as failed, and EXIT.
```

### 3.7 Context references (checklist for command authors)

| Artifact | How PROMPT references it |
|----------|---------------------------|
| `spec-lite.md` | Path under spec root; extract **## For Coding Agents** only |
| Story file | Full path; include acceptance criteria + tasks + hints |
| `.writ/config.md` | Conventions + Ralph keys |
| `AGENTS.md` / `CLAUDE.md` | Repo root; operational context for CLI |

---

## 4. Loop Script Specification (`scripts/ralph.sh`)

### 4.1 Role

Thin orchestration loop: **invoke CLI agent** with `PROMPT_build.md`, enforce counters and stop conditions, **git push** after each successful iteration (per product spec), refresh display.

### 4.2 Invocation

```bash
./ralph.sh [mode] [max_iterations]
# Examples:
./ralph.sh build          # default mode
./ralph.sh build 20       # stop after 20 outer iterations
./ralph.sh plan           # optional: validate plan artifacts only (if implemented)
```

| Argument | Meaning |
|----------|---------|
| `mode` | `build` (default) or `plan` |
| `max_iterations` | Positive integer cap; **`0` or omitted with config `0` = unlimited** |

Environment or config overrides (from `.writ/config.md`) parsed by the script before the loop.

### 4.3 CLI agent invocation

Default invocation shape (exact flags are project-tunable via `Ralph CLI Flags`):

```bash
claude -p "$(cat PROMPT_build.md)" \
  --dangerously-skip-permissions \
  --model opus \
  --verbose
```

- **`Ralph CLI Agent`**: substitute `claude` for another binary if configured.
- **`Ralph CLI Model`**: passes `--model` (or agent-specific equivalent).
- **`Ralph CLI Flags`**: append extra flags (quoted list).

### 4.4 Git behavior

| Step | Behavior |
|------|----------|
| Branch | Detect current branch; optional: assert branch matches `run.cliBranch` from state |
| After iteration | If commit succeeded per state, **`git push`** (upstream as configured) |
| Dirty tree at start | Fail fast with message (or documented auto-stash — **v1: fail fast preferred**) |

### 4.5 Console output

- Print **iteration counter** before each agent invocation: `Ralph iteration 7 / ∞` or `7 / 20`.
- Print **selected `storyKey`** when known (script may parse state or trust agent to log).

### 4.6 Stop conditions

| Condition | Action |
|-----------|--------|
| `max_iterations` reached | Set `summary.stopReason` to `max-iterations` (agent or script), exit 0 |
| All stories `completed` or no eligible remaining | `all-complete`, exit 0 |
| Escalation: **all remaining** stories blocked | `all-blocked`, exit 0 |
| `Ralph Stop on Failure` true | On first `attempted-failed` / `failed` iteration outcome, stop with `stop-on-failure` |
| Environment error | `environment-error`, exit non-zero |

**State detection:** Script reads `ralph-*.json` **after** each agent exit to decide whether to continue.

### 4.7 Resume

- Re-running `./ralph.sh` with same state file resumes from **next eligible story**; iterations append to `iterations[]`.

---

## 5. Configuration Format

Add the following rows to the **Supported Keys** table in `.writ/docs/config-format.md` (and mirror in **Conventions** list as needed).

| Key | Used By | Description |
|-----|---------|-------------|
| `Ralph Max Iterations` | `ralph.sh` | Default max outer-loop iterations (`0` = unlimited) |
| `Ralph CLI Agent` | `ralph.sh` | CLI agent executable name or path (default: `claude`) |
| `Ralph CLI Model` | `ralph.sh` | Model flag value for primary agent (default: `opus`) |
| `Ralph CLI Flags` | `ralph.sh` | Additional CLI flags (space-separated or documented quoting convention) |
| `Ralph Stop on Failure` | `ralph.sh` | If `true`, stop loop on first story failure (default: `false`) |

**Read order:** Same as existing config — merge with detection; Ralph keys have defaults if absent.

---

## 6. Error & Rescue Map

| Operation | What Can Fail | Planned Handling | Test Strategy |
|-----------|----------------|------------------|---------------|
| Spec scanning | No specs found | Report **nothing to plan**; do not write empty plan | Manual: run with empty `.writ/specs/` |
| Dependency resolution | Circular dependencies | Detect cycle, **refuse to plan**, print cycle path | Manual: two specs mutually depending |
| Story selection | All stories blocked | Append **escalation report**; set `run.phase` / `summary.stopReason`; **stop loop** | Manual: mark all blocked in state |
| CLI agent invocation | Agent crash / non-zero exit | Log stderr tail; increment `summary.totalIterations` if partial; **continue** or stop per `Ralph Stop on Failure` | Manual: kill agent mid-run |
| Test execution | Test runner not found | Classify **environment-error**; log; **stop loop** | Manual: broken `Test Runner` in config |
| State file write | Permission denied | Log error; **stop loop** | Manual: chmod read-only `.writ/state` |
| Git commit | Merge conflict or hook failure | Log error; **`git reset --hard`** to last clean commit (per spec); record failure in `iterations`; continue or stop per policy | Manual: force conflicting concurrent edit |
| Git push | Remote unreachable | Log **warning**; **continue**; commit remains local | Manual: disconnect network |

**Notes for implementers:**

- `git reset --hard` is **destructive**; scope documentation must warn that uncommitted work is lost — align with parent spec’s “atomic iteration” story.
- “Continue after agent crash” should still **avoid infinite tight loops** — optional backoff or max consecutive failures (future schema field).

---

## 7. Shadow Paths

| Flow | Happy Path | No Specs Found | Story Fails | All Blocked |
|------|------------|-----------------|-------------|-------------|
| `/ralph plan` | Scans specs, resolves graph, writes `ralph-*.json` + handoff artifacts | Message: **No non-complete specs found** (or nothing to plan) | N/A — planning does not execute stories | N/A |
| `ralph.sh` (build) | Each iteration: one story → validate → commit → push → state update until done | N/A — **plan must exist**; script errors if no active state | Log failure; set `attempted-failed`; next eligible story **unless** stop-on-failure | Escalation summary in state + stdout; **stop** |
| `/ralph status` | Reads latest `ralph-*.json`; shows progress, queue, stats | **No Ralph execution found** | Surfaces **failure details** + last `iterations[]` + `escalations[]` | Shows **escalation summary** and blocked story list |

---

## References

- Parent spec: `.writ/specs/2026-03-27-ralph-loop-orchestration/spec.md`
- Execution state precedent: `commands/implement-spec.md` (`.writ/state/execution-{timestamp}.json`)
- Context Engine (spec-lite sections): `.writ/specs/2026-03-27-context-engine/spec.md`
- Config baseline: `.writ/docs/config-format.md`
