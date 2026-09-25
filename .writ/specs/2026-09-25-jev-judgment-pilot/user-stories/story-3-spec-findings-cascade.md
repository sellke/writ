# Story 3: Spec-Findings Producer and Step 2.6c Cascade

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 2

## User Story

**As a** Writ maintainer running `/create-spec`
**I want** `jev-judge.py spec-findings` to batch-judge all stories in one request, write findings JSON with threshold-driven escalation, and `/create-spec` Step 2.6c to run only the orchestrator LLM pass over escalated stories
**So that** high-confidence stories skip redundant reasoning, the orchestrator pass covers only uncertain cases, and the cascade stays advisory (no gate fails)

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [ ] Given `spec-findings --spec PATH --out FILE` with ≥1 story, when one request is sent per spec with Noul `contradiction` and `gap` per story and Noul `ambiguity` per criterion, then p ≥ emit → finding written; escalate ≤ p < emit → story filename listed in `FILE.escalate.json`; p < escalate → clean. Summary reads `N judged, M escalated`. `uncalibrated_thresholds` is reported while `calibrated` is false. `[AC-3.1]`
- [ ] Given findings JSON and an optional `FILE.escalate.json`, when `python3 scripts/spec-analyze.py check --spec <folder> --findings <file>` is run, then schema passes unchanged. Extra keys `source` and `p` are present on Jev findings. `spec-analyze.py` is not edited. Findings merged with orchestrator results over escalated stories also pass the check. `[AC-3.2]`
- [ ] Given `commands/create-spec.md` Step 2.6c after Step 2.6b, when `jev-judge.py status` is `pass`, then run `spec-findings` first and run the orchestrator LLM pass only over escalated stories. When disabled or `unverifiable`, run the full existing pass. Step 2.9 carries a `jev:` note line. No analysis outcome fails the package or opens an AskQuestion gate (Story 6's one-time setup prompt fires on missing configuration, not on an analysis outcome). `[AC-3.3]`
- [ ] Given `commands/verify-spec.md` advisory check, when added with the same conditional as Step 2.6c, then analysis results stay notes and the verify report never fails on them. `[AC-3.4]`
- [ ] Given pytest and bash test coverage, when replay-mode runs on fixtures covering happy (all confident), partial (1 escalated), empty (zero stories, `unverifiable no_stories`), retry (429 then success, `attempts=2`), and transport failure (`unverifiable transport_error` with full-pass fallback signaled), then all scenarios pass. Command-body wiring is pinned by `scripts/tests/test_spec_analyze_command_hooks.sh`. `[AC-3.5]`

## Implementation Tasks

- [ ] 3.1 Write `scripts/tests/test_jev_judge_spec_findings.py` (replay-mode pytest: happy, partial, empty, upstream error scenarios; state budget; escalation band logic) `[AC-3.1, AC-3.5]`
- [ ] 3.2 Build request in `jev-judge.py spec-findings`: state holds each story's user-story block and criteria keyed by filename; questions per story (contradiction, gap) and per criterion (ambiguity); send one request per spec `[AC-3.1]`
- [ ] 3.3 Apply thresholds and write findings: parse response; apply `emit` and `escalate` from `jev-thresholds.json`; write JSON array (schema-matching `spec-analyze.py`, extra keys `source` and `p`); write `FILE.escalate.json` sidecar; summary line with `N judged, M escalated` and `uncalibrated_thresholds` reason `[AC-3.1, AC-3.2]`
- [ ] 3.4 Wire `commands/create-spec.md` Step 2.6c: one short conditional sub-step after Step 2.6b (keep existing 2.6a, 2.6b numbering); when `jev-judge.py status pass`, run `spec-findings`, read escalate list, run orchestrator pass only over those stories; otherwise run full existing pass; Step 2.9 adds `jev:` note line `[AC-3.3]`
- [ ] 3.5 Wire `commands/verify-spec.md` advisory check: one line conditional matching Step 2.6c logic; analysis notes only; script `fail` does not fail verify report `[AC-3.4]`
- [ ] 3.6 Extend `scripts/tests/test_spec_analyze_command_hooks.sh`: grep Step 2.6c for conditional and `spec-findings` call; grep verify-spec advisory check for same conditional; assert escalation list is read and orchestrator pass is selective `[AC-3.3, AC-3.4, AC-3.5]`
- [ ] 3.7 Verify: pytest green; `bash scripts/tests/test_spec_analyze_command_hooks.sh` green; Step 2.6c sits after 2.6b; verify-spec advisory check never fails package; closing commit appends `{date} jev-pilot:` noting spec-findings producer and Step 2.6c cascade `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`

## Notes

**Depends on Story 2.** Transport, status resolution, and replay mode must exist. This story wires the findings producer and command conditionals.

**Schema constraint.** Findings JSON must pass `spec-analyze.py check --spec <folder> --findings <file>` unchanged. Extra keys `source` (provider ID) and `p` (probability) are allowed. Do not edit `spec-analyze.py`.

**Cascade, not replacement.** Orchestrator LLM pass runs in full when Jev is disabled or a story is escalated. No gate outcome depends on Jev findings in this spec.

**Step 2.6c placement.** After Step 2.6b (not renumbering 2.6a). Conditional logic: if provider enabled and status pass, run spec-findings first and limit orchestrator pass to escalated stories. Otherwise run today's full pass.

**Threshold application.** Emit and escalate thresholds are code-side only, read from `jev-thresholds.json`. While `calibrated` is false, `uncalibrated_thresholds` reason is reported (informational, does not change verdict).

**Empty spec.** If spec has zero stories, no request is sent (mirrors `spec-analyze.py`'s `spec_unreadable` for missing story set). Result is `unverifiable no_stories`.

**Out of scope.** No new agent file. No LLM API in scripts. Do not change `/implement-story` spawn. Story 4 owns calibration and threshold tuning.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Build request (state over budget), Apply thresholds (escalation band logic), Write findings (schema, sidecar), Parse response (model mismatch), Transport error (fallback to full pass)]
- **Shadow paths:** [Happy (all confident, empty escalate list, no orchestrator pass), Nil (provider disabled, full pass), Empty (zero stories, no request sent), Upstream error (429 then success, attempts count in summary), Partial (1 of 5 escalated, orchestrator pass over escalated only)]
- **Business rules:** [Rule 3 (Cascade, not replacement — escalated stories go back to orchestrator), Rule 4 (Advisory only — no gate outcome depends on Jev in this spec), Rule 5 (Pinned model ID), Rule 6 (No network in tests or eval), Rule 10 (Decision log entry per story commit)]
- **Experience:** [Entry point (Step 2.6c after stories exist), Happy path (one Jev request, findings written, selective orchestrator pass, Step 2.9 note), Moment of truth (escalated stories receive full reasoning; empty spec produces no_stories reason), Feedback model (summary line with model ID, input tokens, judged/escalated counts), Error experience (provider disabled → full pass, transport error → full pass, state too large → story escalated)]
