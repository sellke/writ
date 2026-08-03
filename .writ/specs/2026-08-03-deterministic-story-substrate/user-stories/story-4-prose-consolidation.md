# Story 4: Consolidate the Orchestrator Prose onto the Assembler

> **Status:** Completed ✅ (2026-08-03)
> **Priority:** High
> **Dependencies:** Story 3
> **Commit:** 8402a6b66d85252ddbac02392333ca0841916a39

## User Story

**As a** Writ maintainer
**I want to** replace the load-bearing prose parser in `/implement-story` with a single `scripts/story-context.py` invocation, retire the algorithm restatement from the format doc while preserving hint-authoring guidance, and report the measured leanness delta
**So that** context-hint resolution has one authoritative implementation instead of three drifting copies, `story_context_bytes` reflects bytes the pipeline actually delivers, and orchestration policy stays in markdown while parsing and fetching live in code

## Acceptance Criteria

- [x] Given Story 3's assembler, derived budget, and fixture-level equivalence are in place, when a maintainer reads `commands/implement-story.md` Step 2 after this story, then lines 75–123 (the ~50-line prose parser, 4-row source/fallback table, and 7-row degradation table) are gone and replaced by a `scripts/story-context.py assemble` invocation with a documented JSON output contract (`fetched_context`, `warnings`, `bytes`, `truncated`) — while lines 125–175 (knowledge context) and lines 181–200 (per-gate routing table and its degradation notes) remain untouched.
- [x] Given the per-gate routing table at `commands/implement-story.md` lines 191–195, when the command file is edited, then the table and its three degradation rows (legacy spec-lite format, missing agent-specific section, empty `fetched_context`) survive verbatim — orchestration policy stays in the command (Business Rule 7).
- [x] Given the assembler script is missing, exits non-zero, or emits unparseable stdout, when `/implement-story` Step 2 runs, then the orchestrator warns, sets `fetched_context` empty, and proceeds on `spec-lite.md` only — a broken assembler degrades context; it never halts the story (Error & Rescue Map row "Invoke assembler from `/implement-story`", spec Error Experience assembler-fails row).
- [x] Given `.writ/docs/context-hint-format.md` is rewritten, when a maintainer or `agents/user-story-generator.md` (lines 134–158) consults it, then the doc points at `scripts/story-context.py` as the executable contract instead of restating the parsing algorithm, the stale line-340 premise ("no automated test suite") is removed, and the Generation Guidelines / Validation Rules / authoring examples that agents use to write hints survive intact.
- [x] Given the consolidation is complete, when a maintainer runs `bash scripts/eval.sh --check=leanness` before and after (or compares against the pre-change baseline), then the leanness delta is reported with `commands/` line decrease and any `scripts/` increase carrying a recorded ADR-019 baseline justification — and the report notes that the 433-line format doc rewrite in unmeasured `.writ/docs/` is real work excluded from the instrument (Business Rule 8).

## Implementation Tasks

- [x] 4.1 Verify Story 3 gate: run `python3 -m pytest scripts/tests/test_story_context.py`, `bash scripts/eval.sh --check=story-context`, and dogfood the assembler with Story 3's derived `--budget-bytes` across representative specs in `.writ/specs/`; confirm fixture output still matches the prose contract at `commands/implement-story.md` lines 75–123 before any prose is deleted — equivalence is the gate, not assumed.
- [x] 4.2 Replace `commands/implement-story.md` lines 75–123 with a `scripts/story-context.py assemble --story <path> --budget-bytes <FETCHED_CONTEXT_BUDGET_BYTES>` invocation: map JSON fields to `fetched_context`, `context_warnings` (from `warnings`), and byte report; preserve the informational log for absent hints section and wire truncation warnings from `"truncated": true`; do not alter lines 125–175 or 181–200.
- [x] 4.3 Add static verification in `scripts/eval-story-context.py` or a dedicated eval check that `commands/implement-story.md` references `story-context.py`, no longer contains the deleted parsing/degradation tables, and still contains the routing table at lines 191–195 with all five gate agents — per technical-spec Verification Strategy "Static" row.
- [x] 4.4 Rewrite `.writ/docs/context-hint-format.md`: retire the "Parsing Guide (for Orchestrators)" algorithm restatement and manual parsing-validation sections that duplicate the script; replace with a pointer to `scripts/story-context.py` as the executable contract and to `scripts/tests/test_story_context.py` / `bash scripts/eval.sh --check=story-context` for validation; remove the stale line-340 "no automated test suite" premise; preserve "Generation Guidelines (for user-story-generator)", format structure, examples, Validation Rules, and Integration with Pipeline authoring sections so `agents/user-story-generator.md` lines 134–158 remain valid.
- [x] 4.5 Simulate assembler failure modes (missing script, non-zero exit, malformed stdout) in unit or scenario tests and confirm `/implement-story` prose instructions route to spec-lite-only degradation with warnings — matching Error & Rescue Map row "Invoke assembler from `/implement-story`" and Shadow Paths row "Context assembly" Upstream Error column.
- [x] 4.6 Record ADR-019 baseline justification in `.writ/leanness-baseline.json` for any net `scripts/` growth and the expected `commands/` shrink; run `bash scripts/eval.sh --check=leanness` and capture the per-surface delta (baseline, current, delta) in the What Was Built record — note explicitly that `.writ/docs/context-hint-format.md` lives outside the measured surface and its rewrite will not appear in the reported delta.
- [x] 4.7 Run full Tier 1 eval (`bash scripts/eval.sh`), verify `story_context_bytes` is produced by the same code path that delivers context (Moment of Truth), confirm all acceptance criteria pass, and publish the leanness delta report with baseline justification.

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

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated
- [x] Leanness delta reported with baseline justification recorded

