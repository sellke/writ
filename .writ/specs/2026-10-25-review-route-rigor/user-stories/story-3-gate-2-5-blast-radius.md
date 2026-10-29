# Story 3: Blast radius at Gate 2.5

> **Status:** Completed ✅ (2026-10-29)
> **Priority:** High
> **Dependencies:** Story 1, Story 2

## User Story

**As a** /implement-story orchestrator, and the review-agent that traces callers
**I want to** list, for each changed non-test file, the tracked files outside the change set that reference it, and save that list at Gate 2.5 on the review-agent route
**So that** the reviewer starts its caller trace from a concrete list, and Story 4's verifier can check a `traced` claim against it

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [x] Given a changed non-test file that a tracked file outside the change set references by path (with or without extension) or by stem, when `python3 scripts/change-surface.py blast-radius --changed FILE --repo .` runs, then the referring file appears under `consumers` for that changed file, a test-like referrer (`.test.`, `.spec.`, `__tests__/`, `test_*.py`, `*_test.py`, `*_test.go`, or a `test/` or `tests/` segment) appears under `tests` instead, no changed file and no file under `.writ/` appears in either list, and a candidate over 1 MB or not valid UTF-8 is skipped without an error `[AC-3.1]`
- [x] Given a changed file whose stem is generic (for example `index` or `utils`) or shorter than 4 characters, when blast-radius runs, then a file that contains only the bare stem is not listed and a file that contains the file's path is listed; and given any token, a match counts only when the characters on both sides are not `[A-Za-z0-9_-]`, so `review-override` does not match inside `review-override-v2` `[AC-3.2]`
- [x] Given a changed file with more matching referrers than `--limit`, when blast-radius runs with `--limit 2`, then that file's `consumers` list holds exactly 2 entries sorted by path and the changed file's path appears in `truncated` `[AC-3.3]`
- [x] Given `git ls-files` fails in `--repo`, when blast-radius runs, then it walks the filesystem and returns `verdict: pass` with `reasons: ["no_git_walked"]`; given `--repo` is not a readable directory, then it returns `verdict: unverifiable` with `reasons: ["repo_unreadable"]` and exit 0; given an empty `--changed`, then it exits 2; and `classify` output and exit codes match the behavior before this story `[AC-3.4]`
- [x] Given `gate3_route` names `review-agent` and `review-override.py switch --name safety-fact` prints `on`, when Gate 2.5 in `commands/implement-story.md` runs, then it writes `.writ/state/blast-radius-<story-stem>.json` and passes that file to Gate 3 as `blast_radius`; given the switch prints `off` or the route is `evaluator-agent`, then `blast_radius` is `(none)` and no file is written `[AC-3.5]`

## Implementation Tasks

- [x] 3.1 Write tests first by extending `scripts/tests/test_change_surface.py`: stem match, path match with and without extension, generic-stem and short-stem path-only match, token boundaries, `.writ/` and changed-file exclusion, test split, cap and `truncated`, no-git walk, non-UTF-8 and >1 MB skip, bad `--repo`, empty `--changed` exit 2, `--pretty` shape, and existing `classify` tests unchanged. Build fixtures in `TemporaryDirectory` `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`
- [x] 3.2 Implement the `blast-radius` subcommand and a new test-like helper in `scripts/change-surface.py` (leave `is_test` and `classify` as they are): build search tokens, list candidates with `git ls-files` or the walk fallback, skip `.writ/`, changed files, files over 1 MB and non-UTF-8 files, split into `consumers` and `tests`, cap at `--limit` (default 20) with `truncated`, print JSON by default and the check shape with `--pretty`; update the module docstring `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`
- [x] 3.3 Add the "Blast radius" paragraph to the `#### Gate 2.5` section of `commands/implement-story.md`, after the existing `unverifiable` sentence, as drafted in technical-spec § Gate 2.5 Change; record `wc -c commands/implement-story.md` before and after `[AC-3.5]`
- [x] 3.4 Regenerate trees with `python3 scripts/gen-platform-trees.py`; do not hand-edit generated files `[AC-3.5]`
- [x] 3.5 Run `uv run --python 3.9 pytest scripts/tests/test_change_surface.py`, `bash scripts/eval.sh --check=change-surface`, and `python3 scripts/gen-platform-trees.py --check`, and confirm all pass `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`
- [x] 3.6 Verify each acceptance criterion against script output and the Gate 2.5 text `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`

