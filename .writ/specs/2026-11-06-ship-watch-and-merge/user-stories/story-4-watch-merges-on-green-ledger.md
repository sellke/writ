# Story 4: The watch merges on a green ledger

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1, Story 3

## User Story

**As a** developer whose PR `/ship --watch` brought to merge-ready
**I want to** have it merge the PR when `pr-ready.py` passes for the exact head and the doubt check passes, and ask me one question otherwise
**So that** a verified PR lands without a prompt once Jev is calibrated, an unverified or moved head never lands, and release, tag, and publish still wait for me

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.5

- [ ] Given the merge record template in Step 7, when the tests fill it with PR 7, a 40-hex head, and a snapshot path, and run `jev-judge.py doubt` on it with a stub `pr-ready.py` that passes for that PR and head, then with no calibrated threshold it prints `fail` with `reason: fallback_merge`, and with a calibrated fixture threshold and a fake transport above it, it prints `pass` `[AC-4.1]`
- [ ] Given the merge step, when the tests read it, then it saves `pre_merge_base` to the watch file before the doubt check, runs `scripts/jev-judge.py doubt --record .writ/state/ship/merge-record-pr-<n>.json`, merges with `gh pr merge <n> --match-head-commit <head>` and a method taken from `Merge Strategy` (otherwise `merge`), contains none of `--delete-branch`, `--admin`, or `--auto`, reads the state back with `gh pr view <n> --json state,mergeCommit`, and runs Step 6 in the same pass when the state is `MERGED` `[AC-4.2]`
- [ ] Given a doubt `fail`, when the tests read the ask path, then it asks "Merge PR #<n> now?" with "Merge now (Recommended)" and "Leave it at merge-ready", labels the answer with `scripts/jev-judge.py doubt-label`, and a "Merge now" answer runs the same `--match-head-commit` command; a refusal because the head moved reports `waiting`, any other refusal or a non-`MERGED` state reports `asked` `[AC-4.3]`
- [ ] Given the new frontmatter, Overview, and Completion, when `test_harness_cuts.py` runs, then it pins the new `description` and four `exit_criteria` from technical-spec § Story 4, keeps `problem` and `outcome` unchanged, requires the description and Overview to name `--watch` as the only path that merges, and still forbids "merged pr", "branch to merged", and "gets it merged" `[AC-4.4]`
- [ ] Given `commands/ship.md` after this story, when the tests scan it, then it contains no `gh release`, `git tag`, or `npm publish` step, the Completion section says it never requests reviewers, releases, tags, or publishes, `KNOWN_OVER_BUDGET["commands/ship.md"]` equals the exact overage with a dated comment line, `gen-platform-trees.py --check` passes, and `bash scripts/eval.sh` exits 0 `[AC-4.5]`

## Implementation Tasks

- [ ] 4.1 Add a Story 4 section to `scripts/tests/test_ship_watch.py` naming `2026-11-06-ship-watch-and-merge`: parse the merge record template out of Step 7, fill it, run it through `jev-judge.py doubt` with the Story 1 stub helper (no threshold, then calibrated with a fake transport); check the merge, read-back, ask, and refusal lines; scan for release, tag, and publish commands. Update `scripts/tests/test_harness_cuts.py`: new `SHIP_KEPT_FRONTMATTER` values for `description` and `exit_criteria`, and an AC-3.3 docstring and assertion that allow the `--watch` merge sentence while keeping `MERGE_CLAIMS`. Run on Python 3.9 and confirm the new tests fail `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`
- [ ] 4.2 Write the merge step in Step 7 from technical-spec § Story 4: save `pre_merge_base`, write the merge record (add the `/review` line when `.writ/state/review-<branch>.md` exists), run the doubt check, merge on `pass`, and read the state back. Replace the Story 3 `pass` row text with "Merge step" `[AC-4.1, AC-4.2]`
- [ ] 4.3 Write the ask path and the refusal handling: the two-option question, `doubt-label` with `as_recommended` or `overridden`, the same merge command on "Merge now", `waiting` for a moved head, `asked` for other refusals or a non-`MERGED` state `[AC-4.3]`
- [ ] 4.4 Change the frontmatter `description` and `exit_criteria` to the exact text in technical-spec § Story 4, add the Overview sentence, rewrite the Completion terminal constraint, replace the "source of truth" block with one sentence, and add the Step 6 sentence that it runs right after a `--watch` merge `[AC-4.4, AC-4.5]`
- [ ] 4.5 Re-pin `KNOWN_OVER_BUDGET["commands/ship.md"]` with a dated line. If the running total against 28,907 bytes is above zero, apply the reserve cuts in technical-spec § Byte Budget first and disclose any residual in the comment. Run `python3 scripts/gen-platform-trees.py` and `--check` `[AC-4.5]`
- [ ] 4.6 Verify. Run `test_ship_watch.py`, `test_harness_cuts.py`, `test_jev_doubt.py`, and `test_governor_enforcement.py` on Python 3.9 and 3.14, the full suite on both, each run alone, then `bash scripts/eval.sh`, then the bash suite in the background. Check each AC against the test carrying its tag `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`

## Notes

- **The merge asks today.** No doubt threshold is calibrated, so every real merge reaches the ask path. AC-4.1's `pass` case uses a fixture threshold in a temp repo, never a real PR.
- **No real PR in any lane.** Opening or merging a PR is outward-facing. The real-PR run is a human UAT scenario (spec.md → Human UAT).
- **`--match-head-commit` is the remote binding.** The doubt check proves the local snapshot and ledger agree. GitHub refuses the merge if the head moved after the snapshot.
- **Method.** `Merge Strategy` documents base integration, but the example config sets `squash`. Use its value when it is `merge`, `squash`, or `rebase`; otherwise `merge` (B-OQ2). Never delete the branch; the repo's auto-delete setting governs.
- **Restore point.** `pre_merge_base` is the restore path the reversibility precondition needs, saved before the merge.
- **Step 6 pins.** Add one sentence; do not move or reword the pinned literals.
- **AC-3.3 in `test_harness_cuts.py`.** That test was written when `/ship` never merged. Update its docstring to cite ADR-033 point 5 and keep its `MERGE_CLAIMS` check. Do not reword `ship.md` to slip past it.
- **Byte total.** This story closes the budget. Aim for net ≤ 0 against 28,907 bytes; the cap is not a gate (ADR-023), so a residual is disclosed in the dated comment.
- **Bash suite.** About 12 minutes; start it in the background and wait for it (`CLAUDE.md`).

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Doubt check, `gh pr merge` (head moved), `gh pr merge` (other refusal), Read back, Step 6 audit note] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [Merge] — technical-spec.md → ## Shadow Paths
- **Business rules:** [Merge (record path, restore point, method, ask question), Business Rule 2 (snapshot, doubt pass, and `--match-head-commit` in one pass), Business Rule 3 (no threshold → ask), What stays a person's call] — spec.md → ## Business Rules (Expanded) → ### Merge, ### What stays a person's call; spec.md → ## Specification Contract → 📋 Business Rules
- **Experience:** [Moment of truth (`ship-watch: merged ... doubt act (id ...)`), State Catalog (`merged`, `asked`), Journey step 3 (Land)] — spec.md → ## Specification Contract → 🎯 Experience Design; spec.md → ## Experience Design → ### State Catalog, ### Journey
