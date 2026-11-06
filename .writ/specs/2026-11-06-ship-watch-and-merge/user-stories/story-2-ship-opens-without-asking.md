# Story 2: `/ship` opens the PR without asking and records the ledger

> **Status:** Completed ✅ (2026-11-06)
> **Commit:** 02a2fb23366e8badfbe512060a2d592a3998127c
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** developer running `/ship` or `/ship --test` on a green branch
**I want to** reach an open PR without answering questions the evidence already settles, and leave a ledger row for the pushed head when tests ran
**So that** opening a PR costs me nothing, and a later `/ship --watch` can tell whether this exact head was verified

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [x] Given `commands/ship.md` after this story, when the Story 2 tests read it, then no `AskQuestion(` block appears before `### Step 5`, the "Override?" prompt, the "Save to `.writ/config.md`?" offer, the ASCII pipeline diagram, the duplicate "`--dry-run` output for Steps 4-5" block, and the non-extraction note are gone, and Step 1 prints the `.writ/config.md` lines that would skip detection instead of writing them `[AC-2.1]`
- [x] Given Step 3's failure options, Step 4's commit plan, and the Error Handling choices for branch creation and uncommitted changes, when the tests read them, then each names its decision record (site, options, recommended option) and `scripts/jev-judge.py doubt --record`, says that an asked answer is labeled with `doubt-label`, and the untracked-files case carries no recommendation `[AC-2.2]`
- [x] Given Step 4, when the tests read it, then it saves `presplit_sha` before the decision and sets `reversible` true only when the branch has no upstream or `git log origin/<branch>..HEAD` lists every commit the plan restructures; otherwise the record is not reversible and the run asks `[AC-2.3]`
- [x] Given a temp git repo with a clean checked-out head and a saved evidence entry whose exits are all 0 and whose tree equals `HEAD^{tree}`, when the Step 5 `record` command from `ship.md` is filled with that repo's values and run, then `verify-ledger.py check` for that PR and head prints `pass`; and `ship.md` says Step 3 runs the Test Runner and then the `Eval Command` and saves commands, exits, HEAD, and tree to `.writ/state/ship/branch-<slug>.json`, not to record when any exit is non-zero, and to re-run the commands first when the trees differ `[AC-2.4]`
- [x] Given the Story 2 changes, when the checks run, then `config-format.md` has an `Eval Command` row and example line, the `verify-ledger.py` Callers cell reads `commands/ship.md`, `eval-command-structure.py` has passing `invocation` rows for `scripts/verify-ledger.py record --pr` and `scripts/jev-judge.py doubt --record`, `KNOWN_OVER_BUDGET["commands/ship.md"]` equals the exact overage with a dated comment line, `ship.md` stays above 24,960 bytes, and `gen-platform-trees.py --check` passes `[AC-2.5]`

## Implementation Tasks

