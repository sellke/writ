# Ralph State File Format

> Location: `.writ/state/ralph-{timestamp}.json`
> Purpose: Single source of truth for Ralph loop execution — written by `/ralph plan`, updated by `ralph.sh` each iteration, read by `/ralph status`

## File Naming & Discovery

| Rule | Value |
|------|-------|
| Path | `.writ/state/ralph-{timestamp}.json` |
| `{timestamp}` | ISO 8601 compact, filesystem-safe: `20260327-143022` — **must sort lexicographically** for latest-run discovery |
| Active run | The most recently modified `ralph-*.json` in `.writ/state/` is the default target for `/ralph status` and `ralph.sh` |
| Git | `.writ/state/` remains gitignored (ephemeral) |

## Relationship to `execution-*.json`

`/implement-spec` writes `.writ/state/execution-{timestamp}.json` for single-spec supervised execution. Ralph state reuses naming patterns (`startedAt`, `plan`, `stories`) but is a **separate file type** — Ralph runs are cross-spec and use globally unique story keys.

Do not overload `execution-*.json` with Ralph data. Do not read `ralph-*.json` from `/implement-spec`.

## Top-Level Schema

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
| `run` | Run metadata — id, phase, timestamps, branch |
| `configUsed` | Snapshot of Ralph-relevant keys from `.writ/config.md` at plan time |
| `specsIndex` | Normalized list of specs included in this Ralph run |
| `plan` | Cross-spec execution plan — persisted so CLI iterations need not re-scan specs |
| `stories` | Per-story status and pipeline metrics |
| `iterations` | Append-only per-iteration log |
| `escalations` | Structured blocker records |
| `summary` | Rolling aggregates for dashboards and stop conditions |

## Run Metadata (`run`)

```json
"run": {
  "id": "ralph-20260327-143022",
  "startedAt": "2026-03-27T14:30:22Z",
  "lastUpdatedAt": "2026-03-27T18:12:01Z",
  "phase": "planned",
  "cliBranch": "feature/ralph-epic-xyz",
  "planGeneratedBy": "cursor:/ralph plan",
  "notes": "optional free text from planner"
}
```

| Field | Description |
|-------|-------------|
| `id` | Stable id matching filename stem (e.g. `ralph-20260327-143022`) |
| `startedAt` | ISO 8601 timestamp of initial plan generation |
| `lastUpdatedAt` | Updated on every state write (plan, iteration, manual edit) |
| `phase` | High-level lifecycle: `planned`, `executing`, `complete`, `escalated`, `aborted` |
| `cliBranch` | Branch the CLI loop is expected to use; validated by `ralph.sh` |
| `planGeneratedBy` | Origin marker: `cursor:/ralph plan` for Cursor-generated plans |
| `notes` | Optional free text from planner or developer |

## Story Identity (`storyKey`)

Stories are keyed by a composite string to avoid collisions across specs:

```
{specFolderName}::{storySlug}
```

Example: `2026-03-27-ralph-loop-orchestration::story-1-ralph-plan-command`

- `specFolderName` — directory name under `.writ/specs/`
- `storySlug` — filename stem of `story-*.md` (e.g. `story-1-ralph-plan-command`)

## Per-Story Record (`stories[storyKey]`)

```json
"stories": {
  "2026-03-27-foo::story-2-bar": {
    "specId": "2026-03-27-foo",
    "storySlug": "story-2-bar",
    "storyPath": ".writ/specs/2026-03-27-foo/user-stories/story-2-bar.md",
    "status": "not-started",
    "eligibility": "eligible",
    "phase": null,
    "attemptCount": 0,
    "lastAttemptAt": null,
    "lastCompletedAt": null,
    "fixLoopIterations": 0,
    "reviewIterations": 0,
    "reviewResult": "unknown",
    "drift": "unknown",
    "acVerified": null,
    "tests": "unknown",
    "lint": "unknown",
    "coverage": null,
    "lastError": null,
    "quarantineBranch": null,
    "filesTouched": [],
    "commitSha": null,
    "dependsOn": ["2026-03-27-foo::story-1-baz"]
  }
}
```

### Status Values

| `status` | Meaning |
|----------|---------|
| `not-started` | Never picked for an iteration |
| `in-progress` | Current iteration claimed this story (crash-safe marker; may be stale if process died) |
| `completed` | Story pipeline finished; commit recorded |
| `attempted-failed` | Pipeline failed; may retry later if eligibility returns |
| `blocked` | Hard stop — excluded until human clears (e.g. max attempts, environment) |

