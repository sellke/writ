# Delete Merged Branches

> **Status:** Not Started
> **Created:** 2026-11-09
> **Owner:** @AdamSellke
> **Dependencies:** []
> **Origin:** After the v0.47.2 release three merged branches were left behind (`chore/archive-repro-review-route`, `phase/specs-writ-agents-registered`, and its lane branch `writ/phase/specs-writ-agents-registered/2026-11-08-writ-agents-registered`). Nothing in Writ deletes a branch. Decisions in [`recommendation-log.md`](recommendation-log.md).
> **Type:** Improvement. **Priority:** Normal. **Effort:** Small.

## Specification Contract

**Deliverable:** The step that merged a branch deletes it: `phase-state.py integrate` deletes the lane branch after a successful `--no-ff` merge, and `/ship` deletes the local feature branch after its PR lands.

**Must Include:** A branch is deleted only on evidence that no work is lost. Lane: `git branch -d` on the phase branch right after the merge. `/ship`: either `git branch --merged origin/<default>` lists the branch, or (squash or rebase merge) `gh` reports the PR `MERGED` and the local tip equals the PR's `headRefOid`, so the branch holds no unpushed commit.

**Hardest Constraint:** `commands/ship.md` and `commands/implement-phase.md` are both over their byte budgets with exact pinned overages (`KNOWN_OVER_BUDGET` 9110 and 1464 in `scripts/tests/test_governor_enforcement.py`). Every added sentence needs an offset in the same file or a disclosed, dated ledger entry.

**🎯 Experience Design:**
- **Entry point:** `/ship --watch` merging a PR, `/ship` re-run after a PR merged, or an `/implement-phase` lane integrating.
- **Happy path:** the PR merges → Step 6 attaches the audit note → Step 6b switches to the default branch, fast-forwards it, deletes the local branch, and prints one line.
- **Moment of truth:** `git branch` after a phase or a ship lists no branch that was just merged.
- **Feedback model:** `/ship` prints `🧹 deleted local branch <name> (merged into <default>)` or `🧹 kept <name> — <reason>`. Integrate returns `laneBranchDeleted` in its JSON and records it in phase state.
- **Error experience:** cleanup never fails a ship or an integrate. A dirty tree, a branch checked out in another worktree, an unmerged tip, or a git error keeps the branch and prints the reason. Nothing is forced without the merge evidence above.

**📋 Business Rules:**
1. `gh pr merge` keeps "Never `--delete-branch`". Writ does not delete remote heads; GitHub's "Automatically delete head branches" setting covers them.
2. `/ship` cleanup is its own step after Step 6. `writ.auditNotes=false` does not skip it.
3. `/ship` cleanup is opt-out per repo: `git config writ.deleteMergedBranches false` skips it silently. Absent means true, the same pattern as `writ.auditNotes`.
4. `/ship` uses `git branch -d` when `--merged` lists the branch, and `git branch -D` only on the squash or rebase proof in Must Include. Otherwise it keeps the branch.
5. Before deleting the checked-out branch, `/ship` switches to the default branch and runs `git pull --ff-only`. A dirty tree means no switch and no delete.
6. Integrate deletes only the lane branch it just merged, with `git branch -d`, never `-D`. Quarantine branches and closed specs' lane branches are never deleted.
7. Integrate records `laneBranchDeleted: true|false`, plus `laneBranchKeptReason` when false, and keeps `laneBranch` as the historical name. `reconcile` does not flag an integrated spec whose lane branch is gone.

**Success Criteria:**
- **Tests:** integrate deletes the lane on success and keeps it on a failed result, a malformed result, and a merge conflict. The `/ship` helper covers merged, squash-proven, unpushed-commit, dirty, checked-out-elsewhere, and opted-out cases.
- **Eval:** `scripts/eval-phase-lane.py` gains a `lane-branch-deleted-after-merge` check.
- **Suites:** pytest on 3.9 and 3.14, the bash tests, and `eval.sh` stay green; `gen-platform-trees.py --check` is clean; byte ledgers are re-pinned only with a disclosed entry.

**Scope Boundaries:**
- **Included:**
  - new `scripts/ship-branch-cleanup.py` so the deletion rules are tested code, not prose
  - `/ship` Step 6b and its completion line
  - the `integrate` change in `scripts/phase-state.py`
  - one sentence in `commands/implement-phase.md` Step 3.2 item 4
  - `.writ/docs/phase-execution-state-format.md`
  - tests, the eval check, generated plugin copies
- **Excluded:**
  - remote branch deletion
  - `/release` changes
  - sweeping branches merged before this ships
  - quarantine and `close-spec` behavior

**⚠️ Technical Concerns:**
- A squash merge never appears in `--merged`; without the `headRefOid` proof, squash-merge repos would keep every branch.
- `git branch -d` refuses a branch checked out in another worktree. That case is kept and reported, never forced.

**💡 Recommendations:**
- Two stories, one per surface. They share no file, so they can run as parallel lanes.