- [x] 2.1 Create `scripts/tests/test_ship_watch.py` with a module docstring naming `2026-11-06-ship-watch-and-merge` and a Story 2 section: text tests for AC-2.1 to AC-2.3, a filled-command test for AC-2.4 (temp git repo, real `scripts/verify-ledger.py`, the `record` line parsed out of Step 5), and checks for the `config-format.md` row and the Callers cell. Run on Python 3.9 and confirm they fail `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
- [x] 2.2 Make the cuts in technical-spec § Byte Budget, Story 2 row: the PR-agent paragraph, the ASCII pipeline (replace with the one-line flow), "Detection chain details", "Opinionated defaults", the duplicate dry-run block, and the non-extraction note. Measure with `wc -c` after each cut `[AC-2.1, AC-2.5]`
- [x] 2.3 Rewrite Step 1 and Error Handling per technical-spec § Story 2 table: print detected values and the config lines; route an undetectable needed convention, branch creation, and uncommitted changes through decision records and the Doubt Rule; keep the hard stops `[AC-2.1, AC-2.2]`
- [x] 2.4 Rewrite Step 3 (Test Runner, then `Eval Command`; save commands, exits, HEAD, and tree to `.writ/state/ship/branch-<slug>.json`; failure options as a `site: choice` record) and Step 4 (save `presplit_sha`; `site: plan` record with the reversibility rule; drop the `AskQuestion` block and the approval sentence). Add the `Eval Command` row and example line to `.writ/docs/config-format.md` `[AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
- [x] 2.5 Add the Step 5 ledger recording after `gh pr create`: tree check, re-run when trees differ, no record on a non-zero exit, the `verify-ledger.py record` line, and the `verify-ledger:` line in the completion output. Set the `verify-ledger.py` Callers cell to `commands/ship.md`. Add the two `invocation` rows to `scripts/eval-command-structure.py` `ROWS` with `was = "check_command_structure"` `[AC-2.4, AC-2.5]`
- [x] 2.6 Re-pin `KNOWN_OVER_BUDGET["commands/ship.md"]` to `wc -c < commands/ship.md` minus 24960, appending one dated line in the format of technical-spec § Byte Budget directly above the entry. Confirm the file is above 24,960 bytes. Run `python3 scripts/gen-platform-trees.py`, then `--check` `[AC-2.5]`
- [x] 2.7 Verify. Run `test_ship_watch.py`, `test_governor_enforcement.py`, `test_harness_cuts.py`, and `test_eval_command_structure.py` on Python 3.9 and 3.14, then the full suite on both, each run alone, then `bash scripts/eval.sh`. Check each AC against the test carrying its tag `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`

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

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Evidence run, `verify-ledger.py record`, Doubt check] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [Open path] — technical-spec.md → ## Shadow Paths
- **Business rules:** [Open path (Steps 1–5), Ledger recording, Business Rule 9 (record only a head whose tree matches the tested tree), Business Rule 12 (opening the PR asks nothing)] — spec.md → ## Business Rules (Expanded) → ### Open path (Steps 1–5), ### Ledger recording; spec.md → ## Specification Contract → 📋 Business Rules
- **Experience:** [Journey step 1 (Open), Interaction patterns (one bounded question with a recommended option, labeled afterward)] — spec.md → ## Experience Design → ### Journey, ### Interaction patterns

## What Was Built

**Implementation Date:** 2026-11-06

### Files Created

1. **`scripts/tests/test_ship_watch.py`** (Story 2 section) — prose pins over `commands/ship.md` for AC-2.1 to AC-2.3 and AC-2.5, and two filled-command tests: the Step 5 `record` line, filled with a temp git repo's values, writes a row the real `verify-ledger.py check` reads VERIFIED, and with a failing exit writes nothing.

### Files Modified

1. **`commands/ship.md`** (25,381 bytes, from 28,907)
   - Pipeline: the ASCII diagram is one flow line.
   - New `### Decisions` subsection: the record fields, `python3 scripts/jev-judge.py doubt --record .writ/state/ship/decision-<name>.json`, `doubt-label` after an ask, temp-file writes under `.writ/state/ship/`, "Opening the PR asks nothing."
   - Step 1: one detection table (the detection-chain details folded in, including the run commands), the "Override?" prompt and the "Save to `.writ/config.md`?" offer gone; it prints the detected values and the config lines and writes nothing. An undetectable default branch, or Test Runner with `--test`, is a decision with no recommendation, so it asks.
   - Step 3: Test Runner, then `Eval Command`; each command, exit, `HEAD`, and `HEAD^{tree}` saved to `.writ/state/ship/branch-<slug>.json`; the failure options are a `site: choice` decision (`decision-tests.json`); "Ship as a draft" sets `draft_reason: "tests_failed"`.
   - Step 4: `presplit_sha` saved first; a `site: plan` decision (`decision-plan.json`) that is reversible only with no upstream or every restructured commit unpushed; the `AskQuestion` block, the approval sentence, and the non-extraction note gone.
   - Step 5: after `gh pr create`, `verify-ledger.py record` for the pushed head when every exit is 0 and the trees match; re-run first when the trees differ; never a non-zero exit; the `verify-ledger:` completion line.
   - Error Handling: branch creation and uncommitted changes are `site: choice` decisions; untracked files carry no recommendation; the combined case runs both in order.
   - The duplicate "`--dry-run` output for Steps 4-5" block is gone.
2. **`.writ/docs/config-format.md`** — `Eval Command` row and example line.
3. **`.writ/docs/agent-cli-contract.md`** — `verify-ledger.py` Callers cell: `commands/ship.md`.
4. **`scripts/eval-command-structure.py`** — two `invocation` rows on `commands/ship.md`: `scripts/verify-ledger.py record --pr`, `scripts/jev-judge.py doubt --record`.
5. **`scripts/tests/test_governor_enforcement.py`** — `KNOWN_OVER_BUDGET["commands/ship.md"]` 3947 → 421 with a dated line.
6. **Generated copies** — `plugins/writ/commands/ship.md`, `cursor/plugin/commands/ship.md` by `python3 scripts/gen-platform-trees.py`.
7. **`.writ/specs/2026-11-06-ship-watch-and-merge/drift-log.md`**, **`spec-lite.md`** — DEV-002, DEV-003 and their amendments.

