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

---

## Story 3: Empirically Derived Context Budget and Real Measurement — Drift Report

> Run: 2026-08-03
> Overall Drift: Small

### Deviations

#### [DEV-003] Budget constant uses a 2× margin, not a bare round-up, over the observed maximum
- **Severity:** Small
- **Spec said:** Task 3.3 — "choose `FETCHED_CONTEXT_BUDGET_BYTES` above the observed high end (catches pathology, not normal work)." No specific multiplier or rounding rule is specified.
- **Implementation did:** `scripts/story-context.py` sets `FETCHED_CONTEXT_BUDGET_BYTES = 21000`, derived as 2× the measured max (10,251 bytes across 170 real `story-*.md` files → 20,502) rounded up to the nearest 1,000. A bare 1× round-up (→ 11,000) would sit directly on top of the single real outlier.
- **Reason:** The measurement sweep (`scripts/sweep-story-context-bytes.py`) discovered that 9 of the 170 swept stories have a `spec.md` heading (`## 🎯 Experience Design (...)`) that fails `extract_markdown_section()`'s exact-match requirement, silently zeroing affected categories and undercounting the true corpus high end. The 2× margin is documented in code as explicit compensation for this pre-existing, out-of-scope bug rather than an arbitrary safety factor — a bare round-up would risk the budget firing on ordinary future growth once the undercount bug is eventually fixed elsewhere.
- **Resolution:** Auto-amended (logged for traceability only — the choice satisfies spec intent, not violates it)
- **Spec amendment:** No change to `spec.md`/`spec-lite.md`/the story file — "above the observed high end" already permits this reading. The heuristic and its rationale are documented in `scripts/story-context.py`'s module comments and `scripts/sweep-story-context-bytes.py`'s docstring, and now here for durable cross-story visibility.

#### [DEV-004] Truncation relevance order reuses `CATEGORY_ORDER` rather than a purpose-built ranking
- **Severity:** Small
- **Spec said:** AC2 — over-budget truncation "retains higher-relevance content first," without specifying the exact category order.
- **Implementation did:** `enforce_budget()` walks the existing `CATEGORY_ORDER` constant (`error_map_rows` → `shadow_paths` → `business_rules` → `experience`) as truncation priority, documented in-code as "a deliberate implementation choice... not something the spec mandates."
- **Reason:** No relevance ranking is defined elsewhere in the spec. Reusing the assembler's existing deterministic output order is the simplest, most conservative choice available — it avoids inventing a second, independent ordering concept for the same four categories.
- **Resolution:** Auto-amended (logged for traceability only)
- **Spec amendment:** No change to `spec.md`/`spec-lite.md`/the story file — AC2 leaves the exact order unspecified and the choice preserves intent.

---

## Story 4: Consolidate the Orchestrator Prose onto the Assembler — Drift Report

> Run: 2026-08-03
> Overall Drift: Small

### Deviations

#### [DEV-005] Fixed stale output-variable names in `context-hint-format.md` beyond Task 4.4's literal scope
- **Severity:** Minor
- **Spec said:** Task 4.4 scoped the doc rewrite to retiring "Parsing Guide (for Orchestrators)" and the "Parsing Validation (Task 1.5)" subsection, and removing the stale line-340 "no automated test suite" premise. It did not explicitly cite fixing `context_hints_parsed`/`context_content_fetched`.
- **Implementation did:** `context-hint-format.md`'s "Integration with Pipeline" section named orchestrator outputs `context_hints_parsed`/`context_content_fetched`, which never matched `commands/implement-story.md`'s actual variables (`fetched_context`, `context_warnings`) even before this story. Fixed opportunistically during the rewrite, with an inline callout and a Version History 2.0 entry documenting the change.
- **Reason:** Pre-authorized in the coding brief as a legitimate fix-while-touching, not scope creep — strictly corrective, transparently disclosed, no unrelated content changed.
- **Resolution:** Auto-amended (logged for traceability only)
- **Spec amendment:** No change to `spec.md`/`spec-lite.md` — this is a documentation-internal consistency fix, not a contract change.

#### [DEV-006] Legacy per-segment-backtick extended-reference dialect discovered, not migrated
- **Severity:** Minor
- **Spec said:** Business Rule "Legacy stories never break" and the edge-case table's "malformed category → skip + warn" row require graceful degradation for hint content the assembler can't resolve.
- **Implementation did:** Task 4.1's dogfooding sweep found 2 pre-2026-08-03 specs (`2026-03-27-context-engine` story-1, `2026-04-24-phase4-production-grade-substrate` story-1) using an older per-segment-backtick extended-reference dialect that `story-context.py`'s current regex doesn't resolve. Independently reproduced: the assembler exits 0 against `context-engine`'s story-1 with `fetched_context: {}` and 6 "Malformed context hint category"/"Unrecognized context hint category" warnings — exactly the contract's designed degradation, never a crash.
- **Reason:** Correctly out of Story 4's scope (no task authorizes migrating legacy specs to the current dialect); the graceful degradation is the contract working as designed, not a regression this story introduced.
- **Resolution:** Accepted as non-blocking. Filed as `.writ/issues/improvements/2026-08-03-legacy-context-hint-dialect-gap.md` for future consideration — these 2 specs currently get zero hint value silently, which is safe but not ideal.
- **Spec amendment:** None needed.
