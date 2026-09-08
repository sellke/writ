# Story 5: Gate 3.5 Format + Flip + Watch — drift-format.py, prose-only-blocking, runner watch field, baseline replay

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1, Story 2, Story 3, Story 4

## User Story

**As a** Writ maintainer who needs the honor-system count to become a blocking eval finding at 2, a format check on drift, a runner field that counts the print-mode background-task drop, and a replay table against the 16 committed baseline records instead of another $180 eight-run
**I want to** land `scripts/drift-format.py`, flip `commands/implement-story.md` so exactly `gate1_coding` and `gate4_5_visual` stay `prose-only` and the other eight name their scripts, pass `--prose-only-blocking` from `eval.sh`, drop 85/70 from `agents/visual-qa-agent.md`, add `background_tasks_outstanding` on new baseline run records, and replay both committed baseline JSONs
**So that** Goal Card DONE WHEN line 4 (at most two prose-only gates) is a machine finding, Large-drift still pauses a human for accept/reject/modify-spec, Stage 4 can count the print-mode drop without this story changing spawn behavior, and the sixteen Stage 1 / Stage 2a records show agent-vs-rederived verdicts without a keep-or-revert or `/revert`

## Acceptance Criteria

> **AC IDs assigned through:** AC-5.5

- [ ] Given `python3 scripts/drift-format.py check --story <path> [--drift-log PATH] [--review-output PATH]` on Python 3.9 stdlib, when a drift log’s every `DEV-NNN` entry matches `.writ/docs/drift-report-format.md` required fields and a Large-drift heading (when present) has a PAUSE token in the story or `--review-output`, then it prints `pass` and exits 0; when an entry is malformed or Large-drift lacks PAUSE, then it prints `fail` plus `reason:` and exits 1; when there is no drift log and no Large-drift heading, then it prints `unverifiable` and exits 0; and the script never decides accept / reject / modify-spec `[AC-5.1]`
- [ ] Given Stories 1–4 have already set `script:` on gates 3, 0, 5, 0.5, and 2.5, when this story lands, then `commands/implement-story.md` `gates:` names `scripts/arch-check.py`, `scripts/boundary-map.py`, `scripts/build-smoke.py`, `scripts/change-surface.py`, `scripts/review-override.py`, `scripts/drift-format.py`, `scripts/test-integrity.py`, and `scripts/docs-check.py` on those eight ids, only `gate1_coding` and `gate4_5_visual` remain `verification: prose-only`, Gate 3.5 runs `drift-format.py` after the drift step (FAIL → existing BLOCKED; `unverifiable` continues, reason verbatim, no `DEGRADED`), `eval.sh` registers check `drift-format` (not count-blocking), and `check_verdict_provenance()` passes `--prose-only-blocking` so `python3 scripts/verdict-provenance.py check --command commands/implement-story.md --prose-only-blocking` prints `prose_only_count: 2 (cap 2)` and exits 0 `[AC-5.2]`
- [ ] Given `agents/visual-qa-agent.md` still carries the 85/70 percentage lines (Stage 2a DEV-102), when this story lands, then those lines are gone and the verdict vocabulary remains PASS / SOFT PASS / FAIL `[AC-5.3]`
- [ ] Given `scripts/pipeline-baseline.py` after this story, when a **new** run record is written, then it includes `background_tasks_outstanding` (int, default 0), ingest parses Claude Code print-mode stderr for `Background tasks still running after 600s`, and `GATE_NAMES` / `REDERIVATION_KEYS` include the new scripts for future runs; when the two committed files `.writ/eval/baselines/2026-09-06-claude-fable-5-1.json` and `2026-09-07-claude-fable-5-1.json` are read, then their schema is byte-stable (no rewrite) `[AC-5.4]`
- [ ] Given both committed baseline JSONs (16 records), when `scripts/tests/test_gate_replay.py` (or a `replay` subcommand) loads them and invokes each new script in `--changed` / post-hoc mode from paths the record already carries, then it writes an agent-verdict vs re-derived table for What Was Built, disagreement is a note not a revert, `unverifiable` on historical `test_integrity: nothing_inspected` is the expected majority, there is no eight-run re-run and no keep-or-revert and no `/revert`, and the decision-log line names the flip and the replay totals `[AC-5.5]`

