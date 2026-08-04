# Pipeline Streamlining

> **Status:** Complete
> **Created:** 2026-03-19
> **Scope:** Refine ship.md, verify-spec.md, release.md

## Contract Summary

**Deliverable:** Streamline the post-implementation pipeline (ship, verify-spec, release) by giving each command a single clear responsibility, eliminating redundant work, and reducing the pre-release ceremony from 5 commands to 2.

**Must Include:** Self-sufficient `/release` with its own conditional gate, `/verify-spec` stripped to pure diagnostic, `/ship` with opt-in testing.

**Hardest Constraint:** Making `/release`'s test run conditional (skip when HEAD matches last merged PR) requires reliable detection via `gh` CLI with a clean fallback.

## Experience Design

**Before (5-command ceremony):**
```
/status → /verify-spec → /verify-spec --pre-deploy → /release --dry-run → /release
```

**After (2-command release):**
```
/release --dry-run → /release
```

**Full pipeline after implementation:**
```
/review (optional) → /ship → /release
```

`/verify-spec` exits the pipeline entirely — it becomes an independent diagnostic you run when you suspect drift, like running a linter. Useful, never blocking.

## Design Principles

1. **Each command owns one job.** Ship creates PRs. Release publishes versions. Verify-spec checks spec hygiene. No command should half-do another's job.

2. **Self-sufficiency over ceremony.** If `/release` needs tests to pass, it runs them itself rather than trusting that the user remembered to run a separate command first.

3. **Smart redundancy, not dumb repetition.** Re-running tests after a merge (in `/ship --test`) is valuable — the merge could break things. Re-running them in a separate verify-spec command after ship already passed them is not.

4. **Behavior matches philosophy.** Ship says "assumes the code is ready." Now it acts like it — tests are opt-in.

## Business Rules

- Trello integration is removed entirely from the pipeline. No Trello references in any command.
- Changelog generation happens exclusively in `/release`. No other command generates CHANGELOG entries.
- The release gate's test run is conditional: skip when HEAD matches the last merged PR's merge commit, run when intervening commits exist.
- Build verification (typecheck, lint, format) always runs in the release gate, even when tests are skipped — these are fast and catch config drift.
- Ship's inline spec health check runs checks 1-3 only (story integrity, status consistency, completion integrity). Not the full verify-spec suite.

## Scope Boundaries

**Included:**
- Rewrite `commands/verify-spec.md` — strip to pure diagnostic
- Rewrite `commands/release.md` — add self-sufficient release gate
- Refine `commands/ship.md` — opt-in tests, inline spec check
- Update cross-references across all pipeline commands

**Excluded:**
- Changes to `/review` (already clean)
- Changes to `/status` (different concern, separate spec)
- Changes to `/implement-story` or `/implement-spec` (upstream, not affected)
- Building any new commands

## Technical Concerns

- **Conditional test detection depends on `gh` CLI:** The release gate uses `gh pr list --state merged --limit 1 --json mergeCommit` to detect the last merged PR. Repos without `gh` fall back to always running tests. This is acceptable — better safe than sorry.

- **Spec metadata validation in two places:** Both `/release` (inline gate) and `/verify-spec` (standalone diagnostic) run checks 1-5 and 8. This is intentional duplication for self-sufficiency, not accidental overlap.

## Cross-Spec Overlap

- `2026-03-15-phase2a-shipping-review` (In Progress, 6/7 stories) created the current `ship.md`. This spec refines its output. No conflict — phase2a built it, this spec tightens it.
- No other active specs touch `release.md` or `verify-spec.md`.

## Deliverables

- [x] `commands/verify-spec.md` — rewritten as pure diagnostic
- [x] `commands/release.md` — rewritten with self-sufficient release gate
- [x] `commands/ship.md` — refined with opt-in tests and inline spec check
- [x] Cross-references updated across all pipeline commands