## Notes

- The blast radius is a text-reference heuristic, not a call graph. It finds files that mention a changed file. It does not prove they call it.
- Story 4's verifier uses the union of `consumers` to accept the `traced` rung, and accepts `traced: none` only when that union is empty and the verdict is `pass`. Keep the JSON keys (`verdict`, `consumers`, `tests`, `truncated`, `reasons`) exactly as technical-spec § Blast Radius states.
- Generic stems: `index`, `main`, `mod`, `__init__`, `utils`, `util`, `types`, `type`, `constants`, `config`, `helpers`, `readme`, `setup`, `app` (case-insensitive). These and stems under 4 characters match by path only.
- `no_git_walked` is informational and keeps `pass`. Only an unreadable `--repo` gives `unverifiable`.
- The walk fallback skips `.git/`, `node_modules/`, and dot-directories. `.writ/` is always skipped.
- Byte budget: Gate 2.5 and Gate 3 may grow by at most 1,800 bytes net across the whole spec. This story's paragraph should stay well under that so Story 4 has room.
- Edit only the `#### Gate 2.5` section. Do not edit Gate 0 (owned by the design-divergence spec), Gate 3 (Story 4), or Step 4's report-line list.
- Story 1 provides `review-override.py switch`. Story 2 edits Gate 3 of the same command file, so run this story after Story 2 and regenerate trees after rebasing.
- Python 3.9 floor. No `match`, no `X | Y` unions at runtime, no 3.10+ `pathlib` or `str` methods. Use `from __future__ import annotations`.
- Risk: a large repo makes the scan slow. Use one pass over candidates and one compiled pattern per changed file.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [`blast-radius` lists candidates (`git ls-files` fails), `blast-radius` reads a candidate (binary, non-UTF-8, or >1 MB), `blast-radius` on a huge repo (slow scan)] — from technical-spec.md § Error & Rescue Map
- **Shadow paths:** [Blast radius] — from technical-spec.md § Shadow Paths
- **Business rules:** [Safety fact applies only when `gate3_route` names `review-agent` and the `safety-fact` switch is on; switches default to on] — from spec.md → Business Rules and → Business Rules (Expanded) → When the safety fact applies
- **Experience:** [Journey steps 1–2 (Gate 2.5 computes `gate3_route`, then runs blast-radius and saves `.writ/state/blast-radius-<story-stem>.json`); State Catalog row "Blast radius unverifiable"] — from spec.md → Experience Design → Journey and → State Catalog

Contracts: technical-spec.md → ## Blast Radius (tokens, candidates, split, cap, JSON and `--pretty` shapes, exit codes) and → ## Gate 2.5 Change (the paragraph to add).

## What Was Built

**Implementation Date:** 2026-10-29

### Files Created

[None created]

### Files Modified

