# Story 4: Edit-Spec Stability Guard

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** developer editing a spec whose criteria are already cited by tasks and tests
**I want** `/edit-spec` to assign new IDs from the high-water mark and never renumber a sibling
**So that** every citation written before the edit still points at the criterion it was written
for, instead of silently pointing at a different one

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.4

- [ ] Given a story with criteria `AC-2.1` through `AC-2.4` and a marker reading `AC-2.4`, when `/edit-spec` inserts a criterion anywhere in the list, then the new criterion is `AC-2.5`, the marker advances to `AC-2.5`, and all four existing ID tags are byte-identical to their pre-edit state. `[AC-4.1]`
- [ ] Given `/edit-spec` removes a criterion, when the edit completes, then its ID is retired rather than reused, the marker does not move, and any task or test still citing the retired ID is surfaced during the edit as a reference to repoint or delete. `[AC-4.2]`
- [ ] Given a legacy story with no marker and no IDs, when `/edit-spec` adds its first identified criterion, then a marker line is created beneath the `## Acceptance Criteria` heading and the story leaves the edit fully adopted rather than partially. `[AC-4.3]`
- [ ] Given any edit that assigns or retires an ID, when the spec's `CHANGELOG.md` is appended, then it records the IDs assigned and the IDs retired. `[AC-4.4]`

## Implementation Tasks

- [ ] 4.1 Write the guard assertions first — fixture story edited by each of the three shapes (insert, remove, first adoption), asserting sibling IDs are byte-identical and the marker moved only on insert `[AC-4.1, AC-4.2, AC-4.3]`
- [ ] 4.2 Add the never-renumber rule and marker-advance procedure to `commands/edit-spec.md` Step 2.2 story-management rules `[AC-4.1]`
- [ ] 4.3 Add the retirement rule — retired IDs are never reused, and the edit surfaces surviving citations of a retired ID before it completes `[AC-4.2]`
- [ ] 4.4 Add the first-adoption rule: a legacy story gaining its first ID gains a marker, and leaves the edit fully adopted, never partially `[AC-4.3]`
- [ ] 4.5 Extend the Step 2.1 `CHANGELOG.md` entry shape to record assigned and retired IDs `[AC-4.4]`
- [ ] 4.6 Verify acceptance criteria are met — run `/edit-spec` against a fixture spec through all three edit shapes and diff the story files `[AC-4.1, AC-4.2, AC-4.3]`
- [ ] 4.7 Verify all tests pass `[AC-4.1, AC-4.4]`

## Notes

**Technical considerations:** This is the story the source issue named as the main design risk,
and it is the only story that can invalidate the other three retroactively. The high-water mark
makes stability structural rather than a matter of editorial care — but only if `/edit-spec`
actually reads the marker before assigning. An edit that counts the criteria and adds one is
the exact failure mode the mark exists to prevent, and it will look correct on every story
where nothing has ever been deleted.

**Risks:** Partial adoption as a side effect. Task 4.4 exists because the natural way to add
one criterion to a legacy story is to tag just that one — producing precisely the
`partial_adoption` state Story 2 reports as blocking. `/edit-spec` must either identify the
whole story's criteria or none of them.

Second risk: an edit that removes a criterion whose ID is still cited by a passing test. The
test then proves something the spec no longer asks for. Surfacing it during the edit is the
cheap moment to resolve it; discovering it later as a `dangling_reference` is the expensive one.

**Why this depends on Story 1, not Story 3:** the guard needs the grammar and the marker rule,
not the checker. It can land before or after the `/verify-spec` wiring, so it does not sit on
Story 2's critical path.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** `partial_adoption` is blocking while `legacy_story` is not — from
  spec.md → ## 📋 Business Rules → ### Severity reasoning; retired-ID and no-backfill posture —
  from spec.md → ## 📋 Business Rules → ### Legacy and archive posture
- **Experience:** The high-water mark rule and its worked insert/delete example — from
  spec.md → ## 📐 The Grammar → ### The high-water mark, including the two rejected
  alternatives (content-hash IDs, positional + prose rule) that must not be reintroduced here
- **Edge cases:** Insert, remove, and first-adoption edit shapes — from
  sub-specs/technical-spec.md → ## Interaction Edge Cases
- **Files to read:** `commands/edit-spec.md` Step 2.1 (backup and CHANGELOG) and Step 2.2
  (story-management rules) — both change
