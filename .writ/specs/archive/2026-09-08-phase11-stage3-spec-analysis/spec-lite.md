# Phase 11 Stage 3: Spec Analysis (Lite)

> Source: .writ/specs/2026-09-08-phase11-stage3-spec-analysis/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** `spec-analyze.py` after stories exist; advisory; precision on fixtures.

**Implementation Approach:**
- Python 3.9 stdlib; `pass`/`fail`/`unverifiable`; no LLM API in the script
- Structural codes vs schema-checked `--findings` JSON
- New create-spec step after 2.6a; verify-spec notes; eval not count-blocking
- Precision on committed labels, not a live model

**Files in Scope:**
- `scripts/spec-analyze.py` — new
- `commands/create-spec.md` — Step 2.6c after 2.6b
- `commands/verify-spec.md` — advisory check
- `scripts/eval.sh` — `spec-analyze` check

**Error Handling:**
- `unverifiable` → continue, no `DEGRADED`
- Analysis `fail` → note; package still completes
- Exit 2 / missing helper → `add_finding`

**Integration Points:** `ac-trace.py` stays Step 2.6a; `install.sh` `scripts/*.py`

---

## For Review Agents

**Acceptance Criteria:**
1. Script exists; structural + schema-check; unverifiable ≠ fail `[AC-1.1, AC-1.2, AC-1.3]`
2. create-spec after 2.6a and verify-spec invoke it; findings are notes `[AC-2.1, AC-2.2, AC-2.3]`
3. eval.sh `spec-analyze` check; `eval.sh` exits 0 `[AC-3.1, AC-3.3]`
4. Precision per class recorded on labeled fixtures; nothing becomes blocking `[AC-3.5]`

**Business Rules:**
- Advisory one release; no Phase B; no ac-trace replacement
- No yuss checkout; no eight-run; ADR-013; `stage-3:` per story

**Experience Design:**
- Entry: `/create-spec` or `/verify-spec`
- Happy path: stories → LLM JSON → script → notes → package completes
- Moment of truth: real contradiction is a note; missing findings ≠ fail
- Error: unverifiable continues; malformed JSON is a note

---

## For Testing Agents

**Success Criteria:**
1. pytest pass/fail/unverifiable fixtures green
2. eval-wiring bash green; full `eval.sh` Findings 0
3. Precision table in Story 3 WWB

**Shadow Paths:**
- **Happy path:** clean spec + well-formed findings → pass, notes empty or clean
- **Nil input:** no `--spec` → unverifiable
- **Empty input:** no `--findings`, no structural hit → unverifiable
- **Upstream error:** malformed JSON → fail `malformed_findings`; command continues

**Edge Cases:**
- Live Writ spec without findings file → unverifiable note, eval still 0
- `unmeasurable_criterion` must not fail a clean fixture

**Coverage Requirements:** New script ≥80%; error paths 100%

**Test Strategy:** pytest fixtures; `test_eval_spec_analyze.sh`; gold-label precision
