# User Stories — Per-Criterion Traceability IDs

> Spec: [../spec.md](../spec.md)
> Condensed context: [../spec-lite.md](../spec-lite.md)

## Stories

| # | Story | Status | Criteria | Tasks | Progress |
|---|---|---|---|---|---|
| 1 | [ID Grammar and Emitter](story-1-id-grammar-and-emitter.md) | Completed ✅ | 4 | 7/7 | 100% |
| 2 | [The Checker](story-2-the-checker.md) | Not Started | 5 | 0/7 | 0% |
| 3 | [Verify-Spec Wiring](story-3-verify-spec-wiring.md) | Not Started | 4 | 0/7 | 0% |
| 4 | [Edit-Spec Stability Guard](story-4-edit-spec-stability-guard.md) | Not Started | 4 | 0/7 | 0% |

**Total: 7/28 tasks (25%)** · 17 acceptance criteria across 4 stories

## Dependencies

```
Story 1 (grammar + emitter)
   ├── Story 2 (the checker) ── Story 3 (verify-spec wiring)
   └── Story 4 (edit-spec stability guard)
```

- **Story 1 — None.** Produces the grammar doc that both downstream branches implement against.
- **Story 2 — Story 1.** The checker implements the recorded grammar; building it first would
  mean inventing the contract in code.
- **Story 3 — Story 2.** The command file names the script as its executable reference, so the
  script must exist and be trustworthy first.
- **Story 4 — Story 1.** Needs the marker rule, not the checker. Deliberately off Story 2's
  critical path, so it can land in parallel with 2 and 3.

Stories 2 and 4 are independently startable once Story 1 lands.

## Ordering Note

Story 1's task 1.1 is a stop condition for the whole spec, not just its own story. It verifies
that a trailing ID tag still matches both anchored regexes in `scripts/recommend-state.py`
(lines 378 and 2981). Suffix placement is what keeps that 191 KB contract script and its two
eval fixture sets out of scope. If 1.1 fails, stop and re-contract rather than moving the tag
to a prefix and absorbing three additional files.

## Quick Links

- [Story 1 — ID Grammar and Emitter](story-1-id-grammar-and-emitter.md)
- [Story 2 — The Checker](story-2-the-checker.md)
- [Story 3 — Verify-Spec Wiring](story-3-verify-spec-wiring.md)
- [Story 4 — Edit-Spec Stability Guard](story-4-edit-spec-stability-guard.md)
- [Technical Spec](../sub-specs/technical-spec.md)
