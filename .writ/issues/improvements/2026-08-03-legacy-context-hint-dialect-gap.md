# Legacy per-segment-backtick extended-reference dialect not resolved by `story-context.py`

> Filed: 2026-08-03
> Source: Story 4 ([DEV-006](../../specs/2026-08-03-deterministic-story-substrate/drift-log.md)) of `2026-08-03-deterministic-story-substrate`
> Priority: Low
> Status: Open

## Summary

`scripts/story-context.py` (Story 2/3/4 of the Deterministic Story Substrate spec) resolves extended references in the canonical single-backtick-span form (`` `file.md → ## Section → ### Subsection` ``). Two pre-2026-08-03 specs use an older per-segment-backtick dialect (each path segment individually backticked, arrow outside the backticks) that the current regex does not recognize.

## Affected Specs

- `.writ/specs/2026-03-27-context-engine/user-stories/story-1-*.md`
- `.writ/specs/2026-04-24-phase4-production-grade-substrate/user-stories/story-1-*.md`

## Reproduction

```bash
python3 scripts/story-context.py assemble --story .writ/specs/2026-03-27-context-engine/user-stories/story-1-*.md --budget-bytes 21000
```

Returns `fetched_context: {}` with 6 "Malformed context hint category" / "Unrecognized context hint category" warnings, exit 0. This is the contract's designed degradation (never a crash, never a block) — the gap is that these 2 stories currently receive **zero** hint value from the assembler, silently.

## Why This Wasn't Fixed in Story 4

Story 4's scope was retiring the prose parser and wiring the assembler into `/implement-story` — not auditing or migrating legacy content written before the assembler existed. Migrating 2 old stories to the current dialect (or widening the regex to accept both forms) is separable, low-risk work with no dependency on anything else in this spec.

## Suggested Resolution (not yet decided)

Either:
1. Widen `story-context.py`'s extended-reference regex to accept both the canonical single-span form and the older per-segment-backtick form, or
2. Manually migrate the 2 affected story files' `## Context for Agents` sections to the canonical form.

(1) fixes it for any other undiscovered legacy specs; (2) is more surgical but doesn't generalize. No urgency — both affected stories are historical/completed specs, not active work.
