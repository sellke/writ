# Leanness Audit — Ritual Template

> **Purpose:** A repeatable, cadence-bound maintainer ritual that re-applies the
> "does the harness do this natively now?" test (Design Principle #4) and
> surfaces prune candidates, so strategic leanness is a *scheduled discipline*
> rather than a lucky observation.
>
> **Tier B of the leanness guardian.** Tier A (`scripts/eval.sh --check=leanness`)
> catches mechanical drift on every PR; this ritual is the human judgment layer.
> See [ADR-015](../decision-records/adr-015-leanness-self-governance.md) and
> [ADR-019](../decision-records/adr-019-full-surface-leanness-measurement.md)
> (full-surface measurement, the coverage guard, and the reduction ratchet
> that replaced `GROWTH_TOLERANCE`).

## When to Run

- **Per phase close** (after a roadmap phase's specs all ship), **or**
- **Quarterly**, whichever comes first.
- **Never per-release.** Release cadence is too frequent — an audit there is
  friction, not signal. The cadence lives here as documented discipline and must
  **not** be hooked into any shipping command (`/release`, `/implement-phase`,
  `/ship`), which would leak framework-internal governance to users.

## Inputs

Gather before starting; paste the raw numbers into the dated output.

1. **Tier A metrics — full surface (ADR-019).** Run one of:
   - `python3 scripts/eval-leanness.py` — raw `{structural, warnings, metrics}`
     JSON. Paste the whole `metrics` block: `per_surface` (lines/chars per
     gated surface), `total_product_lines` / `total_product_chars`, the
     ungated `writ_workspace_lines`, and `story_context_bytes` **together
     with its `story_context_bytes_note` disclaimer** (as of Story 3,
     2026-08-03-deterministic-story-substrate, this is a MIXED
     real-measurement/declared-load-proxy disclaimer, not a pure-proxy one —
     paste the note itself rather than assuming its wording) — never paste
     the number alone. The legacy `commands` / `agents` / `skills` /
     `command_lines` / `command_chars` keys remain present; paste them too
     for continuity with pre-ADR-019 audits.
   - `bash scripts/eval.sh --check=leanness` — read the "Notes (non-blocking)"
     block for the `Metrics:` lines (now one line each for the legacy
     aggregate, `per_surface`, the product rollup + `writ_workspace_lines`,
     and `story_context_bytes`) and any ratchet/ceiling warnings.
2. **Baseline delta.** Compare current per-surface metrics against
   [`.writ/leanness-baseline.json`](../leanness-baseline.json)'s `surfaces`
   map (schema 2). Note the growth since the recorded date, **per surface**
   (lines, chars) — not as one aggregate figure. Full-surface baselines reset
   on 2026-07-26 (ADR-019); do not compare a post-reset total against a
   pre-ADR-019 command-only figure and call the difference a regression.
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

1. **Metrics snapshot** — the pasted Tier A metrics + baseline delta. Per
   ADR-019, this means `per_surface`, `total_product_lines` /
   `total_product_chars`, `writ_workspace_lines`, and `story_context_bytes`
   **with its `story_context_bytes_note` label** (mixed real-measurement/
   declared-load-proxy as of Story 3, 2026-08-03-deterministic-story-substrate
   — no longer a pure declared-load proxy) — alongside the legacy
   `command_lines` / `command_chars` keys, not `command_lines` alone.
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
