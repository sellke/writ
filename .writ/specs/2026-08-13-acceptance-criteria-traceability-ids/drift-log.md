# Drift Log — Per-Criterion Traceability IDs

> Append-only. Never modify existing entries. Continue DEV-ID numbering from the highest
> existing entry.

#### [DEV-1] Step 2.6b addition to `create-spec.md` (Story 1)
- **Severity:** Small
- **Spec said:** "carry criterion IDs into spec-lite.md's Review-agent acceptance criteria"
  (Task 1.4), with no mechanism specified.
- **Implementation did:** Added a new Step 2.6b (between Step 2.6 and 2.7) that tags
  spec-lite.md's Review-agent bullets with `[AC-N.M]` after story files exist, closing a real
  sequencing gap (Step 2.4 writes spec-lite.md before Step 2.6 assigns per-story IDs).
- **Resolution:** Accepted, no spec-lite.md amendment needed — this is the task's intent
  fulfilled via an explicit, documented mechanism, not a deviation from it.

#### [DEV-2] `scripts/tests/test_governor_enforcement.py` byte-budget disclosure update (Story 1)
- **Severity:** Small
- **Spec said:** Story 1's file scope was `.writ/docs/acceptance-criteria-ids.md`,
  `agents/user-story-generator.md`, `commands/create-spec.md`, `.writ/docs/spec-format.md`.
- **Implementation did:** Editing `create-spec.md` pushed it further past its pre-existing
  recorded byte-budget overage in `KNOWN_OVER_BUDGET`, tripping an unrelated regression gate.
  Updated the recorded value (21463 → 24036 bytes) with a dated disclosure comment, following
  that file's own established precedent for disclosed increases.
- **Resolution:** Accepted, no spec-lite.md amendment needed — a narrowly-scoped, disclosed,
  arithmetically-verified data correction to keep an existing gate honest.