### Eligibility Values

| `eligibility` | Meaning |
|----------------|---------|
| `eligible` | All dependencies completed; ready for the next iteration to pick |
| `blocked-by-dependency` | Upstream story not yet completed |
| `blocked-by-config` | Configuration prevents execution (e.g. missing test runner) |
| `superseded` | Story removed from plan or spec changed |

### Phase Values (CLI Pipeline)

| `phase` | When |
|---------|------|
| `null` | Not yet attempted |
| `orient` | Reading story, spec, state |
| `implement` | Writing code |
| `validate` | Running tests/lint |
| `review` | Review sub-agent verifying AC, quality, drift |
| `commit` | State update and git commit |

### Review Result Values

| `reviewResult` | Meaning |
|----------------|---------|
| `unknown` | Not yet reviewed |
| `passed` | Review sub-agent returned PASS |
| `failed` | Review sub-agent returned FAIL after max iterations |
| `paused` | Review sub-agent returned PAUSE (Large drift) |

### AC Verified Format

`acVerified` uses the format `"{verified}/{total}"` (e.g., `"5/5"`, `"3/5"`). Set from the review sub-agent's `AC Verification` output. `null` when not yet reviewed.

## Per-Iteration Log (`iterations[]`)

Append one object per Ralph outer-loop iteration (one story attempt):

```json
{
  "iteration": 7,
  "startedAt": "2026-03-27T17:55:00Z",
  "endedAt": "2026-03-27T18:02:18Z",
  "durationSeconds": 438,
  "storyKey": "2026-03-27-foo::story-2-bar",
  "result": "completed",
  "summary": "Implemented API endpoints with full test coverage",
  "filesChanged": ["src/a.ts", "tests/a.test.ts"],
  "testCommand": "npm test",
  "testResult": "passed",
  "lintResult": "passed",
  "reviewResult": "passed",
  "drift": "none",
  "acVerified": "4/4",
  "fixLoopIterations": 1,
  "reviewIterations": 1,
  "commitSha": "abc1234",
  "agentLogRef": "optional path or excerpt id"
}
```

| `result` | Meaning |
|----------|---------|
| `completed` | Story pipeline finished successfully |
| `failed` | Pipeline failed (code, tests, or lint) |
| `skipped` | Story was skipped (already done, or superseded) |
| `environment-error` | Infrastructure failure (missing binary, sandbox denial) |

## Escalation Records (`escalations[]`)

```json
{
  "id": "esc-20260327-001",
  "raisedAt": "2026-03-27T18:10:00Z",
  "storyKey": "2026-03-27-foo::story-2-bar",
  "type": "dependency",
  "title": "Upstream story-1 not completed",
  "description": "Story 2 depends on Story 1 which failed with test errors",
  "attemptsMade": 3,
  "diagnostics": {
    "commandsRun": ["npm test"],
    "lastExitCodes": [1],
    "stderrExcerpt": "TypeError: Cannot read properties..."
  },
  "resolution": "open"
}
```

| `type` | Meaning |
|--------|---------|
| `dependency` | Blocked by unfinished upstream work |
| `environment` | Build/test infrastructure problem |
| `merge` | Git conflict or hook failure |
| `drift` | Large spec drift detected — implementation deviates fundamentally from spec intent |
| `review` | Review agent found unresolvable issues after max iterations |
| `policy` | Configuration or autonomy constraint |
| `unknown` | Unclassified failure |

| `resolution` | Meaning |
|--------------|---------|
| `open` | Still blocking — needs human attention |
| `cleared-manually` | Developer resolved outside the loop |
| `deferred` | Acknowledged but postponed |

## Summary Statistics (`summary`)

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

- **`successRate`** — `completedIterations / totalIterations` where completed iterations have `result: "completed"`
- **`stopReason`** — `null` while running; set on termination:

| `stopReason` | Trigger |
|-------------|---------|
| `max-iterations` | Hit configured iteration limit |
| `all-complete` | Every story completed or no eligible remaining |
| `all-blocked` | All remaining stories are blocked — escalation |
| `stop-on-failure` | `Ralph Stop on Failure` config is `true` and a story failed |
| `environment-error` | Infrastructure failure too severe to continue |

## Execution Plan (`plan`)

Persisted in the state file so CLI iterations need not re-scan specs each time.

