# Story 2: /ship deletes the landed local branch

> **Status:** Completed ✅ (2026-11-09)
> **Priority:** Normal
> **Dependencies:** None

## User Story

**As a** developer who lands a PR with `/ship`
**I want to** have the local feature branch deleted after its PR lands, and only when no commit is lost
**So that** `git branch` stops listing branches that are already merged

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [x] Given a local branch whose tip is an ancestor of `origin/<default>`, checked out clean in this repo, when `scripts/ship-branch-cleanup.py delete` runs, then it prints one `ship-branch-cleanup-v1` line with `status: deleted` and `method: -d`, the branch no longer exists, and the exit code is 0 `[AC-2.1]`
- [x] Given a branch whose PR is `MERGED` by squash, with `--pr-head` equal to the local tip, when delete runs, then the branch is deleted with `method: -D`; and given the same PR with one extra local commit, then the branch is kept with reason `local_commits_not_in_pr` and still exists `[AC-2.2]`
- [x] Given a dirty tree on the checked-out branch, a branch checked out in another worktree, a failed `git fetch`, or a branch that is neither merged nor PR-proven, when delete runs, then the branch is kept with reason `dirty_tree`, `checked_out_elsewhere:<path>`, `fetch_failed`, or `not_merged`, and the exit code is 0 `[AC-2.3]`
- [x] Given `writ.deleteMergedBranches` set to `false`, a branch equal to `--default`, or a branch absent locally, when delete runs, then it prints `status: skipped` with reason `opted_out`, `default_branch`, or `no_branch`, and changes no ref `[AC-2.4]`
- [x] Given the Story 2 changes, when the text pins run, then `commands/ship.md` has Step 6b after Step 6 that runs when `writ.auditNotes=false`, 7.6 merge item 7 runs Steps 6 and 6b, the completion output has a `🧹` line, "Never `--delete-branch`" remains, and the helper is registered in `.writ/docs/agent-cli-contract.md` and `scripts/tests/test_agent_cli_contract.py` `[AC-2.5]`

## Implementation Tasks

