# Story 3: Sub-Agent Worktree Integration

> **Status:** Completed ✅ (2026-08-12)
> **Priority:** High
> **Dependencies:** Story 2

## User Story

**As an** orchestrator whose spawned gate agent ran in an isolated git
worktree
**I want** a documented, repeatable procedure for reconciling that worktree's
output with my own checkout
**So that** I stop improvising the diff → copy → re-verify → cleanup dance
fresh for every gate, every story

## Acceptance Criteria

- [x] Given `skills/subagent-worktree-integration/SKILL.md`, when it is read, then it states — as a **capability**, not a workflow (ADR-009) — how to recognize a spawned agent ran in an isolated worktree, how to diff that worktree against the orchestrator's own checkout scoped to the story's owned files, how to copy the changed/created files into the main checkout, what re-verification to run there before trusting the merge (lint/typecheck at minimum; the project's test suite when the story includes one), and how to remove the worktree afterward.
- [x] Given a spawned agent's worktree is behind the orchestrator's checkout (missing commits from earlier stories in the same spec), when the skill is read, then it names this as a recognizable failure mode with a stated resolution (the agent may need a fast-forward merge of the orchestrator's current state, or the orchestrator re-reads the agent's output against the correct baseline) rather than leaving it as a silent surprise.
- [x] Given `bash scripts/lint-skill.sh skills/subagent-worktree-integration/SKILL.md`, when it runs, then it exits clean.
- [x] Given `commands/implement-story.md`, when the skill is wired in, then it is referenced from the same cross-cutting location Story 2 established (the "### Step 3: Run Pipeline" intro blockquote notes), following the file's existing skill-reference phrasing convention exactly.
- [x] Given `bash scripts/eval.sh`, when it runs, then the suite stays green and `commands/implement-story.md`'s required-sections presence, its `_preamble.md` reference, and its frontmatter are all intact.

## Implementation Tasks

- [x] 3.1 Read `commands/implement-story.md` as it stands after Story 2 lands (confirm the exact location and wording of the blockquote note Story 2 added, to append alongside it rather than duplicating structure)
- [x] 3.2 Author `skills/subagent-worktree-integration/SKILL.md` following the same format convention as Story 2's skill (frontmatter + Purpose / When to Use / How to Apply)
- [x] 3.3 Document the recognition signal (a spawned agent's tool result names a worktree path/branch), the diff-scope-copy-reverify-cleanup procedure, and the stale-worktree-behind-main failure mode with its resolution
- [x] 3.4 Run `bash scripts/lint-skill.sh skills/subagent-worktree-integration/SKILL.md` and fix any boundary violation
- [x] 3.5 Add one more blockquote note to `commands/implement-story.md`'s "### Step 3: Run Pipeline" intro, alongside Story 2's, referencing this skill
- [x] 3.6 Run `bash scripts/eval.sh` before and after; confirm `commands/implement-story.md`'s frontmatter, required sections, and `_preamble.md` reference are unchanged

## Notes

**Technical considerations:** This story depends on Story 2 purely for file
sequencing — both add a blockquote note to the same Step 3 intro block in
`commands/implement-story.md`, and running them in sequence avoids a
concurrent-edit conflict on adjacent lines. There is no conceptual dependency
between the two skills' content.

**Evidence for this story:** every gate agent spawned during the
`2026-08-12-machine-evaluable-exit-criteria` run — including nominally
read-only architecture-check and review agents — reported running inside its
own isolated git worktree. The orchestrator had to manually diff each
worktree, copy files into the main checkout, re-run tests/`eval.sh` there,
and remove the worktree — invented fresh each time, for all 6 stories.

**Risks:** Keep the skill capability-shaped per ADR-009 — *what the
integration procedure is and when each step applies*, not a restated
walkthrough of any one specific run. If it reads as a narrative of "what I did
in story X," it will fail `scripts/lint-skill.sh`.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Code reviewed

---

## What Was Built

**Implementation Date:** 2026-08-12

### Files Created

1. **`skills/subagent-worktree-integration/SKILL.md`**
   - Capability skill (ADR-009-conformant, `status: candidate`) documenting
     how to recognize an isolated-worktree result, diff it scoped to the
     story's owned files, copy changed/created files into the orchestrator's
     checkout, re-verify (lint/typecheck mandatory, test suite when the
     story has one), remove the worktree afterward, and recognize/resolve
     the stale-worktree-behind-main failure mode (fast-forward the worktree,
     or re-read the agent's output against its correct baseline)

### Files Modified

1. **`commands/implement-story.md`**
   - Added a "Sub-agent worktree integration" blockquote note to the
     "### Step 3: Run Pipeline" intro, immediately after Story 2's
     "Sub-agent completeness" note, using the same exact phrasing
     convention (`Read skills/.../SKILL.md` for *how* ...; ownership-split
     clause)

### Test Results

**Verification:** N/A — documentation-only deliverable, no executable code
touched. `bash scripts/lint-skill.sh skills/subagent-worktree-integration/SKILL.md`
exits clean. `bash scripts/eval.sh` (full suite) ran clean: Findings 0, Run
errors 0. `git diff commands/implement-story.md` confirmed a single additive
prose-body hunk — frontmatter, `_preamble.md` reference, and required
sections untouched.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration — the phrasing-convention gap found on
  Story 2's first draft was already corrected before this story's blockquote
  was authored, so Story 3's note matched the convention exactly on first
  review
- **Drift:** None
- **Security:** Clean (docs-only change)

### Deviations from Spec

None.
