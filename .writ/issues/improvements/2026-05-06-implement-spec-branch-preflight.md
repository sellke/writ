# Implement Spec Branch Preflight

> **Type:** Improvement
> **Priority:** Normal
> **Effort:** Medium
> **Created:** 2026-05-06
> **Status:** Triaged 2026-07-18 — still valid and still open. `/implement-spec`'s standalone mode has no branch preflight (lane mode gets branch hygiene from `/implement-phase`, direct invocation does not). Kept in backlog; promote via `/create-spec --from-issue` when picked up.
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

Add a branch hygiene preflight to `/implement-spec` so spec execution starts from an intentional branch state.

## Current State

- `/implement-spec` discovers, plans, confirms, and executes stories without first checking the current Git branch state
- Running implementation directly on `main` is possible
- Dirty working trees can proceed into implementation without an explicit continuation or branch decision
- Existing clean feature branches are reused implicitly, even when the user may want a spec-specific branch

## Expected Outcome

- Before initiating implementation, `/implement-spec` checks the current branch and working tree cleanliness
- If currently on `main` with a clean working tree, it automatically creates a new branch referencing the selected specification
- If currently on a clean non-main branch, it asks whether to continue on that branch or create a new spec-referenced branch
- If currently on a dirty branch, it asks whether to continue with existing changes or create a new branch for the spec
- Branch names should be derived predictably from the specification identifier and remain human-readable

## Relevant Files

- `commands/implement-spec.md` - top-level orchestrator where the preflight should run before story execution begins

## Notes

This should happen after the target spec is known, so the generated branch can reference the specification, but before execution state is initialized or any `/implement-story` calls begin.
