# Technical Spec: Evidence-Gated Review

> Spec: [`../spec.md`](../spec.md) · Stories: [`../user-stories/README.md`](../user-stories/README.md)

## Evidence Block Grammar

Each Critical or Major issue under `### Issues Found` may carry exactly one `**Evidence:**` field, written after `**Category:**`. The field's first token names the kind.

````markdown
- **Issue:** `parse_limit()` accepts a negative limit and returns every row
- **Location:** `api/limits.py:31`
- **Severity:** Major
- **Category:** criterion [AC-2.3]
- **Evidence:** test `tests/test_limits_repro.py`
  ```python
  from api.limits import parse_limit

  def test_negative_limit_rejected():
      assert parse_limit("-1") is None
  ```
````

| Kind | Field form | Notes |
|---|---|---|
| `test` | `test <path>` followed by exactly one fenced code block, indented or not | The block is the whole file. One file per finding. |
| `recorded` | `recorded <path>::<test name>` | The test name as the runner prints it (for pytest, `test_fn` or `Class::test_fn`). |
| `check` | `check <command and arguments>` in backticks | The command must start with one of the Gate 2 recorded commands, compared token by token after `shlex.split`. |
| `security-path` | `security-path source <path:line> sink <path:line>` | Two citations. Each is valid the way a `read` line is in `safety-fact`. |

Parsing rules:
- Field names match case-insensitively, with or without bold markers, the same way `SAFETY_FIELD` matches them.
- The first fenced block after a `test` field belongs to it. A second `**Evidence:**` field on the same issue is ignored (`reason: extra_evidence F<n>`).
- An AC ID is any `AC-N.M` token in the issue's Category, Issue, or Location text.
- Finding keys are `F1` to `Fn`, in output order. Each per-finding line also prints the normalized Location, using the rule from `review-panel.py` `normalize_location`, copied as a pattern.

### /review form

`/review` reports have no `### Issues Found`. Story 5 adds a `## Evidence` section after `## Failure Modes Registry`:

```markdown
## Evidence

#### FM-001
- **Location:** `src/pay/charge.ts:88`
- **Category:** security
- **Evidence:** security-path source `src/api/routes.ts:42` sink `src/pay/charge.ts:88`
```

`--surface review` reads severities from the registry table (`| FM-001 | <category> | <severity> | …`) and evidence from `#### FM-NNN` blocks. A registry row with no block is `advisory (no_evidence)`.

## CLI

```
python3 scripts/review-override.py evidence
    --review-output FILE          # the Gate 3 agent output, or the /review report
    --repo DIR                    # default .
    --changed FILE [FILE ...]     # the story's changed files, or the /review diff files
    [--surface gate3|review]      # default gate3
    [--tests-output FILE]         # recorded_test_results, for `recorded` and --prior
    [--checks FILE]               # Gate 2 recorded commands, one per line
    [--prior MANIFEST]            # re-review: check earlier confirmed repros first
    [--manifest-out FILE]         # where to write evidence-manifest-v1 on confirmation
    [--timeout SECONDS]           # per run, default 120
```

Output is the check shape:

```
fail
finding F1: confirmed (test tests/test_limits_repro.py, exit 1)
finding F2: advisory (no_evidence)
finding F3: advisory (unverifiable collection_error)
reason: confirmed F1
review-override evidence: fail (1 confirmed, 1 advisory, 1 unverifiable)
```

| Line 1 | Meaning | Exit |
|---|---|---|
| `fail` | At least one finding confirmed, or a `--prior` check failed, or the tree changed (`reason: repro_mutated_tree <paths>` comes first) | 1 |
| `pass` | The review output has a FAIL verdict and no finding is confirmed | 0 |
| `unverifiable` | Switch off (`reason: switch_off`), no `Test Runner` and no runnable kind left (`no_test_runner`), no git (`no_git`), unreadable review output (`no_review_output`), or a review verdict that is not FAIL (`verdict_not_fail <verdict>`) | 0 |
| — | Usage error, such as a missing `--review-output` path argument or an unknown `--surface` | 2 |

