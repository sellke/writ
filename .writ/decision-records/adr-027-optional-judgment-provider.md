# ADR-027: Optional Judgment Provider — Jev Replaces a Verdict Source, Behind a Double Opt-in

> **Date:** 2026-09-25
> **Status:** Accepted
> **Category:** Framework Architecture
> **Extends:** [ADR-022](adr-022-autonomy-gate-classes.md) (nothing leaves the machine without a human gate; here the gate is the config line), [ADR-023](adr-023-stakes-proportional-diligence.md) (pilot where errors are cheap)
> **Constrains:** [ADR-024](adr-024-model-delegation.md) Decision 3 — not amended; this ADR records why a Jev call is outside it. [ADR-025](adr-025-friction-signals.md) — not extended; shadow rows are not signals
> **Deciders:** @AdamSellke
> **Spec:** [`2026-09-25-jev-judgment-pilot`](../specs/2026-09-25-jev-judgment-pilot/spec.md)
> **Origin:** [`2026-09-25-jev-typed-judgments-for-harness-gates.md`](../issues/improvements/2026-09-25-jev-typed-judgments-for-harness-gates.md)

## Decision

**Writ may ask TypeSafe's Jev model for bounded, typed judgments, but only when the user has opted in twice, only from one separate script, and only where a wrong answer falls back to what Writ does today.** Nothing in this spec lets a Jev answer decide a gate or skip an agent spawn.

1. **One caller.** `scripts/jev-judge.py` is the only file that talks to Jev. It is Python 3.9 stdlib (`urllib.request`, `json`, `hashlib`); there is no SDK dependency. It writes JSON that existing scripts already accept (`spec-analyze.py --findings`) or a local log. Verifier scripts stay key-free.

2. **Double opt-in.** The provider is enabled only when both halves are present:
   - `.writ/config.md` has the line `- **Judgment Provider:** <backend>`, where `<backend>` is `typesafe` or `vercel-gateway`, and
   - that backend's key is set and non-empty in the environment.

   A key alone never enables it. A key in the shell for other work is not consent to send spec text. `none` or any unknown value disables it. `jev-judge.py status` reports the result: `pass` with `reason: enabled`, or `unverifiable` with `provider_disabled`, `no_config_line`, or `no_api_key`. The key value is never printed, logged, or written.

3. **Two backends, one request shape.** Both call `POST <base>/v1/systemone` with the same request and response body.

   | Backend | Endpoint | Key env (first non-empty wins) | `model` sent | Extra body |
   |---|---|---|---|---|
   | `typesafe` | `https://api.typesafe.ai/v1/systemone` | `TYPESAFE_API_KEY` | `jev-1.13.0` (pinned) | — |
   | `vercel-gateway` | `https://ai-gateway.vercel.sh/typesafe/v1/systemone` | `AI_GATEWAY_API_KEY`, then `VERCEL_OIDC_TOKEN` | `typesafe-ai/jev` (alias) | `"providerOptions": {"gateway": {"only": ["typesafe-ai"]}}` |

