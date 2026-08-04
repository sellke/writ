# Spec: Leanness Instrumentation Rewrite

> **Status:** Completed ✅ (5/5 stories complete, 2026-07-26)
> **Owner:** @Adam Sellke
> **Created:** 2026-07-26
> **Dependencies:** []
> **Origin:** Opus 5 harness evaluation (2026-07-25) — recommendation #1 of eleven; the keystone that makes the remaining ten falsifiable
> **Amends:** [`2026-07-11-leanness-guardian`](../2026-07-11-leanness-guardian/spec.md) / [ADR-015](../../decision-records/adr-015-leanness-self-governance.md)

## Contract (Locked)

**Deliverable:** Rewrite the Tier A leanness tripwire so it measures the entire product surface, reports the runtime context cost of a story, ratchets downward instead of tolerating growth, and hard-fails when any product surface goes unmeasured.

**Must include:** The coverage guard. Wider measurement alone fixes today's blind spot; the guard is what prevents the *next* one — and the next blind spot is the actual failure mode, since this one persisted across two audit cycles while both audits reported clean.

**Hardest constraint:** The instrument lives in `scripts/`, which is the surface it will now measure. `eval-leanness.py` is 314 lines and this roughly doubles it. That is not an argument against the change — it is the correct resolution of the irony: for the first time the guardian is accountable to its own metric, and any future growth in it appears in its own output.

## Why This Exists

`scripts/eval-leanness.py` currently measures `commands`, `agents`, `skills`, `command_lines`, and `command_chars`. Of those five, only the last two carry weight; `agents` and `skills` are bare counts and `adapters/`, `system-instructions.md`, and `scripts/` are absent entirely.

Measured against the repo on 2026-07-26:

| Surface | Lines | Guardian |
|---|---:|---|
| `commands/` | 10,726 | counted and weighed |
| `agents/` | 1,768 | counted, weight invisible |
| `skills/` | 920 | counted, weight invisible |
| `adapters/` | 1,677 | invisible |
| `system-instructions.md` | 300 | invisible |
| `scripts/` | 18,260 | invisible |
| **Total product** | **33,651** | **10,726 measured (32%)** |

The guardian returns `structural: [], warnings: []` on this repo. It is not broken — it is faithfully reporting on the third of the product it was scoped to see.

The consequence is already in the record. Between the 2026-07-11 and 2026-07-18 leanness audits, `command_lines` fell 10,659 → 10,342 and was recorded as a −317 line improvement. Over that same window, complexity did not leave the project; it moved into `scripts/`, where nothing was counting. The instrument certified a reduction that had not occurred.

[ADR-015](../../decision-records/adr-015-leanness-self-governance.md) anticipated exactly this risk in its Context section — *"the real risk — total surface weight — had no ceiling and no trend line"* — then scoped "aggregate" to commands only. Its Non-Duplication Boundary carefully defers per-file length to `check_length` and skill boundary to `lint-skill.sh`. `scripts/` is not deferred to anyone. It simply falls outside the frame, and nothing in the design would ever notice.

A second, subtler defect: the tripwire warns when weight grows past a `+10%` tolerance. That design can only ever *fail to complain*. It has no mechanism to drive weight down, which is what the roadmap's stated posture — *"keep the harness light… prune what platforms do natively"* — actually requires.

## 🎯 Experience Design (CLI / CI — no user-facing UI)

### Entry Point

`bash scripts/eval.sh --check=leanness` locally; the existing eval Tier 1 gate on every PR. No new invocation surface.

### Happy Path

1. Maintainer or CI runs the check.
2. Every top-level product path resolves to a declared measurement rule.
3. No surface grew without justification.
4. Silent pass, exit 0 — with a metrics block in the report for the Tier B ritual to consume.

### Moment of Truth

The first run after merge prints full-surface numbers, and `scripts/` — 18,260 lines, the largest single surface in the product — appears in the guardian's output for the first time.

### Error Experience

| Situation | Behavior |
|---|---|
| Top-level product path with no measurement rule | **Structural finding** (hard-FAIL): names the path, offers "add a rule or declare it out of scope" |
| Measured surface grew without a baseline justification | Warning (non-blocking): names the surface and the delta |
| Baseline missing or malformed | Structural finding (existing behavior, preserved) |
| A measured path exists in the registry but not on disk | Structural finding: stale registry entry |
| `.writ/` grew | Reported only — never a finding, never a warning |

### Feedback Model

Unchanged from ADR-015: findings render through `add_finding` and fail the run; warnings and metrics render through `add_note` and never touch the findings counter. A healthy repo stays silent.

## 📋 Business Rules

1. **Product surface is an explicit registry.** `commands/`, `agents/`, `skills/`, `adapters/`, `scripts/`, `system-instructions.md`. Gated.
2. **`.writ/` is ceremony cost, not product.** Reported for trend visibility, never gated — authoring a spec must never read as bloat.
3. **Down is free; up costs a sentence.** Any increase to a measured surface requires a `justification` string in the baseline entry, or it warns.
4. **Only unmeasured surface hard-fails.** Growth stays warn-only; ADR-015's rejection of hard-failing on weight (Alternative B) still holds and is not reopened.
5. **The guardian measures itself.** `eval-leanness.py` lives under `scripts/` and is counted like everything else. No self-exemption.
6. **Dogfooding-only.** No `commands/*.md`, no user-facing surface, no change to `/status` behavior. ADR-015's mandate is unchanged.
7. **`story_context_bytes` is a declared-load proxy.** It measures what `implement-story` says it loads, not what a model consumes. It must be labeled as such wherever it is reported.

