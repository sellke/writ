# Story 2: Issue-Closure Convention

> **Status:** Completed ✅
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** Writ maintainer reading `/status` and `.writ/context.md` to decide what to work on next
**I want to** mark an issue closed by appending a `## Resolution` section, and have every open-issue count and triage list skip it
**So that** resolved issues stop inflating the open count and the stale-untriaged list without being deleted or moved

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.4

- [x] Given an issue file under `.writ/issues/` containing a line that is exactly `## Resolution`, when `/status` runs Step 5, then that file is skipped before the age and `spec_ref` checks and never appears in the NEEDS TRIAGE list; and a line that merely contains the text (e.g. `## Resolution (2026-09-25)` or `## Resolution` inside a longer line) does not close the issue `[AC-2.1]`
- [x] Given issue files where some are closed, when `/status` Step 8 and `skills/project-context-snapshot/SKILL.md` render `## Open Issues`, then both count only files without a `## Resolution` line, stating the rule in the same words as `status.md` Step 5 `[AC-2.2]`
- [x] Given `commands/create-issue.md`, when a maintainer reads it, then a short "Closing an issue" note says to append `## Resolution` with the date and what changed (commit or branch), and never to delete or move the file `[AC-2.3]`
- [x] Given the edit lands, when `test_governor_enforcement.py` runs, then `commands/status.md` has grown by ≤300 bytes from 24,211, stays under the 24,960-byte budget, and has no `KNOWN_OVER_BUDGET` entry; and the regenerated `.writ/context.md` reports the open-issue count (issue files without a `## Resolution` line at regeneration time), excluding `.writ/issues/bugs/2026-09-26-ac-trace-scans-fixture-ac-tokens.md` `[AC-2.4]`

## Implementation Tasks

- [x] 2.1 Write failing tests in `scripts/tests/test_issue_closure_wiring.py` pinning the literal `## Resolution` rule in `commands/status.md`, `skills/project-context-snapshot/SKILL.md`, and `commands/create-issue.md`, and pinning the skip inside `status.md` Step 5 (before the age check) and the open-only wording on the Step 8 Open Issues line `[AC-2.1, AC-2.2, AC-2.3]`
- [x] 2.2 Add a test that `commands/status.md` is ≤ 24,511 bytes and absent from `KNOWN_OVER_BUDGET` `[AC-2.4]`
- [x] 2.3 Edit `commands/status.md`: a skip step at the top of Step 5's per-file list ("a line exactly `## Resolution` means closed; skip it"), and Step 8's Open Issues line counts open issues only. Keep net growth ≤300 bytes by tightening, not by adding sections `[AC-2.1, AC-2.2, AC-2.4]`
- [x] 2.4 Edit `skills/project-context-snapshot/SKILL.md` `## Open Issues`: count of issue files without a `## Resolution` line (absent-folder degradation unchanged) `[AC-2.2]`
- [x] 2.5 Add the "Closing an issue" note to `commands/create-issue.md` (near Step 5's template or Completion): append `## Resolution` with date and what changed; never delete or move `[AC-2.3]`
- [x] 2.6 Regenerate `.writ/context.md` per `/status` Step 8 so `## Open Issues` excludes the fixture-scan issue `[AC-2.4]`
- [x] 2.7 Verify: `uv run --python 3.9 pytest scripts/tests/test_issue_closure_wiring.py scripts/tests/test_governor_enforcement.py` green; `wc -c commands/status.md` ≤ 24,511; `grep -rlx '## Resolution' .writ/issues` lists only the fixture-scan issue `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`

## Notes

"Exactly" is a whole-line match (`grep -x`, or `line.strip() == "## Resolution"` in the test), so archived verification reports with `## Resolution (2026-09-25)` and any prose mention of the heading don't count. The spec-lite edge case — `## Resolution` inside a code-fence line with other text — is not a heading. Currently 13 issue files exist and one (the fixture-scan bug) already has the heading, so the open count at spec creation was 12; verify the exclusion, not the literal number.

`status.md` has ~750 bytes of headroom and Story 3 does not re-pin it. Spend the 300 bytes on the Step 5 skip and the Step 8 wording only. The report-format example and the "omit this section" sentence need no change.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** spec.md → ## 📋 Business Rules (5 Closed means `## Resolution`)
- **Experience:** spec.md → ### State Catalog (Closed issue row)
- **Technical:** sub-specs/technical-spec.md → ## 2
- **Edge cases:** spec-lite.md → ## For Testing Agents → Edge Cases (`## Resolution` in a fence line)

## What Was Built

**Implementation Date:** 2026-09-26

### Files Modified

1. **`commands/status.md`** — Step 5 per-file list opens with "Skip closed — a file with a line exactly `## Resolution` is closed; skip it", before the age and `spec_ref` checks; Step 8's Open Issues line counts files without that line. 24211 → 24328 bytes (+117). [AC-2.1, AC-2.2, AC-2.4]
2. **`skills/project-context-snapshot/SKILL.md`** — `## Open Issues` schema counts files without a line exactly `## Resolution`; absent-folder fallback unchanged. [AC-2.2]
3. **`commands/create-issue.md`** — "Closing an issue" note before Step 6: append `## Resolution` with the date and what changed (commit or branch); never delete or move the file. [AC-2.3]
4. **`scripts/tests/test_issue_closure_wiring.py`** (new) — 14 tests pinning the rule's wording and position in each surface, the create-issue note, and the `status.md` byte ceiling and `KNOWN_OVER_BUDGET` absence. [AC-2.1, AC-2.2, AC-2.3, AC-2.4]
5. **`.writ/context.md`** — regenerated at spec end with the open-only count. [AC-2.4]

### Verification

- 63 tests (closure wiring + governor) and 79 in related suites pass on Python 3.9; install/update thresholds and eval-leanness bash tests pass; `lint-skill.sh` clean; `grep -rlx '## Resolution' .writ/issues` lists only the fixture-scan bug.
- The coding agent stalled after writing its edits; the orchestrator verified and finished the story.
- Gate 3: `review-agent` (routed by boundary crossings) PASS, two Low findings (regeneration timing, a self-referential helper test kept as documentation).
- Drift: DEV-011, Small.
