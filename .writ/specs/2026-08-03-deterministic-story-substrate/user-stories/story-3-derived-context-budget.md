# Story 3: Empirically Derived Context Budget and Real Measurement

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 2

## User Story

**As a** Writ maintainer
**I want to** derive a `fetched_context` byte budget from measurement across the real spec corpus, enforce it with relevance-ordered truncation that warns but never blocks, and wire `story_context_bytes` to the assembler's actual output
**So that** per-story token cost is bounded and honestly reported rather than unbounded and estimated, and the leanness metric reflects bytes the pipeline actually delivers

## Acceptance Criteria

- [ ] Given the Story 2 assembler exists but no `FETCHED_CONTEXT_BUDGET_BYTES` constant is committed, when a maintainer runs a measurement sweep of `scripts/story-context.py assemble --story <path>` across every `user-stories/story-*.md` under `.writ/specs/`, then a distribution report (min, max, median, high-percentile values, and per-spec outliers) is produced and recorded before any cap constant is chosen — the threshold cannot precede the measurement (Business Rule 4).
- [ ] Given a fixture story whose resolved `fetched_context` total strictly exceeds the derived budget, when `scripts/story-context.py assemble --story <path> --budget-bytes <N>` runs, then the payload retains higher-relevance content first, truncates the remainder, sets `"truncated": true`, emits a warning naming actual and budget bytes, and exits successfully — context assembly degrades, never blocks (spec Error Experience over-budget row).
- [ ] Given a fixture story whose resolved `fetched_context` total is exactly equal to the budget (not strictly greater), when the assembler runs with `--budget-bytes <N>`, then `"truncated": false`, no truncation warning is emitted, and the full payload is returned — the comparison is strictly greater-than per the Interaction Edge Cases table.
- [ ] Given `scripts/eval-leanness.py` computes `story_context_components()` on an unchanged tree, when it measures `context_hints`, then the value comes from the assembler's `bytes.total` field (real delivered bytes) rather than the deleted `resolve_context_hints()` declared-load proxy or the static `KNOWLEDGE_CONTEXT_CAP_BYTES` constant charged as a stand-in for actual usage.
- [ ] Given an unchanged spec tree and story file, when the assembler runs twice with the same `--budget-bytes` value, then stdout JSON is byte-identical — budget enforcement preserves determinism (Business Rule 5).

## Implementation Tasks

- [ ] 3.1 Write failing unit tests in `scripts/tests/test_story_context.py` for budget enforcement: over-budget truncation with `"truncated": true` and warning text, exactly-at-threshold no truncation (strictly-greater comparison), relevance-ordered retention (higher-relevance categories survive first), and byte-identical repeat runs with a budget applied; add an oversized fixture under `scripts/tests/fixtures/`.
- [ ] 3.2 Run the measurement sweep: invoke `scripts/story-context.py assemble` for every `user-stories/story-*.md` across all ~40 specs in `.writ/specs/`, aggregate `bytes.total` per story, and produce a distribution report (min, max, median, p95, outliers) — do not choose or commit a cap constant until this report exists.
- [ ] 3.3 From the measured distribution, choose `FETCHED_CONTEXT_BUDGET_BYTES` above the observed high end (catches pathology, not normal work), implement budget enforcement in `scripts/story-context.py` (`--budget-bytes` now active): truncate lowest-relevance content first, set `truncated` and per-category `bytes`, emit `⚠️ fetched_context truncated (N of M bytes)` warning mirroring the `knowledge_context` posture at `commands/implement-story.md` lines 165 and 174 — warn, never block.
- [ ] 3.4 Refactor `scripts/eval-leanness.py` `story_context_components()`: replace the `context_hints` proxy with the assembler's real `bytes.total` output; update `STORY_CONTEXT_BYTES_NOTE` and the module docstring disclaimer (lines 38–39) to reflect delivered-bytes measurement while preserving the "not consumed tokens" labeling discipline; remove any dead helpers left from the proxy path.
- [ ] 3.5 Extend `scripts/eval-story-context.py` with budget-enforcement scenarios (over-budget truncation, exactly-at-threshold pass-through) and ensure `bash scripts/eval.sh --check=story-context` covers them.
- [ ] 3.6 Record the measured distribution, chosen threshold, and ADR-019 baseline justification for `scripts/` surface growth in `.writ/leanness-baseline.json` (per-surface `justification` string) and the story's What Was Built record — moving budget logic from unmeasured prose into measured `scripts/` is expected growth, not an exemption (Business Rule 8).
- [ ] 3.7 Run `python3 -m pytest scripts/tests/test_story_context.py`, `python3 scripts/eval-story-context.py`, `bash scripts/eval.sh --check=story-context`, and `bash scripts/eval.sh --check=leanness`; verify all acceptance criteria pass and Tier 1 eval stays green (`Findings: 0`).

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

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Measured distribution and chosen threshold recorded in the What Was Built record

## Context for Agents

- **Error map rows:** [Assemble payload, `eval-leanness` calls assembler, Baseline update]
- **Shadow paths:** [Budget enforcement, Leanness measurement]
- **Business rules:** [The budget is derived, never invented, Determinism is a testable property, Growth in `scripts/` is expected and must be justified in the baseline]
- **Experience:** [Moment of Truth, Error Experience (over-budget row)]
