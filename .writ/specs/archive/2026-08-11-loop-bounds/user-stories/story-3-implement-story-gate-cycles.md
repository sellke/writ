# Story 3: Bounds on implement-story's Gate-Retry Cycles

> **Status:** Completed
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** maintainer whose story is bouncing between the review gate and the coding agent
**I want** `/implement-story`'s three existing gate-retry caps declared in machine-readable frontmatter instead of prose scattered across a 961-line file
**So that** the caps can be linted, cannot drift from the agent definitions that enforce them, and cannot be quietly dropped when the file is restructured

## Acceptance Criteria

- [x] Given `commands/implement-story.md`, when its frontmatter is read, then `loop.unit` is `review_cycle`, `loop.max_iterations` is `3`, `loop.on_exhaustion` is `escalate`, and `loop.calibrated_against` cites both `commands/implement-story.md:595` (the existing prose cap) and the 42 recorded `Iteration count` values (38 at 1, 4 at 2; max observed 2).
- [x] Given the same frontmatter, when `nested` is read, then it declares exactly two entries: `testing_cycle` at `max_iterations: 2` citing `implement-story.md:732`, and `agent_self_fix` at `max_iterations: 3` citing `MAX_SELF_FIX_ITERATIONS = 3` in `agents/coding-agent.md:232` and `agents/testing-agent.md:225` — both with `on_exhaustion: escalate`.
- [x] Given all three declared numbers, when they are compared against their sources, then each equals its source exactly — no number in this story is newly derived, and the declared values would not have tripped any of the 42 recorded story runs.
- [x] Given the `review_cycle` counter, when its semantics are documented, then it is stated as **one shared counter across four increment sites** — Gate 3 FAIL, Gate 3.5 "Reject", Gate 3.5 "Modify spec", and Gate 4.5 FAIL — and not as four independent budgets.
- [x] Given any of the three caps is reached, when the loop exhausts, then `escalate` presents one bounded `AskQuestion` naming the loop, the bound, the count reached, and the partial state — preserving the existing behavior at `implement-story.md:940–942` and Gates 1 and 4 rather than replacing it, and never silently continuing past a cap.
- [x] Given progressive-disclosure work later restructures this 961-line file, when the frontmatter is validated, then it still passes — validation reads frontmatter only and depends on no body line number.

## Implementation Tasks

- [x] 3.1 Re-verify all three source values before writing them: `commands/implement-story.md:595` and `:732`, and `MAX_SELF_FIX_ITERATIONS = 3` in `agents/coding-agent.md:232` + `agents/testing-agent.md:225`, confirming both agent files still agree
- [x] 3.2 Re-verify the calibration evidence by re-collecting the `Iteration count` records across `.writ/specs/archive/*/user-stories/*.md` and confirming the maximum is still 2, so 3 retains one iteration of headroom
- [x] 3.3 Append the `loop:` block with its two `nested` entries to `commands/implement-story.md`'s existing `---` frontmatter, touching no other key
- [x] 3.4 Document the shared-counter semantics of `review_cycle` — four increment sites, one budget — in the frontmatter's `unit` description or the adjacent prose, so a reader cannot infer four separate caps
- [x] 3.5 Confirm every `escalate` path already exists and preserve it: the Gate 1 and Gate 4 `STATUS: BLOCKED` `AskQuestion` blocks and the review-loop escalation at `:940–942` are the implementation of `on_exhaustion: escalate`, and this story declares them rather than rewriting them
- [x] 3.6 Verify acceptance criteria are met, including a cross-read assertion binding each declared number to its source file so a future edit to either side is caught as drift

## Notes

**Technical considerations:**

- **Why 3 and not 2.** Four archived stories recorded 2 review iterations. A bound of 2 sits exactly at the observed maximum with zero headroom, so the next story resembling those four would trip it — converting a run that succeeded into a failure, which is precisely the hazard the locked contract names as hardest. Business Rule 2 forbids a bound *below* the observed max; setting one *at* the max is technically legal and still wrong here. 3 is also the number already in the file, so declaring it changes no behavior.
- All three values are `escalate`, not `halt_reported` and not `quarantine`. `quarantine` is illegal — no `phase-execution-*.json` record exists for a story. `halt_reported` would be a behavioral regression, since the file already escalates with an `AskQuestion` at each cap. This story declares existing behavior; it does not change it.
- The `testing_cycle` cap of 2 is the weakest-evidenced of the three and should be labelled that way: it is a faithful transcription of `:732`, but the original derivation of that 2 is recorded nowhere, and no recorded run reports a testing-fix iteration above 1. Do not fabricate a justification for it.

**Risks / challenges:**

