# Technical Specification: Evidence-Bound /refresh-command

> **Parent:** `../spec.md`
> **Status:** Not Started
> **Stories:** 1–3

## Architecture Summary

`/refresh-command` stays a human-driven, platform-neutral command. This spec makes its learning loop falsifiable by inserting an evidence contract and a pre-merge eval gate into the command's existing phases, and by adding one fixture-driven eval check wired into the same registry and CI path as the existing 19 checks.

```text
run a Writ command
        │
        ▼
/refresh-command [command]
        │
   gather signals (description | infer from session)
        │
        ▼
 propose amendment(s)  ── each MUST carry Evidence:
        │                  transcript ID/path + observable signal + affected section
        ▼
 pre-merge eval gate: eval.sh --check=refresh-evidence
        │              (+ structural Tier 2 for high-traffic targets)
   ┌────┴─────┐
 pass         fail / no evidence
   │              │
 apply         reject + record reason
   │              │
   └────┬─────────┘
        ▼
 append one .writ/refresh-log.md entry (applied w/ evidence + rejected w/ reason)
        │
        ▼
 CI backstop: .github/workflows/eval.yml runs eval.sh (registry auto-run, no wiring change)
```

## Design Decisions

### D1 — Evidence Is Mandatory and Structured

Every Phase 3 proposal carries five fields: **Title**, **Rationale**, **Confidence** (H/M/L), **Evidence**, **Diff**. The Evidence block has three required parts:

```markdown
**Evidence:**
- Transcript: agent-transcripts/<session-uuid>/<session-uuid>.jsonl   # or .../subagents/<sub-uuid>.jsonl
- Observable signal: "user re-ran /create-spec after the scan skipped the monorepo root"
- Affected section: commands/create-spec.md → "Phase 2: Codebase Scan"
```

The observable signal is a short factual quote of an event (correction, retry, override, error). It is not reasoning, a prompt, or a private body.

### D2 — Rejection Is a First-Class, Logged Outcome

A proposal with no transcript evidence, or one that fails the eval gate, is rejected before Apply and never written to the command file. The `.writ/refresh-log.md` entry records it under `**Rejected:**` with a reason token: `no evidence` or `eval failed`. Rejection is a normal result — it directly supplies the roadmap's required "rejected for lacking evidence" example.

### D3 — Privacy Guard (Prime Directive)

Evidence citations reference transcript IDs/paths and short observable signals only. Stored artifacts must never contain chain-of-thought, prompts, or verbatim private transcript bodies. The eval validator includes a privacy guard: an entry whose Evidence or signal exceeds a short observable quote, or that embeds a fenced transcript body / reasoning block, fails. Transcripts live outside the repo (Cursor platform-local `.jsonl`); their bodies are never committed.

### D4 — Drift Reconciliation Direction

The command lost transcript-evidence citation while docs kept describing it. Resolution:

- **Restore** lightweight evidence citation into `commands/refresh-command.md` (roadmap requires "cited transcript evidence").
- **Redefine docs to reality** for genuinely unimplemented mechanics: remove `--batch`/`--last`/promotion-flow claims and the nonexistent "Phase 2.2" reference rather than implement them.
- **One canonical path:** `.writ/refresh-log.md` everywhere; delete the `.writ/state/refresh-log.md` variant in `status.md`.
- **Accurate README phrasing:** "scans agent transcripts" → cited-evidence, human-driven phrasing.

### D5 — Fixture-Driven Eval Check

`scripts/eval-refresh-evidence.py` follows `scripts/eval-phase-knowledge.py`: build synthetic refresh-log entries in `tempfile.TemporaryDirectory()`, run them through the validator, and `emit()` `PASS\t<name>` / `FAIL\t<name>\t<reason>` lines. `check_refresh_evidence()` in `scripts/eval.sh` counts scenarios into `CURRENT_SCENARIOS[_PASSED]`, calls `add_finding` on FAIL, and adds `require_literal` static assertions. The check is deterministic and never reads the live log for pass/fail.

### D6 — Grandfathering via `LEARNING_CONTRACT_SINCE`

