# Delete Merged Branches (Lite)

> Source: .writ/specs/2026-11-09-delete-merged-branches/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** `phase-state.py integrate` deletes the lane branch after a successful `--no-ff` merge; `/ship` deletes the local feature branch after its PR lands.

**Implementation Approach:**
- Story 1: `git branch -d <lane>` in `cmd_integrate` after worktree removal; record `laneBranchDeleted` / `laneBranchKeptReason`; eval check; state-format doc; one `implement-phase.md` sentence.
- Story 2: new `scripts/ship-branch-cleanup.py delete` (ordered checks in technical-spec); `/ship` Step 6b; completion line; agent-cli-contract registration; plugin copy.
- Python 3.9 floor. Helper never calls `gh`; caller passes `--pr-state`, `--pr-head`.
- Row 9 confirms HEAD and pulls `--ff-only --no-rebase`; a failed `git status` keeps the branch as `dirty_tree` (DEV-003).
- Plain `/ship` reads `gh pr view --json state,headRefOid,mergeCommit` before Step 2; `MERGED` → Steps 6 and 6b, stop (DEV-005).

**Files in Scope:**
- `scripts/phase-state.py`, `scripts/eval-phase-lane.py`, `.writ/docs/phase-execution-state-format.md`, `commands/implement-phase.md`
- `scripts/ship-branch-cleanup.py` (new), `scripts/tests/test_ship_branch_cleanup.py` (new), `commands/ship.md`
- `scripts/tests/test_phase_state.py`, `scripts/tests/test_agent_cli_contract.py`, `.writ/docs/agent-cli-contract.md`
- Generated: `plugins/writ/scripts/` via `gen-platform-trees.py`
- `scripts/tests/test_governor_enforcement.py` (`KNOWN_OVER_BUDGET`, residual only)
- Never: remote branch deletion, `/release`, quarantine or `close-spec`

**Error Handling:**
- Lane `-d` refused → kept, reason recorded, status still `integrated`
- Dirty tree, other worktree, fetch failure, unpushed commits → branch kept, reason printed
- Cleanup never fails a ship or an integrate
- Step 6b does not run under `--dry-run` (DEV-002)

**Integration Points:**
- `/ship` Step 7.6 merge step item 7 appends "; then Step 6b" (the existing clause is pinned; DEV-001)
- `reconcile` does not check lane branches of `integrated` specs

---

## For Review Agents

**Acceptance Criteria:**
1. Integrate deletes the merged lane branch and records `laneBranchDeleted: true` `[AC-1.1]`
2. A failed, malformed, or conflicting result keeps the lane branch `[AC-1.3]`
3. A refused delete keeps the branch, records the reason, and still returns `integrated` `[AC-1.2]`
4. The helper deletes with `-d` when `--merged` lists the branch, and `-D` only when the PR is `MERGED` and the tip equals `headRefOid` `[AC-2.1, AC-2.2]`
5. The helper keeps the branch on dirty tree, other worktree, unpushed commits, or fetch failure, and skips on opt-out `[AC-2.3, AC-2.4]`
6. `/ship` Step 6b runs after Step 6 even when `writ.auditNotes=false`; "Never `--delete-branch`" stays `[AC-2.5]`

**Business Rules:**
- No remote deletion; `-D` only on the squash/rebase proof
- Opt-out `writ.deleteMergedBranches=false`, absent = true
- Quarantine and closed lanes never deleted

**Experience Design:**
- Entry: `/ship --watch` merge, `/ship` re-run after merge, `/implement-phase` integrate
- Happy path: merge → audit note → switch, ff, delete
- Moment of truth: `git branch` lists no just-merged branch
- Feedback: `🧹 deleted local branch …` / `🧹 kept … — <reason>`; `laneBranchDeleted`
- Error: branch kept with a reason; never a failed ship

---

## For Testing Agents

**Success Criteria:**
1. `test_ship_branch_cleanup.py` covers every helper row
2. `eval-phase-lane.py` `lane-branch-deleted-after-merge` passes
3. pytest 3.9 and 3.14, bash tests, `eval.sh`, `gen-platform-trees.py --check` green

**Shadow Paths to Verify:**
- **Happy path:** merge-commit PR, clean, checked out → `deleted`, `-d`
- **Nil input:** no `--pr-head` → only `--merged` proof
- **Empty input:** branch already gone → `skipped`, `no_branch`
- **Upstream error:** fetch fails → `kept`, `fetch_failed`

**Edge Cases:**
- Squash merge, tip equals head → `-D`; tip has an extra commit → kept
- Branch checked out in another worktree → kept

**Test Strategy:**
- Temp git repos with a bare `origin`; pytest for integrate and reconcile; eval check; text pins for Step 6b
