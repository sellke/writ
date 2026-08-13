# Story 6: Adapter Wiring

> **Status:** Completed ✅ (2026-08-12)
> **Priority:** Low
> **Dependencies:** Story 5

## User Story

**As a** Writ user on Claude Code
**I want** `/goal` wired to the checker's exit code, with its constraints documented
**So that** I get Stop-hook enforcement of the same condition the other three platforms enforce by convention, without the hook becoming the definition of the condition

## Acceptance Criteria

- [x] Given `adapters/claude-code.md` § Quality Gates with Hooks, when the `/goal` wiring is documented, then it shows a concrete goal condition phrased against `scripts/exit-criteria.py check` exiting 0, and states that the checker is the authority and `/goal` only the delivery vehicle.
- [x] Given the documented goal condition, when it is read, then it is **satisfiable by pausing** — reaching a retained `AskQuestion` or an `impossible` verdict counts as met — per `spec.md` Business Rule 1.
- [x] Given `/goal`'s single-slot behavior, when the adapter documents it, then it states that registering a goal removes every existing top-level prompt Stop hook, that goals therefore cannot nest, and that only the outermost running command may hold one.
- [x] Given `/goal`'s gating, when the adapter documents it, then it names both refusal modes — restricted hooks (`disableAllHooks` / `allowManagedHooksOnly`) and an untrusted workspace — so a silently-unset goal is diagnosable rather than mistaken for enforcement.
- [x] Given the other three adapters, when this story completes, then `adapters/cursor.md`, `adapters/codex.md`, and `adapters/openclaw.md` are unchanged — they get the checker through Story 5's command wiring, which needs no adapter change.

## Implementation Tasks

- [x] 6.1 Add a `/goal` subsection under the existing § Quality Gates with Hooks in `adapters/claude-code.md`
- [x] 6.2 Write the example goal condition, phrased to be satisfied by a pause as well as by completion
- [x] 6.3 Document the single-slot constraint and the outermost-command-only rule
- [x] 6.4 Document both refusal modes and how to detect a goal that failed to set
- [x] 6.5 Confirm no other adapter file changed; run `bash scripts/eval.sh`

## Notes

**Technical considerations:** `adapters/claude-code.md` line 3 already claims hooks
as a native integration and § Quality Gates with Hooks already carries a Stop-hook
example. This is an addition to an existing section, not a new capability claim.

**Risks:** The failure mode to document is a goal that never registered. Both
refusal paths return a message and set nothing — a user who does not notice
believes they have enforcement they do not have. That is worse than no goal, and it
is why task 6.4 exists.

**Priority is Low deliberately.** Stories 1–5 deliver enforcement on all four
platforms through the command wiring. This story adds Claude-Code-native
*blocking* on top. If the spec is cut short, this is the story to drop — and the
one that must never be the only story shipped, because that would leave the
mechanism platform-specific, which is the outcome the spec exists to avoid.

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

- **`adapters/claude-code.md`** — added a `### The /goal Stop Hook` subsection under the existing § Quality Gates with Hooks, directly after its existing Stop-hook JSON example. 34 insertions, 0 deletions; purely additive.

### Implementation Decisions

1. **Goal condition written as an explicit three-way disjunction** — Gate 0 architecture review flagged this as the load-bearing part of the whole story: a condition phrased as "exits 0" with the pause exception as a footnote would push the model past a human gate, exactly the anti-pattern spec.md's "What `/goal` showed, and why it is not the answer" section warns against. The documented condition names all three states explicitly and independently: (a) checker exits 0/met, (b) the run is currently paused awaiting a retained `AskQuestion` — standing on its own, not expressed as a checker output, since the checker is invoked late (Step 4.1c / completion step) while a pause like Step 2.3's execute/edit/abort confirmation can occur earlier — (c) checker exits 2/impossible.
2. **Single-slot language reproduced verbatim from spec.md** rather than re-derived, including the exact phrase "the innermost silently destroys the outer, and clears leaving nothing behind" — confirmed by Gate 3 review as an exact match to spec.md's own wording, not softened or embellished.
3. **Both refusal modes named by mechanism** (`disableAllHooks`/`allowManagedHooksOnly`, untrusted workspace), with an explicit diagnosability note: a silently-unset goal is worse than no goal, since the run proceeds believing it is gated when it is not.

### Test Results

**Verification:** `bash scripts/eval.sh` — Findings: 0, Run errors: 0, before and after. No test runner applies to markdown adapter files.
- ✅ `git diff --stat adapters/` confirms only `adapters/claude-code.md` changed; `cursor.md`, `codex.md`, `openclaw.md` untouched
- ✅ The pre-existing Stop-hook JSON example in § Quality Gates with Hooks is untouched

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** Small — a citation slip (referenced "Step-3 execute/edit/abort confirmation" where the actual step is 2.3) caught by Gate 3 review and corrected inline; the substantive claim (a retained pause can precede the checker's late invocation) held under the correct step number.
- **Security:** Clean — documentation-only change, no code/exec paths introduced.

### Deviations from Spec

None.
