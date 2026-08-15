# Changelog — Per-Criterion Traceability IDs and an Orphan Check

## 2026-08-13 — Amend AC-2.5 to resolve DEV-4

- **Change type:** Modify existing story (acceptance criterion reword, no new work)
- **What changed:** AC-2.5 in `user-stories/story-2-the-checker.md` reworded from an absolute
  "exits 0" to a criterion that names its own disclosed exception: exits 0, **or** exits 1 with
  only the findings documented as accepted exceptions in `drift-log.md` → DEV-4 as of
  2026-08-13 (`untested_criterion` on Stories 1/2's own criteria; fixture-collision
  `dangling_reference` findings). Any finding outside that named category is still a real
  failure — this is a scoped exception, not a blanket exemption. Checkbox flipped `[ ]` → `[x]`
  since the current, verified dogfood state (14 findings, all matching the documented set)
  satisfies the criterion as reworded. Story 2's Definition of Done "All acceptance criteria
  met" line also flipped to checked.
- **Why:** DEV-4 (recorded during Story 2's implementation) disclosed that AC-2.5's literal
  wording could never be honestly satisfied without either backfilling tests onto
  already-`Completed ✅` stories (forbidden by this spec's own "no retroactive backfill" rule)
  or weakening the checker to hide a real gap (defeats the spec's stated purpose). Left open
  for the spec owner at the time; this edit is that decision.
- **AC IDs assigned:** none
- **AC IDs retired:** none (AC-2.5 keeps its ID — this is a reword, not an insert/delete, per
  this spec's own never-renumber rule)
- **Files updated:**
  - `user-stories/story-2-the-checker.md` — AC-2.5 reworded and checked; Definition of Done
    updated; "What Was Built" → Deviations (DEV-4) note updated to record resolution
  - `user-stories/README.md` — acceptance-criteria summary line updated to 17/17
  - `.writ/context.md` — Recent Drift entry for DEV-4 updated to reflect resolution
- **Backup location:** `backups/20260813T220355Z/` (pre-edit snapshot of `user-stories/` and
  `drift-log.md`)

`drift-log.md`'s DEV-4 entry itself is left unmodified, per that file's own append-only rule —
it remains the accurate historical record of what was found during implementation. This
CHANGELOG entry is the resolution record.
