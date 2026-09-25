# Jev Judgment Pilot

> **Status:** Not Started
> **Created:** 2026-09-25
> **Owner:** @unknown
> **Dependencies:** [2026-09-08-phase11-stage3-spec-analysis, 2026-09-09-phase11-stage4b-pipeline-demote]
> **Origin:** Promoted from issue: [`.writ/issues/improvements/2026-09-25-jev-typed-judgments-for-harness-gates.md`](../../issues/improvements/2026-09-25-jev-typed-judgments-for-harness-gates.md). Authored under `/create-spec --recommend --from-issue`; autonomous decisions are in [`recommendation-log.md`](recommendation-log.md).

## Specification Contract

**Deliverable:** An opt-in TypeSafe Jev judgment provider for Writ. It has four parts:
- ADR-027, which records the decision.
- `scripts/jev-judge.py`, a Python 3.9 stdlib client.
- A Jev-backed findings producer that replaces the orchestrator LLM pass in `/create-spec` Step 2.6c whenever the provider is enabled.
- A calibration record, plus a Gate 3 shadow log that puts Jev's per-criterion judgment next to the evaluator's verdict.

With the provider disabled, Writ behaves byte-for-byte as it does today.

**Must Include:**
- Two backends behind one client, both using TypeSafe's request shape:
  - `typesafe`: `https://api.typesafe.ai`, key `TYPESAFE_API_KEY`.
  - `vercel-gateway`: `https://ai-gateway.vercel.sh/typesafe`, key `AI_GATEWAY_API_KEY` or `VERCEL_OIDC_TOKEN`.
- A double opt-in: a `.writ/config.md` line naming the backend **and** that backend's key in the environment.
- A one-time setup prompt, the first time an interactive Jev-capable step runs with no config line. It never asks for the key value in chat.
- The existing verdict contract: `pass` / `fail` / `unverifiable`, `reason:` lines, summary last, exit codes 0/1/2.
- A low-confidence or failed call becomes `unverifiable`, never `fail`.
- A pinned model ID where the backend allows one: `jev-1.13.0` on `typesafe`. On `vercel-gateway`, only the alias `typesafe-ai/jev` is accepted, and responses echo the alias, so thresholds are recorded as calibrated against the alias and its date.
- Committed recorded responses, so pytest and `eval.sh` never touch the network.

**Hardest Constraint:** Jev must replace orchestrator work without becoming a new way to be wrong silently. Three rules follow:
- Every uncertain answer falls back to the path Writ uses today (a cascade, not a replacement).
- No gate's pass/fail outcome may depend on Jev in this spec.
- The evaluator keeps spawning on every story; shadow mode only records.

**Stories:**

1. **ADR-027 + opt-in resolution.** The decision record, plus `jev-judge.py status`, which reports enabled or disabled and why.
2. **Client transport.** Stdlib `urllib` POST to `/v1/systemone`, with timeout, 429/529 backoff, a state-size guard, error → `unverifiable`, and a replay transport for tests. Adds the `eval.sh` `jev-judge` check.
3. **Spec-findings producer + Step 2.6c cascade.** `jev-judge.py spec-findings` writes `spec-analyze.py --findings` JSON. Stories Jev can't call confidently are handed back to the orchestrator pass.
4. **Calibration.** Grow the labeled fixture set, add `jev-judge.py calibrate`, and commit the thresholds file and a per-class precision/recall record.
5. **Gate 3 shadow.** `jev-judge.py ac-shadow` logs a per-criterion Jev judgment beside the evaluator verdict. `shadow-report` computes agreement against the promotion rule written in ADR-027.
6. **Setup prompt.**
   - `jev-judge.py setup --provider {typesafe,vercel-gateway,none}` writes the config line (never a key).
   - `/create-spec` Step 2.6c asks once, via AskQuestion, when the line is absent and the run is interactive.
   - The prompt names the env var to export; it never collects the key.

