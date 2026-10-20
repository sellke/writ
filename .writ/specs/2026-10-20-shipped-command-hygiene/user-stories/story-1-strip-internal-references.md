# Story 1: Strip Internal References and Add `shipped-refs`

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** developer who installs Writ into a project
**I want to** read shipped commands whose paths all exist in my project or are placeholders for my own files
**So that** no command sends me or my agent to an ADR, archived spec, research document, or calibration record that only exists in Writ's source repo, and an eval check keeps it that way

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [ ] Given a temp root whose `commands/x.md` holds one line of each internal-reference kind (a `../.writ/decision-records/adr-013-….md` link, a `../../decision-records/adr-009-….md` link, a dated `.writ/specs/archive/<date>-<name>/` path, an old `.writ/specs/<date>-<name>/` path whose folder exists under `.writ/specs/archive/`, a dated `.writ/research/<date>-….md` path, and a `calibrated_against:` value naming `.writ/state/phase-execution-20260719-121255.json`), when `python3 scripts/eval-shipped-refs.py --root <tmp>` runs, then it prints one FAIL line per hit naming `commands/x.md:<line>`, the kind, and the token `[AC-1.1]`
- [ ] Given the same root holding only runtime paths (`.writ/state/` in prose, `.writ/state/phase-execution-*.json` on a `calibrated_against:` line, `.writ/specs/<name>/`, `.writ/specs/archive/<name>/`, `.writ/specs/archive/LEDGER.md`, `.writ/research/[DATE]-[topic-name]-research.md`, `.writ/decision-records/adr-*.md`, `.writ/docs/spec-lifecycle.md`, an example ID such as `.writ/specs/2026-03-15-auth-system/spec.md` with no archive folder), when the helper runs, then it prints no FAIL line, and every rule's self-test scenario prints PASS `[AC-1.2]`
- [ ] Given a temp copy of `scripts/eval.sh`, `scripts/eval-shipped-refs.py`, and a clean `commands/` tree, when `bash scripts/eval.sh --check=shipped-refs` runs before and after one ADR link is appended to a command, then it exits 0 before, exits 1 after with a FAIL finding naming that file and line, and exits 0 again once the link is removed; with the helper deleted it exits 2 `[AC-1.3]`
- [ ] Given the real tree after this story, when `bash scripts/eval.sh --check=shipped-refs` runs, then it passes with 0 findings; the contract grep over `commands/*.md` returns only runtime paths and `calibrated_against` values that cite shipped files; and every removed link left no bare `ADR-NNN` label behind `[AC-1.4]`
- [ ] Given the rewritten `calibrated_against` values in `implement-phase.md`, `implement-spec.md`, `implement-story.md` (two units), and `refactor.md`, when `bash scripts/eval.sh --check=loop-bounds` runs, then it passes; each value keeps a shipped path token or `no recorded run`; `refactor.md`'s value still contains `no recorded run`; and no value names `.writ/state/` or `.writ/specs/archive/` except as a glob `[AC-1.5]`

## Implementation Tasks

- [ ] 1.1 Write failing tests in a new `scripts/tests/test_eval_shipped_refs.py`: per-kind positive fixtures and runtime-path negatives against `eval-shipped-refs.py --root <tmp>`, and the eval-level mutation (clean → link added → link removed → helper missing), copying `eval.sh` into a temp `scripts/` the way `scripts/tests/test_product_check_direction.py` does `[AC-1.1, AC-1.2, AC-1.3]`
- [ ] 1.2 Implement `scripts/eval-shipped-refs.py`: the four rules from technical-spec.md → Rules, the scanned-directory constant (`commands` only), `--root`, one self-test scenario per rule, PASS/FAIL TSV; Python 3.9 standard library `[AC-1.1, AC-1.2]`
- [ ] 1.3 Add `check_shipped_refs` to `scripts/eval.sh` (missing-helper run error, FAIL → `add_finding`, PASS → scenario counts) and register `shipped-refs` in `CHECKS` after `referenced-paths` `[AC-1.3]`
- [ ] 1.4 Re-inventory: run the helper and the contract grep on the current tree (expect about 19 lines in about 12 files; `2026-10-20-harness-cuts` may already have removed `retro.md`'s ADR-025 row). Remove each ADR, archived-spec, and research reference with its label, adding the replacement sentences from technical-spec.md → Replacement sentences only where listed `[AC-1.4]`
- [ ] 1.5 Rewrite the five `calibrated_against` values from technical-spec.md → Calibration value rewrites, reading each unit name from the file first `[AC-1.5]`
- [ ] 1.6 Verify the checks: `bash scripts/eval.sh --check=shipped-refs`, `--check=loop-bounds`, `--check=broken-refs`, `--check=referenced-paths` all pass; run the AC-1.3 mutation by hand on a temp copy and see it fail `[AC-1.3, AC-1.4, AC-1.5]`
- [ ] 1.7 Verify the suites: `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, and `bash scripts/eval.sh` (outside the sandbox) with 0 findings `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

## Notes

- **Only links.** Bare `ADR-NNN` labels that were never links stay (spec.md → Grounding Notes). Do not widen the edit.
- **Pinned text nearby.** `check_refresh_evidence` pins "structural only — not an LLM-as-judge" in `refresh-command.md`, next to the research link. Keep that phrase. Run `--check=refresh-evidence` after the edit.
- **`calibrated_against` checks.** `scripts/eval-loop-bounds.py` reads only assertion 4 (path token or `no recorded run`) and the refactor literal from the value. Assertion 8 cross-reads the bound numbers from command prose and agent files, not from the citation.
- **Old-path rule.** The `archived-spec` rule's second form checks `<root>/.writ/specs/archive/<name>/` on disk. Tests must create that folder in the temp root. Example IDs in command docs never match because no such folder exists.
- **`.lean.md`.** The helper skips `*.lean.md` because those never ship. After `2026-10-20-harness-cuts` there are none.
- **Technical spec:** `sub-specs/technical-spec.md` → Current State → Internal references in shipped commands (the per-line table), and → Story 1: Shipped-Refs Check (rules, output, replacement sentences, calibration value rewrites).
- **Product files.** Every `commands/` edit ships to users. Change only the reference lines and their replacement sentences. Check `git diff` before each commit.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Run `shipped-refs`, Strip a link, Rewrite `calibrated_against`, Rewrite refactor's value]
- **Shadow paths:** []
- **Business rules:** [Shipped commands, Internal reference kinds, Runtime paths stay, Removal, `calibrated_against` stays, Runtime]
- **Experience:** [Journey, State Catalog]
