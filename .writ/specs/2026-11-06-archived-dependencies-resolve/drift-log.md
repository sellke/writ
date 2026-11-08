# Drift Log

> Spec: .writ/specs/2026-11-06-archived-dependencies-resolve/
> Created: 2026-11-08
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: Archived dependencies resolve — Drift Report

> Run: 2026-11-08
> Overall Drift: Small

### Deviations

#### [DEV-001] `/verify-spec` section named "Check 3f" in the spec is Check 4d
- **Severity:** Small
- **Spec said:** Check 3f's missing-reference line (AC-1.4; spec-lite Files in Scope, Integration Points, For Review Agents AC 5).
- **Implementation did:** Edited Check 4d, "Cross-spec dependency validation", the only place the quoted line exists. Check 3f is about `ac-trace.py`.
- **Reason:** The spec mislabeled the section; the intent is unchanged.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** spec-lite.md → Files in Scope, Integration Points, For Review Agents AC 5 name Check 4d.

#### [DEV-002] Byte-budget offsets: two prose trims and a ledger re-pin outside the listed edits
- **Severity:** Small
- **Spec said:** Step 2.1 gains the prescribed sentence and Check 4d changes one line; `scripts/tests/test_governor_enforcement.py` is not in scope.
- **Implementation did:** Step 2.1 uses a shorter sentence and replaces the five-code list and "show the affected spec" with "on a `blocker` ... show its exact diagnostic"; Check 4d drops "Existing story dependency validation is unchanged;"; `KNOWN_OVER_BUDGET` is re-pinned down for both files (10818 -> 10791, 1465 -> 1464).
- **Reason:** Both commands were over budget and `total_overage` is asserted exactly; the first pass grew them by 138 and 24 bytes. Every blocker summary already names the spec, and the remaining 4d sentence still says the two graphs stay distinct.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** spec-lite.md → Files in Scope lists the ledger re-pin and the offset Step 2.1 sentence.
