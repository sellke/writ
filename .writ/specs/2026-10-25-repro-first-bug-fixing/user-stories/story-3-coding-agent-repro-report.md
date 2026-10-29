# Story 3: The Coding Agent's Repro Report

> **Status:** Completed ✅ (2026-10-29)
> **Commit:** 320bbf65a218a71ea73afd9728c7023a5b1ef382
> **Priority:** High
> **Dependencies:** Story 2

## User Story

**As a** orchestrator of `/implement-story` and `/prototype`, and a developer reading the coding agent's report **I want to** find the failing output, the passing output, and the commit order in one `### Repro` block **So that** I can confirm a bug fix proved its own repro before handoff.

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [x] Given `agents/coding-agent.md`, when Implementation Requirements 1 and 3 are read, then Requirement 1 names the `### Bug fixes: repro first` section of `skills/tdd-cycle/SKILL.md`, and Requirement 3 has one sentence that requires a `Ref: .writ/specs/<spec-id>/user-stories/<story-file>.md` footer on the repro and fix commits in `/implement-story` runs and states that `/prototype` commits carry no footer `[AC-3.1]`
- [x] Given the Output Requirements list, when read, then it has a `### Repro` item, and given the Output Format, when its `### Repro` block is read in the bug-with-repro form, then the block holds `Kind`, `Surface`, `Command`, `Commits`, failing output (at most 20 lines), passing output (at most 10 lines), and `Check` fields `[AC-3.2]`
- [x] Given the Output Format `### Repro` block, when its short forms are read, then `Repro: none: <reason>` is followed by a `Regression test` line, `Kind: not a bug fix: <reason>` appears, and `Repro: off` appears `[AC-3.3]`
- [x] Given `python3 scripts/gen-platform-trees.py` has run, when `claude-code/agents/writ-coder.md` and `codex/agents/coding-agent.toml` are read, then each carries the `### Repro` heading, its seven field labels, and its four forms as rendered from `agents/coding-agent.md` (generator rewrites of platform terms allowed), and `python3 scripts/gen-platform-trees.py --check` exits 0 `[AC-3.4]`
- [x] Given the extended `scripts/tests/test_repro_first_wiring.py`, when the full pytest run, the bash test loop, and `bash scripts/eval.sh` run, then every assertion for AC-3.1 through AC-3.4 passes and none of the three runs reports a failure `[AC-3.5]`

## Implementation Tasks

- [x] 3.1 Extend `scripts/tests/test_repro_first_wiring.py` with text checks for Requirements 1 and 3, the Output Requirements `### Repro` item, the four Output Format forms, and the `### Repro` block in `claude-code/agents/writ-coder.md` and `codex/agents/coding-agent.toml`. Run the file and confirm the new checks fail before any edit `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`
- [x] 3.2 Edit Implementation Requirement 1 to name the bug path in `skills/tdd-cycle/SKILL.md`. Edit Requirement 3 with one sentence on the `Ref:` footer for story runs and its absence in prototype runs `[AC-3.1]`
- [x] 3.3 Add `### Repro` to Output Requirements. Add the `### Repro` block to Output Format after `### Self-Check Results` and before `### Boundary Compliance`, in four forms: bug with a repro, bug without a repro, not a bug fix, and switch off. Leave the `exit_criteria` block and `MAX_SELF_FIX_ITERATIONS` unchanged `[AC-3.2, AC-3.3]`
- [x] 3.4 Run `python3 scripts/gen-platform-trees.py`, then `python3 scripts/gen-platform-trees.py --check`. Confirm the block appears in `claude-code/agents/writ-coder.md` and `codex/agents/coding-agent.toml` `[AC-3.4]`
- [x] 3.5 Run `uv run --python 3.9 pytest scripts/tests/test_repro_first_wiring.py` and confirm every AC-3.1 through AC-3.4 assertion passes `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`
- [x] 3.6 Verify the full suite: `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, and `bash scripts/eval.sh` outside any sandbox `[AC-3.5]`

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Notes

- **Revert coverage.** The `Ref:` footer is checked as text here. `scripts/revert-resolve.py` already resolves `Ref:` footers naming the spec folder and story file; no new revert test is planned.
- **Report length.** A full bug block adds up to 30 lines of command output to the coding agent's report, plus the field lines. The 20-line and 10-line caps are the only bound on that output. Keep the caps as written.
- **Stable field labels.** Story 4's consumers read the `Commits` field to find the repro and fix SHAs. Keep the label and the `repro [sha] → fix [sha]` shape exactly as the technical spec gives them. Changing either breaks Story 4's parse.
- **Fence nesting.** The Output Format already sits inside a `markdown` fence. The block's inner `text` fences need a four-backtick outer fence, or the file's fences close early. Check the rendered section after the edit.
- **Generated-tree drift.** Edit only `agents/coding-agent.md`. The Claude Code and Codex copies come from `scripts/gen-platform-trees.py`. A hand edit to either copy fails `--check`.
- **Story 2 dependency.** Requirement 1 names the `### Bug fixes: repro first` heading that Story 2 creates. The wiring test file also comes from Story 2. If Story 2 has not landed, create the file with the same docstring and helper shape before task 3.1.
- **Prototype footer.** `/prototype` commits carry no `Ref:` footer (spec Business Rule 6). Requirement 3 must say so, or a prototype agent will add a footer that points at no story.

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** []
- **Business rules:** `spec.md → ## Business Rules (Expanded)` (Rule 6 story footer, Rule 7 report block, Rule 8 no repro possible, Rule 9 switch-off output)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (rows for not a bug fix, bug without a repro, and switch off)
- **Report block:** `technical-spec.md → ## Report Block (agents/coding-agent.md Output Format)` (the four forms and the Requirement 3 sentence)
- **Removal inventory:** `spec.md → ## Removal Inventory` (the `agents/coding-agent.md` row defines what this story adds and must be deletable)
- **Test scope:** `technical-spec.md → ## Tests → ### scripts/tests/test_repro_first_wiring.py` (Story 3 rows)
- **Story scope:** `spec.md → ## Detailed Requirements → ### Story 3`

