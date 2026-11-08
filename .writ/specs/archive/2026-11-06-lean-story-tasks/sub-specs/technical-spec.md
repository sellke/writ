# Technical Spec: Lean Story Tasks

> Spec: [../spec.md](../spec.md)
> Business rules are numbered in `spec.md` → Specification Contract → 📋 Business Rules. This file cites them by number.

## Components

| File | Change | Story |
|---|---|---|
| `scripts/ac-trace.py` | New informational finding `oversized_task` | 1 |
| `scripts/tests/test_ac_trace.py` | Tests for the finding | 1 |
| `.writ/docs/acceptance-criteria-ids.md` | Finding Codes row for `oversized_task` | 1 |
| `agents/user-story-generator.md` | Task rules (Business Rules 1, 2, 3, 6); quality guideline | 2 |
| `commands/create-spec.md` Step 2.6a | `oversized_task` counts as a story failure | 2 |
| `agents/user-story-generator.md` | Template drops `## Definition of Done` (Business Rule 5) | 3 |
| `commands/create-spec.md` Step 2.6 | Story-contents sentence drops definition of done | 3 |
| `commands/verify-spec.md` Checks 1d, 3b | DoD optional; 3b only when present | 3 |
| `commands/create-spec.md` Steps 2.4, 2.8 | Cite rule numbers, do not restate (Business Rule 4) | 4 |
| `agents/user-story-generator.md` Context for Agents | Business-rule hints cite numbers | 4 |
| `scripts/tests/test_rule_citations.py` | New; pins rule-number citations in create-spec, the generator, and context-hint-format | 4 |
| `scripts/tests/test_governor_enforcement.py` | Disclosed ledger entries for byte changes | 2, 3, 4 |
| Generated trees (`claude-code/agents/writ-story-gen.md`, `cursor/plugin/**`) | Regenerate with `python3 scripts/gen-platform-trees.py` | 2, 3, 4 |
| `.writ/specs/2026-11-06-lean-story-tasks/trial-report.md` | Trial results | 5 |

## `oversized_task` finding

**Contract (external):** consumed by `/create-spec` Step 2.6a and displayed by `/verify-spec` 3e/3f output.

| Field | Value |
|---|---|
| `code` | `oversized_task` |
| `severity` | `informational` (never changes the exit code) |
| `story` | story number |
| `id` | `null` |
| `file`, `line` | the task line |
| `detail` | `task N.M has W words (limit 50)`; for an unnumbered task line, `task at line L has W words (limit 50)` |

**Word count (Business Rule 2):** take the line inside `## Implementation Tasks` that matches the existing checkbox pattern; remove the checkbox, an optional leading `N.M` number, and the trailing AC tag (the existing `TAG` pattern); split on whitespace; count. Limit: `> 50` fires.

**Scope:** stories whose `Status` is exactly `Not Started` after trimming. Any other status, or a missing status line, emits nothing.

**Unchanged:** schema name `ac-trace-check-v1`, exit codes, every existing finding, the citation scan.

## Step 2.6a change

Item 2 gains one clause: a story with any `oversized_task` finding fails, the same as a count or tag failure. Item 3's single regeneration at `anchor` applies unchanged. Step 2.9 lists a second failure's `oversized_task` details.

## Error & Rescue Map

| Operation | Failure | Rescue | User sees |
|---|---|---|---|
| Count task words | Task line has no AC tag | Count the whole line after the checkbox and number | Normal finding if over 50 |
| Count task words | Story has no `## Implementation Tasks` section | Emit nothing for that story | Existing findings only |
| Read story status | No `Status` line in the first 15 lines | Treat as not `Not Started`; emit nothing | Existing findings only |
| Step 2.6a regenerate | Anchor retry still has an over-long task | Keep the anchor file; list it in Step 2.9 | `story=N task N.M words=W` note |
| `/verify-spec` 1d | Story has no `## Definition of Done` | Not a finding | Nothing |
| `/verify-spec` 3b | Completed story has a DoD with unchecked items | Unchanged WARN | `[WARN] Unchecked Definition of Done` |
| Trial worktree | Pre-implementation commit cannot be resolved | Pick the next candidate spec; record why in the report | Report names the skipped spec |
| Trial run | `/implement-story` fails or stops for a question in one arm | Record the stop and its gate; do not retry only one arm | Report row reads `stopped at <gate>` |

## Shadow Paths

| Path | Behavior |
|---|---|
| Happy: all tasks ≤50 words | No new finding; Step 2.6a passes |
| Nil: story file has no tasks section | No `oversized_task`; existing `untasked_criterion` behavior unchanged |
| Empty: task line is only a checkbox and tag | 0 words; no finding |
| Upstream: legacy spec under `/verify-spec` with long tasks and `Completed ✅` | No finding (status scope) |

## Trial procedure (Story 5)

1. **Pick the spec.** From `.writ/specs/archive/`, pick a spec with ≤3 stories, a `drift-log.md`, and median task length above 35 words, whose implementation commits are identifiable with `git log --follow` on its files. Record the candidates and why one was picked.
2. **Cut worktrees.** Resolve `BASE` = the parent of the spec's first implementation commit. Create two worktrees from `BASE` in the scratchpad or `/tmp`, never inside the main checkout: `arm-original` with the archived spec folder copied in unchanged, and `arm-lean` with the same folder whose `user-stories/` were regenerated by the Story 2–4 generator from the same `spec.md` and `technical-spec.md`.
3. **Run.** In each arm, run `/implement-story` on every story in dependency order, under the same model and settings. Headless runs: add `< /dev/null` to `claude -p`, and note that headless mode lacks AskUserQuestion and Plan Mode.
4. **Measure per arm:** story words (total and per task), `[DEV-` entries in the drift log, review findings by severity, gates that failed or stopped, tests passing at the end.
5. **Report.** Write `trial-report.md`: method, the spec picked, a per-arm table, and a verdict line: `lean-tasks: keep`, `lean-tasks: regress (<what got worse>)`, or `lean-tasks: inconclusive`. State the sample size. Remove both worktrees with `git worktree remove` when done.