**⚠️ Cross-Spec Overlap:** none. The only open spec, `2026-10-25-gate-upgrade-removal-measurement`, touches `commands/implement-story.md`.

## 🎯 Experience Design

### User journey

1. **Phase lane.** `/implement-phase` validates a lane result and runs `integrate`. The lane merges into the phase branch, its worktree is removed, and its branch is deleted. `progress` and the report read the merge commit from state, so nothing that reads phase state needs the branch.
2. **`/ship --watch`.** The merge step lands the PR, Step 6 attaches the audit note, and Step 6b deletes the local branch. The pass report and the completion output carry the `🧹` line.
3. **`/ship` after a merge done elsewhere.** The next `/ship` that finds the PR merged runs Step 6 and then Step 6b, the same as the re-entry Step 6 already has.

### State catalog

| State | Condition | Behavior |
|---|---|---|
| Merged ancestor | `git branch --merged origin/<default>` lists the branch | switch off it if checked out, `git branch -d`, print `deleted` |
| Squash or rebase landed | PR `MERGED`, local tip equals `headRefOid` | same, with `git branch -D` |
| Unpushed commit | local tip differs from `headRefOid` and the branch is not merged | keep, `kept <name> — local commits not in the PR` |
| Dirty tree | `git status --porcelain` non-empty and the branch is checked out | keep, `kept <name> — uncommitted changes` |
| Other worktree | `git worktree list --porcelain` shows the branch checked out elsewhere | keep, `kept <name> — checked out in <path>` |
| Default branch | the branch is the default branch | keep, no output |
| Opted out | `writ.deleteMergedBranches=false` | skip, no output |
| Lane merged | integrate's `--no-ff` merge succeeded | `git branch -d <lane>`; `laneBranchDeleted: true` |
| Lane delete refused | `git branch -d` exits non-zero | `laneBranchDeleted: false`, `laneBranchKeptReason` = git's message; integrate still returns `integrated` |
| Lane not merged | result not verified, malformed, or merge conflict | lane kept, as today |

## Business Rules (Expanded)

**Business Rule 1.** Remote deletion stays out of Writ: the merge step never deletes a remote head, so a PR's branch on GitHub follows the repository's own setting.

**Business Rule 2.** Step 6's opt-out gate skips Step 6 entirely; cleanup must not sit inside it. Step 6b has its own gate (Business Rule 3).

**Business Rule 3.** The config key mirrors `writ.auditNotes`: read with `git config --bool writ.deleteMergedBranches`, absent or unreadable means true.

**Business Rule 4.** `-D` is allowed only on positive evidence that the branch tip is the commit GitHub merged. A tip that differs is unpushed work and is kept.

**Business Rule 5.** Switching branches with uncommitted changes could carry or lose them; a dirty tree keeps the branch and the checkout as they are.

**Business Rule 6.** Integrate has just merged the lane with `--no-ff` into the checked-out phase branch, so `-d` succeeds unless git finds a reason to refuse; that reason is recorded, never overridden.

**Business Rule 7.** `reconcile` already checks lane branches only for `implementing`, `quarantined`, and `closed_not_implemented` specs. An `integrated` spec is checked by its `mergeCommit`. The field keeps the name so the report can still say which lane merged.

## Detailed Requirements

- **Helper:** `scripts/ship-branch-cleanup.py delete --branch <b> --default <d> [--pr-state <s>] [--pr-head <sha>] [--repo <path>]` prints one JSON object (`schema: ship-branch-cleanup-v1`, `status: deleted|kept|skipped`, `reason`, `method: -d|-D|null`, `branch`) and exits 0 on every outcome except a usage error (2). It reads the opt-out, runs `git fetch origin <default>`, checks worktrees and the tree, switches and fast-forwards when needed, and deletes. It never calls `gh`; the caller passes `--pr-state` and `--pr-head` from the `gh pr view` it already ran.
- **`/ship` Step 6b:** after Step 6 (or after Step 6 is skipped), run the helper with the PR's `state` and `headRefOid`, then print its line. In `--watch`, it runs in the same pass as the merge. The completion output gains one `🧹` line.
- **Integrate:** after the worktree removal, `git branch -d <laneBranch>`; record `laneBranchDeleted` and, on refusal, `laneBranchKeptReason`; include `laneBranchDeleted` in the returned JSON.
- **Docs:** `phase-execution-state-format.md` documents both new fields and says the lane branch is deleted after a merge. `implement-phase.md` Step 3.2 item 4 says "the worktree and lane branch are then removed".
- **Registration:** the new script follows `.writ/docs/agent-cli-contract.md`, is registered in `scripts/tests/test_agent_cli_contract.py`, and gets its plugin copy from `gen-platform-trees.py`.

## Implementation Approach

Two stories with no shared file. Story 1 changes `scripts/phase-state.py`, its state-format doc, `implement-phase.md`, and the lane eval. Story 2 adds the helper, its tests, and `/ship` Step 6b. Python 3.9 floor. Byte growth in the two over-budget commands is offset in the same file where possible, otherwise disclosed in the `KNOWN_OVER_BUDGET` ledger with a dated comment.
