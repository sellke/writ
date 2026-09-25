# Jev Judgment Pilot (Lite)

> Source: .writ/specs/2026-09-25-jev-judgment-pilot/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Opt-in Jev provider. ADR-027 + `scripts/jev-judge.py` (stdlib), Step 2.6c cascade, calibration, Gate 3 shadow. Disabled = today's behavior.

**Implementation Approach:**
- Python 3.9 stdlib only (`urllib.request`, `json`, `hashlib`); no `typesafe_sdk`
- Stage 2b helper shape: one verdict line, `reason:` lines, summary last; exit 0/1/2
- One batched request per spec; Nouls per story (contradiction, gap) and per criterion (ambiguity)
- Thresholds from `scripts/jev-thresholds.json`; p in escalation band → story handed back to orchestrator
- Replay transport (`WRIT_JEV_REPLAY`, SHA-256 of canonical body) for all tests and eval
- Backends: `typesafe` (`api.typesafe.ai`, `TYPESAFE_API_KEY`, pinned `jev-1.13.0`) and `vercel-gateway` (`ai-gateway.vercel.sh/typesafe`, `AI_GATEWAY_API_KEY`, alias `typesafe-ai/jev`, `only: ["typesafe-ai"]`)
- Record backend, response `model`, `usage.input_tokens`, gateway `cost`
- `setup --provider` writes the config line only; Step 2.6c asks once when unconfigured (interactive only)

**Files in Scope:**
- `.writ/decision-records/adr-027-optional-judgment-provider.md` — new
- `scripts/jev-judge.py`, `scripts/jev-thresholds.json` — new
- `scripts/tests/test_jev_judge.py`, `scripts/tests/fixtures/jev-replay/` — new
- `scripts/tests/fixtures/spec-analyze/` — grow to ≥20 labeled stories
- `scripts/eval.sh`, `scripts/tests/test_eval_jev_judge.sh` — `jev-judge` check
- `commands/create-spec.md` (2.6c cascade + setup prompt), `commands/verify-spec.md`, `commands/implement-story.md` (Gate 3) — one short conditional each
- `agents/evaluator-agent.md` — `[AC-N.M]` on checklist lines

**Error Handling:**
- Disabled / transport / auth / 422 / rate-limit / over-budget / replay miss / model mismatch → `unverifiable`, today's path
- Malformed response → `fail`, still a note only
- Missing thresholds file → §4 defaults + informational `thresholds_missing` (DEV-011)
- See technical-spec.md §5 Error & Rescue Map

**Integration Points:** `spec-analyze.py --findings` (unchanged schema; extra keys `source`, `p`); `review-override.py` runs before shadow; `install.sh` copies `scripts/*`

---

## For Review Agents

**Acceptance Criteria:**
1. ADR-027 reconciles ADR-024 D3, Phase 11 no-key rule, ADR-025; states promotion rule `[AC-1.1, AC-1.2]`
2. Double opt-in; key alone sends nothing; key never printed `[AC-1.3, AC-1.4]`
3. Every transport failure maps to a named `unverifiable` reason; tests never network `[AC-2.1, AC-2.2, AC-2.4]`
4. Step 2.6c: orchestrator AC pass runs only over escalated stories; merged JSON passes spec-analyze `[AC-3.1, AC-3.2, AC-3.3]`
5. Calibration on ≥20 labeled stories; zero clean-fixture false positives; thresholds committed `[AC-4.1, AC-4.2, AC-4.3]`
6. Gate 3 shadow logs rows; nothing skips a spawn; `shadow-report` checks rule 8 `[AC-5.1, AC-5.3, AC-5.4]`
7. One-time setup prompt at 2.6c; config line only; no key in output `[AC-6.1, AC-6.2, AC-6.3, AC-6.4]`

**Business Rules:**
- Double opt-in (config line naming a backend + that backend's key)
- Cascade, not replacement; below-threshold answers never acted on
- Advisory only: no gate outcome depends on Jev in this spec
- Pinned model on `typesafe` (`model_mismatch` discards); gateway alias-only (`model_unpinned`)
- Setup prompt never collects a key; `--recommend`/non-interactive → note only
- Secret paths excluded from diff slices
- Promotion rule: ≥30 stories, 0 false passes, ≥95% agreement (a later spec acts on it)

**Experience Design:**
- Entry: config line + key; no new command
- Happy path: 2.6c → `spec-findings` → escalated stories only → `spec-analyze`
- Moment of truth: `jev: 4/5 stories judged, 1 escalated`
- Feedback: summary names model, input tokens, judged/escalated
- Error: named `unverifiable` note; full existing pass runs

---

## For Testing Agents

**Success Criteria:**
1. `uv run --python 3.9 pytest scripts/tests/test_jev_judge.py` green, no network
2. `bash scripts/eval.sh` Findings 0 with provider disabled
3. Calibration table in Story 4 What Was Built (or `no_live_run` stated)

**Shadow Paths to Verify:**
- **Happy path:** all confident → findings, empty escalate list
- **Nil input:** no config line → `unverifiable no_config_line` (key alone included, DEV-001); `none` → `provider_disabled`; no request
- **Empty input:** zero stories → `unverifiable no_stories`, no request
- **Upstream error:** 429 then 200 → one retry, `attempts=2`

**Edge Cases:**
- Key set, no config line → no request
- Replay env set → never live
- Review output without AC tags → `no_evaluator_ids`, Gate 3 unaffected
- `.env.local` in diff → excluded, counted

**Coverage Requirements:** New code ≥80%; error paths 100% (every §1 reason code has a test)

**Test Strategy:** pytest with a replay transport and a fake HTTP handler for status codes; bash eval-wiring test in `test_eval_spec_analyze.sh` shape
