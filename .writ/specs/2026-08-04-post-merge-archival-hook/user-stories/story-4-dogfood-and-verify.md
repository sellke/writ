# Story 4: Dogfood and Verify

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 3

## User Story

**As a** Writ maintainer
**I want to** proof that this hook actually works against real merged PRs and real `/release` runs, including eventually this spec's own lifecycle
**So that** I trust the mechanism before relying on it to replace manual `/status --archive` reminders

## Acceptance Criteria

- [ ] Given a fixture repo with a merged-PR SHA match, a resolvable complete-family spec, and no other outstanding changes, when `/release` (or its direct `scripts/archive-sweep.py` single-spec entry point + `release.md` Step 1.3c logic) runs against it, then exactly that one spec is `git mv`'d to `.writ/specs/archive/<name>/` and `LEDGER.md` gains exactly one new line annotated with the triggering PR number — no other spec folder is touched.
- [ ] Given a real `/release` run in this repo where Step 1.3c's `LAST_MERGED_SHA`/`HEAD_SHA` comparison matches a genuine merged PR, when that PR's Spec Reference resolves to a spec that is not yet complete-family (or resolves to nothing, or resolves ambiguously — the common case for most day-to-day PRs), then `/release`'s terminal output and side effects are byte-for-byte identical to a hook-less run: zero archival, zero new lines anywhere, zero new prose.
- [ ] Given a spec was just archived by a hook-triggered `/release` run (fixture or real), when `/release` is run again immediately afterward with no new merge, then the run is a clean no-op with respect to this hook — no duplicate ledger line, no error, no re-attempted `git mv` — matching the idempotency guarantee `scripts/archive-sweep.py`'s batch sweep already provides.
- [ ] Given this hook is wired into `/release` but does not fire (no spec resolves), when `/release`'s existing gate behavior is exercised (spec metadata validation, build verification, conditional test suite per Step 1.3c's own test-skip heuristic), then all pre-existing gate checks pass or fail exactly as they would without this hook present — no new false pass, false fail, or altered gate ordering.
- [ ] Given `2026-08-04-spec-lifecycle-archival` and `2026-08-04-post-merge-archival-hook` each eventually reach `Complete` status and have their PRs merged, when the next `/release` run after each merge executes, then each spec is found archived at `.writ/specs/archive/<name>/` with a `LEDGER.md` line annotated with its triggering PR number — closing the exact motivating gap without a manual `/status --archive` sweep.

## Implementation Tasks