The story report's `evidence-gate:` line is built from the summary counts. It reads `blocked (...)` when the first reason is `repro_mutated_tree`.

`switch --name evidence-gate` gets added to `SWITCH_LINES` with the pattern `^\s*-\s*\*\*Evidence Gate:\*\*\s*(.*)$`.

## Runner Classification

The runner is detected from the `Test Runner` value after `shlex.split`. Leading `uv run`, `poetry run`, `bundle exec`, `npx`, `pnpm`, `yarn`, and `python -m`/`python3 -m` are skipped. `npm test` and `npm run test` resolve through `package.json` `scripts.test`. Anything else is `unverifiable unknown_runner <token>`.

| Runner | Scoped command | Test-failed class (confirmed) | Passed (advisory) | Everything else (unverifiable) |
|---|---|---|---|---|
| pytest | `<runner> <path>` | exit 1 | exit 0 | exit 2 to 5 (interrupted, internal, usage, no tests collected) |
| jest | `<runner> <path>` | exit 1, a `Tests:` line with `N failed` where N ≥ 1, and no `Test suite failed to run` | exit 0 | any other output |
| vitest | `<runner> run <path>`, or `<runner> <path>` when `run` is already in the value | exit 1 and a `Tests` summary with ≥ 1 failed | exit 0 | `no tests`, `Error:` before any test result, other exits |
| go test | `<runner> ./<dir of path>` | exit 1 and a `--- FAIL:` line | exit 0 | `[build failed]`, `[setup failed]` |
| cargo test | `<runner> --test <file stem>` | exit 101 and `test result: FAILED` | exit 0 | `could not compile`, `error[E` |
| rspec | `<runner> <path>` | exit 1 and `N examples, M failures` where M ≥ 1, with no `errors occurred outside of examples` | exit 0 | any other output |

A timeout is `unverifiable timeout <seconds>`. A runner that cannot start (`FileNotFoundError`) is project-level `unverifiable runner_not_found` for the whole call.

### Repro Paths

A `test` path counts only when:
- it is relative, resolves inside the repo through `_inside`, and does not exist yet (`path_exists`);
- its file name matches the runner's pattern: pytest `test_*.py` or `*_test.py`; jest and vitest `*.test.*` or `*.spec.*`, or any file under `__tests__/`; go `*_test.go`; cargo `tests/<name>.rs`; rspec `*_spec.rb`. Otherwise it is `not_a_test_path`;
- its parent directory either already exists or is created for the run and removed after it.

## Tree Snapshot

Before each run, and again after the repro file is deleted:

1. `git status --porcelain=v1 -z --untracked-files=all` gives the full status list.
2. `git diff HEAD --binary` is hashed with SHA-256.
3. Every untracked path from step 1 is hashed with SHA-256 of its bytes.

The two snapshots must be identical. Ignored files (caches, `node_modules`, `.pytest_cache`) do not appear in step 1, so a runner's cache writes do not count as mutation. On a mismatch, the paths that differ become `reason: repro_mutated_tree <paths>`. The script stops running repros and leaves the tree as it is. It never restores anything. The orchestrator escalates as BLOCKED.

If the repro file cannot be deleted, that is also `repro_mutated_tree <path>`.

## Manifest

`.writ/state/evidence-<story-stem>.json`:

```json
{
  "schema": "evidence-manifest-v1",
  "story": "story-3-settlement-view",
  "repros": [
    {"finding": "F1", "path": "tests/test_limits_repro.py", "sha256": "<hex>", "kind": "test", "location": "api/limits.py:31"}
  ]
}
```

It is written atomically (temporary file, then `os.replace`), the way `review-panel.py` `_write_json_atomic` does it. When the file already exists, `--manifest-out` merges: earlier entries stay, and a new confirmation with the same path replaces that entry. A run with no new confirmations leaves the file as it is. Earlier repros stay protected on every later re-review. With `--prior`, these checks run before anything else, in this order:
- `repro_removed`: the path is not in `--changed`.
- `repro_modified`: the normalized SHA-256 differs.
- `repro_still_failing`: the `--tests-output` text does not contain the path, or has no `exit code: 0` line. This reuses `_tested_ok`'s recorded-run rule. The manifest stores a path, not a test name, so the match is by file.

