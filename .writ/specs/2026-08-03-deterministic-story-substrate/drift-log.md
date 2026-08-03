# Drift Log

> Spec: .writ/specs/2026-08-03-deterministic-story-substrate/
> Created: 2026-08-03
> ⚠️ Append-only — do not modify existing entries.

---

## Story 2: Deterministic Context Assembler — Drift Report

> Run: 2026-08-03
> Overall Drift: Small

### Deviations

#### [DEV-001] Extended-reference backtick style diverges from `context-hint-format.md`'s illustrative example
- **Severity:** Small
- **Spec said:** Story 2's Notes and AC1 both specify the extended-reference example as one backtick span (`` `file.md → ## Section → ### Subsection` ``). `.writ/docs/context-hint-format.md`'s prescriptive "Format Structure" sections are consistent with this; only that same doc's illustrative "Example with Spec Content References" (lines ~244–257) breaks pattern, backticking each segment separately with the arrow outside the backticks.
- **Implementation did:** `scripts/story-context.py` implements the canonical single-backtick-span form only, per AC1 and the story's Notes, not the doc's stray illustrative example (which fails to parse against the implemented grammar).
- **Reason:** Two independent authoritative sources (AC1, the doc's own prescriptive Format Structure sections) agree with the implementation; only one illustrative example elsewhere in the same doc is internally inconsistent with its own rules.
- **Resolution:** Auto-amended
- **Spec amendment:** No change to `spec.md`/`spec-lite.md` — the canonical single-span form is already correctly specified there. `context-hint-format.md`'s stale illustrative example is out-of-scope for this story; Story 4 corrects it to the single-span form when it rewrites the contract to point at `scripts/story-context.py`.

#### [DEV-002] Story 2 Notes claimed `>>` arrow support that was never authoritative
- **Severity:** Small
- **Spec said:** Story 2's "Parser details worth encoding in tests" note stated extended references use `→` or `>>` arrows. AC1, `sub-specs/technical-spec.md`, and `.writ/docs/context-hint-format.md` all show `→` only.
- **Implementation did:** `ARROW = "→"` only; `>>` is explicitly rejected, documented in-code as an artifact inherited from the pre-existing `eval-leanness.py` regex (`r"[→>]{1,2}"`) rather than a documented contract requirement.
- **Reason:** Majority/authoritative reading — 2 canonical documents plus AC1 vs. one inconsistent phrase in the story's own Notes section.
- **Resolution:** Auto-amended
- **Spec amendment:** Updated `user-stories/story-2-context-assembler.md`'s "Parser details worth encoding in tests" line to read "the `→` arrow only (`>>` is not a supported arrow form — see drift-log.md DEV-002)", removing the inaccurate `>>` claim. No change to `spec.md`/`spec-lite.md` (neither ever mentioned `>>`).
