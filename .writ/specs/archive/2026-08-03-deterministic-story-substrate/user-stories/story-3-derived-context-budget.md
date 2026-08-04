# Story 3: Empirically Derived Context Budget and Real Measurement

> **Status:** Completed ✅ (2026-08-03)
> **Priority:** High
> **Dependencies:** Story 2
> **Commit:** a3f4b129713782c75d136252df6ebaf69ce7eb19

## User Story

**As a** Writ maintainer
**I want to** derive a `fetched_context` byte budget from measurement across the real spec corpus, enforce it with relevance-ordered truncation that warns but never blocks, and wire `story_context_bytes` to the assembler's actual output
**So that** per-story token cost is bounded and honestly reported rather than unbounded and estimated, and the leanness metric reflects bytes the pipeline actually delivers

## Acceptance Criteria

- [x] Given the Story 2 assembler exists but no `FETCHED_CONTEXT_BUDGET_BYTES` constant is committed, when a maintainer runs a measurement sweep of `scripts/story-context.py assemble --story <path>` across every `user-stories/story-*.md` under `.writ/specs/`, then a distribution report (min, max, median, high-percentile values, and per-spec outliers) is produced and recorded before any cap constant is chosen — the threshold cannot precede the measurement (Business Rule 4).
- [x] Given a fixture story whose resolved `fetched_context` total strictly exceeds the derived budget, when `scripts/story-context.py assemble --story <path> --budget-bytes <N>` runs, then the payload retains higher-relevance content first, truncates the remainder, sets `"truncated": true`, emits a warning naming actual and budget bytes, and exits successfully — context assembly degrades, never blocks (spec Error Experience over-budget row).
- [x] Given a fixture story whose resolved `fetched_context` total is exactly equal to the budget (not strictly greater), when the assembler runs with `--budget-bytes <N>`, then `"truncated": false`, no truncation warning is emitted, and the full payload is returned — the comparison is strictly greater-than per the Interaction Edge Cases table.
- [x] Given `scripts/eval-leanness.py` computes `story_context_components()` on an unchanged tree, when it measures `context_hints`, then the value comes from the assembler's `bytes.total` field (real delivered bytes) rather than the deleted `resolve_context_hints()` declared-load proxy or the static `KNOWLEDGE_CONTEXT_CAP_BYTES` constant charged as a stand-in for actual usage.
- [x] Given an unchanged spec tree and story file, when the assembler runs twice with the same `--budget-bytes` value, then stdout JSON is byte-identical — budget enforcement preserves determinism (Business Rule 5).

## Implementation Tasks

- [x] 3.1 Write failing unit tests in `scripts/tests/test_story_context.py` for budget enforcement: over-budget truncation with `"truncated": true` and warning text, exactly-at-threshold no truncation (strictly-greater comparison), relevance-ordered retention (higher-relevance categories survive first), and byte-identical repeat runs with a budget applied; add an oversized fixture under `scripts/tests/fixtures/`.
- [x] 3.2 Run the measurement sweep: invoke `scripts/story-context.py assemble` for every `user-stories/story-*.md` across all ~40 specs in `.writ/specs/`, aggregate `bytes.total` per story, and produce a distribution report (min, max, median, p95, outliers) — do not choose or commit a cap constant until this report exists.
- [x] 3.3 From the measured distribution, choose `FETCHED_CONTEXT_BUDGET_BYTES` above the observed high end (catches pathology, not normal work), implement budget enforcement in `scripts/story-context.py` (`--budget-bytes` now active): truncate lowest-relevance content first, set `truncated` and per-category `bytes`, emit `⚠️ fetched_context truncated (N of M bytes)` warning mirroring the `knowledge_context` posture at `commands/implement-story.md` lines 165 and 174 — warn, never block.
- [x] 3.4 Refactor `scripts/eval-leanness.py` `story_context_components()`: replace the `context_hints` proxy with the assembler's real `bytes.total` output; update `STORY_CONTEXT_BYTES_NOTE` and the module docstring disclaimer (lines 38–39) to reflect delivered-bytes measurement while preserving the "not consumed tokens" labeling discipline; remove any dead helpers left from the proxy path.
- [x] 3.5 Extend `scripts/eval-story-context.py` with budget-enforcement scenarios (over-budget truncation, exactly-at-threshold pass-through) and ensure `bash scripts/eval.sh --check=story-context` covers them.
- [x] 3.6 Record the measured distribution, chosen threshold, and ADR-019 baseline justification for `scripts/` surface growth in `.writ/leanness-baseline.json` (per-surface `justification` string) and the story's What Was Built record — moving budget logic from unmeasured prose into measured `scripts/` is expected growth, not an exemption (Business Rule 8).
- [x] 3.7 Run `python3 -m pytest scripts/tests/test_story_context.py`, `python3 scripts/eval-story-context.py`, `bash scripts/eval.sh --check=story-context`, and `bash scripts/eval.sh --check=leanness`; verify all acceptance criteria pass and Tier 1 eval stays green (`Findings: 0`).

