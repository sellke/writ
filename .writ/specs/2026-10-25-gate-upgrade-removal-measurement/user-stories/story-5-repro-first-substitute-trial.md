# Story 5: Run the Repro First Substitute Trial

> **Status:** Completed ✅ (2026-11-09)
> **Priority:** Medium
> **Dependencies:** Story 3 (harness exists); Story 4's report commit `ef0c418`

## User Story

**As a** Writ maintainer
**I want to** run the Repro First arm on a substitute baseline of three bug-fix stories (DEV-014) and hand its findings to labeling
**So that** Repro First gets a measured keep or remove verdict, since the Phase 11 baseline has no bug-fix story to exercise it (drift-log DEV-013)

## Acceptance Criteria

> **AC IDs assigned through:** AC-5.5

- [x] Given the harness and a trial created with `init --upgrades repro-first`, when `record` receives an arm other than `off-1`, `off-2`, or `repro-first`, then `record` exits 2 with `arm_not_applicable` and leaves the file unchanged, and the trial file records `repro-first` as its only scoped upgrade `[AC-5.1]`
- [x] Given a scoped trial, when `report` runs, then it prints `upgrade:` lines for `repro-first` only and its summary counts only that upgrade; given an unscoped trial, when `init`, `record`, `sheet`, and `report` run, then their output and file bytes match the pre-change harness and `report` prints four `upgrade:` lines `[AC-5.2]`
- [x] Given `.writ/eval/baselines/2026-11-09-repro-first-substitute.json`, when `init --baseline` reads it, then `selection` holds the three admitted entries (DEV-014), each with `story_id`, `story_path`, `spec_folder`, `story_commit`, and `parent_sha` as full 40-hex SHAs; `selection_rule` echoes Business Rule 14's rule, including the clause that the story file and spec contract exist at the fix commit; each entry has one `fix_commit_note`; a scoped trial accepts 1 to 4 stories while an unscoped one still requires exactly 4; and no field holds yuss source, diff, story, or commit-subject text `[AC-5.3]`
- [x] Given the substitute trial file, when each story's arms run, then `off-1`, `off-2`, and `repro-first` recognition are recorded for every story; a bug-fix repro also records `--repro-ac`, `--at-parent`, and `--at-commit`; and a repro arm that cannot run at `parent/` stays unrecorded and is reported missing with its reason `[AC-5.4]`
- [x] Given every applicable arm is recorded or reported missing, when `sheet` and `report` run, then `labeling-sheet-repro-first.md` and `rating-handoff-repro-first.md` exist; `report` prints `unverifiable` with `reason: unlabeled` when upgrade-only findings exist, or a final `repro-first` verdict when none exist; `labeled_by` is null; the trial file records yuss `unchanged: true`; and spec.md's status line matches the finding count `[AC-5.5]`

## Implementation Tasks

- [x] 5.1 Write unit tests in `scripts/tests/test_gate_upgrade_trial.py` first: scoped `init`, the `arm_not_applicable` refusal, scoped `report` lines, and unscoped output unchanged `[AC-5.1, AC-5.2]`
- [x] 5.2 Add `--upgrades` (comma list, default all four) to `init` in `.writ/eval/gate-upgrade-trial/gate-upgrade-trial.py`. Scope `record` and `report` to the trial's scoped upgrades. A scoped trial takes 1 to 4 stories; an unscoped one still takes exactly 4 (DEV-014) `[AC-5.1, AC-5.2]`
- [x] 5.3 Write `.writ/eval/baselines/2026-11-09-repro-first-substitute.json`: three identity-only `selection` entries (DEV-014), a `selection_rule` block, and one `fix_commit_note` per story. Field list in AC-5.3 `[AC-5.3]`
- [x] 5.4 Run `init --baseline` on that file with `--upgrades repro-first`, `--yuss`, and `--out .writ/eval/gate-upgrade-trial/2026-11-09-repro-first-substitute-trial.json`. Then run `prepare` for each story `[AC-5.4, AC-5.5]`
- [x] 5.5 Spawn and `record` per story: `off-1`, `off-2`, and `repro-first` recognition. Run a full repro arm on each bug-fix story, recording `--kind`, `--repro-ac`, `--at-parent`, and `--at-commit`. Report any arm that cannot run `[AC-5.4]`
- [x] 5.6 Run `snapshot` against yuss. Run `sheet --out .writ/eval/gate-upgrade-trial/labeling-sheet-repro-first.md`. Write `rating-handoff-repro-first.md` in the spec folder, confirm `report`, and set the spec.md status line `[AC-5.5]`
- [x] 5.7 Verify: run the harness unit tests on Python 3.9 and 3.14, confirm yuss is unchanged, confirm the first trial's JSON and `labeling-sheet.md` are byte-identical, and grep committed files for yuss text `[AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5]`

## Notes

