# Story 1: implement-spec Orchestration & Bookkeeping Clarity

> **Status:** Completed ✅ (2026-08-12)
> **Priority:** High
> **Dependencies:** None

## User Story

**As an** orchestrator running `/implement-spec` across a multi-story spec
**I want** the spawn mechanism, execution-state write, and spec-completion
bookkeeping to be unambiguous and load-bearing
**So that** I don't have to improvise how stories actually get dispatched, and
a finished spec doesn't leave its own header stale after every story completes

## Acceptance Criteria

- [x] Given `commands/implement-spec.md` Step 3.2 ("Execute Batches"), when a platform's invocation of `/implement-story` loads its instructions inline into the current context rather than backgrounding it, then the step explicitly states that "spawn ... concurrently" means the orchestrator issues one parallel tool-call per story (each running that story's own gate sequence), not a nested command call the harness auto-parallelizes.
- [x] Given `commands/implement-spec.md` Step 3.3 ("Update State After Each Story"), when a story completes, then the execution-state file write is stated as a required disk write that must happen before dispatching the next story — not a log line that can be satisfied by conversational progress tracking alone.
- [x] Given `commands/implement-spec.md`'s completion step, when the checker verdict is `met` and every story is `Completed ✅`, then the step states that `spec.md`'s own `> **Status:**` header line is updated to `Complete (<date>)` — the same completion status story files and `README.md` already receive.
- [x] Given the three amendments above, when `bash scripts/eval.sh` runs, then the suite stays green and `commands/implement-spec.md`'s frontmatter (`problem`/`outcome`/`exit_criteria`/`loop:`) and its `## Completion` heading are unchanged.

## Implementation Tasks

- [x] 1.1 Read the current content of `commands/implement-spec.md` Step 3.2, 3.3, and the completion step (post-checker-verdict paragraph, before `## Phase-Orchestrated Lane Mode`) to confirm exact insertion points — the file may have moved since spec creation (see spec.md § Technical Concerns)
- [x] 1.2 Amend Step 3.2 with the platform-note clause above, placed after the "If parallel batch" bullet list, before "If sequential batch"
- [x] 1.3 Amend Step 3.3's "Update execution state file with result" bullet to state it is a required, immediate disk write — not satisfied by TodoWrite or narration alone — since it is the only artifact `--resume` reads
- [x] 1.4 Add a short paragraph to the completion step stating that a `met` checker verdict with all stories `Completed ✅` updates `spec.md`'s own header status to `Complete (<date>)`, naming this as the counterpart to the story-file and README updates that step already performs
- [x] 1.5 Run `bash scripts/eval.sh` before and after; confirm frontmatter and `## Completion` heading in `commands/implement-spec.md` are byte-identical to before

## Notes

**Technical considerations:** All three amendments land in prose bodies, not
in the file's governed frontmatter or its `## Completion` heading — low
structural risk. Keep additions terse; this file already carries the
`Phase-Orchestrated Lane Mode` section below the completion step, which must
not be disturbed.

**Evidence for this story:** during the `2026-08-12-machine-evaluable-exit-criteria`
run, the orchestrator had to manually recognize that invoking `/implement-story`
loaded inline rather than backgrounding, then hand-spawn each story's gates;
`/verify-spec` separately caught `spec.md`'s header reading `Not Started`
after all 6 stories completed; and the execution-state JSON was written once
and then discarded, never updated per-story.

**Risks:** Resist the temptation to add a new step for these — they are
amendments to existing steps, matching this file's own established terseness.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Code reviewed

---

## What Was Built

**Implementation Date:** 2026-08-12

### Files Created

[None]

### Files Modified

1. **`commands/implement-spec.md`**
   - Step 3.2 ("Execute Batches"): added a "Platform note" paragraph clarifying
     that on a harness where `/implement-story` loads inline rather than
     backgrounding, "spawn ... concurrently" means one parallel tool-call per
     story, not harness-auto-parallelized nested command calls
   - Step 3.3 ("Update State After Each Story"): strengthened the "Update
     execution state file with result" bullet into an explicit required,
     immediate disk-write statement — the only artifact `--resume` reads
   - Completion step: added a "Spec header sync" paragraph stating that a
     `met` checker verdict with all stories `Completed ✅` updates `spec.md`'s
     own `> **Status:**` header to `Complete (<date>)`

### Test Results

**Verification:** N/A — documentation-only deliverable, no executable code
touched. `bash scripts/eval.sh` (full suite) ran clean before and after:
Findings 0, Run errors 0. `git diff commands/implement-spec.md` confirmed
only prose-body hunks — frontmatter and `## Completion` heading byte-identical.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** None
- **Security:** Clean (docs-only change)

### Deviations from Spec

None. One accuracy fix beyond the story's own scope was made alongside
Story 2's review: the Step 3.2 platform note originally listed the
sub-agent-spawning gates as "Gate 0/1/3/4/5"; corrected to "Gate 0/1/3/4/4.5"
to match the actual gate numbering used elsewhere in `implement-story.md`.