## What Was Built

**Implementation Date:** 2026-10-29

### Files Created

[None created]

### Files Modified

- **`agents/coding-agent.md`** (12,787 → 14,185 bytes)
  - Requirement 1: "For a bug fix, follow the `### Bug fixes: repro first` section of `skills/tdd-cycle/SKILL.md`." (no second `Read`).
  - Requirement 3: under `/implement-story`, repro and fix commits each end with `Ref: .writ/specs/<spec-id>/user-stories/<story-file>.md` in the message's last paragraph with any other trailers (and, on the repro commit, its `Repro:` trailer); `/prototype` commits carry no `Ref:` footer.
  - Output Requirements: a `### Repro` item. Output Format (outer fence now four backticks): a `### Repro` block between `### Self-Check Results` and `### Boundary Compliance`, in four forms — bug with a repro (Kind, Surface, Command, `Commits: repro [sha] → fix [sha][, [sha]]`, failing output ≤20 lines, passing output ≤10 lines from the same command, Check), bug without a repro (`Repro: none: [reason]` + `Regression test`), not a bug fix, and switch off (`Repro: off`).
- **`scripts/tests/test_repro_first_wiring.py`** — 9 Story 3 tests (Requirements 1 and 3, the Output Requirements item, fence balance and position, the bug form's labels/order/`Commits` regex/caps, short forms, both generated copies line by line, `gen-platform-trees.py --check`); 19 tests in the module.
- Regenerated: `claude-code/agents/writ-coder.md`, `codex/agents/coding-agent.toml`, `cursor/plugin/agents/coding-agent.md`, `plugins/writ/agents/coding-agent.md`, `plugins/writ/agents/writ-coder.md`.

### Implementation Decisions

1. **Gate 0 divergence** — sketch A (fields per form, one arrow `Commits` line) over B (fixed field set with `n/a`, separate `Repro commit:` / `Fix commits:` lines), which renamed labels AC-3.2/3.4 and Story 4 read. Technical-spec field order kept.
2. **Fence nesting** — the Output Format's outer fence widened to four backticks so the inner `text` fences cannot close it.
3. **Leanness** — the agents surface warning predates this story (now 2132 lines / 88,345 chars against 1841 / 75,345); no baseline edit.

### Test Results

**Verification:** `uv run --python 3.9 pytest scripts/tests/test_repro_first_wiring.py scripts/tests/test_gen_platform_trees.py -q` → 121 passed; full `uv run --python 3.9 pytest -q` → 3500 passed, 3 skipped; bash loop → 51/51 (coding agent and reviewer); `bash scripts/eval.sh` → 0 findings; `gen-platform-trees.py --check` → pass; `check-agent-parity.sh` → pass.
- ✅ test-integrity authenticity: pass
- coverage: no new source files in this story

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small
- **Security:** Clean
- **Boundary Compliance:** `agents/coding-agent.md` (named target, missed by the boundary-map tokenizer) and generator output justified
- **gate3-route:** review-agent (outside_boundary agents/coding-agent.md; outside_boundary cursor/plugin/agents/coding-agent.md; outside_boundary plugins/writ/agents/coding-agent.md; outside_boundary plugins/writ/agents/writ-coder.md)
- **reviewer-filters:** on
- **gate0-divergence:** chose A (fields per form × one arrow Commits line) — B renamed the Commits label and arrow shape that AC-3.2/AC-3.4 and Story 4 read
- **review-panel:** skipped — platform cannot spawn other vendors
- **review-override check:** pass (no blocking helper finding)
- **safety-fact:** tested (claimed tested) — every fence in `agents/coding-agent.md` closes
- **arch-lint:** none — see .writ/docs/architecture-lint.md
- **app-verify:** unverifiable (no_recipe)
- **docs-check:** unverifiable (no public exports in the changed set)

### Deviations from Spec

- **[DEV-008] Requirement 3 sentence is longer than the draft** — Severity: Small — Resolution: Auto-amended
- **[DEV-009] Report block presentation differs; labels, order and `Commits` shape do not** — Severity: Small — Resolution: Auto-amended
