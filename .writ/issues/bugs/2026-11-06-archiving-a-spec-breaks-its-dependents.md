# Archiving a Spec Breaks the Dependency Graph of Specs That Depend on It

> **Type:** Bug
> **Priority:** Medium
> **Effort:** Small
> **Created:** 2026-11-06
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

`archive-sweep.py archive-one` moved `2026-10-25-design-divergence` to `.writ/specs/archive/` on 2026-11-04. `2026-10-25-gate-upgrade-removal-measurement` still listed it under `Dependencies:`. `spec-deps.py validate` reads only `.writ/specs/*/spec.md`, so it then failed with `missing_reference`. That error blocks `/implement-phase` Step 2.1 for every phase, not only the dependent spec's.

## Current State

- `scripts/spec-deps.py` has no notion of `archive/`. An archived, complete dependency reads as an unknown spec.
- `scripts/archive-sweep.py` archives a spec without checking whether an active spec depends on it.
- Workaround applied on 2026-11-06: the archived id was removed from the removal-measurement spec's `Dependencies:` header. An archived spec is complete-family, so the dependency was already satisfied.

## Expected Outcome

One of:

- `spec-deps.py` resolves an id found under `.writ/specs/archive/` as a satisfied dependency, or
- `archive-one` and `sweep` refuse, or rewrite the dependent's header, when an active spec depends on the spec being archived.

A test covers it: an active spec depending on an archived one validates `ok`, or archiving is refused.

## Relevant Files

- `scripts/spec-deps.py`: `validate`
- `scripts/archive-sweep.py`: `archive_one()`
- `.writ/docs/spec-lifecycle.md`