- **Placeholder SHAs.** The baseline's full SHAs are not resolved in this file. The implementing task resolves them from the four short SHAs in the brief (`ed15bba`, `73f34d4`, `d0f5f1a`, `403a9cc`) using read-only `rev-parse`.
- **Expected result: remove.** A fix commit normally passes its own bug repro at the story commit. A catch needs the repro to fail at the parent and still fail at the story commit (spec.md Business Rule 5), which is unlikely. The likely outcome is exercised 4/4 with zero catches, which is a `remove`. Do not read zero catches as a pass.
- **Explain each zero.** `--at-parent pass` is stored as `no_repro`, which is different from a repro that fails at the parent and passes at the story commit. The handoff lists each story's `Kind`, parent result, and commit result so the reader can tell them apart.
- **Acknowledgment.** If no story is recognized as a bug fix, exercised is 0/4. The sheet then needs `ack: remove|amend` (Business Rule 7), and the verdict is not final until Story 6 fills it.
- **Missing arm.** If a repro arm cannot run at `parent/` (dependency install or test command fails), record nothing for it. `report` then returns `missing_arm`, not `unlabeled`. Keep the contract's status wording and name the missing arm and reason in the handoff. The contract's two status lines do not cover this case; Story 6 should decide the wording.
- **Repro procedure.** The repro arm spawns in `parent/`, never in `checkout/`. The story-commit run applies the repro commit's test files to `checkout/`. Follow technical-spec.md → Arms (repro-first row). `Targets:` and `Repro: none: <reason>` come from `prompts/repro-stop.md` (drift-log.md DEV-009).
- **Probe first.** `init` probes repro-first (`scripts/repro-order.py` present). If it reads `present: false`, stop before `prepare`. The switch and its files must be in the primary checkout.
- **Substitute scope.** Rule 2 of the selection rule is a hand match, so the three stories are a sample, not a random draw. The small-sample and proxy caveats from spec.md still apply.
- **Resolving identity fields.** Resolve full SHAs with read-only `git -C /Users/asellke/Projects/yuss rev-parse --verify <sha>^{commit}`. `parent_sha` is `<commit>^1`. `story_path` may sit under `.writ/specs/archive/`, so check with `ls`. Do not write any yuss ref or object.
- **Yuss.** Use only `rev-parse`, `show-ref`, `status --porcelain`, and the fetch into a fresh repo under `$TMPDIR` that `prepare` performs. Make no write to `/Users/asellke/Projects/yuss`.
- **Raw outputs.** Raw outputs go to `.writ/state/gate-upgrade-trial/` (gitignored), resolved through `git rev-parse --git-common-dir`. They hold yuss text. Never copy them into committed files.
- **Files this story does not touch.** `trial-report.md`, `2026-10-29-gate-upgrade-trial.json`, `labeling-sheet.md`, the roadmap, and ADR-030. The outcome test reads only `trial-report.md`, so do not point `report` output at that path.
- **Harness stays.** Do not delete the harness. Story 4 task 4.6 stays held until this trial has a verdict (drift-log.md DEV-013).
- **Stale spec text.** spec.md Business Rule 1 still reads "No substitute baseline." This story does not edit it. `/edit-spec` owns that amendment.
- **Labeling.** The maintainer delegated labeling for this run on 2026-11-09. Labeling happens in Story 6, not here. This story never fills the sheet and never runs `label`.
- **Story 6 consumes:** the substitute trial JSON, `labeling-sheet-repro-first.md`, and `rating-handoff-repro-first.md`.
- **Spend.** Up to 12 arm spawns for `off-1`, `off-2`, and recognition (3 per story), up to 4 full repro runs, and one re-spawn per failed spawn.
- **Verification commands.** `uv run --isolated --python 3.9 --with pytest pytest scripts/tests/test_gate_upgrade_trial.py`, and the same with `--python 3.14`. Run pytest alone, not beside `eval.sh` or other writes under `.writ/state/`.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [record (arm not applicable to the story), Spawn (any arm), Repro arm, sheet (an applicable arm missing)] — from technical-spec.md → Error & Rescue Map
- **Shadow paths:** [Trial run (all arms recorded; yuss unreachable), Trial run (zero upgrade-only findings), Report (no labels gives unverifiable)] — from technical-spec.md → Shadow Paths
- **Business rules:** [Baseline (Rule 1, amendment), yuss isolation (Rule 2), Arms (Rule 3), Exercise (Rule 4), Upgrade-only (Rule 5), Acknowledgments (Rule 7), Verdict (Rule 8), Human gate (Rule 9)] — from spec.md → Business Rules (Expanded)
- **Experience:** [Error experience (missing arm or unlabeled finding makes the upgrade unverifiable with a named reason)] — from spec.md → Experience Design
- **Technical:** technical-spec.md → Upgrades Under Test (repro-first row), Arms (repro-first row), Arm Evidence (repro-first row), Harness subcommands table, Verdict steps 2–6. drift-log.md → DEV-004 (`snapshot`), DEV-009 (`Targets:` field)

## What Was Built

**Implementation Date:** 2026-11-09

### Files Created

1. **`.writ/eval/baselines/2026-11-09-repro-first-substitute.json`** (53 lines)
   - Three identity-only entries (`ed15bba`, `d0f5f1a`, `403a9cc`, full SHAs), a five-clause `selection_rule`, one `fix_commit_note` per story, and an `excluded` entry for `73f34d4` (DEV-014).
