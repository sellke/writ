# Story 2: /ship deletes the landed local branch

> **Status:** Not Started
> **Priority:** Normal
> **Dependencies:** None

## User Story

**As a** developer who lands a PR with `/ship`
**I want to** have the local feature branch deleted after its PR lands, and only when no commit is lost
**So that** `git branch` stops listing branches that are already merged

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [ ] Given a local branch whose tip is an ancestor of `origin/<default>`, checked out clean in this repo, when `scripts/ship-branch-cleanup.py delete` runs, then it prints one `ship-branch-cleanup-v1` line with `status: deleted` and `method: -d`, the branch no longer exists, and the exit code is 0 `[AC-2.1]`
- [ ] Given a branch whose PR is `MERGED` by squash, with `--pr-head` equal to the local tip, when delete runs, then the branch is deleted with `method: -D`; and given the same PR with one extra local commit, then the branch is kept with reason `local_commits_not_in_pr` and still exists `[AC-2.2]`
- [ ] Given a dirty tree on the checked-out branch, a branch checked out in another worktree, a failed `git fetch`, or a branch that is neither merged nor PR-proven, when delete runs, then the branch is kept with reason `dirty_tree`, `checked_out_elsewhere:<path>`, `fetch_failed`, or `not_merged`, and the exit code is 0 `[AC-2.3]`
- [ ] Given `writ.deleteMergedBranches` set to `false`, a branch equal to `--default`, or a branch absent locally, when delete runs, then it prints `status: skipped` with reason `opted_out`, `default_branch`, or `no_branch`, and changes no ref `[AC-2.4]`
- [ ] Given the Story 2 changes, when the text pins run, then `commands/ship.md` has Step 6b after Step 6 that runs when `writ.auditNotes=false`, 7.6 merge item 7 runs Steps 6 and 6b, the completion output has a `🧹` line, "Never `--delete-branch`" remains, and the helper is registered in `.writ/docs/agent-cli-contract.md` and `scripts/tests/test_agent_cli_contract.py` `[AC-2.5]`

## Implementation Tasks

- [ ] 2.1 Write tests in `scripts/tests/test_ship_branch_cleanup.py` using temp repos with a bare `origin`: one case per check, plus squash-merge `-D` and extra-commit kept cases. Run with `gh` absent from `PATH`. Add text pins for `commands/ship.md` Step 6b. `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
- [ ] 2.2 Create `scripts/ship-branch-cleanup.py` with a `delete` subcommand taking `--branch`, `--default`, `--pr-state`, `--pr-head`, `--repo`. Implement the ten checks in technical-spec.md Story 2 item 1. Print one `ship-branch-cleanup-v1` JSON line. Exit 0 on every outcome, 2 on usage error. `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`
- [ ] 2.3 Register `scripts/ship-branch-cleanup.py` in `.writ/docs/agent-cli-contract.md` and `scripts/tests/test_agent_cli_contract.py`. Run `python3 scripts/gen-platform-trees.py` to create its `plugins/writ/scripts/` copy. `[AC-2.5]`
- [ ] 2.4 Add Step 6b (Branch Cleanup, post-land) to `commands/ship.md` after Step 6. Gate it per Business Rules 2 and 3. Print the helper's `🧹` line. Change 7.6 merge item 7 to run Steps 6 and 6b. Add the `🧹` line to completion output. Keep "Never `--delete-branch`". `[AC-2.5]`
- [ ] 2.5 Measure `commands/ship.md` growth against `KNOWN_OVER_BUDGET` in `scripts/tests/test_governor_enforcement.py`. Offset growth in-file where no pinned text changes. Otherwise re-pin with a dated `# 2026-11-09` comment, and update `scripts/tests/test_harness_cuts.py` if it pins the same bytes. `[AC-2.5]`
- [ ] 2.6 Verify each acceptance criterion is met by its test or text pin. Confirm the helper deletes nothing on a skipped or kept outcome. `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
- [ ] 2.7 Verify all tests pass: pytest on Python 3.9 and 3.14 (each run alone), the bash test loop, `bash scripts/eval.sh`, and `python3 scripts/gen-platform-trees.py --check`. `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`

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
