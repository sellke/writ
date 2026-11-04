# Drift Log

> Spec: .writ/specs/2026-11-04-evidence-gated-review/
> Created: 2026-11-04
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: ADR-032 and the review-surface inventory — Drift Report

> Run: 2026-11-04
> Overall Drift: Large

### Deviations

#### [DEV-001] The reviewer filters stay; the spec no longer removes them
- **Severity:** Large
- **Spec said:** Contract Must Include 1 and 6, Success Criteria, and Scope Boundaries remove the reviewer filters: `skills/review-judgment-filters/`, the `reviewer-filters` switch, the `Reviewer Filters` config key, the agents' `reviewer_filters` input row and `Read` line, Gate 3's "Reviewer filters." paragraph, and `/review`'s Step 3 filters `Read` and switch line. The spec took over the removal trial's Reviewer Filters verdict.
- **Implementation did:** During `/implement-spec`, Story 1's inventory had to give the reviewer filters a verdict. The removal measurement (`.writ/specs/2026-10-25-gate-upgrade-removal-measurement/trial-report.md`, commit `ef0c418`) had recorded Reviewer Filters `keep`: 1 valid upgrade-only catch on 4 stories. The catch is F01, Critical, `ac:AC-4.3`, a stale doc claim. The user chose to keep the filters.
- **Reason:** The trial's verdict contradicts the contract's removal. Removing the filters would drop the only trial arm that raised F01. The trial also kept Safety Fact, which fits with raising its floor.
- **Resolution:** Pipeline paused — spec modified by user
- **Spec amendment:** `spec.md` gains `### Amendment (2026-11-04, during /implement-spec)` after the authoring corrections. It overrides the Deliverable's filter clause, Must Include 1, 6, and 8 (the roadmap filters criterion stays), the Success Criteria scan (panel names only), Scope Included, Recommendations story 5, and the Cross-Spec Overlap `/edit-spec` precondition (void). Story 6 becomes "Raise the Safety Fact floor to `tested`" (`story-6-raise-safety-fact-floor.md`). Story 7 writes the panel scan test and trims "panel reviewers" from Gate 3's filters paragraph. Story 5 puts the evidence header and `Read` beside the filters ones. `spec.md` no longer amends `2026-10-25-gate-upgrade-removal-measurement`, and that spec's Superseded-by line is removed. Evidence gating, the panel removal, and the `tested` floor are unchanged.

#### [DEV-002] ADR-032 Removals points to technical-spec.md for test files and generated trees
- **Severity:** Small
- **Spec said:** AC-1.4: the ADR-032 removal list names every file, section, and config key in technical-spec.md's Removals tables, which include `Tests` and `Generated trees` rows.
- **Implementation did:** ADR-032 § Removals names every product file, section, function, flag, and config key, and covers the test updates and regenerated trees with one pointer to technical-spec.md § Removals. The test skips those two rows (`NON_FILE_ROWS`).
- **Reason:** Stories 6 and 7 work from technical-spec.md, not from the ADR. Listing every test file in the ADR adds names that go stale.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** spec-lite.md, For Review Agents → Business Rules, gains: "ADR-032 § Removals names every product file, section, and config key, and points to technical-spec § Removals for test updates and regenerated trees (DEV-002)."
