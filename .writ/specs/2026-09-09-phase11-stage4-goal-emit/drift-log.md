# Drift Log

> Spec: .writ/specs/2026-09-09-phase11-stage4-goal-emit/
> Created: 2026-09-09
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: CLI + Schema — goal-emit.py Emit and Check — Drift Report

> Run: 2026-09-09
> Overall Drift: Small

### Deviations

#### [DEV-001] VERIFY.md names exit-criteria.py when spec_ref exists
- **Severity:** Small
- **Spec said:** VERIFY.md carries a “how to check DONE WHEN” paragraph (name `exit-criteria.py` when a promoted spec exists; otherwise “count DONE WHEN lines on the card”).
- **Implementation did:** Detects an existing `spec.md` from card `spec_ref` tokens under `--repo`; Story 1 fixtures omit `spec_ref` and lock the count sentence.
- **Reason:** Mechanical detection without walking the roadmap; matches the technical spec’s fallback rule.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite Implementation Approach now states the `spec_ref` → `exit-criteria.py` rule and the count-lines fallback.

#### [DEV-002] check maps missing emit files to missing_boundary
- **Severity:** Small
- **Spec said:** Written files that lack the ADR-013 sentence print `fail` `missing_boundary`.
- **Implementation did:** Absent `GOAL.md` / `VERIFY.md` on `check` of a valid `loop: yes` card also print `fail` `missing_boundary` and do not create `--out`.
- **Reason:** Closed fail for a valid card with no emit dir; avoids inventing a new reason code.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite Error Handling now lists missing written files on `check` as `fail` `missing_boundary`.

#### [DEV-003] Banned-token matcher uses word boundaries
- **Severity:** Small
- **Spec said:** stdout never prints accept, reject, or modify-spec.
- **Implementation did:** Tests match those tokens with word boundaries so the invoke text word `acceptable` does not false-fail `accept`.
- **Reason:** Preserves AC-1.3 intent against a substring collision in the pinned adapter template.
- **Resolution:** Auto-amended
- **Spec amendment:** N/A — test assertion detail; no spec-lite wording change.
