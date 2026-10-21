# Story 3: Correct the Claude Code Adapter

> **Status:** Completed ✅
> **Commit:** 4cebc62b051be6a861ed0c6e6521416f2944709b
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** developer or agent reading `adapters/claude-code.md` to run Writ on Claude Code
**I want to** see only commands, flags, hook events, agents, and worktree behavior that exist, and install steps that leave my `CLAUDE.md` alone
**So that** I do not try `/implement-story --all`, and I reconcile isolated worktrees instead of assuming their changes come back on their own

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [x] Given `adapters/claude-code.md`, when the test searches it, then it contains no `--all`, no `Agent Teams` heading or section, no case-insensitive `agent teams` (the intro line and Gotcha 2 included), and none of the merge-back claims `Merges changes back`, `changes merge back`, or `merge back automatically` `[AC-3.1]`
- [x] Given the adapter's `### Git Worktree Isolation` section and its `create-spec: Parallel Story Generation` example, when read, then they state that a subagent worktree branches from the repository's default branch unless `worktree.baseRef` is `"head"`, is removed when the agent made no changes, and otherwise stays on disk holding the changes; that the orchestrator reconciles those changes by following the worktree skill (diff, copy, re-verify, remove); and they link `../skills/subagent-worktree-integration/SKILL.md` `[AC-3.2]`
- [x] Given the adapter's parallel-story text and its Gotchas list, when read, then parallel stories are attributed to `/implement-spec` parallel batches, and the "Worktree merges can conflict" gotcha is replaced by one stating that copying a stale worktree's files back can overwrite newer work, with a pointer to the skill's stale-worktree step `[AC-3.3]`
- [x] Given the adapter's Installation section, when read, then the automated-install text and manual Step 1 include copying `system-instructions.md` to `.claude/system-instructions.md`; manual Step 1 appends the template between `<!-- writ:start -->` and `<!-- writ:end -->` and no line copies `claude-code/CLAUDE.md` onto `./CLAUDE.md`; the Final Structure tree lists `.claude/system-instructions.md`; and one sentence says `CLAUDE.md` imports it with `@.claude/system-instructions.md` and that Claude Code asks once to approve an import that resolves outside the working directory `[AC-3.4]`
- [x] Given the adapter, when the test searches it, then it contains no `SubagentCompleted` and no `$WORKTREE`; the hook example uses `SubagentStop` with matcher `^writ-coder$`, reads `cwd` from the hook input, and cites `https://code.claude.com/docs/en/hooks`; the `/goal` section points at the `SubagentStop` example; and every frontmatter `name` in `claude-code/agents/*.md` (seven today, `writ-evaluator` included) appears in the Model Selection tier table, the Permission Modes table, and the Final Structure tree, with no "six Claude-native" or "seventh" wording left `[AC-3.5]`

## Implementation Tasks