## Implementation Tasks

- [ ] 5.1 Write `scripts/tests/test_drift_format.py` (pytest, Python 3.9) with fixtures for `pass` (well-formed `DEV-NNN` + Large-drift with PAUSE), `fail` (malformed entry; Large-drift without PAUSE), and `unverifiable` (no log, no Large-drift heading); assert CLI `check --story` plus optional `--drift-log` / `--review-output`, exit 0/1/2, shared stdout shape (verdict line, optional `reason:`, summary last), and that accept / reject / modify-spec is never a printed verdict `[AC-5.1]`
- [ ] 5.2 Write `scripts/tests/test_gate_replay.py` (and, if needed, a focused pytest for the new baseline field) that loads both committed baseline JSONs (8 + 8 = 16 records) without mutating them; invoke new scripts in `--changed` / post-hoc mode from paths each record already carries; assert the agent-vs-rederived table is produced; treat disagreement as a note; treat `unverifiable` on `test_integrity: nothing_inspected` as expected; plus `scripts/tests/test_eval_drift_format.sh` in the `test_eval_verdict_provenance.sh` shape covering `check_verdict_provenance` now passing `--prose-only-blocking` `[AC-5.2, AC-5.4, AC-5.5]`
- [ ] 5.3 Implement `scripts/drift-format.py` `check --story PATH [--drift-log PATH] [--review-output PATH]` (stdlib, argparse): required fields from `.writ/docs/drift-report-format.md`; Large-drift heading requires a PAUSE token in the story or `--review-output`; verdict table per `sub-specs/technical-spec.md` §5; do not decide accept / reject / modify-spec `[AC-5.1]`
- [ ] 5.4 Set `commands/implement-story.md` `gates:` to the technical-spec §6 table (`gate3_5_drift: script: scripts/drift-format.py`; only `gate1_coding` and `gate4_5_visual` `prose-only`); add a Gate 3.5 “Verify the claim, don't trust it.” format check after the drift step (FAIL → existing BLOCKED; `unverifiable` → continue, no `DEGRADED`); pass `--prose-only-blocking` from `check_verdict_provenance()` in `scripts/eval.sh`; register `drift-format` in `CHECKS=(...)` (`add_finding` / `add_note`, not count-blocking); drop the 85/70 lines from `agents/visual-qa-agent.md` and keep PASS / SOFT PASS / FAIL; do not change how `/implement-story` spawns agents `[AC-5.2, AC-5.3]`
- [ ] 5.5 Extend `scripts/pipeline-baseline.py`: `background_tasks_outstanding` (int, default 0) on **new** run records; parse Claude Code stderr for `Background tasks still running after 600s`; extend `GATE_NAMES` and `REDERIVATION_KEYS` (and `GATE_SCRIPT_VERDICTS` consumers as needed) for future runs; do **not** rewrite the two committed baseline JSON files `[AC-5.4]`
- [ ] 5.6 Land the replay runner (`test_gate_replay.py` and/or `replay` subcommand) so What Was Built can hold the per-run, per-new-gate agent vs re-derived table for all sixteen records; record disagreements as notes; do not treat historical integrity `unverifiable` as a script defect `[AC-5.5]`
- [ ] 5.7 Verify acceptance criteria: `uv run --python 3.9 pytest scripts/tests/test_drift_format.py scripts/tests/test_gate_replay.py` green, bash eval-wiring green, `python3 scripts/verdict-provenance.py check --command commands/implement-story.md --prose-only-blocking` exits 0, `bash scripts/eval.sh` exits 0, visual-qa has no 85/70, committed baselines are unchanged, What Was Built holds the replay table, and the closing commit appends `{date} stage-2b: Story 5 — drift-format.py; gates flipped to 8 script / 2 prose-only; --prose-only-blocking on; watch field; replay totals {N agree / M note / K unverifiable}` — no keep-or-revert, no `/revert` `[AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5]`

