# Story 3: Wire the Hook into /release Step 1.3c

> **Status:** Completed ✅ (2026-08-04)
> **Priority:** High
> **Dependencies:** Story 1, Story 2

## User Story

**As a** Writ maintainer running `/release` after merging a spec's PR
**I want to** that spec archived automatically, silently, the moment `/release` confirms the merge
**So that** I never again have a `2026-08-04-spec-lifecycle-archival`-shaped gap where a shipped, released spec sits unarchived because nobody separately remembered to run the sweep

## Acceptance Criteria

- [x] Given `LAST_MERGED_SHA` equals `HEAD_SHA` in `commands/release.md` Step 1.3c, when the merged PR's branch/commit data resolves unambiguously to exactly one spec via Story 1's shared resolver, and that spec's status is already complete-family and it is not already under `.writ/specs/archive/`, then Story 2's single-spec archive entry point is invoked with that spec name and the PR number, and the ledger line is annotated with the triggering PR (e.g. `via PR #32`).
- [x] Given `LAST_MERGED_SHA` equals `HEAD_SHA` but resolution returns "no match," "ambiguous," not-yet-complete-family, or the spec is already archived, when Step 1.3c runs, then no archival side effect occurs and no output (terminal, PR-body, or release-summary) differs from today's `/release` run.
- [x] Given `LAST_MERGED_SHA` does not equal `HEAD_SHA` (the common case), when Step 1.3c runs, then the new hook does not execute at all — behavior is byte-for-byte identical to `/release` before this story, including the existing test-skip heuristic's own log line.
- [x] Given `--skip-gate` is passed to `/release`, when the command runs, then the hook does not execute, because it lives inside the same gate machinery that computes `LAST_MERGED_SHA`.
- [x] Given the hook fires and either resolution or Story 2's archive call throws/fails for any reason (e.g. `git mv` conflict, dirty tree, script error), when that failure occurs, then it is caught and swallowed inside Step 1.3c and `/release`'s gate result, changelog generation, version bump, git tag, and GitHub release steps all proceed exactly as if the hook had not run.

## Implementation Tasks

> **Note:** This story's architecture-check agent returned CAUTION with 5 findings; the task list below reflects the **revised** scope actually implemented (see "What Was Built" for the full rationale). Original wording is preserved via git history in the story file's earlier revisions.

- [x] 3.1 (revised) Write an **executable** fixture test (`scripts/tests/test_release_archival_hook.py`) modeling Step 1.3c's exact resolve → archive-call control flow against the two real CLIs over fixture repos — not a documented matrix — covering: fires and archives (incl. `archived_unlogged`); resolver `none`/`ambiguous` skip; every non-archiving `archive-one` status; exceptions at either CLI boundary
- [x] 3.2 (revised) In `commands/release.md` Step 1.3c, added the hook immediately after the test-skip log line; the archive-move commit fires **immediately inside Step 1.3c** (Phase 1) rather than deferring to Phase 3's version-bump commit, avoiding a dangling uncommitted `git mv` if the release is later cancelled at Step 2.3
- [x] 3.3 (revised — removes duplicated eligibility logic) No separate complete-family/already-archived pre-check added in `release.md` prose; on the resolver's `matched` result, `archive-one` is called directly and the hook branches purely on its returned `status` field, since `archive_one()` already performs both checks internally
- [x] 3.4 Wrapped the entire resolve → archive-call → commit sequence in one best-effort guard so any failure anywhere never propagates and never affects the existing test-skip logging or the rest of the gate
- [x] 3.4b (new — closes a `gh` field gap the architecture check found) Extended the **same** `gh pr list` call's `--json` selector (additive only) to also capture PR number/branch/commits — no second `gh` call introduced
- [x] 3.5 Confirmed by construction: the hook lives entirely inside the same `Unless --skip-gate is set` block gating all of Step 1.3 — no separate `--skip-gate` check needed
- [x] 3.6 (revised — adds a Phase 2 sequencing note) Verified all 5 acceptance criteria via trace-through (independently re-verified by both the review and testing agents); added one sentence to the new hook prose noting Phase 2/Step 2.1's changelog data was already gathered in Step 1.2, before this hook could move a spec folder — Phase 2 itself left untouched
- [x] 3.7 Verified all tests pass (199/199, zero regressions) and confirmed via diff that Phases 2–5 and Steps 1.3a/1.3b are byte-for-byte untouched

## Notes

**Technical considerations:**

