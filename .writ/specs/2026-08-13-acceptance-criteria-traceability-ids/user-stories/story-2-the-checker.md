# Story 2: The Checker

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** developer or agent about to trust a `Completed ✅` story
**I want** a read-only script that decides, deterministically, whether every criterion is
covered and every citation resolves
**So that** the verdict does not depend on who read the markdown, and a blocking check has an
executable reference behind it like every other blocking check in this repo

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [ ] Given a fixture triggering each of the seven finding codes, when `ac-trace.py check` runs, then it reports that code with the severity recorded in `.writ/docs/acceptance-criteria-ids.md` and exits 1 for any blocking finding, 0 when the only findings are informational. `[AC-2.1]`
- [ ] Given an ID-shaped token that is not an end-anchored `` `[AC-n.m]` `` group — a high-water-mark line, or an example ID quoted in criterion prose — when the check runs, then that token is neither a definition nor a citation, so a marker never satisfies its own ID and quoted prose never manufactures one. `[AC-2.2]`
- [ ] Given two runs over byte-identical input, when their stdout is compared, then it is byte-identical and finding order is deterministic rather than filesystem-order dependent. `[AC-2.3]`
- [ ] Given a `--spec` path with no `user-stories/` directory, or a story file that cannot be read, when the check runs, then it exits 2 naming the offending path — never 0, and never 1. `[AC-2.4]`
- [ ] Given this spec's own four story files, when the check runs against this spec folder, then it exits 0. `[AC-2.5]`

## Implementation Tasks

- [ ] 2.1 Write `scripts/tests/test_ac_trace.py` first — one test per finding code, plus the two non-tag hazards (marker line, prose-quoted ID), determinism, and the three exit codes `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`
- [ ] 2.2 Implement the end-anchored `TAG` parser: definitions and marker from `## Acceptance Criteria`, citations from `## Implementation Tasks`, with the marker consumed and every non-anchored ID token treated as prose. Use Story 4's own criteria as the regression fixture — they must yield exactly four `AC-4.*` definitions `[AC-2.1, AC-2.2]`
- [ ] 2.3 Implement the citation scan outside `.writ/` — classify test-shaped paths as test citations and everything else as informational source citations `[AC-2.1]`
- [ ] 2.4 Implement the finding pass and JSON output with sorted, deterministic finding order; wire exit codes 0/1/2 `[AC-2.1, AC-2.3, AC-2.4]`
- [ ] 2.5 Write `scripts/eval-ac-trace.py` fixture scenarios (disposable spec folders in tempdirs, PASS/FAIL TSV) following `scripts/eval-story-deps.py`, and register `check_ac_trace` in `scripts/eval.sh` `[AC-2.1, AC-2.3]`
- [ ] 2.6 Run the checker against this spec folder as the dogfood fixture and resolve anything it finds `[AC-2.5]`
- [ ] 2.7 Verify all tests pass and coverage on new code is ≥80% with error paths at 100% `[AC-2.1, AC-2.4]`

## Notes

**Technical considerations:** Read-only, in the strict sense `scripts/exit-criteria.py`
documents about itself — never writes a file, and any git invocation stays within the
read-only subcommand families. The output contract is one JSON object on stdout with a schema
string, matching `spec-deps.py` and `exit-criteria.py`.

The citation scan is the only part that reaches outside the spec folder. Bound it: skip
`.git/`, skip anything git-ignored, skip binaries, and do not follow symlinks out of the repo.
A repo-wide scan that silently reads a vendored `node_modules` is both slow and wrong.

**Risks:** The tempting shortcut is to satisfy coverage from *any* occurrence of an ID outside
`.writ/`. That would let a citation in a changelog or a commit-message fixture count as a test
and would launder exactly the gap this spec exists to close. Test-shaped paths satisfy
coverage; everything else is informational and must be reported as such.

Second risk: reporting `untested_criterion` on a story that is not `Completed ✅`. Tests do not
exist before the work does, and a checker that cries every time a spec is authored gets muted,
taking the real findings with it.

**Integration:** Story 1's grammar doc is the specification. A disagreement between the doc and
this script is a defect in whichever is wrong — resolve it in the doc first, then the code, so
the recorded contract stays authoritative.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** Read spec folder, Parse story file, Scan repo for citations, Emit
  verdict — from sub-specs/technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** Happy path, Nil input (no `user-stories/`), Empty input (zero criteria),
  Upstream error (unreadable story) — from sub-specs/technical-spec.md → ## Shadow Paths
- **Business rules:** All seven finding codes with severities, and the "test-shaped path"
  classification — from spec.md → ## 📋 Business Rules
- **Precedent to mirror:** `scripts/story-deps.py` (CLI shape, JSON output, named finding
  codes), `scripts/eval-story-deps.py` (fixture-scenario harness), `scripts/exit-criteria.py`
  (read-only discipline, schema string, exit-code trichotomy)