- **Drift between the frontmatter and the agent files is the real failure mode here.** `MAX_SELF_FIX_ITERATIONS = 3` lives in two agent definitions and is referenced at three points in `implement-story.md`. Once a fourth copy exists in frontmatter there are six places to keep in sync, and the only defense is Story 5's cross-read assertion. Prefer an assertion that reads the agent files over one that hardcodes 3.
- `implement-story.md` is the 961-line file ADR-021's progressive-disclosure work will split first. Any binding to body line numbers will break. Bind to frontmatter and to the agent files, never to `implement-story.md`'s own line offsets.
- A tempting simplification is collapsing the four review-cycle increment sites into "Gate 3 failures." That would silently widen the budget, because Gate 3.5 and Gate 4.5 outcomes also count today (`:595`, `:774`).

**Integration points:**

- Consumes Story 1's schema; adds no keys.
- Owns exactly one file: `commands/implement-story.md`. Reads `agents/coding-agent.md` and `agents/testing-agent.md` but modifies neither.
- Story 5's cross-read assertions verify all three numbers against their sources.
- Must survive the ADR-021 restructuring of this file; coordinate only to the extent of keeping the frontmatter block intact.

**Implementation record (2026-08-11):**

- **Task 3.1: all three source values re-verified and unchanged.** The review-loop cap ("Max 3 iterations across review and visual QA gates") and the Gate 4 cap ("2 fix iterations max") are both still in the file; `MAX_SELF_FIX_ITERATIONS = 3` is still declared in **both** `agents/coding-agent.md` and `agents/testing-agent.md` and they still agree. Every cited line number had shifted +6 when `2026-08-11-component-contract` added `problem:`/`outcome:`/`exit_criteria:` (`:595` -> `:601`, `:732` -> `:738`, `:774` -> `:780`, `:940-942` -> `:946-948`, coding-agent `:232` -> `:238`, testing-agent `:225` -> `:231`).
- **Because of that shift, `calibrated_against` cites anchor text, not line numbers.** Every citation quotes the literal sentence it transcribes. A line offset would have been stale within one merge and would break again under the ADR-021 restructuring this file is first in line for; the quoted text survives both, and Story 5's cross-read greps content.
- **Task 3.2 re-collection corrected the distribution, not the maximum.** Re-running the collection over `.writ/specs/archive/*/user-stories/*.md` gives **42 records: 39 at 1 iteration, 3 at 2** — not the authored 38/4. (A 43rd `iteration counts` match is an acceptance-criteria sentence in an archived `/ralph` story, not a record.) The load-bearing fact is unchanged: **maximum ever observed = 2**, so 3 retains exactly one iteration of headroom and would not have tripped any of the 42 runs.
- **Shared-counter semantics are stated in both carriers.** The frontmatter `calibrated_against` names the four increment sites and says "not four separate budgets"; the Gate 3 prose gained the same sentence, because a reader mid-run is looking at the prose, not the frontmatter.
- **Nothing was rewritten into existence.** All three `on_exhaustion` values are `escalate` because the escalations already exist — the Gate 1 and Gate 4 `STATUS: BLOCKED` `AskQuestion` blocks and the review-loop escalation. `quarantine` is illegal here (no `phase-execution-*.json` record exists for a story) and `halt_reported` would have been a behavioral regression.
- **The `testing_cycle` citation says its evidence is only adequate** and states that the original derivation of the 2 is recorded nowhere. Fabricating a justification for it was the specific temptation this story named.
- **Measured cost:** `commands/implement-story.md` 975 -> 989 lines — 14 frontmatter lines, zero net prose lines (the Gate 3 sentence was extended in place). `grep -c '^---$'` unchanged at 18.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** [Rule 7 (existing prose bounds are transcribed, not re-derived — the primary rule this story implements), Rule 2 (no bound below the highest observed value; 38×1 and 4×2 across 42 records), Rule 5 (exhaustion never degrades scope — `escalate` is mandatory where continuing would change scope), Rule 3 (named state, never a bare halt)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The five bounds table — `implement-story` `review_cycle` (3/escalate) and its nested `testing_cycle` (2/escalate) and `agent_self_fix` (3/escalate), each with source and evidence quality] — from spec.md → ## Detailed Requirements → ### The five bounds
- **Error map rows:** [`/implement-story` invoked directly outside `/implement-spec` → all three bounds are `escalate`, need no phase state; `--quick` skips gates → no separate bound, skipped gates never increment; progressive disclosure restructures the file → check reads frontmatter only] — from sub-specs/technical-spec.md → Interaction Edge Cases
- **Contract:** ["Each bound is derived from that loop's real semantics — `/implement-story` bounds gate-retry cycles — not a single global constant"; "a bound set too low turns a working loop into a spurious failure"] — from spec.md → ## Contract (Locked)
