# Spec: Post-Merge Archival Hook

> **Status:** In Progress (1/4 stories complete)
> **Owner:** @AdamSellke
> **Created:** 2026-08-04
> **Dependencies:** [2026-08-04-spec-lifecycle-archival]
> **Extends:** [2026-08-04-spec-lifecycle-archival](../2026-08-04-spec-lifecycle-archival/spec.md)
> **Origin:** Live evidence during `/ship` + `/release` of the `2026-08-04-spec-lifecycle-archival` amendment: the spec defining archival eligibility went `Complete`, shipped, and released — and stayed unarchived through both, because nothing besides an explicitly-invoked `/status --archive` ever checks. Discussion converged on a scoped, single-spec hook rather than reopening the batch-sweep design.

## Contract (Locked)

**Deliverable:** A scoped, single-spec archival hook that fires once a spec's own PR is confirmed merged — a second, narrow invocation path alongside the existing `/status --archive` batch sweep, not a replacement for it.

**Must include:** Reuse of `/release`'s existing merged-PR detection (Step 1.3c: `LAST_MERGED_SHA` vs `HEAD_SHA`) instead of new persistent cross-command state. Archival of at most the one spec resolved from the merged PR — same Spec Reference heuristic `/ship` already uses to populate its PR body. The archived spec must already be complete-family status; the hook never advances or infers status. Ledger line annotated with the triggering PR number.

**Hardest constraint:** The trigger point cannot live inside `/ship`'s own synchronous run — `/ship` opens a PR and stops; it does not merge. "After merge" has to piggyback on whichever command first observes the merge, which today is `/release`'s existing Step 1.3c check.

## Why This Exists

`2026-08-04-spec-lifecycle-archival` made archival eligibility status-alone and removed the two-signal gate that had left 36 of 39 real Complete specs stranded — but the *invocation* model stayed unconditionally manual (Business Rule 2: "the sweep only ever runs when `/status --archive` is invoked"). That's not a hypothetical gap. In the same session that amendment was written, tested, shipped via `/ship`, and released via `/release`, the amendment's own spec — `2026-08-04-spec-lifecycle-archival` — sat at `Complete` status through both the PR merge and the version tag, never archived, because nobody separately remembered to run `/status --archive` afterward.

A blanket fix — running the full batch sweep automatically inside `/ship` or `/release` — was considered and rejected in discussion. The batch sweep just proved, in this same session, that it can break unrelated things at scale: archiving 36 specs at once surfaced 3 eval checks with hardcoded pre-archive paths that had gone unnoticed for months. Gluing that blast radius into every ship or release run trades a rare manual-maintenance failure for a routine automated one.

The narrower fix — archive *only the one spec this PR just finished*, only after the merge is confirmed, only if that spec was already complete-family before the PR closed — has none of that blast radius. It's the same causal event (a spec's last piece of work landing) that already makes `/ship`'s own "Spec Reference" resolution meaningful; this spec closes the loop `/ship` already opens.

## 🎯 Experience Design (CLI / dogfooding — no user-facing UI)

### Entry Point

No new flag, no new command. `/release`'s existing Step 1.3c (`LAST_MERGED_SHA` vs `HEAD_SHA` comparison, already run for the test-skip heuristic) gains one additional consequence when the two match: resolve the merged PR's spec reference and check archival eligibility.

### Happy Path

1. `/ship` opens a PR; its existing Spec Reference resolution (branch name / story-file match against `.writ/specs/`) identifies which spec, if any, this PR's work belongs to — unchanged from today.
2. Later, `/release` runs. Step 1.3c already fetches the last merged PR's SHA and compares it to `HEAD`.
3. When they match, `/release` re-resolves that merged PR's Spec Reference using the same heuristic `/ship` uses (extracted so both commands share one implementation, not two drifting copies).
4. If a spec resolves unambiguously **and** its status is already complete-family **and** it is not already under `.writ/specs/archive/`, it is `git mv`'d there — identical mechanism to the existing sweep (`scripts/archive-sweep.py`), just invoked for one named spec instead of a full scan.
5. The move appends one line to the existing `.writ/specs/archive/LEDGER.md`, annotated with the triggering PR number (e.g. `... (via PR #32)`), distinguishing it from `no knowledge evidence yet` sweep-originated lines.
6. `/release` continues its own flow unchanged — no new terminal section, no new user-facing step. The archived-spec commit rides alongside the version-bump commit, both direct-to-`main`, same pattern `/release` already uses.

