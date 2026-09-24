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

---

## Story 2: Lean preamble — Drift Report

> Run: 2026-09-25
> Overall Drift: Small

### Deviations

#### [DEV-003] One dropped rule is a product rule, not a restatement
- **Severity:** Small
- **Spec said:** The lean preamble drops sentences that restate `system-instructions.md` on Plan Mode / `--recommend`.
- **Implementation did:** Dropped the whole section, including "validates its invocation matrix before mutation", which `system-instructions.md` does not carry and `implement-phase.md` does not state.
- **Reason:** Not a protected class (exit criteria, gates, production boundary, User Challenge, stakes triage). Routed to Story 4: `implement-phase.lean.md` states the rule.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite Implementation Approach names where the generalized rules live under the flag.

#### [DEV-004] "Never offer to code" relies on per-command Terminal constraints
- **Severity:** Small
- **Spec said:** Drop only restatements of `system-instructions.md`.
- **Implementation did:** The sentence is not in `system-instructions.md`; every planning command's Terminal constraint says it.
- **Reason:** Covered while lean command bodies keep their Terminal constraint lines (Story 4 asserts it).
- **Resolution:** Auto-amended
- **Spec amendment:** Same spec-lite line as DEV-003.

Prior spec-lite SHA-256: `a52cc84aad807358699f81b5492e697a88a66435547d9d0ae1280bb1ef78a80e`
