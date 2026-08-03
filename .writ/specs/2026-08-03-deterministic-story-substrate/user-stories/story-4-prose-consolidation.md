# Story 4: Consolidate the Orchestrator Prose onto the Assembler

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 3

## User Story

**As a** Writ maintainer
**I want to** replace the load-bearing prose parser in `/implement-story` with a single `scripts/story-context.py` invocation, retire the algorithm restatement from the format doc while preserving hint-authoring guidance, and report the measured leanness delta
**So that** context-hint resolution has one authoritative implementation instead of three drifting copies, `story_context_bytes` reflects bytes the pipeline actually delivers, and orchestration policy stays in markdown while parsing and fetching live in code

## Acceptance Criteria

- [ ] Given Story 3's assembler, derived budget, and fixture-level equivalence are in place, when a maintainer reads `commands/implement-story.md` Step 2 after this story, then lines 75–123 (the ~50-line prose parser, 4-row source/fallback table, and 7-row degradation table) are gone and replaced by a `scripts/story-context.py assemble` invocation with a documented JSON output contract (`fetched_context`, `warnings`, `bytes`, `truncated`) — while lines 125–175 (knowledge context) and lines 181–200 (per-gate routing table and its degradation notes) remain untouched.
- [ ] Given the per-gate routing table at `commands/implement-story.md` lines 191–195, when the command file is edited, then the table and its three degradation rows (legacy spec-lite format, missing agent-specific section, empty `fetched_context`) survive verbatim — orchestration policy stays in the command (Business Rule 7).
- [ ] Given the assembler script is missing, exits non-zero, or emits unparseable stdout, when `/implement-story` Step 2 runs, then the orchestrator warns, sets `fetched_context` empty, and proceeds on `spec-lite.md` only — a broken assembler degrades context; it never halts the story (Error & Rescue Map row "Invoke assembler from `/implement-story`", spec Error Experience assembler-fails row).
- [ ] Given `.writ/docs/context-hint-format.md` is rewritten, when a maintainer or `agents/user-story-generator.md` (lines 134–158) consults it, then the doc points at `scripts/story-context.py` as the executable contract instead of restating the parsing algorithm, the stale line-340 premise ("no automated test suite") is removed, and the Generation Guidelines / Validation Rules / authoring examples that agents use to write hints survive intact.
- [ ] Given the consolidation is complete, when a maintainer runs `bash scripts/eval.sh --check=leanness` before and after (or compares against the pre-change baseline), then the leanness delta is reported with `commands/` line decrease and any `scripts/` increase carrying a recorded ADR-019 baseline justification — and the report notes that the 433-line format doc rewrite in unmeasured `.writ/docs/` is real work excluded from the instrument (Business Rule 8).

## Implementation Tasks

- [ ] 4.1 Verify Story 3 gate: run `python3 -m pytest scripts/tests/test_story_context.py`, `bash scripts/eval.sh --check=story-context`, and dogfood the assembler with Story 3's derived `--budget-bytes` across representative specs in `.writ/specs/`; confirm fixture output still matches the prose contract at `commands/implement-story.md` lines 75–123 before any prose is deleted — equivalence is the gate, not assumed.
- [ ] 4.2 Replace `commands/implement-story.md` lines 75–123 with a `scripts/story-context.py assemble --story <path> --budget-bytes <FETCHED_CONTEXT_BUDGET_BYTES>` invocation: map JSON fields to `fetched_context`, `context_warnings` (from `warnings`), and byte report; preserve the informational log for absent hints section and wire truncation warnings from `"truncated": true`; do not alter lines 125–175 or 181–200.
- [ ] 4.3 Add static verification in `scripts/eval-story-context.py` or a dedicated eval check that `commands/implement-story.md` references `story-context.py`, no longer contains the deleted parsing/degradation tables, and still contains the routing table at lines 191–195 with all five gate agents — per technical-spec Verification Strategy "Static" row.
- [ ] 4.4 Rewrite `.writ/docs/context-hint-format.md`: retire the "Parsing Guide (for Orchestrators)" algorithm restatement and manual parsing-validation sections that duplicate the script; replace with a pointer to `scripts/story-context.py` as the executable contract and to `scripts/tests/test_story_context.py` / `bash scripts/eval.sh --check=story-context` for validation; remove the stale line-340 "no automated test suite" premise; preserve "Generation Guidelines (for user-story-generator)", format structure, examples, Validation Rules, and Integration with Pipeline authoring sections so `agents/user-story-generator.md` lines 134–158 remain valid.
- [ ] 4.5 Simulate assembler failure modes (missing script, non-zero exit, malformed stdout) in unit or scenario tests and confirm `/implement-story` prose instructions route to spec-lite-only degradation with warnings — matching Error & Rescue Map row "Invoke assembler from `/implement-story`" and Shadow Paths row "Context assembly" Upstream Error column.
- [ ] 4.6 Record ADR-019 baseline justification in `.writ/leanness-baseline.json` for any net `scripts/` growth and the expected `commands/` shrink; run `bash scripts/eval.sh --check=leanness` and capture the per-surface delta (baseline, current, delta) in the What Was Built record — note explicitly that `.writ/docs/context-hint-format.md` lives outside the measured surface and its rewrite will not appear in the reported delta.
- [ ] 4.7 Run full Tier 1 eval (`bash scripts/eval.sh`), verify `story_context_bytes` is produced by the same code path that delivers context (Moment of Truth), confirm all acceptance criteria pass, and publish the leanness delta report with baseline justification.

