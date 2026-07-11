# Skill Extraction from High-Traffic Commands — User Stories

> **Spec:** [`../spec.md`](../spec.md)
> **Status:** Completed ✅
> **Progress:** 27/27 implementation tasks (100%)
> **Cross-Spec Prerequisite:** `2026-07-10-skill-lifecycle`

## Story Summary

| # | Story | Priority | Dependencies | Status | Tasks |
|---|---|---|---|---|---:|
| 1 | [Retire `/explain-code` into a Skill](story-1-retire-explain-code-into-a-skill.md) | High | None | Completed ✅ | 7/7 |
| 2 | [Extract `tdd-cycle` from `/implement-story`](story-2-extract-tdd-cycle.md) | High | None | Completed ✅ | 7/7 |
| 3 | [Extract `error-rescue-mapping` from `/create-spec`](story-3-extract-error-rescue-mapping.md) | Medium | None | Completed ✅ | 6/6 |
| 4 | [Extract `safe-refactor-loop` and Finalize](story-4-extract-safe-refactor-loop-and-finalize.md) | High | Stories 1–3 | Completed ✅ | 7/7 |

## Dependency Plan

```text
2026-07-10-skill-lifecycle   (binding cross-spec prerequisite)
            │
   ┌────────┼────────┐
Story 1  Story 2  Story 3      (independent extractions — parallelizable)
   └────────┼────────┘
         Story 4               (fourth skill + catalog/docs/dry-run finalization)
```

### Sequencing Rationale

- **Cross-spec prerequisite** — `2026-07-10-skill-lifecycle` must land the `status:` frontmatter field first; every extracted skill is born `status: candidate` under that schema. This spec never defines the schema.
- **Stories 1–3 are independent.** Each extracts one skill from a distinct source (retired `/explain-code`, `/implement-story`, `/create-spec`) touching disjoint command files. They may run in any order or in parallel.
- **Story 4 depends on 1–3** because it lands the fourth skill *and* performs one authoritative finalization pass: regenerate the catalog after all four skills are registered, run `gen-skill.sh --check`, lint every skill, run the install/update dry-runs, add the `skills.md` extraction section, and correct the stale line. Running finalization once — after every manifest edit is in — avoids catalog churn.
- **Shared registry note.** All four stories append to `.writ/manifest.yaml` `skills:` (additive, alphabetical). Each story regenerates the catalog after its edit; Story 4 proves final sync with `--check`.

Stories 1–3 can be parallelized safely; Story 4 must run last.

## Progress Rules

- Update each story's status from `Not Started` → `In Progress` → `Completed ✅`.
- Count only top-level items under `## Implementation Tasks`.
- A story is not complete until its new skill passes `bash scripts/lint-skill.sh` and its wired consumer references the skill by path.
- Do not mark Story 1 complete while any active surface still names `/explain-code` (allowlisted history excepted).
- Do not mark Story 4 or the parent spec complete until `gen-skill.sh --check` passes, all four skills lint clean, and the install/update dry-runs are clean.
- "In real use" is satisfied by wiring live consumers. `candidate → proven` promotion is out of scope and owned by `2026-07-10-skill-lifecycle`; do not claim promotion here.
