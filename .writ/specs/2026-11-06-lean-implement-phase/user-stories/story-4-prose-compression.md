# Story 4: Compress implement-phase.md to 240 lines

> **Status:** Not Started
> **Priority:** Normal
> **Dependencies:** Story 3

## User Story

**As a** model reading `/implement-phase` at the start of a phase
**I want to** a command file that names each step and the script it calls, without re-explaining what the scripts enforce
**So that** the orchestrator spends its context on the phase, not on rationale

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.4

- [ ] Given Story 4 is complete, when `wc -l commands/implement-phase.md` runs, then it prints at most 240 `[AC-4.1]`
- [ ] Given every `require_literal "$implement_phase"` line in `scripts/eval.sh`, when `eval.sh` runs, then each literal is still found and no check on `implement-phase.md` fails `[AC-4.2]`
- [ ] Given the phase and exit-criteria tests, when they run after Story 4, then they pass with no assertion changed in this story `[AC-4.3]`
- [ ] Given the rationale removed from `implement-phase.md` (halt versus quarantine, closure keeps the lane branch, phase-branch naming, retry bound), when `.writ/docs/phase-execution-state-format.md` is read, then each appears there under a "Why" subsection `[AC-4.4]`

## Implementation Tasks

- [ ] 4.1 List every pin on `implement-phase.md`: `grep -n 'require_literal "$implement_phase"' scripts/eval.sh` and `grep -rln implement-phase scripts/tests scripts/eval*.py`; record them in the story's Notes before editing `[AC-4.2, AC-4.3]`
- [ ] 4.2 Move the rationale paragraphs from Steps 3.1, 3.2 and 3.3 into "Why" subsections of `.writ/docs/phase-execution-state-format.md` `[AC-4.4]`
- [ ] 4.3 Replace Step 3.3 and the mid-run closure paragraph with an event → subcommand → effect table; reduce the Step 3.2 iteration bound and Step 3.1 phase-branch note to one line each `[AC-4.1, AC-4.2]`
- [ ] 4.4 Merge the Initiative section, the inherited-answer rule and Step 4.3 into the one Question Policy section; cut Step 1.2b to the proposal shape, the Doubt Rule line, create-spec seeding and the close-spec line; shorten the Step 4.2 checker branches to one line each `[AC-4.1, AC-4.2]`
- [ ] 4.5 Run `python3 scripts/gen-platform-trees.py`; replace the `commands/implement-phase.md` entry in `scripts/tests/test_governor_enforcement.py` with a dated entry for the smaller size `[AC-4.1, AC-4.3]`
- [ ] 4.6 Verify acceptance criteria: `wc -l`, the phase and exit-criteria tests and `test_governor_enforcement.py` on Python 3.9, and `bash scripts/eval.sh --report=<scratch path>` (not while pytest runs) `[AC-4.1, AC-4.2, AC-4.3, AC-4.4]`

## Notes

- **Business Rule 7:** this story moves and cuts text only. A test assertion edited here means behavior moved; flag it in review rather than editing it.
- **Pinned literals:** technical-spec.md → Pinned literals lists the strings known on 2026-11-06. Rebuild the list in task 4.1; Stories 1–3 may have changed it.
- **Compression targets:** technical-spec.md → Compression targets gives the per-section plan.
- **Unchanged (Business Rule 8):** verified-only merge, checker verdict governs, human criteria handed off, lane supervisor, quarantine and closure, terminal constraint. Each keeps at least one sentence in the command.
- **Test runs:** run pytest alone. Run `eval.sh` before or after pytest, not during. Full suites (3.9 and 3.14, bash, eval) run once at spec end.

## Context for Agents

- **Error map rows:** [Compression (Story 4)] — from technical-spec.md error map
- **Shadow paths:** []
- **Business rules:** [7, 8] — from spec.md → Specification Contract → 📋 Business Rules
- **Experience:** []
