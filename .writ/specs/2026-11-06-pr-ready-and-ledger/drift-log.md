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
