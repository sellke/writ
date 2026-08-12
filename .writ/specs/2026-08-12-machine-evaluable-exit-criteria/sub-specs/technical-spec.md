# Technical Spec — Machine-Evaluable Exit Criteria

> Parent: [`spec.md`](../spec.md)

## CLI Surface

```
python3 scripts/exit-criteria.py check --command <implement-phase|implement-spec>
                                       [--state PATH] [--spec DIR] [--repo .]
```

Output is a single JSON object on stdout. Exit codes: `0` met · `1` unmet ·
`2` impossible. Nothing is written to disk (Business Rule 3).

```json
{"verdict": "unmet",
 "command": "implement-phase",
 "state": ".writ/state/phase-execution-20260812-0200.json",
 "criteria": [
   {"id": "implement-phase.c1", "verdict": "met",
    "evidence": "5/5 specs terminal; 0 quarantine branches reachable from phase branch"},
   {"id": "implement-phase.c2", "verdict": "unmet",
    "reason": "2 merged specs lack a populated uat-plan.md: <slug-a>, <slug-b>"},
   {"id": "implement-phase.c4", "verdict": "unknown",
    "reason": "declared unobservable: report is transcript-only"}]}
```

Criterion `id` values come from the Story 1 classification and are stable. An
`id` present in the checker but absent from the classification is `impossible`,
not `unknown` — see § Rollup.

## Rollup

Evaluated in this order; the first match wins.

1. Any **`impossible` trigger** fires → `impossible`. Triggers are checked as a
   pre-pass, before any criterion predicate runs, because a tripped bound or an
   unresolved pause makes per-criterion verdicts irrelevant.
2. Any criterion `impossible` → `impossible`
3. Any criterion `unmet` → `unmet`
4. Otherwise → `met`

`unknown` never blocks — but it is legal only for a criterion the classification
declared structurally unobservable. Validate every criterion ID against the
classification at load time; an unrecognized ID yields `impossible`. Without that
guard, an unimplemented predicate returning `unknown` becomes a silent pass, which
is the single most likely way this instrument goes wrong.

### `impossible` triggers

| Trigger | Detected from |
|---|---|
| Loop bound tripped | `haltReported` present in phase state |
| Unresolved escalation | a `challenge_required` record with no `resolve-challenge` entry |
| Criterion recorded unachievable | `exitCriteria[].verdict == "unachievable"` |
| State/git mismatch | `phase-state.py reconcile` reports a discrepancy |

## Data Contracts (additive, Story 2)

### `phase-execution-v2` — `schemaVersion` stays `2`

| Field | Written by | When | Optional |
|---|---|---|---|
| `exitCriteria[]` | `/implement-phase` | Step 4.1, per criterion verified | yes |
| `exitCriteria[].id` / `.source` / `.class` / `.verdict` / `.evidence` | — | — | — |
| `terminalStatus` | `/implement-phase` | Step 4.2, with the report | yes |
| `haltReported` | `/implement-phase` | Step 3.2 on exhaustion | yes |

`.class` is `machine` or `human`; `.verdict` is `pass`, `fail`, `unachievable`, or
`handed_off`. `terminalStatus` is one of `COMPLETE`,
`IMPLEMENTED_PENDING_HUMAN_VALIDATION`, `PARTIALLY_COMPLETE`.

**`haltReported` and `terminalStatus` are mutually exclusive.** A run that hit its
bound has not reached a terminal status; writing one would let the checker report
`met` for a run that never finished.

### `.writ/state/execution-<ts>.json`

| Field | Written by | When |
|---|---|---|
| `preflight.storyDepsValidated` / `.at` | `/implement-spec` | after the story-graph pre-flight, before batch 1 |
| `postRun.typecheck` / `.testSuite` / `.contextRewritten` / `.at` | `/implement-spec` | after the final story's batch |

These close the two temporal criteria — `implement-spec.c1`'s "before the first
story ran" and `c3`'s "after the final story" — which a post-hoc filesystem read
cannot otherwise recover.

## Reuse

| Need | Existing code | Do not |
|---|---|---|
| Phase spec statuses, quarantine branches, closures, `blockedBy` | `scripts/phase-state.py` `cmd_progress` (returns a dict) | re-read the state file |
| Spec completion classification | `scripts/spec-status.py` `is-complete` / `scan` | re-parse `spec.md` headers |
| Story graph validity | `scripts/story-deps.py` `validate_graph` | reimplement cycle detection |
| State/git agreement | `scripts/phase-state.py reconcile` | shell out to raw git |

