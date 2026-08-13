# Story 2: Sub-Agent Result Completeness

> **Status:** Completed ✅ (2026-08-12)
> **Commit:** c154903cce85b9013ef712d02236594745530545
> **Priority:** High
> **Dependencies:** None

## User Story

**As an** orchestrator running `/implement-story`'s gates
**I want** a documented way to tell a spawned agent's complete verdict from a
mid-task stop, and a named recovery step when it stops early
**So that** I stop manually judging "is this done?" turn by turn and resuming
agents ad hoc — the single largest source of orchestration overhead in the
prior run

## Acceptance Criteria

- [x] Given `skills/subagent-result-completeness/SKILL.md`, when it is read, then it states — as a **capability**, not a workflow (ADR-009) — what a spawned gate agent's final output must contain before its turn is treated as done (the specific verdict shape each gate names: PROCEED/CAUTION/ABORT for Gate 0, PASS/FAIL for Gate 1's `STATUS`, PASS/FAIL/PAUSE for Gate 3, PASS/FAIL for Gate 4, PASS/SOFT PASS/FAIL for Gate 4.5), and how to recognize a mid-task stop (a partial finding, or a sentence describing what the agent is about to do next, with no verdict).
- [x] Given a spawned agent's turn ends mid-synthesis, when the skill's recovery step is followed, then it names resuming the same agent with the same context and asking explicitly for the final verdict — and explicitly forbids advancing to the next gate on a partial return.
- [x] Given `bash scripts/lint-skill.sh skills/subagent-result-completeness/SKILL.md`, when it runs, then it exits clean.
- [x] Given `commands/implement-story.md`, when the skill is wired in, then it is referenced from a single, cross-cutting location applicable to every gate that spawns a sub-agent (Gate 0, 1, 3, 4, 4.5) — following the file's existing skill-reference phrasing convention exactly: `` `Read skills/<name>/SKILL.md` for *how* ... This gate owns *when*...; the skill owns *how*. ``
- [x] Given `bash scripts/eval.sh`, when it runs, then the suite stays green and `commands/implement-story.md`'s required-sections presence, its `_preamble.md` reference, and its frontmatter are all intact (Tier-2 structural allowlist).

## Implementation Tasks

- [x] 2.1 Author `skills/subagent-result-completeness/SKILL.md` following the format of an existing skill (e.g. `skills/story-commit-provenance/SKILL.md`: frontmatter with `name`/`description`/`disable-model-invocation: true`/`status: candidate`, then Purpose / When to Use / How to Apply)
- [x] 2.2 Name the exact verdict shape each of Gate 0/1/3/4/4.5 requires (read `commands/implement-story.md`'s current Gate descriptions for the authoritative shape of each — do not invent a new verdict format)
- [x] 2.3 State the recognition signal for a mid-task stop and the recovery step (resume with same context, ask for the final verdict explicitly, never advance the gate on a partial return)
- [x] 2.4 Run `bash scripts/lint-skill.sh skills/subagent-result-completeness/SKILL.md` and fix any boundary violation
- [x] 2.5 Add one cross-cutting reference to the skill under `commands/implement-story.md`'s "### Step 3: Run Pipeline" intro, alongside the existing "Context refresh" and "File creation discipline" blockquote notes — naming which gates it applies to (0, 1, 3, 4, 4.5) — rather than repeating the reference once per gate
- [x] 2.6 Run `bash scripts/eval.sh` before and after; confirm `commands/implement-story.md`'s frontmatter, required sections, and `_preamble.md` reference are unchanged

## Notes

**Technical considerations:** `commands/implement-story.md`'s Step 3 intro
already carries two parallel blockquote notes (`Context refresh`,
`File creation discipline`) that apply across all gates rather than being
repeated per-gate — this is the established pattern to extend, not a new one
to invent. Match it exactly rather than adding five near-duplicate lines
across Gate 0/1/3/4/4.5.

**Evidence for this story:** across the `2026-08-12-machine-evaluable-exit-criteria`
run's ~18 sub-agent calls, nearly every one stopped mid-synthesis at least
once — architecture-check, coding, and review agents all did this repeatedly
— each requiring a manual "please finish and give your final verdict"
follow-up message before the orchestrator could act on the result.

**Risks:** Keep the skill itself capability-shaped per ADR-009 — it describes
*what a complete result looks like and how to react to an incomplete one*,
not *how to run implement-story's pipeline*. If it starts reading like a
workflow restatement, it will fail `scripts/lint-skill.sh`.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Code reviewed

---

## What Was Built

**Implementation Date:** 2026-08-12

### Files Created

1. **`skills/subagent-result-completeness/SKILL.md`**
   - Capability skill (ADR-009-conformant, `status: candidate`) naming the
     exact verdict shape each sub-agent-spawning gate requires (Gate 0
     `ARCH_CHECK:` PROCEED/CAUTION/ABORT; Gate 1's report-shape plus
     `STATUS: BLOCKED` as its only explicit stop-state; Gate 3
     `REVIEW_RESULT:` PASS/FAIL/PAUSE; Gate 4 `TEST_RESULT:` PASS/FAIL; Gate
     4.5's Gate Decision PASS/SOFT PASS/FAIL), how to recognize a mid-task
     stop, and the resume-and-ask-for-final-verdict recovery step

### Files Modified

1. **`commands/implement-story.md`**
   - Added a "Sub-agent completeness" blockquote note to the "### Step 3:
     Run Pipeline" intro, alongside the existing "Context refresh" and "File
     creation discipline" notes, referencing the new skill using the file's
     exact existing phrasing convention (`Read skills/.../SKILL.md` for
     *how* ...; ownership-split "this note owns *when*...; the skill owns
     *how*" clause)

### Test Results

**Verification:** N/A — documentation-only deliverable, no executable code
touched. `bash scripts/lint-skill.sh skills/subagent-result-completeness/SKILL.md`
exits clean. `bash scripts/eval.sh` (full suite) ran clean: Findings 0, Run
errors 0. `git diff commands/implement-story.md` confirmed only a prose-body
hunk in the Step 3 intro — frontmatter, `_preamble.md` reference, and
required sections untouched.

### Review Outcome

**Result:** PASS (after 1 fix cycle)

- **Iteration count:** 2 — first pass flagged the wired-in blockquote as
  missing the required "this note owns *when*...; the skill owns *how*"
  ownership-split clause (AC4 requires the phrasing convention "exactly");
  fixed and re-verified clean
- **Drift:** Small (an unrelated transcription slip in Story 1's platform
  note — "Gate 0/1/3/4/5" instead of "Gate 0/1/3/4/4.5" — was corrected
  alongside this story's fix, since both blockquotes sit in the same review
  pass)
- **Security:** Clean (docs-only change)

### Deviations from Spec

None against this story's own acceptance criteria. The first-draft blockquote
wording matched `technical-spec.md`'s suggested insertion text verbatim, but
that draft text itself omitted the ownership-split clause AC4 requires —
resolved in favor of the acceptance criterion (the binding contract) over the
technical spec's illustrative draft.
