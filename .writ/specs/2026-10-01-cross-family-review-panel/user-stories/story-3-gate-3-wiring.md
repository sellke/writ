# Story 3: Gate 3 Wiring, `--panel`, and Eval Pins

> **Status:** Completed ✅
> **Commit:** 6590a936ad63b4ae09492a734e09c645717ddec5
> **Priority:** High
> **Dependencies:** Story 1, Story 2

## User Story

**As a** developer using Writ on my own project (and the Writ maintainer)
**I want to** have `/implement-story` convene the cross-family review panel at Gate 3 on risky stories (or when I pass `--panel`), turn a consensus finding into a Gate 3 FAIL, and leave every other outcome as a printed note
**So that** a finding two vendors agree on can block a story the session's own model passed, while today's Gate 3 verdict is never weakened and a project without the config line sees byte-for-byte the same Gate 3

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [x] Given `commands/implement-story.md` and `commands/implement-story.lean.md`, when Story 3 lands, then each carries exactly one `**Review panel (opt-in).**` paragraph placed directly after the `**Risk route:**` paragraph, worded per technical-spec.md → Gate 3 Wiring (Story 3): trigger on `review-panel.py status --platform <origin platform>` printing `pass` (so Claude Code and Codex print the one skip line instead of spawning and dropping) and `gate3_route` naming `review-agent` or `--panel`; same prompt and inputs, `readonly`, `model: <slug>`, plus the one exclusion line; `review-panel: dropped` for rejected or empty reviewers; `review-panel.py tally` after `review-override.py`. No new heading, no new `gates:` frontmatter entry, and no `Task(` marker with an `*-agent` stem outside `spawn-cap.py` `ALLOWED_STEMS` is introduced `[AC-3.1]`
- [x] Given a panel `tally` verdict, when Gate 3 combines it with the primary agent's result, then `block` is a Gate 3 FAIL that takes the existing recode path and increments `evaluator_fail_count` and the shared review loop exactly once even when the primary also failed; on a primary PAUSE, Gate 3.5 presents its unchanged options with the block lines listed and accept still recodes; under `--review-only --panel` a block ends the run; `advisory`, `pass`, `unverifiable`, `skipped`, and `off` print their lines and continue; and the paragraph states the panel never changes the Gate 3 agent's verdict and never marks a story `⚠️ DEGRADED` `[AC-3.2]`
- [x] Given the Invocation table and Step 4 item 8, when Story 3 lands, then the table gains a `/implement-story story-3 --panel` row (convene the panel regardless of route; needs the config line; usage error with `--quick`), the `--quick` conflict is stated as a usage error before any gate, and item 8's report list names the `review-panel:` lines beside `gate3-route:`; with no `- **Review Panel:**` line in `.writ/config.md`, no new step executes and Gate 3 behaves exactly as today `[AC-3.3]`
- [x] Given `scripts/eval.sh`, when `bash scripts/eval.sh --check=review-panel` runs, then `check_review_panel` (registered in the `CHECKS` list beside `jev-judge` and `spawn-cap`) reports a finding if `scripts/review-panel.py` is missing, if `status --repo . --origin <name>` does not parse, if the consensus tally fixture does not exit 1, or if the single-vendor fixture does not exit 0; and `require_literal` pins hold the Gate 3 paragraph in both command files and each adapter's panel row — with each new pin shown to bite by one recorded mutation that turns it into a finding `[AC-3.4]`
- [x] Given `scripts/tests/test_governor_enforcement.py`, when Story 3 lands, then `"commands/implement-story.md"` is re-pinned from `11110` to the new measured value with a dated disclosure comment naming `2026-10-01-cross-family-review-panel` Story 3 ("Inline prose, no new step, gate, or spawn site. Acknowledged, not exempted."), offset by trims of duplicated Gate 3 prose where possible, and `uv run pytest`, `uv run --python 3.9 pytest`, the bash tests, and `bash scripts/eval.sh` (outside the sandbox) all pass with Findings 0 `[AC-3.5]`

## Implementation Tasks

