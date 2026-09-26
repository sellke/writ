# Story 4: Gate 0.5 + 2.5 Classifiers — boundary-map.py and change-surface.py from git + path heuristics

> **Status:** Completed ✅
> **Commit:** dda5623edcac6b435be25d005e3f4c4239cc5c17
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** Writ maintainer who needs the advisory boundary map and change-surface class to be checkable artifacts instead of inline LLM classifications
**I want** `scripts/boundary-map.py compute` and `scripts/change-surface.py classify` to emit a JSON ownership map and a four-class surface label from the story file, optional Check 5 overlap, and path heuristics, then have Gate 0.5 and Gate 2.5 run those scripts and pass stdout onward
**So that** Gates 1 and 3 consume the same artifacts they already take, the maps stay advisory (no hard file locking), and later replay can re-derive both without inventing a new gate number

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.5

- [x] Given a well-formed story file and `--repo .`, when `python3 scripts/boundary-map.py compute --story <path> --repo .` runs with `--overlap` pointing at a Check 5 overlap table and again with overlap omitted, then stdout is JSON `{owned, readable, out_of_scope}` (no files written), overlap-present merges shared paths per `skills/boundary-map-computation/SKILL.md`, overlap-absent degrades to owned = paths named in the story, readable = [], out_of_scope = [], and the process exits 0 `[AC-4.1]`
- [x] Given `boundary-map.py compute`, when the story file is malformed, then it exits 1, and when required flags are missing or usage is otherwise invalid, then it exits 2 `[AC-4.2]`
- [x] Given changed-file lists that match the four classes in `skills/change-surface-classification/SKILL.md`, when `python3 scripts/change-surface.py classify --changed <file>…` runs as path heuristics (not an LLM), then it prints exactly one of `style-only` / `single-component` / `cross-component` / `full-stack` and exits 0, and when `--changed` is empty or omitted, then it exits 2 `[AC-4.3]`
- [x] Given `#### Gate 0.5: Boundary Computation` and `#### Gate 2.5: Change Surface Classification` in `commands/implement-story.md`, when those bodies are read after this story, then each runs its script (0.5 → `boundary-map.py compute`, 2.5 → `change-surface.py classify`), passes stdout to Gates 1 and 3 as `boundary_map` / `change_surface` the same way today, and the maps stay advisory — no hard file locking and no new gate numbers `[AC-4.4]`
- [x] Given `commands/implement-story.md` frontmatter and `scripts/eval.sh` after this story, when the `gates:` block is read, then `gate0_5_boundary` names `script: scripts/boundary-map.py` and `gate2_5_surface` names `script: scripts/change-surface.py`, eval registers `boundary-map` and `change-surface` (findings via `add_finding`, not count-blocking), and `--prose-only-blocking` is still not passed `[AC-4.5]`

## Implementation Tasks

- [x] 4.1 Write `scripts/tests/test_boundary_map.py` and `scripts/tests/test_change_surface.py` (pytest, Python 3.9): overlap-present vs overlap-absent JSON maps; malformed story → exit 1; usage → exit 2; one fixture per surface class; empty `--changed` → exit 2; plus bash eval-wiring tests in the shape of `scripts/tests/test_eval_verdict_provenance.sh` `[AC-4.1, AC-4.2, AC-4.3, AC-4.5]`
- [x] 4.2 Implement `scripts/boundary-map.py` (`compute --story PATH --repo . [--overlap PATH]`, stdlib): extract owned paths from the story’s tasks / files-in-scope; merge optional assess-spec Check 5 overlap; degrade when overlap is absent; print JSON only; exit 0 / 1 / 2 per technical-spec §4. How lives in `skills/boundary-map-computation/SKILL.md` — do not restate the skill as a second algorithm `[AC-4.1, AC-4.2]`
- [x] 4.3 Implement `scripts/change-surface.py` (`classify --changed FILE …`, stdlib): apply the skill’s six-step path heuristic (style-only → single-component → cross-component → full-stack; classify up when ambiguous); print the class on stdout; exit 0 with a class, exit 2 when no files. Prefer this second small file over a combined wrapper `[AC-4.3]`
- [x] 4.4 Wire Gate 0.5 (~line 179) and Gate 2.5 (~line 224) in `commands/implement-story.md` to invoke the scripts and pass stdout to Gates 1 and 3 as today; set frontmatter `gate0_5_boundary: script: scripts/boundary-map.py` and `gate2_5_surface: script: scripts/change-surface.py`; keep headings and ids unchanged; do not add file locking `[AC-4.4, AC-4.5]`
- [x] 4.5 Register `boundary-map` and `change-surface` in `scripts/eval.sh` `CHECKS=(...)` (one check per script, `add_finding` / `add_note`, not count-blocking); do not pass `--prose-only-blocking` — that flip is Story 5 `[AC-4.5]`
- [x] 4.6 Verify all acceptance criteria: `uv run --python 3.9 pytest` on the new test modules green, bash eval-wiring tests green, `bash scripts/eval.sh` Findings 0, and append `{date} stage-2b: Story 4 — boundary-map.py compute + change-surface.py classify land; Gate 0.5/2.5 pass stdout; maps stay advisory` to the completion commit `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`

