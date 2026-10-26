# Drift Log

> Spec: .writ/specs/2026-10-25-design-divergence/
> Created: 2026-10-26
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: Extract the design-divergence Skill and Register It — Drift Report

> Run: 2026-10-26
> Overall Drift: Small

### Deviations

#### [DEV-001] One axis-catalog table per medium, not one shared table
- **Severity:** Small
- **Spec said:** AC-1.2: "one axis-catalog table covers UI, API shape, and data model." technical-spec.md → Skill: "Axis catalog, one table per medium (two or three rows each)." Story 1 Notes: "Three axis tables only."
- **Implementation did:** `### Axis catalog` under `## How to Apply` holds three `####` subsections (UI, API shape, Data model), each with one three-row table.
- **Reason:** The AC wording disagrees with the technical spec, the story notes, and Must Include 1 ("each with an axis catalog"). The implementation follows the higher-ranked sources; the wiring test pins the per-medium shape.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** None needed in spec-lite.md; it does not quote the table count.
