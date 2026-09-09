# Story 1: CLI + Schema — spec-analyze.py Structural Findings and Findings-JSON Check

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer who needs AC defects visible before implementation without failing the spec package
**I want to** land `scripts/spec-analyze.py check --spec PATH [--findings FILE] [--repo .]` that emits deterministic structural findings and schema-checks orchestrator findings JSON
**So that** empty, unmeasurable, and under-min criteria (and malformed semantic JSON) are named as `pass` / `fail` / `unverifiable` before code exists, without an LLM API in the script, without replacing `ac-trace.py`, and without printing accept / reject / modify-spec

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [x] Given a spec folder of `user-stories/story-*.md` files, when `python3 scripts/spec-analyze.py check --spec PATH [--findings FILE] [--repo .]` runs on Python 3.9 stdlib, then the script owns `empty_criterion` (checked Given/When/Then line with empty body), `unmeasurable_criterion` (Then is only a listed vague phrase such as “works correctly” / “as expected” / “looks good” with no named artifact, path, verdict, or count), and `under_min_criteria` (fewer than 3 `- [ ] Given` / `- [x] Given` lines); those codes are `fail` reasons; `unmeasurable_criterion` under-fires so a clean fixture does not trip it; the script does not import `ac-trace.py` parsers; and `install.sh` is not edited (`scripts/*.py` is already copied). `[AC-1.1]`
- [x] Given `--findings FILE` whose JSON is an array of objects, when the script schema-checks that file, then each object requires `code` (`contradiction` | `gap` | `ambiguity`), `story` (story filename or the literal `spec`), and non-empty `summary`, with optional `ac_ids` whose values match `AC-\d+\.\d+` when present; `[]` is well-formed; unknown `code` or a missing required field prints `fail` with `malformed_findings`; and the script does not call an LLM API. `[AC-1.2]`
- [x] Given a `check` invocation, when stories are readable, findings JSON (if given) is well-formed, and no structural code fired, then the only verdict line is `pass` and the process exits 0; when any structural code fires or findings JSON is malformed, the verdict is `fail` and the process exits 1; when `--spec` is missing or unreadable, or when `--findings` is omitted and no structural code fired, the verdict is `unverifiable` (exit 0), not `fail`; unknown subcommand or bad argv exits 2 on stderr; omitting `--findings` is never itself a fail; and stdout never prints accept, reject, or modify-spec. `[AC-1.3]`
- [x] Given pytest fixtures for pass (clean stories plus well-formed empty-or-clean findings), fail-structural, fail-malformed-json, unverifiable-missing-spec, and unverifiable-no-findings-no-structural, when `uv run --python 3.9 pytest scripts/tests/test_spec_analyze.py` runs, then each fixture asserts the matching verdict line, `reason:` lines when present, a summary line last, and exit 0 / 1 / 2. `[AC-1.4]`
- [x] Given the landed CLI, when stdout is inspected and the module graph is checked, then output matches the Stage 2b helper family (one verdict line, optional `reason:` lines, summary last); `--repo` / `--project` alias to repo root defaulting to `.`; the script is read-only except stdout; it does not replace Step 2.6a / verify-spec 3e/3f `ac-trace.py`; and this story does not edit `commands/create-spec.md` or `commands/verify-spec.md`. `[AC-1.5]`

## Implementation Tasks

