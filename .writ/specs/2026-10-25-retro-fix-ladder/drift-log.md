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

## Story 4: /refresh-command Execution-Failure and Used-Skill Criteria — Drift Report

> Run: 2026-10-29
> Overall Drift: Small

### Deviations

#### [DEV-006] Three more places name skills so the command and log format stay consistent
- **Severity:** Small
- **Spec said:** technical-spec § `commands/refresh-command.md` changes lists Phase 3, the Evidence block, Step 4.1a, Step 4.2, exit criteria, and Completion; the log-format section lists two Rejection-reasons rows and the Rejected and Target file rows.
- **Implementation did:** Also: Step 4.1 applies the diff "to the command file or skill"; the Cross-References `skills/*/SKILL.md` row adds "amendment targets when the cited run read them"; `refresh-log-format.md` gains an overview bullet for the two new reasons, names `lint-skill.sh` in the `eval failed` row, and lets the Affected section row name a skill section.
- **Reason:** Contract item 8 allows skill amendments, so the apply step, the cross-reference, and the doc must say so. All four pinned literals are intact.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec adds "Step 4.1 applies the diff to the command file or skill; the Cross-References skills row and refresh-log-format.md's overview, `eval failed`, and Affected section rows name skills." None needed in spec-lite.md.

#### [DEV-007] Step 4.1a lints the skill with the diff applied and restores it on `fail`
- **Severity:** Small
- **Spec said:** "A skill amendment also runs `bash scripts/lint-skill.sh skills/<name>/SKILL.md`; line 1 `fail` rejects with `eval failed`."
- **Implementation did:** Runs the lint with the diff applied, and on line 1 `fail` restores the file and rejects with `eval failed`.
- **Reason:** The lint reads the amended file. The step's opening line says "Before writing any amendment", so a later pass could lint a temp copy instead, as `/new-skill` does.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Step 4.1a: "lints the skill with the diff applied and restores the file on line 1 `fail`." None needed in spec-lite.md.

#### [DEV-008] A covered signal suggests `/retro` when it recurs
- **Severity:** Small
- **Spec said:** Business Rule 13 and contract item 7 stop at logging the signal under `**Rejected:**` with `execution failure` and the covering section.
- **Implementation did:** Adds one clause: "and suggest `/retro` if it recurs."
- **Reason:** Matches the spec's State Catalog row ("suggests `/retro` if it recurs") and the Integration Points line in spec-lite.
- **Resolution:** Auto-amended
- **Spec amendment:** None needed; the State Catalog already states it. None needed in spec-lite.md.

---

## Story 2: Seed This Repository's Rule-to-Enforcer Table — Drift Report

> Run: 2026-10-29
> Overall Drift: Small

### Deviations

#### [DEV-009] The Python 3.9 enforcer adds `--with pytest`
- **Severity:** Small
- **Spec said:** technical-spec § Seeded table: candidate enforcer `uv run --python 3.9 pytest <test>`.
- **Implementation did:** `uv run --python 3.9 --with pytest pytest scripts/tests/test_ac_trace.py::CitationScanTests::test_symlink_loop_does_not_crash_the_scan`, proven against parent `0335b29` of fix `ebbf064` (parent exit 1, `RuntimeError: Symlink loop`; fix exit 0; the same parent passes on Python 3.13).
- **Reason:** The parent has no `pyproject.toml`, so without the flag the parent run fails for a missing pytest, not for the mistake. The flag does nothing in the current repo.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Seeded table candidate enforcer reads `uv run --python 3.9 --with pytest pytest <test>`. None needed in spec-lite.md.

#### [DEV-010] Two enforced rows, not three; the trees proof is a planned stale window
- **Severity:** Small
- **Spec said:** Story 2 Notes list three enforced candidates; AC-2.2 needs at least two, each a fix commit whose parent the enforcer fails on.
- **Implementation did:** Seeded the Python 3.9 row and the generated-trees row (`python3 scripts/gen-platform-trees.py --check`, parent `ddfb17f` of `d47bcec`: parent exit 1 with 2 stale and 2 missing files, fix exit 0). Left out the shipped-refs row: `scripts/eval-shipped-refs.py` did not exist at `7967ea3` or `ce6e8ac`, so it cannot run in a materialized copy of either. The trees parent was a stale state the why-command spec left on purpose between its Stories 1 and 2, closed by a `feat` commit.
- **Reason:** AC-2.2 asks for at least two rows. The trees proof is a real commit that broke the rule, not a fixture, so it meets Business Rule 6. A scan of all 100 commits since `--check` was added found no accidental stale tree.
- **Resolution:** Auto-amended
- **Spec amendment:** Story 2 Notes record that the shipped-refs candidate does not qualify because its enforcer postdates the fix. None needed in spec-lite.md.
