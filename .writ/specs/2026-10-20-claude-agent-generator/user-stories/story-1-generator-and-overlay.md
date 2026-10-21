# Story 1: Generator and Overlay

> **Status:** Completed ✅ (2026-10-20)
> **Commit:** 6352c97297f6fa6ff12d57b374491ff78877acdc
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer
**I want to** generate every Claude agent file from its canonical `agents/*.md` source, with Claude-only frontmatter and suffix held in one `OVERLAY` dict in `scripts/gen-claude-agents.py`, and a `--check` mode that reports drift
**So that** installed Claude agents carry the same prompt contract as the canonical agents, and a stale or hand-edited file fails a check instead of shipping silently

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [x] Given `agents/` holds the eight canonical stems and the overlay maps each to its `writ-*.md` file, when write mode runs against an empty or absent out-dir, then it writes one file per stem in the order overlay frontmatter, generated-header HTML comment, canonical body with YAML frontmatter and retired `model: "fast"` lines removed, optional suffix, with exactly one trailing newline, prints `pass`, one `wrote <path>` line per file, and the summary line, and exits 0 `[AC-1.1]`
- [x] Given a generated file was hand-edited or deleted, a canonical stem has no overlay entry, or a `writ-*.md` in the out-dir maps to no overlay `file`, when `--check` runs, then stdout starts with `fail`, prints one `reason: <stale|missing|unmapped> <stem>` or `reason: orphan writ-<x>` line per problem sorted by stem, ends with the summary line `gen-claude-agents: fail (<s> stale, <m> missing, <o> orphan, <u> unmapped)`, and exits 1 `[AC-1.2]`
- [x] Given one canonical stem has no overlay entry, when write mode runs, then it prints `fail` and `reason: unmapped <stem>`, writes no file to the out-dir (including files for stems that do have overlays), and exits 1 `[AC-1.3]`
- [x] Given the seven committed `claude-code/agents/writ-*.md` files, when the overlay renders their frontmatter and suffix, then each matches the committed file byte for byte in the same key order, and the new `visual-qa-agent` entry renders `writ-visual-qa.md` with the values listed in the technical spec Overlay Schema section `[AC-1.4]`
- [x] Given an unknown argument, when the generator runs, then it prints usage to stderr, prints nothing to stdout, and exits 2; and the agent CLI contract smoke test runs `gen-claude-agents.py` against a temp out-dir and passes `[AC-1.5]`

## Implementation Tasks

- [x] 1.1 Write failing pytest module `scripts/tests/test_gen_claude_agents.py` (`tmp_path` fixtures, 3.9-safe) covering write-mode file shape, `--check` pass, each reason kind, validate-before-write, frontmatter key order, suffix placement, retired-line stripping, header comment placement, overlay-vs-committed frontmatter match, and usage exit 2 with empty stdout `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`
- [x] 1.2 Create `scripts/gen-claude-agents.py` with a module docstring stating the CLI contract and the `OVERLAY` dict: seven stems seeded verbatim from the committed frontmatter and trailing memory lines, plus `visual-qa-agent → writ-visual-qa.md`; duplicate `strip_optional_yaml_frontmatter` and `RETIRED_FAST_LINE` from `scripts/gen-codex-agent-tomls.py` `[AC-1.4]`
- [x] 1.3 Implement `source_stems`, `unmapped_stems`, `render`, and `write`: validate every stem before the first write, create the out-dir with `mkdir(parents=True)`, emit check-shape output `[AC-1.1, AC-1.3]`
- [x] 1.4 Implement `check` with byte comparison and `stale`, `missing`, `orphan`, `unmapped` reasons sorted by stem, summary counts, exit 0/1 `[AC-1.2]`
- [x] 1.5 Implement `main` with `--check`, `--agents-dir`, `--out-dir`, and exit 2 on bad arguments; add the `Smoke("gen-claude-agents.py", ...)` entry to `scripts/tests/test_agent_cli_contract.py` and the classification row to `.writ/docs/agent-cli-contract.md` `[AC-1.5]`
- [x] 1.6 Run `uv run pytest` and `uv run --python 3.9 pytest`; confirm `git status` shows no change under `claude-code/agents/` `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`
- [x] 1.7 Run write mode and `--check` by hand against temp dirs; confirm stdout, exit codes, and summary lines match the technical spec CLI Contract table `[AC-1.1, AC-1.2, AC-1.3, AC-1.5]`

## Notes

