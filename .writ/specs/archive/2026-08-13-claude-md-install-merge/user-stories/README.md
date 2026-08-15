# User Stories: Marker-Based CLAUDE.md Merge

> Parent spec: `../spec.md`

## Progress

| Story | Status | Priority | Dependencies | AC | Tasks |
|---|---|---|---|---|---|
| [Story 1: install.sh — marker-based CLAUDE.md merge](story-1-install-merge.md) | Completed ✅ (2026-08-13) | High | None | 5 (AC-1.1–1.5) | 7 |
| [Story 2: update.sh — migrate CLAUDE.md to inner-block hash tracking](story-2-update-migration.md) | Completed ✅ (2026-08-13) | High | Story 1 | 5 (AC-2.1–2.5) | 7 |

**Total:** 2/2 stories complete, 10/10 acceptance criteria met, 14/14 tasks done.

## Dependency Notes

Story 2 consumes the `CLAUDE.md.writ-block` manifest key that Story 1's
`install.sh` changes introduce via `write_copy_manifest`. Story 2 makes no
changes to `install.sh`; if Story 1's manifest key name changes during
implementation, Story 2 must follow it. The two stories touch different files
(`install.sh` vs. `update.sh`) with no shared code paths beyond the key name
itself, so Story 2 could theoretically be implemented in parallel once the
key name is locked — but is sequenced after Story 1 to avoid the two
diverging on that name.

## Quick Links

- [Story 1: install.sh — marker-based CLAUDE.md merge on initial install](story-1-install-merge.md)
- [Story 2: update.sh — migrate CLAUDE.md to inner-block hash tracking](story-2-update-migration.md)
- [Technical spec](../sub-specs/technical-spec.md)
- [Full spec](../spec.md) · [Lite spec](../spec-lite.md)
