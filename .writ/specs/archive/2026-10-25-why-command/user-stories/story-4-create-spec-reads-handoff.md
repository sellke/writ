# Story 4: `/create-spec` Reads the `/why` Handoff

> **Status:** Completed ✅
> **Commit:** f9569cb60b6718de44f36976ea49992fc15257c4
> **Priority:** High
> **Dependencies:** Story 1, Story 2

## User Story

**As a** developer who ran `/why` before planning a change
**I want to** have `/create-spec` discovery pick up the Preserve / Change / Avoid / Risk list on its own
**So that** the contract keeps what the history says to keep, and discovery does not re-ask what `/why` already settled

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.4

> **Verified by:** AC-4.4 — dogfood fixture question 4 and the `/create-spec` Steps 1.1 and 1.2 run in What Was Built → Dogfood Fixture (AC-4.4), with the saved record `.writ/research/2026-10-25-why-writ-confirmation-four-options.md`

- [x] Given `commands/create-spec.md` Phase 1, when its headings are read, then `#### Step 1.2: Read a `/why` Handoff` sits after Step 1.1 and before Step 1.3, and its section searches the conversation, a file the invocation names, and `.writ/research/*-why-*.md` records whose `Subject` or `Change` line shares a keyword with the feature idea, and says to skip the step when none is found `[AC-4.1]`
- [x] Given that Step 1.2 section and `commands/why.md`, when the seam test compares them, then both contain the literal `## Preserve / Change / Avoid / Risk`, and Step 1.2 maps Preserve to Business Rules, Change to the Deliverable, Avoid to Scope Boundaries → Excluded, and Risk to Technical Concerns, keeping each item's tier and citing the record `[AC-4.2]`
- [x] Given `scripts/tests/test_governor_enforcement.py`, when the full test suite runs, then `KNOWN_OVER_BUDGET["commands/create-spec.md"]` equals the file's measured overage, Step 1.2 added under 700 bytes, and a dated comment above the entry names this spec and the reason, matching the earlier entries' form `[AC-4.3]`
- [x] Given dogfood fixture question 4, when `/why` answers it and `/create-spec` then runs Steps 1.1 and 1.2 in Plan Mode, then `/why` saved a record under `.writ/research/` whose last `##` section is the handoff, the draft contract carries its Preserve item into Business Rules and its Risk item into Technical Concerns with the record cited, and no file is written under `.writ/specs/` `[AC-4.4]`

## Implementation Tasks

- [x] 4.1 Write the failing test first. Add `test_create_spec_reads_handoff` to `scripts/tests/test_why_command.py` per technical-spec.md → Tests, reading the heading literal from `commands/why.md` rather than repeating it. Run it and confirm it fails on the missing step `[AC-4.1, AC-4.2]`
- [x] 4.2 Grep `scripts/` for pins on `Step 1.1` and `Step 1.3` in `commands/create-spec.md`. Then insert Step 1.2 with the text in technical-spec.md → `/create-spec` Step 1.2. Change no other step `[AC-4.1, AC-4.2]`
- [x] 4.3 Measure the file with `wc -c commands/create-spec.md`. Re-pin `KNOWN_OVER_BUDGET["commands/create-spec.md"]` in `scripts/tests/test_governor_enforcement.py` to the new overage, with a dated comment in the form `# 2026-MM-DD (2026-10-25-why-command Story 4): 13654 -> <new>; Step 1.2 reads a /why handoff.` Stop if the step added 700 bytes or more and shorten it `[AC-4.3]`
- [x] 4.4 Add the `commands/create-spec.md` heading row for ``Step 1.2: Read a `/why` Handoff`` to `ROWS` in `scripts/eval-command-structure.py` `[AC-4.1]`
- [x] 4.5 Regenerate the plugin trees with `python3 scripts/gen-platform-trees.py` and confirm `--check` prints `pass` `[AC-4.1]`
- [x] 4.6 Run dogfood fixture question 4. Follow `commands/why.md` to answer it and save the record. Then follow `commands/create-spec.md` Steps 1.1 and 1.2 only, in Plan Mode, for "add a fifth option to /writ's confirmation", and confirm the draft contract carries the Preserve and Risk items with the record cited. Write no spec files. Record the record path and the carried items in What Was Built `[AC-4.4]`
- [x] 4.7 Verify. Run `uv run --python 3.9 pytest` alone, then the bash test loop, then `bash scripts/eval.sh` outside any sandbox. Confirm 0 failures and 0 findings `[AC-4.1, AC-4.2, AC-4.3, AC-4.4]`

