# Transcript-driven retro that fixes the agent environment

> **Type:** Feature
> **Priority:** Normal
> **Effort:** Large
> **Created:** 2026-10-12
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

Augment or replace `/retro` so it reads agent session transcripts after every story, spec, or phase and proposes ranked fixes to the agent's environment (steering files, navigation rules, lint rules, skills, docs) instead of the code.

## Current State

- `/retro` measures git history only: commits, net lines, streaks, Ship of the Week. It sees outcomes, not how the agent got there.
- `/refresh-command` reads transcripts, but only to amend one Writ command file, and only when the user starts it and describes the friction.
- Struggle that the agent patched over silently leaves no trace in git: slow file navigation, reliance on stale docs, dead ends, repeated mistakes, duplicated work, wasted tokens.
- Nothing runs automatically at the end of `/implement-story`, `/implement-spec`, or `/implement-phase` to capture these lessons.

## Expected Outcome

- Reads transcripts from completed or in-progress sessions (main agent and subagents) scoped to a story, spec, or phase.
- Detects inefficiency signals, for example:
  - Many search/read calls before reaching the right file
  - Actions based on outdated docs or instructions, later corrected
  - Dead ends: abandoned approaches, reverted edits
  - The same mistake made and fixed more than once
  - Duplicated work across agents or stories
  - Token-heavy stretches with little output
- Proposes concrete environment changes, most severe first: `CLAUDE.md`/steering edits, navigation hints, lint or architecture rules, skill and doc cleanup, command amendments.
- Never edits source code. The user approves each change before it is applied.
- Works in the Writ repo (improves Writ itself) and in any project with Writ installed (improves that project's setup).
- Keeps `/refresh-command`'s privacy rules: cite transcript IDs/paths and short observable signals; never copy transcript bodies or chain-of-thought into the repo.

## Relevant Files

- `commands/retro.md` - existing git-only retro to augment or replace
- `commands/refresh-command.md` - existing transcript-reading and evidence-citation rules to reuse
- `scripts/eval-refresh-evidence.py` - evidence validator a new command could share

## Notes

- Open decision: extend `/retro` with a transcript mode, fold this into `/refresh-command`, or ship a new command. Overlap with `/refresh-command` is large; avoid two transcript readers.
- Transcript locations differ per platform (Cursor `agent-transcripts/`, Claude Code `~/.claude/projects/`, Codex). Needs an adapter per platform.
- Decide whether it runs automatically at the end of implement-* commands or only on demand.
- Large transcripts need sampling or summarization to keep the analysis itself cheap.

## Resolution

2026-10-12 — `commands/retro.md` rewritten as a transcript review that proposes ranked environment fixes (replace option chosen). ADR-025 amended to allow cited transcript findings. Logged in `.writ/refresh-log.md`. Uncommitted on `main` at time of writing.
