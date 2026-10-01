# Story 4: Gate 4.5 becomes behavioral verification; mockup comparison becomes advisory

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** Story 3

## User Story

**As a** developer running `/implement-story` on their own project
**I want to** have Gate 4.5 run my project's own checks for the features a story touched, through `scripts/app-verify.py`, and decide pass or fail from their exit codes
**So that** a story cannot complete while a feature it changed is broken in the running app, and the verdict comes from a machine rather than an agent's opinion

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.5

- [x] Given `.writ/docs/app-verification.md` exists, when Gate 4.5 runs on the default pipeline or `--full-pipeline`, then it runs `python3 scripts/app-verify.py touched` with the story's changed files and then `run --run-label story-N --features <ids>` on the touched IDs, with no Task spawn; exit 0 continues, exit 1 sends the story to Gate 1 for recode and counts toward the shared 3-iteration review-loop cap, and exit 2 (no recipe, invalid recipe, safety refused) prints one `app-verify:` line and continues without marking the story `⚠️ DEGRADED`; when `touched` prints no IDs, the gate skips `run`, relays the `no mapped features` line, and continues on the same unverifiable branch; under `--review-only` the gate runs and a fail ends the run with no recode; `--quick` skips the gate; and Gate 4.5 never asks a question `[AC-4.1]`
- [x] Given `--full-pipeline` and a story with visual references, when Gate 4.5 runs, then `visual-qa-agent` still runs after the script, its mismatches are written to the story report as notes, and none of them can fail the gate or increment the review-loop counter; the Pipeline table row, the Control flow paragraph, and the Gate 3 review-loop prose stop counting a visual-QA FAIL as a recode site and name Gate 4.5's script fail instead `[AC-4.2]`
- [x] Given the edited `commands/implement-story.md`, when `python3 scripts/verdict-provenance.py check --command commands/implement-story.md --prose-only-blocking` runs, then the `gates:` frontmatter carries `gate4_5_behavior` with `script: scripts/app-verify.py` in place of `gate4_5_visual`, `HEADING_TO_ID["4.5"]` is `gate4_5_behavior`, `DEFAULT_MAX_PROSE_ONLY` is 1, the run reports `prose_only_count: 1 (cap 1)` with no findings, and a fixture with two prose-only gates is a blocking finding in `eval.sh` `[AC-4.3]`
- [x] Given `agents/coding-agent.md`, when a recipe exists and a story adds user-facing behavior that no feature-map row covers, then a single added rule directs the coding agent to write a check in the project's own test harness and add a matching feature-map row (ID, feature, paths, check), and states that the check's exit code is the verdict and the agent never grades the result `[AC-4.4]`
- [x] Given the Gate 4.5 rewrite, when `spawn-cap.py check --command commands/implement-story.md`, the governor suite, and the lean suite run, then `spawn-cap` prints `pass`, `commands/implement-story.lean.md` carries the same Gate 4.5 behavior and `gates:` entry, `KEPT_HEADINGS` and `KEPT_SCRIPTS` in `test_lean_commands.py` name the new heading and `scripts/app-verify.py`, and `KNOWN_OVER_BUDGET["commands/implement-story.md"]` and `DEFAULT_SHA256["implement-story"]` are re-pinned with dated comments naming `2026-10-01-behavioral-verification`, with net growth disclosed and kept no larger than the new gate needs `[AC-4.5]`

## Implementation Tasks

