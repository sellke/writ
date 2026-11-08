# Story 2: Seed This Repository's Rule-to-Enforcer Table

> **Status:** Completed ✅ (2026-10-29)
> **Commit:** 3f1f5e8d7b11266a1612d9c1417f40f9a414ea80
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** maintainer of the Writ repository
**I want to** a rule-to-enforcer table seeded with rules whose enforcers were proven against real past commits
**So that** `/retro` and `retro-check.py` have a real table to read, and the eval gate passes once Story 3 cites the table path.

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.4

- [x] Given `.writ/retros/rule-enforcers.md` in the Writ repo, when its first heading and first table are read, then the heading is `# Rule-to-Enforcer Table`, the file holds one table, and its header row is `| Rule | Written in | Enforcer | Rung | Proof | Since |` `[AC-2.1]`
- [x] Given at least two table rows whose Enforcer is not `none`, when each row's Proof cell is read, then it has the form `<sha>: fails`, and running that row's enforcer in a materialized copy of `<sha>` (the parent of a fix commit) exits non-zero, while the same enforcer on the fix commit exits 0 `[AC-2.2]`
- [x] Given the table, when its rows are counted, then at least one row has Enforcer `none` with Rung `docs` and Proof `—`, and no row has Enforcer `none` with a Rung other than `docs` `[AC-2.3]`
- [x] Given `scripts/tests/test_retro_fix_ladder.py` and the seeded table, when `python3 scripts/retro-check.py --table .writ/retros/rule-enforcers.md --repo .` runs, then line 1 is `pass`, and the test asserts that the table has at least two rows whose Enforcer is not `none` and at least one row whose Enforcer is `none` `[AC-2.4]`

## Implementation Tasks

- [x] 2.1 Write `scripts/tests/test_retro_fix_ladder.py` first. Add one test that runs `python3 scripts/retro-check.py --table .writ/retros/rule-enforcers.md --repo .` through `subprocess` with an argument list, asserts line 1 is `pass`, and counts enforced and `none` rows. Run it and confirm it fails because the table does not exist yet `[AC-2.4]`
- [x] 2.2 Find fix commits in `git log` where an existing enforcer fails on the parent and passes on the fix. Start with the Python 3.9 `pathlib` fix that `CLAUDE.md` describes, and commits touching `plugins/writ/` or `cursor/plugin/` for `gen-platform-trees.py --check`. For each candidate, materialize the parent with `git worktree add --detach <tmp> <parent-sha>` or `git show <sha>:<path>` into a temp directory, run the enforcer, and record the exit code. Remove any worktree afterwards `[AC-2.2]`
- [x] 2.3 Write `.writ/retros/rule-enforcers.md` with the heading, the header row, one row per qualifying rule (Since `seed`, Proof `<parent-sha>: fails`), and one `none` row with Rung `docs` and Proof `—` `[AC-2.1, AC-2.2, AC-2.3]`
- [x] 2.4 Run the `retro-check.py` command from 2.1 by hand and confirm line 1 is `pass`. Confirm the table has at least two enforced rows and one `none` row `[AC-2.1, AC-2.4]`
- [x] 2.5 Verify each criterion with its exact command: the header and heading by reading the file, each Proof SHA and exit code by re-running the enforcer on the recorded parent, and the row counts by counting rows `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`
- [x] 2.6 Run `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, and `bash scripts/eval.sh` outside any sandbox. Run `git worktree list` and confirm no temp worktree from 2.2 remains `[AC-2.2, AC-2.4]`

## Notes

- **Dependency:** Story 1 ships `scripts/retro-check.py`. The test in 2.1 cannot pass without it.
- **Candidate rules:** `sub-specs/technical-spec.md` → ## Seeded table lists four candidates. Use the two whose enforcer fails on a real parent. The candidates are:
  - The suite runs on Python 3.9, enforced by `uv run --python 3.9 pytest <test>`.
  - Generated trees are never stale, enforced by `python3 scripts/gen-platform-trees.py --check`.
  - Shipped commands link no Writ-internal history, enforced by `python3 scripts/eval-shipped-refs.py`. Its fix commit is `2026-10-20-shipped-command-hygiene` Story 1.
  - Instruction files use plain prose, with enforcer `none` (docs: `skills/plain-prose/SKILL.md`).
- **Stop rule:** Fewer than two qualifying fix commits means the story stops and reports which candidates failed and why. It writes no synthetic fixture and no proof that does not come from a real commit. Spec: `spec.md` → ## Technical Concerns → "Proof needs history".
- **Proof rule:** A proof is a commit in this repository. A synthetic fixture is not a past mistake. Spec: `spec.md` → ## Business Rules (Expanded) → 6 and 8.
- **Why this file comes before Story 3:** `check_referenced_paths` in `scripts/eval.sh` fails any command that backticks a missing `*.md` path. Story 3 makes `commands/retro.md` cite `.writ/retros/rule-enforcers.md`.
- **Location:** The table stays in `.writ/retros/`. It does not go in `.writ/docs/`, which `install.sh` ships. Spec: `spec.md` → ## Business Rules (Expanded) → 10.
- **Materialize, do not checkout:** Use `git worktree add --detach` or `git show`. Do not check out a parent in the working tree. Remove every temp worktree before the story ends.
- **Table format:** Heading, one table, six columns. Enforcer is a backticked command or `none`. Since is `seed` for these rows. Spec: `spec.md` → ## Business Rules (Expanded) → 9.
- **Byte and style limits:** Keep the table and the test within the repo's existing lint and leanness checks. Write in plain prose.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Story 2 seeding] — technical-spec.md → ## Error & Rescue Map, row "Story 2 seeding"
- **Shadow paths:** [] — none in technical-spec.md → ## Shadow Paths for this story
- **Business rules:** Rule 6 (proof line grammar and ref types), Rule 8 (materialize the mistake without touching the working tree), Rule 9 (table format), Rule 10 (table location) — spec.md → ## Business Rules (Expanded)
- **Experience:** [] — none for this story
- **Interface and grammar:** technical-spec.md → ## Seeded table and ## Table grammar, for the required header cells and the `none` constraint
- **Constraints:** spec.md → ## Technical Concerns → "Proof needs history" and "Referenced paths"

## What Was Built

**Implementation Date:** 2026-10-29

### Files Created

- **`.writ/retros/rule-enforcers.md`** — heading `# Rule-to-Enforcer Table`, one plain-prose paragraph, and one table with three `seed` rows:
  - The suite runs on Python 3.9 — Written in `CLAUDE.md`; Enforcer `uv run --python 3.9 --with pytest pytest scripts/tests/test_ac_trace.py::CitationScanTests::test_symlink_loop_does_not_crash_the_scan`; Rung `test`; Proof `0335b291e1403b38be6305a4de8154547d92604e: fails` (parent of `ebbf064`, "fix(ac-trace): skip unresolvable symlinks on Python < 3.13").
  - Generated platform trees are never hand-edited or stale — Written in `adapters/claude-code.md`; Enforcer `python3 scripts/gen-platform-trees.py --check`; Rung `lint`; Proof `ddfb17ffe9b6de163a0d9aa31b43d7e2d2e30878: fails` (parent of `d47bcec`).
  - Instruction files use plain prose — Written in `skills/plain-prose/SKILL.md`; Enforcer `none`; Rung `docs`; Proof `—`.
