# Drift Log

> Spec: .writ/specs/2026-10-25-why-command/
> Created: 2026-10-26
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: The `/why` Command File — Drift Report

> Run: 2026-10-26
> Overall Drift: Small

### Deviations

#### [DEV-001] Answer template's ADR placeholder reads `adr-<NNN>-<slug>.md`
- **Severity:** Small
- **Spec said:** technical-spec.md → Output Templates shows the evidence example `` `.writ/decision-records/adr-NNN-<slug>.md` § Decision ``.
- **Implementation did:** `commands/why.md` Step 5 template writes `adr-<NNN>-<slug>.md`.
- **Reason:** `check_referenced_paths` resolves backticked `*.md` tokens unless they carry a `<...>` placeholder. The bracketed form passes the check; the meaning is unchanged.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** None needed in spec-lite.md; the template is not quoted there.

#### [DEV-002] `/why` points to `/research` when the subject is outside the project
- **Severity:** Small
- **Spec said:** technical-spec.md → Step contents, Step 1: not found → what was searched for and one natural-language question, then stop. The Integration table says `/why` points to `/research` when the subject is not in the project.
- **Implementation did:** Step 1's not-found branch adds one sentence pointing to `/research` for a subject outside the project, so the Integration row has a step that carries it. Gate 3 evaluator finding.
- **Reason:** The Integration row named a behavior no step performed.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** None needed in spec-lite.md.