## Notes

**The prose being deleted is load-bearing.** `commands/implement-story.md` lines 75–123 are not decoration — they are the running implementation that every `/implement-story` invocation executes today by LLM judgment. A script that is merely *approximately* equivalent silently degrades every downstream gate's context. This is why Story 4 depends on Story 3 rather than being merged into Story 2: the assembler must exist, be budget-enforced, and be proven on fixtures and real specs before the prose is removed (spec Contract "Hardest constraint").

**ADR-019 leanness instrument blind spot.** The 433-line format doc lives in `.writ/docs/`, which ADR-019's leanness instrument does **not** measure. Rewriting it to retire the parsing-algorithm restatement is real consolidation work that will not appear in the reported `commands/`/`scripts/` delta. The leanness report must say so explicitly so the win is not read as smaller than it is (spec Technical Concerns, ADR-019 coverage guard scope).

**Authoring guidance must survive.** Only the parsing-algorithm restatement is retired. `agents/user-story-generator.md` lines 134–158 still generate hints during `/create-spec`; `.writ/docs/context-hint-format.md` must retain Generation Guidelines, Selection Criteria, Quality Rules, format examples, and Validation Rules for generators. The doc's role shifts from "defines parsing" to "defines authoring; script defines parsing."

**Ratchet interaction.** `commands/` shrinking while `scripts/` grows is expected and visible per-surface under ADR-019 — not laundered through an aggregate tolerance. A non-empty `justification` in `.writ/leanness-baseline.json` is required for any `scripts/` increase or Tier 1 warns (Business Rule 8, Error & Rescue Map row "Baseline update").

**Scope boundary.** This story wires the delivery path and retires duplicate prose; it does not change what any gate agent does with its context, alter the routing table's per-agent category filters, or add shell-level enforcement hooks for the assembler invocation.

**Integration points:**

- `commands/implement-story.md` — lines 75–123 out; lines 125–175 and 181–200 intact
- `scripts/story-context.py` — becomes the sole runtime implementation (Business Rule 2)
- `.writ/docs/context-hint-format.md` — authoring contract retained; executable contract delegated to script
- `agents/user-story-generator.md` lines 134–158 — must remain compatible after doc rewrite
- `scripts/eval-leanness.py` — already imports assembler (Story 2/3); no duplicate `resolve_context_hints()`
- `.writ/leanness-baseline.json` — per-surface justification for net surface movement

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Leanness delta reported with baseline justification recorded

## Context for Agents

- **Error map rows:** [Invoke assembler from `/implement-story`, Baseline update]
- **Shadow paths:** [Context assembly]
- **Business rules:** [Graph validity is blocking; context assembly is degrading, One implementation per contract, Legacy stories never break, Orchestration policy stays in the command, Growth in `scripts/` is expected and must be justified in the baseline]
- **Experience:** [Entry Point, Happy Path, Moment of Truth, Error Experience, Feedback Model]