- [x] 1.1 Write `scripts/tests/test_spec_analyze.py` (pytest, Python 3.9) with fixtures for pass (clean + well-formed `[]` or clean findings), fail-structural (`empty_criterion`, `unmeasurable_criterion`, `under_min_criteria`), fail-malformed-json (`malformed_findings`), unverifiable-missing-spec, and unverifiable-no-findings-no-structural; assert `check --spec PATH [--findings FILE] [--repo .]`, exit 0/1/2, verdict vocabulary, and that accept / reject / modify-spec never appear `[AC-1.3, AC-1.4, AC-1.5]`
- [x] 1.2 Implement `scripts/spec-analyze.py` (stdlib, Python 3.9, argparse subcommands, `--repo` / `--project` house shape): `check --spec PATH [--findings FILE] [--repo .]`; read story markdown by path only; do not import `ac-trace.py` parsers; do not call an LLM API; unknown subcommand / bad argv → exit 2 `[AC-1.1, AC-1.5]`
- [x] 1.3 Emit structural codes only: `empty_criterion`, `unmeasurable_criterion` (listed vague Then-phrases only; prefer under-firing so the clean fixture stays `pass`), `under_min_criteria` (fewer than 3 checked Given lines); each is a `fail` reason `[AC-1.1]`
- [x] 1.4 Schema-check `--findings` as a JSON array of `{code, story, summary, ac_ids?}` per technical-spec §1; treat `[]` as well-formed; unknown code or missing required field → `malformed_findings` (`fail`) `[AC-1.2]`
- [x] 1.5 Map the verdict table: `pass` exit 0, `fail` exit 1, `unverifiable` exit 0 when `--spec` is missing/unreadable or `--findings` is omitted with no structural hit; print one verdict line, optional `reason:` lines, summary last; never print accept / reject / modify-spec `[AC-1.3, AC-1.5]`
- [x] 1.6 Keep the helper read-only except stdout; leave `commands/create-spec.md`, `commands/verify-spec.md`, `scripts/ac-trace.py`, and `scripts/eval.sh` unchanged in this story `[AC-1.5]`
- [x] 1.7 Verify acceptance criteria: `uv run --python 3.9 pytest scripts/tests/test_spec_analyze.py` green; confirm the five fixture classes, exit 0/1/2, no LLM import, no `ac-trace` import, and a closing commit appends `{date} stage-3: {what changed and why}` to `.writ/decision-log.md` `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

## Notes

**Technical considerations.** Mirror `scripts/ac-trace.py`, `scripts/verdict-provenance.py`, and `scripts/drift-format.py` for argparse, one verdict line, `reason:` lines, and summary last — do not import their parsers. Story files are markdown on disk; parse checkboxes the same way other scripts do (path + text), not via `ac-trace.py`. `--findings` absent still runs the structural scan. Semantic codes exist only inside that JSON.

**Risks.** `unmeasurable_criterion` is a heuristic. Over-firing is a false-positive against the hardest constraint; prefer under-firing and let later precision (Story 3) record misses as gaps, not as `fail` on clean fixtures. `unverifiable` must stay exit 0. This story is advisory-shaped at the CLI only — it does not wire commands.

**Integration.** No story dependencies. Story 2 owns `create-spec` Step 2.6c and the verify-spec advisory check. Story 3 owns `eval.sh` `spec-analyze` and labeled precision fixtures. Do not fold this into `ac-trace.py`. ADR-013: nothing merges, opens a PR, or releases.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [check --spec, check --findings, Structural scan, LLM pass]
- **Shadow paths:** [create-spec 2.6c, verify-spec check]
- **Business rules:** [Advisory for one release, `unverifiable` is not a failed analysis, Do not replace `ac-trace.py`, Hybrid judge, Python 3.9 stdlib, Decision log]
- **Experience:** [`spec.md` → `## 🎯 Experience Design`]

---

## What Was Built

**Implementation Date:** 2026-09-08

### Files Created

1. **`scripts/spec-analyze.py`** (208 lines)
   - `check --spec PATH [--findings FILE] [--repo|--project .]`. Structural codes `empty_criterion`, `unmeasurable_criterion` (listed vague Then-phrases only), `under_min_criteria`. Schema-checks `--findings` JSON. No LLM API. No `ac-trace` import. [AC-1.1, AC-1.2, AC-1.3]
2. **`scripts/tests/test_spec_analyze.py`** — pass / fail-structural / fail-malformed / unverifiable-missing-spec / unverifiable-no-findings. [AC-1.4, AC-1.5]

### Files Modified

None outside the new script and its tests. `create-spec.md`, `verify-spec.md`, `eval.sh`, and `ac-trace.py` left unchanged.

### Implementation Decisions

1. **`--spec` is optional** so a missing flag is `unverifiable` (exit 0), not argparse exit 2. Unknown subcommand still exits 2.
2. **`--findings` omitted + no structural hit → `unverifiable`.** `[]` + clean stories → `pass`.
3. **`unmeasurable_criterion` matches only the listed Then-phrases** after stripping the AC tag and trailing period.

### Test Results

- `uv run --python 3.9 pytest scripts/tests/test_spec_analyze.py` — 14 passed
- Mechanical: arch-check `pass` (proceed); review-override `pass`; drift-format `unverifiable` (no drift-log); docs-check `unverifiable` (`no_public_exports`)

### Review Outcome

**Result:** PASS — 1 iteration. Drift: None.
