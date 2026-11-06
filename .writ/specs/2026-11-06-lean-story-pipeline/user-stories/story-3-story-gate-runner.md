# Story 3: story-gate.py runner

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 2

## User Story

**As a** `/implement-story` orchestrator, and the supervisor that reads the record
**I want to** run the default-path deterministic checks through one `story-gate.py` call before Gate 3 and one after, and read a single record per story keyed to the head SHA
**So that** the orchestrator stops invoking each checker by hand, a lane cannot skip a check and still pass, and the procedure file gets smaller

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [ ] Given `scripts/story-gate.py`, when `run --phase pre-review|post-review`, `tally`, `--help`, and exit codes are checked, then the script follows the agent CLI check shape: line 1 `pass|fail|unverifiable`, `reason:` lines, the summary, and `run`'s JSON record as the last line; exit 0/1/2 `[AC-3.1]`
- [ ] Given a stub checker that fails and another that passes in a temp git repo, when `run --phase post-review` runs, then every check runs in fixed order, the record is written atomically to `<state-dir>/story-gate-<story-stem>-post-review.json` with `head_sha` and `dirty`, and `restart` names the first failing check's target `[AC-3.2]`
- [ ] Given a check whose script is missing or exits outside 0, 1, or 2, when `run` completes, then that check reads `unverifiable (helper_error: ...)`, the remaining checks still run, and that check alone does not set the overall verdict to `fail` `[AC-3.3]`
- [ ] Given records under `story-gate-history/`, when `tally` runs, then it prints `runs`, `fails`, and `sole_catches` per check id and writes no file; with no history it prints `unverifiable` and `reason: no_records` `[AC-3.4]`
- [ ] Given the default path in `commands/implement-story.md`, when it is read, then it names exactly two `story-gate.py` calls (`--phase pre-review` before Gate 3, `--phase post-review` after), at most four script invocations in total, a smaller byte size than at story start, and default check ids equal to the `path: default` gates; `agent-cli-contract.md` has a `story-gate.py` row and ADR-029 a dated runner note `[AC-3.5]`

## Implementation Tasks

- [ ] 3.1 Write tests in `scripts/tests/test_story_gate.py` for `run` and `tally` against stub checkers in a temp git repo, covering stdout, record schema, restart order, and `unverifiable`. Add a test that the default check ids equal the `path: default` gates in `commands/implement-story.md`. Confirm they fail first `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`
- [ ] 3.2 Create `scripts/story-gate.py` in the agent CLI check shape: `run --phase pre-review|post-review` and `tally`, with `--help` and exit codes 0/1/2. Invoke the default-path checks in the fixed order from the technical spec. Write the record atomically and keep history. Stdlib only `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`
- [ ] 3.3 Edit the default path in `commands/implement-story.md`: one `story-gate.py run --phase pre-review` call before Gate 3 and one `--phase post-review` call after it, replacing the per-script blocks. Keep Gate 3 and Gate 4 wording otherwise unchanged `[AC-3.5]`
- [ ] 3.4 Update the pinning tests that name the replaced per-script blocks, including `test_implement_story_default_path.py`, `test_boundary_map.py`, `test_change_surface.py`, and `test_docs_check.py`, to pin the runner calls. Keep each guarded behavior. Keep `test_gate_upgrade_trial_outcome.py` presence probes passing `[AC-3.5]`
- [ ] 3.5 Add the `story-gate.py` row to `.writ/docs/agent-cli-contract.md`. Add a dated note to `.writ/decision-records/adr-029-*.md` that a runner for one command's fixed check sequence is not a dispatcher. Record the `implement-story.md` byte change in `KNOWN_OVER_BUDGET` in `scripts/tests/test_governor_enforcement.py`. Regenerate with `python3 scripts/gen-platform-trees.py` `[AC-3.5]`
- [ ] 3.6 Verify acceptance criteria: map each criterion to a passing test or pinned text. Run `python3 scripts/gen-platform-trees.py --check` and confirm it passes `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`
- [ ] 3.7 Verify all tests pass: run the changed test files with `uv run --isolated --python 3.9 --with pytest pytest <files>`, then with `--python 3.14`. Confirm `test_gate_upgrade_trial_outcome.py` passes. Run pytest alone `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`

## Notes

- **Stdout:** `run` always prints the JSON record as its last line, after the check-shape summary (Business Rule 4; `technical-spec.md` → `story-gate.py` → Stdout). There is no `--json` flag.
- **CLI shape is defined elsewhere.** The `run` and `tally` argument lists, the record schema, and the history path are in `technical-spec.md` → `story-gate.py`. Follow that section. Do not copy it into the script's help text.
- **Pre-code check contingency.** If a pre-code check survives Story 2, add a `pre-code` phase. The story then logs Medium drift against the four-invocation success criterion, as `spec.md` → Technical Concerns states.
- **ADR-029 rule 4.** The rule bars "an umbrella binary, dispatcher, or tool registry." The runner covers one command's fixed sequence and routes nothing across commands. If review rejects that distinction, trim the prose and drop the runner. Task 3.5 records the distinction either way.
- **Ledger.** `implement-story.md` must shrink. `KNOWN_OVER_BUDGET` takes a dated entry only for the recorded byte change. Keep the entry tied to the current size, as the test pins it.
- **Stub checkers.** Tests create stub scripts in a temp repo. Do not write under the real `.writ/state/`. Pass `--state-dir` to a temp path.
- **Record location.** `.writ/state/` is gitignored, so records stay local. Tests must not leave files in the checkout.
- **Python 3.9 floor.** Stdlib only. Do not use 3.10+ APIs. Run `scripts/tests/test_agent_cli_contract.py` against the new script.
- **Targeted verification only.** The full pytest suite and `eval.sh` run once at the end of the spec, not in this story. Run pytest alone. `eval.sh`, bash tests, `.writ/state/` writes, or `git worktree` changes in the same checkout make `test_smoke_leaves_repo_unchanged` fail.
- **File ownership.** This story edits `commands/implement-story.md` and the pinning tests. Agent prose (Story 4) and supervisor and `implement-spec.md` (Story 5) belong to later stories.

## Context for Agents

- **Business rules:** [Business Rule 4, Business Rule 5, Business Rule 7] — spec.md → ## Specification Contract → 📋 Business Rules
- **Error map rows:** [Compute changed files, Run one check, Write record, Tally] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [Happy: every check passes, Nil: no review output (`--quick`), Empty: story changed no files, Upstream: a checker script crashes] — technical-spec.md → ## Shadow Paths
- **Interaction edge cases:** [Coder commits again after post-review `pass`, Two stories in one parallel batch write records at once] — technical-spec.md → ## Interaction Edge Cases
- **Experience:** [Every check passes, One check fails (restart line), A check cannot run (`unverifiable`)] — spec.md → ## 🎯 Experience Design → ### State Catalog
- **Technical:** technical-spec.md → ## `story-gate.py` (`run`, `tally`, Record); spec.md → ## Detailed Requirements (`story-gate.py` bullet)