- [x] 4.1 Write failing tests: in `scripts/tests/test_implement_story_default_path.py` pin the Gate 4.5 section (`app-verify.py touched` and `run --run-label story-N`, fail → Gate 1 on the shared cap, unverifiable → one `app-verify:` line and not DEGRADED, no `> **Agent:**` or `Task(` on default, `visual-qa-agent` notes-only under `--full-pipeline`); in `scripts/tests/test_verdict_provenance.py` pin `HEADING_TO_ID["4.5"]` and the default cap of 1; in `scripts/tests/test_eval_verdict_provenance.sh` move the clean fixture to 9 script entries plus 1 prose-only (`prose_only_count: 1 (cap 1)`) and add a two-prose-only fixture that must produce a finding `[AC-4.1, AC-4.2, AC-4.3]`
- [x] 4.2 Rewrite `#### Gate 4.5` in `commands/implement-story.md` as behavioral verification (script commands, the three exit-code outcomes, `--quick` skip, advisory `visual-qa-agent` under `--full-pipeline`), and update the Pipeline table row, the Control flow paragraph, the Gate 3 review-loop sentence, and the `loop.calibrated_against` quote that transcribes it; trim adjacent prose where meaning is unchanged so the edit stays net-tight `[AC-4.1, AC-4.2]`
- [x] 4.3 Replace the `gate4_5_visual` / `verification: prose-only` frontmatter entry with `gate4_5_behavior` / `script: scripts/app-verify.py`; in `scripts/verdict-provenance.py` change `HEADING_TO_ID["4.5"]` and set `DEFAULT_MAX_PROSE_ONLY = 1`, updating the module docstring's `--max-prose-only 2` and the `check_verdict_provenance` comment in `scripts/eval.sh` that says "a third prose-only gate" `[AC-4.3]`
- [x] 4.4 Add the one check-authoring rule to `agents/coding-agent.md`; if `scripts/gen-codex-agent-tomls.py` derives `codex/agents/coding-agent.toml` from that body, regenerate it so the freshness check stays green `[AC-4.4]`
- [x] 4.5 Mirror the Gate 4.5 rewrite, Pipeline row, Control flow, review-loop prose, and `gates:` entry into `commands/implement-story.lean.md`; update `KEPT_HEADINGS` and `KEPT_SCRIPTS` in `scripts/tests/test_lean_commands.py`; re-pin `KNOWN_OVER_BUDGET["commands/implement-story.md"]` in `scripts/tests/test_governor_enforcement.py` and `DEFAULT_SHA256["implement-story"]` in `scripts/tests/test_lean_commands.py`, each with a dated comment naming this spec and the byte delta `[AC-4.2, AC-4.5]`
- [x] 4.6 Verify the acceptance criteria: `verdict-provenance.py check --prose-only-blocking` on `commands/implement-story.md` reports `prose_only_count: 1 (cap 1)` and exit 0; `spawn-cap.py check --command commands/implement-story.md` prints `pass`; grep both command files for the `app-verify.py touched` and `run --run-label story-N` lines `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`
- [x] 4.7 Verify all tests pass: `uv run --python 3.9 pytest` on the touched suites, then `uv run pytest`, the bash tests (`test_eval_verdict_provenance.sh`, `test_eval_drift_format.sh`, `test_eval_boundary_map.sh`), and `bash scripts/eval.sh` with Findings 0 (run outside the sandbox) `[AC-4.3, AC-4.5]`

## Notes

- **Two places own the gate id.** `scripts/verdict-provenance.py` maps headings to ids through a fixed `HEADING_TO_ID` table, so renaming the frontmatter entry alone produces `heading_without_entry` and `entry_without_heading`. Change both together. `test_verdict_provenance.py` and `test_eval_verdict_provenance.sh` also build fixtures from the gate-id list and need the new id.
- **Gate 4.5 must stay a script, not a spawn (Business Rule 7).** `spawn-cap.py` counts only `> **Agent:**` lines and `Task(` calls. Keep the default-path prose free of both. The `> **Agent:** agents/visual-qa-agent.md` marker stays only under the `--full-pipeline` subsection, where it already sits.
- **Byte budget.** `commands/implement-story.md` is already over budget (overage pinned at 11110). Removing visual QA as a recode site, and the old Results ladder (PASS / SOFT PASS / FAIL), frees bytes that the new outcome lines can use. Do not loosen the ratchet beyond what the new gate needs.
- **Lean sibling.** Earlier specs kept `implement-story.lean.md` byte-identical. This story changes the gate contract, so the lean body changes too (technical-spec Files in Scope). The lean frontmatter-contract test then needs the same `gates:` entry in both files.
- **`--review-only` (decided at spec time).** Gate 4.5 runs under `--review-only` because it is verification, not coding. A fail ends the run with no recode, matching the Invocation table's rule for that mode. `--quick` still skips it.
- **Integration with Story 3.** The gate depends on the `touched` and `run` subcommands and on the exit codes 0/1/2 that Story 3 ships. Use Story 3's What Was Built record for the exact summary-line forms; do not restate them here beyond the State Catalog.
- **Risk.** The `loop.calibrated_against` text quotes the review-loop prose verbatim. If that sentence changes and the quote does not, the two drift apart. Update them in the same edit.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Read recipe, Validate recipe, Resolve safety variable, Launch, Readiness, Run check] — technical-spec.md → Error & Rescue Map (Gate 4.5 consumes these outcomes; Story 3 implements them)
- **Shadow paths:** [Gate 4.5] — technical-spec.md → Shadow Paths
- **Business rules:** spec.md → ## 📋 Business Rules (Expanded) (2 Machine verdicts only, and the coding agent may write the check; 5 Gate 4.5 verdicts pass/fail/unverifiable on the shared 3-iteration cap; 6 Mockup comparison advisory under `--full-pipeline`; 7 Gate 4.5 is a script, so the two-subagent default is unchanged)
- **Experience:** spec.md → ## 🎯 Experience Design → State Catalog (`app-verify:` lines), Interaction Patterns (Gate 4.5 never asks a question); User Journey steps 3 and 4
- **Technical:** sub-specs/technical-spec.md → Files in Scope (Story 4 rows); spec.md → ## Detailed Requirements → Gate entry