### Moment of Truth

Never seeing another `2026-08-04-spec-lifecycle-archival`-shaped gap — a spec goes `Complete`, ships, releases, and is *already* archived by the time anyone thinks to check, with zero new steps for the maintainer to remember.

### Feedback Model

Silent, same philosophy as the existing sweep (Business Rule 3 of the parent spec): no prompt, no new PR-body section, no new release-summary line. The committed, PR-annotated ledger entry *is* the audit trail. If nothing resolves, nothing happens and nothing is reported — this is a best-effort closer of a loop, not a required step.

### Error / Edge Experience

| Situation | Behavior |
|---|---|
| No spec resolves from the merged PR (the common case — most PRs aren't spec work) | Skip silently. No note anywhere. |
| Spec Reference resolves to more than one spec | Skip silently — ambiguous match is treated the same as no match, never a guess. |
| Resolved spec exists but is not yet complete-family (e.g. only one story of several merged) | Skip. This hook never triggers on story completion, only whole-spec completion — re-checked on every future `/release` run until it eventually resolves true or the spec is manually archived first. |
| Resolved spec is already archived | No-op — same idempotency guarantee `scripts/archive-sweep.py` already provides for the batch sweep. |
| `git mv` fails (dirty tree, path collision) | Skip and continue `/release`'s own flow uninterrupted — this hook must never block a release. |
| `--skip-gate` passed to `/release` | Hook does not run — it lives inside the same gate machinery that computes `LAST_MERGED_SHA`, so skipping the gate skips this too. |

## 📋 Business Rules

1. **Trigger is whole-spec status, never story-level.** The hook checks the resolved spec's own `Status:` header via the existing format-tolerant detector (`scripts/spec-status.py`) — the same gate the batch sweep uses. A spec with some stories done and others open is never archived by this hook, no matter how many of its stories a given PR closed.
2. **Scope is exactly one spec per merged PR, never a batch.** This hook does not scan `.writ/specs/` broadly and never substitutes for `/status --archive`; the two coexist. If a maintainer wants every eligible spec swept, `/status --archive` remains the tool for that.
3. **Ambiguous or absent resolution always skips, never guesses.** No spec, or more than one candidate spec, is treated identically to "nothing to do here" — consistent with the parent spec's conservative-default philosophy for missing status headers.
4. **Never rides in the PR diff.** The move only happens once `/release` independently confirms the PR is merged (`HEAD` matches the merged SHA) — it can never be part of the PR's own commits, which would defeat the "confirmed merged" precondition entirely.
5. **Reuses, does not duplicate, `scripts/archive-sweep.py`'s move mechanism.** Same `git mv`, same `LEDGER.md`, same idempotency check. This spec adds a single-spec entry point and a PR-number-aware ledger annotation; it does not reimplement the move logic.
6. **Spec Reference resolution becomes a shared, callable heuristic.** Today it exists only as prose inside `commands/ship.md`. This spec extracts it (script or clearly factored shared logic) so `commands/release.md` can call the identical resolution `/ship` already performs, rather than hand-rolling a second, potentially-drifting copy.
7. **Never blocks a release.** Any failure in resolution or archival (ambiguous match, `git mv` conflict, missing ledger) is caught and skipped, not raised — `/release`'s own gate and changelog/version/tag flow proceed unaffected either way.

## Detailed Requirements

### Shared Spec Reference resolution

Extract the branch-name / story-file matching heuristic `commands/ship.md` uses today for its PR body's "Spec Reference" section into a form `commands/release.md` can invoke identically — either a small script (mirroring `scripts/archive-sweep.py`'s shape) or a clearly-labeled shared prose procedure both command files reference by name, so the two never silently diverge.

### Merged-PR archival check (`/release` Step 1.3c extension)

After computing `LAST_MERGED_SHA` and `HEAD_SHA` (existing logic, unchanged), when they match: resolve the merged PR's spec via the shared heuristic above. If resolution is unambiguous, call `scripts/archive-sweep.py`'s single-spec move path (new: an entry point that takes one spec name rather than scanning all of `.writ/specs/`) with the PR number passed through for ledger annotation.

