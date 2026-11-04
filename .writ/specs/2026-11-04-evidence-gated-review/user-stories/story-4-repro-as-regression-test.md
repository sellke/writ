# Story 4: Confirmed repros become regression tests

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 3

## User Story

**As a** developer running `/implement-story`
**I want to** a confirmed repro saved to a manifest and checked on re-review
**So that** a recode cannot silently drop or weaken the test that proved a finding real

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.5

- [ ] Given a `test` repro that the recorded run shows failing, when `evidence` runs with `--manifest-out`, then it writes an `evidence-manifest-v1` file atomically, with one entry per confirmed `test` repro holding finding key, path, normalized SHA-256, kind, and location. If the write fails, it adds `reason: manifest_write_failed` and leaves line 1 unchanged. `[AC-4.1]`
- [ ] Given a manifest repro whose path is missing from `--changed`, or whose normalized SHA-256 differs from the file on disk, when `evidence --prior` runs on any agent verdict (PASS, PAUSE, or FAIL), then line 1 is `fail` with `reason: repro_removed <path>` or `reason: repro_modified <path>`. On a FAIL verdict, new findings are evaluated after those checks. On PASS or PAUSE, only the prior checks run. CRLF endings, trailing whitespace, and the final newline alone do not count as a change. `[AC-4.2]`
- [ ] Given a manifest repro that is in `--changed` and unmodified, when `evidence --prior` runs against a recorded run that does not contain the repro's path or has no `exit code: 0` line, then line 1 is `fail` with `reason: repro_still_failing <path>`. When the recorded run names the path and exits 0, no reason line prints for it. `[AC-4.3]`
- [ ] Given a `--prior` manifest that is missing, unreadable, or not `evidence-manifest-v1`, when `evidence --prior` runs, then line 1 is `unverifiable` with `reason: bad_manifest`, the exit code is 0, and the agent verdict stands. `[AC-4.4]`
- [ ] Given a Gate 3 FAIL with a confirmed `test` repro, when Gate 3 builds the recode brief, then the brief adds an `## Evidence repros` section with the finding, path, exact fenced content, and a no-edit instruction. On re-review, the recorded test run includes every manifest path. `[AC-4.5]`

## Implementation Tasks

- [ ] 4.1 Write failing pytest cases for the manifest write in `scripts/tests/test_review_override.py`: entry shape, normalized-hash equivalence (CRLF, trailing whitespace, extra final newlines), merge with an existing manifest (earlier entries kept, same path replaced, no new confirmations leaves the file unchanged), and an unwritable manifest path. Append them above the `__main__` block under a comment naming `2026-11-04-evidence-gated-review`, and cite each test's ID in its docstring `[AC-4.1, AC-4.2]`
- [ ] 4.2 Write failing pytest cases for `--prior` in the same class: removed path, modified hash, still failing, passing, and missing or wrong-schema manifest `[AC-4.2, AC-4.3, AC-4.4]`
- [ ] 4.3 Write failing wiring assertions in `scripts/tests/test_evidence_gate_wiring.py` (created by Story 3; name the spec in its docstring): the recode brief in `commands/implement-story.md` carries `## Evidence repros` with the no-edit instruction, and the re-review's recorded test command includes each manifest path `[AC-4.5]`
- [ ] 4.4 Implement the manifest write in `scripts/review-override.py` `evidence`: one normalization helper shared by the write and the `--prior` compare, an atomic write copied from `_write_json_atomic` in `scripts/review-panel.py` (copy, do not import), and the `--manifest-out` path. Run the 4.1 cases to green `[AC-4.1, AC-4.2]`
- [ ] 4.5 Implement `--prior` in `scripts/review-override.py`: `repro_removed`, `repro_modified`, `repro_still_failing`, and `bad_manifest`, run before new findings are evaluated. Read the recorded output and file bytes only: no repro run, no git write. Run the 4.2 cases to green `[AC-4.2, AC-4.3, AC-4.4]`
- [ ] 4.6 Edit `commands/implement-story.md`. Add the `## Evidence repros` section to the recode brief written at Gate 3. Add the manifest paths to the re-review's recorded test command. When a manifest exists, run `evidence --prior` on every agent verdict (spec.md Gate 3 decision row 3a). Record `wc -c` before and after the edit. Run `python3 scripts/gen-platform-trees.py`. Run the 4.3 cases to green `[AC-4.5]`
- [ ] 4.7 Verify, one run at a time: pytest on Python 3.9 for `scripts/tests/test_review_override.py` and `scripts/tests/test_evidence_gate_wiring.py`, the same on Python 3.14, `python3 scripts/gen-platform-trees.py --check`, then `bash scripts/eval.sh`. Never run pytest alongside eval.sh `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`

