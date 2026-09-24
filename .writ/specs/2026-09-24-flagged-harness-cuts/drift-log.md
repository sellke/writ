# Drift Log

> Spec: .writ/specs/2026-09-24-flagged-harness-cuts/
> Created: 2026-09-25
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: Flag substrate — Drift Report

> Run: 2026-09-25
> Overall Drift: Small

### Deviations

#### [DEV-001] Existing loader warnings name the file actually loaded
- **Severity:** Small
- **Spec said:** Nothing about the hoisted, unresolved, and double-load warning text.
- **Implementation did:** Those warnings use the resolved path instead of a hard-coded `commands/<stem>.md`. Flag off, the text is identical (floor hash unchanged).
- **Reason:** Flag-on warnings should point at the lean file that was parsed.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite Implementation Approach says loader warnings name the file actually loaded.

#### [DEV-002] Missing-sibling warnings limited to the five in-scope siblings
- **Severity:** Small
- **Spec said:** AC-1.4 warns when a "required lean sibling" is missing.
- **Implementation did:** `LEAN_SIBLINGS` names `_preamble`, `create-spec`, `verify-spec`, `implement-phase`, `implement-story`. Other commands fall back to their default without a warning.
- **Reason:** Matches the spec's scope list. Adding a sibling later means updating the constant.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite Implementation Approach lists the five siblings that warn.

Prior spec-lite SHA-256: `3601348474ec4c70b22faebac2dc71c60cd47a55846a3c74570036b708bd8b87`
