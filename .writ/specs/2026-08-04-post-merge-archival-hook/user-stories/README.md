# User Stories: Post-Merge Archival Hook

> **Status:** Not Started — 0/4 stories complete, 0/28 tasks.

| Story | Title | Status | Tasks | Progress | Dependencies |
|---|---|---|---|---|---|
| 1 | [Shared Spec Reference Resolution](./story-1-shared-spec-reference-resolution.md) | Not Started | 7 | 0/7 | None |
| 2 | [Single-Spec Archive Entry Point](./story-2-single-spec-archive-entry-point.md) | Not Started | 7 | 0/7 | None |
| 3 | [Wire the Hook into /release Step 1.3c](./story-3-release-merged-pr-hook.md) | Not Started | 7 | 0/7 | Story 1, Story 2 |
| 4 | [Dogfood and Verify](./story-4-dogfood-and-verify.md) | Not Started | 7 | 0/7 | Story 3 |

## Dependency Graph

```
Story 1 (Shared Spec Reference Resolution)  ─┐
Story 2 (Single-Spec Archive Entry Point)   ─┤── independent, parallelizable
                                              └── Story 3 (Wire the Hook into /release Step 1.3c)
                                                     └── Story 4 (Dogfood and Verify)
```

**Stories 1 and 2 have no dependency on each other** — Story 1 touches `commands/ship.md` and a new resolver script; Story 2 touches only `scripts/archive-sweep.py` and its test suite. Both can proceed in parallel. **Story 3 is the integration point** and cannot start until both land, since it consumes Story 1's resolver contract and Story 2's archive entry point without reimplementing either. **Story 4 is the closing validation**, mirroring the parent spec's Story 6 — it depends entirely on Story 3's wiring being functional, and its final acceptance criterion (the two motivating specs actually archiving) may not resolve until this repo's next real merge-then-release cycle after each spec reaches `Complete`.

**Suggested execution order:** Stories 1 and 2 in parallel first. Story 3 once both land. Story 4 last — its fixture-based tasks (4.1–4.4) can close immediately after Story 3; its live-confirmation task (4.5) is a documented follow-up procedure that resolves once this spec and its parent each go through a real merge → release cycle.

## Quick Links

- [spec.md](../spec.md) — full contract, business rules, experience design
- [spec-lite.md](../spec-lite.md) — condensed agent-context version
- [sub-specs/technical-spec.md](../sub-specs/technical-spec.md) — resolver shape, single-spec entry point, ledger format extension, `/release` Step 1.3c wiring, error/shadow/edge-case tables

## Open Technical Decision (flagged in sub-specs/technical-spec.md) — Resolved

The Error & Rescue Map carried one deliberate `[UNPLANNED]`: what happens if `git mv` succeeds but the subsequent `LEDGER.md` append fails. **Resolved by Story 2** as option (b) — accepted rare-risk, surfaced as a distinct `archived_unlogged` status rather than rolled back or silently folded into `archived`/`git_mv_failed`. See `sub-specs/technical-spec.md` → Error & Rescue Map for the full rationale and `scripts/archive-sweep.py`'s module docstring for the code-level documentation.

## Motivating Gap (for Story 4)

The concrete, real-world test case this spec exists to fix: `2026-08-04-spec-lifecycle-archival` reached `Complete`, shipped via `/ship`, and released via `/release` — and remains unarchived through both because nothing besides a separately-remembered `/status --archive` invocation ever checks. This spec's own folder, `2026-08-04-post-merge-archival-hook`, will face the identical risk once it too reaches `Complete`. Story 4's live-confirmation task tracks both as the spec's own acceptance evidence.