## Context for Agents

- **Error map rows:** [Invoke assembler from `/implement-story`, Baseline update]
- **Shadow paths:** [Context assembly]
- **Business rules:** [Graph validity is blocking; context assembly is degrading, One implementation per contract, Legacy stories never break, Orchestration policy stays in the command, Growth in `scripts/` is expected and must be justified in the baseline]
- **Experience:** [Entry Point, Happy Path, Moment of Truth, Error Experience, Feedback Model]

---

## What Was Built

**Implementation Date:** 2026-08-03

### Files Modified

- **`commands/implement-story.md`**
  - Replaced the ~49-line prose context-hint parser (former lines 75–123) with a `scripts/story-context.py assemble --story <path> --budget-bytes 21000` invocation, a JSON-field mapping (`fetched_context`/`warnings`→`context_warnings`/`bytes`/`truncated`), and a 3-row assembler-failure degradation table (script missing / non-zero exit / malformed stdout). The routing table and every downstream `fetched_context`/`context_warnings` reference (Gates 0, 1, and 5 "Context routing:" prose, at what were lines 406/510/786) verified content-identical by direct diff — the edit is a single contiguous hunk ending cleanly before `#### Loading Knowledge Context`.
- **`.writ/docs/context-hint-format.md`**
  - Retired "Parsing Guide (for Orchestrators)" and the "Parsing Validation (Task 1.5)" subsection, replacing both with pointers to `scripts/story-context.py` and its tests as the executable contract. Fixed a pre-existing, out-of-task-scope drift (stale `context_hints_parsed`/`context_content_fetched` output names that never matched the command file's real `fetched_context`/`context_warnings`) opportunistically, with a transparent inline callout. Removed the stale "no automated test suite" premise. Added a Version History 2.0 entry. Generation Guidelines, Format Structure, Examples, Validation Rules, and Manual Usage sections preserved byte-for-byte (confirmed zero diff lines).
- **`scripts/eval.sh`**
  - Added 8 new static assertions to `check_story_context()`: requires the assembler invocation and all 5 routing-table gate-agent rows in `commands/implement-story.md`; forbids 2 distinctive strings from the retired prose (regression guard against reintroduction).
- **`scripts/eval-story-context.py`**
  - Added 3 scenarios (6 assertions) using fake wrapper scripts (never the real, unfailable assembler) to prove the documented degrade table is internally sound: missing script, non-zero exit, malformed stdout — each a genuinely distinct code path, independently confirmed non-overlapping.
- **`.writ/leanness-baseline.json`**
  - Hand-extended (not replaced) Story 3's `scripts` justification string; updated lines/chars to 23002/988931.

### Implementation Decisions

1. **Prose replacement preserves load-bearing variable names, not just the routing table.** `fetched_context` and `context_warnings` are read far beyond the routing table (Gates 0/1/5 dispatch prose) — the replacement was required to keep producing these exact identifiers, confirmed by grepping the entire 964-line file, not just the local vicinity of the edit.
2. **Task 4.5 targets what's actually verifiable.** `scripts/story-context.py`'s `main()` guarantees exit 0 unconditionally — it cannot be made to fail for real. The degrade-table test coverage uses fake wrapper scripts to prove the *documented* algorithm is internally sound, explicitly not a claim that an LLM orchestrator will comply with it at runtime (that's not automatable).
3. **Doc rewrite fixed 2 pre-existing drift bugs opportunistically** (stale variable names; stale test-suite premise) — pre-authorized in the coding brief as strictly corrective, not scope creep. Logged as [DEV-005](../drift-log.md).
4. **Legacy per-segment-backtick dialect gap discovered, not fixed.** Task 4.1's dogfooding sweep found 2 pre-2026-08-03 specs (`2026-03-27-context-engine`, `2026-04-24-phase4-production-grade-substrate`, both story-1) using an older extended-reference dialect the current regex doesn't resolve — independently reproduced: exits 0, `fetched_context: {}`, 6 warnings, exactly the contract's designed degradation. Correctly out of Story 4's scope; logged as [DEV-006](../drift-log.md) and filed as `.writ/issues/improvements/2026-08-03-legacy-context-hint-dialect-gap.md`.
5. **Leanness attribution requires disaggregation.** The `commands/` surface's aggregate leanness delta (+162 lines) is dominated by an unrelated, concurrent frontmatter-addition initiative touching all 32 command files (each +5 lines) — Story 4's own isolated edit to `implement-story.md` is net **−3 lines** (53 removed, 50 added). The real consolidation win is the `.writ/docs/context-hint-format.md` rewrite (432→379 lines), which lives entirely outside ADR-019's measured surface (the spec's own predicted "leanness instrument blind spot").

### Test Results

**Verification:** Automated (unit tests + eval scenario emitters + live dogfooding against real spec files), independently re-run by review, testing, and the orchestrator at every stage.
- ✅ 65/65 unit tests (`scripts/tests/test_story_context.py` — unchanged, no assembler logic touched by this story)
- ✅ 58/58 `eval-story-context.py` scenarios (up from 52; 6 new degrade-table assertions confirmed genuinely distinct, non-overlapping)
- ✅ `bash scripts/eval.sh --check=story-context` — 0 findings
- ✅ `bash scripts/eval.sh --check=story-deps` — 16/16, 0 findings (regression clean)
- ✅ `bash scripts/eval.sh --check=leanness` — 0 findings
- ✅ Full `bash scripts/eval.sh` — 1 finding total (`commands/_preamble.md`, 86 vs. 80-line limit) — confirmed pre-existing and unrelated to this story (same unrelated frontmatter-addition initiative referenced in Decision 5)
- ✅ Dogfooded the exact documented invocation against 5 real story files (this spec's story-1/3/4, plus both legacy-dialect specs from Decision 4) — JSON shape and the "malformed category" degrade path both match the newly-documented prose exactly

**Coverage:** No new application logic was written (this story consumes the assembler, never modifies its behavior), so coverage here means contract fidelity — confirmed the documented prose contract matches the real script's behavior across happy-path and malformed-input cases, and confirmed the 8 new static assertions are non-vacuous (each forbidden string verified genuinely absent, each required string verified in its intended context, not an accidental substring hit).

### Review Outcome

**Result:** PASS — 1 review iteration, no recode required

- **Drift:** Small (DEV-005, DEV-006 — both logged to `drift-log.md`, neither required a spec amendment; DEV-006 additionally filed as a follow-up issue)
- **Security:** Clean — no application logic changed; new test-harness subprocess calls use list-form args, no `shell=True`, identical pattern to existing helpers
- **Boundary Compliance:** All changes within Owned/Readable scope; `check_story_deps()` and `scripts/story-context.py` itself confirmed untouched

### Deviations from Spec

See [DEV-005] and [DEV-006] in `drift-log.md` — both Minor, both logged for traceability only (neither violates spec intent, no `spec.md`/`spec-lite.md` amendment needed).

### Lessons Learned

1. **A story that edits its own orchestration playbook needs a diff-based verification step, not a line-number-based one.** Citing "lines 125–175 remain untouched" in the story text was already slightly wrong before any edit happened (actual boundaries were 125–178) and would have been wrong again the moment the edit shifted everything below it. Verifying by content diff ("everything from this header onward is byte-identical") rather than absolute line numbers is the only version of this check that survives the edit it's checking.
2. **"Simulate failure modes" can be a category error when the thing you'd simulate is contractually incapable of failing.** `story-context.py`'s unconditional exit-0 guarantee (a deliberate Story 2/3 design choice) meant Task 4.5's literal phrasing pointed at an untestable scenario. Recognizing this during architecture check — and rewording the deliverable to a static prose-content assertion plus illustrative fake-wrapper scenarios — turned a misleading task into an honest, verifiable one instead of producing tests that would have quietly tested nothing.

### Next Story

None — this is the final story (4 of 4) in `2026-08-03-deterministic-story-substrate`. See the spec's own completion record for the overall spec closure.
