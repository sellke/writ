# Story 1: Pruning Policy ADR and Ledger Tooling — ADR-026, prune-ledger.py, and the pruned-base eval check

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer pruning the shared base under a Goal Card that requires every removed line to be accounted for, **I want to** record the constraint-test pruning rule as an ADR and get a `prune-ledger.py check` command wired into `eval.sh` that fails when a removal has no ledger row or a ledger row's text has crept back in, **so that** every byte cut from `system-instructions.md` and `commands/_preamble.md` is traceable and reversible before any line is actually removed in Stories 2 and 3.

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [ ] Given no removals have happened yet, when `.writ/decision-records/adr-026-constraint-test-pruning.md` is read, then it states the three-way test (environment fact / human boundary / behavior request Fable 5.1-class models do unprompted) as the decision and lists at least one negative consequence (a behavior request later found load-bearing costs a baseline re-run to discover) `[AC-1.1]`
- [ ] Given the repo at the pinned base commit `cf84742` with no lines removed from either base file and the ledger present but empty of rows, when `python3 scripts/prune-ledger.py check --repo .` runs, then it prints the summary line and a `ledger_missing` note (not a finding) and exits 0; and given an invalid `--base-commit`, `check` exits 2 with git's own error on stderr, never a fabricated one `[AC-1.2]`
- [ ] Given a line removed from `system-instructions.md` or `commands/_preamble.md` since `cf84742` with no matching ledger row, or a ledger row whose `Text` is present as a whole line in the same base file at HEAD, when `check` runs, then it prints a `removed_not_in_ledger` finding naming the file and text, or a `ledger_text_reappeared` finding naming the ledger date and file, and exits 1 `[AC-1.3]`
- [ ] Given the base files exceed `--cap` bytes, when `check` runs without `--cap-blocking` it prints an `over_cap` note and exits non-blocking on that condition, and when run with `--cap-blocking` (or `eval.sh` detects the `<!-- cap: blocking -->` marker in the ledger) it prints an `over_cap` finding and exits 1 `[AC-1.4]`
- [ ] Given `bash scripts/eval.sh` runs after Story 1 lands, when the `pruned-base` check executes `check_pruned_base()`, then every `prune-ledger.py` finding surfaces via `add_finding` and the summary/note lines surface via `add_note`, and the overall eval.sh exit stays 0 with no removals yet made `[AC-1.5]`

## Implementation Tasks

- [ ] 1.1 Write `scripts/tests/test_prune_ledger.py` (pytest, temp git repo fixture pinned at a fake base commit) with one test per finding code (`removed_not_in_ledger`, `ledger_text_reappeared`, `over_cap` note vs. finding, `malformed_row`, `ledger_missing`), a pipe-escape/unescape round-trip test, a move-within-a-file-is-not-a-removal test (multiset diff), and a bad-base-commit exit-2 test; write `scripts/tests/test_eval_pruned_base.sh` mirroring `scripts/tests/test_eval_pipeline_baseline.sh`'s fixture shape `[AC-1.2, AC-1.3, AC-1.4, AC-1.5]`
- [ ] 1.2 Write `.writ/decision-records/adr-026-constraint-test-pruning.md` (context citing the assessment §2.1 and §3 Mechanism 1; decision: the three-way test; alternatives: byte target alone, per-model prompt tuning, do nothing; consequences including the negative one) `[AC-1.1]`
- [ ] 1.3 Create `.writ/decision-records/pruned-instructions-ledger.md` with the header block and column format (`| Date | File | Class | Reason | Text |`) and zero data rows, per technical-spec §2 `[AC-1.2]`
- [ ] 1.4 Implement `scripts/prune-ledger.py check` (stdlib, Python 3.9 floor, argparse subcommands, `_fail`/`_refuse` exit-2 pattern mirroring `pipeline-baseline.py`): `git diff --no-color -U0 <base-commit> -- <file>` parsing for removed lines, multiset move-within-file exclusion, ledger row regex and pipe-unescape, the five finding codes, the summary line, exit codes 0/1/2 `[AC-1.2, AC-1.3, AC-1.4]`
- [ ] 1.5 Implement `scripts/prune-ledger.py measure --repo .` printing bytes per `##`/`###` section for both base files `[AC-1.2]`
- [ ] 1.6 Register `check_pruned_base()` in `scripts/eval.sh` next to `check_pipeline_baseline()`, added to the `CHECKS=(...)` array as `pruned-base`; relay findings via `add_finding` and notes via `add_note`; decide `--cap-blocking` by checking for the `<!-- cap: blocking -->` marker line in the ledger file `[AC-1.4, AC-1.5]`
- [ ] 1.7 Verify all acceptance criteria: `uv run --python 3.9 pytest scripts/tests/test_prune_ledger.py` green, `bash scripts/tests/test_eval_pruned_base.sh` green, `bash scripts/eval.sh` shows 0 findings, and append the decision-log line `{date} stage-2: Story 1 — ADR-026, empty ledger, prune-ledger.py check/measure, eval.sh pruned-base check landed` to the story's completion commit `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

