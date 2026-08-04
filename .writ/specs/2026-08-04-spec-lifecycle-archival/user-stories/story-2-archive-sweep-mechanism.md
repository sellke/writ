# Story 2: Archive Sweep Mechanism

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** Story 1
> **Commit:** 453313ba50e96b082be1cbf408cc2d3139d62757

## User Story

**As a** Writ maintainer
**I want to** run `/status --archive` to automatically move completed, knowledge-evidenced specs into `.writ/specs/archive/` with a durable audit ledger
**So that** genuinely-done work leaves the active working set without losing history, addressability, or compatibility with existing single-level spec globs across the command suite

## Acceptance Criteria

- [x] Given a spec whose status resolves to **Complete** under Story 1's format-tolerant detector **and** at least one `.writ/knowledge/{decisions,conventions,glossary,lessons}/*.md` entry lists the spec's folder name in `related_artifacts`, when `/status --archive` runs, then the spec folder is moved via `git mv .writ/specs/<name> .writ/specs/archive/<name>`, one line is appended to `.writ/specs/archive/LEDGER.md` (spec name, citing knowledge filename(s), ISO timestamp), and the terminal summary includes it in the archived count.
- [x] Given a spec that resolves to **Complete** but has **no** knowledge entry referencing its folder name in `related_artifacts`, when the sweep runs, then the spec remains at `.writ/specs/<name>/`, is counted in the "skipped (no knowledge evidence yet)" total, and is **not** treated as a failure.
- [x] Given a spec whose folder name appears in a knowledge entry's `related_artifacts` but whose status does **not** resolve to Complete, when the sweep runs, then the spec is not moved — the status gate is absolute regardless of knowledge evidence.
- [x] Given `.writ/specs/archive/` or `LEDGER.md` do not yet exist, when the first eligible spec is archived, then the archive directory and ledger file are created on first use (ledger is committed to git, not written under `.writ/state/`), and subsequent moves append without overwriting prior ledger lines.
- [x] Given a destination collision (`.writ/specs/archive/<name>/` already exists) or a per-spec `git mv` failure (e.g. dirty working tree), when the sweep encounters that spec, then that spec alone is skipped and named in output, the sweep **continues** for remaining specs (never aborts the whole run), and a second consecutive `/status --archive` run performs a clean no-op for already-moved specs (idempotent — no duplicate ledger entries, no re-move attempts).

## Implementation Tasks

- [x] 2.1 Write failing unit tests in `scripts/tests/test_archive_sweep.py` covering: two-signal eligibility (both signals, Complete-only, evidence-only), happy-path `git mv` + ledger append format, destination collision (skip one, continue), `git mv` failure mid-sweep (skip one, continue), zero-eligible no-op summary (`0 archived, 0 skipped` or correct skip count), and idempotent second run — use temp git fixtures mirroring the `test_spec_status.py` / `eval-knowledge-consolidate.py` precedent.
- [x] 2.2 Implement a shared knowledge-evidence checker — prefer extending `scripts/archive-sweep.py` (new) with functions to scan `.writ/knowledge/{decisions,conventions,glossary,lessons}/*.md` frontmatter and match `related_artifacts` entries on the spec's **folder-name component** (not exact path equality); document the heuristic in module docstring per `spec.md` → `## Technical Concerns`.
- [x] 2.3 Implement the sweep reducer in `scripts/archive-sweep.py`: enumerate `.writ/specs/*/spec.md` (single-level glob only — never scan `archive/`), invoke Story 1's complete-family detector per spec, gate on knowledge evidence, perform `git mv` to `.writ/specs/archive/<name>/`, append ledger lines, and emit structured JSON + human summary (`N specs archived, M Complete specs skipped (no knowledge evidence yet)`).
- [x] 2.4 Add `--archive` invocation surface to `commands/status.md`: document the flag in `## Invocation`, add a dedicated sweep phase (after or instead of routine orientation when `--archive` is present) that calls the shared script or equivalent step-by-step bash, and ensure routine `/status` (no flag) never triggers archival — per Business Rule 2.
- [x] 2.5 Define and implement `.writ/specs/archive/LEDGER.md` format (one append-only line per move: spec folder name, knowledge entry filename(s) that supplied evidence, ISO 8601 timestamp); create-on-first-use, never duplicate an entry for a spec already under `archive/`.
- [x] 2.6 Add an `eval.sh` check (e.g. `archive-sweep`) with scenario fixtures asserting: `commands/status.md` documents `--archive`, no parallel archive-exclusion logic is added to other commands, collision and `git mv` failure paths continue the sweep, and the active-spec glob `.writ/specs/*/spec.md` is unchanged elsewhere.
- [x] 2.7 Run `python3 -m pytest scripts/tests/test_archive_sweep.py`, the new eval scenarios, and a manual dry review against this repo's real specs (post–Story 1 detection fix): confirm eligible specs would archive, ineligible Complete specs appear in skip count, and `/status`, `create-spec`, `implement-spec` still exclude `archive/` via nesting alone before marking complete.

## Notes

**Depends on Story 1.** Eligibility logic is meaningless if Complete/non-Complete classification is still broken. Do not ship or dogfood this story until Story 1's format-tolerant detector and tests are merged.

**Instruction-based command, testable script.** Like Story 1, the product change is prose in `commands/status.md` plus a shared `scripts/archive-sweep.py` reducer — the pattern established by `knowledge-consolidate.py` and `spec-status.py`. Agents executing `/status --archive` should invoke the script for deterministic behavior; eval checks guard drift.

**Nesting is the filter — do not add exclusions elsewhere.** Archived specs live at `.writ/specs/archive/<name>/spec.md`, one path segment deeper than active specs. Every existing `.writ/specs/*/spec.md` glob auto-excludes them. Do not teach `/status`, `create-spec`, or `implement-spec` to skip `archive/` explicitly (Business Rule 5).

