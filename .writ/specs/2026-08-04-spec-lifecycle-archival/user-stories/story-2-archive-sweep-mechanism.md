# Story 2: Archive Sweep Mechanism

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer
**I want to** run `/status --archive` to automatically move completed, knowledge-evidenced specs into `.writ/specs/archive/` with a durable audit ledger
**So that** genuinely-done work leaves the active working set without losing history, addressability, or compatibility with existing single-level spec globs across the command suite

## Acceptance Criteria

- [ ] Given a spec whose status resolves to **Complete** under Story 1's format-tolerant detector **and** at least one `.writ/knowledge/{decisions,conventions,glossary,lessons}/*.md` entry lists the spec's folder name in `related_artifacts`, when `/status --archive` runs, then the spec folder is moved via `git mv .writ/specs/<name> .writ/specs/archive/<name>`, one line is appended to `.writ/specs/archive/LEDGER.md` (spec name, citing knowledge filename(s), ISO timestamp), and the terminal summary includes it in the archived count.
- [ ] Given a spec that resolves to **Complete** but has **no** knowledge entry referencing its folder name in `related_artifacts`, when the sweep runs, then the spec remains at `.writ/specs/<name>/`, is counted in the "skipped (no knowledge evidence yet)" total, and is **not** treated as a failure.
- [ ] Given a spec whose folder name appears in a knowledge entry's `related_artifacts` but whose status does **not** resolve to Complete, when the sweep runs, then the spec is not moved — the status gate is absolute regardless of knowledge evidence.
- [ ] Given `.writ/specs/archive/` or `LEDGER.md` do not yet exist, when the first eligible spec is archived, then the archive directory and ledger file are created on first use (ledger is committed to git, not written under `.writ/state/`), and subsequent moves append without overwriting prior ledger lines.
- [ ] Given a destination collision (`.writ/specs/archive/<name>/` already exists) or a per-spec `git mv` failure (e.g. dirty working tree), when the sweep encounters that spec, then that spec alone is skipped and named in output, the sweep **continues** for remaining specs (never aborts the whole run), and a second consecutive `/status --archive` run performs a clean no-op for already-moved specs (idempotent — no duplicate ledger entries, no re-move attempts).

## Implementation Tasks

- [ ] 2.1 Write failing unit tests in `scripts/tests/test_archive_sweep.py` covering: two-signal eligibility (both signals, Complete-only, evidence-only), happy-path `git mv` + ledger append format, destination collision (skip one, continue), `git mv` failure mid-sweep (skip one, continue), zero-eligible no-op summary (`0 archived, 0 skipped` or correct skip count), and idempotent second run — use temp git fixtures mirroring the `test_spec_status.py` / `eval-knowledge-consolidate.py` precedent.
- [ ] 2.2 Implement a shared knowledge-evidence checker — prefer extending `scripts/archive-sweep.py` (new) with functions to scan `.writ/knowledge/{decisions,conventions,glossary,lessons}/*.md` frontmatter and match `related_artifacts` entries on the spec's **folder-name component** (not exact path equality); document the heuristic in module docstring per `spec.md` → `## Technical Concerns`.
- [ ] 2.3 Implement the sweep reducer in `scripts/archive-sweep.py`: enumerate `.writ/specs/*/spec.md` (single-level glob only — never scan `archive/`), invoke Story 1's complete-family detector per spec, gate on knowledge evidence, perform `git mv` to `.writ/specs/archive/<name>/`, append ledger lines, and emit structured JSON + human summary (`N specs archived, M Complete specs skipped (no knowledge evidence yet)`).
- [ ] 2.4 Add `--archive` invocation surface to `commands/status.md`: document the flag in `## Invocation`, add a dedicated sweep phase (after or instead of routine orientation when `--archive` is present) that calls the shared script or equivalent step-by-step bash, and ensure routine `/status` (no flag) never triggers archival — per Business Rule 2.
- [ ] 2.5 Define and implement `.writ/specs/archive/LEDGER.md` format (one append-only line per move: spec folder name, knowledge entry filename(s) that supplied evidence, ISO 8601 timestamp); create-on-first-use, never duplicate an entry for a spec already under `archive/`.
- [ ] 2.6 Add an `eval.sh` check (e.g. `archive-sweep`) with scenario fixtures asserting: `commands/status.md` documents `--archive`, no parallel archive-exclusion logic is added to other commands, collision and `git mv` failure paths continue the sweep, and the active-spec glob `.writ/specs/*/spec.md` is unchanged elsewhere.
- [ ] 2.7 Run `python3 -m pytest scripts/tests/test_archive_sweep.py`, the new eval scenarios, and a manual dry review against this repo's real specs (post–Story 1 detection fix): confirm eligible specs would archive, ineligible Complete specs appear in skip count, and `/status`, `create-spec`, `implement-spec` still exclude `archive/` via nesting alone before marking complete.

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

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [A spec folder somehow already exists at the destination path, git mv fails (dirty working tree conflict, etc.)]
- **Shadow paths:** [Happy path, Spec Complete no evidence, Spec has evidence not Complete, git mv fails mid-sweep]
- **Business rules:** [Eligibility = Complete status AND cited by knowledge evidence, Auto-move not auto-invoke, Every move is a plain reversible git mv, Archived specs stay fully addressable, Nesting is the filtering mechanism]
- **Experience:** [Entry Point (/status --archive), Happy Path (scan → cross-reference → git mv → ledger → summary), Moment of Truth (real sweep, references still resolve), Feedback Model (terminal summary + durable ledger entry, no per-spec confirmation)]
