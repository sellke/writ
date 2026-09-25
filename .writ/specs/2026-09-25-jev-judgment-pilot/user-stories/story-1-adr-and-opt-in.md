# Story 1: ADR-027 and Opt-in Resolution

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer who wants faster bounded judgments without silently sending spec text to a third party
**I want to** record the decision for an optional judgment provider in ADR-027 and resolve the double opt-in with `scripts/jev-judge.py status`
**So that** the provider stays disabled until `.writ/config.md` names a backend (`typesafe` or `vercel-gateway`) and that backend's key is set, and a key already in my shell for other work never counts as consent to send spec text

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [ ] Given the pilot's design, when `.writ/decision-records/adr-027-optional-judgment-provider.md` is written, then it has context, decision, alternatives (no provider; SDK dependency; call inside `spec-analyze.py`; replace the evaluator now), and consequences sections, and it explicitly reconciles ADR-024 Decision 3 (Jev replaces a verdict source, not an agent tier), Phase 11's no-API-key-in-verifier-scripts rule (a separate caller hands JSON to existing scripts), and ADR-025 (shadow rows are not friction signals); it names both backends (TypeSafe direct; Vercel AI Gateway's TypeSafe-compatible endpoint), the gateway's alias-only model ID (`typesafe-ai/jev`, versioned IDs 404, version drift undetectable), and the `only: ["typesafe-ai"]` routing restriction `[AC-1.1]`
- [ ] Given ADR-027, when its consequences are read, then it states the privacy exposure (spec text, test output, and diff slices are sent) and the promotion rule: ≥30 evaluated stories, zero false passes, and ≥95% per-criterion agreement before any later spec conditions the evaluator spawn `[AC-1.2]`
- [ ] Given `python3 scripts/jev-judge.py status [--repo .]`, when the `.writ/config.md` line `- **Judgment Provider:** <backend>` names `typesafe` with a non-empty `TYPESAFE_API_KEY`, or `vercel-gateway` with a non-empty `AI_GATEWAY_API_KEY` or `VERCEL_OIDC_TOKEN`, then it prints `pass`, `reason: enabled`, and `backend=<name>` in the summary; otherwise it prints `unverifiable` with `reason: provider_disabled` (`none` or unknown value), `no_config_line`, or `no_api_key` (summary names the env var to export); it exits 0 in both cases and 2 on bad argv, emitting one verdict line, `reason:` lines, and the summary line last `[AC-1.3]`
- [ ] Given `TYPESAFE_API_KEY` or `AI_GATEWAY_API_KEY` is set and `.writ/config.md` has no Judgment Provider line, when `status` runs, then the provider is disabled, no request is built, and the key value appears in no stdout, stderr, or written file `[AC-1.4]`
- [ ] Given `scripts/tests/test_jev_judge.py`, when `uv run --python 3.9 pytest scripts/tests/test_jev_judge.py` runs, then it covers every status case with no network access, and the story's closing commit appends a `{date} jev-pilot: ...` line to `.writ/decision-log.md` `[AC-1.5]`

## Implementation Tasks

- [ ] 1.1 Write `scripts/tests/test_jev_judge.py` (pytest, Python 3.9, no network; temp repo via `tmp_path`, env via `monkeypatch`) covering: each backend with its key → `pass` / `reason: enabled` / `backend=`; `.writ/config.md` missing or no line → `no_config_line`; line `none` or unknown → `provider_disabled`; `vercel-gateway` with only `VERCEL_OIDC_TOKEN` → `pass`; both keys set → the config line decides; line present, key empty or whitespace → `no_api_key`; key set with no line → `provider_disabled` and no request built; bad argv → exit 2; key string absent from captured stdout, stderr, and every file under the temp repo `[AC-1.3, AC-1.4, AC-1.5]`
- [ ] 1.2 Write `.writ/decision-records/adr-027-optional-judgment-provider.md`: context, decision, the four alternatives, consequences, and one reconciliation paragraph each for ADR-024 Decision 3, Phase 11's no-API-key-in-verifier-scripts rule, and ADR-025 `[AC-1.1]`
- [ ] 1.3 Add ADR-027's consequences: the privacy exposure (spec text, test output, diff slices) and Business Rule 8's promotion rule (≥30 evaluated stories, zero false passes, ≥95% per-criterion agreement), stated as recorded here and enforced by no code in this spec `[AC-1.2]`
- [ ] 1.4 Implement `scripts/jev-judge.py` with argparse subcommands and a `status [--repo .]` subcommand (`--project` alias), stdlib only: match the config line with `^- \*\*Judgment Provider:\*\*\s*(\S+)` compared case-insensitively to `typesafe` / `vercel-gateway` / `none`, read the backend's key per technical-spec §2's backend table (`TYPESAFE_API_KEY`; or `AI_GATEWAY_API_KEY` then `VERCEL_OIDC_TOKEN`), and never print, log, or write the key or build a request `[AC-1.3, AC-1.4]`
- [ ] 1.5 Emit the technical-spec §1 output shape from `status`: one verdict line, `reason:` lines, summary last (`backend=<name> model=<backend model>`); exit 0 for `pass` / `unverifiable`, exit 2 for usage errors `[AC-1.3]`
- [ ] 1.6 Verify: `uv run --python 3.9 pytest scripts/tests/test_jev_judge.py` green with no network; ADR-027 reviewed against AC-1.1 and AC-1.2; append `{date} jev-pilot: ADR-027 and jev-judge.py status resolve the double opt-in` to `.writ/decision-log.md` in the closing commit `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

## Notes

- **Technical considerations.** Model `jev-judge.py` on the Stage 2b helper family (`scripts/spec-analyze.py`, `scripts/drift-format.py`). Python 3.9 floor, stdlib only. Reason precedence follows technical-spec §1: missing `.writ/config.md` → `no_config_line`; line absent or not `typesafe` → `provider_disabled`; line present, key empty → `no_api_key`.
- **Risks.** Key leakage is the main risk. No error message, traceback, `repr`, or debug line may include the key. The no-network guarantee should be enforced in tests, e.g. by patching `urllib.request.urlopen` to raise.
- **Integration.** Story 2 builds the transport on this opt-in resolver. Story 3 wires Step 2.6c. Do not edit `commands/create-spec.md` or `commands/verify-spec.md` here.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Resolve opt-in] — from technical-spec.md §5
- **Shadow paths:** [Nil (Provider disabled → `unverifiable provider_disabled`; commands unchanged)] — from technical-spec.md §6
- **Business rules:** [Rule 1 (Double opt-in: config line naming a backend and that backend's key; a key alone never sends data), Rule 11 (Gateway routing restricted), Rule 2 (Verdict contract: `pass`/`unverifiable` exit 0, `fail` exit 1, usage error exit 2), Rule 9 (Stdlib only: Python 3.9, `urllib.request`, `json`, no SDK)] — from spec.md → Business Rules
- **Experience:** []
