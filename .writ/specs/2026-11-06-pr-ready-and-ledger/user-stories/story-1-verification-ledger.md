# Story 1: Verification ledger

> **Status:** Completed ✅ (2026-11-06)
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** `/ship --watch` loop, or a developer running it by hand
**I want to** record that a PR head passed the project's test and eval commands, and later ask whether a given head is verified
**So that** a merge is bound to the exact code that was tested, and any change to that code reads NOT VERIFIED until it is tested again

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [x] Given a temp git repo with a clean checked-out head H on a branch off `main` and two `--evidence` pairs whose exits are 0, when `verify-ledger.py record --pr 7 --head H --base main --evidence 0 "<c1>" --evidence 0 "<c2>"` runs, then line 1 is `pass`, `.writ/state/verify-ledger.json` has schema `verify-ledger/1` and one row holding `pr`, `head`, `patch_id`, `base_ref`, `merge_base`, `recorded_at`, and both evidence entries, `check --pr 7 --head H` prints `pass` with a `verified_exact` reason and exits 0, and a second `record` for the same PR and head leaves one row for it, holding the new evidence, with a `reason: replaced` line `[AC-1.1]`
- [x] Given a non-zero evidence exit, a `--head` that is not the checked-out HEAD, or a modified tracked file, when `record` runs, then line 1 is `fail`, a reason names `evidence_failed`, `head_not_checked_out`, or `dirty_tree`, the exit code is 1, and the ledger file is byte-identical to before (or still absent); and when `os.replace` raises during an accepted `record`, then the ledger file is byte-identical to before and no `*.tmp` file remains in `.writ/state/` `[AC-1.2]`
- [x] Given H recorded for PR 7 and a different head J recorded for PR 8, when `check` runs on each single mutation of H — one changed byte, a whitespace-only re-indent of a Python line, `chmod +x` with no content change, a binary file's bytes changed — and on a head with H's diff checked under PR 8, then each prints `fail` with `patch_id_mismatch` and exits 1, and when H's commit is rebased unchanged onto a `main` that gained lines above the changed hunk, then `check` under PR 7 prints `pass` with `verified_patch_id` `[AC-1.3]`
- [x] Given a global git config with `diff.noprefix=true`, `diff.algorithm=patience`, `diff.renames=copies`, and `color.ui=always`, when `record` and `check` compute patch-ids, then the ids equal the ids computed with no config; and given a head absent from the repo, a `--base` that does not resolve, or a `PATH` shim `git` that rejects `patch-id --verbatim`, when `check` runs on a head with no exact row, then it prints `fail` with `head_unavailable`, `base_unavailable`, or `patch_id_unavailable` and never `pass`, while a row recorded under the shim has `patch_id: null` and still reads `verified_exact` for its own head `[AC-1.4]`
- [x] Given the story's changes, when `test_agent_cli_contract.py` and `test_agent_cli_contract_doc.py` run, then `verify-ledger.py` has a `check` row whose Callers cell reads `none shipped yet; /ship --watch (spec 2026-11-06-ship-watch-and-merge)`, its smoke `check` in an empty temp dir prints `fail` with `no_rows` and exits 1, `--help` exits 0, a malformed ledger file makes `check` exit 2 with stdout empty, and `python3 scripts/gen-platform-trees.py --check` reports no stale or missing file `[AC-1.5]`

## Implementation Tasks

