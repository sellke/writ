# Drift Log — Context Engine

> Tracks deviations between spec contract and implementation reality.

## Story 1: Per-Story Context Hints

#### [DEV-001] Orchestrator ACs vs phased delivery
- **Severity:** Medium
- **Spec said:** Story 1 establishes format and generation; Story 4 implements orchestrator parsing
- **Implementation did:** Format + generation complete; AC2-AC4 documented but not runtime-verifiable until Story 4
- **Resolution:** Flagged for review. Story 1 ACs should be reworded to separate format/generation concerns (Story 1) from orchestrator behavior (Story 4)
- **Spec-lite updated:** No (full spec, not spec-lite, needs AC clarification)

#### [DEV-002] Story tasks 1.4–1.5 test approach
- **Severity:** Small
- **Spec said:** "Write tests for hint generation logic" and "Test hint parsing in orchestrator"
- **Implementation did:** Documented validation strategy (golden file comparison, manual verification) in context-hint-format.md
- **Resolution:** Auto-amended — markdown system has no test harness, validation strategy is appropriate
- **Spec-lite updated:** No change needed (implementation note only)
