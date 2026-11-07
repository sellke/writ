# Technical Spec: Lean Story Pipeline

> Spec: [../spec.md](../spec.md)
> Business rules are numbered in `spec.md` → Specification Contract → 📋 Business Rules. This file cites them by number.

## Components

| File | Change | Story |
|---|---|---|
| `implement-story.md` `gates:` frontmatter | `catches:`, `evidence:`, `kill_when:`, optional `path:` per entry (Business Rule 1) | 1 |
| `scripts/verdict-provenance.py` and its tests | Finding codes for missing fields; accepts `path:` | 1 |
| `.writ/specs/2026-11-06-lean-story-pipeline/gate-evidence.md` | One row per gate: catch citation or `none recorded`, dependency reason, decision | 1 |
| `commands/implement-story.md` gate sections | Demoted gates move under `--full-pipeline` (Business Rule 2) | 2 |
| Pinning tests (e.g. `test_implement_story_default_path.py`, `test_boundary_map.py`, `test_change_surface.py`, `test_docs_check.py`) | Pin full-pipeline wording for demoted gates | 2 |
| `scripts/story-gate.py`, `scripts/tests/test_story_gate.py` | New runner: `run`, `tally` (Business Rules 4, 7) | 3 |
| `commands/implement-story.md` default path | Two `story-gate.py` calls replace the per-script blocks | 3 |
| `.writ/docs/agent-cli-contract.md` | Script table row for `story-gate.py` | 3 |
| `.writ/decision-records/adr-029-*.md` | Dated note: a fixed one-command runner is not a dispatcher | 3 |
| `agents/coding-agent.md`, `agents/evaluator-agent.md`, `agents/review-agent.md`; Gate 4 prose | Targeted tests only (Business Rule 6) | 4 |
| `agents/supervisor-agent.md` | `story_gate_record` input; head-SHA check (Business Rule 5) | 5 |
| `commands/implement-spec.md` | Drop Step 2.3; no context regeneration in Step 3.3; pass the record path to the supervisor | 5 |
| `scripts/tests/test_governor_enforcement.py` | Dated `KNOWN_OVER_BUDGET` entries for byte changes | 1, 2, 3, 4, 5 |
| Generated trees (`claude-code/`, `cursor/plugin/`, `codex/`) | `python3 scripts/gen-platform-trees.py` | 2–5 |
| `trial-report.md` | Before/after results | 6 |

## Gate frontmatter (Story 1)

Each `gates:` entry keeps `id` and `script` or `verification`, and adds these fields:

```yaml
  - id: gate2_5_surface
    script: scripts/change-surface.py
    path: default            # or full-pipeline; absent means default
    catches: "Risky diff reviewed by the light evaluator; cost: a cross-component defect ships unreviewed"
    evidence: "none recorded"   # or a citation, e.g. ".writ/retros/2026-10-30-phase-15.md F26"
    kill_when: "sole_catches == 0 over 20 default-path records"
```

`verdict-provenance.py` keeps its minimal line parser and reads the new keys as plain scalars. New finding codes: `missing_catches`, `missing_evidence`, `missing_kill_when`, `unknown_path_value`. The existing codes and exit codes stay as they are.

## `story-gate.py`

**Shape:** check (`.writ/docs/agent-cli-contract.md`). Python 3.9 stdlib. No spawn, poll, sleep, or network (ADR-029 rules 1, 2, 6).

### `run`

```
story-gate.py run --phase pre-review|post-review --story <story-file> --spec <spec-dir>
                  --base <sha> [--repo .] [--review-output <path>] [--tests-output <path>]
                  [--checks <path>] [--manifest <path>] [--state-dir .writ/state]
```