- [x] 1.1 Write `scripts/tests/test_verify_ledger.py`, with a module docstring that names `2026-11-06-pr-ready-and-ledger` Story 1 above every AC tag. Add a `make_repo(tmp_path)` helper: `git init -b main`, commits through `git -c user.name=t -c user.email=t@example.com -c commit.gpgsign=false`, and a feature branch. Write `RecordTests` and `CheckTests`. Write `MutationTests`, one `subTest` per mutation in AC-1.3, each asserting the exact line 1, reason code, and exit. Write `HostileConfigTests`, which point `GIT_CONFIG_GLOBAL` at a temp file. Write `FailClosedTests`, using a `PATH` shim `git` script that exits 129 for `patch-id --verbatim` and `exec`s the real git otherwise. Write a malformed-ledger test and an `os.replace` failure test. Run them on Python 3.9 and confirm they fail `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`
- [x] 1.2 Create `scripts/verify-ledger.py`. The module docstring holds the CLI, the file format, the patch-id recipe, the reason codes, and the exit codes from technical-spec § S4. Use argparse with `RawDescriptionHelpFormatter`. `record` takes `--pr` (int), `--head`, `--base`, `--evidence` (`nargs=2`, `action="append"`, required), and `--repo` (default `.`). `check` takes `--pr`, `--head`, `--base` (optional), and `--repo`. `UsageError` exits 2 with `verify-ledger: <cause>` on stderr and stdout empty. Copy `_git`, `_resolve`, and `printable` from `scripts/repro-order.py`. `main()` returns the exit code `[AC-1.5]`
- [x] 1.3 Add the ledger file I/O. `ledger_path(repo)` returns `<repo>/.writ/state/verify-ledger.json`. `load_ledger` reads a missing file as empty rows and raises `LedgerError` for an unreadable file, invalid JSON, another schema, or a malformed row (field types per technical-spec § File). `write_ledger` writes sorted, indented JSON through `tempfile.mkstemp(dir=<state dir>)` and `os.replace`, removes the temp file on error, and creates `.writ/state/` when missing `[AC-1.1, AC-1.2, AC-1.5]`
- [x] 1.4 Add `patch_id(repo, base_sha, head_sha) -> Tuple[Optional[str], Optional[str], str]` (merge base, id, why). It runs `git merge-base`, then the pinned `git diff` from technical-spec § Patch-id, captured as bytes, then `git patch-id --verbatim` with those bytes as `input=`, keeping the first field. Detect `--verbatim` once with empty input. Map an unsupported flag, an empty diff, and no merge base to `verbatim_unsupported`, `empty_diff`, and `no_merge_base`. A missing `git` inside this path is `git_not_found` `[AC-1.3, AC-1.4]`
- [x] 1.5 Implement `record` per technical-spec § `record`. Resolve `--head` and `--base`, rejecting a leading `-`. Collect every refusal that holds: `evidence_failed`, `head_not_checked_out`, and `dirty_tree` from `git status --porcelain --untracked-files=no`. On a refusal, print `fail` and exit 1 without loading or writing the file. Otherwise compute the merge base and patch-id, set `recorded_at` in UTC, replace or append the `(pr, head)` row, write it, and print the `pass` lines and summary `[AC-1.1, AC-1.2]`
- [x] 1.6 Implement the public `ledger_check(repo, pr, head, base=None) -> (verdict, reasons)` per technical-spec § `check` and `ledger_check`: `no_rows`, exact match without git for full hex, then resolution, the base from the latest row, the patch-id, `verified_patch_id` or `patch_id_mismatch`. It never prints and raises `LedgerError`. The `check` CLI wraps it, maps `LedgerError` to exit 2, and prints the summaries `[AC-1.1, AC-1.3, AC-1.4]`
- [x] 1.7 Register and verify. In `.writ/docs/agent-cli-contract.md`, add the `verify-ledger.py` row after `verdict-provenance.py` and its Notes entry from technical-spec § Notes entries. In `scripts/tests/test_agent_cli_contract.py`, add the `verify-ledger.py` smoke in the `# check` group. Run `python3 scripts/gen-platform-trees.py`, then `--check`. Run `test_verify_ledger.py` and both contract tests on Python 3.9 and 3.14, each run alone, and `bash scripts/eval.sh --check=platform-trees`. Check each AC against the test that carries its tag `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

## Notes

- **Why `--verbatim`.** `--stable` strips whitespace, so a Python re-indent keeps the verified id. Pinned flags matter because `diff.noprefix=true` changed the id. Probes: technical-spec § Probes.
- **Bytes.** Binary diffs are not UTF-8. Do not pass `encoding=` or `text=True` to the `git diff` or `git patch-id` calls. Other git calls may decode, as in `repro-order.py`.
- **Cross-PR mutation.** "H's diff checked under PR 8" needs PR 8 to have its own row (J). Without one, the result is `no_rows`, which does not prove that ids stay within a PR.
- **Rebase case.** Build `main` with lines above the changed hunk, then `git rebase main` on the feature branch. The rebased head is a new SHA with the same verbatim id. `check` finds no exact row and passes through the patch-id path.
- **`recorded_at` ordering.** "Most recent row" means the latest `recorded_at`. Two records in the same second tie; break the tie by file order (later wins).
- **Smoke.** The contract smoke runs `check` with `--repo {tmp}` and no ledger file. It must not touch the Writ checkout's `.writ/state/`: `test_smoke_leaves_repo_unchanged` snapshots that folder.
- **Run pytest alone.** Another `.writ/state/` writer or `eval.sh` running at the same time makes `test_smoke_leaves_repo_unchanged` fail (CLAUDE.md).
- **No caller yet.** The Callers cell says so. The second spec replaces it.
- **Python 3.9.** `from __future__ import annotations`; `typing` generics; no `match`.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Record (refusals), Record (unresolvable rev, bad evidence), Write ledger, Compute patch-id (all four rows), Check, Read ledger (check), Run git] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [`verify-ledger.py record`, `verify-ledger.py check`] — technical-spec.md → ## Shadow Paths
- **Business rules:** [Business Rule 8 (rows only for passing evidence on the checked-out clean head), Business Rule 9 (exact or same-PR patch-id; fail closed), Business Rule 10 (one writer, atomic, replace on same head)] — spec.md → ## Specification Contract → 📋 Business Rules; spec.md → ## Business Rules (Expanded) → ### Ledger record, ### Ledger check, ### State file
- **Experience:** [Error experience (`record` refused, exit 1, nothing written), State Catalog `verify-ledger.py` table] — spec.md → ## Specification Contract → 🎯 Experience Design; spec.md → ## Experience Design → ### State Catalog

---

## What Was Built

**Implementation Date:** 2026-11-06

### Files Created

1. **`scripts/verify-ledger.py`** (523 lines)
   - `record` and `check` in the check shape; the public `ledger_check(repo, pr, head, base=None)`; `load_ledger` / `write_ledger` (`mkstemp` + `os.replace`); `patch_id` over the pinned `git diff` piped as bytes to `git patch-id --verbatim`, with feature detection and fail-closed causes.
2. **`scripts/tests/test_verify_ledger.py`** (773 lines)
   - Temp-repo tests: `RecordTests`, `RefusalTests`, `MutationTests`, `HostileConfigTests`, `SubmoduleTests`, `PopulatedSubmoduleTests`, `FailClosedTests`, `ContractTests` (28 tests, 24 subtests).
3. **`plugins/writ/scripts/verify-ledger.py`** (523 lines)
   - Byte copy generated by `python3 scripts/gen-platform-trees.py`.
4. **`.writ/specs/2026-11-06-pr-ready-and-ledger/drift-log.md`**
   - DEV-001 to DEV-004 (all Small).

### Files Modified

- **`.writ/docs/agent-cli-contract.md`** (Classification table; Notes)
  - `verify-ledger.py` check row after `verdict-provenance.py` with the shared Callers text; its Notes entry from technical-spec § Notes entries.
- **`scripts/tests/test_agent_cli_contract.py`** (`SMOKE_INVOCATIONS`, `# check` group)
  - `Smoke("verify-ledger.py", ["check", "--pr", "1", "--head", "a" * 40, "--repo", "{tmp}"], {})`.