`scripts/recommend-state.py` importing `story_deps.validate_graph` is the house
pattern, and `scripts/eval.sh` `check_story_deps` asserts that delegation with
`require_literal` — a fresh copy would be caught by the suite regardless.

## Error & Rescue Map

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| Load state file | Path missing | `impossible`, exit 2, reason names the path | Unit test with a nonexistent path |
| Load state file | Malformed JSON | `impossible`, exit 2, reason names the parse error and offset | Unit test with a truncated fixture |
| Load state file | Valid JSON, wrong schema | `impossible`, exit 2, reason names the expected schema | Unit test with `{"schemaVersion": 9}` |
| Load classification | `exit-criteria-classification.md` missing | `impossible`, exit 2 — the checker cannot know which unknowns are legal | Unit test with the doc absent |
| Evaluate a criterion | Required field absent (pre-Story-2 record) | `unknown`, reason `record predates exit-criteria instrumentation` | Fixture: a state file with no `exitCriteria[]` |
| Evaluate a criterion | Predicate raises | `impossible`, exit 2, reason names the exception type and criterion id | Fault-injected predicate |
| Evaluate a criterion | Criterion id absent from the classification | `impossible`, exit 2 | Unit test with an unregistered id |
| Read spec folders | `uat-plan.md` present but a stub | `unmet` naming the spec — a stub is not a populated plan | Fixture with a heading-only file |
| Read git | `git` unavailable or not a repo | `impossible`, exit 2, reason names it | Run in a temp dir with no `.git` |
| Read git | Quarantine branch check ambiguous | `unmet` with the branch names listed | Fixture repo with a stray branch |
| Run `reconcile` | Reports a discrepancy | `impossible`, exit 2, reason quotes the named mismatch | Fixture with a divergent lane branch |
| Write anything | — | `[OUT OF SCOPE — the checker is read-only, Business Rule 3]` | Assert no file mtime changes across a run |

No `[UNPLANNED]` cells remain.

## Shadow Paths

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| Phase check | `met`, exit 0, per-criterion evidence | `--state` missing → `impossible` + path named | `specs: {}` → `unmet` ("no spec resolved"), never vacuously `met` | `cmd_progress` raises → `impossible` + exception named |
| Spec check | `met`, exit 0, story counts in evidence | `--spec` missing → `impossible` + path named | zero stories in the batch plan → `unmet` | `story-deps.py` unavailable → `impossible` |
| Goal evaluation (adapter) | exit 0 → hook clears, run stops | goal never registered (hooks restricted) → adapter documents how to detect | no active goal → checker still runnable by hand | exit 2 → hook reports impossible, run halts rather than spins |

The empty-input column is the one to get right: an empty spec set satisfies "every
spec reached a terminal status" **vacuously**. Returning `met` there would pass a
phase that resolved to nothing.

## Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| Checker run twice in a row | Identical verdict — read-only, no memoized state |
| Checker run mid-batch | `unmet` naming the pending specs; never `impossible` — an in-flight run is not a blocked one |
| Two state files match `phase-execution-*.json` | `--state` is required and explicit; no globbing, no most-recent heuristic |
| Concurrent lane worktrees present | Ignored — the checker reads phase state and the phase branch, not lane trees |
| Criterion prose edited after the predicate was written | Story 4's `require_literal` binding fails the suite |
| Goal set while another goal is active (Claude Code) | Documented in the adapter: the prior Stop hook is silently removed; only the outermost command may hold a goal |
| All criteria `unknown` | `met` **only** if all were declared unobservable; otherwise `impossible` |

## Verification

```bash
python3 -m pytest scripts/tests/test_exit_criteria.py
bash scripts/eval.sh --check=exit-criteria
bash scripts/eval.sh
```

End-to-end replay — run the checker against each archived
`.writ/state/phase-execution-*.json` and confirm the verdict matches the recorded
outcome. Phase 10's `PARTIALLY COMPLETE` must return `impossible`, not `unmet`:
its unmet criteria were recorded unachievable and accepted, which is a halt, not a
failure to finish.