Each failure is one `reason:` line and makes line 1 `fail`.
- On a review verdict of FAIL, new findings are then evaluated as usual.
- On PASS or PAUSE, only the prior checks run. If they all pass, line 1 is `pass` with `reason: prior_ok`, and the `verdict_not_fail` unverifiable row does not apply.

## Gate 3 Wiring (Story 3, Story 4)

- Save Gate 2's lint and typecheck commands, one per line, to `.writ/state/gate2-checks-<story-stem>.txt`, and the agent output to `.writ/state/gate3-review-<story-stem>.md`. `safety-fact` already uses that review path.
- After `check` and `safety-fact`, run the following on an agent FAIL. When `.writ/state/evidence-<story-stem>.json` exists, run it on every verdict, with `--prior`:

```bash
python3 scripts/review-override.py evidence --review-output .writ/state/gate3-review-<story-stem>.md --repo . --changed <files> --tests-output .writ/state/gate3-tests-<story-stem>.txt --checks .writ/state/gate2-checks-<story-stem>.txt --manifest-out .writ/state/evidence-<story-stem>.json [--prior .writ/state/evidence-<story-stem>.json]
```

- The recode brief adds an `## Evidence repros` section. Each entry lists the confirmed finding, the path, the exact content inside a fence, and one line: "Create this file with this exact content and do not edit it. Make it pass."
- The re-review's `recorded_test_results` run includes every path in the manifest.
- Report line: `evidence-gate: <summary counts>`, `off`, `unverifiable (<reason>)`, `blocked (<reason>)`, or `not run (PASS|PAUSE)`.

## Removals

### Safety Fact floor (Story 6)

This is a change, not a removal. The reviewer filters stay (spec.md → Amendment). Line numbers are from 2026-11-04; re-grep before editing.

| File | Change |
|---|---|
| `scripts/review-override.py` | set `FLOOR = "tested"` (line 276). In the module docstring, change the `Floor:` line (lines 43 to 44, "Floor: `traced`") and the output example `(measured <m>, floor traced)` (line 48) to `tested`. The printed line already uses `FLOOR`. |
| `skills/blast-radius/SKILL.md` | Evidence Ladder (lines 34 to 35): "The floor is `traced`" becomes `tested`. On a re-review (line 119): the `safety_fact_below_floor` advice becomes "the measured rung is under `tested`. Cite a test from the recorded run; only the coder can add one." The `reproduced` section has no floor sentence today. |
| Tests | `test_review_override.py`: `_sf_expected` prints `floor traced` (line 731). `SafetyFactVerdictTests` cases that expect `pass` at measured `traced` (`TRACED` evidence, for example `test_pass_prints_contract_lines`, `test_holds_no_with_fail_or_pause_passes`, `test_overclaim_alone_is_not_a_reason`, `test_underclaim_prints_measured`) now expect `safety_fact_below_floor traced`, or switch to `tested` evidence. `test_below_floor_alone`'s docstring names the `traced` floor. No other test under `scripts/tests/` asserts the floor. The `reviewer-filters` tests do not change. |
| Generated trees | `python3 scripts/gen-platform-trees.py` rewrites `cursor/plugin/skills/blast-radius/SKILL.md`, `plugins/writ/skills/blast-radius/SKILL.md`, and `plugins/writ/scripts/review-override.py` |

`commands/implement-story.md` and `agents/review-agent.md` carry no `traced` floor wording. The Gate 3 safety-fact paragraph says "below floor" without naming the rung.

### Review panel (Story 7)