## What Was Built

**Implementation Date:** 2026-10-01

### Files Modified

1. **`commands/implement-story.md`** and **`commands/implement-story.lean.md`** — `#### Gate 4.5: Behavioral Verification`: `app-verify.py touched` then `run --recipe .writ/docs/app-verification.md --spec <spec-folder> --run-label story-N --features <touched ids, comma-joined>`, no Task spawn; exit 0 continue, exit 1 Gate 1 recode on the shared review-loop cap, exit 2 or no touched IDs relay one `app-verify:` line and continue (not DEGRADED); `--review-only` fail ends the run; `--quick` skips; never asks a question. `--full-pipeline` keeps `visual-qa-agent` after the script with notes-only mismatches. Pipeline row, Control flow, Gate 3 review-loop sentence, and `loop.calibrated_against` quote name "Gate 4.5 script fail"; `gates:` entry `gate4_5_behavior` / `script: scripts/app-verify.py`. Default body 36,070 → 36,063 bytes (old Results ladder plus one Gate 4 analogy clause trimmed). [AC-4.1, AC-4.2, AC-4.3]
2. **`scripts/verdict-provenance.py`** — `HEADING_TO_ID["4.5"] = "gate4_5_behavior"`, `DEFAULT_MAX_PROSE_ONLY = 1`, docstring; **`scripts/eval.sh`** comment ("a second prose-only gate"); **`scripts/eval-loop-bounds.py`** quoted label. [AC-4.3]
3. **`agents/coding-agent.md`** — rule 6 (behavioral checks: write a check in the project's harness plus a Feature Map row; exit code is the verdict, never graded); **`agents/visual-qa-agent.md`**, **`adapters/codex.md`**, **`commands/design.md`** — stale visual-QA-recodes wording made notes-only; `codex/agents/*.toml` regenerated. [AC-4.2, AC-4.4]
4. **Tests** — `test_implement_story_default_path.py` (Gate 4.5 pins, `BehavioralVerificationContractTests` for lean parity and the coding-agent rule), `test_verdict_provenance.py` (new id, heading, cap 1, real command `prose_only_count: 1 (cap 1)`), `test_eval_verdict_provenance.sh` (9 script + 1 prose-only clean fixture; two-prose fixture is a finding), `test_lean_commands.py` (`KEPT_HEADINGS`, `KEPT_SCRIPTS`, `DEFAULT_SHA256` re-pin), `test_governor_enforcement.py` (`KNOWN_OVER_BUDGET` 11110 → 11103), all with dated comments naming this spec. [AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]

### Verification

- `verdict-provenance.py check --prose-only-blocking` on both bodies → `prose_only_count: 1 (cap 1)`, findings 0, exit 0; `spawn-cap.py check` on both → `pass`; `gen-codex-agent-tomls.py --check` → pass.
- Targeted suites (3.9) → 202 passed; `test_eval_verdict_provenance.sh`, `test_eval_drift_format.sh`, `test_eval_boundary_map.sh` pass.
- Gates: arch-check pass; boundary-map 3 crossings (cross-component) → `review-agent`; Gate 3 review-agent PASS, Small drift, 5 Minor findings fixed in place (comma-joined `--features`, three stale visual-QA docs, untested coding-agent rule); test-integrity authenticity pass; docs-check unverifiable (no public exports); drift-format pass.
- Drift: DEV-006, DEV-007, both Small.
- Iteration count: 1
