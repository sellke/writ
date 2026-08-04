# Remaining Command Refinement — User Stories

> **Spec:** `.writ/specs/2026-03-18-remaining-command-refinement/spec.md`
> **Total Stories:** 5 (4 refinement + 1 validation)
> **Total Tasks:** 34

## Stories Overview

| # | Story | Status | Tasks | Priority | Dependencies |
|---|-------|--------|-------|----------|-------------|
| 1 | [new-command.md Refinement](story-1-new-command.md) | Not Started | 7 | High | None |
| 2 | [refactor.md Refinement](story-2-refactor.md) | Not Started | 7 | High | None |
| 3 | [review.md Refinement](story-3-review.md) | Not Started | 6 | High | None |
| 4 | [retro.md Refinement](story-4-retro.md) | Not Started | 7 | High | None |
| 5 | [Validation](story-5-validation.md) | Not Started | 6 | High | Stories 1–4 |

## Dependencies

Stories 1–4 are fully independent — each refines a separate command file with no cross-dependencies. They can be executed in any order or in parallel.

Story 5 (Validation) depends on all four refinement stories being complete. It performs cross-file litmus testing, cross-reference checking, capability comparison, and voice/density consistency validation.

## Target Line Counts

| File | Before | Target | Range (±10%) |
|------|--------|--------|-------------|
| new-command.md | 438 | ~200 | 180–220 |
| refactor.md | 416 | ~220 | 198–242 |
| review.md | 292 | ~200 | 180–220 |
| retro.md | 455 | ~220 | 198–242 |
| **Total** | **1,601** | **~840** | **756–924** |