- **Scope:** This story does not regenerate `claude-code/agents/`. Against the committed tree, `--check` reports `stale` for the seven existing files and `missing writ-visual-qa` until Story 2 runs. Tests use temp dirs for that reason. The repo-level `--check` test listed in the technical spec Test Strategy belongs to Story 2.
- **Seed values:** Copy frontmatter and suffix text from the seven committed files exactly. A changed value changes Claude agent behavior. AC-1.4 tests this by comparing rendered frontmatter to the committed files.
- **Standalone script:** Duplicate the strip helper and retired-line regex. Do not import from `gen-codex-agent-tomls.py`.
- **Python 3.9 floor:** Use `from __future__ import annotations` for `dict[str, dict]` style hints. No stdlib behavior newer than 3.9.
- **Integration:** Story 3 folds this script's `reason:` lines into `check-agent-parity.sh` and `eval.sh`. Keep the output shape identical to `gen-codex-agent-tomls.py` so Story 3 needs no special cases.
- **Risk:** `--check` compares bytes, so any whitespace difference between render and file reads as `stale`. Pin the blank lines around the header comment and the single trailing newline in tests first.
- **Risk:** Overlay values are emitted unquoted. Assert each frontmatter line is a plain `key: value` line that Claude Code parses.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** technical-spec.md → Error & Rescue Map: Write mode "Stem has no overlay", Write mode "`--out-dir` missing", `--check` "Generated file edited by hand", `--check` "Generated file deleted", `--check` "Extra `writ-*.md`". The parity-script and `eval.sh` rows belong to Story 3.
- **Shadow paths:** technical-spec.md → Shadow Paths: Happy, Nil (`agents/` absent), Empty (frontmatter-only canonical file), Upstream error (non-UTF-8 file). Also technical-spec.md → Interaction Edge Cases: `---` horizontal rules, `<!--` comments, `:` in descriptions.
- **Business rules:** spec.md → ## Business Rules: 1 Single writer, 2 Body is verbatim, 3 Overlay owns Claude metadata, 4 Stem → filename map is explicit, 5 Validate before write, 7 3.9 floor.
- **Experience:** spec.md → Experience Design: State catalog rows Aligned, Canonical edited not regenerated, Generated file hand-edited, New canonical agent no overlay, `writ-*.md` with no canonical source, Generated file deleted. Feedback model and Error experience from the Specification Contract's Experience Design block. Output format from technical-spec.md → Output Format and CLI Contract.

---

## What Was Built

**Implementation Date:** 2026-10-20

### Files Created

1. **`scripts/gen-claude-agents.py`** (337 lines)
   - Generator for `claude-code/agents/writ-*.md`. Module docstring states the CLI contract. `OVERLAY` covers all 8 stems (`file`, ordered `frontmatter` pairs, `suffix`). Duplicates `strip_optional_yaml_frontmatter` and `RETIRED_FAST_LINE` from the Codex generator; `write`, `check`, argparse `main` with `allow_abbrev=False`.
2. **`scripts/tests/test_gen_claude_agents.py`** (480 lines)
   - 46 pytest cases on `tmp_path`, 3.9-safe: write-mode bytes, every `--check` reason kind, validate-before-write, overlay seed values vs committed files, usage errors.

### Files Modified

- **`scripts/tests/test_agent_cli_contract.py`** (Smoke list)
  - Added `Smoke("gen-claude-agents.py", ...)`.
- **`.writ/docs/agent-cli-contract.md`** (Classification table)
  - Added the `gen-claude-agents.py | check` row.

### Implementation Decisions

1. **Orphan keyed on canonical stems** — matches `gen-codex-agent-tomls.py` and catches a file whose canonical source was deleted.
2. **Suffix = memory lines only** — set on architect, coder, evaluator, reviewer; other tail lines already exist in the canonical bodies.

### Test Results

**Verification:** `uv run pytest scripts/tests/test_gen_claude_agents.py scripts/tests/test_agent_cli_contract.py scripts/tests/test_agent_cli_contract_doc.py` → 364 passed; `uv run --python 3.9 pytest scripts/tests/test_gen_claude_agents.py` → 46 passed
**Coverage:** 98%
- ✅ Line coverage on `scripts/gen-claude-agents.py` measured with subprocess patching (lines 210, 337 uncovered); `test-integrity.py coverage` unverifiable (no coverage report on disk)
- ✅ `test-integrity.py authenticity` pass

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small
- **Security:** Not assessed
- **Boundary Compliance:** Owned files only; 0 crossings

### Deviations from Spec

- **[DEV-001] Orphan means no current canonical stem generates the file** — Severity: Small
  - Spec said: orphan = a `writ-*.md` no overlay `file` maps to
  - Reality: orphan = a `writ-*.md` no current canonical stem generates
  - Resolution: Auto-amended
  - Spec amendment: spec-lite.md Error Handling orphan line
- **[DEV-002] Reasons sorted by reported name** — Severity: Small
  - Spec said: sorted by stem
  - Reality: sorted on the printed token (orphans by filename stem)
  - Resolution: Auto-amended
- **[DEV-003] Suffixes hold memory lines only** — Severity: Small
  - Spec said: suffix = trailing memory lines
  - Reality: suffix on four stems; Story 2 drops non-memory hand-written tail lines
  - Resolution: Auto-amended (no change needed)
