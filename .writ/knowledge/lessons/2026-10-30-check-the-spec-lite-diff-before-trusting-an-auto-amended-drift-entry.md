---
category: lessons
tags: [phase-close, drift, implement-phase]
created: 2026-10-30
related_artifacts:
  - .writ/specs/2026-10-25-repro-first-bug-fixing/drift-log.md
  - .writ/specs/2026-10-25-retro-fix-ladder/drift-log.md
  - skills/drift-triage/SKILL.md
---

# Check the spec-lite diff before trusting an Auto-amended drift entry

## TL;DR

Lane runs logged Small drift as 'Resolution: Auto-amended' without editing spec-lite.md: Phase 15 has 65 Auto-amended entries across six specs and one spec-lite edit (design-divergence Story 3). implement-story's drift handling and the drift-triage skill amend spec-lite.md only, and never the technical spec, so after a lane both files describe the plan and the drift log alone describes the build. Before relying on spec-lite.md or the technical spec after a lane, compare `git log -- <spec>/spec-lite.md` with the drift log's Auto-amended count; UAT authors follow the drift log where they disagree.

## Context

Recorded at phase close from evidence-bound knowledge writeback.

**Cited evidence:**

- .writ/specs/2026-10-25-review-route-rigor/drift-log.md
- .writ/specs/2026-10-25-repro-first-bug-fixing/drift-log.md
- .writ/specs/2026-10-25-retro-fix-ladder/drift-log.md
- .writ/specs/2026-10-25-gate-upgrade-removal-measurement/drift-log.md
- skills/drift-triage/SKILL.md
- commands/implement-story.md
- repeated drift: 65 Auto-amended entries, 1 spec-lite.md edit after 1fe981b (git log per spec)

## Related

- `.writ/specs/2026-10-25-repro-first-bug-fixing/drift-log.md`
- `.writ/specs/2026-10-25-retro-fix-ladder/drift-log.md`
- `skills/drift-triage/SKILL.md`