## Notes

**The cap is derived, never invented.** A guessed threshold either never fires (set too high — the budget is theater) or fires constantly (set too low — warnings become noise). Both failure modes destroy the signal. Story 3 opens with the measurement sweep across `.writ/specs/` and records both the distribution and the chosen number so a later reader can verify the cap was measured, not picked (Business Rule 4, spec "The budget is on the wrong artifact").

**Partial retirement of leanness-instrumentation Business Rule 7.** The leanness-instrumentation spec's `story_context_bytes` was a declared-load proxy — it summed what `implement-story.md` says it loads, including charging `KNOWLEDGE_CONTEXT_CAP_BYTES` as a flat constant rather than actual assembled usage. This story narrows that disclaimer: `context_hints` becomes a real measurement of **delivered bytes** from the same assembler code path that produces context. It is still not consumed-token accounting (ADR-019 labeling discipline remains), so `STORY_CONTEXT_BYTES_NOTE` must continue to say so — the proxy label is retired for `fetched_context`, not for the entire metric.

**ADR-019 ratchet interaction.** Budget enforcement adds lines to `scripts/story-context.py` and may extend `eval-leanness.py`. That registers as `scripts/` surface growth under the reduction ratchet. A non-empty `justification` in `.writ/leanness-baseline.json` is required or Tier 1 warns — record the justification as part of this story, not as an afterthought (Business Rule 8, technical-spec Error & Rescue Map "Baseline update" row).

**Scope boundary.** This story derives the budget, enforces truncation in the assembler, and switches leanness measurement to real assembler output. It does **not** wire `/implement-story` Step 2 to call the assembler with the budget (Story 4) or remove the prose parser (Story 4). The `--budget-bytes` flag becomes active here; the command invocation that passes the derived constant lands in Story 4.

**Integration points:**

- `scripts/story-context.py` — budget enforcement, `truncated` flag, relevance ordering
- `scripts/eval-leanness.py` — `story_context_components()`, `STORY_CONTEXT_BYTES_NOTE`, `context_hints` component
- `scripts/eval-story-context.py` / `scripts/eval.sh` — new budget scenarios in `check_story_context`
- `.writ/leanness-baseline.json` — per-surface justification for `scripts/` growth
- `commands/implement-story.md` lines 165, 174 — truncation posture to mirror for `fetched_context`

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated
- [x] Measured distribution and chosen threshold recorded in the What Was Built record

## Context for Agents

- **Error map rows:** [Assemble payload, `eval-leanness` calls assembler, Baseline update]
- **Shadow paths:** [Budget enforcement, Leanness measurement]
- **Business rules:** [The budget is derived, never invented, Determinism is a testable property, Growth in `scripts/` is expected and must be justified in the baseline]
- **Experience:** [Moment of Truth, Error Experience (over-budget row)]

---

## What Was Built

**Implementation Date:** 2026-08-03

### Files Created

1. **`scripts/sweep-story-context-bytes.py`** (153 lines)
   - Committed measurement sweep tool (deliberately not throwaway) — invokes `scripts/story-context.py assemble` as a subprocess against every `user-stories/story-*.md` under `.writ/specs/`, aggregates `bytes.total` per story, and reports min/median/p90/p95/p99/max plus a `heading_mismatch_suspected` flag per story.
   - Committed because the flagged heading-mismatch undercount (below) means this exact script must be re-run once that bug is fixed elsewhere to confirm `FETCHED_CONTEXT_BUDGET_BYTES` still holds — a one-off shell loop would not survive to that day.

