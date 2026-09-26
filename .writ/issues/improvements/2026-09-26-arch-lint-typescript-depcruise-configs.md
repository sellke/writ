# arch-lint.py misses TypeScript dependency-cruiser configs

> **Type:** Improvement
> **Priority:** Low
> **Effort:** Small
> **Created:** 2026-09-26
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

dependency-cruiser also reads `.dependency-cruiser.ts`, `.cts` and `.mts`, but `scripts/arch-lint.py` detects only `.js`, `.cjs`, `.mjs` and `.json`, so a TypeScript-configured project gets `arch-lint: none`.

## Current State

- `DEPCRUISE_CONFIGS` in `scripts/arch-lint.py` follows the locked technical-spec §3 table of `2026-09-26-arch-lint-and-follow-ups`.
- dependency-cruiser's own search list (`src/cli/defaults.mjs`) includes the three TypeScript names (confirmed during that spec's Story 4 review).
- `.writ/docs/architecture-lint.md` says Gate 2 does not detect them (DEV-010).

## Expected Outcome

Add the three names to `DEPCRUISE_CONFIGS` in dependency-cruiser's search order, with detection tests, and drop the caveat from the guide. `test_architecture_lint_doc.py` reads the names from the helper, so it fails until the guide lists them.

## Relevant Files

- `scripts/arch-lint.py`, `scripts/tests/test_arch_lint.py`
- `.writ/docs/architecture-lint.md`