- **`scripts/tests/test_retro_fix_ladder.py`** (2 tests) — the heading, one table, and the exact header (AC-2.1); `retro-check.py --table` prints `pass`, at least two enforced rows with `<sha>: fails` proofs, and at least one `none` row with `docs` and `—` (AC-2.2 to AC-2.4). Module-level `REPO_ROOT`, `run_retro_check`, `table_blocks`, and `table_rows` for Story 3's pins.

### Files Modified

None.

### Implementation Decisions

1. **Proofs materialized with `git worktree add --detach`** under the scratchpad for each parent and fix, then removed; `git worktree list` shows none left.
2. **Rungs** — a pytest node is `test`; the static `--check` is `lint` (Business Rule 4).
3. **Shipped-refs left out** — its enforcer postdates the fix (DEV-010).
4. **`--with pytest`** keeps the parent run comparable (DEV-009).

### Test Results

**Verification:** `uv run --python 3.9 pytest scripts/tests/test_retro_fix_ladder.py scripts/tests/test_retro_check.py -v` → 64 passed; `python3 scripts/retro-check.py --table .writ/retros/rule-enforcers.md --repo .` → `pass` (3 table rows); both proofs re-run by the reviewer (parents exit 1, fixes exit 0); reviewer's full `uv run --python 3.9 pytest` in a temp copy → 3632 passed, 3 skipped; `bash scripts/eval.sh` → 0 findings; `ac-trace.py check` → 0 findings.
- ✅ test-integrity authenticity: pass
- coverage: unverifiable (`no_coverage_report`)

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small
- **Security:** Clean (list-argv subprocess)
- **Boundary Compliance:** both files owned
- **gate3-route:** evaluator-agent
- **reviewer-filters:** on
- **gate0-divergence:** skip (route evaluator-agent)
- **review-panel:** skipped — platform cannot spawn other vendors
- **review-override check:** unverifiable (test-integrity coverage: no_coverage_report)
- **safety-fact:** not on route
- **arch-lint:** none — see .writ/docs/architecture-lint.md
- **build-smoke:** unverifiable (unsupported_stack)
- **app-verify:** unverifiable (no_recipe)
- **docs-check:** unverifiable (no public exports in the changed set)

### Deviations from Spec

- **[DEV-009] The Python 3.9 enforcer adds `--with pytest`** — Severity: Small — Resolution: Auto-amended
- **[DEV-010] Two enforced rows, not three; the trees proof is a planned stale window** — Severity: Small — Resolution: Auto-amended
