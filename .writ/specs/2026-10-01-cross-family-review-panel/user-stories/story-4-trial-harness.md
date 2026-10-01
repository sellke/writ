# Story 4: Retrospective Trial Harness and Report

> **Status:** Completed ✅
> **Commit:** 1df2344b03513c1a7fc5f30c7770a06c83dc6320
> **Priority:** Medium
> **Dependencies:** Story 2 (tally parser)

## User Story

**As a** Writ maintainer
**I want to** prepare, record, label, and score a retrospective trial of the single evaluator against the evaluator plus the panel over the four Phase 11 baseline stories, using `review-panel.py trial-*` subcommands
**So that** whether the panel stays or is removed is decided by a committed, text-free trial file and a mechanical `trial-report` verdict, without ever writing inside the read-only yuss.app checkout

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.5

- [x] Given a baseline JSON with a four-story `selection`, when `python3 scripts/review-panel.py trial-init --baseline PATH --out PATH` runs, then it writes a `panel-trial-v1` skeleton carrying each story's `story_id`, `story_path`, `spec_folder`, `story_commit`, and `parent_sha` with no recorded arms, and a missing or unparseable baseline (or a `selection` without four stories) exits 2 without writing `--out` `[AC-4.1]`
- [x] Given a trial file and a local git repository standing in for yuss, when `trial-prepare --trial FILE --yuss PATH --story ID --tmp-root DIR` runs, then it creates `<tmp-root>/writ-panel-trial-<story>/checkout` via `git init` + `git fetch --depth 2 <yuss> <story_commit>`, asserts the checked-out commit equals `story_commit`, writes `diff.patch` (`parent_sha..story_commit`), the story file, and the spec's `## Specification Contract` into the run directory, prints their paths, and leaves the yuss repo's HEAD, refs, index, and working tree unchanged; a missing yuss path or an unreachable commit exits 2 with one line naming the story and writes nothing `[AC-4.2]`
- [x] Given reviewer output fixtures for one story, when `trial-record --trial FILE --story ID --arm evaluator|panel --origin "<model>" --primary FILE [--reviewer slug=FILE …]` runs, then it parses the outputs with the Story 2 tally parser, stores per story and arm the finding keys with their vendors and severities, copies the raw outputs to `.writ/state/panel-trial/<story>/`, and marks every key in the `panel` arm raised by ≥1 panel vendor and absent from the `evaluator` arm as a panel-only finding with `label: null`; the trial JSON contains no reviewer, diff, source, or story text `[AC-4.3]`
- [x] Given a recorded panel-only finding, when `trial-label --trial FILE --story ID --key KEY --label valid|invalid --note "<text>"` runs, then it sets that finding's label and note; a note over 200 characters, containing a newline, or containing a backtick block, a label other than `valid`/`invalid`, or a key that is not a panel-only finding for that story exits 2 and leaves the file unchanged `[AC-4.4]`
- [x] Given a trial file, when `trial-report --trial FILE [--json]` runs, then it prints `keep` when ≥1 panel-only finding is labeled `valid`, `remove` when every panel-only finding is labeled and none is valid, and `unverifiable` (e.g. `review-panel: unverifiable — 2 unlabeled`) when any finding is unlabeled or any of the four stories lacks either arm; the output is verdict-first with per-story counts, includes the line `sample: 4 stories; one valid miss keeps the panel — a low bar, not a cost case`, ends with a `review-panel:` summary line, and exits 0 `[AC-4.5]`

## Implementation Tasks