| File | Change |
|---|---|
| `scripts/review-panel.py` | remove `status`, `tally`, `resolve`, `config_value`, `slug_vendor`, `origin_vendor`, `load_tally`, `cmd_tally`, `cmd_status`, and their parser entries. Keep `_prepare_run`, `PrepareError`, `parse_output`, `trial_key`, `_key_order`, `normalize_location`, `_issue_entries`, and the trial subcommands. |
| `commands/implement-story.md` | remove the `--panel` invocation row and its conflict rule, the `--panel` qualifier in Gate 0's Route line, the "Review panel (opt-in)" paragraph, the panel `block` clause in Gate 3.5 § A, "A fail counts as a panel `block`" in the safety-fact paragraph (rewrite it to "A fail is one review-loop increment"), the `review-panel:` report line, the panel mention in the default spawn count, and the words "panel reviewers" in Gate 3's "Reviewer filters." paragraph (the paragraph stays). Add the leftover-config line and the `--panel` rejection. |
| `.writ/docs/config-format.md` | remove the `Review Panel` row and section; add a one-line "Removed keys" entry pointing to ADR-032 |
| `.writ/config.md` (this repo only; does not ship) | delete the `- **Review Panel:**` line |
| `adapters/claude-code.md`, `codex.md`, `cursor.md`, `openclaw.md` | remove the "Review panel (ADR-028)" paragraph |
| `.writ/docs/agent-cli-contract.md` | update the `review-panel.py` row to the remaining subcommands |
| `scripts/eval.sh` | remove `review-panel` from the check list and delete its function |
| Tests | update `test_review_panel.py` (drop the status and tally cases, keep the parser and trial cases), `test_panel_trial_outcome.py` (`test_panel_wiring_matches_the_verdict` expects the paragraph absent once ADR-032 is accepted; the record checks stay), `test_eval_shipped_refs.py`, `test_agent_cli_contract.py`, `test_harness_cuts.py`, `test_governor_enforcement.py`, `test_design_divergence_wiring.py`, and `test_review_route_rigor.py` (`Gate3WiringTest` asserts "panel reviewers" in the reviewer-filters paragraph); add `ShippedPanelScanTests` to `test_evidence_gate_wiring.py` |

`review-panel.py` has no shipped caller after Story 7. Moving it out of the shipped set is left for when the gate-upgrade-trial harness is deleted, which is that spec's Story 4.

## Byte Budget

`commands/implement-story.md` is over its per-invocation budget (`.writ/docs/leanness-audit-2026-10-21.md`). Each story that edits it prints the byte count before and after, using `wc -c`, in its What Was Built record. Stories 3, 4, and 7 edit it. Story 6 does not plan to; it records the counts only if it does. The total across these stories must be ≤ 0. Story 7's panel removals, including the "panel reviewers" trim, must free at least what Stories 3 and 4 add. The panel paragraph alone is about 1,100 bytes. The reviewer filters free nothing, because they stay.

## Error & Rescue Map

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| Read the review output | Missing or unreadable file | `unverifiable no_review_output`; the agent FAIL stands | Pytest with a missing path |
| Parse issues | No `### Issues Found`, or malformed fields | Every finding `advisory (no_evidence)`; line 1 `pass` when the verdict is FAIL | Fixture with a FAIL verdict and no issues section |
| Resolve the runner | No `Test Runner` line | `test` findings `unverifiable no_test_runner`; when no finding can be decided otherwise, line 1 `unverifiable no_test_runner` | Fixture config with no line |
| Resolve the runner | Unknown runner token | That finding `unverifiable unknown_runner <token>` | Fixture `Test Runner: make test` |
| Write the repro | Path exists, outside the repo, or not a test path | That finding `unverifiable path_exists` / `path_outside_repo` / `not_a_test_path`; nothing is written | Pytest, one case per reason |
| Run the repro | Timeout | Kill the process group; `unverifiable timeout 120` | Fixture runner that sleeps |
| Run the repro | Runner binary missing | Project-level `unverifiable runner_not_found` | Fixture `Test Runner: no-such-binary` |
| Run the repro | Collection or import error | `unverifiable collection_error` (pytest exit 2 to 5, and the per-runner rows) | Fixture repro with a syntax error |
| Snapshot | `git` missing or not a repo | Project-level `unverifiable no_git` | Pytest in a temp dir without `git init` |
| Snapshot | Tree differs after the run | `fail`, `repro_mutated_tree <paths>`, stop; the orchestrator escalates as BLOCKED | Fixture repro that writes `src/x.py` |
| Delete the repro | Removal fails | `repro_mutated_tree <path>` | Pytest with the parent directory made read-only (skipped on Windows) |
| Write the manifest | Disk error | `reason: manifest_write_failed`; line 1 is unchanged; the recode brief carries the repros anyway | Pytest with an unwritable path |
| `--prior` | Manifest missing or wrong schema | `unverifiable bad_manifest`; the agent verdict stands | Fixture with a wrong schema |
| `/review` | No diff files | All findings `advisory (location_outside_change_set)` | Fixture with `--changed` empty |

