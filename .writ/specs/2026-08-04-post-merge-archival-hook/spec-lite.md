# Post-Merge Archival Hook (Lite)

> Source: .writ/specs/2026-08-04-post-merge-archival-hook/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** A scoped, single-spec archival hook inside `/release` Step 1.3c that fires when a merged PR's `HEAD` SHA matches — reuses that existing merged-PR signal, resolves the PR's spec via a shared heuristic `/ship` already uses, and archives that one spec if (and only if) it's already complete-family status.

**Implementation Approach:**
- Extract `/ship`'s branch-name/story-file Spec Reference resolution into a shared, callable form both `ship.md` and `release.md` reference identically.
- Add a single-spec entry point to `scripts/archive-sweep.py` (reuses the existing `git mv` + `LEDGER.md` move logic, just scoped to one named spec instead of a full scan).
- Wire it into `/release` Step 1.3c: when `LAST_MERGED_SHA == HEAD_SHA`, resolve the merged PR's spec, check complete-family status, archive if eligible.
- Stateless by design — no new persistent file; everything re-derives from git/`gh` at `/release` run time (so it works even if `/ship` and `/release` run in different sessions/machines).

**Files in Scope:**
- `commands/ship.md` — factor out the Spec Reference resolution so it's reusable, not just inline prose.
- `commands/release.md` — Step 1.3c gains the merged-PR archival check.
- `scripts/archive-sweep.py` — new single-spec move entry point, PR-number ledger annotation.
- `.writ/specs/archive/LEDGER.md` — line format gains an optional `via PR #N` field (backward-compatible; sweep-originated lines stay unannotated).

**Error Handling:**
- No spec resolves, or resolution is ambiguous → skip silently, no output.
- Resolved spec not yet complete-family → skip (never triggers on story-level completion).
- Already archived → no-op (idempotent).
- `git mv` conflict → skip that spec, never block `/release`'s own flow.
- `--skip-gate` → hook doesn't run (lives inside the same gate as the SHA check).

**Integration Points:** `/release` Step 1.3c (existing `LAST_MERGED_SHA`/`HEAD_SHA` comparison); `scripts/archive-sweep.py` (existing move/ledger mechanism from `2026-08-04-spec-lifecycle-archival`).

---

## For Review Agents

**Acceptance Criteria:**
1. `/release` archives exactly the one spec resolved from a just-merged PR when that spec is already complete-family — no other spec touched, no batch scan triggered.
2. When no spec resolves or resolution is ambiguous, `/release`'s output and behavior are byte-for-byte identical to a run with this hook absent.
3. Re-running `/release` after a hook-triggered archive is a clean no-op.

**Business Rules:**
- Trigger = whole-spec status only, never per-story (Business Rule 1).
- Scope = exactly one spec per merged PR, never a batch — `/status --archive` remains the batch tool, unchanged (Business Rule 2).
- Ambiguous or absent resolution always skips, never guesses (Business Rule 3).
- Never rides in the PR diff — only fires once merge is independently confirmed (Business Rule 4).
- Reuses `scripts/archive-sweep.py`'s existing move mechanism rather than reimplementing it (Business Rule 5).
- Spec Reference resolution must be one shared implementation `/ship` and `/release` both call, not two drifting copies (Business Rule 6).
- Never blocks a release — any resolution or archival failure is caught and skipped (Business Rule 7).

**Experience Design:**
- Entry: no new flag/command — extends `/release`'s existing Step 1.3c merged-PR check.
- Happy path: PR merges → next `/release` run resolves its spec → archives if complete-family → annotated ledger line.
- Moment of truth: a spec goes Complete, ships, releases, and is already archived — no separate manual step required.
- Feedback: silent — ledger entry is the only trace, no prompt, no new PR-body or release-summary section.
- Error: silent skip in every failure/ambiguity mode; never blocks the release itself.

---

## For Testing Agents

**Success Criteria:**
1. Single-spec archival fires correctly when `LAST_MERGED_SHA == HEAD_SHA` and exactly one complete-family spec resolves.
2. Zero side effects when zero or multiple specs resolve.
3. Idempotent re-run produces no duplicate ledger entries or errors.
4. `LEDGER.md` parses correctly whether or not the PR-number annotation is present (backward compatibility with existing sweep-originated lines).
5. No regression to `/release`'s existing gate (spec metadata, build verification, conditional test suite) when the hook is present but doesn't fire.

**Shadow Paths to Verify:**
- **Happy path:** one spec resolves, is complete-family, gets archived with `via PR #N` ledger line.
- **Nil input:** no merged-PR SHA available (`gh` unavailable) → hook doesn't run, same as today's test-skip fallback.
- **Empty input:** PR resolves to zero specs → silent no-op.
- **Upstream error:** `git mv` fails mid-move → that spec skipped, `/release` continues.

**Edge Cases:**
- PR references multiple specs → skip (ambiguous), never pick one arbitrarily.
- Spec already archived by a prior manual sweep → no-op, not an error.
- Story-level completion within a still-open spec → never triggers.
- `/release --skip-gate` → hook does not run.

**Coverage Requirements:**
- New code: ≥80%
- Critical paths (resolution ambiguity, idempotency): 100%
- Error paths (git mv failure, missing gh data): 100%

**Test Strategy:**
- Unit tests for the shared Spec Reference resolution (branch name / story-file matching, ambiguous-match cases).
- Unit tests for `scripts/archive-sweep.py`'s new single-spec entry point (eligible, ineligible, already-archived, collision cases).
- Integration test: fixture repo with a merged PR referencing a complete-family spec, verify `/release`'s Step 1.3c archives it and annotates the ledger.
- Dogfood: real run against this repo once `2026-08-04-spec-lifecycle-archival` and this spec itself each reach `Complete` and merge.
