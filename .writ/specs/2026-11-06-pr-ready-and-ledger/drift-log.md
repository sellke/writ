# Drift Log

> Spec: .writ/specs/2026-11-06-pr-ready-and-ledger/
> Created: 2026-11-06
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: Verification ledger — Drift Report

> Run: 2026-11-06
> Overall Drift: Small

### Deviations

#### [DEV-001] Pinned diff recipe pins five more options and drops two env vars
- **Severity:** Small
- **Spec said:** technical-spec § Patch-id: `git diff --no-color --no-ext-diff --no-textconv --binary --full-index --no-renames --src-prefix=a/ --dst-prefix=b/ --diff-algorithm=myers -U3 --no-relative`.
- **Implementation did:** Adds `-c diff.suppressBlankEmpty=false`, `--inter-hunk-context=0`, `--indent-heuristic`, `--ignore-submodules=none`, and `--submodule=short`, and runs the diff without `GIT_DIFF_OPTS` or `GIT_EXTERNAL_DIFF` in its environment. The first three equal Git's defaults, so ids match the spec's list on a default config.
- **Reason:** The Hardest Constraint requires every output-affecting option pinned. A probe showed `diff.suppressBlankEmpty=true` changed the verbatim id. The Gate 3 review found that `.gitmodules` `ignore = all` (which a verified head can add), `diff.ignoreSubmodules=all`, or `diff.submodule=log` hid a submodule pointer bump, so a bumped head read `verified_patch_id`, and that `GIT_DIFF_OPTS=-u0` overrode `-U3`. `SubmoduleTests` and `test_git_diff_opts_does_not_change_the_id` pin the fix.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** spec-lite.md → For Coding Agents → Patch-id bullet names the added pins.

#### [DEV-002] Extra `patch_id_unavailable (git_failed)` cause
- **Severity:** Small
- **Spec said:** The `why` values are `verbatim_unsupported`, `empty_diff`, `no_merge_base`, and `git_not_found`.
- **Implementation did:** An unexpected non-zero exit from `merge-base`, `diff`, or `patch-id`, or an OS error other than a missing `git`, gives `patch_id_unavailable (git_failed)`. The id is null, so the result fails closed.
- **Reason:** The spec left these cases undefined. Callers branch on the `patch_id_unavailable` code, not the cause.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** spec-lite.md → For Coding Agents → Error Handling names `git_failed`.

#### [DEV-003] Test harness uses unittest classes with temp dirs
- **Severity:** Small
- **Spec said:** `make_repo(tmp_path)`, pytest `tmp_path`, and classes `RecordTests`, `CheckTests`, `MutationTests`, `HostileConfigTests`, `FailClosedTests`.
- **Implementation did:** `unittest.TestCase` classes with `tempfile.TemporaryDirectory`, as `scripts/tests/test_repro_order.py` does. The check tests sit in `RecordTests`; `RefusalTests`, `SubmoduleTests`, and `ContractTests` are added.
- **Reason:** House style. Each test still builds its own repo and never touches the Writ checkout's `.writ/state/`.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** spec-lite.md → For Testing Agents → Test Strategy says "in a temp dir".

#### [DEV-004] `record`'s tracked-change check counts submodule state
- **Severity:** Small
- **Spec said:** Refuse when `git status --porcelain --untracked-files=no` is non-empty.
- **Implementation did:** Adds `--ignore-submodules=untracked`, so a submodule whose checked-out commit or tracked content differs from the head refuses `record` even when `.gitmodules` says `ignore = all`.
- **Reason:** Business Rule 8 binds the evidence to the head's code. A submodule at another commit means the tests ran on other code. Untracked files stay ignored, as the spec says.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** spec-lite.md → For Coding Agents → Error Handling names the submodule check.

## Story 2: `pr-ready.py` snapshot and blocker classes — Drift Report

> Run: 2026-11-06
> Overall Drift: Small

### Deviations

#### [DEV-005] A running CheckRun may carry conclusion `""` or null
- **Severity:** Small
- **Spec said:** technical-spec § Fields read: any `conclusion` outside the `statusCheckRollup` table is exit 2; the table lists only `COMPLETED` conclusions.
- **Implementation did:** Accepts `""` or null when `status` is not `COMPLETED`. A `COMPLETED` run still needs a listed conclusion.
- **Reason:** `gh pr view` prints `"conclusion": ""` for a running check. Without this, every snapshot with a pending check would exit 2 instead of reporting `checks_pending`.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** spec-lite.md → For Coding Agents → Error Handling notes the running-check conclusion.