**Success Criteria:**
- With no config line or no key, `jev-judge.py status` prints `unverifiable` with reason `provider_disabled`. `/create-spec` and `/implement-story` take their current paths. The full pytest suite and `bash scripts/eval.sh` pass with no network access.
- With the provider enabled, Step 2.6c runs no orchestrator AC reasoning for stories Jev answered above threshold. The orchestrator pass runs only over the stories Jev returned as uncertain.
- `scripts/jev-thresholds.json` and the calibration record give TP/FP/FN per class (contradiction, gap, ambiguity, clean) on at least 20 labeled stories, scored from committed recorded responses.
- In an interactive `/create-spec` with no `Judgment Provider` line, Step 2.6c asks the setup question once. The answer writes the line (or nothing, for "Not now") and no key ever appears in the transcript, in `.writ/config.md`, or in any output.
- Gate 3 appends one shadow row per evaluated story. `shadow-report` prints agreement, false-pass count, and whether ADR-027's promotion rule is met. Nothing reads the result to skip a spawn.

**Scope Boundaries:**
- **Included:**
  - ADR-027.
  - Both backends (`typesafe`, `vercel-gateway`).
  - The `setup` subcommand and the one-time Step 2.6c prompt.
  - `scripts/jev-judge.py` (`status`, `spec-findings`, `calibrate`, `ac-shadow`, `shadow-report`).
  - `scripts/jev-thresholds.json`.
  - Recorded-response fixtures.
  - The `/create-spec` Step 2.6c and `/verify-spec` advisory-check wiring.
  - A Gate 3 shadow hook in `/implement-story`.
  - `[AC-N.M]` tags on the evaluator's per-criterion checklist lines.
  - The `eval.sh` `jev-judge` check.
- **Excluded:**
  - Skipping or conditioning the evaluator spawn (a later spec, and only once the ADR-027 promotion rule is met).
  - Drift severity, roadmap→spec matching, cross-spec overlap, knowledge relevance or dedupe, `--recommend` auto-adopt calls, `/create-issue` and `/knowledge` classification, `/prototype` UI detection, `/release` categorization. All of these are listed in the source issue as follow-ups.
  - The Python `typesafe_sdk` dependency.
  - Any change to `spec-analyze.py`, `review-override.py`, or other verifier scripts beyond what they already accept.
  - Friction-signal kinds (ADR-025).
  - The test-integrity bash false positive, which has its own issue.

**⚠️ Technical Concerns:**
- This is the first paid third-party network call in Writ's product source. ADR-027 must reconcile it with the no-dependency posture, Phase 11's "no API key in verifier scripts" rule, and ADR-024 Decision 3 (floor never crosses vendors). The reconciliation: Jev replaces a *verdict source*, not an agent tier, and it lives in its own caller that hands JSON to scripts that already accept it.
- Calibration needs a live key at implementation time. This repo has `AI_GATEWAY_API_KEY`: a dummy call on 2026-09-25 returned Noul 0.01 for "Did the build succeed?" on an exit-code-1 state. So Story 4 can run live through `vercel-gateway`. Without any key, Story 4 records `unverifiable no_live_run` and keeps the starting thresholds.
- **Gateway routing.**
  - Unrestricted, the gateway tried DigitalOcean first (503), then TypeSafe.
  - `vercel-gateway` requests always send `providerOptions.gateway.only: ["typesafe-ai"]`, so state goes only to Vercel and TypeSafe. Verified 2026-09-25: providers tried, `typesafe-ai` only.