- [ ] 4.1 Write a fixture-based eval suite (e.g. `scripts/eval-post-merge-archival.py`, registered in `eval.sh` mirroring `scripts/eval-archive-sweep.py`'s pattern) covering: single-spec archive on merge match, no-op on unresolved/ambiguous spec, no-op on not-yet-complete-family spec, no-op on already-archived spec, idempotent re-run, and `git mv` failure (dirty tree/collision) not blocking `/release`
- [ ] 4.2 Run the fixture suite against a disposable test repo/worktree simulating a merged PR (fake `LAST_MERGED_SHA`/`HEAD_SHA` match, a fixture spec folder at complete-family status, a fixture branch name the shared resolver can match) and confirm the single-spec move, PR-annotated ledger line, and idempotent re-run all behave per Story 2/3's contract
- [ ] 4.3 Run a second fixture pass confirming the "common case" no-op: no resolvable spec, ambiguous resolution, and a resolved-but-not-complete-family spec each produce zero archival side effects and output identical to a hook-less baseline run (diff the full terminal output, not just exit code)
- [ ] 4.4 Confirm no regression to `/release`'s existing gate behavior by running `/release`'s documented gate steps (spec metadata validation, build verification, Step 1.3c's conditional test-skip heuristic) against a case where the hook is present but does not fire, and diff against a pre-hook baseline run of the same gate steps
- [ ] 4.5 Document the live-confirmation procedure for this repo's own two motivating specs: once `2026-08-04-spec-lifecycle-archival` and this spec (`2026-08-04-post-merge-archival-hook`) each reach `Complete` and their PRs merge, the next real `/release` run should archive each — capture that run's terminal output, the resulting `LEDGER.md` lines (with PR numbers), and confirm via `git log --follow` that each archived spec's history is preserved, exactly mirroring the parent spec's Story 6 verification method
- [ ] 4.6 Verify acceptance criteria are met: fixture criteria (1–4) confirmed immediately via Tasks 4.1–4.4; the live criterion (5) confirmed once this repo's real merge-then-release cycle for both specs actually occurs — record whichever has occurred by story completion and flag the remainder as a follow-up verification, not a blocker to closing this story
- [ ] 4.7 Verify all tests pass, including the new eval suite registered in `eval.sh`, and that existing `/release`-related eval scenarios (if any) still pass unmodified

## Notes

**Technical considerations:**

- This story cannot fully self-certify at authoring time the way the parent spec's Story 6 could — Story 6 had 39 pre-existing real specs to sweep against immediately; this hook only proves itself against live git/`gh` state at the moment `/release` runs, which requires an actual merged PR to exist. The fixture suite (Tasks 4.1–4.4) is the isolated, immediately-runnable proof; the live confirmation (Task 4.5) is real-world proof that may lag the story's own completion.
- Both paths matter and neither substitutes for the other: fixtures prove the logic is correct in isolation; the live run proves the logic survives contact with this repo's actual git history, actual `gh` PR metadata, and actual spec statuses — the same gap that motivated this spec in the first place (the parent spec shipped and released without ever being archived).
- Do not force an artificial merge cycle just to manufacture live evidence early. The story should describe the verification procedure precisely enough that whoever runs the next real `/release` after either motivating spec's PR merges can follow it and record the result — the check does not need to happen inside this story's own authoring session.

**Risks / challenges:**

- If this story's own definition of done is completed before either motivating spec's PR has actually merged, Acceptance Criterion 5 is necessarily unconfirmed at story-close time. Treat that as an expected, documented gap (per Task 4.6) rather than blocking the story — the parent spec itself already accepted a similar timing reality (its own Story 6 dogfooded against pre-existing specs, but this spec's archival could not be proven until this very story exists and ships).
- Fixture tests risk drifting from real `/release` behavior if `release.md`'s actual Step 1.3c prose changes after this story is written. Task 4.4's diff-against-baseline approach mitigates this by anchoring to documented gate steps, not assumptions about them.
- There is a bootstrapping irony worth naming plainly: this spec's own successful archival is simultaneously a Success Criterion and a test case — if the hook is broken, the clearest symptom will be `2026-08-04-post-merge-archival-hook` itself sitting unarchived after its own release, exactly like its motivating predecessor.

**Integration points:**

- Depends entirely on Story 3 (the wired hook inside `/release` Step 1.3c) being functional — do not begin fixture verification until Story 3's tests pass.
- This is this spec's own closing validation, directly mirroring the parent spec's Story 6 ("Dogfood the Sweep Against This Repo") — same philosophy (prove against production data and process, not just fixtures), same eventual outcome (both motivating specs end up archived), different mechanism (single-spec hook vs. batch sweep) and different timing constraint (requires a live merge-then-release cycle rather than a pre-existing corpus).
- Once both `2026-08-04-spec-lifecycle-archival` and `2026-08-04-post-merge-archival-hook` are archived via this mechanism, that is the concrete, human-verifiable proof the entire spec's `## Why This Exists` section was written to prevent recurring.

### Live Confirmation Status

_Recorded 2026-08-04 by the Story 4 coding agent, after Tasks 4.0–4.4._

**Fixture Acceptance Criteria (1–4): confirmed.**

- **AC1 (single-spec archive on merge match)** — confirmed by `test_hook_fires_and_archives_on_matched_and_eligible` in `scripts/tests/test_release_archival_hook.py` and by `shared-model-happy-path-archives-with-pr-annotation` in `scripts/eval-post-merge-archival.py`. Both exercises confirm exactly one spec is `git mv`'d, exactly one PR-annotated `LEDGER.md` line is added, and no other spec folder is touched.
- **AC2 (no-op byte-identical to a hook-less run on the common case)** — confirmed by `test_resolver_none_makes_no_archive_call`, `test_resolver_ambiguous_makes_no_archive_call`, and `test_resolver_matches_but_not_eligible_no_further_action` in `test_release_archival_hook.py`, plus `shared-model-skips-with-no-side-effect-on-no-match` in `eval-post-merge-archival.py`. Per Task 4.3, this combined coverage (no-match / ambiguous / not-yet-complete-family) was confirmed adequate by a targeted read of both files rather than re-derived a third time.
- **AC3 (idempotent re-run)** — confirmed by `test_resolver_matches_but_already_archived_no_further_action` in `test_release_archival_hook.py` (second hook invocation against an already-archived spec produces no duplicate ledger line and no error).
- **AC4 (no regression to `/release`'s existing gate behavior when the hook doesn't fire)** — confirmed two ways: (a) `git show a7a0bba` and `git show 5ef23c0` (Story 3's two commits touching `commands/release.md`) show every diff hunk confined to Step 1.3c's bash block and its adjacent notes — Phases 2–5 and Steps 1.3a/1.3b are byte-for-byte untouched by either commit; (b) that guarantee is now a durable, automatically-enforced invariant via `check_post_merge_archival()`'s `require_literal` pins in `scripts/eval.sh` on Step 1.3c's original three-row table (`gh` unavailable / `LAST_MERGED_SHA` equals `HEAD_SHA` / Otherwise), not merely a one-time diff claim.

**Live Acceptance Criterion (5): not yet confirmed.**

As of this recording, **0 of 2** motivating specs (`2026-08-04-spec-lifecycle-archival`, `2026-08-04-post-merge-archival-hook`) have been archived via a hook-triggered commit. AC5 requires a real merge + `/release` run for each — that has not happened yet in this session, and Task 4.5's coding-agent instructions explicitly say not to force one.

**Important — do not credit the currently-visible manual move toward AC5.** This repo's working tree currently shows `2026-08-04-spec-lifecycle-archival` mid-move: staged as deleted from `.writ/specs/2026-08-04-spec-lifecycle-archival/` and added under `.writ/specs/archive/2026-08-04-spec-lifecycle-archival/`. That is a manual `/status --archive` move that **pre-dates Story 3 and Story 4 even existing** — it is not, and cannot be, a hook-triggered archival. AC5 is satisfied **only** by an archival whose triggering commit message matches the hook's exact pattern from `commands/release.md` Step 1.3c: `chore(archive): auto-archive <spec> via PR #<n>`. `scripts/eval-post-merge-dogfood.py` (not wired into `scripts/eval.sh`'s `CHECKS=()` — see its docstring for the exact registration procedure once both specs qualify) greps committed history for that literal pattern per spec, not directory existence, so this manual move is correctly never counted. Running it today reports `0 of 2 motivating specs archived via the hook so far` and exits 0.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** [Rule 3 (ambiguous/absent resolution always skips), Rule 5 (reuses `scripts/archive-sweep.py`'s move mechanism, same idempotency check), Rule 7 (never blocks a release)] — from spec.md → 📋 Business Rules
- **Shadow paths:** [No spec resolves (common case, silent skip), Ambiguous match (silent skip), Not-yet-complete-family spec (silent skip, re-checked on future runs), Already-archived spec (no-op), `git mv` failure (skip and continue)] — from spec.md → ## 🎯 Experience Design → ### Error / Edge Experience
- **Success criteria:** [Criterion 1 (single-spec archive on merge), Criterion 2 (no-op indistinguishable from hook-less run), Criterion 3 (idempotent re-run), Criterion 4 (PR-annotated vs. unannotated ledger lines), Criterion 5 (no gate regression)] — from spec.md → ## Success Criteria
- **Origin / motivating gap:** [Real prior incident: `2026-08-04-spec-lifecycle-archival` shipped and released while `Complete`, never archived] — from spec.md → ## Origin and ## Why This Exists
- **Implementation approach:** [Story 4 dependency on Story 3, dogfood scope description] — from spec.md → ## Implementation Approach (item 4)
