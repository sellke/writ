# Technical Spec: Jev Judgment Pilot

> Parent: [`../spec.md`](../spec.md)
> Stories: [1](../user-stories/story-1-adr-and-opt-in.md) · [2](../user-stories/story-2-client-transport.md) · [3](../user-stories/story-3-spec-findings-cascade.md) · [4](../user-stories/story-4-calibration.md) · [5](../user-stories/story-5-gate3-shadow.md) · [6](../user-stories/story-6-setup-prompt.md)

## 1. CLI surface — `scripts/jev-judge.py`

| Subcommand | Story | Args | Writes |
|---|---|---|---|
| `status` | 1 | `[--repo .]` | stdout only |
| `setup` | 6 | `--provider {typesafe,vercel-gateway,none} [--repo .]` | the `Judgment Provider` line in `.writ/config.md` only |
| `spec-findings` | 3 | `--spec PATH --out FILE [--repo .]` | `FILE`, `FILE.escalate.json` |
| `calibrate` | 4 | `--fixtures DIR [--live] [--write-thresholds]` | `scripts/jev-thresholds.json` only when `--write-thresholds` is passed |
| `ac-shadow` | 5 | `--story FILE --tests-output FILE --diff FILE --review-output FILE [--log PATH]` | appends one row to `PATH` (default `.writ/state/jev-shadow.jsonl`) |
| `shadow-report` | 5 | `[--log PATH]` | stdout only |

- **Output:** one verdict line (`pass` / `fail` / `unverifiable`), zero or more `reason: <code>` lines, and a summary line last.
- **Summary:** includes `model=<id>`, `input_tokens=<n>` when a request was made, and subcommand counts.
- **Exit codes:** 0 for `pass` or `unverifiable`; 1 for `fail`; 2 for usage errors.

### Reason codes

| Code | Verdict | Meaning |
|---|---|---|
| `enabled` | pass | Both opt-in halves present (`status` only); summary carries `backend=<name>` |
| `model_unpinned` | (informational) | `vercel-gateway` backend: alias only, version drift undetectable |
| `provider_disabled` | unverifiable | Config line is `none` or an unknown value |
| `no_config_line` | unverifiable | `.writ/config.md` missing or has no `Judgment Provider` line (triggers the Story 6 prompt in interactive runs) |
| `no_api_key` | unverifiable | Named backend's key is empty; summary names the env var |
| `transport_error` | unverifiable | Network, DNS, timeout, 5xx other than 529 |
| `auth_error` | unverifiable | HTTP 401 |
| `request_invalid` | unverifiable | HTTP 422, or 404 `model_not_found` from the gateway (body logged to stderr, truncated to 500 chars) |
| `rate_limited` | unverifiable | 429/529 after 3 attempts |
| `state_too_large` | unverifiable | State + longest question estimated > 30,000 tokens |
| `replay_miss` | unverifiable | Replay transport has no recorded response for the request hash |
| `model_mismatch` | unverifiable | `typesafe` backend: response `model` ≠ `jev-1.13.0`; answers are not applied |
| `malformed_response` | fail | Response missing `answers`, or an answer missing its typed field |
| `no_evaluator_ids` | unverifiable | `ac-shadow` found no `[AC-N.M]` tags in review output |
| `no_live_run` | unverifiable | `calibrate` ran with no recorded responses and no `--live` |
| `promotion_met` / `promotion_not_met` | pass / unverifiable | `shadow-report` result against Business Rule 8 |

## 2. Opt-in resolution

- The config line is matched with `^- \*\*Judgment Provider:\*\*\s*(\S+)`, compared case-insensitively to `typesafe`, `vercel-gateway`, or `none`.

