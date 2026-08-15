# Story 5: Gate Wiring — Making the Checkers Decide

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 3, Story 4

## User Story

**As a** developer running `/implement-story`
**I want** Gate 2 to boot the framework and Gate 4's coverage verdict to come from the
coverage tool rather than from the agent that ran it
**So that** the two gates that already claim these guarantees actually hold them, without a
new gate, a new number, or a new thing to learn

## Acceptance Criteria

> **AC IDs assigned through:** AC-5.5

- [ ] Given Gate 4 receives `TEST_RESULT: PASS` with `Coverage threshold met: YES` while `test-integrity.py coverage` re-derives a value below the bar, when the gate completes, then the checker's verdict is authoritative, the story does not reach `Completed ✅`, and the report shows both the claim and the measurement. `[AC-5.1]`
- [ ] Given Gate 2 runs on a story that changed source, when the gate completes, then `build-smoke.py` has run, its verdict appears in the story report, and a `build_failed_source` finding routes through the existing shared BLOCKED escalation rather than new control flow. `[AC-5.2]`
- [ ] Given either checker returns `unverifiable`, when the gate completes, then the pipeline continues, the reason is surfaced verbatim in the story report, and the story is not marked `⚠️ DEGRADED` on that basis alone — an unverifiable check is not a failed gate. `[AC-5.3]`
- [ ] Given the wiring is complete, when `bash scripts/eval.sh` runs, then it passes — specifically the five literal-pinned routing-table rows at `scripts/eval.sh:2232–2236` are unchanged, `scripts/eval-loop-bounds.py`'s frontmatter/prose cross-read still agrees, and `scripts/check-agent-parity.sh` reports no drift between `agents/coding-agent.md` and `claude-code/agents/writ-coder.md`. `[AC-5.4]`
- [ ] Given no new gate number is introduced, when the pipeline table and every gate-number reference outside `implement-story.md` are inspected, then the gate set is unchanged from Gate 0 through Gate 5 and `agents/visual-qa-agent.md`'s ASCII pipeline diagram needs no edit. `[AC-5.5]`

## Implementation Tasks

- [ ] 5.1 Extend Gate 2's block in `commands/implement-story.md` (lines 183–191) with the smoke step, and update the Pipeline-table Name cell at line 60 and the `--quick` **Keeps** line at line 333 to match `[AC-5.2, AC-5.5]`
- [ ] 5.2 Extend Gate 4's block (lines 235–249) so `test-integrity.py` runs after the testing agent returns and its verdict overrides the self-reported field, using the wording `commands/implement-spec.md:261–265` uses for `exit-criteria.py` `[AC-5.1]`
- [ ] 5.3 Add a sentence to `agents/testing-agent.md` recording that `Coverage threshold met` at line 133 is now verified rather than trusted — leaving the field itself in place, since Gate 4's BLOCKED handling and `skills/subagent-result-completeness/SKILL.md:44` both key off the existing `TEST_RESULT:` shape `[AC-5.1]`
- [ ] 5.4 Specify the `unverifiable` handling in both gates: continue, surface verbatim, do not mark DEGRADED `[AC-5.3]`
- [ ] 5.5 Update `agents/coding-agent.md:130,132,221` where they describe Gate 2's remit, mirror into `claude-code/agents/writ-coder.md:60`, and run `scripts/check-agent-parity.sh` `[AC-5.4]`
- [ ] 5.6 Fix `skills/tdd-cycle/SKILL.md:10`, which reads "Gate 2 spawns the coding agent" — Gate 1 does `[AC-5.4]`
- [ ] 5.7 Add the dated schema-3 justification entry to `.writ/leanness-baseline.json` for the command-surface growth, and verify `bash scripts/eval.sh` passes end to end `[AC-5.4, AC-5.5]`

## Notes

**Technical considerations:** The decision not to add a gate number is load-bearing and should
survive review pressure. Gate numbers are free-text strings with no registry, pinned by
literal in five places in `scripts/eval.sh`, mirrored in `scripts/eval-leanness.py`'s
`GATE_AGENT_FILES`, in `skills/subagent-result-completeness/SKILL.md`'s gate→verdict table,
and in an ASCII pipeline diagram in `agents/visual-qa-agent.md`. Extending two existing blocks
costs a table cell and a `--quick` line. Inserting Gate 2.6 costs all of the above plus a
`--quick` policy decision — for two checks that are not new stages but the missing halves of
existing ones.

Neither addition introduces an iteration cap. That matters: `scripts/eval-loop-bounds.py`
cross-reads the `loop.nested` frontmatter against prose sentences like "2 fix iterations max",
and a cap added in one place and not the other emits `drift-*`.

**Risks:** The override at Gate 4 is the point of the story, and the tempting softening is to
report the discrepancy and continue. That reproduces exactly the condition the parent spec
exists to end — a stated guarantee with no consequence. If the checker says the bar was not
met, the story does not close, and the escape hatch is the existing BLOCKED escalation with
its human decision, not a quiet downgrade.

Second risk: `unverifiable` and `⚠️ DEGRADED` are easy to conflate. DEGRADED means a gate could
not be cleared; `unverifiable` means a check could not be run. Conflating them either floods
DEGRADED until it stops meaning anything, or hides real gate failures. AC-5.3 pins the
distinction.

**Integration:** This story does not touch `implement-story.c3` or
`.writ/docs/exit-criteria-classification.md`. That criterion is recorded as `Scope: excluded`
on the ground that the What Was Built record it reads from is allowed to be incomplete by
design, and reopening it is out of scope here.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** "no permanent-warning instruments", "`DEGRADED` semantics are consumed,
  not redefined", the verdict trichotomy — from `spec.md` → `## 📋 Business Rules`
- **Gate wiring detail:** exact line numbers, what must not change, the byte-budget cost —
  from `sub-specs/technical-spec.md` → `## Gate Wiring` and `## Byte Budget`
- **The override precedent:** `commands/implement-spec.md:261–265` — "a run may report
  COMPLETE and be published as `unmet`" — is the sentence pattern to reuse at Gate 4
- **Escalation to reuse:** `commands/implement-story.md:307–324`, the shared BLOCKED
  escalation, anchor `#blocked-agent-escalation`
