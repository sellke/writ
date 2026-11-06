# Story 1: Gate declarations and evidence

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer
**I want to** declare, for each gate in `commands/implement-story.md`, the failure it catches, its recorded evidence, and a checkable removal condition
**So that** gates with no recorded catch can be moved to `--full-pipeline` with a traceable reason

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [ ] Given a `gates:` entry in `commands/implement-story.md` that lacks `catches:`, `evidence:`, or `kill_when:`, when `verdict-provenance.py check` runs, then it reports `missing_catches`, `missing_evidence`, or `missing_kill_when` for that gate `[AC-1.1]`
- [ ] Given a `gates:` entry whose `path:` is neither `default` nor `full-pipeline`, when the check runs, then it reports `unknown_path_value` for that gate, and an entry with no `path:` produces no finding `[AC-1.2]`
- [ ] Given every `gates:` entry has all three fields and a valid or absent `path:`, when the check runs, then it reports no new finding codes, and existing finding codes and exit codes are unchanged `[AC-1.3]`
- [ ] Given `gate-evidence.md`, when it is read, then it has one row per `gates:` entry giving a dated catch citation or `none recorded`, the dependency reason if any, and a path decision that follows Business Rules 2 and 3 (`full-pipeline` only for `none recorded` with no kept dependent) `[AC-1.4]`
- [ ] Given Story 1 is complete, when the diff of `commands/implement-story.md` is read, then only `gates:` frontmatter lines changed, and no gate section, script call, or prose changed `[AC-1.5]`

## Implementation Tasks

- [ ] 1.1 Write tests in `scripts/tests/test_verdict_provenance.py` for the three missing-field codes, `unknown_path_value`, and an absent `path:` producing no finding `[AC-1.1, AC-1.2]`
- [ ] 1.2 Extend `scripts/verdict-provenance.py` `check` to emit `missing_catches`, `missing_evidence`, `missing_kill_when`, and `unknown_path_value`, and to read the optional `path:` key. Existing codes and exit codes stay unchanged `[AC-1.1, AC-1.2, AC-1.3]`
- [ ] 1.3 Write `.writ/specs/2026-11-06-lean-story-pipeline/gate-evidence.md` with one row per gate: the catch citation or `none recorded`, the dependency reason under Business Rule 3, and the path decision `[AC-1.4]`
- [ ] 1.4 Add `catches:`, `evidence:`, `kill_when:`, and `path:` to each `gates:` entry in `commands/implement-story.md`, using the values recorded in `gate-evidence.md`. Change no body text `[AC-1.4, AC-1.5]`
- [ ] 1.5 Run `verdict-provenance.py check` on the updated `commands/implement-story.md`. Confirm zero findings and exit 0, and confirm `test_verdict_provenance.py` passes `[AC-1.3]`
- [ ] 1.6 Verify `git diff` of `commands/implement-story.md` touches only `gates:` frontmatter, and that `test_eval_verdict_provenance.sh` and `test_implement_story_default_path.py` pass `[AC-1.5]`

## Notes

- **Evidence sources.** Cite only dated artifacts that show a gate changing an outcome: `.writ/retros/2026-10-30-phase-15.md` (for example F26), `.writ/specs/2026-10-25-gate-upgrade-removal-measurement/trial-report.md`, `.writ/eval/supervisor-trial/report.md`, `.writ/specs/2026-11-06-lean-story-tasks/trial-report.md`, `gate3-review-*` records, and fix commits. "Would catch X" is not evidence (spec Business Rule 1).
- **Kept gates stay on the default path.** Safety Fact, Reviewer Filters, Gate 0 Divergence, and the ADR-032 evidence gate are not demoted. Their inputs stay too: `gate2_5_surface` (change-surface) feeds the risk route that turns Safety Fact on, so it keeps `path: default` with that dependency as its reason (Business Rule 3). Record each kept gate in `gate-evidence.md` as staying on the default path.
- **kill_when must be checkable.** Write it as a condition over `story-gate.py tally` output or a named file, for example `sole_catches == 0 over 20 default-path records`. Story 1 does not build the tally; the wording only has to be checkable later (Business Rule 7).
- **Parser.** `verdict-provenance.py` uses a line parser with no YAML library. Confirm that quoted values containing `:`, `==`, or `.` parse as plain scalars before relying on them.
- **No behavior change.** This story only declares and records. The 42 test and eval files that pin text in `implement-story.md` read the body, so frontmatter-only edits should not break them. `test_gate_upgrade_trial_outcome.py` ties kept upgrades to presence probes in that file and must keep passing.
- **Byte size.** Frontmatter additions grow `implement-story.md`. `KNOWN_OVER_BUDGET` in `scripts/tests/test_governor_enforcement.py` may need a dated entry, but the spec assigns those entries to Stories 2–5 only. If that test fails here, raise it with the maintainer before adding an entry.
- **Targeted verification only.** Run this story's test files. The full pytest suite and `eval.sh` run once at the end of the spec, not per story. Run pytest alone: `eval.sh`, bash tests, writes under `.writ/state/`, or `git worktree` changes in the same checkout during pytest break `test_smoke_leaves_repo_unchanged`.
- **Interpreters.** Targeted pytest runs must pass on Python 3.9, the floor. Stdlib only.

## Context for Agents

- **Business rules:** [Business Rule 1, Business Rule 3, Business Rule 7]
- **Error map rows:** []
- **Shadow paths:** []
- **Experience:** []