- **`scripts/change-surface.py`** (`blast-radius` subcommand)
  - `python3 scripts/change-surface.py blast-radius --changed FILE … [--repo .] [--limit 20] [--pretty] [--json]`. JSON keys `verdict`, `consumers`, `tests`, `truncated`, `reasons`; every non-test changed file is a key in both maps. `--pretty` prints the verdict, one `<changed>: <n> consumer(s), <m> test(s)` line per non-test changed file, `reason:` lines, and `change-surface blast-radius: <verdict> (<n> changed, <k> consumers)`.
  - Tokens: repo-relative path, path without extension, and the stem unless generic or under 4 characters; boundaries `(?<![A-Za-z0-9_-])…(?![A-Za-z0-9_-])`; one compiled pattern per changed file, one read per candidate.
  - Candidates from `git ls-files -z`; on git failure a walk that skips `.git/`, `node_modules/`, and dot-directories (`no_git_walked`, still `pass`). Always skips `.writ/` at any depth, changed files, non-regular files, files over 1 MB, and non-UTF-8 files. Unreadable `--repo` → `unverifiable` + `repo_unreadable`, exit 0; empty `--changed` or `--limit` < 1 → exit 2.
  - New `is_test_like` helper; `is_test` and `classify` unchanged (stdout and exit codes diffed against HEAD).
- **`commands/implement-story.md`** (`#### Gate 2.5` only) — "Blast radius." paragraph from technical-spec § Gate 2.5 Change, word for word. File 38,729 → 39,076 bytes (+347).
- **`scripts/tests/test_change_surface.py`** — 34 tests in 10 classes appended under Story 3 of `2026-10-25-review-route-rigor`.
- **`scripts/tests/test_governor_enforcement.py`** — `KNOWN_OVER_BUDGET["commands/implement-story.md"]` 13769 → 14116, dated.
- Regenerated: `plugins/writ/scripts/change-surface.py`, `plugins/writ/commands/implement-story.md`, `cursor/plugin/commands/implement-story.md`.

### Implementation Decisions

1. **Gate 0 divergence skipped** — the planned files routed `evaluator-agent` (`gate0-divergence: skip (route evaluator-agent)`); the actual change set routed `review-agent` at Gate 2.5.
2. **FIFO guard** — `stat` before `open`, so a tracked FIFO cannot hang Gate 2.5 (DEV-010).
3. **Smoke on this repo** — `blast-radius --changed scripts/review-override.py --repo . --pretty` → `pass`, 12 consumers, 14 tests, 0.14 s over ~2,310 tracked files.

### Test Results

**Verification:** `uv run --python 3.9 pytest scripts/tests/test_change_surface.py scripts/tests/test_governor_enforcement.py scripts/tests/test_agent_cli_contract.py scripts/tests/test_gen_platform_trees.py -q` → 485 passed; coding agent's full 3.9 suite → 3356 passed, 3 skipped; bash tests 0 FAIL; `bash scripts/eval.sh --check=change-surface` → pass; `gen-platform-trees.py --check` → pass; `ac-trace.py check` → 0 findings.
- ✅ test-integrity authenticity: pass
- coverage: no new files in this story

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small
- **Security:** Clean (fixed-argv `git ls-files`, regular-file reads capped at 1 MB, `re.escape`d tokens)
- **Boundary Compliance:** three owned files; governor pin and three generated copies justified
- **gate3-route:** review-agent (outside_boundary cursor/plugin/commands/implement-story.md; outside_boundary plugins/writ/commands/implement-story.md; outside_boundary plugins/writ/scripts/change-surface.py; outside_boundary scripts/tests/test_governor_enforcement.py)
- **reviewer-filters:** on
- **gate0-divergence:** skip (route evaluator-agent)
- **review-panel:** skipped — platform cannot spawn other vendors
- **review-override check:** pass (no blocking helper finding)
- **jev shadow:** pass (judged) criteria=5 agree=4 false_block=1 — advisory only

### Deviations from Spec

- **[DEV-008] Repo-root extensionless path token dropped for generic or short stems** — Severity: Small — Resolution: Auto-amended
- **[DEV-009] `.writ/` skipped at any depth** — Severity: Small — Resolution: Auto-amended
- **[DEV-010] Non-regular and unreadable candidates skipped** — Severity: Small — Resolution: Auto-amended
- **[DEV-011] `--pretty` counts are taken before the cap and cover non-test changed files** — Severity: Small — Resolution: Auto-amended
