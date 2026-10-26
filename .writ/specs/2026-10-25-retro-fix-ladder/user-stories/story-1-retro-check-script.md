# Story 1: retro-check.py, the Rule Table and Ladder Checker

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer running `/retro` **I want to** run one script that rejects malformed retro files and rule tables **So that** each ladder fix I approve carries a proof that fails on a real past mistake.

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [ ] Given a conforming retro file and rule table fixture in `tmp_path`, when `python3 scripts/retro-check.py --retro <file> --table <table> --repo <repo>` runs, then line 1 is `pass`, the summary line starts `retro-check: pass`, and the exit code is 0 `[AC-1.1]`
- [ ] Given one fixture per finding-level defect (no Rung line, Ladder entries out of order, no Proof line, an applied finding whose proof result is `passes`, an applied finding with Rung `test`, and no Disposition line), when the script runs on each, then line 1 is `fail`, a `reason:` line names `rung_missing`, `ladder_order`, `proof_missing`, `proof_not_failing`, `applied_test_rung`, or `disposition_missing` with the finding ID, and the exit code is 1 `[AC-1.2]`
- [ ] Given a `git init` repository passed as `--repo` and a Proof line citing a SHA that is not in it, when the script runs, then line 1 is `fail` with `reason: proof_ref_unknown F<n> <sha>`; the same file with a real commit SHA from that repository, or with a `.jsonl` path listed under `## Transcripts`, has no `proof_ref_unknown` reason; and with `--repo` set to a directory outside any git work tree, line 1 is `unverifiable` with `reason: no_git` and the exit code is 0 `[AC-1.3]`
- [ ] Given a rule table whose header cells differ from the six required names, or whose row has enforcer `none` with rung `lint`, when the script runs with `--table` on it, then line 1 is `fail` with `reason: table_header` or `reason: table_unenforced_rung row <n>`; and given an explicit `--table` path that does not exist, line 1 is `unverifiable` with `reason: table_missing` and the exit code is 0 `[AC-1.4]`
- [ ] Given no arguments, when the script runs, then the exit code is 2, stdout is empty, and usage text goes to stderr; given `--help`, the exit code is 0; and given a fixture directory, a listing of file names and checksums taken before and after a full run is identical `[AC-1.5]`

## Implementation Tasks

- [ ] 1.1 Write `scripts/tests/test_retro_check.py` first. Cover every reason code in technical-spec.md → ## `retro-check.py` → ### Reason codes with one fixture each, built in `tmp_path`. Use a `git init` repository with one commit for SHA cases, and call the real script through an argument list. Run the file and confirm the new tests fail `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`
- [ ] 1.2 Implement the retro-file parser in `scripts/retro-check.py`. Read the `## Transcripts` and `## Findings` blocks and the Rung, Ladder, Proof, and Disposition fields. Add the rung, ladder, proof-shape, disposition, and applied-test-rung checks `[AC-1.1, AC-1.2]`
- [ ] 1.3 Add SHA resolution with `git -C <repo> cat-file -e <sha>^{commit}` as an argument list. Add the transcript-path lookup, the `proof_ref_unknown` reason, and the `no_git` path. Keep an unknown SHA (`fail`) separate from a missing git work tree (`unverifiable`) `[AC-1.3]`
- [ ] 1.4 Add the table checks: the first markdown table, the six header cells, the rung vocabulary, the enforcer and Proof rules, and `table_row_missing` for applied or refreshed findings. Add the `--table` default and the `table_missing` handling `[AC-1.4]`
- [ ] 1.5 Add the row `| retro-check.py | check |  | commands/retro.md |` to the Classification table in `.writ/docs/agent-cli-contract.md`. Run `python3 scripts/gen-platform-trees.py` to copy the script into `plugins/writ/scripts/`. Never hand-edit generated files `[AC-1.5]`
- [ ] 1.6 Verify: run `uv run --python 3.9 pytest scripts/tests/test_retro_check.py scripts/tests/test_agent_cli_contract.py`, then `uv run --python 3.9 pytest` and `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`. Confirm no failures `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`
- [ ] 1.7 Verify: run `python3 scripts/gen-platform-trees.py --check`, which must print `pass`, then run `bash scripts/eval.sh` outside any sandbox and confirm 0 findings `[AC-1.5]`

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

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