### Ledger annotation format

Extend the existing `LEDGER.md` line format to optionally record a triggering PR number alongside the existing knowledge-evidence field, e.g.:

```
2026-08-04-example-spec | no knowledge evidence yet | via PR #32 | 2026-08-04T20:00:00Z
```

Sweep-originated lines (from `/status --archive`) continue to omit the PR field entirely — the format must stay backward-compatible with every existing `LEDGER.md` line written by the parent spec's mechanism.

### Idempotency and no-op safety

The single-spec move path must perform the same existence/collision checks `scripts/archive-sweep.py`'s batch scan already does — re-running `/release` after a spec has already been archived (by this hook or by a manual sweep) must be a clean no-op, never an error.

## Implementation Approach

1. **Extract the shared Spec Reference resolution** (Story 1) — has no dependents blocked on it existing first in principle, but every other story needs it to call into, so it lands first.
2. **Single-spec archive entry point in `scripts/archive-sweep.py`** (Story 2) — depends on nothing new, can proceed in parallel with Story 1.
3. **Wire the hook into `/release` Step 1.3c** (Story 3) — depends on both Story 1 (resolution) and Story 2 (move mechanism).
4. **Dogfood** (Story 4) — depends on Story 3. Verify against this repo: confirm `2026-08-04-spec-lifecycle-archival` and `2026-08-04-post-merge-archival-hook` itself eventually archive correctly once each reaches `Complete` and its PR is merged, without a full `/status --archive` sweep.

## Success Criteria

1. Running `/release` after merging a PR whose resolved spec is complete-family actually archives that one spec, with no other spec touched.
2. Running `/release` when no spec resolves, or resolution is ambiguous, produces zero archival side effects and zero new output — indistinguishable from today's `/release` run.
3. Re-running `/release` after a hook-triggered archive is a clean no-op (idempotency parity with the existing batch sweep).
4. `LEDGER.md` lines written by this hook are annotated with the triggering PR number; lines written by `/status --archive` remain unannotated, and both formats parse under the same ledger-reading logic.
5. No regression to `/release`'s existing gate behavior (spec metadata validation, build verification, conditional test suite) when this hook is present but does not fire.

## Technical Concerns (surfaced at contract time)

- **`/release` can run outside the session that ran `/ship`.** A different machine, a different day, even a different person can run `/release`. The design deliberately avoids any state file for this reason — everything the hook needs (merged PR metadata, current spec statuses) is re-derived from already-available git/`gh` state at the moment `/release` runs, never carried over from a prior `/ship` invocation.
- **Spec Reference resolution is a heuristic, not a guarantee.** Branch-name and story-file matching can occasionally be ambiguous or wrong by coincidence (e.g. a branch name that happens to contain a spec-folder-like string but isn't actually about that spec). Business Rule 3's "skip on ambiguity" is the safeguard — a false skip costs nothing (the batch sweep still catches it later); a false archive would be the failure mode worth avoiding, so the heuristic is deliberately conservative.
- **This does not change `/ship`'s synchronous flow.** No merge-polling, no waiting, no new step added to `ship.md` itself — `/ship` continues to open a PR and stop, exactly as documented today. All new behavior lives in `/release`.

## Scope Boundaries

**Included:** shared Spec Reference resolution usable by both `ship.md` and `release.md`; a single-spec archive entry point in `scripts/archive-sweep.py`; the merged-PR-triggered hook inside `/release` Step 1.3c; PR-number ledger annotation; one dogfooding run against this repo's own specs (including this spec and its parent, once each reaches `Complete`).

**Excluded, deliberately:**

- **Any change to `/ship`'s own synchronous flow.** No merge-waiting, no new `/ship` flag, no archival attempt before merge is confirmed.
- **Story-level or partial-spec triggering.** Only whole-spec complete-family status fires the hook — never "this PR closed the spec's last story," computed independently of the spec's own status header.
- **Batch archival, or any change to `/status --archive`'s existing behavior.** The two invocation paths coexist; this spec adds a second narrow path, it does not touch or replace the first.
- **New persistent cross-command state files.** Everything is re-derived statelessly from git/`gh` at `/release` run time.
- **A user-facing confirmation, new PR-body section, or new `/release` terminal output.** Silent, ledger-only, consistent with the parent spec's existing no-prompt philosophy.