- [x] 4.1 Write failing tests in `scripts/tests/test_review_panel.py` (new `trial_*` test group) using a fixture mini-baseline and trial files under `scripts/tests/fixtures/review-panel/trial/` plus a throwaway local git repo built in `tmp_path` (two commits, a story file, a spec with `## Specification Contract`) standing in for yuss: init skeleton and refusals; prepare outputs, commit assertion, yuss-unchanged check (HEAD, `git status --porcelain`, refs before and after), missing-path and unreachable-commit exit 2; record keys/vendors/severities, `label: null` panel-only marking, raw-output copy, and a no-text scan of the JSON; label validation; report `keep`/`remove`/`unverifiable` and the caveat line — no network, no real yuss `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`
- [x] 4.2 Implement `trial-init` in `scripts/review-panel.py`: read the baseline's `selection`, copy the five identity fields per story into a `panel-trial-v1` object (`schema`, `baseline`, `stories[]` with empty `arms`), refuse to overwrite an existing `--out` without `--force` `[AC-4.1]`
- [x] 4.3 Implement `trial-prepare` following `scripts/pipeline-baseline.py`'s isolation (read-only `git -C <yuss> rev-parse` reachability check before any write, then fresh `git init` + `git fetch --depth 2` under `--tmp-root`/`$TMPDIR`, `git rev-parse HEAD` assertion, `git diff parent..commit` into `diff.patch`, story and contract extracted via `git show <commit>:<path>`) `[AC-4.2]`
- [x] 4.4 Implement `trial-record` by calling Story 2's per-output parse and vendor resolution (no second parser): store `{key, vendors, severity}` per story per arm, recompute panel-only findings whenever either arm is recorded (preserving existing labels for keys still panel-only), and copy raw outputs to `.writ/state/panel-trial/<story>/<arm>-<slug|primary>.md` `[AC-4.3]`
- [x] 4.5 Implement `trial-label` (validation, atomic write) and `trial-report` (Business Rule 12 verdict, per-story arm and finding counts, caveat line, `--json` single object, `review-panel:` last line, exit 0; usage errors exit 2) `[AC-4.4, AC-4.5]`
- [x] 4.6 Verify acceptance criteria: run `trial-init` against `.writ/eval/baselines/2026-09-07-claude-fable-5-1.json` into a temp path and confirm four stories; run the fixture flow end to end; `rg` the fixture trial JSON for diff markers (`@@`, `+++`) and story prose to confirm no text leaked `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`
- [x] 4.7 Verify all tests pass: `uv run pytest`, `uv run --python 3.9 pytest scripts/tests/test_review_panel.py`, the bash tests, and `bash scripts/eval.sh` (outside the sandbox) with Findings 0 `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`

## Notes

- **Reuse, don't re-parse.** Story 2 should expose the per-output parse (verdict line, `ac:` and `<category>:<path>` keys, severity) and the vendor lookup as module functions; `trial-record` calls them. If Story 2 shipped them inline in the `tally` handler, extract them first rather than duplicating the regexes.
- **yuss is read-only.** The only commands that touch the yuss path are `git -C <yuss> rev-parse`/`show`/`diff-tree` and `git fetch` *from* it into the fresh repo. Tests must snapshot the stand-in repo's HEAD, refs, and `git status --porcelain` before and after `trial-prepare` and assert equality.
- **Depth 2 matters.** `diff.patch` needs `parent_sha` present in the fresh clone; fetching `story_commit` at depth 2 brings its first parent. A merge-commit story (`parent_is_merge` in the baseline) still diffs against the recorded `parent_sha`; if that parent is not fetched, exit 2 rather than diffing against the wrong base.
- **No text in the committed file.** Keys are already path-or-ID shaped; severities are an enum; label notes are capped and screened. The raw outputs (which contain prose and may quote source) live only under gitignored `.writ/state/panel-trial/`. Story 5 commits the trial JSON, so a leak here becomes a committed leak there.
- **Panel-only is relative.** Recording the `evaluator` arm after the `panel` arm can remove a panel-only finding; recording order must not matter for the final set, and labels on keys that stop being panel-only are dropped.
- **Integration.** Story 5 drives these subcommands in Cursor and acts on `trial-report`. If Story 5 ends in `remove`, `status` and `tally` are deleted but the committed trial JSON and `trial-report.md` remain as the record.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Trial prepare (yuss path missing / commit unreachable), Trial report (unlabeled finding or missing arm)]
- **Shadow paths:** []
- **Business rules:** spec.md → ## 📋 Business Rules (Expanded) (11 Trial integrity — no text in the trial file, raw outputs gitignored, yuss read-only; 12 Trial verdict — panel-only definition and keep/remove/unverifiable); spec.md → ## 📋 Business Rules (8 Removal rule)
- **Experience:** [User Journey step 6 (Trial), Interaction Patterns → every line starts with `review-panel:`]
- **Technical:** sub-specs/technical-spec.md → ## Trial Harness (Story 4); ## `tally` (Parse per output, finding keys); ## Files in Scope (`review-panel.py`, test file, fixtures rows); spec.md → ⚠️ Technical Concerns (The trial is small); `scripts/pipeline-baseline.py` module docstring (read-only yuss isolation)

