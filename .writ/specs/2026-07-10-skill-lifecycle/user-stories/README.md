# Skill Lifecycle — User Stories

> **Spec:** [`../spec.md`](../spec.md)
> **Status:** Not Started
> **Progress:** 6/20 implementation tasks (30%)
> **Cross-Spec Dependencies:** None (this spec is the foundation for `2026-07-10-skill-extraction`)

## Story Summary

| # | Story | Priority | Dependencies | Status | Tasks |
|---|---|---|---|---|---:|
| 1 | [Skill Lifecycle Schema + ADR](story-1-skill-lifecycle-schema-and-adr.md) | High | None | Completed ✅ | 6/6 |
| 2 | [Lifecycle Hygiene Lint](story-2-lifecycle-hygiene-lint.md) | High | Story 1 | Not Started | 0/7 |
| 3 | [Authoring + Catalog Wiring](story-3-authoring-and-catalog-wiring.md) | Medium | Stories 1, 2 | Not Started | 0/7 |

## Dependency Plan

```text
Story 1  (schema + ADR + conventional-commits status)
   │
Story 2  (lint rules + eval fixtures)
   │
Story 3  (new-skill scaffold + catalog column + docs)
```

### Sequencing Rationale

- **Story 1** defines the `status:` field, the evidence schema, and the earned-state thresholds, and records ADR-014. Nothing can be validated or scaffolded before the schema exists, so it leads. It also sets `conventional-commits` to `proven` — the first real datum the lint (Story 2) will validate against.
- **Story 2** turns the Story 1 schema into an enforced contract: lifecycle rules in `scripts/lint-skill.sh` and a `skill-lifecycle` eval check with failing-first fixtures. It depends on the schema being final.
- **Story 3** wires the human-facing surfaces — `/new-skill` scaffolds `candidate`, `gen-skill.sh` renders the `Status` column, and `.writ/docs/skills.md` documents the lifecycle. It depends on both the schema (Story 1) and the lint (Story 2), since the scaffold must pass the lint the moment it is written.

Execution is sequential. The stories share `.writ/manifest.yaml` and layer on one another's contracts; later stories intentionally consume the artifacts established earlier.

## Progress Rules

- Update each story's status from `Not Started` → `In Progress` → `Completed ✅`.
- Count only top-level items under `## Implementation Tasks`.
- Do not mark a story complete while any acceptance criterion or Definition of Done item is unmet.
- The schema and lint contract (Stories 1–2) must be stable before `2026-07-10-skill-extraction` begins — do not weaken either after downstream extraction starts.