## Shadow Paths

| Path | Input | Outcome |
|---|---|---|
| Happy | FAIL with one `test` repro that fails on exit 1 | `fail`, `confirmed F1`, manifest written |
| Nil | `--review-output` names a missing file | `unverifiable no_review_output`, exit 0 |
| Empty | FAIL verdict, `### Issues Found` empty | `pass`, `0 confirmed, 0 advisory, 0 unverifiable` |
| Upstream error | `Test Runner` binary missing | `unverifiable runner_not_found`, the agent FAIL stands |

## Interaction Edge Cases

| Case | Behavior |
|---|---|
| Two findings ship the same repro path | The second one is `unverifiable path_exists`. The first one's file is deleted before the second runs, so the path has to be checked against the set of declared paths, not the disk. |
| A repro passes, but the bug is real | It is advisory. The reviewer's repro has to fail. That burden of proof is intended. |
| A repro fails for an unrelated reason the runner reports as a test failure (a wrong assertion) | It is confirmed. The coder cannot satisfy it, so the loop reaches its cap and the user decides (Business Rule 5). |
| A `check` command that writes files (`eslint --fix`) | The snapshot catches it: `repro_mutated_tree`, BLOCKED. The skill tells reviewers never to use fix flags. |
| A `recorded` test failed and the agent already FAILed on it | It is confirmed at no run cost. This is the common evaluator case. |
| Agent FAIL, and `check` also fails | Row 1 wins. `evidence` still runs, so its lines are in the report, but it does not change the FAIL. |
| `--review-only` | `evidence` runs the same way. A confirmed finding ends the run as FAIL; nothing confirmed ends it as PASS. There is no recode. |

## Test Plan

- `scripts/tests/test_review_override.py` gains an `EvidenceTests` class. Fixtures go under `scripts/tests/fixtures/review-override/evidence/`: a tiny pytest project with `Test Runner: python3 -m pytest`, plus stub runners written as Python scripts that print jest, vitest, go, cargo, and rspec output and exit with set codes.
- There is one test per row of § Error & Rescue Map and § Evidence outcomes. Each runs on Python 3.9 and 3.14.
- A replay test in `scripts/tests/test_evidence_gate_wiring.py` feeds a saved evaluator FAIL output, with and without a confirmed repro, through `evidence`. It asserts the Gate 3 decision row.
- Story 7 writes a scan test, `ShippedPanelScanTests` in `scripts/tests/test_evidence_gate_wiring.py`. It fails when `Review Panel` or `--panel` appears in `commands/`, `agents/`, `skills/`, `adapters/`, `claude-code/`, `cursor/`, `plugins/`, `codex/`, `README.md`, or `SKILL.md`. It skips `.writ/`. A match is allowed only on a line containing `removed (ADR-032)`: the leftover-config and rejection lines. The filter names are not scanned, because the filters stay.
- Full gates: `uv run --isolated --python 3.9 --with pytest pytest`, `uv run --isolated --python 3.14 --with pytest pytest`, the bash suite in the background, `python3 scripts/gen-platform-trees.py --check`, and `bash scripts/eval.sh`. Run pytest on its own (CLAUDE.md).
