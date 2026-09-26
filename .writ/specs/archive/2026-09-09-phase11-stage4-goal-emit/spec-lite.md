# Phase 11 Stage 4a: Goal Emit (Lite)

> Source: .writ/specs/2026-09-09-phase11-stage4-goal-emit/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Goal Card → `GOAL.md` + `VERIFY.md` + printed `/goal` line; emit only.

**Implementation Approach:**
- Python 3.9 stdlib; `emit` + `check`; no LLM API; no hook registration
- Default out `.writ/goals/<card-stem>/`; idempotent overwrite
- create-goal after save; implement-phase when origin is a card
- Adapter invoke is a copy of the existing three-way template
- VERIFY.md names `exit-criteria.py` when card `spec_ref` points at an existing `spec.md`; otherwise "count DONE WHEN lines on the card"

**Files in Scope:**
- `scripts/goal-emit.py` — new
- `commands/create-goal.md` — emit after save
- `commands/implement-phase.md` — emit when origin is a card
- `adapters/claude-code.md` — paste-the-emit-line
- `scripts/eval.sh` — `goal-emit` check

**Error Handling:**
- Missing/`loop: no` card → `unverifiable`; command continues
- Malformed card / missing ADR sentence → `fail`
- Missing written `GOAL.md` / `VERIFY.md` on `check` of a valid `loop: yes` card → `fail` `missing_boundary`
- Helper missing / exit 2 → `add_finding`

**Integration Points:** Do not rewrite `/goal` clauses; do not change `implement-story` spawn

---

## For Review Agents

**Acceptance Criteria:**
1. Script emits/checks; unverifiable ≠ fail; ADR sentence in both files `[AC-1.1, AC-1.2, AC-1.3]`
2. create-goal and implement-phase invoke emit; never register `/goal` `[AC-2.1, AC-2.3, AC-2.4]`
3. Printed invoke equals adapter template; eval check; gold equality `[AC-3.1, AC-3.2, AC-3.5]`
4. Nothing demotes the five-agent pipeline `[AC-3.5]`

**Business Rules:**
- Emit is not register; `loop: no` skips; overwrite idempotent
- ADR-013 verbatim; no yuss; no eight-run; no live `/goal`
- `stage-4a:` per story; Cursor/Codex adapters unchanged

**Experience Design:**
- Entry: `/create-goal` save or `/implement-phase` with card origin
- Happy path: save → files → printed line → paste unchanged
- Moment of truth: invoke diffs empty vs adapter; ADR sentence present
- Error: `loop: no` is a note; helper crash is a finding

---

## For Testing Agents

**Success Criteria:**
1. pytest pass/fail/unverifiable fixtures green
2. eval-wiring bash green; full `eval.sh` Findings 0
3. Gold equality in Story 3 WWB

**Shadow Paths:**
- **Happy path:** `loop: yes` card → files + invoke match gold
- **Nil input:** missing `--card` → unverifiable
- **Empty input:** `loop: no` → unverifiable `loop_no`, no dir
- **Upstream error:** missing OBJECTIVE → `fail` `malformed_card`

**Edge Cases:**
- Re-emit overwrites same stem; missing phase origin → unverifiable note
- Gold invoke line must equal adapter template bytes

**Coverage Requirements:** New script ≥80%; error paths 100%

**Test Strategy:** pytest CLI fixtures; `test_eval_goal_emit.sh`; gold-file diff
