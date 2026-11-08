# Story 1: retro-check.py, the Rule Table and Ladder Checker

> **Status:** Completed ✅ (2026-10-29)
> **Commit:** 50ecd98ac4ceec066baf952313df53e8ba70de51
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer running `/retro` **I want to** run one script that rejects malformed retro files and rule tables **So that** each ladder fix I approve carries a proof that fails on a real past mistake.

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [x] Given a conforming retro file and rule table fixture in `tmp_path`, when `python3 scripts/retro-check.py --retro <file> --table <table> --repo <repo>` runs, then line 1 is `pass`, the summary line starts `retro-check: pass`, and the exit code is 0 `[AC-1.1]`
- [x] Given one fixture per finding-level defect (no Rung line, Ladder entries out of order, no Proof line, an applied finding whose proof result is `passes`, an applied finding with Rung `test`, and no Disposition line), when the script runs on each, then line 1 is `fail`, a `reason:` line names `rung_missing`, `ladder_order`, `proof_missing`, `proof_not_failing`, `applied_test_rung`, or `disposition_missing` with the finding ID, and the exit code is 1 `[AC-1.2]`
- [x] Given a `git init` repository passed as `--repo` and a Proof line citing a SHA that is not in it, when the script runs, then line 1 is `fail` with `reason: proof_ref_unknown F<n> <sha>`; the same file with a real commit SHA from that repository, or with a `.jsonl` path listed under `## Transcripts`, has no `proof_ref_unknown` reason; and with `--repo` set to a directory outside any git work tree, line 1 is `unverifiable` with `reason: no_git` and the exit code is 0 `[AC-1.3]`
- [x] Given a rule table whose header cells differ from the six required names, or whose row has enforcer `none` with rung `lint`, when the script runs with `--table` on it, then line 1 is `fail` with `reason: table_header` or `reason: table_unenforced_rung row <n>`; and given an explicit `--table` path that does not exist, line 1 is `unverifiable` with `reason: table_missing` and the exit code is 0 `[AC-1.4]`
- [x] Given no arguments, when the script runs, then the exit code is 2, stdout is empty, and usage text goes to stderr; given `--help`, the exit code is 0; and given a fixture directory, a listing of file names and checksums taken before and after a full run is identical `[AC-1.5]`

## Implementation Tasks

- [x] 1.1 Write `scripts/tests/test_retro_check.py` first. Cover every reason code in technical-spec.md → ## `retro-check.py` → ### Reason codes with one fixture each, built in `tmp_path`. Use a `git init` repository with one commit for SHA cases, and call the real script through an argument list. Run the file and confirm the new tests fail `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`
- [x] 1.2 Implement the retro-file parser in `scripts/retro-check.py`. Read the `## Transcripts` and `## Findings` blocks and the Rung, Ladder, Proof, and Disposition fields. Add the rung, ladder, proof-shape, disposition, and applied-test-rung checks `[AC-1.1, AC-1.2]`
- [x] 1.3 Add SHA resolution with `git -C <repo> cat-file -e <sha>^{commit}` as an argument list. Add the transcript-path lookup, the `proof_ref_unknown` reason, and the `no_git` path. Keep an unknown SHA (`fail`) separate from a missing git work tree (`unverifiable`) `[AC-1.3]`
- [x] 1.4 Add the table checks: the first markdown table, the six header cells, the rung vocabulary, the enforcer and Proof rules, and `table_row_missing` for applied or refreshed findings. Add the `--table` default and the `table_missing` handling `[AC-1.4]`
- [x] 1.5 Add the row `| retro-check.py | check |  | commands/retro.md |` to the Classification table in `.writ/docs/agent-cli-contract.md`. Run `python3 scripts/gen-platform-trees.py` to copy the script into `plugins/writ/scripts/`. Never hand-edit generated files `[AC-1.5]`
- [x] 1.6 Verify: run `uv run --python 3.9 pytest scripts/tests/test_retro_check.py scripts/tests/test_agent_cli_contract.py`, then `uv run --python 3.9 pytest` and `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`. Confirm no failures `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`
- [x] 1.7 Verify: run `python3 scripts/gen-platform-trees.py --check`, which must print `pass`, then run `bash scripts/eval.sh` outside any sandbox and confirm 0 findings `[AC-1.5]`

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Notes

- **Interface:** `python3 scripts/retro-check.py [--retro PATH] [--table PATH] [--repo DIR]`. Exit 0 for pass or unverifiable, 1 for fail, 2 for usage. The spec fixes the output shape: line 1 verdict, `reason:` lines in file order (retro findings, then table rows), and a summary line.
- **Verdict precedence:** any fail reason makes the verdict `fail`. Otherwise any unverifiable reason makes it `unverifiable`. Otherwise `pass`.
- **Two SHA outcomes:** `git cat-file` returning non-zero inside a real repository means the SHA is unknown, which is `fail`. A missing `git` binary or a non-repo `--repo` is `unverifiable`. Tests cover both.
- **Git identity in fixtures:** the `git init` fixture needs a commit. Set `GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`, `GIT_COMMITTER_NAME`, and `GIT_COMMITTER_EMAIL` in the subprocess environment so the test does not depend on the developer's git config.
- **Fixtures only:** Story 1 tests use fixture tables. The seeded `.writ/retros/rule-enforcers.md` lands in Story 2, which runs this script against it.
- **Out of scope here:** `commands/retro.md` changes belong to Story 3. The script reads files, runs `git cat-file`, and writes nothing.
- **Python floor:** 3.9 stdlib only. Subprocess calls use an argument list, never `shell=True`.
- **Shipping:** `is_shippable_script` ships any `*.py` not on its deny list, so `plugins/writ/scripts/` gains the script on regeneration. `test_table_complete` in `scripts/tests/test_agent_cli_contract.py` fails until the Classification row exists, so add both in the same change.

