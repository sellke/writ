# Story 1: Pruning Policy ADR and Ledger Tooling — ADR-026, prune-ledger.py, and the pruned-base eval check

> **Status:** Completed ✅ (2026-09-07)
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer pruning the shared base under a Goal Card that requires every removed line to be accounted for, **I want to** record the constraint-test pruning rule as an ADR and get a `prune-ledger.py check` command wired into `eval.sh` that fails when a removal has no ledger row or a ledger row's text has crept back in, **so that** every byte cut from `system-instructions.md` and `commands/_preamble.md` is traceable and reversible before any line is actually removed in Stories 2 and 3.

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [x] Given no removals have happened yet, when `.writ/decision-records/adr-026-constraint-test-pruning.md` is read, then it states the three-way test (environment fact / human boundary / behavior request Fable 5.1-class models do unprompted) as the decision and lists at least one negative consequence (a behavior request later found load-bearing costs a baseline re-run to discover) `[AC-1.1]`
- [x] Given the repo at the pinned base commit `cf84742` with no lines removed from either base file and the ledger present but empty of rows, when `python3 scripts/prune-ledger.py check --repo .` runs, then it prints the summary line and a `ledger_missing` note (not a finding) and exits 0; and given an invalid `--base-commit`, `check` exits 2 with git's own error on stderr, never a fabricated one `[AC-1.2]`
- [x] Given a line removed from `system-instructions.md` or `commands/_preamble.md` since `cf84742` with no matching ledger row, or a ledger row whose `Text` is present as a whole line in the same base file at HEAD, when `check` runs, then it prints a `removed_not_in_ledger` finding naming the file and text, or a `ledger_text_reappeared` finding naming the ledger date and file, and exits 1 `[AC-1.3]`
- [x] Given the base files exceed `--cap` bytes, when `check` runs without `--cap-blocking` it prints an `over_cap` note and exits non-blocking on that condition, and when run with `--cap-blocking` (or `eval.sh` detects the `<!-- cap: blocking -->` marker in the ledger) it prints an `over_cap` finding and exits 1 `[AC-1.4]`
- [x] Given `bash scripts/eval.sh` runs after Story 1 lands, when the `pruned-base` check executes `check_pruned_base()`, then every `prune-ledger.py` finding surfaces via `add_finding` and the summary/note lines surface via `add_note`, and the overall eval.sh exit stays 0 with no removals yet made `[AC-1.5]`

## Implementation Tasks

- [x] 1.1 Write `scripts/tests/test_prune_ledger.py` (pytest, temp git repo fixture pinned at a fake base commit) with one test per finding code (`removed_not_in_ledger`, `ledger_text_reappeared`, `over_cap` note vs. finding, `malformed_row`, `ledger_missing`), a pipe-escape/unescape round-trip test, a move-within-a-file-is-not-a-removal test (multiset diff), and a bad-base-commit exit-2 test; write `scripts/tests/test_eval_pruned_base.sh` mirroring `scripts/tests/test_eval_pipeline_baseline.sh`'s fixture shape `[AC-1.2, AC-1.3, AC-1.4, AC-1.5]`
- [x] 1.2 Write `.writ/decision-records/adr-026-constraint-test-pruning.md` (context citing the assessment §2.1 and §3 Mechanism 1; decision: the three-way test; alternatives: byte target alone, per-model prompt tuning, do nothing; consequences including the negative one) `[AC-1.1]`
- [x] 1.3 Create `.writ/decision-records/pruned-instructions-ledger.md` with the header block and column format (`| Date | File | Class | Reason | Text |`) and zero data rows, per technical-spec §2 `[AC-1.2]`
- [x] 1.4 Implement `scripts/prune-ledger.py check` (stdlib, Python 3.9 floor, argparse subcommands, `_fail`/`_refuse` exit-2 pattern mirroring `pipeline-baseline.py`): `git diff --no-color -U0 <base-commit> -- <file>` parsing for removed lines, multiset move-within-file exclusion, ledger row regex and pipe-unescape, the five finding codes, the summary line, exit codes 0/1/2 `[AC-1.2, AC-1.3, AC-1.4]`
- [x] 1.5 Implement `scripts/prune-ledger.py measure --repo .` printing bytes per `##`/`###` section for both base files `[AC-1.2]`
- [x] 1.6 Register `check_pruned_base()` in `scripts/eval.sh` next to `check_pipeline_baseline()`, added to the `CHECKS=(...)` array as `pruned-base`; relay findings via `add_finding` and notes via `add_note`; decide `--cap-blocking` by checking for the `<!-- cap: blocking -->` marker line in the ledger file `[AC-1.4, AC-1.5]`
- [x] 1.7 Verify all acceptance criteria: `uv run --python 3.9 pytest scripts/tests/test_prune_ledger.py` green, `bash scripts/tests/test_eval_pruned_base.sh` green, `bash scripts/eval.sh` shows 0 findings, and append the decision-log line `{date} stage-2: Story 1 — ADR-026, empty ledger, prune-ledger.py check/measure, eval.sh pruned-base check landed` to the story's completion commit `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