- [x] 3.1 Write failing tests in a new `scripts/tests/test_claude_code_adapter_claims.py` (unittest, reads the adapter as text): absence checks for AC-3.1, matching `--all` as a whole flag (regex `--all\b`) so a later `--allowedTools` does not trip it; presence of `worktree.baseRef`, the skill link, and `/implement-spec` parallel batches in the relevant sections for AC-3.2 and AC-3.3; presence of `.claude/system-instructions.md`, the markers, and the import line inside `## Installation`, and absence of the regex `cp\s+\S*claude-code/CLAUDE\.md\s+\./CLAUDE\.md`, for AC-3.4; absence of `SubagentCompleted` and `$WORKTREE`, presence of `SubagentStop`, and the agent names read from `claude-code/agents/*.md` frontmatter (not a hard-coded list) in each of the three places, for AC-3.5 `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`
- [x] 3.2 Remove the `/implement-story --all` paragraph under `### Git Worktree Isolation`, the whole `### implement-story --all: Agent Teams (Experimental)` section, "agent teams" from the intro line, and Gotcha 2; renumber the Gotchas `[AC-3.1]`
- [x] 3.3 Rewrite the four worktree steps and the `create-spec` example's closing comments per `sub-specs/technical-spec.md` → Adapter Corrections, citing `https://code.claude.com/docs/en/worktrees` and linking the skill `[AC-3.2]`
- [x] 3.4 Add the one-line `/implement-spec` parallel-batch replacement and rewrite Gotcha 1 around the stale-worktree risk `[AC-3.3]`
- [x] 3.5 Update the Installation section: automated-install sentence, manual Step 1 (newline guard, append between markers, `system-instructions.md` copy, per technical-spec.md → Adapter Corrections), Final Structure tree entry, and the import sentence `[AC-3.4]`
- [x] 3.6 Replace the `### Quality Gates with Hooks` example with the `SubagentStop` example and its stated facts, change the `/goal` section's pointer, and add `writ-evaluator` to the Model Selection intro and tier table (`anchor`, `inherit`), the Permission Modes table (`plan`), and the Final Structure tree `[AC-3.5]`
- [x] 3.7 Verify: `uv run --python 3.9 pytest` (including `test_goal_emit_gold.py`, `test_governor_enforcement.py`, `test_review_panel.py`, which read this adapter), then `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, then `bash scripts/eval.sh` outside the sandbox with 0 findings (its `recommendation-semantics`, `phase-lanes`, `phase-quarantine`, `review-panel`, and `broken-refs` checks pin text in this file) `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`

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

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Claude Code session, Reinstall merges block]
- **Shadow paths:** []
- **Business rules:** [Adapter claims, Import line, No copy over `CLAUDE.md`]
- **Experience:** [Who uses it]

## What Was Built

**Implementation Date:** 2026-10-21

### Files Created

- **`scripts/tests/test_claude_code_adapter_claims.py`** — 34 unittest cases that read the adapter as text. Agent names, `model`, `permissionMode`, and `isolation` come from `claude-code/agents/*.md` frontmatter; skill step numbers come from the skill's headings. Covers AC-3.1 to AC-3.5.

### Files Modified

- **`adapters/claude-code.md`**:
  - Intro no longer mentions agent teams. The `/implement-story --all` paragraph, the Agent Teams section, and the agent-teams gotcha are gone; Gotchas renumbered 1–5.
  - Worktree steps: a subagent worktree branches from the default branch unless `worktree.baseRef` is `"head"`, is removed when there are no changes, and otherwise stays on disk until a sweep; the orchestrator reconciles per `skills/subagent-worktree-integration/SKILL.md`. Cites the worktrees docs. Parallel stories are `/implement-spec` batches. The `create-spec` example says each story file stays in its worktree until copied back.
  - Gotcha 1 is the stale-worktree risk with both causes and a link to skill step 6.
  - Installation: the automated text names `.claude/system-instructions.md` and the markers; manual Step 1 appends the template between `<!-- writ:start -->` and `<!-- writ:end -->` and copies `system-instructions.md`, with no copy over `CLAUDE.md`; the prose explains the missing manifest baseline and what `--force` overwrites; one sentence on the `@.claude/system-instructions.md` import and the external-import approval; the tree lists `.claude/system-instructions.md`.
  - Hooks: a `SubagentStop` example (matcher `^writ-coder$`, a script that reads `cwd` from the input JSON and exits 2), the documented facts, and the hooks docs link. The `/goal` section points at the `SubagentStop` example.

### Implementation Decisions

1. **No `visual-qa` sentence.** `writ-visual-qa` exists now (spec `2026-10-20-claude-agent-generator`), so the technical spec's "There is no `visual-qa` equivalent here yet" was not reintroduced. The agent tables already named all eight agents.
2. **The adapter does not claim `cwd` is the subagent's worktree** (D6). The orchestrator re-runs checks in its own checkout after reconciling.

### Test Results

**Verification:** test-first, then full suites.

- Red: 24 failed, 7 passed on the unmodified adapter (the 7 cover what the agent-generator spec already fixed); iteration 2 red 3 failed / 30 passed; iteration 3 red 1 failed / 33 passed.
- Green: 34 passed.
- Mutations (reviewer, scratch copies): 10 mutants in iteration 1 (7 killed; the three survivors led to the iteration-2 regex and prose tests); iteration 2 and 3 mutants of the regex, Gotcha 1, the Step 1 baseline sentence, and the `--force` sentence each fail a test.
- Orchestrator run: the new test plus `test_goal_emit_gold.py`, `test_governor_enforcement.py`, `test_review_panel.py`, `test_gen_claude_agents.py` → 281 passed (iteration 2); `check-agent-parity.sh` → exit 0; eval `recommendation-semantics`, `phase-lanes`, `phase-quarantine`, `review-panel`, `broken-refs`, `claude-agents` → Findings 0 each.
- Full suites (orchestrator, after iteration 3): pytest 3.9 → 2672 passed, 2 skipped; bash loop → 41 run, 0 failed.

### Review Outcome

**Result:** PASS

- **Iteration count:** 3 iteration(s)
- **Drift:** Small (DEV-005 to DEV-008)
- **Security:** Clean
- **Boundary Compliance:** only `adapters/claude-code.md` and the new test changed. Gate 0.5's map did not list the adapter (the derivation missed it), so Gate 2.5 reported `outside_boundary adapters/claude-code.md`; the reviewer judged it owned per the story.
- gate3-route: review-agent (outside_boundary adapters/claude-code.md). review-panel: skipped — platform cannot spawn other vendors. arch-lint: none — see .writ/docs/architecture-lint.md.
- Gate 0 arch-check: pass (rederived proceed). Gate 2: `py_compile` clean; no linter configured. Gate 3 iteration 1: PASS with three Minor issues (Gotcha 1 cause, the `--force` sentence for manual installs, the regex gap), sent back. Iteration 2: PASS with one Minor issue (`--force` scope), sent back. Iteration 3: PASS, no issues. Gate 3.5 drift-format: pass. Gate 3 review-override and Gate 4 authenticity: `test_imports_no_source` on the new test. The test reads a markdown deliverable as text, so it imports no code; other doc-text tests (`test_ci_workflow.py`, `test_issue_closure_wiring.py`) get the same finding. Carried on the red-phase and mutation evidence above, not DEGRADED. Gate 4 coverage: unverifiable (no report). Gate 4.5: app-verify unverifiable (no recipe). Gate 5: docs-check unverifiable (no public exports).
- Reviewer notes outside scope: `scripts/measure-invocation.py` and `scripts/tests/test_measure_invocation.py` cite `adapters/claude-code.md:396`, which was stale before this story; the adapter's "Files you have customized are never overwritten" line ignores `--force`.

### Deviations from Spec

- **[DEV-005] Manual Step 1 prose corrects the technical spec's claim** — Severity: Small. Resolution: Auto-amended (spec-lite S3 line).
- **[DEV-006] Gotcha 1 names both causes of a stale worktree** — Severity: Small. Resolution: Auto-amended.
- **[DEV-007] The parallel-stories line has an extra clause** — Severity: Small. Resolution: Auto-amended.
- **[DEV-008] Adapter test checks more than task 3.1 lists** — Severity: Small. Resolution: Auto-amended.
