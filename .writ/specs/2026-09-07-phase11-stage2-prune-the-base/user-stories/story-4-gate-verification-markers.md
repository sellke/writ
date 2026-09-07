# Story 4: Gate Verification Markers and Provenance Check — gates: Frontmatter, verdict-provenance.py, and the verdict-provenance Eval Check

> **Status:** Completed ✅ (2026-09-07)
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer who needs every Step 3 gate's verdict source declared so the honor-system gates in `implement-story.md` are visible rather than implicit, **I want to** add a `gates:` block to the command's frontmatter naming each gate's `script` or `prose-only` verification, and get a `verdict-provenance.py check` command wired into `eval.sh` that fails when a gate heading and its frontmatter entry drift apart, **so that** the mechanization spec (the second Stage 2 spec) has a truthful, checkable starting count of how many gates still run on prose alone.

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.5

- [x] Given `commands/implement-story.md` after this story lands, when its frontmatter `gates:` block is read, then it names all ten Step 3 gate ids (`gate0_arch`, `gate0_5_boundary`, `gate1_coding`, `gate2_build`, `gate2_5_surface`, `gate3_review`, `gate3_5_drift`, `gate4_tests`, `gate4_5_visual`, `gate5_docs`) with truthful sources — `gate2_build: script: scripts/build-smoke.py` and `gate4_tests: script: scripts/test-integrity.py`, the other eight `verification: prose-only` — and `python3 scripts/verdict-provenance.py check --command commands/implement-story.md` exits 0 printing the note `prose_only_count: 8 (cap 2)` `[AC-4.1]`
- [x] Given fixture command files with one drift each (a `#### Gate N` heading with no matching frontmatter entry; a frontmatter entry with no matching heading; an entry carrying neither `script` nor `verification`; an entry carrying both; a `script:` path that does not exist on disk; a `verification:` value other than `prose-only`), when `check` runs against each fixture, then it prints the corresponding finding (`heading_without_entry`, `entry_without_heading`, `entry_without_source`, `entry_both_sources`, `script_missing`, `unknown_verification_value`) naming the fixture file and the gate id, and exits 1 `[AC-4.2]`
- [x] Given a command file with more than `--max-prose-only` (default 2) `verification: prose-only` entries, when `check` runs without `--prose-only-blocking`, then it prints `prose_only_count: <n> (cap <max>)` as a note and exits 0 on that condition alone, and when run with `--prose-only-blocking`, then the same line is a finding and exit is 1 `[AC-4.3]`
- [x] Given `bash scripts/eval.sh` runs after this story lands, when the `verdict-provenance` check executes `check_verdict_provenance()` against the real `commands/implement-story.md`, then every `verdict-provenance.py` finding surfaces via `add_finding`, the `prose_only_count` line surfaces via `add_note` (not blocking, per technical-spec §5), and the overall eval.sh exit stays 0 with 0 findings `[AC-4.4]`
- [x] Given `#### Gate 4.5: Visual QA (Optional)` in `commands/implement-story.md`'s body after this story lands, when the section is read, then it names no percentage threshold and still uses PASS / SOFT PASS / FAIL vocabulary, and `check_required_sections` and `check_loop_bounds` in `eval.sh` (which already parse this file's frontmatter) stay green `[AC-4.5]`

## Implementation Tasks

