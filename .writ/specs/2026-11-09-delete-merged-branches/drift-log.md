# Drift Log

> Spec: .writ/specs/2026-11-09-delete-merged-branches/
> Created: 2026-11-09
> ⚠️ Append-only — do not modify existing entries.

---

## Story 2: /ship deletes the landed local branch — Drift Report

> Run: 2026-11-09
> Overall Drift: Small (Medium at review iteration 1, resolved by the person's decision)

### Deviations

#### [DEV-001] Merge step item 7 appends "; then Step 6b"
- **Severity:** Small
- **Spec said:** technical-spec.md Story 2 item 3: in 7.6 merge step item 7, "then Step 6" becomes "then Steps 6 and 6b".
- **Implementation did:** item 7 keeps its wording and appends "; then Step 6b" after "`merged` with the doubt id".
- **Reason:** `scripts/tests/test_ship_watch.py:628` pins the existing clause verbatim; behavior is the same.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → For Coding Agents → Integration Points: item 7 appends "; then Step 6b" (the existing clause is pinned).

#### [DEV-002] Step 6b does not run under `--dry-run`
- **Severity:** Small
- **Spec said:** nothing.
- **Implementation did:** Step 6b states "but not with `--dry-run`".
- **Reason:** the Dry Run rule says a dry run changes no git state; deleting a branch would break it.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → For Coding Agents → Error Handling: Step 6b does not run under `--dry-run`.

#### [DEV-003] `pull --ff-only --no-rebase` and a HEAD check after checkout
- **Severity:** Small
- **Spec said:** technical-spec.md row 9: `git checkout <default>` then `git pull --ff-only`.
- **Implementation did:** confirms HEAD is `refs/heads/<default>` after the checkout and pulls with `--ff-only --no-rebase`; both failures give `switch_failed`. A failing `git status` is read as `dirty_tree`.
- **Reason:** `pull.rebase=true` would otherwise turn the pull into a rebase; a checkout that resolves to a path would read as a switch; a failed status must not read as clean.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → For Coding Agents → Implementation Approach: row 9 confirms HEAD and pulls `--ff-only --no-rebase`; a failed `git status` keeps the branch as `dirty_tree`.

#### [DEV-005] Squash proof on the re-run entry points
- **Severity:** Medium
- **Spec said:** Must Include: the squash or rebase proof (PR `MERGED`, local tip equals `headRefOid`); "`/ship` re-run after a PR merged" is a named entry point. Story 2 Notes: "Step 6b adds no `gh` call."
- **Implementation did:** review iteration 1 found the proof reachable only from the watch pass that merges. After the person chose option (a) on 2026-11-09: plain `/ship` runs `gh pr view --json state,headRefOid,mergeCommit` before Step 2's merge and before "No changes to ship"; `MERGED` → Steps 6 and 6b with `mergeCommit.oid` as the landed SHA, then stop; any other result → Step 2 as before. `--watch` 7.1 reads `number,state,headRefOid,mergeCommit`. The helper still never calls `gh`.
- **Reason:** without the head on the re-run paths, squash-merge repos keep every branch with a wrong reason (`not_merged`), which the contract's Technical Concerns names.
- **Resolution:** Accepted by the person (option a, over limiting the proof to `--watch`).
- **Spec amendment:** none to spec.md; the Must Include already requires it. technical-spec.md § Story 2 item 3 is superseded by this entry for the Step 2 and 7.1 changes.
