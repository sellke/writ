# Drift Log

> Spec: .writ/specs/2026-10-25-retro-fix-ladder/
> Created: 2026-10-29
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: retro-check.py, the Rule Table and Ladder Checker — Drift Report

> Run: 2026-10-29
> Overall Drift: Small

### Deviations

#### [DEV-001] Field parsing accepts the formatting the spec's own examples use
- **Severity:** Small
- **Spec said:** technical-spec § Retro file grammar: field lines start with `**<Field>:**`; the Ladder splits on `;`; values are bare words.
- **Implementation did:** Strips backticks that wrap a whole Rung, Disposition, Enforcer, or Since value or a Proof ref. Accepts a field line written as a list item. Does not split on a `;` inside a parenthesized ladder reason (an unbalanced `(` still fails). Ignores lines inside fenced code. Compares signal names without regard to case.
- **Reason:** Business Rule 9 puts enforcers in backticks, and a ladder reason can hold a `;`. No probe produced a false pass from these rules.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Retro file grammar adds: "Backticks around a whole value are ignored; a field line may be a list item; a `;` inside parentheses does not split a ladder entry; fenced code is skipped." None needed in spec-lite.md.

#### [DEV-002] A missing or unreadable table reports one reason instead of per-row and per-finding reasons
- **Severity:** Small
- **Spec said:** `table_header` when the header cells differ; `table_missing` and `table_row_missing F<n>` listed separately.
- **Implementation did:** A table file with no markdown table also reports `table_header`, and a wrong header skips the row checks and `table_row_missing`, since columns cannot be mapped. When a needed default table is missing, `table_missing` replaces the per-finding `table_row_missing` lines.
- **Reason:** The verdict and exit code are the same; the reason lines are fewer and name the real cause.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Reason codes: "`table_header` also covers a file with no table; with a bad header or a missing table, row-level and `table_row_missing` reasons are not printed." None needed in spec-lite.md.

#### [DEV-003] `no_git` prints once; `proof_not_failing` needs a well-formed Proof line
- **Severity:** Small
- **Spec said:** No rule on how often `no_git` prints. `proof_not_failing` when Disposition is `applied` and the result is not `fails`.
- **Implementation did:** `no_git` prints once, at the first SHA that needs resolving. A missing or malformed Proof line reports `proof_missing` or `proof_malformed`, not `proof_not_failing`. A Proof line on a `docs` or `none` finding is still shape-checked.
- **Reason:** With no parsed result there is nothing to compare; the verdict is `fail` either way.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Reason codes notes both. None needed in spec-lite.md.

#### [DEV-004] A path that exists but cannot be read exits 2
- **Severity:** Small
- **Spec said:** Exit 2 for usage errors; the error map covers only a missing path.
- **Implementation did:** A `--retro` or `--table` path that is a directory or cannot be read exits 2 with stdout empty and `retro-check: cannot read ...` on stderr.
- **Reason:** The check-shape contract in `.writ/docs/agent-cli-contract.md` allows exit 2 for a check that could not start.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Error & Rescue Map adds the row "path exists but is unreadable → exit 2, cause on stderr". None needed in spec-lite.md.

#### [DEV-005] Grammar parts with no reason code are not enforced
- **Severity:** Small
- **Spec said:** A Since-cell grammar, a finding-heading grammar, a signal vocabulary, and `.jsonl` refs in the table, with no reason code for any of them.
- **Implementation did:** Leaves a malformed Since cell (it surfaces only as `table_row_missing`), a mistyped `###` heading under `## Findings`, an unknown signal, and table `.jsonl` refs unreported.
- **Reason:** Follows the reason-code table. A heading code would need `/edit-spec`. The only producer is `/retro` Step 8 (Story 3).
- **Resolution:** Auto-amended
- **Spec amendment:** None; recorded as an open gap for a later `/edit-spec`. None needed in spec-lite.md.

---