## Notes

- **Budget.** `commands/create-spec.md` is the tree's largest command and is pinned over budget. Every earlier growth re-pinned `KNOWN_OVER_BUDGET` with a dated disclosure. Do not trim other steps to offset; they are outside this story.
- **No new gate.** Step 1.2 adds no AskQuestion. Under `--recommend`, a carried section is evidence for the recommendation log like any other.
- **Modes.** `--from-issue` and `--from-prototype` replace Phase 1, so Step 1.2 does not run there. That is in scope boundaries as excluded; do not add it.
- **Fixture record.** Keep the saved record under `.writ/research/` as evidence. It is a real why record about Writ.
- **Parallel with Story 3.** Story 3 edits `commands/writ.md`, the prompting guide, and two existing test files. This story touches none of them.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Find handoff in create-spec, Save why record]
- **Shadow paths:** [Change follows, Happy path]
- **Business rules:** [Fixed handoff shape, The handoff maps into the contract, Saved record, Budgets, Generated files are regenerated]
- **Experience:** [Output Shape]

---

## What Was Built

**Implementation Date:** 2026-10-25

### Files Created

1. **`.writ/research/2026-10-25-why-writ-confirmation-four-options.md`** — the why record from dogfood fixture question 4, kept as evidence. Header (`Asked`, `Subject`, `Change`, `Question`), the answer at `Recorded`, and `## Preserve / Change / Avoid / Risk` as its last `##` section.

### Files Modified

- **`commands/create-spec.md`** — `#### Step 1.2: Read a `/why` Handoff` inserted between Step 1.1 and Step 1.3, text copied from technical-spec.md → `/create-spec` Step 1.2. 38,614 → 39,169 bytes (+555, under the 700-byte limit). No other step changed; no AskQuestion added.
- **`scripts/tests/test_governor_enforcement.py`** — `KNOWN_OVER_BUDGET["commands/create-spec.md"]` 13654 → 14209 (39,169 − 24,960) with the dated comment `# 2026-10-25 (2026-10-25-why-command Story 4): 13654 -> 14209; Step 1.2 reads a /why handoff.`
- **`scripts/eval-command-structure.py`** (`ROWS`) — `commands/create-spec.md` heading ``Step 1.2: Read a `/why` Handoff`` (`check_command_structure`).
- **`scripts/tests/test_why_command.py`** — `test_create_spec_reads_handoff`: reads the heading literal from `commands/why.md`, checks Step 1.2's position, its three search places, the `Subject` or `Change` keyword match, the four mappings, the keep-tier-and-cite sentence, and the skip sentence (AC-4.1, AC-4.2).
- **`cursor/plugin/commands/create-spec.md`, `plugins/writ/commands/create-spec.md`** — regenerated by `python3 scripts/gen-platform-trees.py`.

### Implementation Decisions

1. **Pins grepped first** — no file under `scripts/` pinned Step 1.1 or Step 1.3 text, so inserting Step 1.2 moved no other pin.
2. **Record dated by the session's local date** — 2026-10-25; the first draft used the UTC date, corrected after Gate 3 review.
3. **Record tiers checked against the tier rules** — Gate 3 review lowered the Change item to `Inferred` (it concludes from Business Rule 4 and DEV-007 rather than quoting them) and moved the test claim's source from the commit message to DEV-007's Resolution, which names the test.