## Notes

**Technical considerations.** Line diffs come only from `git diff --no-color -U0 <base-commit> -- <file>`, parsed for hunk lines starting with `-` (not `---`) — never a Python reimplementation of diff. No whitespace normalization anywhere: a kept line that gets reflowed or rewrapped reads as a removal, which is intended (Business Rule 5). Move detection inside a single file is a multiset (Counter) difference of removed-line texts vs. added-line texts for that file only — a line moved between the two base files is a real removal in one and a real addition in the other, not a move. Byte counts use `os.path.getsize` on the working tree, not `git show`.

**Risks.** A reflowed kept line producing a false-positive `removed_not_in_ledger` is the documented, intended failure mode (see Business Rule 5 and the spec's Error Experience) — do not special-case it away. The ledger regex must reject any line starting with `|` that isn't a valid data row, header, or separator (`malformed_row`), so a hand-edited ledger with a typo is caught rather than silently ignored.

**Integration with later stories.** Story 2 and Story 3 are the first real consumers of `check`: every commit that removes a line must add its ledger row in the same commit (Business Rule 4), so `check` must stay green at every commit on the branch, not just at story close. Story 3 is the one that flips the cap to blocking by appending `<!-- cap: blocking -->` to the ledger file — this story's `check_pruned_base()` must already know to look for that marker even though no one sets it yet. Story 4's `verdict-provenance.py` and `eval.sh` registration mirror this story's shape exactly (same finding/note/exit-code conventions), so keeping this implementation clean and conventional pays forward directly. Story 5's `compare` step never touches the ledger; it only needs Stories 1–3's commits to exist.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows** [technical-spec.md → ## 1. `scripts/prune-ledger.py` (Story 1) → Findings table: `removed_not_in_ledger`, `ledger_text_reappeared`, `over_cap`, `malformed_row`, `ledger_missing`] [technical-spec.md → ## 1. → Summary line and Exit codes]
- **Shadow paths** [spec.md → 🎯 Experience Design → Error experience] [technical-spec.md → ## 1. → Removed lines (move-within-file exclusion via multiset difference)]
- **Business rules** [spec.md → 📋 Business Rules → 1 (constraint test is the rule, bytes are the finish line)] [spec.md → 📋 Business Rules → 2 (ledger append-only, re-add is a finding)] [spec.md → 📋 Business Rules → 3 (removed includes moved)] [spec.md → 📋 Business Rules → 4 (ledger rows land in the removal commit)] [spec.md → 📋 Business Rules → 5 (kept lines byte-identical; diff against cf84742)] [spec.md → 📋 Business Rules → 12 (decision-log line)]
- **Experience** [spec.md → 🎯 Experience Design → Happy path, step 1] [spec.md → 🎯 Experience Design → Feedback model] [spec.md → 🎯 Experience Design → State catalog → "Ledger empty (Story 1)"]
- **Requirements** [spec.md → Detailed Requirements → Story 1 — Pruning policy ADR and ledger tooling]
- **Codebase** [technical-spec.md → ## 1. `scripts/prune-ledger.py` (Story 1) → Inputs, command shape] [technical-spec.md → ## 2. Ledger format (Story 1)] [technical-spec.md → ## 7. Tests → `test_prune_ledger.py`, `test_eval_pruned_base.sh`] [scripts/pipeline-baseline.py → argparse subcommand and exit-code shape to mirror] [scripts/eval.sh → `check_pipeline_baseline()` and `CHECKS=(...)` registration shape to mirror] [scripts/tests/test_eval_pipeline_baseline.sh → bash fixture test shape to mirror] [.writ/decision-records/adr-023-stakes-proportional-diligence.md → ADR shape to mirror]

---

## What Was Built

**Implementation Date:** 2026-09-07

### Files Created

1. **`scripts/prune-ledger.py`** (355 lines)
   - Stdlib, Python 3.9. `check --repo . [--base-commit cf84742] [--cap 10000] [--cap-blocking]` and `measure --repo .`. Removed lines from `git diff --no-color -U0 <base> -- <file>` parsed after the first `@@` (so a removed `---` rule is not mistaken for the file header); per-file multiset cancellation of removed vs added texts (in-file move ≠ removal); whitespace-only lines exempt; ledger regex per technical-spec §2 with `\|` unescape; findings `removed_not_in_ledger: <file>: <text>`, `ledger_text_reappeared: <date> <file>: <text>`, `over_cap: <bytes> bytes > cap <cap>` (finding only with `--cap-blocking`, else `note:`), `malformed_row: <ledger>:<line>: <row>`; `note: ledger_missing: …` while the ledger has no rows; summary line always last: `base: <bytes> bytes (cap <cap>), ledger: <rows> rows, removed: <n>, re-added: <n>`. Exit 0/1/2; on git failure stderr is git's own message, stdout empty. `measure` reproduces the technical-spec section figures (Identity & Approach 663, Command Execution Protocol 827, Hard Constraints 1,064, Interaction Tool Selection 1,241, …; total 28,157).
2. **`scripts/tests/test_prune_ledger.py`** (438 lines)
   - 31 tests over a temp git repo fixture pinned at a fake base commit: one per finding code, note vs finding for `over_cap`, absent vs empty ledger, in-file move not a removal, cross-file move is a removal, removed `---` line, blank-line exemption, cross-file and same-file duplicate rows not reappeared, no whitespace normalization, pipe escape round-trip (unit + integration), bad base commit exit 2 with `fatal:` on stderr and empty stdout, missing repo/base file exit 2, stdlib-only AST check, `parse_diff` unit tests, `measure` output and section-sum invariant.
3. **`scripts/tests/test_eval_pruned_base.sh`** (174 lines)
   - 9 assertions mirroring `test_eval_pipeline_baseline.sh`: fixture git repo with both base files committed, `WRIT_PRUNE_BASE_COMMIT` pointed at that commit; empty ledger → PASS with summary + `ledger_missing` notes; no ledger file → note; removal without row → `FAIL (1 finding)` naming file and text; removal with row → PASS; over cap → note, then finding once `<!-- cap: blocking -->` is appended; helper exit 2 → one finding carrying git's `bad revision`; missing helper → finding; `CHECKS` registration.
4. **`.writ/decision-records/adr-026-constraint-test-pruning.md`** (106 lines)
   - Decision: the three-way test (environment fact / human boundary / behavior request) with the ledger, the check, and bytes-as-finish-line; context cites assessment §2.1, §3 Mechanism 1, §5 Step 2; alternatives A byte target alone, B per-model prompt tuning, C do nothing, D chosen; negative consequences include "a behavior request later found load-bearing costs a baseline re-run to discover" and the whitespace/move exemption.
5. **`.writ/decision-records/pruned-instructions-ledger.md`** (10 lines)
   - Header block, column legend, `| Date | File | Class | Reason | Text |` header and separator, zero rows. No `<!-- cap: blocking -->` marker (Story 3 appends it).
6. **`.writ/specs/2026-09-07-phase11-stage2-prune-the-base/drift-log.md`**
   - DEV-001..DEV-004 (below).

### Files Modified

- **`scripts/eval.sh`** (`CHECKS=(...)`, new `check_pruned_base()` beside `check_pipeline_baseline()`)
  - Registered `pruned-base`. The check notes and returns when the tree has no shared base; findings when the helper is missing or exits 2 (git's message relayed); passes `--cap-blocking` when the ledger contains the exact line `<!-- cap: blocking -->`; relays `note:` lines and the summary via `add_note` as `NOTE [pruned-base]: …` and every other line via `add_finding` at `pruned-base:<code>`. Base commit is `${WRIT_PRUNE_BASE_COMMIT:-cf84742}`.
- **`.writ/specs/2026-09-07-phase11-stage2-prune-the-base/spec-lite.md`** (For Coding Agents → Implementation Approach)
  - Two bullets amended to record DEV-001..DEV-004 (Small-drift auto-amend; pre-edit SHA-256 `274bdd4ae643f6982a0e3b51d2d7e612bc74140d763b2dcda034e94a226b6d65`).
- **`.writ/decision-log.md`** — one `2026-09-07 stage-2:` line (Business Rule 12).
- **`user-stories/README.md`** — Story 1 row and totals.

`system-instructions.md` and `commands/_preamble.md` are untouched: `git diff --stat cf84742 -- system-instructions.md commands/_preamble.md` is empty.

### Implementation Decisions

1. **Diff prefixes are classified only after the first `@@`** — the naive "starts with `-` but not `---`" rule drops a removed horizontal rule (`----` in the diff). Fixture `test_removed_horizontal_rule_is_a_removal`.
2. **Whitespace-only lines are exempt (DEV-002)** — the literal rule is unsatisfiable once a section is removed whole (every blank line would need an empty-text row that reads as re-added immediately). Recorded as a negative consequence in ADR-026.
3. **Reappeared = present and not a net removal (DEV-003)** — keeps a row for one of two identical lines honest while a real remove-then-re-add (net diff empty, text present) still fires.
4. **Working tree is the "HEAD" of the check** — `git diff <base>` already compares the working tree, so byte counts (`os.path.getsize`), reappeared scans, and removals all read the same state; the check is green or red for what `eval.sh` sees, not for the last commit.
5. **A row's `file` outside `BASE_FILES` is not itself a finding** — the removal it meant to cover surfaces as `removed_not_in_ledger`, so the typo is caught indirectly; a dedicated code was left out to stay within the five codes technical-spec §1 names.
6. **Percent-format strings and `Optional[...]`** follow `pipeline-baseline.py`'s house style; ruff's UP031/UP045 hits on both files are the same rules the mirrored script trips and the repo configures no ruff.

### Test Results

**Verification:** `uv run --python 3.9 pytest scripts/tests/test_prune_ledger.py` — 31 passed; `uv run --python 3.9 pytest -q` — 1048 passed, 1 skipped; `bash scripts/tests/test_eval_pruned_base.sh` — 9/9; all 13 `scripts/tests/test_*.sh` green; `bash scripts/eval.sh` (sandbox off) → `Findings: 0`, `Run errors: 0`, `pruned-base` PASS with notes `over_cap: 28157 bytes > cap 10000`, `ledger_missing: no rows yet`, `base: 28157 bytes (cap 10000), ledger: 0 rows, removed: 0, re-added: 0`.
**Coverage:** 97% (`scripts/prune-ledger.py`, 201 statements, 6 missed: `diff --git` reset inside a hunk, `--cap < 0` refusal, the `read_text` comprehension line, one `measure` branch, `__main__` guard)
- ✅ `test-integrity.py coverage --new-files scripts/prune-ledger.py` on the cobertura XML → `verdict: pass` (threshold 80%)
- ⚠️ `test-integrity.py authenticity --tests scripts/tests/test_prune_ledger.py` → `test_imports_no_source` (blocking). Checker false positive, pre-existing: its specifier extractor is JS-only (`from '…'` / `require(...)`) and flags every Python test in this repo that loads a hyphenated script via `spec_from_file_location` (`test_revert_resolve.py` fails identically at HEAD; issue `2026-09-03-test-integrity-authenticity-flags-every-bash-test.md`; same treatment as Stage 1 Story 1). Binding proof: the suite errored at collection before `prune-ledger.py` existed (red beat), and all 31 tests call `pl.main` / `pl.parse_ledger` / `pl.parse_diff` / `pl.measure_sections`. Not DEGRADED.
- ✅ mypy clean (`--ignore-missing-imports`); `python3 -m py_compile` ok; `bash -n scripts/eval.sh` ok
- ✅ `build-smoke.py check` → `unverifiable` (`unsupported_stack`, markdown/Python repo) — surfaced, not DEGRADED
- ✅ `python3 scripts/prune-ledger.py check --repo . --base-commit nosuchrev` → stderr `fatal: bad revision 'nosuchrev'`, stdout empty, exit 2

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Medium (DEV-002); Small (DEV-001, DEV-003, DEV-004)
- **Security:** Low — subprocess with list argv and no shell; `eval.sh` relays helper output through `printf %s`; no secrets, no network
- **Boundary Compliance:** all edits inside the owned set; `system-instructions.md`, `commands/_preamble.md`, `commands/implement-story.md` untouched

### Deviations from Spec

- **[DEV-001] `WRIT_PRUNE_BASE_COMMIT` override in `check_pruned_base()`** — Severity: Small
  - Spec said: `eval.sh` decides only `--cap-blocking`
  - Reality: base commit is `${WRIT_PRUNE_BASE_COMMIT:-cf84742}` so the bash fixture (whose history cannot contain `cf84742`) can run the real check
  - Resolution: logged; `spec-lite.md` amended
- **[DEV-002] Whitespace-only lines exempt from ledger accounting** — Severity: Medium
  - Spec said: every removed line needs a row with identical text
  - Reality: blank lines are dropped from net removals and skipped in the reappeared scan
  - Resolution: ⚠️ flagged; ADR-026 records it as a negative consequence; `spec.md` unchanged
- **[DEV-003] Reappeared requires absence from net removals** — Severity: Small
  - Spec said: a row's text present as a whole line at HEAD
  - Reality: present and not among that file's net removals
  - Resolution: logged; `spec-lite.md` amended
- **[DEV-004] Missing base file → exit 2; no-base tree → note** — Severity: Small
  - Spec said: silent
  - Reality: `check`/`measure` refuse with exit 2; `check_pruned_base()` notes and returns when either base file is absent
  - Resolution: logged; `spec-lite.md` amended

### For Story 2 and Story 3

- Append rows by hand or script; escape `|` in the text column as `\|`; the row lands in the removal commit. Run `python3 scripts/prune-ledger.py check --repo .` before each commit — it must print no finding lines.
- `python3 scripts/prune-ledger.py measure --repo .` gives the per-section byte table.
- Story 3 flips the cap by appending the exact line `<!-- cap: blocking -->` to the ledger file (anywhere; `grep -Fxq`).
- Blank lines removed with a section need no rows; a `---` rule or a table separator does.
