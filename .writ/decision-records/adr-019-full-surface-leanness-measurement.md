# ADR-019: Full-Surface Leanness Measurement, the Coverage Guard, and the Reduction Ratchet

> **Date:** 2026-07-26
> **Status:** Accepted
> **Category:** Framework Architecture
> **Extends:** [ADR-015](adr-015-leanness-self-governance.md) (partial supersession — see Relationship to ADR-015 below)
> **Origin:** Opus 5 harness evaluation (2026-07-25) — recommendation #1 of eleven, per the owning spec's header (see References)

## Decision

Tier A (`scripts/eval.sh --check=leanness`) now measures the framework's
**entire declared product surface** — `commands/`, `agents/`, `skills/`,
`adapters/`, `scripts/`, and `system-instructions.md` — via a registry-driven
walk, instead of the command-only slice ADR-015 originally scoped. Three
decisions ship together:

1. **The coverage guard.** Every top-level repository entry must resolve to
   the gated registry, the ungated `.writ/` workspace, or an explicit
   `OUT_OF_SCOPE` declaration (or a leading-dot name). Anything left over is a
   **hard-FAIL structural finding** — the first new structural check ADR-015's
   Tier A has gained since its own introduction of registry parity.
2. **The reduction ratchet replaces `GROWTH_TOLERANCE`.** Each gated surface
   now ratchets against its own recorded baseline instead of one aggregate
   `+10%` tolerance: a decrease is silent and auto-recorded on
   `--update-baseline`; an increase is silent only with a non-empty
   `justification` string; an unjustified increase warns, naming the surface,
   baseline, current value, and delta. `GROWTH_TOLERANCE` is deleted, not
   deprecated.
3. **The trend line resets, on the record.** The only prior history
   (`command_lines` 10,659 → 10,342, recorded as an improvement while
   complexity moved into unmeasured `scripts/`) does not translate to a
   full-surface baseline. Full-surface baselines start fresh as of this ADR;
   comparing pre-2026-07-26 command-only audits to post-merge full-surface
   totals is a category error, not a regression.

`story_context_bytes` — a static, declared-load proxy for the bytes
`implement-story.md` Step 2 says it loads for a full-pipeline story — ships
alongside these three as a fourth metric, reported (never gated, never
ratcheted) so a routing-table change that balloons per-story load shows up as
a number.

## Context

ADR-015 measured `commands/`, `agents/`, and `skills/` and stated its
Non-Duplication Boundary carefully: per-file length is `check_length`'s job,
skill boundary is `lint-skill.sh`'s job. What it did not do — and did not say
it was deferring to anyone — was declare who owns `adapters/`,
`system-instructions.md`, or `scripts/`. `scripts/` in particular sat outside
every registry: not in the leanness guardian's `compute_metrics`, not named
in the Non-Duplication Boundary table, not covered by any other Tier A check.

Measured on 2026-07-26, before this spec landed:

| Surface | Lines | Guardian |
|---|---:|---|
| `commands/` | 10,726 | counted and weighed |
| `agents/` | 1,768 | counted, weight invisible |
| `skills/` | 920 | counted, weight invisible |
| `adapters/` | 1,677 | invisible |
| `system-instructions.md` | 300 | invisible |
| `scripts/` | 18,260 | invisible |
| **Total product** | **33,651** | **10,726 measured (32%)** |

The guardian returned `structural: [], warnings: []` against this repo. It
was not broken — it was faithfully reporting on the third of the product it
was scoped to see. The consequence is already in the record: between the
2026-07-11 and 2026-07-18 leanness audits, `command_lines` fell 10,659 →
10,342 and was logged as a −317 line improvement. Over that same window,
complexity did not leave the project; it moved into `scripts/`, where nothing
was counting. **The instrument certified a reduction that had not occurred,
and both audits reported clean.**

### The Non-Duplication Boundary gap

ADR-015's boundary table explicitly named three deferrals:

| Existing mechanism | Owns | Leanness guardian does NOT |
|---|---|---|
| `check_manifest` | `commands/`·`agents/` ↔ manifest parity | redo manifest parity |
| `check_length` | per-file line ceilings | check per-file length (aggregate only) |
| `lint-skill.sh` / `skill-lifecycle` | skill boundary + lifecycle | re-lint skills (counts only) |

Every deferral in that table names a receiving mechanism. `scripts/` was
deferred to **nobody** — it simply fell outside the frame the boundary table
drew, and nothing in ADR-015's design would ever notice a new top-level
directory arriving with no owner. That is the specific, nameable gap this ADR
closes: not "the guardian missed a surface" (a one-time fix), but "the
guardian had no mechanism to notice *any* surface it was missing" (the
recurring failure mode). Widening the registry to include `scripts/` fixes
2026. The coverage guard is what fixes the next directory someone adds.

## Decision 1: The Coverage Guard