## Notes

**Technical considerations.** Two small files matching the two gate ids, not one mega-verifier. Both CLIs are public surface (`compute` / `classify`). Python 3.9 stdlib; exit 0/1/2 as technical-spec §4 — well-formed map or printed class is exit 0 (data, not a `pass`/`fail` verdict line); malformed story is exit 1; usage / no files is exit 2. `install.sh` already copies `scripts/*.py`. Frontmatter `script:` paths go on in this story so provenance stays truthful mid-spec; Story 5 still owns the `--prose-only-blocking` flip and the eight-script / two-prose-only final block.

**Skills vs scripts.** `skills/boundary-map-computation/SKILL.md` and `skills/change-surface-classification/SKILL.md` own how the map and class are derived. This story owns the scripts and when Gates 0.5 / 2.5 run them. The skill’s markdown schema is the algorithm; the script’s checkable artifact is JSON / a single class token on stdout.

**Risks.** Overlap-absent degrade must not invent readable or out-of-scope entries. Path heuristics will mis-rank some diffs; that is acceptable — classify up when ambiguous, and the class remains advisory. Do not treat these scripts as Gate 4-style verdict overrides; they feed Gates 1 and 3 the same way the inline steps do today.

**Integration.** No story dependencies. Story 2 may later pass a `--boundary` file into `arch-check.py`; this story does not implement that consumption. Story 5 must not be required to flip `--prose-only-blocking`. ADR-013: nothing merges, opens a PR, or releases.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [boundary-map.py compute, change-surface.py classify]
- **Shadow paths:** [Happy path]
- **Business rules:** [No new gate numbers, Python 3.9 stdlib, ADR-013 holds, Decision log]
- **Experience:** [Happy path (step 4: 0.5 and 2.5 emit maps), Feedback model (stdout passed as today), Error experience (maps stay advisory; no new control flow)]

---

## What Was Built

**Implementation Date:** 2026-09-08

### Files Created

1. **`scripts/boundary-map.py`** (236 lines) — `compute --story --repo [--overlap]`. JSON `{owned, readable, out_of_scope}`; writes nothing. Overlap-absent: owned = named paths, readable/out_of_scope empty.
2. **`scripts/change-surface.py`** (191 lines) — `classify --changed`. Path heuristics; classify up when ambiguous.
3. **`scripts/tests/test_boundary_map.py`** (197 lines), **`scripts/tests/test_change_surface.py`** (137 lines), **`scripts/tests/test_eval_boundary_map.sh`** (270 lines). [AC-4.1–AC-4.5]

### Files Modified

- **`commands/implement-story.md`** — `gate0_5_boundary` / `gate2_5_surface` script paths; Gate 0.5/2.5 invoke the scripts and pass stdout; maps stay advisory.
- **`scripts/eval.sh`** — `boundary-map` / `change-surface` checks.
- **`scripts/tests/test_governor_enforcement.py`** — `implement-story.md` overage 5381 → 8554.

### Implementation Decisions

1. **Two small files, not one mega-verifier.**
2. **`out_of_scope` stays `[]` unless overlap data names it** — do not enumerate the tree.

### Test Results

18+ pytest on the two modules, bash harness 8/8. Full suite 1135 passed, 1 skipped. `eval.sh` Findings 0.

### Review Outcome

**Result:** PASS — 1 iteration. Drift: Medium (DEV-001). Maps advisory; no file locking.