**Knowledge path matching is approximate.** `related_artifacts` may cite full paths, `spec.md`, or `spec-lite.md` with slight drift. Match on the spec folder-name component (e.g. `2026-08-04-spec-lifecycle-archival`) to avoid false negatives — document as a known heuristic, not exact-match verification (`spec.md` → `## Technical Concerns`).

**No dry-run mode.** Per locked contract, auto-move on explicit `/status --archive` is deliberate; observability comes from terminal summary + committed `LEDGER.md`, mirroring the audit-trail principle in `scripts/knowledge-consolidate.py` without its dry-run gate.

**No reference rewriting.** Issue `spec_ref`, ADR `Amends:` pointers, and other historical cross-references are left unchanged; git rename tracking is sufficient (Business Rules 3–4). Precedent: `commands/edit-spec.md` "move, never delete" for archived stories.

**Risks:**

- Folder-name heuristic may false-positive if two unrelated artifacts share a slug substring — mitigated by matching the full dated spec folder name, not a bare keyword.
- `git mv` requires a clean enough working tree per spec; partial failures must not block the rest of the sweep.
- Agent may hand-roll bash instead of calling `archive-sweep.py` — eval scenarios should enforce documented invocation.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [A spec folder somehow already exists at the destination path, git mv fails (dirty working tree conflict, etc.)]
- **Shadow paths:** [Happy path, Spec Complete no evidence, Spec has evidence not Complete, git mv fails mid-sweep]
- **Business rules:** [Eligibility = Complete status AND cited by knowledge evidence, Auto-move not auto-invoke, Every move is a plain reversible git mv, Archived specs stay fully addressable, Nesting is the filtering mechanism]
- **Experience:** [Entry Point (/status --archive), Happy Path (scan → cross-reference → git mv → ledger → summary), Moment of Truth (real sweep, references still resolve), Feedback Model (terminal summary + durable ledger entry, no per-spec confirmation)]

---

## What Was Built

**Implementation Date:** 2026-08-04

### Files Created

1. **`scripts/archive-sweep.py`** (~230 lines)
   - `scan` subcommand: read-only eligibility report (delegates classification to `spec-status.py`, cross-references `related_artifacts` frontmatter across the four knowledge categories, folder-name substring match).
   - `sweep` subcommand: performs the real `git mv` + `LEDGER.md` append, skipping (never aborting on) destination collisions or `git mv` failures.
2. **`scripts/tests/test_archive_sweep.py`** (10 tests) — real temp-git-repo fixtures (not mocked) covering the full 2×2 eligibility matrix, happy path, collision, `git mv` failure, zero-eligible no-op, nil-input (no specs dir), idempotent second run, and the full-path-vs-folder-name substring heuristic.
3. **`scripts/eval-archive-sweep.py`** (4 scenarios) — CLI-boundary contract checks wired into `scripts/eval.sh`'s new `archive-sweep` check.

### Files Modified

- **`commands/status.md`** — Added `--archive` to `## Invocation` with a behavior table; added a new `### Archive Sweep (--archive)` phase documenting the scan → cross-reference → move → ledger → summary flow, explicitly stating it never runs as a side effect of routine `/status`; added an `Integration with Writ` row.
- **`scripts/eval.sh`** — Registered the `archive-sweep` check (CHECKS array + `check_archive_sweep()`), including `forbid_literal` guards against `status.md`/`create-spec.md`/`implement-spec.md` growing a parallel `archive/` exclusion (Business Rule 5).

### Implementation Decisions

1. **Delegate classification, don't duplicate it.** `archive-sweep.py` shells out to `spec-status.py scan` rather than reimplementing header parsing — one source of truth for complete-family detection, reusable and independently testable (per Story 1's design intent).
2. **The move IS the idempotency mechanism.** No separate "already archived" tracking file — a spec under `.writ/specs/archive/<name>/` simply no longer appears in the next `specs_dir.glob("*/spec.md")` scan. Verified with an explicit `test_second_run_is_idempotent` test and a real CLI-boundary scenario.
3. **Never fail closed.** Both subcommands always print JSON and exit 0; a missing knowledge dir, missing specs dir, destination collision, or `git mv` failure all degrade gracefully to an empty/partial result rather than raising — matching the "best-effort sweep, not a fail-closed validator" contract documented in the module docstring.

### Test Results

**Verification:** `python3 -m pytest scripts/tests/test_archive_sweep.py` + `python3 scripts/eval-archive-sweep.py` + a real dry-run `scan` (no mutation) against this repo's own `.writ/specs/` and `.writ/knowledge/`
**Coverage:** 100% of the documented shadow paths (happy path, Complete-no-evidence, evidence-not-Complete, git-mv-failure) and both named error paths (destination collision, git mv failure)
- ✅ 10/10 pytest fixtures passing (real temp git repos, not mocks)
- ✅ 4/4 eval scenarios passing
- ✅ `bash scripts/eval.sh --check=archive-sweep` — PASS, 0 findings
- ✅ Real dry-run `scan` against this repo found **3 eligible specs** (`2026-03-27-context-engine`, `2026-04-24-phase4-production-grade-substrate`, `2026-07-18-artifact-integrity-handshake`) — more than the 2 predicted in `user-stories/README.md`, confirming the mechanism works correctly against production data ahead of Story 6's actual mutating run
- ✅ Confirmed no regression: `bash scripts/eval.sh --check=spec-status` and `--check=spec-dependencies` still pass

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** None
- **Security:** Clean — `git mv` invoked via subprocess argv list (no shell interpolation); no destructive operation beyond the documented, reversible `git mv`

### Deviations from Spec

None
