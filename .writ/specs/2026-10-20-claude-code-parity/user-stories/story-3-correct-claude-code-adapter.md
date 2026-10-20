# Story 3: Correct the Claude Code Adapter

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** developer or agent reading `adapters/claude-code.md` to run Writ on Claude Code
**I want to** see only commands, flags, hook events, agents, and worktree behavior that exist, and install steps that leave my `CLAUDE.md` alone
**So that** I do not try `/implement-story --all`, and I reconcile isolated worktrees instead of assuming their changes come back on their own

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [ ] Given `adapters/claude-code.md`, when the test searches it, then it contains no `--all`, no `Agent Teams` heading or section, no case-insensitive `agent teams` (the intro line and Gotcha 2 included), and none of the merge-back claims `Merges changes back`, `changes merge back`, or `merge back automatically` `[AC-3.1]`
- [ ] Given the adapter's `### Git Worktree Isolation` section and its `create-spec: Parallel Story Generation` example, when read, then they state that a subagent worktree branches from the repository's default branch unless `worktree.baseRef` is `"head"`, is removed when the agent made no changes, and otherwise stays on disk holding the changes; that the orchestrator reconciles those changes by following the worktree skill (diff, copy, re-verify, remove); and they link `../skills/subagent-worktree-integration/SKILL.md` `[AC-3.2]`
- [ ] Given the adapter's parallel-story text and its Gotchas list, when read, then parallel stories are attributed to `/implement-spec` parallel batches, and the "Worktree merges can conflict" gotcha is replaced by one stating that copying a stale worktree's files back can overwrite newer work, with a pointer to the skill's stale-worktree step `[AC-3.3]`
- [ ] Given the adapter's Installation section, when read, then the automated-install text and manual Step 1 include copying `system-instructions.md` to `.claude/system-instructions.md`; manual Step 1 appends the template between `<!-- writ:start -->` and `<!-- writ:end -->` and no line copies `claude-code/CLAUDE.md` onto `./CLAUDE.md`; the Final Structure tree lists `.claude/system-instructions.md`; and one sentence says `CLAUDE.md` imports it with `@.claude/system-instructions.md` and that Claude Code asks once to approve an import that resolves outside the working directory `[AC-3.4]`
- [ ] Given the adapter, when the test searches it, then it contains no `SubagentCompleted` and no `$WORKTREE`; the hook example uses `SubagentStop` with matcher `^writ-coder$`, reads `cwd` from the hook input, and cites `https://code.claude.com/docs/en/hooks`; the `/goal` section points at the `SubagentStop` example; and every frontmatter `name` in `claude-code/agents/*.md` (seven today, `writ-evaluator` included) appears in the Model Selection tier table, the Permission Modes table, and the Final Structure tree, with no "six Claude-native" or "seventh" wording left `[AC-3.5]`

## Implementation Tasks

- [ ] 3.1 Write failing tests in a new `scripts/tests/test_claude_code_adapter_claims.py` (unittest, reads the adapter as text): absence checks for AC-3.1, matching `--all` as a whole flag (regex `--all\b`) so a later `--allowedTools` does not trip it; presence of `worktree.baseRef`, the skill link, and `/implement-spec` parallel batches in the relevant sections for AC-3.2 and AC-3.3; presence of `.claude/system-instructions.md`, the markers, and the import line inside `## Installation`, and absence of the regex `cp\s+\S*claude-code/CLAUDE\.md\s+\./CLAUDE\.md`, for AC-3.4; absence of `SubagentCompleted` and `$WORKTREE`, presence of `SubagentStop`, and the agent names read from `claude-code/agents/*.md` frontmatter (not a hard-coded list) in each of the three places, for AC-3.5 `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`
- [ ] 3.2 Remove the `/implement-story --all` paragraph under `### Git Worktree Isolation`, the whole `### implement-story --all: Agent Teams (Experimental)` section, "agent teams" from the intro line, and Gotcha 2; renumber the Gotchas `[AC-3.1]`
- [ ] 3.3 Rewrite the four worktree steps and the `create-spec` example's closing comments per `sub-specs/technical-spec.md` → Adapter Corrections, citing `https://code.claude.com/docs/en/worktrees` and linking the skill `[AC-3.2]`
- [ ] 3.4 Add the one-line `/implement-spec` parallel-batch replacement and rewrite Gotcha 1 around the stale-worktree risk `[AC-3.3]`
- [ ] 3.5 Update the Installation section: automated-install sentence, manual Step 1 (newline guard, append between markers, `system-instructions.md` copy, per technical-spec.md → Adapter Corrections), Final Structure tree entry, and the import sentence `[AC-3.4]`
- [ ] 3.6 Replace the `### Quality Gates with Hooks` example with the `SubagentStop` example and its stated facts, change the `/goal` section's pointer, and add `writ-evaluator` to the Model Selection intro and tier table (`anchor`, `inherit`), the Permission Modes table (`plan`), and the Final Structure tree `[AC-3.5]`
- [ ] 3.7 Verify: `uv run --python 3.9 pytest` (including `test_goal_emit_gold.py`, `test_governor_enforcement.py`, `test_review_panel.py`, which read this adapter), then `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, then `bash scripts/eval.sh` outside the sandbox with 0 findings (its `recommendation-semantics`, `phase-lanes`, `phase-quarantine`, `review-panel`, and `broken-refs` checks pin text in this file) `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`

## Notes

- **Never run `install.sh` or `update.sh` against the Writ repo.** This story only edits a doc and adds a test, but if you want to see the installed tree, install into a temp directory.
- **Pinned text stays.** technical-spec.md → Adapter Corrections lists the literals that eval and pytest require. Edit around them.
- **Worktree facts come from the docs, not memory.** Subagent worktrees use the same base as `--worktree` (default branch, or `HEAD` with `worktree.baseRef: "head"`); a worktree with changes stays until a periodic sweep can remove it without losing work. Source: `https://code.claude.com/docs/en/worktrees` § Isolate subagents with worktrees (fetched 2026-10-20).
- **The subdirectory approval is an inference.** The memory docs define an external import as one that resolves outside the working directory. Word the sentence as a condition, not a promise about subdirectories.
- **Independence.** Story 3 touches only `adapters/claude-code.md` and its new test. It can run in parallel with Story 1. The Installation text describes Story 2's behavior; both land in this spec before release.
- **Added by the 2026-10-20 amendment:** the hook example, the seven agents, and manual Step 1's merge (AC-3.4, AC-3.5). Hook facts come from `https://code.claude.com/docs/en/hooks` (fetched 2026-10-20): 33 events, no `SubagentCompleted`; the `SubagentStop` matcher is the agent type (the frontmatter `name` for a custom subagent); exit 2 keeps the subagent running and gives it the stderr text; `cwd` arrives in the input JSON; no `$WORKTREE` is documented. Do not claim `cwd` is the subagent's worktree; the docs do not say so (spec.md → D6).
- **Still out of scope:** the `writ-story-gen` worktree base, and prompt bodies of `claude-code/agents/*.md` (`.writ/issues/improvements/2026-10-20-claude-agent-prompt-parity.md`).
- **Read first.** technical-spec.md → Adapter Corrections (Story 3) (the change table and the pinned-text list) and Import Line; `skills/subagent-worktree-integration/SKILL.md` steps 1–6, which the adapter text must agree with.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Claude Code session, Reinstall merges block]
- **Shadow paths:** []
- **Business rules:** [Adapter claims, Import line, No copy over `CLAUDE.md`]
- **Experience:** [Who uses it]
