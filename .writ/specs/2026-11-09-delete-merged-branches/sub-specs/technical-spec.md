# Technical Spec: Delete Merged Branches

> Spec: [`../spec.md`](../spec.md)

## Current behavior

- `scripts/phase-state.py` `cmd_integrate` (about line 394) checks out the phase branch, merges the lane with `--no-ff`, removes the worktree with `git worktree remove --force`, and records `integrated` + `mergeCommit`. The lane branch stays.
- `cmd_reconcile` checks lane branches for `implementing`, `quarantined`, and `closed_not_implemented` specs only; `integrated` is checked by `mergeCommit`.
- `scripts/eval-phase-lane.py` asserts `verified-success-merges`, `worktree-removed-after-merge`, `state-records-integrated`, and the not-merged cases.
- `commands/ship.md` Step 7.6 merge step: `gh pr merge … --<method>`, "Never `--delete-branch`, `--admin`, or `--auto`". Step 6 attaches the audit note; its 6.0 gate skips all of Step 6 when `writ.auditNotes=false`. Nothing deletes the local branch.
- Byte budgets: `KNOWN_OVER_BUDGET["commands/ship.md"] = 9110`, `["commands/implement-phase.md"] = 1464`.

## Change

### Story 1: integrate deletes the lane branch

1. In `cmd_integrate`, after the worktree removal:

```python
deleted = _git(repo, "branch", "-d", lane_branch, check=False)
record["laneBranchDeleted"] = deleted.returncode == 0
if deleted.returncode != 0:
    record["laneBranchKeptReason"] = (deleted.stderr or deleted.stdout).strip()
```

   Return `laneBranchDeleted` in the result dict. Status stays `integrated` either way (Business Rule 6).
2. No change to `cmd_reconcile`; add a test that an integrated spec with no lane branch reconciles `consistent` (Business Rule 7).
3. `scripts/eval-phase-lane.py`: add `lane-branch-deleted-after-merge` (branch gone, `laneBranchDeleted` true) after `worktree-removed-after-merge`; the failed and malformed cases also assert the lane branch still exists.
4. `.writ/docs/phase-execution-state-format.md`: `laneBranch` row reads "The lane branch `writ/phase/{phase}/{spec}`; deleted after a successful merge, kept on quarantine (renamed) and closure"; add `laneBranchDeleted` and `laneBranchKeptReason` rows.
5. `commands/implement-phase.md` Step 3.2 item 4: "the worktree is then removed and the merge commit recorded" → "the worktree and lane branch are then removed and the merge commit recorded". Offset any growth in the same file or disclose it.

### Story 2: `/ship` deletes the landed local branch

1. New `scripts/ship-branch-cleanup.py`, subcommand `delete`:

| Order | Check | Outcome |
|---|---|---|
| 1 | `git config --bool writ.deleteMergedBranches` is `false` | `skipped`, reason `opted_out` |
| 2 | branch equals `--default`, or does not exist locally | `skipped`, reason `default_branch` / `no_branch` |
| 3 | `git worktree list --porcelain` shows the branch in a worktree other than `--repo` | `kept`, reason `checked_out_elsewhere:<path>` |
| 4 | `git fetch origin <default>` | failure → `kept`, reason `fetch_failed` |
| 5 | `git branch --merged origin/<default>` lists it | method `-d` |
| 6 | else `--pr-state MERGED` and `git rev-parse <branch>` equals `--pr-head` | method `-D` |
| 7 | else | `kept`, reason `not_merged` (or `local_commits_not_in_pr` when `--pr-head` was given and differs) |
| 8 | branch is checked out here and `git status --porcelain` non-empty | `kept`, reason `dirty_tree` |
| 9 | branch is checked out here | `git checkout <default>` then `git pull --ff-only`; failure → `kept`, reason `switch_failed` |
| 10 | `git branch <method> <branch>` | 0 → `deleted`; else `kept`, reason `delete_failed:<git message>` |

   Output: one JSON line, `schema: ship-branch-cleanup-v1`, fields `status`, `reason`, `method`, `branch`, `default`. Exit 0 for every outcome; exit 2 for a usage error. Never calls `gh`.
2. `scripts/tests/test_ship_branch_cleanup.py`: temp repo with a bare `origin`; cases for each row above, including a squash merge (branch not an ancestor, `--pr-head` equal) and a squash with one extra local commit (kept).
3. `commands/ship.md` new **Step 6b: Branch Cleanup (post-land)** after Step 6: runs whether Step 6 attached a note or was skipped; `python3 scripts/ship-branch-cleanup.py delete --branch <branch> --default <default> --pr-state <state> --pr-head <headRefOid>`; print `🧹 deleted local branch <b> (merged into <d>)` or `🧹 kept <b> — <reason>`; nothing for `skipped`. Non-blocking. In 7.6 merge step item 7, "then Step 6" becomes "then Steps 6 and 6b". Completion output gains the `🧹` line. Keep "Never `--delete-branch`".
4. Register the script per `.writ/docs/agent-cli-contract.md` and in `scripts/tests/test_agent_cli_contract.py`; regenerate `plugins/writ/scripts/` with `python3 scripts/gen-platform-trees.py`.
5. Byte ledger: offset in `ship.md` where no test or eval literal pins the text (`git grep` each trimmed phrase); re-pin `KNOWN_OVER_BUDGET["commands/ship.md"]` only for a residual, with a `# 2026-11-09 (...)` comment.

## Tests

| Test | Where | Asserts |
|---|---|---|
| lane deleted on merge | `eval-phase-lane.py`, pytest | branch gone, `laneBranchDeleted: true` |
| lane kept on failure | `eval-phase-lane.py` | failed, malformed, conflict keep the branch |
| delete refused | pytest | `laneBranchDeleted: false`, reason recorded, status `integrated` |
| reconcile after delete | pytest | `consistent` |
| helper rows 1–10 | `test_ship_branch_cleanup.py` | status, reason, method per row |
| Step 6b text | pytest text pin | Step 6b present, "Never `--delete-branch`" kept |
| byte ledger | `test_governor_enforcement.py`, `test_harness_cuts.py` | green after any re-pin |

## Error & Rescue Map

| Failure | Detected by | Rescue |
|---|---|---|
| `git branch -d` refuses the lane | integrate | branch kept, reason recorded; delete by hand |
| fetch fails | helper row 4 | branch kept; re-run `/ship` |
| dirty tree | helper row 8 | branch kept; commit or stash, re-run |
| branch in another worktree | helper row 3 | branch kept; remove that worktree, re-run |
| local commits not in the PR | helper row 7 | branch kept; push them to a new branch |
| `ff-only` pull fails | helper row 9 | branch kept, checkout left on default |

## Shadow Paths

| Path | Input | Outcome |
|---|---|---|
| Happy path | merge-commit PR, branch checked out, clean | switch, ff, `-d`, `deleted` |
| Nil input | no `--pr-head` | only the `--merged` proof applies |
| Empty input | branch already gone | `skipped`, `no_branch` |
| Upstream error | `git fetch` fails | `kept`, `fetch_failed` |

## Out of scope

Remote branches, `/release`, existing stale branches, quarantine and `close-spec`.
