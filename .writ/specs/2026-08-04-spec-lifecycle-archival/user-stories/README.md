# User Stories: Spec Lifecycle & Archival

> **Status:** Completed ✅ — amended 2026-08-04 (Business Rule 1's knowledge-evidence gate removed; see `spec.md` → Technical Concerns → Amendment). 6/6 stories complete, 44/44 tasks.

| Story | Title | Status | Tasks | Progress | Dependencies |
|---|---|---|---|---|---|
| 1 | [Status Detection Fix](./story-1-status-detection-fix.md) | Completed ✅ | 7 | 7/7 | None |
| 2 | [Archive Sweep Mechanism](./story-2-archive-sweep-mechanism.md) | Completed ✅ | 8 | 8/8 | Story 1 |
| 3 | [Lifecycle Documentation](./story-3-lifecycle-documentation.md) | Completed ✅ | 7 | 7/7 | None |
| 4 | [.cursorindexingignore Scaffolding](./story-4-cursorindexingignore-scaffolding.md) | Completed ✅ | 7 | 7/7 | None |
| 5 | [Supersession Banner Convention](./story-5-supersession-banner-convention.md) | Completed ✅ | 7 | 7/7 | None |
| 6 | [Dogfood the Sweep Against This Repo](./story-6-dogfood-sweep.md) | Completed ✅ | 8 | 8/8 | Story 2 |

## Dependency Graph

```
Story 1 (Status Detection Fix)
  └── Story 2 (Archive Sweep Mechanism)
        └── Story 6 (Dogfood the Sweep Against This Repo)

Story 3 (Lifecycle Documentation)       — independent, parallelizable
Story 4 (.cursorindexingignore)         — independent, parallelizable
Story 5 (Supersession Banner Convention) — independent, parallelizable
```

**Story 1 is the critical-path prerequisite.** Every downstream story either depends on it directly (Story 2 → Story 6) or must describe the *fixed* target state rather than today's broken detection (Story 3). Stories 3, 4, and 5 have no functional dependency on Story 1's code landing first — they touch documentation, `install.sh`, and header-convention prose respectively — but Story 3 in particular should be sequenced after Story 1 is at least drafted so its documented vocabulary matches what actually ships.

**Suggested execution order:** Story 1 first (blocking). Then Stories 2, 3, 4, 5 in parallel (up to 4 concurrent). Story 6 last, once Story 2 is merged and functional — it validates the whole spec against this repo's real 39 specs and 12 knowledge entries, not fixtures.

## Quick Links

- [spec.md](../spec.md) — full contract, business rules, experience design
- [spec-lite.md](../spec-lite.md) — condensed agent-context version
- [sub-specs/technical-spec.md](../sub-specs/technical-spec.md) — detection logic, eligibility check, ledger format, install.sh scaffolding, supersession write-back format

## Known Real-World Validation Candidates (for Story 6)

Confirmed during spec authoring — not a guarantee, but strong evidence the dogfood run will find at least one real match:

- **`2026-04-24-phase4-production-grade-substrate`** — status resolves to `Completed ✅`; referenced in `related_artifacts` by at least 6 separate `.writ/knowledge/` entries (`2026-04-24-date-prefixed-slugs.md`, `2026-04-24-self-dogfooding-symlinks.md`, `2026-04-24-adapter-neutrality.md`, `2026-04-24-markdown-as-instructions.md`, `dual-use-test.md`, `2026-04-24-story-overlap-needs-boundaries.md`).
- **`2026-07-18-artifact-integrity-handshake`** — status resolves to `Complete`; referenced by `.writ/knowledge/lessons/2026-07-19-artifact-map-belongs-in-context-md-not-index-md.md`.
