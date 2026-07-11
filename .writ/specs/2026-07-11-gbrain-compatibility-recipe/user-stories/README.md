# Phase 8: GBrain Compatibility Recipe — User Stories

> **Spec:** [`../spec.md`](../spec.md)
> **Status:** Not Started
> **Progress:** 0/2 stories
> **Dependencies:** [] (independent; the sibling `native-memory-guidance` spec depends on this one)

## Story Summary

| # | Story | Priority | Dependencies | Status | Tasks |
|---|---|---|---|---|---:|
| 1 | [`gbrain-interop` skill + registration](story-1-gbrain-interop-skill.md) | High | None | Not Started | 0/5 |
| 2 | [`gbrain-recipe.md` user-facing recipe](story-2-recipe-doc.md) | High | Story 1 | Not Started | 0/4 |

## Dependency Plan

```text
Story 1  (skill: detect · route · cite · write markdown-first · degrade; manifest + catalog)
   │
Story 2  (recipe doc: install · sources add · sync · map · MCP · round-trip · remove)
```

### Sequencing Rationale

- **Story 1** creates the agent capability — the `gbrain-interop` skill — and registers it in the manifest and root catalog. It establishes the routing vocabulary (detect / brain-first / cite markdown / markdown-first writes / graceful degrade) the recipe doc then references.
- **Story 2** writes the human-facing recipe that operationalizes the skill: how to install GBrain, register `.writ/` as a source, map artifacts to pages, register MCP, and remove the index with zero canonical loss. It depends on Story 1 so the doc can point at a skill that already exists.

Execution is sequential.

## Progress Rules

- Update each story's status from `Not Started` → `In Progress` → `Completed ✅`.
- Count only top-level items under `## Implementation Tasks`.
- Every cited GBrain command must be verified against current GBrain/GStack docs before a story is marked complete — no fabricated flags (Prime Directive: match confidence to evidence).
- The round-trip guarantee is a blocking property: if canonical data could live only in the index, the spec is not done.