## Notes

**Codebase facts (verify at implementation)**
- `evidence` does not exist yet. Story 2 adds it to `scripts/review-override.py`, which today has `check`, `switch`, and `safety-fact`. Confirm Story 2 declares `--manifest-out` and `--prior`. If not, add them here.
- Reuse, do not import: `_emit` (line 93), `_inside` (line 328), `_read_text` (line 353) in `review-override.py`; `_write_json_atomic` (line 553) in `review-panel.py`.
- Check shape: line 1 `pass`, `fail`, or `unverifiable`; `reason:` lines; summary last; exit 0, 1, or 2 (`.writ/docs/agent-cli-contract.md`, check shape).
- Normalization on both sides: CRLF to LF, strip trailing whitespace per line, exactly one final newline. One helper serves the write and the compare.
- `--prior` reads the recorded output and file bytes. It runs no repro.
- Python 3.9 floor: stdlib only, `from __future__ import annotations`, no `match` statements.
- Test citations: an AC token counts only after a spec name appears above it in the same file (`.writ/docs/acceptance-criteria-ids.md`, Scan Bounds). Name the spec above the new tests.
- Run pytest alone. Concurrent writes under `.writ/state/` break the smoke and app-verify tests (`CLAUDE.md`).

**Byte budget**
- `commands/implement-story.md` is 40,759 bytes at authoring, before Story 3. Re-run `wc -c` at the start of task 4.6, because Story 3 edits the file first.
- Net change across Stories 3, 4, 6, and 7 must be zero or less (`spec.md` → `## Implementation Approach` → Byte budget; `technical-spec.md` → `## Byte Budget`). Keep the recode brief addition short.

**Gaps found at generation, resolved in the spec (2026-11-04)**
- **A passing re-review used to skip `--prior`.** Now `--prior` runs on every agent verdict when a manifest exists (`spec.md` → `### Gate 3 decision`, row 3a; `### Repro as regression test`).
- **There was no match rule for `repro_still_failing`.** The match is by file. The recorded run must contain the path and an `exit code: 0` line, the same rule `_tested_ok` uses (`technical-spec.md` → `## Manifest`).
- **Manifest overwrite.** `--manifest-out` merges with an existing file, and an entry with the same path is replaced. A run with no new confirmations leaves the file unchanged (`technical-spec.md` → `## Manifest`). Task 4.1 adds a merge case.

**Assumptions**
- `user_type` was not supplied. "Developer running `/implement-story`" comes from `spec.md` → `## Experience Design` → `### Who uses it`.
- The coder creates each repro file in the working tree, per `technical-spec.md` → `## Gate 3 Wiring`. The contract says "commits." This story follows the technical spec.

**Integration**
- Depends on Story 3: the `evidence` call, the Gate 3 report line, and `test_evidence_gate_wiring.py`.
- Stories 6 and 7 also edit Gate 3 of `commands/implement-story.md`. Run in sequence.
- Generated trees: after any edit to `commands/`, run `python3 scripts/gen-platform-trees.py` and commit the trees in the same story.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Write the manifest, --prior] — `technical-spec.md` → `## Error & Rescue Map`
- **Shadow paths:** [Happy] — `technical-spec.md` → `## Shadow Paths`
- **Business rules:** [Repro as regression test, normalization on both sides] — `spec.md` → `## Business Rules (Expanded)` → `### Repro as regression test`; `technical-spec.md` → `## Manifest`, `## Gate 3 Wiring (Story 3, Story 4)`
- **Experience:** [Coder receives the repro file itself, Gate 3 journey steps 4 and 5] — `spec.md` → `## Experience Design` → `### Interaction patterns`, `### Journey (Gate 3)`
