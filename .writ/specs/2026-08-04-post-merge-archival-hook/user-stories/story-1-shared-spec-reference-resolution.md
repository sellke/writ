# Story 1: Shared Spec Reference Resolution

> **Status:** Completed ✅ (2026-08-04)
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer running `/release`
**I want to** the same Spec Reference resolution logic `/ship` already uses to be callable from `/release` too
**So that** `/release` can reliably determine which spec a merged PR belongs to without a second, drifting implementation

## Acceptance Criteria

- [x] Given a branch name or set of recent commit messages that unambiguously match exactly one folder under `.writ/specs/`, when the shared resolution is invoked, then it returns that single spec identifier.
- [x] Given a branch name or commit set that matches zero spec folders, when the shared resolution is invoked, then it returns "no match" rather than guessing.
- [x] Given a branch name or commit set that matches more than one spec folder (or matches one folder via conflicting signals — e.g. branch name suggests spec A but a commit references story files under spec B), when the shared resolution is invoked, then it returns "ambiguous" rather than picking either candidate.
- [x] Given `commands/ship.md`'s Step 5 PR body population, when Spec Reference is populated today's way (post-extraction), then the PR body's `## Spec Reference` section content and the "no spec" / "standalone change" placeholder text are byte-for-byte unchanged from current `/ship` behavior.
- [x] Given `commands/release.md` needs to resolve which spec a just-merged PR belongs to (feeding Story 2's archival hook), when it invokes the shared resolution with that PR's branch name/commit data, then it gets back the identical identifier `/ship` would have produced for that same branch — no separate matching logic exists in `release.md`.

## Implementation Tasks

- [x] 1.1 Write tests for the resolver's three outcomes (single match / no match / ambiguous match) covering exact folder-name match, fuzzy/partial branch-name match, story-file-reference match, and a deliberately conflicting-signal case
- [x] 1.2 Extract the matching heuristic out of `commands/ship.md`'s Step 5 prose into a standalone script (e.g. `scripts/resolve-spec-reference.py`), mirroring `scripts/archive-sweep.py`'s shape: pure functions for matching + a thin CLI (`resolve --branch <name> [--commits <log-text>] --specs-dir <dir>`), one JSON result object, exit 0 always (best-effort resolution, never fail-closed)
- [x] 1.3 Implement the JSON contract with an explicit tri-state result (`matched` / `none` / `ambiguous`), the resolved spec id (when `matched`), and the candidate list (when `ambiguous`) so callers can log *why* it skipped
- [x] 1.4 Update `commands/ship.md` Step 5's Spec Reference row/prose to call the new script instead of describing the heuristic inline, verifying the PR body template's rendered output is unchanged for at least one matched, one unmatched, and one standalone-change case
- [x] 1.5 Add the equivalent invocation to `commands/release.md` (documentation-only in this story — the archival *trigger* is Story 2/3's job) so it references the same script by name for resolving a merged PR's spec, rather than restating the heuristic
- [x] 1.6 Verify acceptance criteria are met against real branch names/commits from this repo's history (e.g. `chore/spec-lifecycle-status-alone-eligibility` → `2026-08-04-spec-lifecycle-archival`)
- [x] 1.7 Verify all tests pass and `/ship`'s Step 5 PR-body output is unchanged via a before/after diff on a sample run

## Notes

**Technical considerations:**

- The resolver must stay conservative: Business Rule 3 ("ambiguous or absent resolution always skips, never guesses") means the `ambiguous` outcome is not a bug to eliminate — it's the safeguard. Don't add tie-breaking logic (e.g. "pick the most recent spec") to force a single answer; surface the tie as `ambiguous` and let the caller skip.
- `/ship`'s existing behavior is a hard constraint, not just a nice-to-have: this is a pure extraction. The PR body's `## Spec Reference` section and the "Standalone change (no spec)" placeholder must render identically before and after — no wording changes, no new sections, no behavior drift for `/ship` users.
- Do not reimplement status classification here. This resolver answers "which spec folder does this branch/PR refer to," full stop — status (`Complete` vs. not) is `scripts/spec-status.py`'s job and is out of scope for this story entirely (Story 2/3 compose the two).
- Match inputs should cover both signals `/ship` already prose-describes: branch name (fuzzy/partial against `.writ/specs/*` folder names) and recent commit messages/story-file references (e.g. a commit mentioning `story-3-session-management.md`). Both signals should be checked; a conflict between them is itself an `ambiguous` result, not a tie-break opportunity.

**Risks / challenges:**

- The current heuristic has never been executable or tested — it's prose. Formalizing it may reveal that real branch names in this repo (and others) are messier than the prose implies (e.g. multi-word slugs, unrelated `chore/` or `fix/` prefixes). Bias test cases toward real repo history rather than synthetic examples to catch this early.
- Risk of scope creep into rewriting `/ship`'s Step 5 section wholesale. Keep the `commands/ship.md` edit surgical: swap the inline heuristic description for a script invocation, touch nothing else in Step 5.

**Integration points:**

- Story 2 (the archival hook trigger inside `/release`'s Step 1.3c merged-PR check) depends directly on this story's script/CLI contract — it will call this resolver with the newly-merged PR's branch name to get the single spec id to archive, and must treat `ambiguous`/`none` as "skip, don't archive" per Business Rule 3.
- Story 3 (if it exists — ledger annotation with triggering PR number) will consume the same resolved spec id this story produces; it does not need its own resolution logic.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** [Rule 3 (ambiguous/absent resolution always skips, never guesses), Rule 6 (Spec Reference resolution becomes a shared, callable heuristic — the primary rule this story implements)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [Shared Spec Reference resolution — extraction target and shape] — from spec.md → ## Detailed Requirements → ### Shared Spec Reference resolution
- **Technical concerns:** [Spec Reference resolution is a heuristic, not a guarantee — conservative-skip rationale] — from spec.md → ## Technical Concerns
- **Contract:** [Must include: "same Spec Reference heuristic `/ship` already uses"; Hardest constraint: heuristic exists only as prose in `commands/ship.md` today] — from spec.md → ## Contract (Locked)

---

## What Was Built

**Implementation Date:** 2026-08-04

### Files Created

- **`scripts/resolve-spec-reference.py`** (Owned) — `resolve_spec_reference(specs_dir, branch=None, commits=None)` pure function plus a thin `resolve` CLI subcommand. Mirrors `scripts/archive-sweep.py`'s shape: one JSON result object, exit 0 always (best-effort, never fail-closed).
- **`scripts/tests/test_resolve_spec_reference.py`** (Owned) — 21 tests total (16 from the coding agent + 5 added by the testing agent to close coverage gaps).

### Files Modified

- **`commands/ship.md`** (Readable→edited per task) — Step 5's "Populating the template" table row for Spec Reference swapped from inline heuristic prose to a call to `scripts/resolve-spec-reference.py`. Surgical: markdown structure and placeholder wording untouched.
- **`commands/release.md`** (Readable→edited per task) — one documentation-only paragraph added after Step 1.3c naming the shared script for a future merged-PR spec lookup. No trigger wiring in this story — that's Story 3's job.

### Implementation Decisions

1. **Two matching signals, deduplicated before counting** — branch name (substring against spec-folder names/slugs, with a last-path-segment fallback to strip common prefixes like `chore/`) and commit-message text (folder-name or story-file substring scan). The same spec surfaced by both signals resolves as `matched`, not `ambiguous`; only genuinely distinct candidates after dedup trigger `ambiguous`, and zero trigger `none` — never a guess.
2. **Story-file signal restricted to `story-N-*.md` filenames, not every `*.md` under `user-stories/`** — dogfooding against this repo's real commit history (Task 1.6) surfaced a false positive: every spec's `user-stories/` folder has a generic `README.md` index file, so any commit merely mentioning "README.md" (extremely common) matched nearly every spec at once. Fixed by restricting the signal to filenames shaped like an actual story file, per the technical spec's own `story-3-session-management.md` example. This was a same-story implementation fix (caught by the story's own Task 1.6 dogfood verification, not a review-fail or spec deviation), so it is not logged in `drift-log.md`.
3. **Graceful degradation throughout** — missing `--specs-dir`, absent branch name, or any unexpected error (including `OSError` in the folder-listing and commit-matching helpers) all degrade to a `none` result rather than raising, consistent with the "best-effort resolver, not a fail-closed validator" contract.

### Test Results

**Verification:** Full `scripts/tests/*.py` pytest suite plus 3 shell-based suites — all passing, zero regressions.
**Coverage:** 100% on `scripts/resolve-spec-reference.py` (initially 75% — CLI smoke tests invoke the script via subprocess, so `main()` and the `__main__` entrypoint never registered with the coverage tool despite being exercised; closed with in-process tests for `main()`'s argparse/print path, its fail-open `except` branch, the `__main__` guard via `runpy`, and both `OSError` degradation branches).
- ✅ 21/21 tests in `test_resolve_spec_reference.py`
- ✅ All 5 acceptance criteria mapped to passing tests, including a real-repo dogfood case (Task 1.6: `chore/spec-lifecycle-status-alone-eligibility` → `2026-08-04-spec-lifecycle-archival`)
- ✅ `/ship`'s Step 5 PR-body output confirmed byte-for-byte unchanged via before/after diff (matched, unmatched, and standalone-change cases)

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration (no review-fail cycles)
- **Drift:** None — zero deviations from spec
- **Security:** Clean — no shell injection surface, no untrusted external input beyond local git branch/commit text already trusted by the calling command
- **Boundary Compliance:** All changes fell within Owned/task-scoped Readable edits; zero touches to Out-of-scope files

### Deviations from Spec

None.