## Notes

**Technical considerations.** Line diffs come only from `git diff --no-color -U0 <base-commit> -- <file>`, parsed for hunk lines starting with `-` (not `---`) — never a Python reimplementation of diff. No whitespace normalization anywhere: a kept line that gets reflowed or rewrapped reads as a removal, which is intended (Business Rule 5). Move detection inside a single file is a multiset (Counter) difference of removed-line texts vs. added-line texts for that file only — a line moved between the two base files is a real removal in one and a real addition in the other, not a move. Byte counts use `os.path.getsize` on the working tree, not `git show`.

**Risks.** A reflowed kept line producing a false-positive `removed_not_in_ledger` is the documented, intended failure mode (see Business Rule 5 and the spec's Error Experience) — do not special-case it away. The ledger regex must reject any line starting with `|` that isn't a valid data row, header, or separator (`malformed_row`), so a hand-edited ledger with a typo is caught rather than silently ignored.

**Integration with later stories.** Story 2 and Story 3 are the first real consumers of `check`: every commit that removes a line must add its ledger row in the same commit (Business Rule 4), so `check` must stay green at every commit on the branch, not just at story close. Story 3 is the one that flips the cap to blocking by appending `<!-- cap: blocking -->` to the ledger file — this story's `check_pruned_base()` must already know to look for that marker even though no one sets it yet. Story 4's `verdict-provenance.py` and `eval.sh` registration mirror this story's shape exactly (same finding/note/exit-code conventions), so keeping this implementation clean and conventional pays forward directly. Story 5's `compare` step never touches the ledger; it only needs Stories 1–3's commits to exist.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows** [technical-spec.md → ## 1. `scripts/prune-ledger.py` (Story 1) → Findings table: `removed_not_in_ledger`, `ledger_text_reappeared`, `over_cap`, `malformed_row`, `ledger_missing`] [technical-spec.md → ## 1. → Summary line and Exit codes]
- **Shadow paths** [spec.md → 🎯 Experience Design → Error experience] [technical-spec.md → ## 1. → Removed lines (move-within-file exclusion via multiset difference)]
- **Business rules** [spec.md → 📋 Business Rules → 1 (constraint test is the rule, bytes are the finish line)] [spec.md → 📋 Business Rules → 2 (ledger append-only, re-add is a finding)] [spec.md → 📋 Business Rules → 3 (removed includes moved)] [spec.md → 📋 Business Rules → 4 (ledger rows land in the removal commit)] [spec.md → 📋 Business Rules → 5 (kept lines byte-identical; diff against cf84742)] [spec.md → 📋 Business Rules → 12 (decision-log line)]
- **Experience** [spec.md → 🎯 Experience Design → Happy path, step 1] [spec.md → 🎯 Experience Design → Feedback model] [spec.md → 🎯 Experience Design → State catalog → "Ledger empty (Story 1)"]
- **Requirements** [spec.md → Detailed Requirements → Story 1 — Pruning policy ADR and ledger tooling]
- **Codebase** [technical-spec.md → ## 1. `scripts/prune-ledger.py` (Story 1) → Inputs, command shape] [technical-spec.md → ## 2. Ledger format (Story 1)] [technical-spec.md → ## 7. Tests → `test_prune_ledger.py`, `test_eval_pruned_base.sh`] [scripts/pipeline-baseline.py → argparse subcommand and exit-code shape to mirror] [scripts/eval.sh → `check_pipeline_baseline()` and `CHECKS=(...)` registration shape to mirror] [scripts/tests/test_eval_pipeline_baseline.sh → bash fixture test shape to mirror] [.writ/decision-records/adr-023-stakes-proportional-diligence.md → ADR shape to mirror]
