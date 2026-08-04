# Story 4: Dogfood and Verify

> **Status:** Completed ✅ (2026-08-04) — fixture-scope (AC1–4) confirmed; AC5 (live merge-then-release confirmation) explicitly open, tracked below, not a blocker per this story's own Notes.
> **Commit:** d9a90af623a4b401d00e6c8455cc4c062c927548
> **Priority:** Medium
> **Dependencies:** Story 3

## User Story

**As a** Writ maintainer
**I want to** proof that this hook actually works against real merged PRs and real `/release` runs, including eventually this spec's own lifecycle
**So that** I trust the mechanism before relying on it to replace manual `/status --archive` reminders

## Acceptance Criteria

- [x] Given a fixture repo with a merged-PR SHA match, a resolvable complete-family spec, and no other outstanding changes, when `/release` (or its direct `scripts/archive-sweep.py` single-spec entry point + `release.md` Step 1.3c logic) runs against it, then exactly that one spec is `git mv`'d to `.writ/specs/archive/<name>/` and `LEDGER.md` gains exactly one new line annotated with the triggering PR number — no other spec folder is touched. _(Confirmed: `test_hook_fires_and_archives_on_matched_and_eligible` + `shared-model-happy-path-archives-with-pr-annotation`.)_
- [x] Given a real `/release` run in this repo where Step 1.3c's `LAST_MERGED_SHA`/`HEAD_SHA` comparison matches a genuine merged PR, when that PR's Spec Reference resolves to a spec that is not yet complete-family (or resolves to nothing, or resolves ambiguously — the common case for most day-to-day PRs), then `/release`'s terminal output and side effects are byte-for-byte identical to a hook-less run: zero archival, zero new lines anywhere, zero new prose. _(Confirmed: `test_resolver_none_makes_no_archive_call`, `test_resolver_ambiguous_makes_no_archive_call`, `test_resolver_matches_but_not_eligible_no_further_action` + `shared-model-skips-with-no-side-effect-on-no-match`.)_
- [x] Given a spec was just archived by a hook-triggered `/release` run (fixture or real), when `/release` is run again immediately afterward with no new merge, then the run is a clean no-op with respect to this hook — no duplicate ledger line, no error, no re-attempted `git mv` — matching the idempotency guarantee `scripts/archive-sweep.py`'s batch sweep already provides. _(Confirmed: `test_resolver_matches_but_already_archived_no_further_action`.)_
- [x] Given this hook is wired into `/release` but does not fire (no spec resolves), when `/release`'s existing gate behavior is exercised (spec metadata validation, build verification, conditional test suite per Step 1.3c's own test-skip heuristic), then all pre-existing gate checks pass or fail exactly as they would without this hook present — no new false pass, false fail, or altered gate ordering. _(Confirmed: `git show a7a0bba` diff confinement to Step 1.3c, now durably pinned via `check_post_merge_archival()`'s `require_literal` assertions on the original three-row test-skip table.)_
- [ ] Given `2026-08-04-spec-lifecycle-archival` and `2026-08-04-post-merge-archival-hook` each eventually reach `Complete` status and have their PRs merged, when the next `/release` run after each merge executes, then each spec is found archived at `.writ/specs/archive/<name>/` with a `LEDGER.md` line annotated with its triggering PR number — closing the exact motivating gap without a manual `/status --archive` sweep. _(Genuinely open — see Live Confirmation Status below. Not a blocker to this story's closure per its own Notes.)_

## Implementation Tasks

> **Note:** This story's architecture check (2026-08-04, CAUTION) found the original 4.1–4.7 list below would substantially duplicate Story 3's existing `scripts/tests/test_release_archival_hook.py` coverage. Tasks were revised pre-implementation to the list actually delivered:

- [x] 4.0 (new) Extract `run_archival_hook()` and its fixture helpers out of `scripts/tests/test_release_archival_hook.py` into a shared, non-test-prefixed module (`scripts/_archival_hook_model.py`); refactor the test file to import from it (pure refactor — same 11 tests, same assertions, verified unchanged via diff against the Story 3 commit)
- [x] 4.1 (narrowed) Write `scripts/eval-post-merge-archival.py`, registered in `eval.sh`, whose primary payload is `require_literal`/`forbid_literal` prose-pinning of `commands/release.md` Step 1.3c (resolve call, `archive-one` call, forbid-duplicate-eligibility-check guard, best-effort-guard language, immediate-commit note), plus 2 smoke scenarios (not an 11-case re-derivation) importing the shared model from Task 4.0
- [x] 4.2 Register `post-merge-archival` in `eval.sh`'s `CHECKS=()` array and add `check_post_merge_archival()`, placed adjacent to `check_archive_dogfood()`
- [x] 4.3 (narrowed) Confirm via a targeted read (not new fixture code) that the "common case" no-op paths — no-match, ambiguous, not-yet-complete-family — are adequately covered across `test_release_archival_hook.py` + the new smoke scenarios combined
- [x] 4.4 (narrowed) Confirm Story 3's prior diff claim (Phases 2–5 / Steps 1.3a/1.3b of `release.md` untouched) still holds via `git show`, then fold the guarantee durably into `require_literal` pins on Step 1.3c's original three-row test-skip table, rather than re-running a full manual diff
- [x] 4.5 (narrowed) Write `scripts/eval-post-merge-dogfood.py`, a real-repo AC5 readiness probe that defaults to a non-failing "0 of 2 archived so far" state and is deliberately **not** registered in `eval.sh`'s `CHECKS()` array until real hook-triggered evidence exists (its own docstring documents the exact registration steps for whoever picks this up once AC5 resolves)
- [x] 4.6 (narrowed) Add a `### Live Confirmation Status` subsection directly to this story file recording AC1–4 confirmed and AC5 explicitly not-yet-confirmed, with an explicit guard against crediting the pre-existing manual `/status --archive` move of `2026-08-04-spec-lifecycle-archival` toward AC5
- [x] 4.7 Full pytest suite (199/199, zero regressions, independently re-verified by both the coding agent and the review agent in isolated venvs) + manual confirmation both new scripts behave as designed (`bash scripts/eval.sh --check=post-merge-archival` exits 0; `python3 scripts/eval-post-merge-dogfood.py` exits 0 and is absent from `CHECKS()`)

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

- [x] All tasks completed (as revised by architecture check — see note above Implementation Tasks)
- [ ] All acceptance criteria met _(AC1–4 met; AC5 genuinely pending a real merge-then-release cycle — see Live Confirmation Status)_
- [x] Tests passing (199/199, zero regressions)
- [x] Code reviewed ([review agent](dff9c538-08b7-459f-bf9c-95ebf9110d08) — PASS, one Small drift item logged as DEV-004)
- [x] Documentation updated (this story file's Live Confirmation Status; Story 3 already updated `.writ/docs/spec-lifecycle.md` and `README.md` for the hook itself)

## Context for Agents

- **Business rules:** [Rule 3 (ambiguous/absent resolution always skips), Rule 5 (reuses `scripts/archive-sweep.py`'s move mechanism, same idempotency check), Rule 7 (never blocks a release)] — from spec.md → 📋 Business Rules
- **Shadow paths:** [No spec resolves (common case, silent skip), Ambiguous match (silent skip), Not-yet-complete-family spec (silent skip, re-checked on future runs), Already-archived spec (no-op), `git mv` failure (skip and continue)] — from spec.md → ## 🎯 Experience Design → ### Error / Edge Experience
- **Success criteria:** [Criterion 1 (single-spec archive on merge), Criterion 2 (no-op indistinguishable from hook-less run), Criterion 3 (idempotent re-run), Criterion 4 (PR-annotated vs. unannotated ledger lines), Criterion 5 (no gate regression)] — from spec.md → ## Success Criteria
- **Origin / motivating gap:** [Real prior incident: `2026-08-04-spec-lifecycle-archival` shipped and released while `Complete`, never archived] — from spec.md → ## Origin and ## Why This Exists
- **Implementation approach:** [Story 4 dependency on Story 3, dogfood scope description] — from spec.md → ## Implementation Approach (item 4)

---

## What Was Built

**Implementation Date:** 2026-08-04

### Files Created

1. **`scripts/_archival_hook_model.py`** (159 lines) — Shared composition model extracted out of `scripts/tests/test_release_archival_hook.py`. Contains `run_archival_hook()` (models Step 1.3c's exact resolve → archive-call control flow) plus its fixture helpers (`init_repo`, `make_spec`, `commit_all`, `empty_knowledge_dir`, `fixed_output_script`, `fake_matched_resolver`, `_run_git`). Single source of truth for both the pytest suite and the new eval script below — no second copy exists anywhere (independently confirmed via a repo-wide grep for `run_archival_hook`).
2. **`scripts/eval-post-merge-archival.py`** (110 lines) — 2 smoke-level PASS/FAIL scenarios (happy-path archive, no-match skip) importing the shared model, exercised under `eval.sh`'s scenario-TSV harness. Its own docstring is explicit that it deliberately does not re-derive Story 3's 11-case matrix — that duplication risk was the architecture check's primary finding.
3. **`scripts/eval-post-merge-dogfood.py`** (95 lines) — Real-repo AC5 readiness probe. Greps committed history for the hook's exact commit-message pattern (`chore(archive): auto-archive <spec> via PR #<n>`) per motivating spec, never directory existence — so the pre-existing manual `/status --archive` move of `2026-08-04-spec-lifecycle-archival` sitting uncommitted in this repo's working tree is correctly never counted. Always exits 0 today ("0 of 2"); deliberately **not** registered in `eval.sh`'s `CHECKS=()` — its own docstring documents the exact flip-and-register steps for once real evidence exists.

### Files Modified

- **`scripts/tests/test_release_archival_hook.py`** (Owned) — Refactor-only: replaced its own local definitions of `run_archival_hook()` and all 7 fixture helpers with an `importlib` load from the new shared module. All 11 original tests and their assertions are byte-identical to the Story 3 commit (`a7a0bba`) except for the module-loading boilerplate itself — independently confirmed by both the review agent and the testing agent via diff, not just the coding agent's claim.
- **`scripts/eval.sh`** (Owned — one entry + one function only) — Added `post-merge-archival` to the `CHECKS=()` array (immediately after `archive-dogfood`) and `check_post_merge_archival()` (immediately after `check_archive_dogfood()`), structurally identical to the file's other archive-family checks. The function's real payload is 7 `require_literal`/`forbid_literal` pins on `commands/release.md`'s actual Step 1.3c prose — every one independently verified present (or, for the one `forbid_literal`, absent) verbatim in the file today by both the review and testing agents.
- **`.writ/specs/2026-08-04-post-merge-archival-hook/user-stories/story-4-dogfood-and-verify.md`** (this file) — Added the `### Live Confirmation Status` subsection (by the coding agent); status header, task checkboxes, and Definition of Done flipped to reflect the delivered scope (by the orchestrator, post-review, closing DEV-004).
- **`.writ/specs/2026-08-04-post-merge-archival-hook/user-stories/README.md`**, **`spec.md`**, **`.writ/context.md`** (by the orchestrator) — rollup/status updates to 4/4 stories, spec marked Complete (all 5 numbered Success Criteria fixture-satisfied; AC5 tracked as an open, non-blocking follow-up here).

### Implementation Decisions

This story's architecture-check agent returned **CAUTION** with 6 findings, all folded into the coding agent's task list before implementation began — the story file's original 7-task list would have substantially duplicated Story 3's existing coverage:

1. **Shared-model extraction (primary finding).** `test_release_archival_hook.py` was already a pure CLI-boundary test, not an internals test — a naive `eval-post-merge-archival.py` mirroring Story 2's dual-coverage pattern would have re-implemented the same 11 scenarios almost verbatim. Resolved by extracting the composition model into `scripts/_archival_hook_model.py`, making both consumers import rather than duplicate.
2. **Prose-pinning as the eval script's real payload, not fixture replay.** The check's genuinely new, non-duplicative value is guarding `release.md` Step 1.3c's actual prose against silent regression — nothing else in the suite did this. Narrowed Task 4.1 to 2 smoke scenarios plus 7 `require_literal`/`forbid_literal` pins, rather than an 11-case re-derivation.
3. **Task 4.4 reframed from re-verification to durable encoding.** Story 3's own Task 3.7 had already closed the "no regression to non-firing gate behavior" diff claim; re-running it from scratch would have been redundant motion. Reframed to confirm the existing claim still holds (`git show`) and fold it into automatically-enforced literal pins on the original three-row test-skip table.
4. **AC5 anti-false-positive guard.** This repo's own working tree shows `2026-08-04-spec-lifecycle-archival` mid-move via a manual `/status --archive` invocation that pre-dates Story 3/4 entirely. Explicit guard added (both in the dogfood probe's commit-message-pattern grep and in the story file's own Live Confirmation Status prose) against ever crediting that move toward AC5.
5. **Dogfood stub must never hard-fail by default.** Unlike `eval-archive-dogfood.py` (written *after* its real sweep had already happened), this story's live event hasn't occurred yet. `eval-post-merge-dogfood.py` was required to default to a non-failing "0 of 2" state and stay unregistered in `CHECKS=()` — a hard-fail-by-default stub would have broken every future contributor's `eval.sh` run indefinitely.
6. **`eval.sh` insertion placement.** Low risk, but the new check/function were placed adjacent to the existing archive-family checks (`archive-sweep`, `archive-dogfood`) rather than appended at file-end, matching the file's existing grouping convention.

**Boundary override applied:** `scripts/archive-sweep.py`, `scripts/resolve-spec-reference.py`, and `commands/release.md` remained explicit **Readable-only** (established by Story 3, carried forward here) — confirmed zero modifications to any of the three across the full pipeline via `git show bed04bb --stat`.

### Test Results

**Verification:** Full `scripts/tests/*.py` pytest suite — 199/199 passing, zero regressions from the Task 4.0 extraction. Independently re-run by the coding agent, the review agent, and the testing agent, each in their own fresh isolated venv.
**Coverage:** `scripts/_archival_hook_model.py` — 100% line (53/53 statements) and 100% branch (6/6) coverage, confirmed via `coverage run --branch --include`. The two new `eval-*.py` scripts follow this repo's established convention of being exercised via `eval.sh`'s scenario harness and direct execution rather than line-coverage-enforced, matching `eval-archive-sweep.py`/`eval-archive-dogfood.py`'s precedent (confirmed, not assumed, by the testing agent).
- ✅ AC1–4 each independently confirmed to have genuine test/assertion backing (not prose-only) by both the review and testing agents — see the story's own Acceptance Criteria checkboxes above for the specific tests backing each.
- `bash scripts/eval.sh --check=post-merge-archival` exits 0 (2/2 scenarios, 0 findings). `python3 scripts/eval-post-merge-dogfood.py` exits 0, correctly reports "0 of 2," confirmed absent from `CHECKS=()`.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration (no review-fail cycles)
- **Drift:** Small (2 items total — 1 from the review agent, DEV-004, closed by the orchestrator post-review; see Deviations below)
- **Security:** Clean — no user-controlled subprocess arguments beyond what Story 3 already established; the dogfood probe's `git log --grep` uses a fixed local pattern, no injection surface; no secrets, no new network calls
- **Boundary Compliance:** All changes confined to the documented Owned file set; `archive-sweep.py`, `resolve-spec-reference.py`, `release.md` confirmed untouched via commit-stat diff

### Deviations from Spec

- **[DEV-004] Story-4 tracking metadata (status header, task checkboxes, rollups) not updated to reflect completed work** — Severity: Small
  - Spec said: Story 4's own Definition of Done, and the established convention from Stories 1–3, of flipping status headers and checking task boxes on story close.
  - Reality: The coding agent delivered the substantively-narrowed Task 4.0–4.7 scope correctly (independently confirmed by review) but left the story's status header, all seven original (superseded) task checkboxes, and `README.md`/`spec.md`'s rollups stale.
  - Resolution: Auto-amended by the orchestrator immediately following review PASS — see `drift-log.md` DEV-004 for the full record. Story status flipped to Completed ✅, task list replaced with the actual delivered 8-item list, `README.md` updated to 4/4 stories, `spec.md` marked Complete.
  - Spec amendment: None needed to `spec.md`'s contract terms — this was tracking hygiene, not a contract deviation.

### Lessons Learned

1. **Architecture-check-driven task revision compounds across stories.** All four stories in this spec had their task lists materially revised by their own architecture checks before coding began — a pattern worth naming explicitly for future multi-story specs: budget for a scope-narrowing pass between story authoring and coding, not just a rubber-stamp PROCEED.
2. **Test-file "duplication" risk is easy to underestimate at spec-authoring time.** Story 4's story file, written before Story 3 existed, couldn't have known Story 3's eventual test file would already be a pure CLI-boundary test. Specs that plan a "verify the prior story" story should expect its scope to shrink once the prior story's actual test shape is known — this isn't scope creep to resist, it's the process working as intended.

### Next Story

None — this is the spec's closing story. All 5 of `spec.md`'s numbered Success Criteria are now fixture-satisfied. Story 4's own AC5 (real-world archival of this spec and `2026-08-04-spec-lifecycle-archival`) remains an honestly-tracked, non-blocking follow-up in this section's Live Confirmation Status — to be closed by whoever runs the next real `/release` after either spec's PR merges, following `scripts/eval-post-merge-dogfood.py`'s own docstring instructions to flip its `main()` return and register it in `eval.sh`.
