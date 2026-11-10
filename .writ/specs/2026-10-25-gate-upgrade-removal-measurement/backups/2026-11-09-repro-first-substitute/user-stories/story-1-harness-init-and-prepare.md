# Story 1: Trial Harness: init and prepare

> **Status:** Completed ✅ (2026-10-29)
> **Commit:** 2d1f3e50538d9be95f7d89b379f7214c8eca66b3
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer
**I want to** build the `init` and `prepare` subcommands of the dev-only harness `.writ/eval/gate-upgrade-trial/gate-upgrade-trial.py`
**So that** each of the four Phase 11 baseline stories gets a trial file, a read-only checkout, and one config per arm, with yuss left unchanged

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [x] Given a baseline JSON with a four-story `selection`, when `init --baseline FILE --out FILE` runs, then it writes a `gate-upgrade-trial-v1` skeleton that copies the five identity fields of each story, records a `present` value for each of the four upgrades, and has no recorded arms. A failed presence probe stores `present: false` for that upgrade and does not fail the run `[AC-1.1]`
- [x] Given a baseline that is missing, unparseable, or has a `selection` other than four stories, or a non-hex SHA, or an unsafe path, or an existing `--out` without `--force`, when `init` runs, then it exits 2 with a `reason:` line and leaves `--out` unchanged `[AC-1.2]`
- [x] Given a local git repository standing in for yuss, when `prepare --trial FILE --story ID --yuss PATH --tmp-root DIR` runs, then it creates `<tmp-root>/writ-gate-trial-<slug>/` with `checkout/` at the story commit, a `parent/` worktree at the parent SHA, `diff.patch`, `story.md`, and `contract.md`. The yuss HEAD, refs, index, and `git status --porcelain` are unchanged afterward `[AC-1.3]`
- [x] Given a trial file and a prepared story, when `prepare` runs, then it runs the Gate 2.5 and Gate 0 route subprocesses, stores `routes` in the trial file atomically, runs `blast-radius` when `gate3_route` is `review-agent` and `safety-fact` is present, and writes `arms/<arm>/.writ/config.md` for every arm with the switch states from technical-spec § Arms `[AC-1.4]`
- [x] Given a yuss path that is missing, a commit that is unreachable, a parent beyond depth 2, or a `review-panel.py` that is missing or lacks a reused name, when `prepare` runs, then it exits 2 with one line naming the story (or `reason: review_panel_missing`), removes any partial run directory, and writes nothing to the trial file `[AC-1.5]`

## Implementation Tasks

