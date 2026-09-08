# User Stories — Phase 11 Stage 2b: Mechanize the Gates

> Spec: [`../spec.md`](../spec.md) · Origin: [Goal Card](../../../issues/goals/2026-09-05-writ-contract-and-verifier-layer.md) (Stage 2b) · Evidence: [assessment](../../../product/2026-09-05-goldilocks-assessment.md) §2.3, §3 Mechanism 2, §5 Step 3

## Summary

| # | Story | Status | Priority | Deps | AC | Tasks | Progress |
|---|---|---|---|---|---|---|---|
| 1 | [Gate 3 Review Override — review-override.py Re-derives PASS/FAIL from ac-trace + test-integrity](story-1-gate3-review-override.md) | Completed ✅ | High | — | 5 | 7 | 7/7 |
| 2 | [Gate 0 Architecture Re-derivation — arch-check.py Re-derives PROCEED/CAUTION, Never ABORT](story-2-gate0-arch-rederive.md) | Completed ✅ | High | — | 5 | 6 | 6/6 |
| 3 | [Gate 5 Docs Check — docs-check.py Diffs Documented Symbols Against Changed Exports](story-3-gate5-docs-check.md) | Completed ✅ | High | — | 5 | 6 | 6/6 |
| 4 | [Gate 0.5 + 2.5 Classifiers — boundary-map.py and change-surface.py from git + path heuristics](story-4-boundary-and-surface-classifiers.md) | Completed ✅ | Medium | — | 5 | 6 | 6/6 |
| 5 | [Gate 3.5 Format + Flip + Watch — drift-format.py, prose-only-blocking, runner watch field, baseline replay](story-5-drift-format-flip-and-watch.md) | Not Started | High | 1, 2, 3, 4 | 5 | 7 | 0/7 |

**Total:** 5 stories · 25 acceptance criteria · 32 tasks · 25/32 complete (78%)

## Dependency Graph

```
Story 1 (Gate 3 override) ──┐
Story 2 (Gate 0 arch)     ──┤
Story 3 (Gate 5 docs)     ──┼── Story 5 (3.5 format + flip + watch + replay)
Story 4 (0.5 + 2.5 maps)  ──┘
```

- **Batch 1 (parallel):** Stories 1–4 completed 2026-09-08. Exclusive scripts were authored concurrently; shared `implement-story.md` / `eval.sh` wiring is sequential in one checkout (DEV-001).
- **Story 5** needs the four scripts and their frontmatter `script:` lines in place before it flips `--prose-only-blocking` and replays the sixteen committed baseline records.
- **No revert range.** This spec does not keep-or-revert. The background-subagent drop is a watch field on the runner, not a story that changes spawn behavior.

## Prerequisites outside this repo

None. Proof is fixtures plus read-only replay of `.writ/eval/baselines/2026-09-06-claude-fable-5-1.json` and `2026-09-07-claude-fable-5-1.json`. No Fable 5.1 eight-run, no `~/Projects/yuss` checkout.
