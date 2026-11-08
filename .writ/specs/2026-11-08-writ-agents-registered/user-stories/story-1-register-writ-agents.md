# Story 1: Register the writ-* agents in this repo

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** Writ maintainer running `/implement-story` in this repo
**I want to** Claude Code to register the nine `writ-*` agents through `.claude/agents`
**So that** Gate 1 spawns `writ-coder` by name, and a broken registration fails `eval.sh`

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [ ] Given the repo checkout, when a pytest reads the `.claude/agents` link, then its target is `../claude-code/agents` and each of the nine `writ-*` names resolves to a frontmatter `name:` in `claude-code/agents/*.md` `[AC-1.1]`
- [ ] Given a temp copy of the repo whose `.claude/agents` links to `../claude-code/agents`, when the `claude-agents` check runs, then it reports Findings: 0 `[AC-1.2]`
- [ ] Given a temp copy whose `.claude/agents` links to a folder of frontmatter-less copies of `agents/*.md`, when the `claude-agents` check runs, then it reports nine missing-name findings and nine no-frontmatter findings and exits non-zero `[AC-1.3]`
- [ ] Given a temp copy with no `.claude/agents`, when the `claude-agents` check runs, then it reports Findings: 0 `[AC-1.4]`
- [ ] Given a fresh Claude Code session started in this repo after the repoint, when its agent-type list is read, then it lists the nine `writ-*` types, recorded in a `Verified by:` line under this marker `[AC-1.5]`

## Implementation Tasks

- [ ] 1.1 Write `scripts/tests/test_claude_agents_registered.py`, one test that reads the `.claude/agents` link with `os.readlink` and asserts the nine `writ-*` names resolve. Cite AC-1.1 in its docstring. Run it on the unmodified repo and confirm it fails `[AC-1.1]`
- [ ] 1.2 Add three cases to `scripts/tests/test_eval_claude_agents.sh` in temp copies: a link to `claude-code/agents` passes; a link to frontmatter-less copies fails with eighteen findings; no link passes. Run the failing case before editing `eval.sh` and confirm it fails `[AC-1.2, AC-1.3, AC-1.4]`
- [ ] 1.3 Replace `.claude/agents` with a symlink to `../claude-code/agents`: `git rm .claude/agents`, then `ln -s`, then `git add`. The committed entry must be mode 120000 `[AC-1.1]`
- [ ] 1.4 In `.writ/docs/self-dogfooding.md`, change the `.claude/agents/` row to `../claude-code/agents/` and add one sentence on frontmatter registration. Leave the `.cursor/agents/` row at `../agents/` `[AC-1.1]`
- [ ] 1.5 Extend `check_claude_agents` in `scripts/eval.sh`, after the generator check, to add one finding per missing name, one per frontmatter-less file, and one for a dangling link. Remedy: `ln -sfn ../claude-code/agents .claude/agents` `[AC-1.2, AC-1.3, AC-1.4]`
- [ ] 1.6 Run the new pytest on Python 3.9 and 3.14, the bash test file, and `bash scripts/eval.sh --check=claude-agents --report=<scratch path>`. Confirm all pass `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
- [ ] 1.7 In a fresh Claude Code session started in this repo, list the agent types. Record the nine `writ-*` names in a `Verified by:` line under the AC marker `[AC-1.5]`

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
