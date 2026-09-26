# Phase 11 Stage 2b: Mechanize the Gates (Lite)

> Source: .writ/specs/2026-09-08-phase11-stage2b-mechanize-the-gates/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Eight of ten `implement-story` gates name a script; Gate 1 and Gate 4.5 stay `prose-only`; `--prose-only-blocking` is on.

**Implementation Approach:**
- Python 3.9 stdlib; Gate 4 override pattern; `pass`/`fail`/`unverifiable`; checker wins
- Gate 3 override is FAIL-only — mechanical pass does not wash out an agent FAIL
- Gate 0 never re-derives ABORT; `--planned` vs `--changed`
- Gate 5 fixtures use a tiny app tree, not this repo
- No eight-run re-run; replay against committed baseline JSON
- Watch field only — do not change how `/implement-story` spawns

**Files in Scope:**
- `scripts/{review-override,arch-check,docs-check,boundary-map,change-surface,drift-format}.py` — new
- `commands/implement-story.md` — wiring + `gates:` flip
- `agents/visual-qa-agent.md` — drop 85/70 (DEV-102)
- `scripts/pipeline-baseline.py` — `background_tasks_outstanding`, extend `REDERIVATION_KEYS`
- `scripts/eval.sh` — one check per new script; `--prose-only-blocking`

**Error Handling:**
- FAIL → existing BLOCKED escalation
- `unverifiable` → continue, no `DEGRADED`
- Replay disagreement → note, not revert

**Integration Points:** `ac-trace.py`, `test-integrity.py`, `story-deps.py`, `verdict-provenance.py`, `install.sh` `scripts/*.py` glob

---

## For Review Agents

**Acceptance Criteria:**
1. Exactly two `prose-only` gates (Gate 1, 4.5); every other gate names an existing script `[AC-5.2]`
2. `verdict-provenance.py check --prose-only-blocking` exits 0 `[AC-5.2]`
3. Each new script has pass / fail / unverifiable fixtures `[AC-1.4, AC-2.5, AC-3.1, AC-4.1, AC-5.1]`
4. Replay table covers all 16 committed baseline records `[AC-5.5]`
5. ABORT and Large-drift accept/reject/modify stay human `[AC-2.2, AC-5.1]`

**Business Rules:**
- Checker wins; `unverifiable` ≠ fail; no new gate numbers
- No eight-run re-run; no orchestrator spawn change
- ADR-013; decision-log `stage-2b:` per story

**Experience Design:**
- Entry: `/implement-spec`; users see it after `/release`
- Happy path: six scripts → flip → blocking on → replay table
- Moment of truth: `prose_only_count: 2 (cap 2)`, exit 0
- Feedback: claim vs measurement, Gate 4 style
- Error: FAIL blocks; unverifiable continues

---

## For Testing Agents

**Success Criteria:**
1. `uv run --python 3.9 pytest` green on every new test module
2. `bash scripts/eval.sh` Findings: 0 at every story close
3. `--prose-only-blocking` green only after Story 5

**Shadow Paths to Verify:**
- **Happy path:** mechanical fail overrides agent PASS
- **Nil input:** missing spec/story → unverifiable
- **Empty input:** no `--planned`/`--changed` → unverifiable
- **Upstream error:** helper unverifiable → override unverifiable

**Edge Cases:**
- Historical `test_integrity: nothing_inspected` → unverifiable on replay
- Gate 5 on this markdown repo → unverifiable
- Large-drift without PAUSE → drift-format fail

**Coverage Requirements:** new scripts ≥80% lines; every verdict class has a fixture.

**Test Strategy:** pytest fixtures (temp trees, not Writ); bash eval wiring tests; Story 5 replay over the two committed JSON files.