### Files Modified

- **`scripts/story-context.py`**
  - Added `FETCHED_CONTEXT_BUDGET_BYTES = 21000` (derivation documented in-code) and `enforce_budget()` (relevance-ordered truncation), wired into `_payload()`/`assemble()`. `--budget-bytes` is now active (previously an inert passthrough from Story 2).
- **`scripts/eval-leanness.py`**
  - Docstring/comment-only update to `STORY_CONTEXT_BYTES_NOTE` and the module docstring, clarifying that `context_hints` is now real assembler-delivered bytes while the rest of `story_context_bytes` remains a declared-load proxy. No logic changed — `assembler_bytes_for_story()` already drove `context_hints` since Story 2's commit `7628bf7`.
- **`scripts/eval-story-context.py`**
  - Added 4 scenario functions (over-budget truncation, exact-threshold boundary, relevance-ordered retention, byte-identical repeats with a budget) — 13 new PASS lines.
- **`scripts/eval.sh`**
  - Replaced the stale `'"truncated": False'` literal check in `check_story_context()` with checks for `FETCHED_CONTEXT_BUDGET_BYTES` and `def enforce_budget(`.
- **`scripts/tests/test_story_context.py`**
  - Added unit tests for budget enforcement (65 total, up from 53): boundary, over-budget, relevance order, zero-budget, byte-identical-with-budget, and two testing-agent-added regression tests (multi-byte-truncation-to-empty, `budget_bytes` inertness on early-return paths).
- **`scripts/tests/test_eval_leanness.sh`**
  - Added a regression scenario proving `context_hints` still equals the assembler's own `bytes.total`.
