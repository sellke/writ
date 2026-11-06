# Story 2: `/ship` opens the PR without asking and records the ledger

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** developer running `/ship` or `/ship --test` on a green branch
**I want to** reach an open PR without answering questions the evidence already settles, and leave a ledger row for the pushed head when tests ran
**So that** opening a PR costs me nothing, and a later `/ship --watch` can tell whether this exact head was verified

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [ ] Given `commands/ship.md` after this story, when the Story 2 tests read it, then no `AskQuestion(` block appears before `### Step 5`, the "Override?" prompt, the "Save to `.writ/config.md`?" offer, the ASCII pipeline diagram, the duplicate "`--dry-run` output for Steps 4-5" block, and the non-extraction note are gone, and Step 1 prints the `.writ/config.md` lines that would skip detection instead of writing them `[AC-2.1]`
- [ ] Given Step 3's failure options, Step 4's commit plan, and the Error Handling choices for branch creation and uncommitted changes, when the tests read them, then each names its decision record (site, options, recommended option) and `scripts/jev-judge.py doubt --record`, says that an asked answer is labeled with `doubt-label`, and the untracked-files case carries no recommendation `[AC-2.2]`
- [ ] Given Step 4, when the tests read it, then it saves `presplit_sha` before the decision and sets `reversible` true only when the branch has no upstream or `git log origin/<branch>..HEAD` lists every commit the plan restructures; otherwise the record is not reversible and the run asks `[AC-2.3]`
- [ ] Given a temp git repo with a clean checked-out head and a saved evidence entry whose exits are all 0 and whose tree equals `HEAD^{tree}`, when the Step 5 `record` command from `ship.md` is filled with that repo's values and run, then `verify-ledger.py check` for that PR and head prints `pass`; and `ship.md` says Step 3 runs the Test Runner and then the `Eval Command` and saves commands, exits, HEAD, and tree to `.writ/state/ship/branch-<slug>.json`, not to record when any exit is non-zero, and to re-run the commands first when the trees differ `[AC-2.4]`
- [ ] Given the Story 2 changes, when the checks run, then `config-format.md` has an `Eval Command` row and example line, the `verify-ledger.py` Callers cell reads `commands/ship.md`, `eval-command-structure.py` has passing `invocation` rows for `scripts/verify-ledger.py record --pr` and `scripts/jev-judge.py doubt --record`, `KNOWN_OVER_BUDGET["commands/ship.md"]` equals the exact overage with a dated comment line, `ship.md` stays above 24,960 bytes, and `gen-platform-trees.py --check` passes `[AC-2.5]`

## Implementation Tasks

- [ ] 2.1 Create `scripts/tests/test_ship_watch.py` with a module docstring naming `2026-11-06-ship-watch-and-merge` and a Story 2 section: text tests for AC-2.1 to AC-2.3, a filled-command test for AC-2.4 (temp git repo, real `scripts/verify-ledger.py`, the `record` line parsed out of Step 5), and checks for the `config-format.md` row and the Callers cell. Run on Python 3.9 and confirm they fail `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
- [ ] 2.2 Make the cuts in technical-spec § Byte Budget, Story 2 row: the PR-agent paragraph, the ASCII pipeline (replace with the one-line flow), "Detection chain details", "Opinionated defaults", the duplicate dry-run block, and the non-extraction note. Measure with `wc -c` after each cut `[AC-2.1, AC-2.5]`
- [ ] 2.3 Rewrite Step 1 and Error Handling per technical-spec § Story 2 table: print detected values and the config lines; route an undetectable needed convention, branch creation, and uncommitted changes through decision records and the Doubt Rule; keep the hard stops `[AC-2.1, AC-2.2]`
- [ ] 2.4 Rewrite Step 3 (Test Runner, then `Eval Command`; save commands, exits, HEAD, and tree to `.writ/state/ship/branch-<slug>.json`; failure options as a `site: choice` record) and Step 4 (save `presplit_sha`; `site: plan` record with the reversibility rule; drop the `AskQuestion` block and the approval sentence). Add the `Eval Command` row and example line to `.writ/docs/config-format.md` `[AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
- [ ] 2.5 Add the Step 5 ledger recording after `gh pr create`: tree check, re-run when trees differ, no record on a non-zero exit, the `verify-ledger.py record` line, and the `verify-ledger:` line in the completion output. Set the `verify-ledger.py` Callers cell to `commands/ship.md`. Add the two `invocation` rows to `scripts/eval-command-structure.py` `ROWS` with `was = "check_command_structure"` `[AC-2.4, AC-2.5]`
- [ ] 2.6 Re-pin `KNOWN_OVER_BUDGET["commands/ship.md"]` to `wc -c < commands/ship.md` minus 24960, appending one dated line in the format of technical-spec § Byte Budget directly above the entry. Confirm the file is above 24,960 bytes. Run `python3 scripts/gen-platform-trees.py`, then `--check` `[AC-2.5]`
- [ ] 2.7 Verify. Run `test_ship_watch.py`, `test_governor_enforcement.py`, `test_harness_cuts.py`, and `test_eval_command_structure.py` on Python 3.9 and 3.14, then the full suite on both, each run alone, then `bash scripts/eval.sh`. Check each AC against the test carrying its tag `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`

## Notes

- **`--watch` is not mentioned yet.** Story 3 adds the flag and "implies `--test`". This story covers `/ship` and `/ship --test` only, so every sentence it adds describes behavior that exists when it lands.
- **Byte floor.** The Story 2 net target is −2,500 to −3,900 bytes. Below 24,960 bytes the `KNOWN_OVER_BUDGET` entry and `test_harness_cuts.py`'s `recorded[SHIP]` lookup break. If the cuts would cross the floor, leave the rest for Story 4.
- **Ledger comment block.** Append the dated line inside the contiguous comment block above `"commands/ship.md"`. `test_ac_3_4_each_lowered_entry_has_a_dated_ledger_line` needs the existing `2026-10-20 (2026-10-20-harness-cuts Story 3): 4030 -> 4023;` line to stay in that block.
- **Pinned frontmatter.** `test_harness_cuts.py` pins `problem`, `outcome`, and `exit_criteria`, and forbids merge claims in the description and Overview. This story changes none of them.
- **Step 6 pins.** Leave Step 6 alone; `eval.sh` and `eval-git-notes-audit.py` pin its literals.
- **`record` refuses failing evidence.** It also refuses when `--head` is not the checked-out HEAD or a tracked file is modified, and writes nothing. `/ship` reports the refusal and does not retry.
- **Config persistence.** Writing `.writ/config.md` during `/ship` would leave an uncommitted file outside the PR. Printing the lines removes the question; it is not a decision (`_preamble.md` → Stakes triage).
- **Test isolation.** The filled-command test runs in a temp repo with `GIT_CONFIG_GLOBAL=/dev/null` and never writes under the Writ checkout's `.writ/state/`.
- **Vendor scan.** Name no vendor tool in `ship.md`. Use `AskQuestion` for asks.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Evidence run, `verify-ledger.py record`, Doubt check] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [Open path] — technical-spec.md → ## Shadow Paths
- **Business rules:** [Open path (Steps 1–5), Ledger recording, Business Rule 9 (record only a head whose tree matches the tested tree), Business Rule 12 (opening the PR asks nothing)] — spec.md → ## Business Rules (Expanded) → ### Open path (Steps 1–5), ### Ledger recording; spec.md → ## Specification Contract → 📋 Business Rules
- **Experience:** [Journey step 1 (Open), Interaction patterns (one bounded question with a recommended option, labeled afterward)] — spec.md → ## Experience Design → ### Journey, ### Interaction patterns
