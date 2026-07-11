# UAT Plan: Native-Memory Guidance Per Adapter

> **Generated:** 2026-07-11
> **Spec:** `.writ/specs/2026-07-11-native-memory-guidance/`
> **Stories Covered:** 2 of 2 completed
> **Total Scenarios:** 9

## How to Use This Plan

1. Work through scenarios in order (grouped by story).
2. For each scenario, follow the steps exactly as written.
3. Mark Pass or Fail — add notes for any unexpected behavior.
4. Scenarios marked Fail should be filed as issues or fed back to the spec.
5. A feature passes UAT when all scenarios pass (or failures are accepted as known limitations).

All commands assume the repository root `/Users/Adam/Projects/writ` as the working directory. Every scenario here is artifact/machine-verifiable — no external tooling required.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: Per-adapter guidance + mission sweep | ✅ Covered | 5 | AC: 4, Consistency: 1 |
| Story 2: `memory-interop` eval check | ✅ Covered | 4 | AC: 3, Shadow: 1 |

---

## Story 1: Per-Adapter Native-Memory Guidance + Mission Sweep

### Scenario 1: All four adapters carry the section

**Source:** Acceptance Criteria — Story 1

**Steps:**
1. Run `grep -l "Native Memory & the Writ Ledger" adapters/*.md`.

**Expected Result:**
- All four adapters (`cursor.md`, `claude-code.md`, `codex.md`, `openclaw.md`) are listed.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** `adapters/*.md`

**Notes:**

---

### Scenario 2: The two-place rule is identical across adapters

**Source:** Consistency (Business Rule 2)

**Steps:**
1. Run `grep -rc "the reviewable markdown layer that feeds" adapters/*.md`.

**Expected Result:**
- Each of the four adapters returns a count of 1 — the canonical rule appears verbatim in all four.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** `adapters/*.md`

**Notes:**

---

### Scenario 3: Each section names the platform's real native-memory surface

**Source:** Acceptance Criteria — Story 1

**Steps:**
1. Read the section in each adapter.

**Expected Result:**
- `cursor.md` names Cursor Memories + semantic indexing; `claude-code.md` names `CLAUDE.md` + `.claude/agent-memory/`; `codex.md` names `AGENTS.md`; `openclaw.md` names session/file-based state. Each names the anti-pattern (decisions only in native memory are unreviewable and evaporate on churn).

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** `adapters/*.md`

**Notes:**

---

### Scenario 4: Each section cross-links the external-index layer

**Source:** Acceptance Criteria — Story 1

**Steps:**
1. Confirm each adapter section references the `gbrain-interop` skill or `.writ/docs/gbrain-recipe.md`.

**Expected Result:**
- The three-layer model (native memory → ledger → external index) reads consistently, with a one-line cross-link to the GBrain recipe/skill in each adapter.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** `adapters/*.md`

**Notes:**

---

### Scenario 5: Mission sweep is clean on active surfaces

**Source:** Acceptance Criteria — Story 1

**Steps:**
1. Run `grep -rF "persistent-database knowledge layer" .writ/product/mission.md .writ/product/mission-lite.md README.md .writ/docs/`.

**Expected Result:**
- No matches on active surfaces. (The phrase remains only in `roadmap.md` and `adr-011`, which describe the change — those are intentionally untouched.)

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** `.writ/product/mission.md` (active "not a memory database or retrieval engine")

**Notes:**

---

## Story 2: `memory-interop` Eval Check

### Scenario 6: The targeted check passes

**Source:** Acceptance Criteria — Story 2

**Steps:**
1. Run `bash scripts/eval.sh --check=memory-interop`.

**Expected Result:**
- The `memory-interop` check reports PASS with 0 findings.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** `scripts/eval.sh` → `check_memory_interop`

**Notes:**

---

### Scenario 7: The check is registered additively

**Source:** Acceptance Criteria — Story 2

**Steps:**
1. Confirm `memory-interop` appears exactly once in the `CHECKS` array and `check_memory_interop` is defined.
2. Confirm no existing check function or `CHECKS` entry was altered (`git diff` against the phase base for `scripts/eval.sh` shows only additions).

**Expected Result:**
- Exactly one new `CHECKS` entry and one new function; existing checks untouched.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** `scripts/eval.sh`

**Notes:**

---

### Scenario 8: The check asserts the sibling GBrain artifacts

**Source:** Acceptance Criteria — Story 2

**Steps:**
1. Read `check_memory_interop`.

**Expected Result:**
- It asserts `skills/gbrain-interop/SKILL.md` exists and is registered in `.writ/manifest.yaml` + root `SKILL.md`, and that `.writ/docs/gbrain-recipe.md` contains the round-trip/graceful-absence language. It `forbid_literal`s stale mission framing on active surfaces.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** `scripts/eval.sh` → `check_memory_interop`

**Notes:**

---

### Scenario 9 (Shadow): The full suite stays green

**Source:** Acceptance Criteria — Story 2

**Steps:**
1. Run the full `bash scripts/eval.sh`.

**Expected Result:**
- 0 findings, 0 run errors; all checks PASS, including `memory-interop`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** `scripts/eval.sh`

**Notes:**

---

## Sign-Off

- [ ] All 9 scenarios pass (no external tooling required)
- Overall UAT status: ______________________
