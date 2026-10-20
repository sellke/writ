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

---

## Story 3: Record Baselines Only for Shipped Paths; Customized Files Keep Their Baseline — Drift Report

> Run: 2026-10-20
> Overall Drift: Small

### Deviations

#### [DEV-002] Baseline rule applied by a post-run comparison, not the action variables
- **Severity:** Small
- **Spec said:** Task 3.4: when `CLAUDE_MD_ACTION`, `AGENTS_MD_ACTION`, `RULE_ACTION`, or `SYSINST_ACTION` is `preserved`, write the previous baseline.
- **Implementation did:** After the run, files are compared to upstream with `cmp`, and Writ blocks by inner hash against the template hash. Equal records the upstream hash; different carries the previous baseline or writes no line. `install.sh` uses the same rule, since it has no action variables for it.
- **Reason:** The evaluator probed every reachable action. `unchanged`, `update`, `restore`, `new`, and `--force` end equal to upstream; `preserved` ends different; `error` aborts before the manifest is written. The two methods agree.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md S3 line names the post-run comparison.

#### [DEV-003] install.sh gained helpers called only by write_copy_manifest
- **Severity:** Small
- **Spec said:** "Change only `write_copy_manifest` and the two helpers it alone calls."
- **Implementation did:** Added `MANIFEST_PREVIOUS_BASELINES`, `previous_manifest_hash_for`, and `record_file_baseline`, called only from `write_copy_manifest` and the two `append_manifest_*` helpers. No other existing `install.sh` function changed.
- **Reason:** Keeps the scope boundary (no other install path changes) while sharing one baseline rule between the walk loops.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md "Files in Scope" install.sh line names the new helpers.
