# Leanness Audit — 2026-07-11

> First dated audit produced from
> [`leanness-audit-format.md`](leanness-audit-format.md). Doubles as the
> dogfood proof for the leanness guardian (`2026-07-11-leanness-guardian`,
> Story 2). Recommend-only: this audit deletes no surface.
>
> **Auditor:** @adam · **Trigger:** phase-close (Phase 8, memory-interop) + guardian ship

## Metrics Snapshot

Source: `python3 scripts/eval-leanness.py` (2026-07-11).

| Metric | Value | Ceiling | Headroom |
|---|---|---|---|
| commands | 31 (30 non-infra + `_preamble`) | 35 | 4 |
| agents | 7 | 10 | 3 |
| skills | 6 | 12 | 6 |
| command_lines | 10,659 | — | — |
| command_chars | 484,616 | — | — |

- **Structural findings:** 0 (registry parity clean — README ↔ files bidirectional; `/status` allowlist → files phantom-free).
- **Warnings:** 0 (all counts under ceilings; aggregate weight at baseline).
- **Baseline delta:** 0% — `.writ/leanness-baseline.json` was recorded today
  (2026-07-11), so this audit establishes the reference point. The *next* audit
  measures drift against it.

## Judgment Checklist Results

Applied to all 30 non-infra commands, 7 agents, 6 skills. Most surface is
intentional and recently pruned (the maintainer retired `/audit`, `/lessons`,
Ralph, and `/explain-code` before this audit), so the honest result is mostly
**keep**. Genuine review candidates below.

### (a) Native displacement — "does the harness do this natively now?"
The live risk area, since harnesses evolve fastest.
- `/research` — agentic web search + fetch are increasingly first-class in
  Cursor/Claude Code. The command still adds a *structured 4-phase workflow and
  durable `.writ/research/` artifacts* that raw native search does not, but the
  gap is narrowing. **Watch item.**
- `/design` — Cursor now has native browser + image tools. The command still
  orchestrates mockup management, screenshot capture, and visual comparison as a
  workflow, which native tools do not sequence. Gap remains real today.

### (b) Command overlap
- Lifecycle trio `/update-writ` · `/reinstall-writ` · `/uninstall-writ` — adjacent
  but semantically distinct verbs (update in place / clean reinstall / remove).
  No functional overlap; keeping three is clearer than one flagged command.
- Capture set `/create-adr` · `/create-issue` · `/knowledge` — all "capture," but
  each writes a different durable artifact (ADR / issue / knowledge ledger) with
  different ceremony. No merge warranted.

### (c) Existence justification
- All commands appear in the README catalog and are wired in `.writ/manifest.yaml`
  (Tier A confirms parity). No dead command surface detected.
- `_preamble.md` remains the sole infra exception — the exclusion list has not
  grown, which is itself a healthy leanness signal.

### (d) Prune candidates
Consolidated below. No `prune` this cycle; two `defer` watch items.

## Findings → Decisions

| Surface | Finding | Decision | Follow-up |
|---|---|---|---|
| `commands/research.md` | (a) Native agentic search narrowing the gap; structured workflow + artifacts still add value | **defer** | Re-evaluate at next audit; if native search gains durable-artifact support, open an ADR to retire or thin `/research`. Tracked as a watch item here. |
| `commands/design.md` | (a) Native browser/image tools exist; command still sequences mockup/compare workflow | **keep** | Re-check native visual-diff maturity next audit. |
| `/update-writ`, `/reinstall-writ`, `/uninstall-writ` | (b) Adjacent lifecycle verbs, no functional overlap | **keep** | None. |
| `/create-adr`, `/create-issue`, `/knowledge` | (b) Shared "capture" theme, distinct artifacts | **keep** | None. |
| Whole command surface | (c) 30 non-infra commands, 0 dead/orphaned, parity clean | **keep** | None. |
| Aggregate weight | 10,659 lines at freshly-set baseline; 0% drift | **keep** | Next audit compares against this baseline; warn fires at +10%. |

## Recommend-Only Guarantee

This audit **deletes nothing**. The single actionable item — the `/research`
native-displacement watch — is a `defer` with a re-evaluation trigger, not a
prune. Any future removal will go through a human decision and a routed
follow-up (ADR / roadmap / issue), per [ADR-015](../decision-records/adr-015-leanness-self-governance.md).

## Next Audit

**Trigger:** next phase close or 2026-10-11 (quarterly), whichever first.
**Focus carried forward:** `/research` vs. native search maturity; first real
aggregate-weight delta against the 2026-07-11 baseline.
