# Story 2: Single-Spec Archive Entry Point

> **Status:** Completed ✅ (2026-08-04)
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer whose `/release` run just confirmed a PR merged
**I want to** archive exactly one named, already-complete spec with a PR-annotated ledger line
**So that** the archival mechanism can be triggered for a single spec without running the full batch sweep

## Acceptance Criteria

- [x] Given a spec folder under `.writ/specs/<name>/` whose `Status:` header is complete-family per `scripts/spec-status.py`, when the single-spec entry point is invoked with that spec's name, then it performs the identical `git mv` to `.writ/specs/archive/<name>/` and ledger-append that `sweep()` already performs for that spec, moving only that one spec.
- [x] Given a spec folder whose `Status:` header is not yet complete-family, when the single-spec entry point is invoked with that spec's name (even though it was explicitly named), then no `git mv` occurs and the result reports it as skipped, not archived.
- [x] Given a spec that is already archived (present under `.writ/specs/archive/<name>/`, absent from `.writ/specs/<name>/`), when the single-spec entry point is invoked again with that same spec name, then it returns a clean no-op result with no error and no duplicate ledger line.
- [x] Given a spec whose destination path under `.writ/specs/archive/<name>/` already exists but the source `.writ/specs/<name>/` is unexpectedly also still present, when the single-spec entry point is invoked, then it hard-stops that spec as a collision (matching `sweep()`'s existing collision handling) rather than overwriting or silently choosing a side.
- [x] Given the single-spec entry point is invoked with an optional PR number, when the move succeeds, then the appended `LEDGER.md` line carries a `via PR #N` annotation while every ledger line written by the existing `sweep()` path (no PR number passed) remains byte-for-byte unchanged in format.
- [x] Given an existing `LEDGER.md` containing only pre-existing sweep-originated lines (no PR annotation), when a new hook-triggered line is appended alongside them, then the file still parses/reads correctly as a whole — old lines are untouched, not rewritten or reformatted.

## Implementation Tasks

- [x] 2.1 Write tests in `scripts/tests/test_archive_sweep.py` for the new single-spec entry point: eligible-and-complete (archives), not-yet-complete (skips even when named explicitly), already-archived (idempotent no-op), destination collision (hard stop, reported not raised), and PR-number-annotated vs. unannotated ledger line output
- [x] 2.2 Add `archive_one(repo_root, specs_dir, knowledge_dir, spec_name, pr_number=None)` to `scripts/archive-sweep.py`, reusing `_classify_specs`/`find_knowledge_evidence` for the eligibility + evidence lookup on exactly the named spec instead of iterating `scan()`'s full result set
- [x] 2.3 Reuse the exact same collision check, `git mv` subprocess call, and failure handling `sweep()` already uses for a single spec, so behavior (including "skip and report, never raise" on `git mv` failure) stays identical between the batch and single-spec paths
- [x] 2.4 Extend `_append_ledger()` (or thread an optional `pr_number` parameter through it) so the appended line gains a `via PR #N` segment only when a PR number is supplied, leaving the existing sweep-originated call site's output unchanged when it passes none
- [x] 2.5 Add an `archive-one` CLI subcommand (`--specs-dir`, `--knowledge-dir`, `--repo-root`, `--spec-name`, `--pr-number` optional) alongside the existing `scan`/`sweep` subcommands in `main()`, printing the same one-JSON-object-always-exit-0 contract
- [x] 2.6 Verify acceptance criteria are met, including a fixture asserting an existing `LEDGER.md` with only unannotated lines still parses correctly once a `via PR #N` line is appended after it
- [x] 2.7 Verify all tests pass, covering both `archive_one()` called directly and via the new CLI subcommand

## Notes

**Technical considerations:**

- The real `LEDGER.md` line format (see `_append_ledger()` in `scripts/archive-sweep.py`) is `- {timestamp} — \`{spec_id}\` archived (evidence: {evidence_str})\n`, not a pipe-delimited row — the spec.md's illustrative `... | via PR #32 | ...` example is describing the concept, not the literal string. The PR annotation should slot into the existing parenthetical or as a second parenthetical/clause (e.g. `archived (evidence: ...) (via PR #32)`), matching the existing line's actual shape rather than the spec's shorthand example. Confirm the exact placement renders sensibly against real lines already committed in `.writ/specs/archive/LEDGER.md` before finalizing the format.
- No line-parsing/regex code currently reads `LEDGER.md` back in — it's write-only, append-only, human/audit-readable. "Stays backward-compatible" for this story means: existing lines are never rewritten, and the file remains a flat, human-scannable Markdown list after the new line format is mixed in — not that a new parser must be written. Don't invent a parser this story doesn't need.
- Idempotency for the single-spec path is a state check (source path absent + destination present = already archived, no-op), not a ledger-scan — mirrors how `sweep()`'s idempotency already works (an archived spec simply no longer appears in the next `scan()`).
- Collision detection must distinguish "already archived cleanly" (source gone, dest exists → no-op) from "unexpected collision" (source still exists AND dest exists → hard stop) — these are different states with different correct behaviors, unlike `sweep()`'s scan which never encounters "source still exists" for a dest that exists, since eligible specs are always sourced from an active scan of `.writ/specs/`.

**Risks / challenges:**

- Ledger format drift: if the PR-annotation placement doesn't match how a future ledger-reading tool (if one is ever written) expects to find it, backward compatibility is only half the story — forward-compatibility of the *new* format also matters. Keep the annotation as a simple appended clause, not a structural reordering, to minimize the chance any future reader needs two different parse paths.
- `archive_one()` and `sweep()` sharing eligibility/move logic risks silent divergence if refactored carelessly — extract shared helpers (collision check, `git mv` + failure handling, ledger append) rather than copy-pasting `sweep()`'s loop body with a single-item list.

**Integration points:**

- Story 3 (wiring the hook into `/release` Step 1.3c) depends directly on this story: it will call `archive_one()` (or the `archive-one` CLI subcommand) with the spec name resolved by Story 1's shared Spec Reference resolution, plus the merged PR's number. Story 3 does not need to know anything about `git mv`, collision handling, or ledger formatting — this story's contract (input: spec name + optional PR number; output: one JSON result) is the entire surface Story 3 consumes.
- This story does not touch `commands/release.md` or `commands/ship.md` at all — it is purely `scripts/archive-sweep.py` + its test suite.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** [Rule 5 (reuses, does not duplicate, `scripts/archive-sweep.py`'s move mechanism — the primary rule this story implements), Rule 1 (trigger is whole-spec status, never story-level — this story's eligibility check must still gate the move even for an explicitly-named spec), Rule 7 (never blocks a release — collision/`git mv` failures must be skipped and reported, not raised)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [Ledger annotation format — the `via PR #N` extension target and its backward-compatibility constraint; Idempotency and no-op safety — the existence/collision checks this entry point must replicate from the batch scan] — from spec.md → ## Detailed Requirements → ### Ledger annotation format, ### Idempotency and no-op safety
- **Error map rows:** [Resolved spec exists but is not yet complete-family → Skip; Resolved spec is already archived → No-op — idempotent; `git mv` fails (dirty tree, path collision) → Skip and continue, never block] — from spec.md → ### Error / Edge Experience
- **Contract:** [Must include: "Ledger line annotated with the triggering PR number"; Business Rule 5's "same `git mv`, same `LEDGER.md`, same idempotency check" instruction not to reimplement move logic] — from spec.md → ## Contract (Locked)

---

## What Was Built

**Implementation Date:** 2026-08-04

### Files Created

[None created]

### Files Modified

- **`scripts/archive-sweep.py`** (Owned)
  - Added `archive_one(repo_root, specs_dir, knowledge_dir, spec_name, pr_number=None)` — single-spec-scoped sibling of `sweep()`.
  - Extracted `_git_mv()` shared by `sweep()` and `archive_one()` so the two paths cannot silently diverge.
  - Checks destination/source existence first (no subprocess) to separate `already_archived` from a true `collision` before ever touching git or running the completeness check.
  - Falls through to `not_eligible` for a spec name absent from both `specs_dir` and the archive, without crashing.
  - Extended `_append_ledger()` with a trailing, optional `pr_number` parameter (existing positional call site in `sweep()` untouched) — appends a `via PR #N` clause inside the existing evidence parenthetical when supplied; output is byte-for-byte unchanged when omitted. Now returns the line it wrote.
  - Resolved the sub-spec's flagged `[UNPLANNED]` atomicity question (git mv succeeds, ledger append fails): accepted as a rare, recoverable risk, surfaced via a new `archived_unlogged` status rather than rolled back or folded into `archived`/`git_mv_failed`.
  - Added the `archive-one` CLI subcommand (`--specs-dir`, `--knowledge-dir`, `--repo-root`, `--spec-name`, `--pr-number` optional) alongside `scan`/`sweep`.
- **`scripts/tests/test_archive_sweep.py`** (Owned) — 13 new fixture tests (12 from the coding agent + 1 added by the testing agent to close an in-process CLI-coverage gap).
- **`scripts/eval-archive-sweep.py`** (Owned, optional) — 2 new CLI-boundary scenarios (4 PASS lines) for `archive-one`.
- **`.writ/specs/2026-08-04-post-merge-archival-hook/sub-specs/technical-spec.md`** — Error & Rescue Map's `[UNPLANNED]` row resolved and struck; `ArchiveOneResult` illustration corrected to note the actual dict-based return shape and the `archived_unlogged` status.
- **`.writ/specs/2026-08-04-post-merge-archival-hook/user-stories/README.md`** — "Open Technical Decision" section marked Resolved.
- **`.writ/specs/2026-08-04-post-merge-archival-hook/drift-log.md`** — created; logs DEV-001 and DEV-002.

### Implementation Decisions

1. **Result shape** — plain dict keyed `"spec"` (not the technical-spec's illustrative `ArchiveOneResult` dataclass with `spec_name`), matching `scan()`/`sweep()`'s existing convention in the same module. Logged as DEV-001 (Small drift).
2. **Check ordering** — destination/source existence checked before the `_classify_specs()`-based completeness check, per the architecture-check agent's binding recommendation: cheaper, and correctly separates `already_archived` (source absent, dest present) from `collision` (both present) ahead of any subprocess call.
3. **Ledger-append-after-successful-move atomicity** — resolved as option (b) from the sub-spec's `[UNPLANNED]` note: accepted rare-risk, not rolled back, surfaced as a distinct `archived_unlogged` status so callers can tell it apart from a clean archive or a failed move. Rationale documented in `archive-sweep.py`'s module docstring and in `technical-spec.md`.

### Test Results

**Verification:** Full `scripts/tests/*.py` pytest suite (183 tests) plus 3 shell-based suites — all passing, zero regressions.
**Coverage:** 96% file-wide on `scripts/archive-sweep.py`; 100% on all new/modified code (`archive_one()`, `_git_mv()`, extended `_append_ledger()`, `archive-one` CLI wiring).
- ✅ 23/23 tests in `test_archive_sweep.py` (10 pre-existing, unmodified + 13 new)
- ✅ All 6 acceptance criteria mapped to passing tests (see Testing Agent record)
- ✅ Idempotent re-run, collision hard-stop, `git mv` failure, and `archived_unlogged` ledger-failure paths each covered by a dedicated fixture

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration (no review-fail cycles)
- **Drift:** Small (2 items, both auto-amended — see Drift Analysis below)
- **Security:** Clean — all subprocess calls use list-form args, no `shell=True`, no untrusted external input
- **Boundary Compliance:** All changes fell within Owned; zero touches to Readable or Out-of-scope files

### Deviations from Spec

- **[DEV-001] `ArchiveOneResult` implemented as a plain dict with `spec` key, not a dataclass with `spec_name`** — Severity: Small
  - Spec said: Technical spec's illustrative `@dataclass ArchiveOneResult` with a `spec_name` field.
  - Reality: Plain dict with key `"spec"`, matching `scan()`/`sweep()`'s existing convention.
  - Resolution: Auto-amended — `technical-spec.md`'s illustration corrected with an implementation note; no `spec-lite.md` change needed.
- **[DEV-002] Sub-spec's `[UNPLANNED]` atomicity note required explicit resolution** — Severity: Small
  - Spec said: "Resolution required before Story 2 implementation starts... Record the decision in this sub-spec once made."
  - Reality: Decision made and documented in code; the sub-spec itself wasn't updated until Gate 3.5 follow-up.
  - Resolution: Auto-amended — `technical-spec.md`'s Error & Rescue Map row updated to strike `[UNPLANNED]` and cite the `archived_unlogged` resolution.