- **Changed files:** computed by the runner as `git diff --name-only <base>` plus untracked files, so the orchestrator never types a file list.
- **Checks:** a fixed table in the script, with one row per default-path check: `id`, the gate it belongs to, the argv builder, and the `restart` target. A test asserts that the set of gate ids in the table equals the `gates:` entries whose `path` is `default` (Implementation Approach, Story 3).
- **Order:** pre-review covers whatever Gate 2 / 2.5 checks Story 2 leaves on the default path, in pipeline order: build smoke, arch-lint ruleset, change surface, crossings / route, blast radius. Post-review covers `review-override` check, safety-fact, evidence, `drift-format` check, `test-integrity` coverage and authenticity, then any surviving Gate 4.5 / 5 checks. The Jev shadow comes last and only when `jev-judge.py status` prints `pass`; its verdict is recorded but never counted.
- **Per check:** run the script, read line 1 (`pass`, `fail`, or `unverifiable`) and the `reason:` lines, and record the exit code. A non-0/1/2 exit, or a missing script, records `unverifiable (helper_error: <detail>)`.
- **Overall verdict:** `fail` if any counted check is `fail`, otherwise `pass`. `unverifiable` never sets `fail` (Business Rule 4).
- **Restart:** the first failing check's `restart` (`gate1` recode, `gate2` BLOCKED, `gate3` re-review) is printed as `restart: <target>`. Every check still runs.
- **Pre-review extras:** prints `route: evaluator-agent|review-agent (<reasons>)` and `change_surface: <class>` so Gate 3 has its inputs.
- **Review-dependent checks without `--review-output`** (the `--quick` path) record `unverifiable (no_review_output)`.

**Stdout:**

```
pass|fail
check: <id> <verdict> (<first reason or "ok">)    # one per check, in order
restart: <target>                                 # only on fail
route: ... / change_surface: ...                  # pre-review only
story-gate: <verdict> (phase <phase>, <n> checks, <f> fail, <u> unverifiable)
{"schema": "story-gate-v1", ...}                  # the record, always the last line
```

The JSON document (Business Rule 4) is always printed, with no flag, as the last line after the summary. The agent CLI contract allows this form, and `app-verify.py --json` already uses it. Its content is the same as the record file.

**Record:** written atomically (temp file + `os.replace`) to `<state-dir>/story-gate-<story-stem>-<phase>.json`:

```json
{
  "schema": "story-gate-v1",
  "story": "story-3-...",
  "phase": "post-review",
  "head_sha": "<git rev-parse HEAD>",
  "dirty": false,
  "base": "<sha>",
  "at": "<UTC ISO-8601>",
  "verdict": "pass",
  "restart": null,
  "checks": [
    {"id": "gate4_tests", "command": ["python3", "..."], "exit": 0,
     "verdict": "pass", "reasons": [], "counted": true}
  ]
}
```

On every run the record is replaced, never appended. Earlier runs of the same story and phase are kept for `tally` under `<state-dir>/story-gate-history/<story-stem>-<phase>-<at>.json`.

### `tally`

```
story-gate.py tally [--state-dir .writ/state]
```

This reads `story-gate-history/*.json` and prints `pass` on line 1, then one line per check id: `tally: <id> runs=<n> fails=<n> sole_catches=<n>`, then a summary. It reports only: it never edits a file (Business Rule 7). No history prints `unverifiable` with `reason: no_records`.

## Supervisor change (Story 5)

- New optional input `story_gate_record`: the post-review record path.
- New rule:
  - Absent post-review record, on any mode (`--quick` writes one too) → claim `story-gate record missing`, marked `false` → `RERUN`.
  - Record `head_sha` ≠ the last commit in `base_commit..head_ref` that touches a non-Writ-artifact file → claim `story-gate record head <sha> ≠ final code commit <sha>` → `RERUN`.
  - `dirty: true` → claim `story-gate record written on a dirty tree` → `RERUN`.
  - A report claim about a check's verdict that disagrees with the record is `false`.
- The supervisor no longer re-runs `review-override.py`, `test-integrity.py`, or `drift-format.py` when a valid record exists. It reads their verdicts from the record and verifies git and story-file claims as today.

## `implement-spec.md` cuts (Story 5)

- **Step 2.3** (scope estimate): removed. Step 2.3b pre-flight stays and produces the same counts.
- **Step 3.3:** removes the "Regenerate `.writ/context.md`" bullet. `postRun.contextRewritten` stays, set from `implement-story` Step 4's last regeneration.
- **Step 3.3** supervisor spawn passes `story_gate_record`.