4. **Pinned where the backend allows it.**
   - On `typesafe`, the client sends `jev-1.13.0`. A response whose `model` differs is `unverifiable model_mismatch`, and its answers are discarded.
   - On `vercel-gateway`, only the alias `typesafe-ai/jev` is accepted. The versioned ID `typesafe-ai/jev-1.13.0` returns 404 `model_not_found`. Responses echo the alias ([vercel/ai #21213](https://github.com/vercel/ai/issues/21213)), so a version change behind the alias cannot be detected. Every `vercel-gateway` output carries the informational reason `model_unpinned`, and thresholds record that they were calibrated against the alias on a date.

5. **Gateway routing is restricted.** Unrestricted, the gateway tried DigitalOcean first (503) and then TypeSafe. Every `vercel-gateway` request sends `providerOptions: {"gateway": {"only": ["typesafe-ai"]}}`, which limits the providers tried to `typesafe-ai`. State then reaches Vercel and TypeSafe only.

6. **Cascade, not replacement.** An answer below its calibrated threshold is never acted on; the item goes back to the path Writ uses today. Disabled, over budget, rate-limited, or failed calls are `unverifiable` (exit 0). Only a malformed response is `fail`, and even that is a note.

7. **Where it runs in this spec.** `/create-spec` Step 2.6c, which is advisory, uses Jev in place of the orchestrator's LLM pass for stories Jev answers confidently. `/implement-story` Gate 3 runs Jev in shadow mode beside the evaluator and only records the result. The evaluator still spawns on every story.

Facts above were checked live on 2026-09-25. Jev pricing on that date: $0.042 per million input tokens; output tokens are free. The gateway's model entry lists `zdr: none`.

## Context

### What forced the decision

Several Writ gates make small semantic judgments with a known answer set: does an acceptance criterion contradict another, is a criterion ambiguous, did the diff satisfy it. Today each costs an anchor-tier spawn or a round of orchestrator reasoning. Jev returns typed answers (Noul, Choice, Score) with a probability attached, so code can act on confident answers and route the rest to the current path. The source issue lists the candidate sites and ranks them.

Three existing rules stand in the way: Writ ships with no runtime dependency and no network call in its methodology path; Phase 11 Stage 3 put "no API key in the script" into `spec-analyze.py`'s contract; and ADR-024 Decision 3 says the `floor` tier never crosses vendors. Each is reconciled below.

### Precedent

`scripts/measure-invocation.py` already calls Anthropic's `count_tokens` endpoint over `urllib` when `ANTHROPIC_API_KEY` is set. It is a maintainer measurement tool, it sends only Writ's own markdown, and no command step runs it. Jev is different on all three counts: it runs from command steps, it sends the user's project content, and it is paid. That is why it needs a config line as well as a key.

## Reconciliation With Existing Rules

**ADR-024 Decision 3 (floor never crosses vendors).** ADR-024 governs which model runs an *agent*. Its family lock exists because agent prompts are tuned to the anchor's instruction-following, a cross-family model may truncate the context `/implement-story` routes to each gate, and a same-family floor keeps the audit trail predictable. None of that applies here. Jev is not assigned an agent, is not given an agent prompt, and does not receive a gate's context payload. It answers typed questions built by code and returns a probability that code thresholds. Jev replaces a *verdict source* (the orchestrator's findings pass, and in shadow the evaluator's per-criterion line), not an agent tier. `model_tier` values, their resolution, and the escalation rule are unchanged.

**Phase 11's "no API key in verifier scripts" rule.** The rule stays as written. `spec-analyze.py`, `review-override.py`, and every other verifier remain key-free and network-free; this spec does not change what they accept. The Jev call lives in a separate caller, `jev-judge.py`, which writes JSON in the schema `spec-analyze.py check --findings` already validates (extra keys `source` and `p` are ignored by that check). A verifier cannot tell whether its input came from the orchestrator or from Jev, which is the point of the rule: the verifier's verdict never depends on a network call.

**ADR-025 (friction signals).** Gate 3 shadow rows go to `.writ/state/jev-shadow.jsonl`, a separate file written only by `jev-judge.py ac-shadow`. They are measurement rows, not friction signals: they are written on every evaluated story whether or not anything struggled, they are read only by `jev-judge.py shadow-report`, and they never enter `.writ/state/signals.jsonl`. ADR-025's closed vocabulary of six kinds is unchanged. A Jev failure (`transport_error`, `rate_limited`, and so on) is a note in the command output and does not emit a `degraded` signal in this spec; adding one would require amending ADR-025.

## Decision Drivers (force-ranked)

1. **No silent new failure mode.** An uncertain or failed Jev answer must fall back to today's path, and no gate outcome may depend on Jev until evidence says it can.
2. **Consent before data leaves the machine.** Sending spec text is a choice the user makes on purpose, per project.
3. **Portability and the 3.9 floor.** No new dependency, nothing to install.
4. **Evidence before promotion.** The high-value site (the evaluator) is measured in shadow before anything is skipped.
5. **Cost.** Fewer orchestrator reasoning passes on the advisory site.

## Considered Options

### A. No provider (keep today's orchestrator pass and evaluator only)
- **Pros:** Nothing to build. No network, no key, no privacy question.
- **Cons:** Every bounded judgment keeps costing an orchestrator pass or an anchor spawn. There is no way to collect evidence on whether a typed judgment could replace any of them.
- **Risk:** Low. The cost is opportunity, not breakage.

### B. Depend on the `typesafe_sdk` Python package
- **Pros:** Maintained client, typed request builders, less code of our own.
- **Cons:** Writ's first runtime dependency. `install.sh` copies `scripts/*` into projects that have no virtualenv; the macOS 3.9 floor would need a pip step. The SDK does not cover the Vercel gateway's routing options or its error shape. The request is one POST with a JSON body, which `urllib` handles.
- **Risk:** Medium. A dependency breaks the zero-install promise for every user, including the ones who never enable Jev.

### C. Put the Jev call inside `spec-analyze.py`
- **Pros:** One script, one invocation at Step 2.6c.
- **Cons:** Breaks Phase 11's rule directly: a verifier would hold a key and its verdict would depend on a network call. The structural checks, which are deterministic today, would share a process with a paid call. Gate 3 shadow would need a second home anyway.
- **Risk:** Medium. It mixes a checker with the thing being checked.

### D. Replace the evaluator now
- **Pros:** The largest payoff. The evaluator is the biggest recurring spawn on the default path.
- **Cons:** No calibration data exists. A false pass at Gate 3 ships an unmet criterion, and nothing downstream catches it. Jev's documented weaknesses (literal reading, counting, numeric comparison, accuracy loss on large irrelevant state) are exactly the ones an evaluator hits on real diffs.
- **Risk:** High. It trades a measured cost for an unmeasured failure mode.

### E. Separate stdlib caller, double opt-in, advisory pilot plus Gate 3 shadow — **chosen**
- **Pros:** Meets all five drivers. Disabled means byte-for-byte today's behavior. Verifiers stay key-free. The advisory site gets the savings now; the high-value site collects the evidence a later spec needs.
- **Cons:** One more script to ship. Two backends to keep in step. Shadow mode costs a Jev call per story with no saving until promotion.
- **Risk:** Low. Every failure path ends on today's path.

## Decision Outcome

**Option E.** Driver 1 rejects D. Driver 3 rejects B. Phase 11's rule, which this ADR keeps, rejects C. Option A fails driver 4: it collects no evidence, so the question never gets answered.

**What is explicitly NOT decided:** skipping or conditioning the evaluator spawn (a later spec, under the promotion rule below); any other candidate site from the source issue (drift severity, roadmap-to-spec matching, cross-spec overlap, knowledge relevance, `--recommend` auto-adopt calls, and the smaller classifications); a Jev-related ADR-025 signal kind.

## Consequences

### Privacy exposure

When the provider is enabled, Writ sends project content to a third party:
- **Step 2.6c:** spec text — each story's user-story block and acceptance criteria.
- **Gate 3 shadow:** acceptance criteria, recorded test output, and diff slices.

On `typesafe`, that content goes to TypeSafe. On `vercel-gateway`, it goes to Vercel and TypeSafe (the `only` restriction keeps it from other providers). The gateway's model entry lists `zdr: none`, so no zero-data-retention guarantee applies on that route. Diff slices exclude paths matching `.env*`, `*.pem`, `*.key`, `*secret*`, and `*credential*`, and each exclusion is counted in the output. That filter catches common secret files, not secrets pasted into ordinary source. The double opt-in exists so this exposure is a decision the user makes in `.writ/config.md`, not a side effect of having a key in the shell.

### Promotion rule

A later spec may make the evaluator spawn conditional on Jev only after `jev-judge.py shadow-report` shows all three of:
- **≥30 evaluated stories** in the shadow log;
- **zero false passes**, where a false pass is Jev at or above its "satisfied" threshold on a criterion the evaluator marked not satisfied;
- **≥95% per-criterion agreement** between Jev and the evaluator.

This rule is recorded here and enforced by no code in this spec. `shadow-report` computes and prints whether it is met; nothing reads that result to skip a spawn. A spec that wants to act on it must cite the report and this ADR.

### Positive

- Step 2.6c's orchestrator pass runs only over the stories Jev could not answer confidently, in one batched request per spec.
- The evaluator question gets measured instead of argued: the shadow log is the evidence the promotion rule reads.
- With the provider disabled, nothing changes. Users who never set the config line never see a network call.
- The request, thresholds, and replay fixtures are committed, so pytest and `eval.sh` never touch the network.

### Negative

- **First paid third-party call from a command step.** *Mitigation:* double opt-in; `status` reports why it is on or off; every failure is `unverifiable` and falls back.
- **Silent model drift on `vercel-gateway`.** The alias can change model version with no signal in the response. *Mitigation:* `model_unpinned` on every gateway output; thresholds record the alias and calibration date; `typesafe` remains the pinned option.
- **Calibration can go stale.** Thresholds fit one model version on a small fixture set (≥20 stories). *Mitigation:* the loader reports `uncalibrated_thresholds` when the active backend or model differs from the recorded one; the escalation band starts wide.
- **Two backends to maintain.** Error bodies differ (`{"error": {"message", "type"}}` vs `{"message", "error_type"}`). *Mitigation:* one client reads both; the request and response bodies are otherwise identical.
- **Shadow mode costs money with no saving yet.** *Mitigation:* input is $0.042 per million tokens and output is free; a 10,000-token shadow row costs about $0.0004. The promotion rule defines when the shadow period can end.

## Implementation Plan

Tracked in [`2026-09-25-jev-judgment-pilot`](../specs/2026-09-25-jev-judgment-pilot/spec.md):

1. This ADR and `jev-judge.py status` (opt-in resolution).
2. Client transport: timeout, 429/529 backoff, state-size guard, replay transport; `eval.sh` `jev-judge` check.
3. `spec-findings` and the Step 2.6c cascade.
4. Calibration: labeled fixtures, `calibrate`, `scripts/jev-thresholds.json`.
5. Gate 3 shadow: `ac-shadow`, `shadow-report`, `[AC-N.M]` tags on evaluator checklist lines.
6. `setup --provider` and the one-time Step 2.6c prompt, which never collects a key.

## References

- Spec: [`../specs/2026-09-25-jev-judgment-pilot/spec.md`](../specs/2026-09-25-jev-judgment-pilot/spec.md), technical spec §1–§2
- Source issue: [`../issues/improvements/2026-09-25-jev-typed-judgments-for-harness-gates.md`](../issues/improvements/2026-09-25-jev-typed-judgments-for-harness-gates.md)
- [ADR-024](adr-024-model-delegation.md) Decision 3 — family-locked floor
- [ADR-025](adr-025-friction-signals.md) — closed signal vocabulary
- Phase 11 Stage 3: [`../specs/2026-09-08-phase11-stage3-spec-analysis/spec.md`](../specs/2026-09-08-phase11-stage3-spec-analysis/spec.md) — "Do not add an API key dependency"
- vercel/ai issue #21213 — gateway responses echo the requested alias