- [x] 3.1 Write failing tests first: add `check_review_panel` with its `require_literal` pins (Gate 3 paragraph opener and the `block is a Gate 3 FAIL` sentence in `implement-story.md` and `.lean.md`, the `--panel` Invocation row, the `review-panel:` report entry, each of the four adapter panel rows from Story 1) and the two tally fixture probes reusing Story 2's `scripts/tests/fixtures/review-panel/` consensus and single-vendor outputs; register `review-panel` in the `CHECKS` list next to `jev-judge` / `spawn-cap`, modeled on `check_jev_judge`; confirm `--check=review-panel` reports findings before the prose lands `[AC-3.1, AC-3.4]`
- [x] 3.2 Insert the `**Review panel (opt-in).**` paragraph in `commands/implement-story.md` directly after the `**Risk route:**` paragraph (before `**`--full-pipeline`:**`), using the technical spec's text; keep it inline prose with no heading, no `Task(` marker, and no new agent name, and confirm `python3 scripts/spawn-cap.py check --command commands/implement-story.md` still passes `[AC-3.1, AC-3.2]`
- [x] 3.3 Add the `--panel` Invocation row and extend the mutual-exclusion sentence so `--panel --quick` is a usage error before any gate; add `review-panel:` beside `gate3-route:` in Step 4 item 8's report list; check that the Pipeline control flow's two-fail escalation sentence still reads correctly with a panel block counting as a Gate 3 FAIL (after escalation `review-agent` is primary and the panel still runs) without adding a sentence unless it is needed `[AC-3.2, AC-3.3]`
- [x] 3.4 Mirror the paragraph, row, and report entry into `commands/implement-story.lean.md` at the matching positions; run `uv run pytest scripts/tests/test_lean_commands.py` to confirm heading parity and that no `gates:` frontmatter entry changed in either file `[AC-3.1, AC-3.3]`
- [x] 3.5 Measure the new byte count of `commands/implement-story.md`, trim duplicated Gate 3 / Gate 2.5 prose where meaning is preserved, and re-pin `"commands/implement-story.md": 11110` in `scripts/tests/test_governor_enforcement.py` with a dated disclosure comment in the existing style (`Updated 2026-10-NN (spec 2026-10-01-cross-family-review-panel, Story 3): …`); if `2026-10-01-behavioral-verification` Story 4 has landed, rebase on its value instead `[AC-3.5]`
- [x] 3.6 Verify acceptance criteria and pin bite: for each new `require_literal` pin and each fixture probe, apply one mutation (delete or reword the pinned sentence in one command file, remove one adapter row, flip a fixture's expected exit) and record that `bash scripts/eval.sh --check=review-panel` reports a finding, then revert; read the no-config path end to end to confirm no new step runs without the config line `[AC-3.2, AC-3.3, AC-3.4]`
- [x] 3.7 Verify all tests pass: `uv run pytest`, `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, and `bash scripts/eval.sh` (outside the sandbox) with Findings 0 `[AC-3.1, AC-3.4, AC-3.5]`

## Notes

- **Only story that touches `implement-story.md`.** Story 3 adds one paragraph and two table/list cells. Every new prose line costs ratchet bytes, so prefer the technical spec's exact paragraph over elaboration, and offset with trims of genuinely duplicated text rather than deleting load-bearing rules.
- **Cross-spec overlap.** `2026-10-01-behavioral-verification` Story 4 also edits `commands/implement-story.md` (Gate 4.5), the `.lean` twin, the `gates:` frontmatter, and the same `"commands/implement-story.md"` ratchet entry. The two specs edit different gates and don't depend on each other. Whichever lands second rebases and re-pins, and its disclosure comment cites the other spec's value as the starting point.
- **Structural guards that must stay green.** `test_lean_commands.py` enforces heading parity (no new headings in either file); `spawn-cap.py` `ALLOWED_STEMS` is `coding-agent` and `evaluator-agent`, so the panel prose must describe spawning in words, never as a new `Task(` marker naming a `*-agent` stem. The panel reuses the evaluator/review-agent prompts, so default spawns stay ≤ 2.
- **Combination edge cases.** Follow technical-spec.md → Interaction Edge Cases exactly: primary FAIL + panel block is one recode and one loop increment; primary PASS + `review-override.py` fail + panel pass still recodes via the override (unchanged); `--review-only --panel` + block ends the run.
- **Pins must bite.** A `require_literal` pin that a mutation cannot turn red is not a pin. Record each mutation and its finding in the story's What Was Built notes.
- **Depends on Stories 1 and 2.** The adapter panel rows and `status` come from Story 1; `tally`, its exit codes, and the consensus / single-vendor fixtures come from Story 2. The eval probes call those, so this story cannot land first.
- **`eval.sh` runs `git init` in a temp dir** — run it outside any sandbox.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Spawn reviewer (slug rejected / timeout or empty return), Parse reviewer (no verdict line), Parse primary (no verdict line → today's handling), Tally (no usable reviewer left), Tally (consensus found → Gate 3 FAIL → recode), Read config (no line → panel off), Platform check (Claude Code / Codex → skip)]
- **Shadow paths:** [Happy path (block → recode → second Gate 3 → pass), Nil input (no config line → Gate 3 identical), Empty input (`none` → off/skipped), Upstream error (every slug rejected → unverifiable, primary verdict stands)]
- **Business rules:** spec.md → ## 📋 Business Rules (Expanded) (4 Trigger precedence, 5 Same prompt plus one line, 9 Gate 3 combination, 10 Never DEGRADED); spec.md → ## 📋 Business Rules (3 Trigger, 6 Authority)
- **Experience:** [State Catalog → every `review-panel:` line (off, skipped, dropped, pass, advisory, block), Interaction Patterns → no new question; Gate 3.5 PAUSE options unchanged; lines grep beside `gate3-route:`]
- **Technical:** sub-specs/technical-spec.md → ## Gate 3 Wiring (Story 3); ## Interaction Edge Cases; ## Files in Scope (Story 3 rows); spec.md → Detailed Requirements (Gate 3 prose, Eval, Ratchet); spec.md → ⚠️ Cross-Spec Overlap; spec.md → ⚠️ Technical Concerns (Spawn cap)

## What Was Built

**Implementation Date:** 2026-10-01

### Files Modified

1. **`commands/implement-story.md`** — one inline `**Review panel (opt-in).**` paragraph directly after `**Risk route:**` (runs only with the config line; `status --platform`; trigger = Gate 3 spawns `review-agent` or `--panel`; same prompt, `readonly`, `model: <slug>`, exclusion line; `review-panel: dropped`; `tally` after `review-override.py`; `block` is a Gate 3 FAIL, one increment, PAUSE lists block lines, `--review-only` ends the run; never changes the verdict, never `⚠️ DEGRADED`). `--panel` Invocation row; mutual-exclusion sentence gains the `--panel`/`--quick` usage error before any gate; item 8 names `review-panel:`; one-clause notes in the Overview and Gate 3.5 § A. Duplicated verify-claim and review-loop prose replaced with the lean twin's wording. No heading, no `gates:` entry, no `Task(` marker. [AC-3.1, AC-3.2, AC-3.3]
2. **`commands/implement-story.lean.md`** — same paragraph in the Risk-route slot (after the default-spawn line), `--panel` row carrying the `--quick` usage error, item 8 entry, same Overview / Gate 3.5 clauses (DEV-006). [AC-3.1, AC-3.3]
3. **`scripts/eval.sh`** — `check_review_panel`, registered after `app-verify`: helper missing, `status` non-zero exit, consensus probe ≠ 1, single-vendor probe ≠ 0 are findings; the status summary is a note; `require_literal` pins on the opener, the `block` sentence, and the `--panel` row in both command files, both report entries, and the four adapter rows. [AC-3.4]
4. **`scripts/tests/test_review_panel.py`** — +27 tests (101 total): placement, wording, no heading / spawn marker / frontmatter change, spawn-cap pass, combination rules, invocation / report / no-config path, eval pin mutations, ratchet disclosure. [AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]
5. **`scripts/tests/test_governor_enforcement.py`** — `"commands/implement-story.md"` 11103 → 12013 (file 36973), rebased on `2026-10-01-behavioral-verification` Story 4's 11103; +1131 bytes gross, −221 trimmed. Disclosed, not exempted. [AC-3.5]
6. **`scripts/tests/test_lean_commands.py`** — `implement-story` sha256 re-pinned with a dated note. [AC-3.5]

### Pin Mutations (each one finding, recorded by `EvalPinMutationTests`)

| Mutation | Finding |
|---|---|
| delete `scripts/review-panel.py` | helper is missing |
| `status` stub exits 2 / raises (exit 1) | `status exited 2` / `status exited 1` |
| `primary-fail-ac23.md` ← `primary-pass.md` | two-vendor fixture exited 0, not 1 |
| `primary-pass.md` ← `primary-fail-ac23.md` | one-vendor fixture exited 1, not 0 |
| cut opener / `block` sentence / `--panel` row (×2 files) | six per-file findings |
| cut `review-panel:` report entry (×2 files) | two report findings |
| cut each adapter's `**Review panel (ADR-028): …**` opener (×4) | four adapter findings |

### Verification

- Before the prose: `eval.sh --check=review-panel` → 8 findings; after → PASS, Findings 0.
- `uv run pytest` and `uv run --python 3.9 pytest` → 2210 passed, 1 skipped each; all `scripts/tests/test_*.sh` pass; `bash scripts/eval.sh` → Findings 0.
- `spawn-cap.py check` on both command files → pass. No-config path read end to end: the paragraph's leading clause is the only `review-panel.py` entry in Gate 3.
- Gates: arch-check pass; boundary 3 crossings → `review-agent`; review-override pass; drift-format pass; authenticity pass; app-verify unverifiable (no recipe); docs-check unverifiable (no public exports).
- Gate 3 review-agent PASS, iteration 1. Minor findings fixed: `status` crash (exit 1) now a finding; Gate 3.5 and Overview cross-references added. Full-suite evidence recorded above.
- Drift: DEV-005, DEV-006, Small.
- Iteration count: 1
