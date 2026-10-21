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

---

## Story 4: Keep Modified Stale Files in Every Category — Drift Report

> Run: 2026-10-20
> Overall Drift: Small

### Deviations

#### [DEV-004] Pre-fix failure names a missing warning, not a removal
- **Severity:** Small
- **Spec said:** AC-4.4: on the pre-fix `update.sh` the test "fails, naming a kept file the update removed".
- **Implementation did:** On both `ce2f049` (after Story 3) and `953f47e` (before the spec) the test fails at update 1 with `no stale warning for the kept commands/zz-kept.md`. After Story 3 the pre-fix script no longer removes the kept file; it drops the file's manifest line, so the file goes untracked. On `953f47e` the removal happens at update 2, and the test's existence check catches it when the warning check is skipped (evaluator variant: `FAIL: update 2: update removed the kept commands/zz-kept.md`).
- **Reason:** Story 3 changed how the bug shows, as the spec's Technical Concerns predicted. The test still fails on the pre-fix scripts, names a kept file, and passes after the fix.
- **Resolution:** Accepted (Small). AC wording is out of date; behavior is covered.
- **Spec amendment:** None.

#### [DEV-005] Steps 3 and 6 state two of the three doc claims
- **Severity:** Small
- **Spec said:** The technical spec says each edited section of `commands/update-writ.md` states all three claims (shipped-only baselines; kept customized or stale files keep their previous baseline; modified stale files flagged every run).
- **Implementation did:** The frontmatter `outcome`, the exit criterion, Step 7, and Completion state all three. Step 3 "Detect stale files" and Step 6 item 6 are about stale files and state the shipped-only and stale claims, not the customized-file claim.
- **Reason:** No section misdescribes the fixed behavior. The customized-file rule appears in four of the six places.
- **Resolution:** Accepted (Small).
- **Spec amendment:** None.

---

## Story 5: Repair Legacy Manifests and Remove Stale Files From Their Real Path — Drift Report

> Run: 2026-10-20
> Overall Drift: Medium (iteration 1 was Large; resolved by recode)

### Deviations

#### [DEV-006] A path rm cannot remove keeps its manifest line
- **Severity:** Small
- **Spec said:** A failed `rm` gets no Removed line and is not counted (Error & Rescue Map; story Notes).
- **Implementation did:** Also appends the path to `STALE_KEPT_ENTRIES` so its line survives and the next update retries. `rm -f … || true` no longer aborts the run under `set -e`.
- **Reason:** Without it the file would leave the manifest and stay on disk untracked. A file still on disk is a kept stale entry under Business Rule 2.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md S5 line.

#### [DEV-007] Cursor units on an unresolved legacy manifest
- **Severity:** Medium (Large at iteration 1)
- **Spec said:** Business Rule 9 and task 5.3: on an unresolved version, keep only the `.codex/config.toml.baseline` line and behave as if there were no manifest. The same rule, the State Catalog, AC-5.3, and the notice say differing files are preserved and nothing that differs is overwritten. The contract's Included list does not name update.sh's Cursor scan blocks.
- **Implementation did:** Iteration 1 followed the mechanism. On Cursor, "no baseline" meant Update, so a customized `rules/writ.mdc` and `system-instructions.md` were overwritten while the notice said they were preserved (evaluator PAUSE, Large). The orchestrator resolved it against the contract's stated outcome (AC-5.3, Rule 9, State Catalog, and `update-writ.md` Step 6 item 7, "same three-way logic as commands/agents"): the deviation was rejected and recoded. The Cursor blocks now update a unit with no baseline only when no manifest file exists. With a manifest (header or legacy), a differing unit with no baseline is preserved as "no baseline, assuming modified". `--force` still updates. The test gained Cursor unresolved, second-update, and resolved cases.
- **Reason:** The contract states the outcome; the mechanism in Rule 9 assumed "no baseline" means "preserved", which was false for the two Cursor units. The fix touches a site outside the Included list (not in the Excluded list) and also changes header manifests that lack a Cursor line (now preserved instead of updated). No-manifest behavior is unchanged.
- **Resolution:** Rejected at iteration 1, recoded; accepted at iteration 2 as Medium (warn and continue). No User Challenge: the choice keeps the locked contract rather than weakening it.
- **Spec amendment:** None.

#### [DEV-008] A legacy run that ends "Already up to date" writes no header manifest
- **Severity:** Small
- **Spec said:** AC-5.3 says the run writes a manifest with the header. The contract's Technical Concerns and Error & Rescue Map accept the early exit without a rewrite.
- **Implementation did:** The early exit is unchanged, so the repair and any fallback notice repeat until a run rewrites the manifest.
- **Reason:** Idempotent and safe; the only cost is a repeated notice.
- **Resolution:** Accepted (Small).
- **Spec amendment:** None.

#### [DEV-009] The recorded version must be 4-40 lowercase hex
- **Severity:** Small
- **Spec said:** Resolve `# version:` with `git cat-file -e "$v^{commit}"`.
- **Implementation did:** Rejects anything else before calling git (`HEAD`, `main`, uppercase hex, `--help`) and reports "version X was not found upstream".
- **Reason:** The version comes from a project file; this keeps it from being read as a git option. The scripts only ever wrote `%h` or `unknown`.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md S5 line.