- **Gateway model pinning.**
  - Versioned IDs (`typesafe-ai/jev-1.13.0`) return 404 `model_not_found`.
  - The response `model` echoes the alias (vercel/ai #21213).
  - Silent version drift behind the alias cannot be detected on this backend. ADR-027 must state this.
- State sent to Jev includes spec text, test output, and diff slices. That is a privacy exposure the user must knowingly accept.
- Gate 2.5 `change_surface` does not reach the evaluator on the default path. This spec does not fix that; shadow mode builds its own diff slice.

**💡 Recommendations:**
- Pilot where errors are cheap (Step 2.6c is advisory) and collect evidence where the payoff is large (the evaluator is the largest recurring spawn).
- Batch every question for one spec into a single request. Jev evaluates questions in parallel, and TypeSafe's parallel-questions cookbook reports roughly 10× lower latency than one call per question.
- Keep counting, thresholds, and token estimates in code (jev-1.13 jaggedness: counting, numeric comparison, indirection).

**⚠️ Cross-Spec Overlap:** None. Every spec under `.writ/specs/*/spec.md` resolves complete-family.

---

## 🎯 Experience Design

**Entry point.** There are two routes:
- The first interactive `/create-spec` that reaches Step 2.6c asks: set up Jev via TypeSafe, via Vercel AI Gateway, not now, or never.
- Or the maintainer runs `jev-judge.py setup --provider <name>` directly.

Either writes `- **Judgment Provider:** <name>` to `.writ/config.md` and prints the one env var to export (`TYPESAFE_API_KEY` or `AI_GATEWAY_API_KEY`). After that, nothing new to run: `/create-spec`, `/verify-spec`, and `/implement-story` call the provider at their existing steps.

**Happy path.**
1. `/create-spec` reaches Step 2.6c.
2. The orchestrator runs `jev-judge.py spec-findings --spec <folder> --out <json>` instead of reading every criterion itself.
3. Jev answers all stories in one request. Confident answers become findings; stories with uncertain answers are listed in the output.
4. The orchestrator runs its own LLM pass over only those stories and merges the results.
5. `spec-analyze.py check --findings <json>` verifies the merged file, exactly as today.

**Moment of truth.** A five-story spec comes back with findings for four stories from Jev in one call. The orchestrator reads one story instead of five. Step 2.9's note line reads `jev: 4/5 stories judged, 1 escalated`.

**Feedback model.**
- Each subcommand prints one verdict line, optional `reason:` lines, and a summary last.
- The summary names the model ID that answered (from the response's `model` field), the count of judged vs escalated stories, and the input tokens from `usage`.
- Shadow rows are silent in the story report except for one note line.

**Error experience.**
- Disabled provider: `unverifiable provider_disabled`. The command takes today's path with no extra output beyond the note.
- Network error, timeout, 401, 422, or rate-limit exhaustion: `unverifiable` with a named reason (`transport_error`, `auth_error`, `request_invalid`, `rate_limited`). The orchestrator runs the full existing pass. No gate fails and no story is marked `DEGRADED`.
- State over budget: `unverifiable state_too_large`. That story is escalated; nothing is truncated.

### State Catalog

| State | What the user sees |
|---|---|
| Not configured, interactive | One-time AskQuestion at Step 2.6c (TypeSafe / Vercel AI Gateway / Not now / Never); then today's path for this run |
| Not configured, `--recommend` or non-interactive | `jev: not configured (no_config_line)` note; today's path |
| Provider named, key missing | `jev: unverifiable (no_api_key) — export AI_GATEWAY_API_KEY` note; no re-prompt |
| Disabled (`none`) | Nothing new. One `jev: disabled (provider_disabled)` note in Step 2.9 |
| Enabled, all confident | Findings note with judged count; no orchestrator AC pass |
| Enabled, partial | Findings note naming the escalated stories; orchestrator pass over those only |
| Enabled, transport failure | `jev: unverifiable (<reason>)` note; full orchestrator pass |
| Shadow at Gate 3 | One note: `jev-shadow: logged N criteria` or `jev-shadow: skipped (<reason>)` |

---

## 📋 Business Rules

1. **Double opt-in.** The provider is enabled only when `.writ/config.md` carries `**Judgment Provider:** typesafe` (with `TYPESAFE_API_KEY`) or `vercel-gateway` (with `AI_GATEWAY_API_KEY` or `VERCEL_OIDC_TOKEN`), **and** that key is non-empty. A key alone never sends data, because a key present in the shell for other work is not consent to send spec text.
2. **Verdict contract.** Every subcommand emits the Stage 2b helper shape. Low confidence, disabled, over budget, and transport failure are all `unverifiable` (exit 0). Only a malformed response or an internal defect is `fail` (exit 1). Usage errors exit 2.
3. **Cascade, not replacement.** A Jev answer below its threshold is never acted on. The item goes back to the path Writ uses today.
4. **Advisory only.** No `pass`/`fail` gate outcome in `/create-spec`, `/verify-spec`, or `/implement-story` depends on Jev in this spec. Step 2.6c findings stay notes, as they are today.
5. **Pinned model where possible.**
   - `typesafe` sends `model: "jev-1.13.0"`. A response whose `model` differs is reported as `model_mismatch`, and its answers are discarded.
   - `vercel-gateway` sends `typesafe-ai/jev`, the only ID the gateway accepts. Its outputs carry the informational reason `model_unpinned`.
   - Every output records the response's `model` field and the backend.
   - Thresholds record which backend and model ID they were calibrated against.
6. **No network in tests or eval.** pytest and `eval.sh` use a replay transport over committed recorded responses. The live transport runs only from command steps and `calibrate --live`.
7. **Secret-path exclusion.** Diff slices sent at Gate 3 exclude paths matching `.env*`, `*.pem`, `*.key`, `*secret*`, and `*credential*`, and each exclusion is counted in the output.
8. **Promotion rule (recorded in ADR-027, enforced by no code here).** A later spec may make the evaluator spawn conditional only after `shadow-report` shows all three of: ≥30 evaluated stories; zero false passes (Jev ≥ threshold "satisfied" where the evaluator said not satisfied); ≥95% per-criterion agreement.
9. **Stdlib only.** Python 3.9 floor, `urllib.request`, and `json`. No SDK dependency.
10. **Decision log.** Each story's closing commit appends `{date} jev-pilot: {what changed and why}` to `.writ/decision-log.md`.
11. **Gateway routing restricted.** Every `vercel-gateway` request sends `providerOptions: {"gateway": {"only": ["typesafe-ai"]}}`, so state reaches only Vercel and TypeSafe.
12. **Setup prompt, never key collection.**
    - The prompt appears only in an interactive run, at the first Jev-capable step (`/create-spec` Step 2.6c), when `.writ/config.md` has no `Judgment Provider` line.
    - Options: TypeSafe direct, Vercel AI Gateway, Not now (asked again next run), Never (writes `none`, never asked again).
    - It writes only the config line, then prints the one env var to export.
    - It never asks for, echoes, or stores a key value.
    - Under `--recommend` or any non-interactive run, it is a note, not a prompt.
    - With a provider named but its key missing, the result is `unverifiable no_api_key` plus a one-line export hint. There is no re-prompt.

---

## Detailed Requirements

### Opt-in resolution (Story 1)
`jev-judge.py status [--repo .]` reads `.writ/config.md` and the environment. It prints:
- `pass` with reason `enabled` and `backend=<name>` in the summary when the config line names `typesafe` or `vercel-gateway` and that backend's key is set.
- Otherwise `unverifiable` with one of these reasons:
  - `provider_disabled`: line is `none` or an unknown value;
  - `no_config_line`: `.writ/config.md` missing, or no line;
  - `no_api_key`: named backend's key is empty; the summary names the env var to export.

It never prints the key.

ADR-027 records:
- the decision;
- alternatives (no provider; SDK dependency; putting the call inside `spec-analyze.py`; replacing the evaluator now);
- the reconciliation with ADR-024 Decision 3, Phase 11's rule, and ADR-025;
- privacy;
- the promotion rule.

### Client (Story 2)
- One function, `judge(state, questions) -> response | Unverifiable(reason)`.
- 10-second timeout.
- Up to 3 attempts on 429/529 with exponential backoff, honoring `retry-after`.
- 401 → `auth_error`; 422 → `request_invalid`; other errors → `transport_error`.
- A state-size guard estimates tokens as characters ÷ 4 and refuses anything over 30,000 for state plus the longest question.
- The transport is injectable. `WRIT_JEV_REPLAY=<dir>` selects replay, keyed by a SHA-256 of the canonical request body.

### Spec findings (Story 3)
- One request per spec. State holds each story's user-story block and its criteria, keyed by filename.
- Questions per story:
  - Noul `contradiction`: two criteria require outcomes that cannot both hold.
  - Noul `gap`: the user story or criteria imply a nil, empty, or error case that no criterion covers.
- Question per criterion:
  - Noul `ambiguity`: two competent implementers could satisfy the criterion's Then with opposite behavior.
- Code applies `emit` and `escalate` thresholds from `jev-thresholds.json`:
  - p ≥ emit → finding;
  - escalate ≤ p < emit → the story goes on the escalation list;
  - p < escalate → clean.
- Output is a JSON array matching `spec-analyze.py`'s schema, with extra keys `source` and `p`, plus a sidecar `<out>.escalate.json` listing the escalated story filenames.

### Calibration (Story 4)
- Grow `scripts/tests/fixtures/spec-analyze/` to ≥20 labeled stories with ≥4 per class, keeping the four existing slugs.
- `calibrate --fixtures <dir> [--live]` scores recorded responses against `gold.json`. It prints TP/FP/FN per class and picks thresholds that give zero false positives on clean fixtures, then maximum recall.
- `--live` records fresh responses into the replay directory.
- The result is written to `scripts/jev-thresholds.json` and to Story 4's What Was Built.

### Gate 3 shadow (Story 5)
- `ac-shadow --story <file> --tests-output <file> --diff <file> --review-output <file> [--log .writ/state/jev-shadow.jsonl]`.
- Asks one Noul per criterion: is the criterion satisfied by the recorded test output and diff?
- Parses the evaluator's per-criterion lines by `[AC-N.M]` tag, then appends one JSONL row: story, model, per-criterion `p`, evaluator verdict, and agreement.
- `shadow-report [--log …]` prints the counts and whether rule 8 is met.
- `agents/evaluator-agent.md`'s Acceptance Criteria checklist lines gain a trailing `[AC-N.M]` tag.
- `/implement-story` Gate 3 runs `ac-shadow` after `review-override.py` when the provider is enabled. Any result is a note.

### Setup prompt (Story 6)
- `jev-judge.py setup --provider {typesafe,vercel-gateway,none} [--repo .]` inserts or replaces the `- **Judgment Provider:**` line in `.writ/config.md`. It prints `export <VAR>=...` guidance, and never reads or writes a key.
- `/create-spec` Step 2.6c: when `status` reports `no_config_line` and the run is interactive, present one AskQuestion.
  - Title: "Jev judgment provider".
  - Options: TypeSafe direct / Vercel AI Gateway / Not now / Never.
  - Map the answer to `setup --provider`; "Not now" writes nothing.
  - Then continue Step 2.6c on the existing path for this run.
  - Business Rule 12 governs everything else.

---

## Implementation Approach

- Python 3.9 stdlib script in the Stage 2b helper family: argparse subcommands, `--repo`/`--project`, one verdict line, `reason:` lines, summary last. Model it on `scripts/spec-analyze.py` and `scripts/drift-format.py`.
- `install.sh` already copies `scripts/*.py`.
- `scripts/jev-thresholds.json` ships beside the script.
- Recorded responses live under `scripts/tests/fixtures/jev-replay/`.
- Command edits are additive and short: one conditional sub-step in `create-spec.md` Step 2.6c, one line in `verify-spec.md`'s spec-analyze check, one line in `implement-story.md` Gate 3. Each names the script and says any outcome is a note.
- The `eval.sh` check `jev-judge` follows `check_spec_analyze()`:
  - missing helper or exit 2 → `add_finding`;
  - replay-mode `spec-findings` on a fixture → `add_note`;
  - never networked.

## Approved Scope Additions

_None yet._
