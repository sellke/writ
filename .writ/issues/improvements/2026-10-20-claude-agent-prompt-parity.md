# Claude Code Agent Prompts Lag the Canonical Agents

> **Type:** Improvement
> **Priority:** Normal
> **Effort:** Medium
> **Created:** 2026-10-20
> **spec_ref:** .writ/specs/2026-10-20-claude-agent-generator/spec.md

## TL;DR

The seven Claude Code agent definitions in `claude-code/agents/` are 45 to 79 lines. Their counterparts in `agents/` are 160 to 390 lines. A Claude Code install runs agents that miss constraints the canonical agents carry, and nothing checks the gap.

## Current State

- `claude-code/agents/writ-coder.md` (79 lines) has no boundary-map scope rule and no `MAX_SELF_FIX_ITERATIONS` cap. `agents/coding-agent.md` (287 lines) has both.
- `scripts/check-agent-parity.sh` checks only that each canonical agent has a counterpart file. It does not compare content.
- This repo's `.claude/agents` symlinks to `agents/` (no frontmatter), so dogfooding never runs the Claude-native agents. The gap is invisible in daily use.
- There is no `visual-qa` counterpart in `claude-code/agents/`.
- `claude-code/agents/writ-story-gen.md` sets `isolation: worktree`. A Claude Code subagent worktree branches from the default branch unless `worktree.baseRef: "head"` is set (https://code.claude.com/docs/en/worktrees, "Isolate subagents with worktrees"). The story files it writes land in a worktree cut from main, not on the feature branch. `/create-spec` Step 2.6 spawns general-purpose agents, so today only the adapter's example path is affected.
- Found during the 2026-10-19 pstack comparison (`.writ/research/2026-10-19-writ-vs-pstack-research.md`, finding F6). Excluded from Phase 13's `2026-10-20-claude-code-parity` spec by contract.

## Expected Outcome

- Each Claude Code agent carries the constraints its canonical agent declares: scope law, iteration caps, verdict vocabulary, and the parse contract a gate depends on. Coaching prose can stay out.
- A check fails when a canonical agent gains a constraint its Claude Code counterpart lacks. One way is to generate the Claude Code bodies from `agents/` plus a frontmatter overlay, the same way `gen-codex-agent-tomls.py` generates the Codex files.
- `check-agent-parity.sh` covers content, not only file presence.

## Relevant Files

- `claude-code/agents/*.md` - the Claude Code definitions
- `agents/*.md` - the canonical agents
- `scripts/check-agent-parity.sh` - presence-only parity check
- `scripts/gen-codex-agent-tomls.py` - the existing generate-from-canonical pattern