- **`.writ/specs/2026-11-06-pr-ready-and-ledger/spec-lite.md`** (For Coding Agents; Test Strategy)
  - Small-drift amendments for DEV-001 to DEV-004.

### Implementation Decisions

1. **No coding subagent** — this lane ran the coding role itself with the full spec in context; Gate 3 ran as a spawned read-only `review-agent` (Gate 2.5 routed it). Every gate script implement-story names was run.
2. **Pins beyond the spec's flag list** — `--ignore-submodules=none --submodule=short` close a fail-open the Gate 3 review found (a submodule bump read VERIFIED under `ignore = all`); `-c diff.suppressBlankEmpty=false`, `--inter-hunk-context=0`, `--indent-heuristic`, and dropping `GIT_DIFF_OPTS`/`GIT_EXTERNAL_DIFF` pin the remaining config that changes the id.
3. **`record` checks run before the ledger is loaded** — a refusal never reads or writes the file.

### Test Results

**Verification:** `uv run --isolated --python 3.9 --with pytest pytest -q scripts/tests/test_verify_ledger.py scripts/tests/test_agent_cli_contract.py scripts/tests/test_agent_cli_contract_doc.py` and the same on 3.14: 341 passed each (story file alone: 28 passed). `gen-platform-trees.py --check`: pass. Gate scripts: arch-check pass (proceed); arch-lint 0 rulesets; build-smoke unsupported_stack (informational); change-surface cross-component, route review-agent; review-override check unverifiable (no_coverage_report); safety-fact pass (measured tested); evidence unverifiable (verdict_not_fail PASS); drift-format pass; test-integrity authenticity pass; app-verify unverifiable (no_recipe); docs-check unverifiable (no public exports).
**Coverage:** 94%
- ✅ `test-integrity.py coverage --new-files scripts/verify-ledger.py`: pass, re-derived from a subprocess-measured cobertura report (291 statements, 17 missed)
- ✅ Each AC-1.3 mutation asserts the exact verdict, reason, and exit
- ✅ The submodule test fails on a copy of the script without the two submodule flags

### Review Outcome

**Result:** PASS

- **Iteration count:** 2 iteration(s)
- **Drift:** Small
- **Security:** Clean
- **Boundary Compliance:** All code changes are within Owned; the generated plugin copy and the spec-healing files are justified.

### Deviations from Spec

- **[DEV-001] Pinned diff recipe pins five more options and drops two env vars** — Severity: Small
  - Spec said: technical-spec § Patch-id flag list ending `-U3 --no-relative`.
  - Reality: adds `-c diff.suppressBlankEmpty=false`, `--inter-hunk-context=0`, `--indent-heuristic`, `--ignore-submodules=none`, `--submodule=short`; drops `GIT_DIFF_OPTS` and `GIT_EXTERNAL_DIFF` for the diff.
  - Resolution: Auto-amended spec-lite.md
- **[DEV-002] Extra `patch_id_unavailable (git_failed)` cause** — Severity: Small
  - Spec said: causes `verbatim_unsupported`, `empty_diff`, `no_merge_base`, `git_not_found`.
  - Reality: any other git failure is `git_failed`, which fails closed.
  - Resolution: Auto-amended spec-lite.md
- **[DEV-003] Test harness uses unittest classes with temp dirs** — Severity: Small
  - Spec said: pytest `tmp_path` and five named classes.
  - Reality: `unittest` + `tempfile`, house style; more classes.
  - Resolution: Auto-amended spec-lite.md
- **[DEV-004] `record`'s tracked-change check counts submodule state** — Severity: Small
  - Spec said: `git status --porcelain --untracked-files=no`.
  - Reality: adds `--ignore-submodules=untracked`.
  - Resolution: Auto-amended spec-lite.md
