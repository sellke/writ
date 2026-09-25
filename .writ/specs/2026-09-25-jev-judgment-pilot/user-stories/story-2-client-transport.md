# Story 2: Client Transport and eval Check

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer implementing the Jev judgment provider
**I want to** land `scripts/jev-judge.py` with a stdlib HTTP client, timeout, retry logic, state-size guard, error mapping, and a replay transport for tests
**So that** the provider can call TypeSafe's API safely, fails gracefully with named reasons, never touches the network during testing or eval, and ships with conservative default thresholds

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [ ] Given any HTTP outcome at `POST <base>/v1/systemone` on either backend (technical-spec §2 table), when the client handles it, then timeout/DNS/5xx other than 529 → `transport_error`; 401 → `auth_error`; 422 or gateway 404 `model_not_found` → `request_invalid` (both error body shapes read; body logged to stderr, truncated to 500 chars); 429/529 after 3 attempts → `rate_limited` per technical-spec §1. All outcomes are `unverifiable`, exit 0. One 429 followed by success shows `attempts=2` in the summary per technical-spec §5. `[AC-2.1]`
- [ ] Given `WRIT_JEV_REPLAY=<dir>` is set in the environment, when the client is initialized, then no socket is opened. The request body is canonicalized (JSON dump with sort_keys=True, separators=(",", ":")), hashed SHA-256, and the response is read from `<dir>/<hash>.json`. A missing file gives `replay_miss` reason per technical-spec §1. Tests prove no network by patching `urllib.request.urlopen` to raise; pytest and `bash scripts/eval.sh` never touch the network. `[AC-2.2]`
- [ ] Given a request to judge questions, when the client builds and sends the message, then it sends the backend's model per BR 5 (`jev-1.13.0` on `typesafe`; `typesafe-ai/jev` plus `providerOptions.gateway.only: ["typesafe-ai"]` on `vercel-gateway`, with informational `model_unpinned`). On `typesafe`, a response whose `model` differs gives `model_mismatch` and answers are discarded. A response missing `answers` or any typed field gives `fail` with reason `malformed_response` (exit 1). State plus the longest question estimated over 30,000 tokens (chars ÷ 4) gives `state_too_large` with no request sent. The summary records `backend=`, `model=<id>`, `input_tokens=<n>` from `usage`, and gateway `cost=` when present. `[AC-2.3]`
- [ ] Given `scripts/eval.sh` and the provider disabled, when the `jev-judge` check runs, then the check function follows the shape of `check_spec_analyze()` in technical-spec §5: missing helper or exit 2 → `add_finding`; any verdict → `add_note`; no network connection opened. `scripts/tests/test_eval_jev_judge.sh` in the style of `test_eval_spec_analyze.sh` pins the check. The eval report ends with Findings 0 while the provider is disabled. `[AC-2.4]`
- [ ] Given `scripts/jev-thresholds.json` at ship time, when the file is loaded, then it contains technical-spec §4's starting values (backend=null, model=null, calibrated_on=null, spec_findings contradiction/gap/ambiguity emit/escalate at 0.85/0.35, ac_shadow satisfied at 0.9, calibrated=false). When `calibrated` is true and the active backend or model differs from the recorded ones, the loader reports `uncalibrated_thresholds` and keeps the values. `[AC-2.5]`

## Implementation Tasks