## What Was Built

**Implementation Date:** 2026-10-01

### Files Created

1. **`scripts/tests/fixtures/review-panel/trial/mini-baseline.json`** — four-story `selection` for `trial-init` tests. [AC-4.1]
2. **`scripts/tests/fixtures/review-panel/trial/panel-location-source.md`** — a reviewer output whose Location quotes code, for the digest-key rule. [AC-4.3]

### Files Modified

1. **`scripts/review-panel.py`** — five trial subcommands on Story 2's `parse_output` / `slug_vendor` / `origin_vendor` (no second parser): [AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]
   - `trial-init` writes a `panel-trial-v1` skeleton (five identity fields, empty `arms`, empty `panel_only`); refuses a missing / unparseable baseline, a selection without four stories, non-hex SHAs, unsafe paths, and an existing `--out` without `--force`.
   - `trial-prepare` checks both SHAs with read-only `git -C <yuss> rev-parse` before writing, then `git init` + `fetch --depth 2 -- <yuss> <commit>` under `<tmp-root>/writ-panel-trial-<spec>--<story>/checkout`, asserts HEAD, writes `diff.patch`, `story.md`, `contract.md`; every failure exits 2 with one line naming the story and removes the run dir.
   - `trial-record` stores `{key, vendors, severity}` per arm plus `origin`, `session_vendor`, `primary_verdict`, `reviewers`, `dropped`; recomputes panel-only findings on every record (order-independent, labels kept for keys still panel-only); copies raw outputs to `.writ/state/panel-trial/<spec>--<story>/<arm>-<slug|primary>.md`; non-path Locations become digests.
   - `trial-label` validates label, key, and note (≤200 chars, one line, no code block) before an atomic write.
   - `trial-report` prints `keep` / `remove` / `unverifiable`, `reason:` lines, per-story counts, the caveat line, and a `review-panel:` summary; `--json` one object; exit 0.
2. **`scripts/tests/test_review_panel.py`** — +38 tests (139 total) across `TrialInitTests`, `TrialPrepareTests` (stand-in yuss built per test; HEAD, refs, and `git status --porcelain` compared before and after), `TrialRecordTests` (no-text scan over every fixture line), `TrialLabelTests`, `TrialReportTests`. [AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]

### Verification

- `uv run pytest scripts/tests/test_review_panel.py` and `uv run --python 3.9 …` → 139 passed each; `review-panel.py` line coverage 98% (653/669); test-integrity coverage and authenticity pass.
- `trial-init` on `.writ/eval/baselines/2026-09-07-claude-fable-5-1.json` into a temp path → four stories (test). The real yuss was never touched.
- Gates: arch-check pass; boundary 0 crossings → `evaluator-agent`; review-override pass; drift-format pass; app-verify unverifiable (no recipe); docs-check unverifiable (no public exports).
- Gate 3 evaluator-agent PASS, iteration 1. Minor findings fixed in place: source-shaped Locations stored as digests, `trial-record` bound to the repo root, `--` before the fetch source, four-story check on load, tests for a missing contract and a parent beyond depth 2 (DEV-009).
- Drift: DEV-007, DEV-008, DEV-009, Small.
- Iteration count: 1
