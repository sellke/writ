# Story 4: Gate Verification Markers and Provenance Check — gates: Frontmatter, verdict-provenance.py, and the verdict-provenance Eval Check

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer who needs every Step 3 gate's verdict source declared so the honor-system gates in `implement-story.md` are visible rather than implicit, **I want to** add a `gates:` block to the command's frontmatter naming each gate's `script` or `prose-only` verification, and get a `verdict-provenance.py check` command wired into `eval.sh` that fails when a gate heading and its frontmatter entry drift apart, **so that** the mechanization spec (the second Stage 2 spec) has a truthful, checkable starting count of how many gates still run on prose alone.

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.5

- [ ] Given `commands/implement-story.md` after this story lands, when its frontmatter `gates:` block is read, then it names all ten Step 3 gate ids (`gate0_arch`, `gate0_5_boundary`, `gate1_coding`, `gate2_build`, `gate2_5_surface`, `gate3_review`, `gate3_5_drift`, `gate4_tests`, `gate4_5_visual`, `gate5_docs`) with truthful sources — `gate2_build: script: scripts/build-smoke.py` and `gate4_tests: script: scripts/test-integrity.py`, the other eight `verification: prose-only` — and `python3 scripts/verdict-provenance.py check --command commands/implement-story.md` exits 0 printing the note `prose_only_count: 8 (cap 2)` `[AC-4.1]`
- [ ] Given fixture command files with one drift each (a `#### Gate N` heading with no matching frontmatter entry; a frontmatter entry with no matching heading; an entry carrying neither `script` nor `verification`; an entry carrying both; a `script:` path that does not exist on disk; a `verification:` value other than `prose-only`), when `check` runs against each fixture, then it prints the corresponding finding (`heading_without_entry`, `entry_without_heading`, `entry_without_source`, `entry_both_sources`, `script_missing`, `unknown_verification_value`) naming the fixture file and the gate id, and exits 1 `[AC-4.2]`
- [ ] Given a command file with more than `--max-prose-only` (default 2) `verification: prose-only` entries, when `check` runs without `--prose-only-blocking`, then it prints `prose_only_count: <n> (cap <max>)` as a note and exits 0 on that condition alone, and when run with `--prose-only-blocking`, then the same line is a finding and exit is 1 `[AC-4.3]`
- [ ] Given `bash scripts/eval.sh` runs after this story lands, when the `verdict-provenance` check executes `check_verdict_provenance()` against the real `commands/implement-story.md`, then every `verdict-provenance.py` finding surfaces via `add_finding`, the `prose_only_count` line surfaces via `add_note` (not blocking, per technical-spec §5), and the overall eval.sh exit stays 0 with 0 findings `[AC-4.4]`
- [ ] Given `#### Gate 4.5: Visual QA (Optional)` in `commands/implement-story.md`'s body after this story lands, when the section is read, then it names no percentage threshold and still uses PASS / SOFT PASS / FAIL vocabulary, and `check_required_sections` and `check_loop_bounds` in `eval.sh` (which already parse this file's frontmatter) stay green `[AC-4.5]`

## Implementation Tasks

