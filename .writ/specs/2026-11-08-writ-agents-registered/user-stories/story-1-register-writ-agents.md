# Story 1: Register the writ-* agents in this repo

> **Status:** Completed ✅ (2026-11-08)
> **Commit:** b13110ffe50c101f0f7ef5abd2af004700d09fbf
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** Writ maintainer running `/implement-story` in this repo
**I want to** Claude Code to register the nine `writ-*` agents through `.claude/agents`
**So that** Gate 1 spawns `writ-coder` by name, and a broken registration fails `eval.sh`

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [x] Given the repo checkout, when a pytest reads the `.claude/agents` link, then its target is `../claude-code/agents` and each of the nine `writ-*` names resolves to a frontmatter `name:` in `claude-code/agents/*.md` `[AC-1.1]`
- [x] Given a temp copy of the repo whose `.claude/agents` links to `../claude-code/agents`, when the `claude-agents` check runs, then it reports Findings: 0 `[AC-1.2]`
- [x] Given a temp copy whose `.claude/agents` links to a folder of frontmatter-less copies of `agents/*.md`, when the `claude-agents` check runs, then it reports nine missing-name findings and nine no-frontmatter findings and exits non-zero `[AC-1.3]`
- [x] Given a temp copy with no `.claude/agents`, when the `claude-agents` check runs, then it reports Findings: 0 `[AC-1.4]`
- [x] Given a fresh Claude Code session started in this repo after the repoint, when its agent-type list is read, then it lists the nine `writ-*` types, recorded in a `Verified by:` line under this marker `[AC-1.5]`

> **Verified by:** AC-1.5 — fresh-session run: `claude -p "List every subagent type name available to your Agent/Task tool, one per line, names only, no other text." < /dev/null` (Claude Code 2.1.310), run 2026-11-08 in a fresh headless session in the lane worktree after commit `98bed64` -> listed `writ-architect`, `writ-coder`, `writ-documenter`, `writ-evaluator`, `writ-reviewer`, `writ-story-gen`, `writ-supervisor`, `writ-tester`, `writ-visual-qa` (plus the built-in types).

## Implementation Tasks