Any live-log lint grandfathers entries dated strictly before `LEARNING_CONTRACT_SINCE = 2026-07-11` (the day after this spec's Created date). The two existing entries (`2026-03-15`, `2026-07-10`) are grandfathered, so CI never fails on pre-contract history. The constant is documented in `.writ/docs/refresh-log-format.md`.

### D7 — Two Enforcement Points, No New CI Wiring

Enforcement is layered: (1) the in-command Apply-time gate gives fast feedback and blocks unevidenced/failing edits before they are written; (2) CI (`.github/workflows/eval.yml`) is the backstop. Because the new check is registered in the `CHECKS` array and dispatched via `check_${check//-/_}`, the existing `bash scripts/eval.sh` CI step runs it automatically — `eval.yml` needs no change. This is verified and explicitly noted.

### D8 — Tier 2 Is Structural, Bounded, and Not an LLM Judge

Research deferred the LLM-as-judge Tier 2 on cost grounds (~$0.15/30s; "cost grossly exceeds value for current scale"). This spec defines Tier 2 as a lightweight structural reuse of existing Tier 1 primitives (required-sections, broken-refs, length, preamble reference, diff-anchor), run only for the high-traffic allowlist (`create-spec`, `implement-story`, `ship`, `refactor`). The LLM-judge variant stays out of scope behind an explicit future decision. Tier 2 adds fixture scenarios and static assertions to the same `refresh-evidence` check — it is not a separate registry entry.

## File × Story Matrix

| File | S1 | S2 | S3 |
|---|---:|---:|---:|
| `commands/refresh-command.md` | ✓ |  | ✓ |
| `.writ/docs/refresh-log-format.md` | ✓ |  |  |
| `commands/status.md` | ✓ |  |  |
| `README.md` | ✓ |  |  |
| `scripts/eval-refresh-evidence.py` (new) |  | ✓ | ✓ |
| `scripts/eval.sh` |  | ✓ | ✓ |
| `.github/workflows/eval.yml` (verify no-change) |  | ✓ |  |
| `.writ/refresh-log.md` (acceptance entries) |  |  | ✓ |

## Error & Rescue Map

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| Parse refresh-log entry | Malformed/missing fields | Report the missing field and treat the amendment as unevidenced; never guess | Fixture entries: complete, missing-signal, malformed block |
| Missing transcript citation | Proposal has no transcript ID/path | Reject before Apply; record `no evidence`; do not write the diff | Fixture: evidenced (pass) vs. citation-absent (fail) |
| Eval check crash | Fixture/validator raises or exits non-zero | `run_check` records a run error (exit 2 semantics); amendment is not written | Deliberately broken fixture in a sandbox copy |
| Tier 2 scope miss | Wrong command treated as (non-)high-traffic | Allowlist is explicit; assert allowlisted → deeper check, non-allowlisted → base check only | Fixtures for one allowlisted + one non-allowlisted target |
| Transcript file absent | Cited `.jsonl` not present on this machine | Accept the ID citation; never fabricate a body; note unavailability; grandfather legacy | Fixture citing an absent path (pass on ID) |
| Private-content guard | Entry embeds CoT / verbatim private body | Fail the entry; instruct to keep ID + short observable signal only | Fixture embedding a fenced transcript body (fail) |
| Grandfathered legacy entry | Pre-contract entry lacks new evidence block | Grandfather when dated `< LEARNING_CONTRACT_SINCE`; do not retroactively fail | Fixture dated 2026-03-15 (pass) |

No `[UNPLANNED]` operations remain. Transcript bodies are never committed; the check tolerates their absence.

## Shadow Paths

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| Evidence citation | Proposal carries ID + signal + section → applied | No target command → list and ask | Reviewed, zero amendments → valid no-op, exempt | Missing citation → reject with `no evidence` |
| Eval gate | Clean gate → apply and log | No amendment proposed → gate not run | Only no-op review → gate skipped, review logged | Gate fails → reject with `eval failed` |
| Refresh-evidence check | All fixtures pass → check clean | No fixtures matched → scenario count zero, static assertions still run | Empty candidate set → PASS no-op scenario | Validator raises → run error surfaced |
| Tier 2 (high-traffic) | Allowlisted target → structural check passes → apply | Non-allowlisted target → base check only | No structural regression introduced → pass | Structural regression in refreshed file → reject |
| Drift reconciliation | Docs match command reality | No stale reference found → grep clean | N/A | Stale "Phase 2.2"/path/README claim remains → grep fails |
| Log audit trail | Applied entries carry evidence; rejected carry reason | No prior log → create with header | Legacy entries present → grandfathered | Private content in an entry → privacy guard fails |

## Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| Maintainer insists on applying an unevidenced edit | Contract-degrading; requires an explicit human choice, not a silent default; still logged |
| Same-session inference with no clear transcript ID | Attribute to the current session transcript ID/path; if none is resolvable, reject as unevidenced |
| High-traffic command with a purely cosmetic diff | Tier 2 structural check still runs; passes if structure is intact |
| Transcript on a different machine | ID citation accepted; body never required; entry stands as auditable by ID |
| Legacy entry edited after the contract lands | Once edited into the new schema it is validated; otherwise grandfathered by date |
| Second Phase 7 spec also appends to `eval.sh` | Both edits are append-only and must not reorder the registry; sequential phase execution keeps them safe |

## Verification Commands

```bash
python3 scripts/eval-refresh-evidence.py
bash scripts/eval.sh --check=refresh-evidence
bash scripts/eval.sh
bash scripts/gen-skill.sh --check
```

Also run targeted greps proving drift is reconciled: no `Phase 2.2` reference in `commands/status.md`; a single canonical `.writ/refresh-log.md` path (no `.writ/state/refresh-log.md`); accurate transcript phrasing in `README.md`; a mandatory `**Evidence:**` block in `commands/refresh-command.md` Phase 3.