- [ ] 4.1 Write `scripts/tests/test_verdict_provenance.py` (pytest, fixture command files per technical-spec §7: complete block, missing entry, extra entry, both keys, missing script, unknown verification value, prose-only count over cap as note vs. finding) and `scripts/tests/test_eval_verdict_provenance.sh` mirroring `scripts/tests/test_eval_pipeline_baseline.sh`'s fixture shape `[AC-4.1]` `[AC-4.2]` `[AC-4.3]` `[AC-4.4]`
- [ ] 4.2 Implement the frontmatter and heading parser in `scripts/verdict-provenance.py` (stdlib, Python 3.9 floor, no PyYAML — a minimal line parser mirroring `scripts/exit-criteria.py`'s approach): read the `gates:` list of `{id, script?, verification?}` from frontmatter, read `#### Gate N` headings from the body, and map both to the fixed heading→id table from technical-spec §5 (`Gate 0`→`gate0_arch`, `0.5`→`gate0_5_boundary`, `1`→`gate1_coding`, `2`→`gate2_build`, `2.5`→`gate2_5_surface`, `3`→`gate3_review`, `3.5`→`gate3_5_drift`, `4`→`gate4_tests`, `4.5`→`gate4_5_visual`, `5`→`gate5_docs`) `[AC-4.1]` `[AC-4.2]`
- [ ] 4.3 Implement `verdict-provenance.py check` (argparse subcommand, `_fail`/`_refuse` exit-2 pattern mirroring `pipeline-baseline.py`): the six finding codes, `script_missing` resolved relative to `--repo`, the `prose_only_count: <n> (cap <max>)` note-vs-finding split on `--prose-only-blocking`, the summary line, and exit codes 0/1/2 `[AC-4.1]` `[AC-4.2]` `[AC-4.3]`
- [ ] 4.4 Add the `gates:` block to `commands/implement-story.md` frontmatter with all ten entries and truthful sources per technical-spec §5, without disturbing the existing `exit_criteria:` and `loop:` keys `[AC-4.1, AC-4.5]`
- [ ] 4.5 Edit `commands/implement-story.md`'s `#### Gate 4.5: Visual QA (Optional)` body to drop percentage thresholds while keeping the PASS / SOFT PASS / FAIL vocabulary, per the assessment's "an actual pixel or DOM diff or drop the percentage" `[AC-4.5]`
- [ ] 4.6 Register `check_verdict_provenance()` in `scripts/eval.sh` next to `check_pruned_base()`, added to the `CHECKS=(...)` array as `verdict-provenance`, not count-blocking (no `--prose-only-blocking` flag passed) yet; relay findings via `add_finding` and the `prose_only_count` line via `add_note` `[AC-4.3]` `[AC-4.4]`
- [ ] 4.7 Verify all acceptance criteria: `uv run --python 3.9 pytest scripts/tests/test_verdict_provenance.py` green, `bash scripts/tests/test_eval_verdict_provenance.sh` green, `bash scripts/eval.sh` shows 0 findings including `check_required_sections` and `check_loop_bounds` still passing, and append the decision-log line `{date} stage-2: Story 4 — gates: frontmatter block, verdict-provenance.py check, eval.sh verdict-provenance check landed` to the story's completion commit `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`

## Notes

**Technical considerations.** The heading→id table is fixed and shared with `pipeline-baseline.py`'s `GATE_NAMES` (`gate0_arch`, `gate2_build`, `gate3_review`, `gate4_tests`, `gate5_docs` already match) so a later join between the two scripts' output is free — do not invent a different naming scheme for the other five ids. No YAML library: the frontmatter parser is a minimal stdlib line parser in the shape of `scripts/exit-criteria.py`, not a general YAML reader, so it only needs to understand the `gates:` list's fixed two-key-per-entry shape. `script_missing` checks the path relative to `--repo`, the same convention `prune-ledger.py` and `pipeline-baseline.py` use for repo-relative paths.

**Risks.** Adding a `gates:` block grows `commands/implement-story.md`'s frontmatter — that is itself bytes, but `implement-story.md` is a command file, not one of the two base files (`system-instructions.md`, `commands/_preamble.md`) the byte cap in Stories 1–3 governs, so this growth is out of scope for the cap and must not be treated as a pruning target. Existing frontmatter parsers in `eval.sh` (`check_required_sections`, `check_loop_bounds`) already read this file's frontmatter for other keys — adding `gates:` must not break their parsing, which is why AC-4.5 requires both to stay green.

**Integration with later stories.** This story runs independent of Stories 2 and 3 (it touches only `commands/implement-story.md`'s frontmatter, `scripts/`, and `eval.sh`, never the two base files or the ledger) and independent of Story 5 (baselines don't read the `gates:` block). It is the story that makes the Goal Card's DONE WHEN line 4 target — "at most 2 gates `verification: prose-only`; every other gate names a script" — visible and checkable today, even though today's truthful count is 8 prose-only against a cap of 2: this story does not need to reach the cap, only to state the state honestly and let `verdict-provenance.py check` report the gap as a note. The second Stage 2 spec (gate mechanization) is the one that adds scripts for Gates 0, 0.5, 1, 2.5, 3, 5 and then flips `--prose-only-blocking` on; this story's job is only to lay the frontmatter and checker groundwork that spec builds on. Stage 1's baseline records already carry per-gate `rederived` blocks for `gate2_build` and `gate4_tests` (`GATE_SCRIPT_VERDICTS`, `REDERIVATION_KEYS` in `pipeline-baseline.py`) — this story's ids are chosen to line up with those, not to replace them.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows** [technical-spec.md → ## 5. `scripts/verdict-provenance.py` (Story 4) → Findings: `heading_without_entry`, `entry_without_heading`, `entry_without_source`, `entry_both_sources`, `script_missing`, `unknown_verification_value`] [technical-spec.md → ## 5. → Note: `prose_only_count: <n> (cap <max>)`; Exit codes as §1]
- **Shadow paths** [spec.md → 🎯 Experience Design → Error experience] [technical-spec.md → ## 5. → heading→id fixed table (drift between heading and frontmatter entry is the failure mode this script exists to catch)]
- **Business rules** [spec.md → 📋 Business Rules → 11 (ADR-013 holds — nothing merges, opens a PR, or releases)] [spec.md → 📋 Business Rules → 12 (decision-log line)]
- **Experience** [spec.md → 🎯 Experience Design → Happy path, step 4] [spec.md → 🎯 Experience Design → State catalog]
- **Requirements** [spec.md → Detailed Requirements → Story 4 — Gate verification markers and provenance check] [spec.md → Specification Contract → Deliverable ("every `implement-story` gate carrying an explicit verification marker")]
- **Codebase** [technical-spec.md → ## 5. `scripts/verdict-provenance.py` (Story 4) → full command shape, parsing rules, findings, note] [technical-spec.md → ## 7. Tests → `test_verdict_provenance.py`, `test_eval_verdict_provenance.sh`] [commands/implement-story.md → lines ~141–286, `#### Gate N` headings in Step 3] [scripts/exit-criteria.py → stdlib frontmatter line-parser shape to mirror] [scripts/pipeline-baseline.py → `GATE_NAMES`, `GATE_SCRIPT_VERDICTS`, `REDERIVATION_KEYS`, argparse subcommand and exit-code shape to mirror] [scripts/eval.sh → `check_pipeline_baseline()`, `check_required_sections`, `check_loop_bounds`, and `CHECKS=(...)` registration shape to mirror] [scripts/tests/test_eval_pipeline_baseline.sh → bash fixture test shape to mirror]