```json
"plan": {
  "version": 1,
  "generatedAt": "2026-03-27T14:30:22Z",
  "specs": [],
  "crossSpecEdges": [],
  "orderedStoryKeys": [],
  "storyMeta": {},
  "graph": { "nodes": [], "edges": [] },
  "assessmentNotes": "optional narrative from planner"
}
```

### `plan.specs[]`

```json
{
  "id": "2026-03-27-foo",
  "path": ".writ/specs/2026-03-27-foo",
  "title": "Feature Name",
  "status": "In Progress",
  "dependsOnSpecIds": [],
  "storyFiles": [
    ".writ/specs/2026-03-27-foo/user-stories/story-1-bar.md"
  ]
}
```

### `plan.crossSpecEdges[]`

```json
{ "fromSpecId": "2026-03-27-b", "toSpecId": "2026-03-27-a", "reason": "spec.md Dependencies section" }
```

Meaning: `b` depends on `a` — finish all of `a` before starting `b`.

### `plan.orderedStoryKeys`

Topological order of all `storyKey` values, respecting intra-spec story dependencies and inter-spec dependencies. Tie-breaking by priority, then dependency count, then alphabetical.

### `plan.storyMeta[storyKey]`

```json
{
  "specId": "2026-03-27-foo",
  "storySlug": "story-2-bar",
  "title": "Readable title",
  "dependsOnStoryKeys": ["2026-03-27-foo::story-1-baz"],
  "complexity": "M",
  "complexitySignals": { "taskCount": 5, "acCount": 4, "flags": [] },
  "eligibility": "eligible",
  "eligibilityReason": null
}
```

Complexity scale: `S` (≤3 tasks), `M` (4–5), `L` (6–7), `XL` (8+ or `context-risk` flag).

### `plan.graph`

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

## Minimal Example

```json
{
  "schemaVersion": "1.0",
  "run": {
    "id": "ralph-20260327-143022",
    "startedAt": "2026-03-27T14:30:22Z",
    "lastUpdatedAt": "2026-03-27T14:35:00Z",
    "phase": "planned",
    "cliBranch": "main",
    "planGeneratedBy": "cursor:/ralph plan",
    "notes": null
  },
  "configUsed": {
    "Ralph Max Iterations": "0",
    "Ralph CLI Agent": "claude",
    "Ralph CLI Model": "opus"
  },
  "specsIndex": [
    { "id": "2026-03-27-foo", "path": ".writ/specs/2026-03-27-foo", "status": "In Progress" }
  ],
  "plan": {
    "version": 1,
    "generatedAt": "2026-03-27T14:30:22Z",
    "specs": [],
    "crossSpecEdges": [],
    "orderedStoryKeys": [
      "2026-03-27-foo::story-1-baz",
      "2026-03-27-foo::story-2-bar"
    ],
    "storyMeta": {},
    "graph": { "nodes": [], "edges": [] },
    "assessmentNotes": null
  },
  "stories": {
    "2026-03-27-foo::story-1-baz": {
      "specId": "2026-03-27-foo",
      "storySlug": "story-1-baz",
      "storyPath": ".writ/specs/2026-03-27-foo/user-stories/story-1-baz.md",
      "status": "not-started",
      "eligibility": "eligible",
      "phase": null,
      "attemptCount": 0,
      "lastAttemptAt": null,
      "lastCompletedAt": null,
      "fixLoopIterations": 0,
      "reviewIterations": null,
      "drift": "unknown",
      "tests": "unknown",
      "lint": "unknown",
      "coverage": null,
      "lastError": null,
      "filesTouched": [],
      "commitSha": null,
      "dependsOn": []
    }
  },
  "iterations": [],
  "escalations": [],
  "summary": {
    "totalIterations": 0,
    "completedStories": 0,
    "remainingEligible": 1,
    "blockedStories": 0,
    "attemptedFailedStories": 0,
    "successRate": null,
    "lastStoryKey": null,
    "stopReason": null
  }
}
```

## Writers & Readers

| Actor | Reads | Writes |
|-------|-------|--------|
| `/ralph plan` (Cursor) | Specs, stories, config | Creates initial state file |
| `ralph.sh` + CLI agent | State file, specs, stories | Updates stories, iterations, escalations, summary |
| `/ralph status` (Cursor) | State file | Does not write (read-only view) |

## Versioning

The `schemaVersion` field enables forward compatibility. Parsers should:
1. Check `schemaVersion` before processing
2. Handle unknown fields gracefully (ignore, don't error)
3. Log a warning if the schema version is newer than expected