- [x] 1.1 Write failing tests for `init` in `scripts/tests/test_gate_upgrade_trial.py`, loading the harness by file path with importlib. Use a mini baseline under `scripts/tests/fixtures/gate-upgrade-trial/`. Cover the skeleton, presence probes, and each refusal. No network `[AC-1.1, AC-1.2]`
- [x] 1.2 Write failing tests for `prepare` using a throwaway local git repo in `tmp_path` as the yuss stand-in. Snapshot HEAD, refs, and `git status --porcelain` before and after. Cover the missing path, the unreachable commit, the depth-2 parent, and the missing `review-panel.py` `[AC-1.3, AC-1.5]`
- [x] 1.3 Implement `init` in the harness: validate the baseline, copy the five identity fields, run the four presence probes against `--repo`, and write the skeleton atomically. Refuse per the Subcommands table `[AC-1.1, AC-1.2]`
- [x] 1.4 Implement the checkout half of `prepare`: load `scripts/review-panel.py` with `spec_from_file_location`, call `_prepare_run` into `<tmp-root>/writ-gate-trial-<slug>/`, add the `parent/` worktree, and remove the run directory on any failure `[AC-1.3, AC-1.5]`
- [x] 1.5 Implement routes and arm configs in `prepare`: run `change-surface.py classify` and `boundary-map.py compute` and `crossings` as subprocesses, store `gate0_route` as `skip` on an empty or unverifiable set, run `blast-radius` when required, write each arm's config, and store routes atomically `[AC-1.4, AC-1.5]`
- [x] 1.6 Verify acceptance criteria are met: run `init` against `.writ/eval/baselines/2026-09-07-claude-fable-5-1.json` into a temp path and confirm four stories. Run the fixture flow and confirm yuss is unchanged `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`
- [x] 1.7 Verify all tests pass: `uv run pytest`, `uv run --python 3.9 pytest`, the bash tests, and `bash scripts/eval.sh` outside the sandbox `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

## Notes

- **Dev-only harness.** The file lives under `.writ/eval/`, so `is_shippable_script` never ships it and the Classification table needs no row. It is deleted in Story 4.
- **Reuse by path.** `_prepare_run` is the only `review-panel.py` name this story needs. Story 2 needs `parse_output`, `trial_key`, and `_key_order`. Check all four at load time so a missing name exits 2 with `reason: review_panel_missing`.
- **Depth 2.** `prepare` fetches the story commit at depth 2 so that `parent_sha` is present. A parent beyond that depth must exit 2, not diff against a wrong base.
- **State directory.** Resolve `<primary checkout>/.writ/state/gate-upgrade-trial/` through `git rev-parse --path-format=absolute --git-common-dir`. Tests pass `--state-dir` so they never write to the real primary checkout.
- **Presence probes are checked at `init` only.** The sibling specs create the switches and skills this story probes. Tests use fixtures, so they pass before those specs land. The real `init` run belongs to Story 3, which depends on all three siblings.
- **Blast-radius dependency.** `blast-radius` comes from `2026-10-25-review-route-rigor`. If the subcommand is absent while `safety-fact` is present, `prepare` exits 2 with `reason: blast_radius_unavailable`.
- **Arm configs are inputs only.** Each `arms/<arm>/.writ/config.md` carries switch states and nothing else. The arm procedures (spawns, verifier runs) belong to Story 3.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [init (baseline missing or unparseable; selection not four stories; non-hex SHA; unsafe path; `--out` exists without `--force`; presence probe fails), prepare (yuss path missing or SHA unreachable; parent not reachable at depth 2; `review-panel.py` missing or lacks a reused name; planned set empty or crossings `unverifiable`; `blast-radius` absent while `safety-fact` present)] — from technical-spec.md § Error & Rescue Map
- **Shadow paths:** [Trial run (nil: no trial file; empty: no upgrade-only findings; upstream error: yuss unreachable before any write)] — from technical-spec.md § Shadow Paths
- **Business rules:** [Baseline (the four-story `selection` only, no substitute), yuss isolation (read-only `rev-parse` before any write, then `git init` and `git fetch --depth 2` under `$TMPDIR`)] — from spec.md → ## Business Rules (Expanded) → 1. Baseline and 2. yuss isolation
- **Technical:** technical-spec.md → ## Upgrades Under Test (probe table); ## Harness (state directory, importlib loading, `gate-upgrade-trial-v1` schema); ## Subcommands (`init` and `prepare` rows); ## Routes (Gate 2.5 and Gate 0 commands); ## Arms (switch states per arm)
- **Files in scope:** technical-spec.md → ## Files in Scope (harness, `scripts/tests/test_gate_upgrade_trial.py`, fixtures row, Stories 1 and 2)

## What Was Built

**Implementation Date:** 2026-10-29

### Files Created

1. **`.writ/eval/gate-upgrade-trial/gate-upgrade-trial.py`** (578 lines) — dev-only harness, Python 3.9 stdlib. `init` (baseline selection → `gate-upgrade-trial-v1` skeleton, four presence probes, optional `--yuss` before-snapshot as hashes) and `prepare` (pre-flight with no writes; `_prepare_run` loaded from `scripts/review-panel.py` by path; `parent/` worktree; Gate 2.5 and Gate 0 routes via `change-surface.py` and `boundary-map.py` subprocesses; blast radius on the review-agent route; `tests.txt`; six arm configs; routes stored atomically last). Refusals raise `Refusal(code, detail)`; `main` prints one stderr `reason:` line, stdout empty, exit 2.
2. **`scripts/tests/test_gate_upgrade_trial.py`** (1034 lines, 93 tests) — init skeleton, probes, refusals, yuss snapshot; prepare inputs, routes (review-agent, evaluator-agent, skip, unverifiable), tests.txt, arm configs checked with `review-override.py switch`, every refusal with run-dir cleanup and an unchanged stand-in yuss.
3. **`scripts/tests/fixtures/gate-upgrade-trial/mini-baseline.json`** — four-story mini baseline.

### Files Modified

[None modified]

### Implementation Decisions

1. **Sketch A (Gate 0 divergence)** — exceptions plus one cohesive `prepare`; chosen over the result-value sketch because it added fewer new public names with the same unchanged usage.
2. **Local git helpers for pre-flight** — `init` must not load review-panel.py; only `_prepare_run` and `PrepareError` are called from it (DEV-002).
3. **`init --yuss`** records the before-snapshot so Business Rule 2 needs no hand edit (DEV-001).

### Test Results

**Verification:** orchestrator run `uv run pytest scripts/tests/test_gate_upgrade_trial.py -q` → 93 passed, exit 0; coder and reviewer: `uv run --python 3.9 pytest` 93 passed, full suite 3734 passed, 3 skipped; bash tests 51/51; `bash scripts/eval.sh` 0 findings.
**Coverage:** 99% (coverage.py, orchestrator-measured; `test-integrity.py coverage` unverifiable: no report format it reads)
- ✅ test-integrity authenticity: pass

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small (DEV-001, DEV-002, DEV-003)
- **Security:** Low (read-only git calls on yuss, list-argv subprocesses, no network)
- **Boundary Compliance:** three owned files only
- **gate3-route:** review-agent (outside_boundary .writ/eval/gate-upgrade-trial/gate-upgrade-trial.py scripts/tests/test_gate_upgrade_trial.py scripts/tests/fixtures/gate-upgrade-trial/mini-baseline.json)
- **reviewer-filters:** on
- **gate0-divergence:** chose A (errors as exceptions, one call) — B added more refusal codes with the same unchanged usage
- **review-panel:** skipped — platform cannot spawn other vendors
- **review-override check:** unverifiable (test-integrity coverage: no_coverage_report)
- **safety-fact:** traced (claimed traced) — no existing file loads, imports, or runs the new harness, tests, or fixture
- **jev shadow:** pass (criteria=5 agree=3 false_block=2) — advisory only
- **arch-lint:** none — see .writ/docs/architecture-lint.md
- **build-smoke:** unverifiable (unsupported_stack)
- **app-verify:** unverifiable (no_recipe); **docs-check:** unverifiable (no public exports)
- **Recommendations carried forward:** run `prepare` one story at a time (concurrent runs on one trial file can lose `routes`); confirm each real `tests.txt` has content.