`check_coverage()` enumerates top-level repository entries and subtracts the
union of the gated `SURFACE_REGISTRY` paths, the ungated `.writ/` workspace,
and an explicit `OUT_OF_SCOPE` list (`archive`, `bin`, `claude-code`, `codex`,
`cursor`, `node_modules`, `test`, and named root files). Any leading-dot
top-level name (`.git`, `.github`, `.claude`, `.codex`, `.cursor`,
`.writ-lanes-*`, `.gitignore`, `.DS_Store`, …) is out of scope unconditionally
— matched by prefix, not enumerated by name, so worktree lanes and platform
install directories can never individually require a registry edit. Anything
left over is a structural finding naming the path and offering both
remedies: add a measurement rule, or declare it out of scope. A registry path
that no longer exists on disk produces a distinguishable stale-registry
finding.

This is the anti-recurrence mechanism, and the reason this spec ships the
guard alongside wider measurement rather than shipping wider measurement
alone. Widening the registry only re-plays the same failure mode with a
longer list — a future maintainer who adds a seventh top-level directory
inherits exactly the blind spot `scripts/` proves is not hypothetical. The
guard makes silently falling outside the frame structurally impossible: the
walk covers 100% of the repository root by construction, not by the
registry's completeness at any given moment.

Enumerating `OUT_OF_SCOPE` explicitly, rather than exempting "any loose
top-level file," was a deliberate rejection of the cheaper alternative: a
blanket exemption for non-directory root entries would have reintroduced
exactly this blind spot for the next root-level product markdown file. The
one-line cost of naming a new out-of-scope path is the price of keeping the
guard honest, and `OUT_OF_SCOPE`'s own growth is itself a leanness signal
worth noticing — mirroring `INFRA_PREFIXES`' existing discipline.

**Only unmeasured surface gains structural teeth.** ADR-015's Alternative B
(hard-FAIL on weight growth) is not reopened by this decision — see
Relationship to ADR-015 below.

## Decision 2: The Ratchet Reversal

`GROWTH_TOLERANCE = 0.10` could only ever *fail to complain*: it permitted
silent drift up to a threshold and had no mechanism to drive weight down.
That design cannot deliver on the roadmap's stated posture — "keep the
harness light… prune what platforms do natively" — because tolerating growth
up to 10% is not the same instrument as one that rewards shrinking.

The reduction ratchet inverts the posture per surface rather than in
aggregate:

- **Current ≤ baseline → silent.** `--update-baseline` rewrites the baseline
  down automatically; a shrink is free and requires no ceremony.
- **Current > baseline, with a non-empty `justification` → silent.** Growth
  is a signal for judgment, not a bug (ADR-015's own framing) — a documented,
  deliberate increase does not nag.
- **Current > baseline, no `justification` → warning**, naming the surface,
  baseline value, current value, and delta.

Comparing per-surface rather than in aggregate closes a specific evasion the
old design permitted: a large decrease in one surface could mask a smaller
but real increase in another, and the +10% *aggregate* tolerance would stay
silent throughout. Per-surface comparison means `scripts/` growing while
`commands/` shrinks is visible on `scripts/` alone, not laundered through the
sum.

`--update-baseline` reseeding is a clean-slate operation: every gated
surface's baseline becomes exactly the current measurement, and
`justification` resets to `""` on every reseed. A justification describes a
specific past delta; once that delta is absorbed into a new baseline, the
delta no longer exists, and a future increase past the fresh baseline earns
its own fresh justification. This is a deliberate, documented write contract
— not an oversight — chosen to keep the baseline file from accumulating
stale rationale text that no longer describes anything measurable.

## Decision 3: The Trend Line Resets

The only weight history that exists — `command_lines` 10,659 → 10,342,
command-only — does not translate to a full-surface trend. Full-surface
baselines start fresh as of this ADR's merge. This is stated plainly, not
buried: comparing a pre-2026-07-26 command-only audit number to a
post-full-surface total in a future Tier B ritual would read as either a
false regression (the total is much larger because it now counts real
surface, not because anything grew) or, worse, invite exactly the same
laundering this ADR closes. ADR-015's Alternative C (deriving history from
git tags) was rejected for v1 and **stays rejected** — see below.

## Relationship to ADR-015

ADR-015 remains the historical record of v1 leanness governance and is
**not edited in place**. This ADR is a **partial supersession**, scoped to
exactly three things:

| Aspect | ADR-015 (v1) | ADR-019 (this decision) |
|---|---|---|
| Aggregate measurement scope | `commands/`, `agents/`, `skills/` only | Full product surface (adds `adapters/`, `scripts/`, `system-instructions.md`) |
| Growth mechanic | `GROWTH_TOLERANCE = 0.10`, aggregate, warn-only | Per-surface reduction ratchet, warn-only |
| Baseline trend semantics | Continuous from 2026-07-11 | Honest reset — full-surface history begins here |

