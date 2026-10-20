# Drift Log

> Spec: .writ/specs/2026-10-20-ci-and-update-integrity/
> Created: 2026-10-20
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: CI Runs Every Suite — Drift Report

> Run: 2026-10-20
> Overall Drift: Small

### Deviations

#### [DEV-001] Bash step skips an unmatched glob
- **Severity:** Small
- **Spec said:** The technical-spec sketch of the bash step has no guard. The Shadow Paths row for "CI run" says "No `test_*.sh`: zero tests, exit 0".
- **Implementation did:** The step starts each iteration with `[ -f "$t" ] || continue`, and `test_bash_block_with_no_tests_exits_zero` covers it. Without the guard, an empty test folder would print `FAIL scripts/tests/test_*.sh` and exit 1.
- **Reason:** The sketch and the shadow-path row disagreed. The implementation follows the shadow path. If the test folder moves, CI passes with 0 tests, and only the `bash tests failed: 0` line shows it.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md S1 line now says the bash step skips an unmatched glob.