| Backend | Base URL | Key env (first non-empty wins) | `model` sent | Extra body |
|---|---|---|---|---|
| `typesafe` | `https://api.typesafe.ai` | `TYPESAFE_API_KEY` | `jev-1.13.0` | — |
| `vercel-gateway` | `https://ai-gateway.vercel.sh/typesafe` | `AI_GATEWAY_API_KEY`, `VERCEL_OIDC_TOKEN` | `typesafe-ai/jev` | `"providerOptions": {"gateway": {"only": ["typesafe-ai"]}}` |

- Both backends use the same path (`/v1/systemone`), request shape, and response shape.
- The gateway adds `provider_metadata.gateway` (routing, cost). The client records `cost` when present.
- Gateway errors use `{"error": {"message", "type"}}`; TypeSafe's use `{"message", "error_type"}`. The client reads both.
- **Verified 2026-09-25** against `vercel-gateway` with dummy state: `typesafe-ai/jev` → 200, Noul 0.01, `input_tokens=280`, ~0.5 s. `typesafe-ai/jev-1.13.0` → 404 `model_not_found`. The `only` option restricted the providers tried to `typesafe-ai`.
- The key is never printed, logged, or written to any file.

## 3. Transport

```
POST <base>/v1/systemone
Authorization: Bearer <backend key>
Content-Type: application/json
{"model": <backend model>, "state": <object>, "questions": {<id>: {"type": "noul", "instructions": ..., "criteria": {"true": ..., "false": ...}}}}
```

- `urllib.request.urlopen(req, timeout=10)`.
- Retries: 429/529 only. Up to 3 attempts; sleep `retry-after` seconds when present, otherwise 1, then 2, then 4.
- Replay: when `WRIT_JEV_REPLAY` is set, the request body is canonicalized (`json.dumps(sort_keys=True, separators=(",", ":"))`) and hashed with SHA-256. The script reads `<dir>/<hash>.json`. A missing file gives `replay_miss`. `calibrate --live` writes new files with the same key.
- Token estimate: `len(json.dumps(state)) + max(len(json.dumps(q)) for q in questions)`, divided by 4.
- Question IDs are code-side only. Each question's instructions reference state by backticked path (for example ``Do two criteria in `stories["story-2-x.md"].criteria` require outcomes that cannot both hold?``), following TypeSafe state guidance.

## 4. Thresholds file — `scripts/jev-thresholds.json`

```json
{
  "backend": null,
  "model": null,
  "calibrated": false,
  "calibrated_on": null,
  "spec_findings": {
    "contradiction": {"emit": 0.85, "escalate": 0.35},
    "gap":           {"emit": 0.85, "escalate": 0.35},
    "ambiguity":     {"emit": 0.85, "escalate": 0.35}
  },
  "ac_shadow": {"satisfied": 0.9}
}
```

- The starting values are deliberately conservative: a wide escalation band means more stories go back to the orchestrator.
- Story 4 replaces them and sets `"calibrated": true`, `backend`, `model`, and `calibrated_on` only after a scored run.
- When `calibrated` is true and the active backend or model differs from the recorded ones, the loader reports `uncalibrated_thresholds` and keeps using the values.
- `spec-findings` adds the reason `uncalibrated_thresholds` to its output while `calibrated` is `false`. That reason is informational and does not change the verdict.

## 5. Error & Rescue Map

| Operation | What can go wrong | Handling | What the user sees |
|---|---|---|---|
| Resolve opt-in | Config line absent / `none` or unknown / key empty | `unverifiable no_config_line` / `provider_disabled` / `no_api_key` (DEV-001) | `jev: disabled (<reason>)` note; today's path; `no_config_line` in an interactive run triggers the Story 6 prompt |
| Build request | State over budget | `unverifiable state_too_large`; story escalated | Note names the story; orchestrator pass covers it |
| POST /v1/systemone | Timeout, DNS, 5xx | `unverifiable transport_error` | `jev: unverifiable (transport_error)` note; full orchestrator pass |
| POST /v1/systemone | 401 | `unverifiable auth_error` | Same note with `auth_error`; hint names the backend's key var |
| POST /v1/systemone | 422 | `unverifiable request_invalid`; body to stderr | Same note; a bug report is warranted |
| POST /v1/systemone | 429/529 ×3 | `unverifiable rate_limited` | Same note; full orchestrator pass |
| Parse response | Missing `answers` / typed field | `fail malformed_response` | Note only (Step 2.6c never fails the package) |
| Parse response | `model` ≠ pinned | `unverifiable model_mismatch`; answers discarded | Note names both IDs |
| Apply thresholds | p in escalation band | Story listed in `.escalate.json` | Note: `N judged, M escalated` |
| Write findings | Out path unwritable | Exit 2 on stderr | Existing command error path (`add_finding`) |
| Shadow parse | No `[AC-N.M]` in review output | `unverifiable no_evaluator_ids`; no row | `jev-shadow: skipped (no_evaluator_ids)` |
| Shadow log append | `.writ/state/` missing | Create directory; append | Silent |