2. **`scripts/tests/fixtures/gate-upgrade-trial/unscoped-golden.json`** (414 lines)
   - A 30-command transcript captured from the harness at `7c3f001`; pins unscoped behavior byte for byte.
3. **`.writ/eval/gate-upgrade-trial/2026-11-09-repro-first-substitute-trial.json`** (219 lines)
   - The scoped trial: 3 stories, 9 recorded arms, 0 upgrade-only findings, yuss `unchanged: true`, `labeled_by: null`.
4. **`.writ/eval/gate-upgrade-trial/labeling-sheet-repro-first.md`** (11 lines)
   - No findings and no acknowledgments.
5. **`.writ/specs/2026-10-25-gate-upgrade-removal-measurement/rating-handoff-repro-first.md`** (58 lines)
   - Per-story repro results, the Story 6 `label` and `report` commands, and caveats.

### Files Modified

- **`.writ/eval/gate-upgrade-trial/gate-upgrade-trial.py`** (`init`, `prepare`, `record`, `sheet`, `label`, `report`)
  - `init --upgrades` stores a `scope` only when narrower than all four. A scoped trial applies `off-1`, `off-2`, and its scoped arms, takes 1 to 4 stories, and reports over its scope with a `scope:` line.
- **`scripts/tests/test_gate_upgrade_trial.py`** (Story 5 section)
  - Eight test classes for scoped init, record, sheet, report, prepare, story count, the baseline, and unscoped byte-identity.
- **`spec.md`, `spec-lite.md`, `sub-specs/technical-spec.md`, `drift-log.md`** — DEV-014 to DEV-017 and their amendments; spec status `In Progress — Repro First report ready (rating-handoff-repro-first.md)`.

### Implementation Decisions

1. **Trial run by the orchestrator** — Gate 1 wrote the harness change, tests, and baseline; the orchestrator ran `init`, `prepare`, the 9 arm spawns, the repro checks, `record`, `snapshot`, and `sheet`, as in Story 3.
2. **Three stories** — `73f34d4`'s spec was committed after the fix, so `prepare` cannot read it; the maintainer chose three stories (DEV-014).
3. **Legacy AC mapping** — two stories without `AC-N.M` IDs use `AC-1.k` by reading order (DEV-015).
4. **Test environment** — `pnpm install --frozen-lockfile --prefer-offline --ignore-scripts` in each temporary checkout, with `parent/` linked to the same `node_modules`; each fix commit's own tests passed at its story commit first.
5. **Repro applied by cherry-pick** — the cover repro conflicted with the fix commit's own test edit and was resolved as a union (fix tests kept, repro test appended).

### Test Results

**Verification:** orchestrator run `uv run --isolated --python 3.9 --with pytest pytest -q scripts/tests/test_gate_upgrade_trial.py scripts/tests/test_gate_upgrade_trial_outcome.py scripts/tests/test_review_panel.py` → 483 passed; the same on Python 3.14 → 483 passed, 15 subtests passed. Red run before the harness change: 39 failed, 352 passed. First-trial files (`2026-10-29-gate-upgrade-trial.json`, `labeling-sheet.md`, `trial-report.md`) unchanged. No yuss text in the new committed files.
- ✅ test-integrity authenticity: pass
- coverage: unverifiable (coverage_report_absent)

### Trial Run

- **Exercise:** Repro First 3/3 (each repro arm recognized a bug).
- **Repros:** all three failed at the parent and passed at the story commit (`fixed`), so no repro yields a key.
- **Upgrade-only findings:** 0. "Current gates" arms: cover `off-1` FAIL (one Major, unmeasured production `NEXTAUTH_URL`), stretch `off-2` FAIL (Major without evidence, advisory), the other four PASS.
- **Report:** `unverifiable`, `reason: repro-first unlabeled 0`, until Story 6 runs `label` (DEV-016); then `remove`.
- **Spawns:** 9 (6 Gate 3 review arms, 3 repro arms); one model (`claude-opus-5-5`); no spawn failed.
- **yuss:** HEAD, refs, and status identical before and after.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Medium (DEV-014 ⚠️, DEV-017 ⚠️; DEV-015, DEV-016 Small)
- **Security:** Clean
- **Boundary Compliance:** code changes in Owned files; the golden fixture and spec-doc edits outside the map are justified
- **gate3-route:** review-agent (outside_boundary scripts/tests/fixtures/gate-upgrade-trial/unscoped-golden.json)
- **reviewer-filters:** on
- **safety-fact:** tested (claimed tested)
- **evidence-gate:** not run (PASS)
- **jev shadow:** unverifiable (state_too_large) — advisory only
- **arch-lint:** none — see .writ/docs/architecture-lint.md
- **build-smoke:** unverifiable (unsupported_stack)
- **Reviewer advisories not applied:** two test names still say "four" (`test_selection_is_four_identity_entries_with_full_shas`, `test_selection_rule_echoes_the_four_parts`) while asserting three entries and five clauses.
