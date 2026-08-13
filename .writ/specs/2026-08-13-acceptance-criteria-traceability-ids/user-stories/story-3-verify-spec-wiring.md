# Story 3: Verify-Spec Wiring

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 2

## User Story

**As a** developer running `/verify-spec` on a spec that claims to be finished
**I want** the orphan findings to appear inside Check 3 Completion Integrity as blocking
failures
**So that** a criterion nothing implements or tests contradicts the `Completed ✅` claim in the
same place and with the same weight as Check 3a's false completion

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.4

- [ ] Given `commands/verify-spec.md` after this change, when Check 3 is read, then 3e (criterion coverage) and 3f (dangling and malformed references) exist, each naming the `scripts/ac-trace.py check` invocation as its executable reference and its blocking classification — and the command's check table still has exactly eight rows. `[AC-3.1]`
- [ ] Given `/verify-spec` on a spec with orphan findings, when the verification report is written, then the Check 3 row reports failure and every finding appears once in Outstanding Warnings with its finding code and criterion ID. `[AC-3.2]`
- [ ] Given the same spec under `/verify-spec --check`, when the output is compared to default mode, then the 3e/3f findings are identical — these checks are report-only and Phase 4 never touches them. `[AC-3.3]`
- [ ] Given a legacy spec whose stories carry no IDs at all, when the check runs, then it reports `legacy_story` informationally and raises no blocking finding. `[AC-3.4]`

## Implementation Tasks

- [ ] 3.1 Write the wiring assertions first — a check that `commands/verify-spec.md` contains the 3e/3f sub-checks, the executable-reference invocation, and still exactly eight check-table rows `[AC-3.1]`
- [ ] 3.2 Add Check 3e (criterion coverage: `untasked_criterion`, `untested_criterion`) under Check 3 Completion Integrity `[AC-3.1, AC-3.2]`
- [ ] 3.3 Add Check 3f (`dangling_reference`, `duplicate_id`, `marker_violation`, `partial_adoption`) with the same executable reference `[AC-3.1, AC-3.2]`
- [ ] 3.4 Record the auto-fix boundary explicitly — 3e/3f are report-only inside default mode; Phase 4's fix list is unchanged `[AC-3.3]`
- [ ] 3.5 Document the legacy posture in the check text: zero IDs is informational, partial adoption is blocking `[AC-3.4]`
- [ ] 3.6 Verify acceptance criteria are met — run `/verify-spec` against one spec with seeded findings and one legacy spec, comparing default and `--check` output `[AC-3.2, AC-3.3, AC-3.4]`
- [ ] 3.7 Verify all tests pass `[AC-3.1]`

## Notes

**Technical considerations:** These are sub-checks of Check 3, not a new Check 9. The reason is
concrete rather than aesthetic: `commands/verify-spec.md`'s own `exit_criteria` promise "an
eight-row check table," so a ninth check would falsify the command's frontmatter and, through
it, `scripts/exit-criteria.py`'s verdict on this command. Adding 3e/3f keeps the row count and
matches the source issue's framing — same failure class as 3a.

**Risks:** The auto-fix temptation. `/verify-spec` default mode fixes what it safely can, and
an `untasked_criterion` looks trivially fixable by appending the ID to some plausible task. It
is not: choosing which task covers a criterion is the authorial judgment the check exists to
demand, and a machine-appended tag would produce a satisfied check with no trace link behind
it — worse than the finding it silenced.

Second risk: double-reporting. A finding must appear in exactly one of Issues Found & Resolved
or Outstanding Warnings, per this command's second exit criterion. Since nothing here is
auto-fixed, every 3e/3f finding belongs in Outstanding Warnings and never in the resolved
section.

**Integration:** Story 2's script is the authority. This story adds no parsing logic of its own
— if the command file and the script disagree about a severity, the script is right and the
command text is the defect.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** Severity table and the auto-fix boundary — from spec.md → ## 📋 Business
  Rules → ### Auto-fix boundary; legacy and archive posture — from spec.md → ## 📋 Business
  Rules → ### Legacy and archive posture
- **Experience:** Feedback model (findings in Check 3 rows plus Outstanding Warnings, each
  citing file and criterion text) and the exit-1-versus-exit-2 distinction — from spec.md →
  ## 🎯 Experience Design
- **Precedent to mirror:** Check 4d in `commands/verify-spec.md` — a blocking check with a
  named executable reference (`scripts/spec-deps.py validate`), named finding codes, and an
  explicit statement of what may and may not be auto-fixed