### Implementation Decisions

1. **No coding subagent.** No `coding-agent` type is registered in this harness; the lane wrote the change itself, tests first (27 new tests failed before `ship.md` changed). Gate 3 ran as a spawned read-only `review-agent`.
2. **The PR-agent paragraph stays until Story 4** (DEV-002): with it cut the file measured 24,767 bytes, under the 24,960 floor.
3. **Review recommendations applied after the PASS:** `evidence` is a list of strings and the `id` is on `doubt`'s last line; Step 1's no-recommendation decisions name their options; "Fix and retry" commits the fix before re-running; Step 4 item 4 runs only on "Split as planned"; the `record` command is single-quoted for the shell; the completion line names the not-recorded case; the Draft vs. Ready row no longer names the retired "Ship anyway" option.

### Test Results

**Verification:** `uv run --isolated --python 3.9 --with pytest pytest -q` on `test_ship_watch.py`, `test_governor_enforcement.py`, `test_harness_cuts.py`, `test_eval_command_structure.py`, `test_agent_cli_contract.py`, `test_agent_cli_contract_doc.py`, `test_gen_platform_trees.py`, `test_plugin_distribution.py`, `test_platform_neutral_names.py`, `test_eval_shipped_refs.py`, `test_eval_size_pins.py`, `test_jev_doubt.py`: 878 passed; 3.14: 878 passed. After the review fixes: the first five files, 269 passed on 3.9 and 3.14. `gen-platform-trees.py --check`: pass. `bash scripts/eval.sh --report=<scratch>`: exit 0. Full pytest and the bash suite run once at spec close-out. Gate scripts: arch-check pass; boundary-map crossings pass, 3 crossings, route review-agent; change-surface cross-component; review-override check pass; safety-fact pass (measured tested); evidence-gate not run (PASS); drift-format pass; test-integrity authenticity pass, coverage not applicable (no new source file); app-verify unverifiable (no_recipe); docs-check unverifiable (no public exports).
**Coverage:** no new source file; the filled-command tests run the real `verify-ledger.py`.
- ✅ AC-2.1 to AC-2.5 each carry tagged tests in `test_ship_watch.py`.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small
- **Security:** Clean
- **Boundary Compliance:** All changes are owned or generated; the one unlisted file is the `verify-ledger.py` Callers cell that Reconciliation 8 assigns to this story.
- `reviewer-filters: on` · `evidence-gate: not run (PASS)` · `safety-fact: tested (claimed tested)` · `gate3-route: review-agent (boundary-map crossings)` · `arch-lint: none — see .writ/docs/architecture-lint.md`

### Deviations from Spec

- **[DEV-002] The PR-agent Overview paragraph cut moves to Story 4** — Severity: Small
  - Spec said: cut it in Story 2. Reality: kept until Story 4 by the byte floor. Resolution: Auto-amended spec-lite.md
- **[DEV-003] The Doubt Rule call is stated once, in a `### Decisions` subsection** — Severity: Small
  - Spec said: each decision names `doubt --record` and `doubt-label`. Reality: each names its record file, site, options, and recommendation; the calls are stated once. Resolution: Auto-amended spec-lite.md

### Review Outcome — close-out repair `b3d8d16`

**Result:** PASS

- **What it covers:** commit `b3d8d16` changes the `CALLERS` constant in `scripts/tests/test_verify_ledger.py` to the `verify-ledger.py` Callers cell this story filled (DEV-011). The full pytest run at spec close-out had failed that pin.
- **Verdict source:** a spawned read-only `evaluator-agent`, run as `--review-only` on `b3d8d16` (implement-spec Step 4.1, "Fix in place"): the contract test still checks row shape, position, Notes, and smoke entry with only the Callers value changed; neither script changed; `ac-trace.py check` reports no findings for either Phase 16 spec; `pytest -q` on the two contract test files, 67 passed (Python 3.9).
- **Iteration count:** 1 iteration(s)
- **Drift:** Small (DEV-011)