### Dogfood Fixture (AC-4.4)

`/why "Why does /writ's confirmation offer at most four options? I want to add a fifth."`, followed by `commands/why.md`:

- **Answer:** Claude Code's question tool takes two to four options per question, and the front-door UAT saw the widget show only four, so the confirmation was cut from up to seven options to the proposed route, two alternatives, and "Not what I meant". — Recorded
- Ledger source: `.writ/specs/2026-10-22-front-door/spec.md` Business Rule 4 and `.writ/specs/2026-10-22-front-door/drift-log.md` DEV-007. Git: `00f8261` (Step 3 created), `9d75383` (cut to four). No `refs/notes/writ` note. MCP: not read; the ledger answered at Recorded.
- A change followed, so Step 6 saved `.writ/research/2026-10-25-why-writ-confirmation-four-options.md`.

Then `commands/create-spec.md` Steps 1.1 and 1.2 only, in Plan Mode, for "add a fifth option to /writ's confirmation":

- Step 1.1 context scan: `.writ/specs/2026-10-22-front-door/` is the related spec; no files written.
- Step 1.2 found the record by glob `.writ/research/*-why-*.md`: its `Change` line is the feature idea word for word, and its `Subject` line shares `/writ` and `confirmation`.
- Draft contract carried from the record, each item citing `.writ/research/2026-10-25-why-writ-confirmation-four-options.md`:
  - **Business Rules** (Preserve): at most four options in the one AskQuestion, because Claude Code's question tool renders two to four (Recorded); "Not what I meant" stays and the prompt names the routes left out (Recorded).
  - **Deliverable** (Change): a fifth choice enters as a replacement for one of the two alternatives or in the "Other routes" line, not as a fifth option (Inferred).
  - **Scope Boundaries → Excluded** (Avoid): offering every route as its own option (Recorded).
  - **Technical Concerns** (Risk): the question tool drops or truncates a fifth option (Recorded); `test_confirmation_fits_four_options` fails on a fifth option (Recorded).
- Discovery would not re-ask the option cap. No file was written under `.writ/specs/`.

### Test Results

**Verification:** Automated, test-first (`test_create_spec_reads_handoff` red on the missing step; green after the insert).
**Coverage:** Not measured by the script (no coverage report; markdown and test changes only).

- ✅ Targeted: `uv run --python 3.9 pytest -q scripts/tests/test_why_command.py scripts/tests/test_governor_enforcement.py scripts/tests/test_front_door.py` → 80 passed.
- ✅ Full run with Stories 3 and 4 in the tree: `uv run --python 3.9 pytest -q` → 3071 passed, 2 skipped; bash test loop → 0 FAIL; `bash scripts/eval.sh` → Findings 0, Run errors 0. Final spec-level run recorded in the execution state.
- ✅ Gate 0 arch-check: pass (rederived proceed). Gate 2: no linter configured; arch-lint: none — see .writ/docs/architecture-lint.md; build-smoke unverifiable (unsupported_stack). Gate 2.5: cross-component, 3 crossings (two regenerated plugin copies and the dogfood record, which task 4.6 names), route review-agent. Gate 3 review-override: pass. Gate 3.5 drift-format: pass. Gate 4 coverage: unverifiable (no_coverage_report); authenticity: pass. Gate 4.5 app-verify: unverifiable (no_recipe). Gate 5 docs-check: unverifiable (no_public_exports).

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** None
- **Security:** Clean (markdown and tests)
- **Boundary Compliance:** 3 crossings, all named by the story's tasks
- gate3-route: review-agent (outside_boundary cursor/plugin/commands/create-spec.md; outside_boundary plugins/writ/commands/create-spec.md; outside_boundary .writ/research/2026-10-25-why-writ-confirmation-four-options.md). Stories 3 and 4 were reviewed in one review-agent pass.