- [x] 2.1 Write tests in `scripts/tests/test_ship_branch_cleanup.py` using temp repos with a bare `origin`: one case per check, plus squash-merge `-D` and extra-commit kept cases. Run with `gh` absent from `PATH`. Add text pins for `commands/ship.md` Step 6b. `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
- [x] 2.2 Create `scripts/ship-branch-cleanup.py` with a `delete` subcommand taking `--branch`, `--default`, `--pr-state`, `--pr-head`, `--repo`. Implement the ten checks in technical-spec.md Story 2 item 1. Print one `ship-branch-cleanup-v1` JSON line. Exit 0 on every outcome, 2 on usage error. `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`
- [x] 2.3 Register `scripts/ship-branch-cleanup.py` in `.writ/docs/agent-cli-contract.md` and `scripts/tests/test_agent_cli_contract.py`. Run `python3 scripts/gen-platform-trees.py` to create its `plugins/writ/scripts/` copy. `[AC-2.5]`
- [x] 2.4 Add Step 6b (Branch Cleanup, post-land) to `commands/ship.md` after Step 6. Gate it per Business Rules 2 and 3. Print the helper's `🧹` line. Change 7.6 merge item 7 to run Steps 6 and 6b. Add the `🧹` line to completion output. Keep "Never `--delete-branch`". `[AC-2.5]`
- [x] 2.5 Measure `commands/ship.md` growth against `KNOWN_OVER_BUDGET` in `scripts/tests/test_governor_enforcement.py`. Offset growth in-file where no pinned text changes. Otherwise re-pin with a dated `# 2026-11-09` comment, and update `scripts/tests/test_harness_cuts.py` if it pins the same bytes. `[AC-2.5]`
- [x] 2.6 Verify each acceptance criterion is met by its test or text pin. Confirm the helper deletes nothing on a skipped or kept outcome. `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
- [x] 2.7 Verify all tests pass: pytest on Python 3.9 and 3.14 (each run alone), the bash test loop, `bash scripts/eval.sh`, and `python3 scripts/gen-platform-trees.py --check`. `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`

## Notes

- **Squash merges never appear in `git branch --merged`.** The `-D` path needs the PR proof: `--pr-state MERGED` and `--pr-head` equal to `git rev-parse <branch>`. Without `--pr-head`, only the `--merged` proof applies.
- **`git branch -d` refuses a branch checked out in another worktree.** Keep the branch and report the path. Never force it.
- **The helper never calls `gh`.** The caller passes `--pr-state` and `--pr-head` from a `gh pr view` it already ran. Step 6b adds no `gh` call.
- **Byte budget.** `commands/ship.md` is pinned at `KNOWN_OVER_BUDGET` 9110 in `scripts/tests/test_governor_enforcement.py`. Growth needs an in-file offset or a dated re-pin. Re-pin only the residual.
- **Python 3.9 floor.** No 3.10+ syntax or stdlib. The suite runs on 3.9 and 3.14.
- **Test isolation.** Temp repos must not read the user's git config. Set `GIT_CONFIG_GLOBAL=/dev/null`, and pass `-c user.name=t -c user.email=t@t` on every commit. Otherwise `writ.deleteMergedBranches` or the default branch name can leak in.
- **Run pytest alone.** `eval.sh`, the bash tests, or `git worktree` changes in the same checkout during pytest break `test_smoke_leaves_repo_unchanged` and the `app-verify` tests.
- **No shared file with Story 1.** Story 1 changes `scripts/phase-state.py`. The two stories can run as parallel lanes.
- **Out of scope.** Remote branch deletion; `--delete-branch` stays banned (GitHub's head-branch setting covers remote heads); sweeping branches merged before this ships.

## Context for Agents

- **Error map rows:** [fetch fails, dirty tree, branch in another worktree, local commits not in the PR, ff-only pull fails] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [Happy path, Nil input, Empty input, Upstream error] — technical-spec.md → ## Shadow Paths
- **Business rules:** [Business Rule 1, Business Rule 2, Business Rule 3, Business Rule 4, Business Rule 5] — spec.md → ## Business Rules (Expanded)
- **Experience:** [State catalog rows: Merged ancestor, Squash or rebase landed, Unpushed commit, Dirty tree, Other worktree, Default branch, Opted out (spec.md → ## 🎯 Experience Design → ### State catalog); Feedback model (spec.md → ## Specification Contract → 🎯 Experience Design)]

## What Was Built

**Implementation Date:** 2026-11-09

### Files Created

1. **`scripts/ship-branch-cleanup.py`** (`delete` subcommand)
   - Runs the ten ordered checks (opt-out, default/no branch, other worktree, fetch, `--merged` → `-d`, PR `MERGED` + tip == `--pr-head` → `-D`, kept, dirty tree, switch + `pull --ff-only --no-rebase`, delete). Prints one `ship-branch-cleanup-v1` line; exit 0 on every outcome, 2 on usage error; never calls `gh`; rejects names starting with `-`; a failed `git status` keeps the branch as `dirty_tree`.
2. **`scripts/tests/test_ship_branch_cleanup.py`** — 32 tests over temp repos with a bare `origin` and a stand-in remote that lands by merge or squash; `gh` absent from PATH; global/system git config off.
3. **`scripts/tests/test_ship_step6b_head_repro.py`** — Gate 3 evidence repro for F1 (7.1 reads `headRefOid`), committed unedited.
4. **`plugins/writ/scripts/ship-branch-cleanup.py`** — generated copy.

### Files Modified

- **`commands/ship.md`**
  - New Step 6b (Branch Cleanup, post-land): own `writ.deleteMergedBranches` gate, runs even when `writ.auditNotes=false`, not under `--dry-run`, non-blocking, prints the 🧹 line.
  - Step 2: before "No changes to ship", `gh pr view --json state,headRefOid,mergeCommit`; `MERGED` → Steps 6 and 6b with `mergeCommit.oid` as the landed SHA, then stop; otherwise (`OPEN`, `CLOSED`, no PR, `gh` fails) → merge as before.
  - 7.1 reads `number,state,headRefOid,mergeCommit`; `MERGED` → Steps 6 and 6b. Merge item 7 appends "; then Step 6b". Completion output gains the 🧹 line. "Never `--delete-branch`" kept.
  - 34070 bytes before and after, by in-file trims checked against pins; `KNOWN_OVER_BUDGET` 9110 unchanged.
- **`.writ/docs/agent-cli-contract.md`** — classification row and Notes line for the helper.
- **`scripts/tests/test_agent_cli_contract.py`** — read-only smoke (`no_branch`).
- **Generated copies:** `cursor/plugin/commands/ship.md`, `plugins/writ/commands/ship.md`.

### Implementation Decisions

1. **The helper never calls `gh`**; callers pass `--pr-state` and `--pr-head` from the `gh pr view` they already make.
2. **Plain `/ship` checks for a merged PR before Step 2** (person's decision, DEV-005 option a): a Step 2 merge would add a commit and break the tip == `headRefOid` proof.
3. **`method` records the `git branch` flag that ran**, so it is set on `deleted` and `delete_failed`.

### Test Results

**Verification:** orchestrator run of 17 pytest files on 3.9 and 3.14: 800 passed each, exit 0; `eval.sh` checks git-notes-audit, command-structure, leanness, broken-refs, shipped-refs: exit 0; `gen-platform-trees.py --check` pass.
- ✅ story-gate post-review: pass (9 checks, 0 fail, 2 unverifiable: no_coverage_report, coverage_report_absent); safety-fact: tested; evidence-gate: prior_ok

### Review Outcome

**Result:** PASS

- **Iteration count:** 3 iteration(s) — iteration 1 FAIL (F1: 7.1 read no `headRefOid`; confirmed by repro), iteration 2 PASS with recommendations, iteration 3 PASS after taking recommendations 1, 2 and 4
- **Drift:** Small overall (DEV-001, DEV-002, DEV-003 auto-amended; DEV-005 Medium resolved by the person's decision)
- **Security:** Clean
- **Boundary Compliance:** all hand edits in owned files; generated copies verified; the repro file is a Gate 3 artifact
- **Gate 3 route:** review-agent (outside_boundary generated copies), safety_fact on
- **Agents that ran:** Gate 1 `writ-coder` (three runs); Gate 3 `writ-reviewer` (three runs)
- **Advisory (not fixed):** Error Handling's dirty-tree and not-on-a-feature-branch decisions have no stated order relative to the Step 2 `MERGED` check; plain `--dry-run` on a merged PR is not stated; the 6.3 fallback digest range is unspecified. From iteration 1: `switch_failed` when the default branch is checked out in another worktree could get its own reason.

### Deviations from Spec

See drift-log.md DEV-001, DEV-002, DEV-003, DEV-005.