- [ ] 2.1 Write `scripts/tests/test_jev_judge.py` (pytest, Python 3.9 stdlib) with fixtures for HTTP outcomes: timeout, DNS, 401, 422, 429→200, 429×3, 5xx; verify each maps to the named reason in technical-spec §1 and exits 0. Prove no network by patching `urllib.request.urlopen` to raise on any call; enable `WRIT_JEV_REPLAY` env and read from test fixtures. `[AC-2.1, AC-2.2]`
- [ ] 2.2 Implement the transport layer in `scripts/jev-judge.py` (stdlib `urllib.request`, 10s timeout per technical-spec §3): POST to `https://api.typesafe.ai/v1/systemone` with Authorization header, Content-Type application/json. Catch exceptions and map to reasons per technical-spec §1. On 429/529, retry up to 3 attempts with `retry-after` header or exponential backoff (1, 2, 4 sec). `[AC-2.1]`
- [ ] 2.3 Implement the replay transport: when `WRIT_JEV_REPLAY` is set, canonicalize request body (`json.dumps(sort_keys=True, separators=(",", ":"))`, hash with SHA-256, read from `<dir>/<hash>.json`. Missing file → `replay_miss`. Never call the network layer when replay is active. `[AC-2.2]`
- [ ] 2.4 Implement state-size guard and model checking: estimate tokens as `len(json.dumps(state)) + max(len(json.dumps(q)) for q in questions)` ÷ 4 per technical-spec §3. If estimate > 30,000, emit `state_too_large` and skip the request. Send the backend's model and, on `vercel-gateway`, the `only` routing option. Parse the response; on `typesafe`, if `model` differs, emit `model_mismatch` and discard answers; on `vercel-gateway`, add `model_unpinned`. If `answers` or typed fields are missing, emit `malformed_response` (exit 1). Record `model=` and `input_tokens=` in the summary from `usage` per technical-spec §1. `[AC-2.3]`
- [ ] 2.5 Create `scripts/jev-thresholds.json` with technical-spec §4 starting values: backend=null, model=null, calibrated=false, calibrated_on=null, spec_findings (contradiction/gap/ambiguity: emit=0.85, escalate=0.35), ac_shadow (satisfied=0.9). Ship alongside `jev-judge.py`. `[AC-2.5]`
- [ ] 2.6 Add `jev-judge` check to `scripts/eval.sh` (modeled on `check_spec_analyze()` per technical-spec §5): call the helper; missing or exit 2 → `add_finding`; any verdict line → `add_note`. Create `scripts/tests/test_eval_jev_judge.sh` in the shape of `test_eval_spec_analyze.sh`. Confirm `bash scripts/eval.sh` reports Findings 0 while the provider is disabled (BR 6 no network in eval). `[AC-2.4]`
- [ ] 2.7 Verify acceptance criteria: `uv run --python 3.9 pytest scripts/tests/test_jev_judge.py` green; `bash scripts/tests/test_eval_jev_judge.sh` green; confirm no `urllib.request.urlopen` calls in test runs; check thresholds file against technical-spec §4; closing commit appends `{date} jev-pilot: {what changed and why}` to `.writ/decision-log.md`. `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`

## Notes

**Technical considerations.** Model on `scripts/spec-analyze.py` and `scripts/drift-format.py` for argparse shape and verdict output (one line, optional `reason:` lines, summary last). Use stdlib `urllib.request` (no requests, no SDK) per BR 9. Token estimate is `len(json.dumps(...)) / 4`, not `len(text) / 4`. Request body canonicalization must be deterministic for replay hashing (sort_keys=True, separators with no spaces). The `judge(state, questions)` function is internal; replay keying is SHA-256 of the canonical body, not the questions alone.

**Risks.** Retry logic with exponential backoff and `retry-after` parsing is error-prone; test both paths. State-size estimation is approximate (dividing by 4 matches spec language); recalibrate if precision matters later. The pinned model ID (`jev-1.13.0`) is a later-story constraint; do not allow overrides here.

**Integration.** Story 1 provides `jev-judge.py status`. This story adds the `judge()` function, the HTTP transport, the replay fallback, and the eval check. Story 3 calls `judge()` inside `spec-findings`. Story 4 replaces thresholds after calibration. Story 5 adds `ac-shadow`. Leave `commands/create-spec.md` and `commands/verify-spec.md` unchanged in this story.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing (`pytest` + `eval.sh` both green)
- [ ] Code reviewed
- [ ] Thresholds file shipped
- [ ] Decision log updated

## Context for Agents

- **Error map rows:** [Build request (state over budget), POST /v1/systemone (timeout/DNS/5xx/401/422/429/529), Parse response (missing answers/typed field, model mismatch), Upstream error (429 then success)] — technical-spec §5
- **Shadow paths:** [Enabled provider with all stories confident, Provider disabled, Network error or timeout, State over budget] — technical-spec §6
- **Business rules:** [BR 5 Pinned model where possible, BR 11 Gateway routing restricted, BR 6 No network in tests or eval, BR 9 Stdlib only, BR 1 Double opt-in, BR 2 Verdict contract] — spec.md
- **Experience:** [Disabled provider note, Transport error with named reason, State too large escalation] — spec.md → 🎯 Experience Design