## Detailed Requirements

### Full-surface measurement

`compute_metrics` is replaced by a registry-driven walk. Each entry declares a path, a glob, and whether it is gated. The output gains `per_surface` (lines and chars keyed by surface name) and `total_product_lines` / `total_product_chars`, alongside a separate ungated `writ_workspace_lines`.

The existing `commands`, `agents`, `skills`, `command_lines`, and `command_chars` keys are retained so the Tier B format and any existing consumers do not break on the first run.

### Coverage guard

After metrics, the guard enumerates top-level entries in the repo and compares them against the union of the product registry, an explicit `out_of_scope` declaration list (`.git`, `.writ`, `archive`, `test`, `node_modules`, dotfiles, and similar), and the gated registry. Anything unaccounted for produces a structural finding.

This is the anti-recurrence mechanism and the reason the spec exists in this shape. Adding `scripts/` to the registry fixes 2026; the guard is what fixes the next directory someone adds.

### Static `story_context_bytes`

A deterministic sum of the byte size of every artifact `commands/implement-story.md` declares it loads for a full-pipeline story: `.writ/context.md`, the story file, `spec-lite.md`, fetched context sources, `knowledge_context` (capped at its documented 2KB), and the agent definition files spawned at each gate.

It is a proxy, and the spec says so plainly. It is good for catching a routing-table change that balloons the load. It is not token accounting and must never be reported as such.

### Reduction ratchet

The baseline schema gains a per-surface structure. On each run, every measured surface is compared to its recorded baseline:

- Current **≤** baseline → silent. The baseline is rewritten down automatically on `--update-baseline`.
- Current **>** baseline and a non-empty `justification` exists for that surface → silent.
- Current **>** baseline with no justification → warning naming surface, baseline, current, and delta.

The ratchet replaces `GROWTH_TOLERANCE`. A tolerance permits silent drift up to a threshold; a ratchet makes every increase a deliberate, recorded act. ADR-015 already accepted this class of friction for baseline bumps ("intentional and rare").

### ADR-019 and Tier B

A new ADR extending and partially superseding ADR-015, following the existing `Extends:` convention. It records the coverage-guard principle, the ratchet-over-tolerance reversal, and the honest reset of the trend line. `.writ/docs/leanness-audit-format.md` is updated so the Tier B ritual reads the new metric set.

## Implementation Approach

Test-first against the existing `scripts/tests/test_eval_leanness.sh`, which already exercises the script's JSON contract. The script's `main()` already returns a stable JSON envelope (`structural` / `warnings` / `metrics`) and always exits 0, letting `eval.sh` decide FAIL — that contract is preserved so `check_leanness` wiring changes minimally.

Work order follows the dependency graph: measurement and the context metric are independent and land first; the guard and the ratchet both build on the registry introduced by measurement; the ADR and Tier B doc record what actually shipped.

## Success Criteria

1. Measured coverage of product surface goes 32% → 100%, asserted by the guard itself rather than claimed in prose.
2. A new top-level product directory with no measurement rule hard-FAILs eval Tier 1.
3. `story_context_bytes` is reported and byte-identical across repeated runs on an unchanged tree.
4. An unjustified increase to any measured surface warns, naming surface and delta; a decrease is silent.
5. Full eval Tier 1 stays green (`Findings: 0`); ADR-019 is recorded; the Tier B format consumes the new metric set.

## Technical Concerns (surfaced at contract time)

- **The trend line resets.** The only history that exists (10,659 → 10,342, command-only) does not translate to full-surface. ADR-015 already rejected deriving history from git tags as Alternative C. Accepted: start the honest trend now rather than reopen a settled decision. ADR-019 records the reset explicitly so a future reader does not mistake the discontinuity for a sudden regression.
- **`story_context_bytes` is a proxy.** Declared load, not consumed tokens. Useful for detecting routing-table ballooning; not ground truth. Labeled at every reporting site.
- **Ratchet friction is real.** Every legitimate increase costs a one-line justification. Consistent with ADR-015's accepted tradeoff rather than new friction.
- **The instrument grows.** `eval-leanness.py` roughly doubles. Mitigated by the fact that it is now measured by its own metric — the first surface in the project that is fully self-accounting.

## Scope Boundaries

**Included:** full-surface measurement, coverage guard, static context metric, reduction ratchet, ADR-019, Tier B format update.

**Excluded, deliberately:**

- **Any actual deletion.** This spec builds the instrument; it does not perform the surgery. If one spec both measures and cuts, the cut becomes unfalsifiable — you cannot validate a change with the instrument that change produced. The ten remaining recommendations from the originating evaluation are downstream work.
- **User-facing surface.** No `commands/*.md`. ADR-015's dogfooding-only mandate is unchanged.
- **Auto-pruning.** The guardian recommends; it never deletes.
- **Gating `.writ/`.** Reported only.
- **Live token instrumentation.** Static proxy only.
- **Reopening ADR-015's warn-only decision for growth.** Only unmeasured surface gains teeth.