- [x] 4.1 Write `scripts/tests/test_verdict_provenance.py` (pytest, fixture command files per technical-spec §7: complete block, missing entry, extra entry, both keys, missing script, unknown verification value, prose-only count over cap as note vs. finding) and `scripts/tests/test_eval_verdict_provenance.sh` mirroring `scripts/tests/test_eval_pipeline_baseline.sh`'s fixture shape `[AC-4.1]` `[AC-4.2]` `[AC-4.3]` `[AC-4.4]`
- [x] 4.2 Implement the frontmatter and heading parser in `scripts/verdict-provenance.py` (stdlib, Python 3.9 floor, no PyYAML — a minimal line parser mirroring `scripts/exit-criteria.py`'s approach): read the `gates:` list of `{id, script?, verification?}` from frontmatter, read `#### Gate N` headings from the body, and map both to the fixed heading→id table from technical-spec §5 (`Gate 0`→`gate0_arch`, `0.5`→`gate0_5_boundary`, `1`→`gate1_coding`, `2`→`gate2_build`, `2.5`→`gate2_5_surface`, `3`→`gate3_review`, `3.5`→`gate3_5_drift`, `4`→`gate4_tests`, `4.5`→`gate4_5_visual`, `5`→`gate5_docs`) `[AC-4.1]` `[AC-4.2]`
- [x] 4.3 Implement `verdict-provenance.py check` (argparse subcommand, `_fail`/`_refuse` exit-2 pattern mirroring `pipeline-baseline.py`): the six finding codes, `script_missing` resolved relative to `--repo`, the `prose_only_count: <n> (cap <max>)` note-vs-finding split on `--prose-only-blocking`, the summary line, and exit codes 0/1/2 `[AC-4.1]` `[AC-4.2]` `[AC-4.3]`
- [x] 4.4 Add the `gates:` block to `commands/implement-story.md` frontmatter with all ten entries and truthful sources per technical-spec §5, without disturbing the existing `exit_criteria:` and `loop:` keys `[AC-4.1, AC-4.5]`
- [x] 4.5 Edit `commands/implement-story.md`'s `#### Gate 4.5: Visual QA (Optional)` body to drop percentage thresholds while keeping the PASS / SOFT PASS / FAIL vocabulary, per the assessment's "an actual pixel or DOM diff or drop the percentage" `[AC-4.5]`
- [x] 4.6 Register `check_verdict_provenance()` in `scripts/eval.sh` next to `check_pruned_base()`, added to the `CHECKS=(...)` array as `verdict-provenance`, not count-blocking (no `--prose-only-blocking` flag passed) yet; relay findings via `add_finding` and the `prose_only_count` line via `add_note` `[AC-4.3]` `[AC-4.4]`
- [x] 4.7 Verify all acceptance criteria: `uv run --python 3.9 pytest scripts/tests/test_verdict_provenance.py` green, `bash scripts/tests/test_eval_verdict_provenance.sh` green, `bash scripts/eval.sh` shows 0 findings including `check_required_sections` and `check_loop_bounds` still passing, and append the decision-log line `{date} stage-2: Story 4 — gates: frontmatter block, verdict-provenance.py check, eval.sh verdict-provenance check landed` to the story's completion commit `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`

## Notes

**Technical considerations.** The heading→id table is fixed and shared with `pipeline-baseline.py`'s `GATE_NAMES` (`gate0_arch`, `gate2_build`, `gate3_review`, `gate4_tests`, `gate5_docs` already match) so a later join between the two scripts' output is free — do not invent a different naming scheme for the other five ids. No YAML library: the frontmatter parser is a minimal stdlib line parser in the shape of `scripts/exit-criteria.py`, not a general YAML reader, so it only needs to understand the `gates:` list's fixed two-key-per-entry shape. `script_missing` checks the path relative to `--repo`, the same convention `prune-ledger.py` and `pipeline-baseline.py` use for repo-relative paths.

**Risks.** Adding a `gates:` block grows `commands/implement-story.md`'s frontmatter — that is itself bytes, but `implement-story.md` is a command file, not one of the two base files (`system-instructions.md`, `commands/_preamble.md`) the byte cap in Stories 1–3 governs, so this growth is out of scope for the cap and must not be treated as a pruning target. Existing frontmatter parsers in `eval.sh` (`check_required_sections`, `check_loop_bounds`) already read this file's frontmatter for other keys — adding `gates:` must not break their parsing, which is why AC-4.5 requires both to stay green.

**Integration with later stories.** This story runs independent of Stories 2 and 3 (it touches only `commands/implement-story.md`'s frontmatter, `scripts/`, and `eval.sh`, never the two base files or the ledger) and independent of Story 5 (baselines don't read the `gates:` block). It is the story that makes the Goal Card's DONE WHEN line 4 target — "at most 2 gates `verification: prose-only`; every other gate names a script" — visible and checkable today, even though today's truthful count is 8 prose-only against a cap of 2: this story does not need to reach the cap, only to state the state honestly and let `verdict-provenance.py check` report the gap as a note. The second Stage 2 spec (gate mechanization) is the one that adds scripts for Gates 0, 0.5, 1, 2.5, 3, 5 and then flips `--prose-only-blocking` on; this story's job is only to lay the frontmatter and checker groundwork that spec builds on. Stage 1's baseline records already carry per-gate `rederived` blocks for `gate2_build` and `gate4_tests` (`GATE_SCRIPT_VERDICTS`, `REDERIVATION_KEYS` in `pipeline-baseline.py`) — this story's ids are chosen to line up with those, not to replace them.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows** [technical-spec.md → ## 5. `scripts/verdict-provenance.py` (Story 4) → Findings: `heading_without_entry`, `entry_without_heading`, `entry_without_source`, `entry_both_sources`, `script_missing`, `unknown_verification_value`] [technical-spec.md → ## 5. → Note: `prose_only_count: <n> (cap <max>)`; Exit codes as §1]
- **Shadow paths** [spec.md → 🎯 Experience Design → Error experience] [technical-spec.md → ## 5. → heading→id fixed table (drift between heading and frontmatter entry is the failure mode this script exists to catch)]
- **Business rules** [spec.md → 📋 Business Rules → 11 (ADR-013 holds — nothing merges, opens a PR, or releases)] [spec.md → 📋 Business Rules → 12 (decision-log line)]
- **Experience** [spec.md → 🎯 Experience Design → Happy path, step 4] [spec.md → 🎯 Experience Design → State catalog]
- **Requirements** [spec.md → Detailed Requirements → Story 4 — Gate verification markers and provenance check] [spec.md → Specification Contract → Deliverable ("every `implement-story` gate carrying an explicit verification marker")]
- **Codebase** [technical-spec.md → ## 5. `scripts/verdict-provenance.py` (Story 4) → full command shape, parsing rules, findings, note] [technical-spec.md → ## 7. Tests → `test_verdict_provenance.py`, `test_eval_verdict_provenance.sh`] [commands/implement-story.md → lines ~141–286, `#### Gate N` headings in Step 3] [scripts/exit-criteria.py → stdlib frontmatter line-parser shape to mirror] [scripts/pipeline-baseline.py → `GATE_NAMES`, `GATE_SCRIPT_VERDICTS`, `REDERIVATION_KEYS`, argparse subcommand and exit-code shape to mirror] [scripts/eval.sh → `check_pipeline_baseline()`, `check_required_sections`, `check_loop_bounds`, and `CHECKS=(...)` registration shape to mirror] [scripts/tests/test_eval_pipeline_baseline.sh → bash fixture test shape to mirror]

---

## What Was Built

**Implementation Date:** 2026-09-07

### Files Created

1. **`scripts/verdict-provenance.py`** (268 lines)
   - `check --command PATH [--repo .] [--max-prose-only 2] [--prose-only-blocking]`. Stdlib, Python 3.9. `parse_gates` is a minimal line parser for the frontmatter `gates:` list (`- id:` plus `script:` or `verification:`; quotes stripped; comments skipped; an entry with no `id` is a `ParseError` → exit 2). `parse_headings` maps body `#### Gate N` headings through the fixed `HEADING_TO_ID` table (ids for 0, 2, 3, 4, 5 equal `pipeline-baseline.py` `GATE_NAMES`). `run_check` emits the six finding codes as `<code>: <file> <gate-id> (<detail>)`, then `note: prose_only_count: <n> (cap <max>)` — or the bare line as a finding when `--prose-only-blocking` and `n > max` — then the summary `gates: N entries, headings: N, script: N, prose-only: N, findings: N`, always last. `script:` paths resolve under `--repo`. Exit 0 / 1 / 2 per technical-spec §1; `_fail` prints `check: error: …` to stderr.
2. **`scripts/tests/test_verdict_provenance.py`** (364 lines)
   - 27 tests: the heading table and its shared ids; parser cases (quotes, absent key, other heading levels); one test per finding code plus a `--repo`-not-cwd resolution test; note-vs-finding under and over the cap, `--max-prose-only`; exit 2 for a missing file, no frontmatter fence, an entry without `id`; and three tests against the real `commands/implement-story.md` (exit 0 with `prose_only_count: 8 (cap 2)`, all ten ids with truthful sources, Gate 4.5 body free of `%` while keeping PASS / SOFT PASS / FAIL).
3. **`scripts/tests/test_eval_verdict_provenance.sh`** (172 lines)
   - 7 assertions in `test_eval_pipeline_baseline.sh`'s shape: clean ten-gate fixture → PASS, exit 0, exactly one `add_note` carrying `prose_only_count: 8 (cap 2)`; three drift fixtures (dropped entry, dropped heading, `verification: manual`) → exit 1, one finding naming code and gate id, note still relayed; missing command file and missing helper → one finding each; `verdict-provenance` in `CHECKS=(...)`, `check_verdict_provenance` defined, and the `"$helper" check` invocation passes no `--prose-only-blocking`.
4. **`.writ/specs/2026-09-07-phase11-stage2-prune-the-base/drift-log.md`**
   - Created with DEV-101 and DEV-102 (Story 4 numbers from DEV-101; Story 1 runs in parallel from DEV-001).

### Files Modified

- **`commands/implement-story.md`** (frontmatter; `#### Gate 4.5: Visual QA (Optional)`)
  - `gates:` block appended after `loop:` with all ten entries: `gate2_build: script: scripts/build-smoke.py`, `gate4_tests: script: scripts/test-integrity.py`, the other eight `verification: prose-only`; a two-line comment explains the keys. `exit_criteria:` and `loop:` untouched. Gate 4.5's Results line no longer names ≥85 / ≥70 / <70; PASS / SOFT PASS / FAIL now key on the agent's mismatch priorities, and one sentence records that the thresholds are gone because no pixel or DOM diff produced them. File grew 29,374 → 30,341 bytes.
- **`scripts/eval.sh`** (`CHECKS=(...)`; new `check_verdict_provenance()` before `run_check`)
  - Registered `verdict-provenance` after `pipeline-baseline`. The check runs `python3 scripts/verdict-provenance.py check --command commands/implement-story.md --repo "$PROJECT_ROOT"` without `--prose-only-blocking`; `note:` lines → `add_note` (with the "not blocking until the mechanization spec" sentence), the summary line → `add_note "Metrics: …"`, every other line → `add_finding "<rel>:<code>"`; exit 2 → one finding quoting the last output line; missing helper or command file → one finding each.
- **`scripts/tests/test_governor_enforcement.py`** (`KNOWN_OVER_BUDGET`)
  - `commands/implement-story.md` pin 4414 → 5381 with a dated comment (DEV-101).
- **`.writ/specs/2026-09-07-phase11-stage2-prune-the-base/spec-lite.md`** (Deliverables)
  - One parenthetical on the `implement-story.md` line recording DEV-102.
- **`.writ/specs/2026-09-07-phase11-stage2-prune-the-base/user-stories/README.md`** (Story 4 row, totals)
- **`.writ/decision-log.md`** (one `2026-09-07 stage-2:` line, Business Rule 12)

### Implementation Decisions

1. **Note lines carry a `note:` prefix; the summary line starts with `gates:`** — technical-spec §1 defines notes as `note:`-prefixed lines, so `eval.sh` can route note vs finding by prefix instead of by code list. The count line is printed on every run (under the cap too) so the number is always visible.
2. **A `gates:` entry without `id` is exit 2, not a finding** — a malformed block is a usage defect in the shape of `pipeline-baseline.py`'s refusals; the six finding codes stay the whole drift vocabulary. A `gates:` key that is absent altogether is not a refusal: every heading becomes `heading_without_entry` (ten findings), which is the honest reading of "no entry".
3. **Unknown gate numbers surface as `heading_without_entry`** — a `#### Gate 6` heading outside the fixed table has, by construction, no entry; it is reported under that code with the placeholder id `gate?6` rather than inventing a seventh code.
4. **Both `script` and `verification` on one entry report `entry_both_sources` and, if the value is not `prose-only`, also `unknown_verification_value`** — one line per condition, no suppression.
5. **Duplicate ids are not detected** — two entries with the same id are each checked against the headings and neither is flagged. Out of the six-code contract; noted for the mechanization spec.
6. **Frontmatter comment kept to two lines** — the block is bytes on a command file the byte cap does not govern, but the governor test pins its overage (DEV-101), so the explanatory comment was cut from six lines to two before the pin was raised.

### Test Results

**Verification:** `uv run --python 3.9 pytest scripts/tests/test_verdict_provenance.py` — 27 passed. `bash scripts/tests/test_eval_verdict_provenance.sh` — 7/7. Full `uv run --python 3.9 pytest -q` — 1044 passed, 1 skipped. All 13 `scripts/tests/test_*.sh` green. `bash scripts/eval.sh` (sandbox disabled) — exit 0, 52/52 checks PASS, 0 findings, 0 run errors; `verdict-provenance` reports the note `prose_only_count: 8 (cap 2)` and `Metrics: gates: 10 entries, headings: 10, script: 2, prose-only: 8, findings: 0`. Single checks `--check=verdict-provenance`, `--check=required-sections`, `--check=loop-bounds` (18/18 scenarios), `--check=exit-criteria` (37/37 scenarios) each exit 0.
- ✅ Red first: the pytest module failed collection before `scripts/verdict-provenance.py` existed; the three real-command tests were red until the `gates:` block and the Gate 4.5 edit landed; the bash test aborted before `check_verdict_provenance` existed.
- ✅ `python3 scripts/verdict-provenance.py check --command commands/implement-story.md` → exit 0, `note: prose_only_count: 8 (cap 2)`; with `--prose-only-blocking` → exit 1, the same line as a finding.
- ⚠️ `test-integrity.py coverage --new-files scripts/verdict-provenance.py` → `unverifiable` (`no_coverage_report`; no coverage tool configured in this repo). `test-integrity.py authenticity --tests scripts/tests/test_verdict_provenance.py` → `test_imports_no_source` (blocking). **Checker false positive, pre-existing:** the extractor is JS-specifier based and Python tests load hyphenated scripts via `spec_from_file_location`; Stage 1 Story 1 recorded the same finding and the issue `2026-09-03-test-integrity-authenticity-flags-every-bash-test.md` tracks it. `test_pipeline_baseline.py` passes the same check only because its fixture strings contain JS `from "../foo"` text. Not treated as DEGRADED; the red-then-green evidence above is the binding proof.
- ⚠️ `build-smoke.py check --project .` → `unverifiable` (`unsupported_stack`); pipeline continued per Gate 2's rule.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Medium (DEV-101), Small (DEV-102)
- **Security:** Low — the script reads one markdown file and stats paths under `--repo`; no subprocess, no writes.
- **Boundary Compliance:** one edit outside the owned list (`scripts/tests/test_governor_enforcement.py`, DEV-101); base files, Story 1 files, `agents/visual-qa-agent.md`, and `.writ/context.md` untouched.

### Deviations from Spec

- **[DEV-101] `KNOWN_OVER_BUDGET` pin raised for `implement-story.md`** — Severity: Medium
  - Spec said: the story touches `commands/implement-story.md` frontmatter, `scripts/`, and `eval.sh`; growth of the command file is out of the byte cap's scope.
  - Reality: `test_governor_enforcement.py` pins the file's overage and failed on +967 bytes; the pin was raised 4414 → 5381 with a dated comment in the file's own convention.
  - Resolution: flagged, pipeline PASS; `spec.md` unchanged.
- **[DEV-102] `agents/visual-qa-agent.md` still carries the 85/70 thresholds** — Severity: Small
  - Spec said: drop the percentage thresholds from the command body's Gate 4.5 section.
  - Reality: done for the command body; the agent definition (outcome, exit criterion, decision list) still names 85 / 70 and is outside this story's boundary.
  - Resolution: logged; `spec-lite.md` amended with one parenthetical; the mechanization spec owns the agent rewrite.