## Notes

**Technical considerations.** Same CLI family as `build-smoke.py` / `test-integrity.py` / `verdict-provenance.py`: Python 3.9 stdlib, subcommands, exit 0/1/2. Verdict vocabulary is `GATE_SCRIPT_VERDICTS`: `pass` / `fail` / `unverifiable`. `verdict-provenance.py` already accepts `--prose-only-blocking`; this story is the first time `eval.sh` passes it. `install.sh` already copies `scripts/*.py`. Gate 3.5 format-checks only — Business Rule 4 keeps accept / reject / modify-spec human.

**QUALITY adapted.** This is not a cut. Proof is fixtures plus read-only re-derivation against the two committed baseline files. No eight-run Fable 5.1 re-run. No keep-or-revert. No `/revert`. Replay disagreement with a Stage 1/2a self-report is a note in What Was Built.

**Watch item.** `background_tasks_outstanding` records the print-mode “Background tasks still running after 600s” drop so Stage 4 can count it. Do not change how `/implement-story` spawns agents. Stage 4 owns any orchestrator fix (ADR-013: nothing merges, opens a PR, or releases).

**Risks.** Stage 2a already shows `test_integrity: unverifiable` / `nothing_inspected` on the eight runs; Gate 3 replay will inherit that majority. Treating it as a script defect would mute the real findings. Extending `REDERIVATION_KEYS` must not rewrite the committed JSON schema — old records simply lack the new field.

**Integration.** Depends on Stories 1–4 so the eight `script:` paths exist before `--prose-only-blocking` turns on. This story sets `gate3_5_drift` and flips the remaining honor-system count to two. Decision-log line must name the flip and the replay totals.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [spec.md → ## 🎯 Experience Design → Error experience (script FAIL → existing BLOCKED; `unverifiable` → continue, no `DEGRADED`; replay disagreement is a note, not a revert)]
- **Shadow paths:** [spec.md → ## 🎯 Experience Design → Happy path, step (5) 3.5 format-checks; frontmatter 8 script / 2 prose-only; eval Findings 0 with `--prose-only-blocking`; replay table on sixteen committed runs]
- **Business rules:** [Rule 4 (ABORT and Large-drift stay human — format check only), Rule 5 (exactly Gate 1 and Gate 4.5 remain prose-only; drop 85/70), Rule 6 (No eight-run re-run, no keep-or-revert — fixtures + read-only replay), Rule 7 (Background-subagent drop is a watch item; do not change spawn), Rule 8 (Python 3.9 stdlib), Rule 9 (ADR-013 holds), Rule 10 (Decision log names the flip and replay totals)]
- **Experience:** [Moment of truth (`prose_only_count: 2 (cap 2)`), Feedback model (verdict line + reason; agent claim vs measurement), Error experience (FAIL vs unverifiable; replay note), State catalog → frontmatter flipped / blocking on / replay recorded]
- **Detailed requirements:** [spec.md → ## Detailed Requirements → ### Story 5 — Gate 3.5 format + flip + watch]
- **Technical contract:** [technical-spec.md → ## 5. `scripts/drift-format.py` (Story 5); ## 6. Frontmatter flip, provenance, visual-qa, runner (Story 5); ## 7. Replay (Story 5)]
- **Technical concerns:** [spec.md → ## ⚠️ Technical Concerns (historical `test_integrity: unverifiable` is expected on replay; do not rewrite committed baseline JSON schema)]
- **Scope boundaries:** [spec.md → ## Specification Contract → Scope Boundaries (Excluded: eight-run re-run; orchestrator background-subagent fix; Stage 4 evaluator)]