Everything else ADR-015 decided remains in force, **unchanged, via ADR-015
itself**: the Tier A / Tier B split, warn-only growth as a category
(Alternative B stays rejected — only *unmeasured* surface gains structural
teeth; weight growth itself is still never a hard-FAIL), the dogfooding-only
mandate (no `commands/*.md`, no `/status` behavior change), the `add_note`
warn-only primitive, and directional registry parity (`check_parity`,
untouched by this spec).

## Considered Alternatives

**A. Widen the registry to include `scripts/` without adding a coverage
guard.** Rejected. This is the "fix 2026, not the recurrence" trap the
Context section names directly: it repeats the exact shape of failure that
let `scripts/` go unmeasured for two audit cycles, only with one more surface
in the list. The guard is what makes the *next* undeclared directory
structurally impossible instead of merely less likely.

**B. Hard-FAIL on per-surface weight growth (reopening ADR-015 Alternative
B).** Rejected, again. A legitimate large feature would nag or block Tier 1
on every PR. The ratchet's per-surface warning plus a one-line justification
delivers the same "growth is a deliberate act" discipline without turning
Tier 1 into a blocker for honest work. ADR-015's original reasoning for
rejecting this holds without modification.

**C. Derive the full-surface weight trend retroactively from git tag
history.** Rejected, again, for the same reason ADR-015 rejected it for v1:
it needs tag access in CI and is less deterministic than a committed
baseline. A committed, per-surface baseline is explicit, reviewable, and
bumped deliberately — the delta remains the signal, now at finer grain.

**D. Treat `story_context_bytes` as gated/ratcheted like the product
surfaces.** Rejected. It is a declared-load *proxy*, not a measured product
surface — gating a proxy would imply a precision the metric does not have.
It is reported for trend visibility (Tier B) and never fails or warns a run
on its own.

**E. Blanket-exempt loose top-level files from the coverage guard.**
Rejected. See Decision 1 above — this is the specific evasion that would let
a future root-level product markdown file repeat the `scripts/` failure
mode. The one-line `OUT_OF_SCOPE` cost per new root file is the guard's
actual mechanism, not friction to be optimized away.

## Consequences

**Positive:**

- Product coverage goes from 32% (command-only) to 100% (full surface),
  asserted by the coverage guard itself rather than claimed in prose.
- The next undeclared top-level directory hard-FAILs Tier 1 immediately,
  instead of silently persisting across audit cycles the way `scripts/` did.
- Per-surface ratcheting closes the aggregate-laundering evasion the old
  tolerance permitted, and rewards shrinking automatically via
  `--update-baseline`.
- `story_context_bytes` gives Tier B a routing-table-ballooning tripwire that
  did not exist before, clearly labeled as a proxy so it cannot be mistaken
  for token accounting.
- The guardian measures itself: `scripts/` — the surface that hid the
  original blind spot — now includes `eval-leanness.py`'s own weight, with
  no self-exemption.

**Negative:**

- The instrument that enforces leanness grew to enforce it —
  `eval-leanness.py` roughly doubled in this spec. Mitigated by the fact that
  this is now the first surface in the project that is fully self-accounting:
  the growth appears in the guardian's own `scripts` surface figure and, per
  the ratchet, needed (and received) a fresh baseline on merge.
- Every legitimate future increase to a gated surface costs a one-line
  justification. This is real, intentional friction — ADR-015 already
  accepted this tradeoff class for baseline bumps, and the ratchet applies it
  per-surface rather than in aggregate.
- The full-surface trend line has no history before 2026-07-26. A future
  reader comparing an old command-only audit number to a new full-surface
  total without reading this ADR could mistake the discontinuity for a
  regression. Mitigated by stating the reset explicitly here and in the
  updated Tier B template.

## References

- Owning spec — [`2026-07-26-leanness-instrumentation`](../specs/2026-07-26-leanness-instrumentation/spec.md)
- Tripwire — [`scripts/eval-leanness.py`](../../scripts/eval-leanness.py) (`SURFACE_REGISTRY`, `OUT_OF_SCOPE`, `check_coverage`, `check_baseline`), wired via `scripts/eval.sh` `check_leanness`
- Baseline — [`.writ/leanness-baseline.json`](../leanness-baseline.json) (schema 2, full-surface reset recorded 2026-07-26)
- Tier B ritual template — [`.writ/docs/leanness-audit-format.md`](../docs/leanness-audit-format.md)
- Test harness — `scripts/tests/test_eval_leanness.sh`
- [ADR-015](adr-015-leanness-self-governance.md) — the leanness self-governance decision this ADR partially supersedes (Tier A/Tier B split, warn-only growth, dogfooding-only mandate, directional registry parity all remain in force)
- [ADR-018](adr-018-third-party-skill-trust-model.md) — most recent numbering/format precedent