- This is an integration story into an existing, already-complex command document. The edit must be additive and scoped to the Step 1.3c subsection — do not restructure Step 1.3c's existing table, log messages, or `--dry-run` preview prose, and do not touch Phase 2–5 (changelog, version bump, tag, publish) at all.
- The hook is informational/best-effort archival, never a gate condition: it must not be able to flip the release gate's pass/fail outcome, and it must not appear in the gate's `--dry-run` preview output (per spec.md's "no new terminal output" rule) — the preview describes gate checks that block; this hook never blocks.
- `--skip-gate` skipping the hook should fall out naturally from placement (the hook lives inside the same 1.3c block that only runs when the gate runs) rather than requiring a second, separate `--skip-gate` check — verify this is actually true structurally, not just asserted.
- The archive-move commit this hook produces (when it fires) rides the same "small commit direct to `main`" pattern `/release` already uses for its version-bump commit (Phase 3, Step 3.2) — no new commit-strategy exception should be introduced.

**Risks / challenges:**

- `commands/release.md` is a markdown workflow document the agent follows, not compiled code — "implementation" here means precise process documentation (so a future agent executing `/release` reliably performs the resolve → check → archive → ledger sequence) plus whatever backing script wiring (Story 2's entry point, Story 1's resolver) actually gets invoked. Ambiguous prose is the primary failure mode, not a runtime bug.
- Highest risk is scope creep: since Step 1.3c already contains nontrivial `gh`/git logic, it's tempting to "clean up" adjacent prose while editing. Resist — the acceptance criteria explicitly require the non-firing path to be byte-for-byte/behaviorally identical to today.
- Second risk is silently weakening the "never blocks" guarantee — e.g. letting an uncaught script exit code from Story 2's entry point propagate into the gate's own failure handling. The guard in task 3.4 must wrap the entire chain, not just the resolver call.

**Integration points:**

- Depends on Story 1's shared Spec Reference resolver (must consume its tri-state `matched`/`none`/`ambiguous` contract exactly, treating `none` and `ambiguous` identically as "skip").
- Depends on Story 2's single-spec archive entry point (must pass the resolved spec name and PR number, and must not reimplement any part of the `git mv` / `LEDGER.md` move logic itself).
- Story 4 (dogfooding) depends on this story — it will run `/release` for real against this repo's own specs to confirm the wiring works end-to-end.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [No spec resolves, Spec Reference resolves to more than one spec, Resolved spec not yet complete-family, Resolved spec already archived, `git mv` fails, `--skip-gate` passed] — from spec.md → ## 🎯 Experience Design → ### Error / Edge Experience (full table applies to this story as the integration point)
- **Shadow paths:** [Happy Path steps 2–6 (Step 1.3c SHA match → re-resolve → complete-family + not-archived check → `git mv` via single-spec entry point → PR-annotated ledger line → `/release` continues unchanged)] — from spec.md → ## 🎯 Experience Design → ### Happy Path
- **Business rules:** [Rule 1 (whole-spec status only, via `scripts/spec-status.py`), Rule 2 (exactly one spec per merged PR, never a batch), Rule 3 (ambiguous/absent resolution always skips), Rule 4 (trigger only after `/release` independently confirms merge — never rides in the PR diff), Rule 7 (never blocks a release — failures are caught and skipped)] — from spec.md → 📋 Business Rules
- **Experience:** [Entry Point (no new flag/command — extends existing Step 1.3c comparison), Feedback Model (silent — no prompt, no PR-body section, no release-summary line), Moment of Truth (spec archived by the time anyone checks, zero new maintainer steps)] — from spec.md → ## 🎯 Experience Design
- **Detailed requirements:** [Merged-PR archival check — exact sequencing of resolve-then-call with PR number pass-through] — from spec.md → ## Detailed Requirements → ### Merged-PR archival check (`/release` Step 1.3c extension)
- **Technical concerns:** [No persistent cross-command state — everything re-derived from git/`gh` at `/release` run time; heuristic is deliberately conservative, false skip costs nothing but false archive would be the failure mode to avoid] — from spec.md → ## Technical Concerns
- **Contract:** [Must include: reuse of existing Step 1.3c detection, not new state; Hardest constraint: "after merge" can only piggyback on whichever command first observes the merge, which today is `/release`'s Step 1.3c] — from spec.md → ## Contract (Locked)
- **Success criteria:** [Criterion 1 (archives exactly the resolved spec, no other spec touched), Criterion 2 (no-match/ambiguous produces zero side effects and zero new output), Criterion 5 (no regression to existing gate behavior when hook doesn't fire)] — from spec.md → ## Success Criteria
- **Codebase anchor:** [`commands/release.md` lines ~119–138, Step 1.3c — existing `LAST_MERGED_SHA`/`HEAD_SHA` comparison this story extends]

---

## What Was Built

**Implementation Date:** 2026-08-04

### Files Created

- **`scripts/tests/test_release_archival_hook.py`** (Owned) — 11 executable pytest fixture tests. Defines `run_archival_hook()`, a helper that models Step 1.3c's exact resolve → archive-call control flow and drives it against the real `resolve-spec-reference.py` and `archive-sweep.py` CLIs via subprocess over real fixture git repos — since `commands/release.md` is a prose document with no importable module, this helper is this story's de facto "new production code."

### Files Modified

- **`commands/release.md`** (Owned — Step 1.3c only) — Two hunks: (1) extended the existing single `gh pr list` call's `--json` selector (additive: `mergeCommit,number,headRefName,commits`) to capture the PR number/branch/commits the hook needs, without adding a second `gh` call; (2) replaced the prior "documentation only — no trigger here" closing sentence with the fully wired hook — resolve via Story 1's script, branch on `matched`, call Story 2's `archive-one` directly, branch purely on its returned `status`, commit immediately on `archived`/`archived_unlogged`. Phases 2–5 and Steps 1.3a/1.3b confirmed byte-for-byte untouched (verified independently by the review and testing agents, not just the coding agent's own claim).
- **`.writ/docs/spec-lifecycle.md`** — new paragraph in the Archive Eligibility section documenting this second, narrower trigger path alongside the pre-existing `/status --archive` batch path.
- **`README.md`** — one-clause addition to the `/release` command-table row noting the new silent auto-archival behavior.
- **`.writ/specs/2026-08-04-post-merge-archival-hook/drift-log.md`** — DEV-003 entry (Small, auto-amended).

### Implementation Decisions

This story's architecture-check agent returned **CAUTION** with 5 findings, all folded into the coding agent's task list before implementation began (rather than implementing the story file's original wording verbatim):

1. **No duplicated eligibility logic (primary finding).** The story file's original Task 3.3 read as instructing a *second* complete-family/already-archived pre-check in `release.md`'s prose, ahead of calling `archive-one` — which already performs both checks internally and is fully tested for them. Revised: call `archive-one` directly on `matched`, branch purely on its returned `status`. Avoids the exact "second, drifting implementation" pattern this whole 4-story spec exists to eliminate.
2. **Commit timing resolved in favor of immediacy, not deferral.** The technical spec's "sequenced immediately before or after" the Phase 3 version-bump commit language permitted either ordering, but deferring the *commit* to Phase 3 while the `git mv` happens synchronously in Phase 1 would leave a dangling uncommitted rename if the user cancels the release at Step 2.3's confirmation gate — a real, reachable, untested path. Resolved: commit immediately inside Step 1.3c when `status` is `archived` or `archived_unlogged`.
3. **`gh pr list` field gap closed additively.** The original call only fetched `mergeCommit` — neither the PR number nor branch/commits (both needed by the resolver and `archive-one`) were actually available. Extended the same call's `--json` selector rather than adding a second `gh pr view` call.
4. **Executable test required, not a prose matrix.** The story file's Task 3.1 hedged with "or... a documented verification matrix." Since all the real logic here is composing two already-tested, already-CLI-callable scripts, an executable fixture test was clearly feasible and was required instead — closing what would otherwise have been an unverified composition until Story 4's live dogfood run.
5. **Phase 2 sequencing risk closed with a one-sentence note, not a Phase 2 edit.** The changelog data Step 2.1 (Phase 2) consumes is gathered earlier in Step 1.2 (Phase 1), before this hook could move a spec folder to `archive/` — but this wasn't previously a stated invariant. Added one clarifying sentence to the *new* Step 1.3c hook prose (in scope) rather than editing Step 2.1 itself (explicitly out of scope per the story's own Notes).

**Boundary override applied:** `scripts/archive-sweep.py` and `scripts/resolve-spec-reference.py` were demoted from the story's original implicit "Owned-if-touched" status to explicit **Readable-only** by the architecture check, since both are fully implemented and tested by Stories 1/2. Confirmed zero modifications to either file across the full pipeline.

### Test Results

**Verification:** Full `scripts/tests/*.py` pytest suite — 199/199 passing (188 pre-existing + 11 new), zero regressions. Independently re-verified by the orchestrator in a separate fresh venv before review, and again by the testing agent in its own isolated venv.
**Coverage:** 100% line and 100% branch coverage on `run_archival_hook()` — every resolver outcome (`matched`/`none`/`ambiguous`), every `archive-one` status bucket, and the exception-guard path are each independently exercised.
- ✅ All 5 acceptance criteria verified — 3 via direct fixture test, 2 (SHA-mismatch scoping, `--skip-gate` scoping) via independent trace-through of `commands/release.md`'s actual prose, performed separately by the review agent and the testing agent (not just repeating the coding agent's claim)

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration (no review-fail cycles)
- **Drift:** Small (1 item — see Deviations below)
- **Security:** Clean — no `shell=True`, all interpolated bash variables double-quoted, list-form `subprocess.run` throughout the test file
- **Boundary Compliance:** All changes within Owned; both Readable-only backing scripts confirmed untouched

### Deviations from Spec

- **[DEV-003] SHA-extraction mechanism swapped from `gh`'s built-in `--jq` to an external `jq` pipe** — Severity: Small
  - Spec said: Task 3.4b — extend the existing `gh pr list` call's `--json` fields, additive only.
  - Reality: Additive in effect, but the *mechanism* changed — the prior line used `gh pr list --json mergeCommit --jq '...'` (gh's built-in JSON engine); the new line pipes raw JSON through the external `jq` binary instead, needed to extract four independent fields in one call.
  - Resolution: Auto-amended — added a clarifying note below Step 1.3c's bash block documenting the external-`jq` dependency and its fail-safe degradation, consistent with Step 3.1's existing external-`jq`-with-fallback assumption elsewhere in the same file. No code change requested by the review agent.
