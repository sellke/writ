# Drift Log

> Spec: .writ/specs/2026-11-06-lean-implement-phase/
> Created: 2026-11-07
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: UAT plans on request — Drift Report

> Run: 2026-11-07
> Overall Drift: Small

### Deviations

#### [DEV-001] c2 skips only on an explicit `false`, not on any falsy value
- **Severity:** Small
- **Spec said:** technical-spec.md § c2 predicate: `uat_requested = state.get("uatRequested", True); if not uat_requested: return met`.
- **Implementation did:** `if state.get("uatRequested", True) is False`; `null`, `0`, `""` or `"false"` check plans.
- **Reason:** The stricter direction: an odd value never turns a promised plan into `met`. `init` writes only a bool.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → For Coding Agents → Implementation Approach: c2 skips plan checks only on an explicit `false`.

#### [DEV-002] Handoff lines are printed per merged spec, not per spec that needs a person
- **Severity:** Small
- **Spec said:** Contract Experience Design, happy path: "one `/create-uat-plan {spec}` line for each spec that needs a person to validate it."
- **Implementation did:** The Invocation row, the Step 4.2 example and Completion item 2 print one line per merged spec.
- **Reason:** The orchestrator has no per-spec "needs a person" signal; a superset leaves no spec out.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → For Review Agents → Experience Design: one `/create-uat-plan {spec}` line per merged spec.

---
