# Leanness Audit — Ritual Template

> **Purpose:** A repeatable, cadence-bound maintainer ritual that re-applies the
> "does the harness do this natively now?" test (Design Principle #4) and
> surfaces prune candidates, so strategic leanness is a *scheduled discipline*
> rather than a lucky observation.
>
> **Tier B of the leanness guardian.** Tier A (`scripts/eval.sh --check=leanness`)
> catches mechanical drift on every PR; this ritual is the human judgment layer.
> See [ADR-015](../decision-records/adr-015-leanness-self-governance.md).

## When to Run

- **Per phase close** (after a roadmap phase's specs all ship), **or**
- **Quarterly**, whichever comes first.
- **Never per-release.** Release cadence is too frequent — an audit there is
  friction, not signal. The cadence lives here as documented discipline and must
  **not** be hooked into any shipping command (`/release`, `/implement-phase`,
  `/ship`), which would leak framework-internal governance to users.

## Inputs

Gather before starting; paste the raw numbers into the dated output.

1. **Tier A metrics.** Run one of:
   - `python3 scripts/eval-leanness.py` — raw `{structural, warnings, metrics}` JSON, or
   - `bash scripts/eval.sh --check=leanness` — read the "Notes (non-blocking)"
     block for the `Metrics:` summary line and any growth/ceiling warnings.
2. **Baseline delta.** Compare current metrics against
   [`.writ/leanness-baseline.json`](../leanness-baseline.json). Note the growth
   since the recorded date (lines, chars, counts).
3. **Registries.** `.writ/manifest.yaml` (commands, agents, skills) and the four
   adapters (`adapters/cursor.md`, `claude-code.md`, `codex.md`, `openclaw.md`).
4. **Recent harness/platform changes** since the last audit (new native
   capabilities in Cursor/Claude Code/Codex that might displace Writ surface).

## Judgment Checklist

Work each command, agent, and skill through these questions. This is judgment,
not a mechanical pass — Tier A already owns the mechanical checks.

### (a) Native displacement (Principle #4)
> *Does the harness do this natively now?*
For each command/agent, ask whether a platform capability that did not exist (or
was immature) when it was written now covers its job. This is the test that
retired Ralph and `/audit`. Name the specific native feature and the surface it
would displace.

### (b) Command overlap
> *Do two commands do substantially the same thing?*
Look for pairs whose purpose statements or workflows have converged. Overlap is a
merge candidate, not necessarily a delete.

### (c) Existence justification
> *Should this still exist?*
For each surface: when was it last invoked or referenced? Does it earn its weight?
A command nobody runs is dead surface even if it is technically correct.

### (d) Prune candidates
Consolidate (a)–(c) into a candidate list. Every candidate is a *recommendation*
for human decision — this ritual **recommends, never deletes**.

## Output Contract

Produce a dated file: **`.writ/docs/leanness-audit-YYYY-MM-DD.md`** (the date is
the audit date). It MUST contain:

1. **Metrics snapshot** — the pasted Tier A metrics + baseline delta.
2. **Findings → Decisions table** — one row per candidate:

   | Surface | Finding | Decision | Follow-up |
   |---|---|---|---|
   | `commands/foo.md` | Cursor now does X natively (a) | **prune** \| **merge** \| **keep** \| **defer** | ADR-0NN / roadmap entry / issue #NN |

   - **Decision** is exactly one of: `keep`, `prune`, `merge`, `defer`.
   - **Follow-up** routes every non-`keep` decision to a durable artifact — an
     ADR (for a stance), a roadmap entry (for planned work), or an issue (for a
     tracked task). A decision with no follow-up is not done.
3. **Recommend-only guarantee** — the audit deletes no surface itself. Pruning
   happens later, by a human, via the routed follow-up.

## Precedent

- [`.writ/docs/swot-2026-03-01.md`](swot-2026-03-01.md) — the format precedent for
  a dated strategic review.
- The 2026 harness audit that produced ADR-010–013 is the **ad-hoc** version of
  this ritual; this template makes it routine.
