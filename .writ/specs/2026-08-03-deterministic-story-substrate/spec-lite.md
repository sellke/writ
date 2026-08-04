# Deterministic Story Substrate (Lite)

> Source: .writ/specs/2026-08-03-deterministic-story-substrate/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Two Python validators + consolidation. `story-deps.py` blocks `/implement-spec` on an invalid story DAG. `story-context.py` becomes the single context-hint implementation, byte-budgeted.

**Implementation Approach:**
- Python 3 logic + bash harness (existing split). Pattern: `spec-deps.py` — stable JSON envelope, `eval.sh` decides FAIL.
- `story-deps.py`: `validate --spec-dir <path> [--json]`. Dep regex from `recommend-state.py:363-366`. Emits topological batches, tie-break by story number.
- `story-context.py`: implements `.writ/docs/context-hint-format.md` — 4 categories, bracketed + extended (`file.md → ## Section`) forms, technical-spec.md primary / spec.md fallback.
- Each script gets `eval-*.py` scenario emitter + `check_*` in `eval.sh` CHECKS array (lines 19-47) + tests in `scripts/tests/`.
- Deduplicate: `recommend-state.py:validate_dag()` imports story-deps; `eval-leanness.py:resolve_context_hints()` (lines 234-253) is deleted and imports story-context.

**Files in Scope:**
- `scripts/story-deps.py`, `scripts/story-context.py` (new)
- `scripts/eval-story-deps.py`, `scripts/eval-story-context.py` (new)
- `scripts/eval.sh` — 2 check functions + CHECKS entries
- `scripts/recommend-state.py` — validate_dag delegates
- `scripts/eval-leanness.py` — story_context_bytes calls assembler
- `commands/implement-spec.md` — blocking gate before Step 2.2
- `commands/implement-story.md` — replace lines 75-123; **keep routing table 191-195**
- `.writ/docs/context-hint-format.md` — point at script, drop stale line 340 premise
- `scripts/tests/` — unit tests both scripts

**Error Handling:**
- Invalid graph → **blocking**, stop before confirmation gate, name story + diagnostic
- Missing hints section / bad category / missing ref / unreadable spec → warn, degrade to spec-lite
- Over budget → truncate by relevance, warn, continue
- Assembler missing or crashing → warn, fall back to spec-lite only

**Integration Points:** `/implement-spec` batching; `/implement-story` Step 2; eval Tier 1 CI; ADR-019 leanness ratchet.

---

## For Review Agents

**Acceptance Criteria:**
1. All 5 error classes (`malformed_dependencies`, `missing_reference`, `self_reference`, `duplicate_reference`, `dependency_cycle`) block `/implement-spec` with a named diagnostic.
2. Story-dep parsing and hint resolution each exist in exactly ONE place after this spec.
3. Assembler matches prose behavior on fixtures for every edge-case-table row.
4. `fetched_context` cap documented with the measured distribution it came from.
5. `commands/` shrinks; `scripts/` growth carries a baseline justification; eval Tier 1 `Findings: 0`.

**Business Rules:**
- **Graph validity blocks; context assembly degrades.** No exceptions either way.
- One implementation per contract — no duplicated parsers survive.
- Error classes match `spec-deps.py` exactly.
- Budget is **derived from measurement**, never invented.
- Determinism is asserted, not assumed (byte-identical repeat runs).
- Legacy stories (no hints section) never break.
- Routing table stays in the command — that's policy, not parsing.
- `scripts/` growth needs a recorded ADR-019 justification.

**Experience Design:**
- Entry: no new user surface — 2 scripts called by existing commands + 2 eval checks.
- Happy path: validate graph → deterministic batches → bounded context per story → gates unchanged.
- Moment of truth: `story_context_bytes` stops being a proxy — same code delivers and measures.
- Error: graph diagnostics mirror `implement-phase`'s; assembler warnings use existing `context_warnings`.

---

## For Testing Agents

**Success Criteria:**
1. Fixtures cover all 5 graph error classes + valid multi-batch graph.
2. Fixtures cover all 6 degradation rows from the edge-case table.
3. Repeated runs on unchanged tree → byte-identical output (both scripts).
4. ≥80% coverage on both new scripts (real Python, unit-testable).

**Shadow Paths to Verify:**
- **Happy:** valid graph → batches; hints present → bounded fetched_context.
- **Nil:** no `## Context for Agents` section → spec-lite only, informational log.
- **Empty:** `[]` brackets → skip category, valid, no warning.
- **Upstream error:** `spec.md`/`technical-spec.md` unreadable → warn, degrade, never halt.

**Edge Cases:**
- Cycle spanning 3+ stories → diagnostic names the full cycle path
- `Dependencies: Story 1, Story 1` → duplicate_reference
- Category prefix typo (`Eror map rows`) → skip + warn
- Malformed bracket (`[a, b`) → skip category + warn
- Over-budget fetched_context → truncate by relevance + warn, story still runs
- Assembler absent → `/implement-story` proceeds on spec-lite

**Verification Strategy (methodology repo):**
- Both scripts are real code → unit tests + `eval-*.py` scenario emitters wired into `eval.sh`.
- Command-file rules verified by eval static checks + dogfooding on this repo's own specs.