## Error & Rescue Map

| Operation | Failure | Rescue | User sees |
|---|---|---|---|
| Compute changed files | `--base` not a commit | Exit 2, usage blocker | `story-gate` usage error; orchestrator follows Agent crash handling |
| Compute changed files | Not a git repo | Every git-dependent check records `unverifiable (no_git)` | `check: ... unverifiable (no_git)` |
| Run one check | Script missing | `unverifiable (helper_error: missing <path>)` | That check's line; run continues |
| Run one check | Exit outside 0/1/2, or empty stdout | `unverifiable (helper_error: exit <n>)` | That check's line; run continues |
| Run one check | Times out (per-check limit from the script's own `--timeout`, else 600 s) | `unverifiable (timeout)` | That check's line |
| Write record | State dir not writable | Print the result; add `reason: record_write_failed`; line 1 unchanged | Orchestrator marks the story `⚠️ DEGRADED` (no record, Business Rule 5) |
| Supervisor read | Record schema unknown | Claim `story-gate record unreadable` → `RERUN` | Supervisor claims table |
| Tally | History dir empty | `unverifiable` + `reason: no_records` | Tally line |
| Demotion (Story 2) | A pinning test guards a default-path behavior that a kept gate needs | Gate stays on default; `gate-evidence.md` records the dependency | Row reads `kept: input to <gate>` |
| Trial (Story 6) | One arm stops for a question or a crash | Record the stop and its gate; do not re-run only one arm | Report row `stopped at <gate>` |

## Shadow Paths

| Path | Behavior |
|---|---|
| Happy: every check passes | `pass`; record written; story completes |
| Nil: no review output (`--quick`) | Review-dependent checks `unverifiable (no_review_output)`; record still written |
| Empty: story changed no files | Changed-file list empty; checks that need files print their own `unverifiable`; overall `pass` |
| Upstream: a checker script crashes | That check `unverifiable (helper_error: ...)`; others run; overall verdict unaffected |

## Interaction Edge Cases

| Case | Behavior |
|---|---|
| Coder commits again after post-review `pass` | Supervisor sees head ≠ record → `RERUN` (Business Rule 5) |
| Two stories in one parallel batch write records at once | Separate files per story stem; atomic replace; no shared file |
| Parallel batch in one working tree | stories run one after another; each record names its own final code commit |
| `--full-pipeline` | `story-gate.py` runs as on default; the full-pipeline-only gates run in their own sections in addition |
| `--review-only` | Post-review only; a `fail` ends the run as today |

## Trial procedure (Story 6)

1. **Pick the spec.** From `.writ/specs/archive/`, take an archived spec with ≤3 stories, identifiable implementation commits, and at least one recorded Gate 3 FAIL or drift entry. Prefer `2026-08-13-claude-md-install-merge`, whose known Major defect (lean-story-tasks trial) is a planted catch. Record the candidates and the reason for the pick.
2. **Cut worktrees** from the parent of the spec's first implementation commit, in the scratchpad or `/tmp`, never inside the main checkout: `arm-before` with `implement-story.md` and the agents as of this spec's base commit, and `arm-after` with them as of Story 5's commit. Both use the same story files.
3. **Run** `/implement-story` on every story in order, under the same model and settings, on the default path (no `--full-pipeline`). Headless: `claude -p ... < /dev/null`, and note that headless lacks AskUserQuestion and Plan Mode.
4. **Measure per arm:**
   - blocking findings
   - Major+ defects that escape review, checked by a post-run read against the known defect and a full-suite run on the arm
   - review iterations
   - wall-clock time
   - tokens (session usage or `measure-invocation.py`)
   - script invocations made by the orchestrator
   - gates that failed or stopped
5. **Report** in `trial-report.md`: method, pick, a per-arm table, limits, and one verdict line: `lean-pipeline: keep`, `lean-pipeline: regress (<what got worse>)`, or `lean-pipeline: inconclusive`. More escaped defects in `arm-after` is `regress`. Remove the worktrees with `git worktree remove`.