- [x] 1.1 Write `scripts/tests/test_claude_agents_registered.py`, one test that reads the `.claude/agents` link with `os.readlink` and asserts the nine `writ-*` names resolve. Cite AC-1.1 in its docstring. Run it on the unmodified repo and confirm it fails `[AC-1.1]`
- [x] 1.2 Add three cases to `scripts/tests/test_eval_claude_agents.sh` in temp copies: a link to `claude-code/agents` passes; a link to frontmatter-less copies fails with eighteen findings; no link passes. Run the failing case before editing `eval.sh` and confirm it fails `[AC-1.2, AC-1.3, AC-1.4]`
- [x] 1.3 Replace `.claude/agents` with a symlink to `../claude-code/agents`: `git rm .claude/agents`, then `ln -s`, then `git add`. The committed entry must be mode 120000 `[AC-1.1]`
- [x] 1.4 In `.writ/docs/self-dogfooding.md`, change the `.claude/agents/` row to `../claude-code/agents/` and add one sentence on frontmatter registration. Leave the `.cursor/agents/` row at `../agents/` `[AC-1.1]`
- [x] 1.5 Extend `check_claude_agents` in `scripts/eval.sh`, after the generator check, to add one finding per missing name, one per frontmatter-less file, and one for a dangling link. Remedy: `ln -sfn ../claude-code/agents .claude/agents` `[AC-1.2, AC-1.3, AC-1.4]`
- [x] 1.6 Run the new pytest on Python 3.9 and 3.14, the bash test file, and `bash scripts/eval.sh --check=claude-agents --report=<scratch path>`. Confirm all pass `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
- [x] 1.7 In a fresh Claude Code session started in this repo, list the agent types. Record the nine `writ-*` names in a `Verified by:` line under the AC marker `[AC-1.5]`

## Notes

- **Session-start read.** Claude Code reads `.claude/agents/` when a session starts. The authoring session cannot list agent types, so AC-1.5 needs a fresh session after the commit.
- **Link creation.** `ln -s` onto an existing symlink to a directory creates the new link inside the target. Run `git rm .claude/agents` first.
- **Generated files.** `claude-code/agents/writ-*.md` are generated from `agents/*.md`. A hand edit made through the link fails `python3 scripts/gen-claude-agents.py --check`.
- **Scope gate.** The new check runs only when both `claude-code/agents/` and `.claude/agents` exist under the project root.
- **Bash 3.2.** `check_claude_agents` must avoid associative arrays and `mapfile`.
- **Python.** The pytest must pass on 3.9 and 3.14. Run it alone. `eval.sh`, bash tests, or writes under `.writ/state/` during a pytest run break `test_smoke_leaves_repo_unchanged`.
- **Integration.** Story 2 edits the adapter, `commands/implement-story.md`, and the supervisor. It does not touch the symlink or `check_claude_agents`.

## Context for Agents

- **Error map rows:** [`.claude/agents` dangling, link points at frontmatter-less files, generated file hand-edited through the link] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [Happy path, Nil input, Empty input] — technical-spec.md → ## Shadow Paths
- **Business rules:** [Business Rule 1, Business Rule 2, Business Rule 5] — spec.md → ## Business Rules (Expanded)
- **Experience:** [State catalog] — spec.md → ## 🎯 Experience Design → ### State catalog

---

## What Was Built

**Implementation Date:** 2026-11-08

### Files Created

1. **`scripts/tests/test_claude_agents_registered.py`** (50 lines)
   - AC-1.1 pytest: `os.readlink(".claude/agents") == "../claude-code/agents"`, the nine `writ-*` names resolve to frontmatter `name:` values through the link, and `.claude/agents/writ-coder.md` resolves to `claude-code/agents/writ-coder.md` with name `writ-coder`.

### Files Modified

- **`.claude/agents`** (symlink, git mode 120000)
  - Target changed from `../agents` to `../claude-code/agents`.
- **`.writ/docs/self-dogfooding.md`** (symlink table)
  - `.claude/agents/` row now reads `../claude-code/agents/`, plus one sentence on frontmatter registration. `.cursor/agents/` unchanged.
- **`scripts/eval.sh`** (`check_claude_agents`, new helper `claude_agent_frontmatter_name`)
  - After the generator check, when `claude-code/agents/` is a directory and `.claude/agents` exists: one finding for a dangling link, one per linked file with no frontmatter `name:`, one per source name not exposed. Remedy `ln -sfn ../claude-code/agents .claude/agents`. Bash 3.2 safe.
- **`scripts/tests/test_eval_claude_agents.sh`** (three new cases)
  - AC-1.2 real link -> Findings 0; AC-1.3 frontmatter-less copies -> 18 findings, non-zero exit; AC-1.4 no link -> Findings 0.

### Implementation Decisions

1. **Link check after the generator check, not gated on it** — generator drift (exit 1) still reaches the link check, so both findings surface in one run; a missing or crashing generator keeps its existing early return.
2. **AC-1.1 test reads `writ-coder.md` through the link** — the Gate 1 recode added a concrete file read so `test-integrity.py authenticity` sees a project file exercised.

### Test Results

**Verification:** pytest on 3.9 and 3.14 (1 passed each); `bash scripts/tests/test_eval_claude_agents.sh` (11 assertions passed, `/bin/bash` 3.2.57); `bash scripts/eval.sh --check=claude-agents` Findings 0; both generator `--check`s pass; fresh-session agent list (AC-1.5).
- ✅ story-gate post-review: pass (9 checks, 0 fail, 2 unverifiable: no_drift_signal, coverage_report_absent)

### Review Outcome

**Result:** PASS

- **Iteration count:** 2 iteration(s) (post-review `test_imports_no_source` on iteration 1, recoded in `98bed64`)
- **Drift:** None
- **Security:** None
- **Boundary Compliance:** no deviations, no violations
- **Agents that ran:** Gate 1 `general-purpose (agents/coding-agent.md)`; Gate 3 `general-purpose (agents/evaluator-agent.md)` — this session started before the repoint, so no `writ-*` type was registered.

### Deviations from Spec

None
