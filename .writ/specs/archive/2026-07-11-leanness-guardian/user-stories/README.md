# User Stories: Leanness Guardian

> **Spec:** 2026-07-11-leanness-guardian
> **Status:** Complete

## Progress

| # | Story | Status | Tasks | Dependencies |
|---|-------|--------|-------|--------------|
| 1 | [Leanness Tripwire (Tier A eval check)](story-1-leanness-tripwire.md) | Complete | 6/6 | None |
| 2 | [Leanness Audit Ritual (Tier B cadence)](story-2-audit-ritual.md) | Complete | 4/4 | Story 1 |

**Total:** 10/10 tasks (100%)

## Dependencies

- **Story 1 → Story 2:** the Tier B ritual template consumes the Tier A metrics
  output, so the tripwire's metric shape must exist first.

## Quick Links

- [spec.md](../spec.md) — full contract and non-duplication mandate
- [spec-lite.md](../spec-lite.md) — condensed agent context
- [sub-specs/technical-spec.md](../sub-specs/technical-spec.md) — eval wiring, helper contract, fixtures