## 6. Shadow Paths

| Path | Input | Expected |
|---|---|---|
| Happy | Enabled; all stories confident | Findings JSON; empty escalate list; no orchestrator AC pass |
| Nil | Provider disabled | `unverifiable provider_disabled`; commands unchanged |
| Empty | Spec with zero stories | `unverifiable no_stories`; no request sent (mirrors `spec-analyze.py`'s `spec_unreadable` for a missing story set) |
| Upstream error | 429 then success | One retry; findings written; summary shows `attempts=2` |
| Partial | 1 of 5 stories escalated | Findings for 4; orchestrator pass over 1; merged JSON passes `spec-analyze.py` schema |

## 7. Interaction Edge Cases

| Case | Behavior |
|---|---|
| Key set, config line absent | Disabled. No request is sent (Business Rule 1). Interactive runs get the Story 6 prompt |
| Both `TYPESAFE_API_KEY` and `AI_GATEWAY_API_KEY` set | The config line decides the backend; the other key is ignored |
| User pastes a key into the setup prompt's free-text field | Not stored; the prompt text tells them to export it instead and warns that the transcript now holds it |
| Replay env set during a live command run | Replay wins. Tests and eval can never reach the network |
| Evaluator lines lack IDs (older agent file) | `no_evaluator_ids`; shadow skipped; Gate 3 unaffected |
| Response from `jev-1.14.0` after alias drift | `typesafe`: cannot happen with a pinned ID; if it does, `model_mismatch` and answers are discarded. `vercel-gateway`: undetectable (response echoes the alias); `model_unpinned` on every output says so |
| Diff contains `.env.local` | Excluded; summary `excluded_paths=1` |

## 8. Files in scope

| File | Story | Change |
|---|---|---|
| `.writ/decision-records/adr-027-optional-judgment-provider.md` | 1 | New |
| `scripts/jev-judge.py` | 1–5 | New; grows one subcommand per story |
| `scripts/tests/test_jev_judge.py` | 1–5 | New pytest file |
| `scripts/jev-thresholds.json` | 2, 4 | New; calibrated in 4 |
| `scripts/tests/fixtures/jev-replay/` | 2–5 | Recorded responses |
| `scripts/tests/fixtures/spec-analyze/` | 4 | Grow to ≥20 labeled stories |
| `scripts/eval.sh` + `scripts/tests/test_eval_jev_judge.sh` | 2 | New `jev-judge` check |
| `commands/create-spec.md` | 3 | Step 2.6c conditional sub-step |
| `commands/verify-spec.md` | 3 | One line in the spec-analyze advisory check |
| `agents/evaluator-agent.md` | 5 | `[AC-N.M]` on checklist lines |
| `commands/implement-story.md` | 5 | One Gate 3 shadow line |
| `commands/create-spec.md` | 6 | One-time setup AskQuestion in Step 2.6c; amend "does not open an AskQuestion gate" to exempt the configuration prompt |
| `.writ/config.md` | 6 | Written only by `setup`; this repo may set `vercel-gateway` (it has `AI_GATEWAY_API_KEY`) |