## Context for Agents

- **Error map rows:** [retro-check.py reads the retro file, retro-check.py reads the table, retro-check.py resolves a SHA, retro-check.py args] — from technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [`--retro` happy path, nil input, empty input, upstream error] — from technical-spec.md → ## Shadow Paths
- **Business rules:** [Proof line grammar (rule 6), proof outcomes per disposition (rule 7), table format (rule 9), Python 3.9 floor (rule 17)] — from spec.md → ## Business Rules (Expanded)
- **Experience:** [] — command-line output only; no UI states

## What Was Built

**Implementation Date:** 2026-10-29

### Files Created

- **`scripts/retro-check.py`** (499 lines) — `[--retro PATH] [--table PATH] [--repo DIR]`. Check shape: line 1 `pass`, `fail`, or `unverifiable`; `reason:` lines in file order (retro findings, then table rows); summary `retro-check: <verdict> (<f> findings, <r> table rows, <n> reasons)`. Exit 0 pass/unverifiable, 1 fail, 2 usage. Python 3.9 stdlib, read-only, no network.
  - Parses `## Transcripts` and `## Findings` (`### F<n> [<Severity>] <Signal>: <title>` blocks; `Rung`, `Ladder`, `Proof`, `Disposition` fields) and the first markdown table of the rule table.
  - Emits all 23 reason codes in technical-spec § Reason codes.
  - Runs `git -C <repo> rev-parse --is-inside-work-tree` once, only when a SHA needs resolving, then `git -C <repo> cat-file -e <sha>^{commit}` per SHA, as argument lists. Each ref passes a hex `fullmatch` before reaching git. An unknown SHA is `fail`; no work tree or no `git` is `unverifiable` / `no_git`.
  - `--table` defaults to `rule-enforcers.md` beside the retro file. Control characters in echoed values are escaped.
- **`scripts/tests/test_retro_check.py`** (62 tests) — one fixture per reason code, a conforming retro file and table, `--help`, no-args and bad-flag usage errors with empty stdout, a read-only SHA-256 snapshot of the fixture directory (including its `.git`), SHA resolution against a `git init` repo with isolated git identity, `no_git` outside a work tree and with `git` off `PATH`, explicit and default `table_missing`, an empty `## Findings`, and the skipped-rung and applied-`passes` edge cases.
- Generated: `plugins/writ/scripts/retro-check.py`.

### Files Modified

- **`.writ/docs/agent-cli-contract.md`** — Classification row `` | `retro-check.py` | check |  | commands/retro.md | ``.

### Implementation Decisions

1. **Lenient field parsing** — backticks around a whole value, list-item field lines, `;` inside a parenthesized ladder reason, fenced code, and signal-name case are tolerated (DEV-001).
2. **One reason for an unusable table** — no table or a wrong header reports `table_header`; a needed missing default table reports `table_missing` in place of per-finding `table_row_missing` (DEV-002).
3. **`no_git` once; `proof_not_failing` only on a parsed proof** (DEV-003).
4. **Unreadable path exits 2** with the cause on stderr (DEV-004).
5. **No reason code for malformed headings, Since cells, unknown signals, or table `.jsonl` refs** — follows the spec's code table; open gap (DEV-005).

### Test Results

**Verification:** `uv run --python 3.9 pytest scripts/tests/test_retro_check.py scripts/tests/test_agent_cli_contract.py -q` → 352 passed; full `uv run --python 3.9 pytest -q` → 3630 passed, 3 skipped; bash loop → 51/51, no FAIL; `bash scripts/eval.sh` → Findings: 0; `gen-platform-trees.py --check` → pass.
- ✅ test-integrity authenticity: pass
- coverage: unverifiable (`no_coverage_report`; tests drive the script as a subprocess)

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small
- **Security:** Clean (hex-checked refs, list-argv `git`, read-only, no network)
- **Boundary Compliance:** all files owned; `plugins/writ/scripts/` copy generated
- **gate3-route:** evaluator-agent
- **reviewer-filters:** on
- **gate0-divergence:** skip (route evaluator-agent)
- **review-panel:** skipped — platform cannot spawn other vendors
- **review-override check:** unverifiable (test-integrity coverage: no_coverage_report)
- **safety-fact:** not on route
- **jev shadow:** pass (judged) criteria=5 agree=5 — advisory only
- **arch-lint:** none — see .writ/docs/architecture-lint.md
- **build-smoke:** unverifiable (unsupported_stack)
- **app-verify:** unverifiable (no_recipe)
- **docs-check:** unverifiable (no public exports in the changed set)

### Deviations from Spec

- **[DEV-001] Field parsing accepts the formatting the spec's own examples use** — Severity: Small — Resolution: Auto-amended
- **[DEV-002] A missing or unreadable table reports one reason instead of per-row and per-finding reasons** — Severity: Small — Resolution: Auto-amended
- **[DEV-003] `no_git` prints once; `proof_not_failing` needs a well-formed Proof line** — Severity: Small — Resolution: Auto-amended
- **[DEV-004] A path that exists but cannot be read exits 2** — Severity: Small — Resolution: Auto-amended
- **[DEV-005] Grammar parts with no reason code are not enforced** — Severity: Small — Resolution: Auto-amended
