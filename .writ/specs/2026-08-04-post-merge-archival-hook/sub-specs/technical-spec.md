# Technical Spec: Post-Merge Archival Hook

> Source: `.writ/specs/2026-08-04-post-merge-archival-hook/spec.md`

## Shared Spec Reference Resolution (Story 1)

### Current state (prose only)

`commands/ship.md`'s PR-body population step currently describes Spec Reference resolution only as guidance: match the branch name or recent story-file references in commits against `.writ/specs/`. There is no discrete, callable implementation — `/release` cannot reuse it without either duplicating the prose or reimplementing the matching logic independently.

### Target shape

Extract the heuristic into a small script mirroring `scripts/archive-sweep.py`'s shape and testability bar — e.g. `scripts/resolve-spec-reference.py` — with a single well-defined entry point:

```
resolve_spec_reference(branch_name: str, commit_messages: list[str], specs_dir: str = ".writ/specs") -> ResolveResult
```

`ResolveResult` distinguishes three outcomes explicitly rather than returning a bare string:

```python
@dataclass
class ResolveResult:
    matches: list[str]   # spec folder names found; empty if none
    ambiguous: bool       # True if len(matches) > 1
```

Matching strategy (illustrative — exact heuristic is the coding agent's call, but must satisfy the "skip on ambiguity" business rule):

1. Exact or substring match of a `.writ/specs/<date>-<name>` folder-name component against the branch name (case-insensitive, ignoring common branch prefixes like `feature/`, `chore/`, `fix/`).
2. Fall back to scanning recent commit messages / story-file paths referenced in the diff for a `.writ/specs/<date>-<name>/` path substring.
3. If step 1 and step 2 together produce more than one distinct spec folder, or zero, return the "no unambiguous match" result — never guess between candidates.

`commands/ship.md` is updated to call this script (or the equivalent shared logic) for its own PR-body Spec Reference section, replacing the inline prose — **this must not change `/ship`'s existing PR-body output** for any case that resolves unambiguously today; it only makes the logic reusable and testable.

### Why a script, not just refactored prose

`commands/release.md` needs to invoke this from Step 1.3c without a human reading prose and improvising — a script with a stable CLI/importable interface is what makes "both commands call the identical resolution" verifiable rather than aspirational.

## Single-Spec Archive Entry Point (Story 2)

### Current state

`scripts/archive-sweep.py` has `scan()` (finds all complete-family specs, computes eligibility + knowledge evidence for each) and `sweep()` (iterates eligible specs from `scan()`, `git mv`s each, appends to `LEDGER.md` via `_append_ledger()`).

### New entry point

```python
def archive_one(spec_name: str, pr_number: int | None = None, specs_dir: str = ".writ/specs") -> ArchiveOneResult:
    """Archive exactly one named spec if eligible. Idempotent: already-archived
    specs return a no-op result, not an error. Not-yet-complete specs are
    skipped, not forced."""
```

Reuses the exact eligibility check (`is_complete_family`, via `scripts/spec-status.py`) and the exact `git mv` + `_append_ledger()` mechanism `sweep()` already uses — this function is a single-spec-scoped wrapper around the same primitives, not a parallel implementation.

```python
@dataclass
class ArchiveOneResult:
    status: Literal["archived", "already_archived", "not_eligible", "collision", "git_mv_failed", "archived_unlogged"]
    spec_name: str
    ledger_line: str | None  # populated only when status == "archived"
```

> **Implementation note (Story 2):** this dataclass shape is illustrative, not binding — `scripts/archive-sweep.py` returns a plain dict keyed `"spec"` (not `"spec_name"`), matching `scan()`/`sweep()`'s existing convention in the same module. The `status` literal set above is accurate as implemented, including the `archived_unlogged` sixth value (see Error & Rescue Map below).

### Ledger format extension

Current line shape (from parent spec):

```
2026-08-04T15:32:00Z — `2026-07-10-knowledge-consolidation` archived (evidence: `.writ/knowledge/lessons/2026-07-19-...md`)
```

or, for the status-alone amendment:

```
2026-08-04T15:32:00Z — `2026-08-04-example-spec` archived (evidence: no knowledge evidence yet)
```

Extended shape when `pr_number` is provided:

```
2026-08-04T20:00:00Z — `2026-08-04-example-spec` archived (evidence: no knowledge evidence yet, via PR #32)
```

`_append_ledger()` gains an optional `pr_number` parameter; when `None` (every existing call site — the batch `sweep()` never passes one), output is byte-for-byte unchanged from today. Any ledger-reading logic (if any exists beyond human/agent reading) must not assume a fixed number of comma-separated clauses inside the parenthetical — treat `via PR #N` as an optional trailing clause.

### Idempotency

`archive_one()` checks `.writ/specs/archive/<spec_name>/` for existence before attempting `git mv`; if already present, returns `already_archived` — never raises, never double-appends to the ledger.

## Wiring into `/release` Step 1.3c (Story 3)

### Current state

`commands/release.md` Step 1.3c computes `LAST_MERGED_SHA` (via `gh pr list --state merged --limit 1`) and compares it to `HEAD_SHA`, today used only to decide whether to skip a redundant test run.

### Extension

When `LAST_MERGED_SHA == HEAD_SHA`:

1. Fetch the merged PR's branch name and commit messages (already available from the same `gh pr list` call, or one additional `gh pr view` call).
2. Call `resolve_spec_reference(...)` from Story 1.
3. If `result.ambiguous` or `not result.matches`: do nothing further, no output.
4. If exactly one match: check `is_complete_family(.writ/specs/<match>/spec.md)`. If false: do nothing further.
5. If true: call `archive_one(match, pr_number=<merged PR number>)`.
6. If the result is `"archived"`: commit the `git mv` + `LEDGER.md` change as a small standalone commit direct to `main` — same commit pattern `/release` already uses for its version-bump commit, sequenced immediately before or after it (implementer's call; either ordering is acceptable since both land in the same release run).
7. Any other result (`already_archived`, `not_eligible`, `collision`, `git_mv_failed`): no output, no commit, `/release` proceeds exactly as it would without this step.

**Guard clause:** wrap steps 1–6 in error handling that catches any exception and treats it identically to a `git_mv_failed`/no-op outcome — this hook must never raise an uncaught error that halts `/release`'s remaining steps (changelog, version bump, git tag, GitHub release).

**`--skip-gate` interaction:** since this hook lives inside the same Step 1.3c block as the `LAST_MERGED_SHA`/`HEAD_SHA` comparison that `--skip-gate` already bypasses, no separate flag check is needed — skipping the gate skips this by construction.

## Dogfood Run (Story 4)

### Fixture-based verification (available immediately)

Unit/integration tests exercise `resolve_spec_reference()` and `archive_one()` against fixture repos — no real PR-merge cycle required:

- Fixture branch name matching a real fixture spec folder → single match.
- Fixture branch name matching zero or two+ fixture spec folders → ambiguous/no-match, verify no archival attempt.
- Fixture spec already complete-family → `archive_one()` returns `"archived"`, ledger line contains `via PR #N`.
- Fixture spec not complete-family → `archive_one()` returns `"not_eligible"`, no move.
- Re-invoke `archive_one()` on an already-archived fixture spec → `"already_archived"`, no duplicate ledger line.
- Simulate `commands/release.md` Step 1.3c end-to-end against a fixture repo state where `LAST_MERGED_SHA == HEAD_SHA` and a real fixture PR resolves — confirm the archive commit lands and `/release`'s subsequent steps are unaffected.

### Live confirmation (once this spec's own lifecycle completes)

This spec and its parent (`2026-08-04-spec-lifecycle-archival`) are themselves the eventual live test case: once this spec reaches `Complete`, its own PR merges, and a subsequent `/release` run executes, that run's Step 1.3c should resolve and archive this spec (and, separately, `2026-08-04-spec-lifecycle-archival`, once *its* still-open loop closes the same way — either via this hook on a later trivial PR that references it, or via a manual `/status --archive` run in the interim). Record the outcome — which specs archived, which `/release` run, which PR number — in this story's own "What Was Built" section when it occurs, mirroring the parent spec's Story 6 dogfooding record.

## Error & Rescue Map

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| Fetch merged PR metadata (`gh pr view`/`gh pr list`) | `gh` unavailable, auth expired, network error | Treat identically to "no match resolved" — skip silently, `/release` continues using its existing pre-hook behavior | Simulate `gh` command failure, assert no exception propagates and `/release`'s remaining steps still run |
| Resolve Spec Reference | Zero or multiple candidate specs match | Skip silently — never guess | Fixture branch names with 0 and 2+ matching spec folders |
| Check spec status | Malformed or missing `Status:` header | Conservative default: treat as not complete-family, skip (same rule as the parent spec's detection) | Fixture spec.md with missing/malformed status header |
| `git mv` the spec folder | Dirty working tree, destination path collision | Skip that spec, report nothing user-facing, `/release` continues | Simulate a pre-existing destination folder; simulate a dirty-tree `git mv` failure |
| Append to `LEDGER.md` | File write failure (permissions, disk) | Resolved (Story 2): returns a distinct `"archived_unlogged"` status — the move is accepted as a rare, recoverable risk rather than rolled back | Simulated a forced ledger-append failure after a successful move; asserts `archived_unlogged`, not an exception or a mislabeled `archived`/`git_mv_failed` |

**Resolved — option (b), accepted rare-risk, surfaced as a distinct status.** Story 2's implementation (`archive_one()` in `scripts/archive-sweep.py`) does not roll back the `git mv` on a ledger-append failure. Rationale (documented in the module's docstring near `archive_one()`): `git mv` is a working-tree rename already tracked by git — rolling it back would require a second subprocess call that can itself fail, compounding the failure mode rather than resolving it, and the actual commit of this change happens later (`/release` Step 1.3c), so an uncommitted, unlogged move is visible and recoverable via `git status` rather than silently lost. A ledger write failing on a small tracked markdown file in the same working tree immediately after a successful rename is exceedingly rare and independent of the move itself. Rather than folding this outcome into the existing `"archived"` (which implies a populated `ledger_line`) or `"git_mv_failed"` (which would misreport that the move never happened) statuses, `archive_one()` returns a sixth, distinct status — `"archived_unlogged"` — so callers can tell the three outcomes apart. Covered by a dedicated fixture test in `scripts/tests/test_archive_sweep.py`.

## Shadow Paths

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| `/release` Step 1.3c archival check | One spec resolves, is complete-family, archived with `via PR #N` ledger line | No merged PR found (`gh` returns nothing) → hook doesn't run, identical to today's behavior | Merged PR found but resolves to zero specs → silent no-op | `gh` call fails/times out → caught, treated as no-op, `/release` continues |

## Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| PR references multiple specs (e.g. a multi-spec cleanup PR) | Ambiguous → skip, never pick one arbitrarily |
| Spec already archived by a prior manual `/status --archive` sweep | `archive_one()` returns `already_archived` → no-op, no duplicate ledger line |
| Story-level completion within a still-open spec (PR closes one story of several) | Never triggers — status header gates on the whole spec, not story counts |
| Two `/release` runs in quick succession (e.g. retry after a transient failure) | Idempotent — second run sees the spec already archived and no-ops |
| `/release --skip-gate` | Hook does not run at all — same gate block as the `LAST_MERGED_SHA` check |

## Testing Strategy

- **Story 1:** Fixture branch names + commit message lists covering exact match, substring match, zero match, and ambiguous (2+) match cases for `resolve_spec_reference()`. Regression test confirming `/ship`'s existing PR-body Spec Reference output is unchanged for cases that resolve today.
- **Story 2:** Fixture specs crossed complete-family/not × archived/not-yet-archived (2×2) for `archive_one()`; ledger-format round-trip test confirming old-format (no PR) and new-format (with PR) lines both remain parseable; collision and `git-mv`-failure simulation.
- **Story 3:** Fixture repo state simulating `LAST_MERGED_SHA == HEAD_SHA` with a resolvable and complete-family spec → assert archive commit lands; simulate every "no output" branch (no match, ambiguous, not-yet-complete, already-archived) → assert zero side effects and zero output diff from a hook-less baseline run; simulate an exception inside the hook → assert `/release`'s remaining steps still execute.
- **Story 4:** Not unit-testable for the live-confirmation half — recorded as dogfooding evidence in the story file once this spec's own PR merges and a subsequent `/release` run occurs, mirroring the parent spec's Story 6.

## Non-Goals (restated from spec.md Scope Boundaries)

No change to `/ship`'s own synchronous flow (no merge-waiting, no new flag). No story-level or partial-spec triggering. No batch archival or change to `/status --archive`'s existing behavior — the two paths coexist. No new persistent cross-command state files. No user-facing confirmation, new PR-body section, or new `/release` terminal output.
