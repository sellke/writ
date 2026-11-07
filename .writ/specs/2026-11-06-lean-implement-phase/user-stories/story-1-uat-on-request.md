# Story 1: UAT plans on request

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** developer running `/implement-phase`
**I want to** UAT plans generated only when I pass `--uat` or run `/create-uat-plan` myself
**So that** a phase stops spending tokens on human-only scenarios nobody asked for

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [ ] Given a phase state file with `uatRequested: false` and merged specs with no `uat-plan.md`, when `exit-criteria.py check --command implement-phase` runs, then `implement-phase.c2` is `met` with evidence `UAT not requested` `[AC-1.1]`
- [ ] Given a phase state file with `uatRequested: true` and a merged spec with a missing or stub `uat-plan.md`, when the checker runs, then c2 is `unmet` naming that spec `[AC-1.2]`
- [ ] Given a phase state file with no `uatRequested` key, when the checker runs, then c2 checks plans as if `uatRequested` were true `[AC-1.3]`
- [ ] Given `commands/implement-phase.md`, when Story 1 is complete, then the Invocation table lists `--uat`, Step 3.2 runs `/create-uat-plan` only when `uatRequested` is true, Step 1.3 skips specs by phase state and story status rather than by `uat-plan.md`, and the Step 4.2 report prints `/create-uat-plan {spec}` lines when UAT was not requested `[AC-1.4]`
- [ ] Given the new c2 text, when `bash scripts/eval.sh --check=exit-criteria` runs, then it reports no finding and the same text appears in the command frontmatter, `scripts/exit-criteria.py`, `scripts/eval.sh` and `.writ/docs/exit-criteria-classification.md` `[AC-1.5]`

## Implementation Tasks

- [ ] 1.1 Write failing tests in `scripts/tests/test_exit_criteria.py` for c2 with `uatRequested` false, true, and absent, and in `scripts/tests/test_phase_state.py` for `init --uat` writing `uatRequested` `[AC-1.1, AC-1.2, AC-1.3]`
- [ ] 1.2 Add `--uat` to `phase-state.py init` and the top-level `uatRequested` field; document it in `.writ/docs/phase-execution-state-format.md` `[AC-1.1, AC-1.3]`
- [ ] 1.3 Change `_predicate_phase_c2` and its criterion constant in `scripts/exit-criteria.py`; update the c2 text in `scripts/eval.sh` and `.writ/docs/exit-criteria-classification.md` `[AC-1.1, AC-1.2, AC-1.3, AC-1.5]`
- [ ] 1.4 Edit `commands/implement-phase.md`: frontmatter c2, Invocation `--uat`, Step 1.3 resume order, Step 2.3 plan line, Step 3.2 item 6, Step 4.2 report, Integration table, Completion; update the `/implement-phase` rows and pipeline line in `README.md` and `SKILL.md` `[AC-1.4, AC-1.5]`
- [ ] 1.5 Run `python3 scripts/gen-platform-trees.py`; add a dated `KNOWN_OVER_BUDGET` entry in `scripts/tests/test_governor_enforcement.py` if the byte size grew `[AC-1.4]`
- [ ] 1.6 Verify acceptance criteria: run `test_exit_criteria.py`, `test_phase_state.py`, `test_governor_enforcement.py` on Python 3.9, and `bash scripts/eval.sh --check=exit-criteria --report=<scratch path>` `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

## Notes

- **Business Rule 2, old state files:** a missing `uatRequested` must read as true so finished runs keep their checker verdicts. The existing c2 tests at `test_exit_criteria.py` lines ~511–564 build state without the key; they must keep passing unchanged.
- **Criterion text:** "when UAT plans were requested, each merged spec folder contains a populated uat-plan.md generated after that spec was implemented". The four copies must match byte for byte.
- `check-uat --spec DIR` and `/create-uat-plan` are unchanged.
- `--resume --uat` on a run started without `--uat` sets `uatRequested: true` from then on (technical-spec.md → Interaction Edge Cases).
- **Test runs:** run pytest alone. `eval.sh` in the same checkout during pytest breaks `test_smoke_leaves_repo_unchanged`. Use `--report=<scratch path>` so eval writes nothing into the tree. Full suites run once at spec end.
- **Symlinks:** `.claude/` and `.cursor/` point at product source. Do not run `install.sh` on this repo.

## Context for Agents

- **Error map rows:** [c2 change (Story 1), Resume (Story 1)] — from technical-spec.md error map
- **Shadow paths:** [Happy path, Nil input, Empty input, Upstream error] — from technical-spec.md
- **Business rules:** [1, 2, 3] — from spec.md → Specification Contract → 📋 Business Rules
- **Experience:** [Entry point, Moment of truth, Error experience] — from spec.md → 🎯 Experience Design
