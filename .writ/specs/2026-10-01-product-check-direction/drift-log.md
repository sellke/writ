# Drift Log

> Spec: .writ/specs/2026-10-01-product-check-direction/
> Created: 2026-10-02
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: Reframe the Boundary — Drift Report

> Run: 2026-10-02
> Overall Drift: Medium

### Deviations

#### [DEV-001] verify-spec.md Integration row reworded
- **Severity:** Small
- **Spec said:** Story 1 edits `verify-spec.md`'s description, `--product` Modes row, callout, and Product Consistency Boundary paragraph.
- **Implementation did:** Also rewrote the Integration-with-Writ row for `/plan-product --reconcile`, which read "`--product` lints (before), `--reconcile` revises (after)".
- **Reason:** The contract's Success Criteria forbid any file in `commands/` from describing `--product` as running "before" a decision; the row was the last such sentence.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md "Files in Scope" names the Integration row.

#### [DEV-002] verify-spec.md ratchet entry re-pinned down, not left unchanged
- **Severity:** Medium
- **Spec said:** AC-1.5: tests pass "with the ratchet entry unchanged", `verify-spec.md` at or below its prior byte count.
- **Implementation did:** `verify-spec.md` shrank 80 bytes (35858 -> 35778) and its `KNOWN_OVER_BUDGET` entry moved 10898 -> 10818 with a dated comment.
- **Reason:** `test_the_byte_cap_is_the_half_that_does_not_comply_and_is_not_blocking` asserts `total_overage == sum(KNOWN_OVER_BUDGET.values())` exactly, so "unchanged" and "below" cannot both hold; the alternative was padding 80 bytes of prose back in. The downward pin tightens the one-way ratchet the Hardest Constraint protects. Reviewers split Small/Medium (one cross-family panelist failed AC-1.5 on it; tally advisory, no consensus); logged Medium per the ambiguity rule.
- **Resolution:** Flagged for review
- **Spec amendment:** spec-lite.md review criterion 5 reads "does not grow (re-pinned down if it shrinks)".

#### [DEV-003] verify-spec.md sha256 pin re-pinned
- **Severity:** Small
- **Spec said:** `test_lean_commands.py` heading parity stays green; the file's `DEFAULT_SHA256` pin is not mentioned.
- **Implementation did:** Re-pinned `DEFAULT_SHA256["verify-spec"]` with a dated comment in the file's convention.
- **Reason:** The pin hashes the whole default file, so any wording change trips it.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md "Files in Scope" names the sha256 pin.

#### [DEV-004] Eval check invoked by its dash-spelled name
- **Severity:** Small
- **Spec said:** Task 1.5 runs `bash scripts/eval.sh --check=product_check_direction`.
- **Implementation did:** Registered and ran it as `--check=product-check-direction`; the function is still `check_product_check_direction`.
- **Reason:** `eval.sh` validates `--check` against the dash-spelled `CHECKS` list; the underscore form exits 2 "Unknown check".
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md "Files in Scope" gives the dash-spelled name.

#### [DEV-005] Lean description mirrored; one extra forbid pin
- **Severity:** Small
- **Spec said:** Mirror `verify-spec.lean.md` lines 33–35 and 295; forbid "a lint you run before deciding anything" and "consistency lint (before)".
- **Implementation did:** Also mirrored the lean frontmatter `description:`, and added `forbid_literal 'lints (before'` on both verify-spec files.
- **Reason:** The lean twin's actual old wording was "`--product` lints (before a decision)", which neither specified pin could ever have caught (the review found the gap).
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md "Implementation Approach" lists the third forbid pin.

---

## Story 2: Suggest the Check Where Drift Appears — Drift Report

> Run: 2026-10-02
> Overall Drift: Medium

### Deviations

#### [DEV-006] Spec-attributed test module added
- **Severity:** Medium
- **Spec said:** Story 2's files are the eval pins, `implement-phase.md`, `release.md`, the governor re-pins, and the source issue; no new test module.
- **Implementation did:** Added `scripts/tests/test_product_check_direction.py` (10 tests naming this spec, AC-1.1–AC-2.5), including temp-tree runs of the eval check for every pin mutation.
- **Reason:** Once Story 1 read `Completed ✅`, `ac-trace` reported `untested_criterion` for AC-1.5 and the full eval failed; AC-1.1–1.4 were only matched by other specs' unattributed tokens. Scope expansion confined to this spec's own verification.
- **Resolution:** Flagged for review
- **Spec amendment:** spec-lite.md "Files in Scope" names the module.

#### [DEV-007] implement-phase.md sha256 pin re-pinned
- **Severity:** Small
- **Spec said:** Re-pin the `implement-phase.md` byte ratchet; the `DEFAULT_SHA256` pin is not mentioned.
- **Implementation did:** Re-pinned `DEFAULT_SHA256["implement-phase"]` with a dated comment; `implement-phase.lean.md` left unchanged.
- **Reason:** The pin hashes the whole default file. The spec names only the default file, and lean bodies are a measurement baseline.
- **Resolution:** Auto-amended
- **Spec amendment:** None (spec-lite already names the sha256 re-pin, DEV-003).

#### [DEV-008] Release summary line made conditional by a sentence after the template
- **Severity:** Small
- **Spec said:** AC-2.2 replaces the Roadmap pointer in place; Business Rule 4 says each new completion line appears only when `.writ/product/` exists.
- **Implementation did:** One sentence after the Phase 5 template omits the `Roadmap:` line without `.writ/product/`, matching the implement-phase pattern; `release.md` re-pinned 7576 -> 7655.
- **Reason:** Three of four Gate 3 reviewers found the pointer unconditional against Business Rule 4; the contract outranks the AC's silence. Without `.writ/product/` there is no roadmap for the line to report.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md "Error Handling" names both conditional lines.