#### [DEV-006] A missing key in the comments chain reads as null
- **Severity:** Small
- **Spec said:** `comments.nodes[0].author.login` is a string or null at any level; a missing required field is exit 2.
- **Implementation did:** A missing `comments`, `nodes`, `author`, or `login` key reads as null and prints `?`. A present value of the wrong type is still exit 2.
- **Reason:** The S1 query always requests the chain, so only a hand-built snapshot lacks a key, and the only effect is a `?` login.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** spec-lite.md → For Coding Agents → Error Handling notes the missing-key rule.

#### [DEV-007] The contract test's AC-ID guard accepts a later spec's IDs, and two tests are appended
- **Severity:** Small
- **Spec said:** technical-spec § `scripts/tests/test_agent_cli_contract.py`: append one doc-coverage test under a docstring naming this spec.
- **Implementation did:** Appends `test_fail_exits_are_documented` and `test_fail_exits_apply_only_to_listed_scripts`, and widens `test_every_test_names_its_ac_id` (AC-3.4 of `2026-10-12-agent-cli-contract`) to accept an `AC-N.M` beside a backticked spec name and `Story N`.
- **Reason:** The old guard accepted only `AC-[35].[1-5]`, so it rejected this spec's AC-2.5 tags. ac-trace still attributes the tags to this spec through the section comment that names it.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** spec-lite.md → Files in Scope names the two appended tests and the widened guard.

#### [DEV-008] A rejected snapshot value prints in a bounded form
- **Severity:** Small
- **Spec said:** spec.md § Snapshot validity: an enum value outside the tables, or a wrong `schema`, is exit 2 with the cause on stderr. The spec does not say how the rejected value prints.
- **Implementation did:** The stderr cause shows a rejected enum or `schema` value as a string cut to 80 characters, a JSON scalar (`null`, `true`, `7`), or `<type>` for a list or object (`_shown` in `scripts/pr-ready.py`).
- **Reason:** A hostile snapshot could put a long or crafted value in an enum field. Printing containers by type only keeps that text off stderr; the value still passes through `printable`.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** spec-lite.md → For Coding Agents → Error Handling notes the bounded form.

## Story 3: Ledger gate and machine output — Drift Report

> Run: 2026-11-06
> Overall Drift: Small

### Deviations

#### [DEV-009] `evaluate` takes a `(pr, head)` gate that wraps `ledger_check`, and the loader checks the module and writes no bytecode
- **Severity:** Small
- **Spec said:** technical-spec § S2 Evaluation: "Story 3 passes the loaded `ledger_check`" to `evaluate(snapshot, ledger)`. § S3: a missing file or a load error exits 2, loaded with the `scripts/exit-criteria.py` `_load_sibling` pattern.
- **Implementation did:** `ledger_gate(repo)` returns `gate(pr, head)`, which calls `ledger_check(repo, pr=..., head=...)` and maps `LedgerError` to `("fail", ["ledger_unreadable (<detail>)"])`; `evaluate` prints that reason as `not_verified ledger_unreadable (...)`. A loaded module without `ledger_check` or `LedgerError` is a load error (exit 2, `it defines no ledger_check`). `_load_sibling` sets `sys.dont_write_bytecode` while it runs the module, so a check writes no `__pycache__`.
- **Reason:** `evaluate` stays pure and free of the ledger module's exception type. The Gate 3 review found that the plain load pattern wrote `__pycache__/verify-ledger.*.pyc` beside the script under a default Python, against Business Rule 1 ("writes nothing"). The CLI output, JSON shape, and exit codes are as specified.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** spec-lite.md → For Coding Agents → Implementation Approach names `ledger_gate` and the bytecode guard.

## Spec close-out — Drift Report

> Run: 2026-11-06
> Overall Drift: Small

### Deviations

#### [DEV-010] The Story 2 review repro ships as its own test file
- **Severity:** Small
- **Spec said:** spec-lite.md → Files in Scope lists `scripts/tests/test_verify_ledger.py`, `scripts/tests/test_pr_ready.py`, and the fixtures as the new test files.
- **Implementation did:** Story 2 also adds `scripts/tests/test_pr_ready_head_repro.py`, the Gate 3 reviewer's confirmed repro (a `headRefOid` with a trailing newline exits 2), kept byte for byte.
- **Reason:** implement-story's evidence gate pins the repro by sha256 in `.writ/state/evidence-story-2-pr-ready-blocker-classes.json` and fails `repro_removed` or `repro_modified` if it is deleted or edited. It tests only in-scope code. The spec supervisor flagged the file as outside Files in Scope.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** spec-lite.md → For Coding Agents → Files in Scope names the repro file.
