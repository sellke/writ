# Story 1 — Knowledge Loading Organic Validation

> **Type:** Improvement
> **Priority:** Low
> **Effort:** Small
> **Created:** 2026-04-26
> **spec_ref:** .writ/specs/2026-04-24-phase4-production-grade-substrate/spec.md

## TL;DR

Confirm — organically, not via a contrived test — that an agent on a future feature loads a backfilled `.writ/knowledge/` entry without the maintainer mentioning the directory in the prompt. This is the ADR-005 success criterion that Story 1's AC3 hooks into.

## Current State

- Story 1 implementation is complete: knowledge-loading hook in `commands/implement-story.md` Step 2; keyword extraction, grep selection, ≤2KB cap, and `knowledge_context` parameter routing through architecture-check, coding, and review agents.
- 7 backfilled entries exist across `decisions/`, `conventions/`, `glossary/`, and `lessons/`.
- The mechanism has been reviewed and confirmed wired; what remains is observed evidence that it fires in real downstream work without being prompted.

## Expected Outcome

- On the next Phase 5 feature run through `/implement-story` (e.g., `/audit`, `/lessons`, dependency block, or status board), an agent loads at least one backfilled `.writ/knowledge/` entry as context without any prompt-side mention of `.writ/knowledge/`.
- Outcome captured in that feature's "What Was Built" section: which entry was loaded, by which agent, on which task.
- This is the organic confirmation of Story 1's AC3 and a key ADR-005 success criterion.

## Relevant Files

- `.writ/decision-records/adr-005-knowledge-substrate-markdown-over-database.md`
- `.writ/specs/2026-04-24-phase4-production-grade-substrate/user-stories/story-1-knowledge-ledger.md`
- `commands/implement-story.md`

## Notes

- The 90-day ADR-005 review (≈2026-07-24) is the formal recheck point. If no organic confirmation has surfaced by then, escalate: the entries may exist but never be reached, which is the named risk ADR-005 specifically warned about.
- This issue is tracked rather than gated, per the 2026-04-26 contract update on the Phase 4 spec — see that spec's `CHANGELOG.md`.
- Do not contrive a synthetic test to close this issue. Either organic confirmation arrives or the 90-day review uncovers a real problem worth fixing.
