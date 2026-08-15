# Story 6: Adoption — Baseline at Initialize, Visibility at Status

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 2, Story 3

## User Story

**As a** developer adopting Writ on a codebase that already has years of quality debt
**I want** the first run to record what is already wrong instead of blocking on it, and my
project's own coverage floor written where the project enforces it
**So that** the checks are survivable on day one and the debt is visible and dated rather than
either invisible or paralyzing

## Acceptance Criteria

> **AC IDs assigned through:** AC-6.5

- [ ] Given `/initialize` runs on a brownfield project with existing quality-config findings, when it completes, then `.writ/quality-baseline.md` exists recording each finding with the date and a rationale line, and those findings are acknowledged rather than blocking on subsequent runs. `[AC-6.1]`
- [ ] Given a project with a coverage tool and measured coverage below the nominal bar, when `/initialize` writes a threshold, then the value written is the measured floor rather than 80% or any other aspiration, so the number can only ratchet upward and the first run after adoption does not break the project's build. `[AC-6.2]`
- [ ] Given a finding not present in the baseline appears on a later run, when the check runs, then it is reported as new and blocks, and the baseline is not rewritten to absorb it automatically. `[AC-6.3]`
- [ ] Given `/status` runs, when the quality-config findings are surfaced, then only pure file-read results appear — no build, test, or git-mutating command runs — satisfying `/status`'s third exit criterion, and the verdict uses the existing `Healthy` / `Warning` / `Attention` vocabulary rather than a fourth scheme. `[AC-6.4]`
- [ ] Given a project with no findings, or one where `.writ/quality-baseline.md` is absent, when `/status` runs, then the section is omitted entirely rather than rendering an empty block — matching how Step 5's stale-issue block and Step 4's phase-health block already behave. `[AC-6.5]`

## Implementation Tasks

- [ ] 6.1 Add the quality-config audit to `/initialize`'s brownfield Phase 3 Gap Analysis, where `ignoreBuildErrors` maps onto **Technical debt** and the existing prioritization principle — "lead with gaps that cause silent bugs" — already describes it `[AC-6.1]`
- [ ] 6.2 Specify the `.writ/quality-baseline.md` write in `/initialize`, following Story 1's format, including the greenfield case where the baseline is empty by construction `[AC-6.1, AC-6.3]`
- [ ] 6.3 Specify the coverage-floor write: measure current coverage, write `floor(measured)` into the project's coverage config, and record the value and date. Note that brownfield `/initialize` is otherwise read-only with respect to target-project config, so this write needs the same explicit confirmation the `.writ/config.md` write already carries `[AC-6.2]`
- [ ] 6.4 Add the findings surface to `/status` Step 7 Project Health Signals as pure file reads, with the omit-if-empty behavior of Steps 4 and 5 `[AC-6.4, AC-6.5]`
- [ ] 6.5 Confirm any suggested next action drawn from the findings uses only commands on `/status`'s allowlist — `/initialize` is on it; anything else must be plain English `[AC-6.4]`
- [ ] 6.6 Extend `scripts/eval.sh`'s `check_quality_config_audit()` with `require_literal` bindings asserting the `/initialize` and `/status` wiring prose, following how `check_ac_trace` binds `verify-spec.md`'s Check 3e/3f `[AC-6.1, AC-6.4]`
- [ ] 6.7 Verify `bash scripts/eval.sh` passes and `/status`'s no-build-no-test exit criterion still holds by inspection `[AC-6.4]`

## Notes

**Technical considerations:** `/status`'s third exit criterion is a hard constraint, not a
preference: *"every execution state file under `.writ/state/` was read without being written,
and no build, test or git-mutating command ran"*, restated as a terminal constraint at
`commands/status.md:477`. Only the config audit — pure file reads — may appear there.
Coverage re-derivation and build smoke run tooling and must not.

`/status` already has a categorical health verdict worth matching rather than duplicating:
`scripts/phase-state.py health` renders `Healthy` / `Warning` / `Attention`, where missing or
stale evidence is a Warning ("never a silent pass") and `Attention` requires an affirmative
current failure. That is the same trichotomy this spec calls `pass` / `unverifiable` / `fail`.

`/initialize`'s asymmetry matters for task 6.3: greenfield writes real project config
unconditionally, while brownfield is read-only with respect to target-project config and asks
before writing even `.writ/config.md`. Writing a coverage threshold into an existing project is
a brownfield mutation and should carry at least the same confirmation.

**Risks:** The baseline is the mechanism that makes adoption survivable and also the mechanism
most likely to hollow the whole spec out. A baseline that grows on each run is a disabled
check. Make re-baselining a deliberate, dated, human act — and consider whether the baseline
should record a count that can only decrease.

Second risk: `/status` is meant to orient in under ten seconds. A findings block that lists
forty baselined items defeats the command. Surface the count and the new findings; leave the
enumeration to the baseline file.

**Integration:** `.writ/config.md` already carries `**Test Coverage Tool:** jest --coverage`
(see `commands/initialize.md:106` and `.writ/docs/config-format.md`), which is the natural
anchor for coverage-tool detection — no new artifact needed for that half. The baseline is a
new artifact and does need Story 1's format.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** baseline-then-ratchet, coverage thresholds at the measured floor, the
  `/status` read-only constraint, verdict vocabulary alignment — from `spec.md` →
  `## 📋 Business Rules` and `## Implementation Approach`
- **Shadow paths:** Read baseline (absent → empty, every finding new), Read baseline
  (malformed → exit 2, never ignored) — from `sub-specs/technical-spec.md` →
  `## Error & Rescue Map`
- **Insertion points:** `/initialize` brownfield Phase 3 Gap Analysis; `/status` Step 7
  Project Health Signals; the omit-if-empty precedent in `/status` Steps 4 and 5
- **Precedent to mirror:** `check_ac_trace`'s `require_literal` bindings against
  `commands/verify-spec.md` for asserting command-file wiring prose
