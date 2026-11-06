# Writ's Own Claude Code Install Registers No `writ-*` Agent Types, So Gate 1 Is Skipped

> **Type:** Bug
> **Priority:** Medium
> **Effort:** Small
> **Created:** 2026-11-06
> **spec_ref:** _(set automatically when promoted via /create-spec --from-issue)_

## TL;DR

In this repo `.claude/agents` links to `agents/`, whose files have no frontmatter, so Claude Code registers none of `writ-coder`, `writ-reviewer`, `writ-supervisor` and the rest. Both Phase 16 lanes (2026-11-06) found no coding-agent type and wrote the code themselves. Every story disclosed it, and the phase supervisor escalated lane B for it. The maintainer waived Gate 1 for Phase 16. `/implement-story` names no fallback for this case.

## Current State

- `.claude/agents -> ../agents`. Installs into other projects copy `claude-code/agents/` (`scripts/install.sh`, `AGENTS_SRC="claude-code/agents"`), which carries the frontmatter, so only the Writ repo is affected.
- `commands/implement-story.md` Gate 1 requires a `coding-agent` spawn. The gate table lists Gate 1 as skippable only under `--review-only`. Nothing says what to do when the type is not registered.
- Phase 16 lanes A and B: every story's What Was Built reads "No coding subagent". The lane A supervisor accepted. The lane B supervisor escalated on this alone, and the orchestrator accepted after the waiver (doubt-log id `6074602c0d4c`).

## Expected Outcome

- Writ's own Claude Code install registers the `writ-*` agents, so `/implement-story` can spawn `writ-coder` in this repo. For example, point `.claude/agents` at `claude-code/agents/`. Check this against CLAUDE.md's symlink rule and against what `gen-platform-trees.py --check` expects.
- `/implement-story` Gate 1 states the fallback when no coding-agent type exists: spawn a general-purpose agent briefed from the coder definition. Inline coding, if allowed at all, is disclosed and makes the supervisor escalate.
- A test or eval check fails when the repo's `.claude/agents` exposes no agent with frontmatter.

## Relevant Files

- `.claude/agents` (symlink)
- `claude-code/agents/writ-coder.md`
- `commands/implement-story.md`: Gate 1
- `agents/supervisor-agent.md`
- `CLAUDE.md`: Repository Structure
