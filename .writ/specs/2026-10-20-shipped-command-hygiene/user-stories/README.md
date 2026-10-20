# User Stories: Shipped Command Hygiene

> Spec: [`../spec.md`](../spec.md)

| # | Story | Status | Priority | Dependencies | Tasks | Progress |
|---|---|---|---|---|---|---|
| 1 | [Strip Internal References and Add `shipped-refs`](story-1-strip-internal-references.md) | Not Started | High | None | 7 | 0/7 |
| 2 | [Pin Map and Conversions](story-2-pin-map-and-conversions.md) | Not Started | High | Story 1 | 7 | 0/7 |
| 3 | [`create-spec.md` Reduction Pass](story-3-create-spec-reduction.md) | Not Started | Medium | Story 2 | 7 | 0/7 |

**Total:** 3 stories, 21 tasks, 15 acceptance criteria.

## Dependencies

- **Spec level:** `2026-10-20-harness-cuts` and `2026-10-20-platform-neutral-names` land first. Both change command text and eval pins, so every story re-inventories on the tree it starts from.
- **Story 1** has no story dependency. It adds `check_shipped_refs` to `scripts/eval.sh` and edits 12 command files.
- **Story 2** needs Story 1: both edit `scripts/eval.sh`, and the pins are classified against the text Story 1 leaves.
- **Story 3** needs Story 2: a cut may touch only text that no `keep` row or structural row requires, and Story 1 already edited `create-spec.md`.