- **`.writ/leanness-baseline.json`**
  - Hand-edited only the `scripts` surface (lines 19826→22858, chars 841506→979695) with a justification string. `--update-baseline` was deliberately NOT run (it globally resets every surface's justification, which would have laundered unrelated in-flight `commands`/`skills` growth into the baseline).
- **`.writ/docs/leanness-audit-format.md`**
  - Two references to `story_context_bytes` as a pure "declared-load proxy" corrected to point at the (already-accurate) `story_context_bytes_note`, since that characterization went stale once `context_hints` became real measured bytes.

### Implementation Decisions

1. **Measured distribution:** Swept all 170 `story-*.md` files under `.writ/specs/`: min=0, median=0, p90≈0, p95≈2205, p99≈3619, max=10251 bytes. 9 of 170 stories flagged `heading_mismatch_suspected` (their `spec.md` carries a `## 🎯 Experience Design (...)` heading with trailing text that fails `extract_markdown_section()`'s exact-match, silently zeroing affected categories) — the true corpus high end is unmeasured, not just underestimated at the margin.
2. **Threshold heuristic — `FETCHED_CONTEXT_BUDGET_BYTES = 21000`:** 2× the observed max (10,251 × 2 = 20,502), rounded up to the nearest 1,000. The 2× margin (rather than 1× or p99) is explicit, documented compensation for the heading-mismatch undercount above — a bare round-up (→11,000) would sit directly on top of the one real outlier and risk firing on ordinary future growth once that bug is eventually fixed. Logged as [DEV-003](../drift-log.md) since the spec text ("above the observed high end") doesn't itself specify a multiplier.
3. **Relevance order reuses `CATEGORY_ORDER`:** Truncation priority (error_map_rows → shadow_paths → business_rules → experience) reuses the assembler's existing output-order constant rather than inventing a second ordering concept — documented in code as a deliberate implementation choice, not a spec mandate. Logged as [DEV-004](../drift-log.md).
4. **Task 3.4 scope, accurately stated:** The `context_hints` → real-assembler wiring landed in Story 2's commit `7628bf7`, not here (confirmed via `git show 7628bf7`). This story's actual Task 3.4 work was the regression test proving it stays that way, plus correcting the docstrings/note wording — not re-claiming the wiring itself.

### Test Results

**Verification:** Automated (unit tests + eval scenario emitters), independently re-run by review, testing, and the orchestrator at every stage — including an independent re-run of the measurement sweep itself, which reproduced byte-identical distribution numbers.
- ✅ 65/65 unit tests (`scripts/tests/test_story_context.py`, up from 53 pre-Story-3)
- ✅ 52/52 `eval-story-context.py` scenarios (up from 39)
- ✅ `bash scripts/eval.sh --check=story-context` — 0 findings
- ✅ `bash scripts/eval.sh --check=story-deps` — 16/16, 0 findings (regression check — Story 1's territory unaffected)
- ✅ `bash scripts/eval.sh --check=leanness` — 0 findings; `scripts` growth warning resolved via baseline justification; pre-existing unrelated `commands`/`skills` warnings correctly persist untouched
- ✅ `scripts/tests/test_eval_leanness.sh` — 34/34 shell assertions

**Coverage:** Manual branch-coverage walk (no `coverage` tool installed) of `enforce_budget()` and its call sites — every branch (under-budget passthrough, exact-boundary, category-fits-whole, mid-category truncation, multi-byte-truncation-to-empty, zero-remaining-budget skip, `budget_bytes=None` unbounded default, early-return inertness) has a dedicated test. The testing agent found and closed 2 genuine gaps (multi-byte UTF-8 truncation-to-empty at a category boundary; `budget_bytes` inertness on `assemble()`'s 4 early-return paths) — both pinned current-correct behavior, no implementation bugs found.

### Review Outcome

**Result:** PASS (functional) — 1 review iteration, no recode required

- The review agent returned a procedural `FAIL` citing a missing `## What Was Built` section — this is not a defect; per `implement-story.md`'s own Gate 3.5 spec, that section is populated by the orchestrator from the review's own output *after* review passes, exactly as it was for Story 1 and Story 2. All 7 substantive review categories (acceptance criteria, code quality, security, test coverage, integration, boundary compliance, drift analysis) were independently verified clean.
- **Drift:** Small (DEV-003, DEV-004 — both logged to `drift-log.md`, neither required a spec amendment)
- **Security:** Clean — the new sweep tool's subprocess invocation mirrors `eval-leanness.py`'s existing pattern exactly (no `shell=True`, local `glob` paths only); Story 2's path-traversal confinement fix (`resolve_spec_file()`) confirmed byte-for-byte unmodified
- **Boundary Compliance:** All changes within Owned/Readable scope; `scripts/eval.sh` and `.writ/leanness-baseline.json` (shared surfaces with Story 1/2) confirmed additive-only via direct diff

### Deviations from Spec

See [DEV-003] and [DEV-004] in `drift-log.md` — both Small, both logged for traceability only (neither violates spec intent, no `spec.md`/`spec-lite.md` amendment needed).

### Lessons Learned

1. **A "record this in the What Was Built section" task instruction and the pipeline's own gate ordering can appear to conflict** — Task 3.6 reads as if the coding agent should populate the WWB record, but Gate 3.5 (which runs *after* Gate 3 review) is what actually assembles it, sourced from the review agent's own output. A review agent unfamiliar with this ordering will reasonably (but incorrectly) treat the record's absence at review time as a blocking defect. Worth clarifying in the story text for future stories with a similar DoD bullet.
2. **A derived threshold needs its margin justified as explicitly as the measurement itself** — "above the observed high end" alone doesn't specify a multiplier, and an undocumented choice (1×? 2×? p99?) would have been legitimate drift. Anchoring the 2× margin to a named, verifiable defect (the heading-mismatch undercount) rather than an arbitrary safety factor turned a potential invented-threshold problem into a traceable, reproducible one.

### Next Story

**Story 4:** Prose Consolidation — replaces `commands/implement-story.md`'s prose context-hint parser (lines 75-123) with a call to `scripts/story-context.py assemble --budget-bytes 21000`, retiring the last hand-parsed implementation of the context-hint contract and wiring the derived budget from this story into the actual pipeline invocation for the first time.
