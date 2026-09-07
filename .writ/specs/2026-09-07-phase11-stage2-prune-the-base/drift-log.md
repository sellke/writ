# Drift Log — Phase 11 Stage 2a: Prune the Base

> Parent: [`spec.md`](spec.md)

Deviations recorded during implementation. Per-story detail lives in each
story's `## What Was Built` → *Deviations from Spec*; this file carries the
spec-level entries. Append-only; `spec.md` is never auto-modified. Story 4
numbers from DEV-101 (it ran in parallel with Story 1, which numbers from
DEV-001).

| ID | Story | Severity | Title |
|---|---|---|---|
| DEV-101 | 4 | Medium | `KNOWN_OVER_BUDGET` pin for `implement-story.md` raised 4414 → 5381 in `test_governor_enforcement.py` |
| DEV-102 | 4 | Small | `agents/visual-qa-agent.md` still names the 85/70 match thresholds the command body dropped |

---

## DEV-101 — `KNOWN_OVER_BUDGET` pin raised for `implement-story.md`

**Severity:** Medium · **Story:** 4 · **Found:** 2026-09-07, Gate 4 full-suite run

**Spec said:** the story touches `commands/implement-story.md` frontmatter, `scripts/`, and `eval.sh`; the Risks note foresaw that the `gates:` block grows the command file and said the growth "must not be treated as a pruning target". **Implementation did:** `scripts/tests/test_governor_enforcement.py::ComplianceGateTests` pins each over-budget command's overage and fails on growth; the block plus the Gate 4.5 sentence grew `implement-story.md` 29,374 → 30,341 bytes (+967), so the pin was raised 4414 → 5381 with a dated comment in the file's own convention (the 2026-09-04 and 2026-09-06 updates did the same). **Why it matters:** a test file outside the story's file list was edited; the leanness warning for the file already fired before this story and still does. **Resolution:** ⚠️ flagged; pipeline PASS. `spec.md` unchanged.

## DEV-102 — `agents/visual-qa-agent.md` still carries the thresholds

**Severity:** Small · **Story:** 4 · **Found:** 2026-09-07, Gate 0 review. Task 4.5 scopes the percentage removal to the command body's `#### Gate 4.5` section, which now names no percentage. `agents/visual-qa-agent.md` (outcome, exit criterion, and the PASS / SOFT PASS / FAIL list at lines 132–134) still says 85 / 70. Left as authored — the agent file is outside this story's boundary and the mechanization spec that gives Gate 4.5 a real diff owns the rewrite. `spec-lite.md` amended with one parenthetical.
