# ADR-021: Progressive Disclosure — Thin Command Contracts, On-Demand Skills, and a Budget That Binds

> **Date:** 2026-08-11
> **Status:** Accepted
> **Category:** Framework Architecture
> **Extends:** [ADR-015](adr-015-leanness-self-governance.md), [ADR-019](adr-019-full-surface-leanness-measurement.md) (adds an absolute budget alongside the reduction ratchet); adopts the `required_skills:` convention reserved in [`system-instructions.md`](../../system-instructions.md)
> **Paired with:** [ADR-020](adr-020-component-contract.md) — neither ships alone
> **Origin:** `/plan-product` Phase 10 discovery (2026-08-11)

## Decision

Command files shrink to a **thin contract**; procedural detail moves into **skills loaded on demand**; and the leanness governor gains an **absolute budget** alongside its existing delta ratchet.

1. **A command file retains only:** frontmatter contract ([ADR-020](adr-020-component-contract.md)), `## Overview`, `## Invocation` table, the phase list with gate names, `## Completion`, `## References`.

2. **Per-phase procedural detail extracts to `skills/<name>/SKILL.md`**, authored through `/new-skill` so each is born `status: candidate` and passes `lint-skill.sh` on arrival.

3. **The command declares `required_skills: [...]`** so the harness pre-loads only what that invocation needs. This gives the reserved convention its **first real consumer**.

4. **Detail duplicated across ≥3 commands** moves to [`commands/_preamble.md`](../../commands/_preamble.md) (respecting its 80-line cap) or becomes a shared skill — never copied.

5. **`check_length`'s command limit goes 2000 → 400 lines**, and `per_surface.commands.chars` gains an absolute cap that **fails** rather than warns.

Applied to the top 6 files (40% of all command bytes) in descending size order, **one spec per file**, `implement-story.md` first.

## Context

### The measurement

| Measure | Value |
|---|---|
| `commands/` surface | 516,589 chars / 10,996 lines / 32 files ≈ **129k tokens** (chars/4) |
| Top 6 files | 205,104 chars = **40% of all command bytes** |
| `implement-story.md` | 49,360 chars / 961 lines ≈ **12.3k tokens loaded before any work begins** |
| `create-spec.md` | 45,772 chars / 865 lines ≈ 11.4k tokens |
| Total product surface | 1,889,002 chars |

### Why the existing governor never caught it

This is the crux, and it is not a missing-tooling problem. ADR-015 and ADR-019 built a real leanness guardian. It failed for three specific, fixable reasons:

1. **The limit cannot bind.** `check_length` caps commands at **2000 lines**. The worst offender is 961. The limit is 2× the maximum observed value — it is a runaway-content backstop, not a budget. For contrast, the same function holds `_preamble.md` to **80** lines and `spec-lite.md` to **100**.

2. **Growth warns, it does not fail.** Surface deltas land in `warnings` (non-blocking, exit 0). **Four unjustified-growth warnings for `commands` and `scripts` are live right now and have been ignored.** ADR-019's ratchet works exactly as designed; nothing was ever wired to make ignoring it costly.

3. **A ratchet is not a budget.** ADR-019 deliberately chose per-surface ratcheting against a recorded baseline over an aggregate tolerance. That is the right instrument for detecting *drift* and the wrong one for enforcing an *absolute ceiling*. A surface that is already too large ratchets happily at its bloated baseline forever.

The three fixes are additive to ADR-019, not corrective of it.

### The mission contradiction

[`mission.md`](../product/mission.md) positions Writ as *"the **thin**, portable methodology layer on top of increasingly capable AI harnesses."* 516KB of command prose falsifies "thin" by measurement. Phase 10 is not a strategic pivot — it is the phase that makes the existing mission statement true.

### Why `required_skills:` gets adopted instead of deprecated

The convention has **0 real adoptions** and its own review trigger fired on **2026-08-03 — 8 days before this ADR**. Its documented terms say *"deprecate or revisit."*

Revisiting is the correct call, and the reasoning is not sentimental: the convention was designed for precisely this problem and shipped before a consumer existed. Progressive disclosure needs a declarative, harness-resolved, per-invocation load mechanism. That is the exact contract `required_skills:` specifies — including its graceful-degradation rule (unknown names warn, never hard-fail). Deprecating it would mean designing the same thing again under a new name within the same phase.

## Considered Alternatives

**Compress prose in place; keep one file per command.**
Rejected as insufficient, though it is the cheapest option and requires no new mechanism. Realistic aggressive editing takes a 12.3k-token file to roughly 6k — still the largest single context cost in any Writ invocation, and **nothing is loaded conditionally**, so `/implement-story` on a trivial story still pays for the full pipeline's prose. Prose compression is retained as a *tactic within* extraction, not as the strategy.

**Move mechanical steps into `scripts/` for maximum determinism.**
Rejected for this phase, and it is the strongest rejected option. It offers near-zero token cost and true determinism for mechanical steps, and `scripts/` already holds 50+ files including `phase-state.py` and `story-context.py`, so the precedent exists. Three reasons it loses: (a) `scripts/` is already the **largest surface at 1,158,393 chars** — moving bytes there relocates bloat into the surface with the weakest review discipline; (b) it changes what Writ *is*, from a portable markdown methodology to platform tooling, contradicting the mission's "plain markdown, on git, portable across every platform"; (c) it breaks adapter neutrality, which `_preamble.md` names as a hard constraint. Worth revisiting for *specific* mechanical steps later; wrong as the phase's primary lever.

**Split large commands into multiple `.md` files under `commands/<name>/`.**
Rejected. Achieves file-size reduction without achieving *conditional* loading — a reader still needs all parts. It also breaks the one-file-per-command assumption in `install.sh` fan-out, `gen-skill.sh`, the README command table parity check, and the `/status` allowlist, for no benefit skills don't already provide.

**Raise the leanness limit to match reality and declare the surface acceptable.**
Named explicitly because it is the honest null option. Rejected: it resolves the contradiction by abandoning the mission's central claim rather than by doing the work. If "thin" is not the goal, the differentiator "The Contract Layer, Not Another Harness" loses its argument.

**Cut commands from the surface entirely.**
Deferred, not rejected. The goal-orientation audit ([ADR-020](adr-020-component-contract.md)) may reveal commands with no distinct outcome — genuine consolidation candidates. That is a separate decision requiring its own evidence, explicitly out of scope for Phase 10.

## Consequences

**Positive**

- Per-invocation context cost drops materially, and *conditionally* — a simple story stops paying for the full pipeline's prose.
- The mission's "thin" claim becomes measurable rather than aspirational.
- `required_skills:` gains a real consumer, resolving an overdue review trigger by adoption.
- The 400-line limit makes future bloat fail fast instead of accumulating for months, which is what actually happened under a 2000-line limit.
- Extraction produces reusable skills; procedure shared by `implement-story` and `implement-spec` becomes one skill instead of two divergent copies.

**Negative — including the one that could invalidate the approach**

- **Progressive disclosure can increase total tokens.** It trades one large upfront load for several conditional loads. A command that ends up needing every extracted skill costs *more* than the monolith, plus per-skill frontmatter overhead. `implement-story` — 961 lines of genuinely sequential pipeline — is the likeliest case to bite. **Mitigation: the success criterion is measured per-invocation load, not file size.** If real measurement shows `implement-story` loading everything anyway, that file is the correct place to grant a tracked exemption rather than force a worse outcome to satisfy a metric.
- chars/4 is an **estimate, not a tokenizer count**. The 400-line figure inherits that imprecision.
- 400 lines is derived from the current distribution (median ~250, max 961), **not from a measured quality threshold**. Expect to tune it after 2-3 real extractions.
- Skill count rises against `MAX_SKILLS = 12` (currently 6). Extracting 6 command files will likely exceed that cap, and it must be raised deliberately with justification rather than silently — the cap exists to prevent exactly the sprawl this work risks.
- Extracted skills are born `status: candidate`; promotion to `proven` accrues from real use afterward. This phase does not close the lifecycle loop.
- Indirection cost: reading a command no longer shows the whole procedure. Mitigated by keeping the phase list and gate names in the command file, so the *shape* stays visible even when the detail does not.
- 6 specs' worth of migration, each touching a high-traffic command. `implement-story` first means the riskiest extraction happens while the pattern is least proven — deliberate, since a failure there should stop the phase rather than surface after five easier wins.

**Review trigger: 2026-11-11** (90 days post-ship). If measured per-invocation load has not dropped for at least 4 of the 6 targeted commands, the thin-contract pattern is not delivering and the remaining files should stay monolithic with prose compression instead.

## References

- Roadmap: [Phase 10 — Component Contract & Progressive Disclosure](../product/roadmap.md)
- Paired decision: [ADR-020](adr-020-component-contract.md)
- Governor being extended: [ADR-015](adr-015-leanness-self-governance.md), [ADR-019](adr-019-full-surface-leanness-measurement.md)
- Skill lifecycle for extracted skills: [ADR-014](adr-014-skill-lifecycle.md)
- Boundary that keeps skills from becoming workflows: [ADR-009](adr-009-command-agent-skill-boundary.md)
- Files: [`scripts/eval.sh`](../../scripts/eval.sh) (`check_length`), [`scripts/eval-leanness.py`](../../scripts/eval-leanness.py), [`commands/_preamble.md`](../../commands/_preamble.md), [`commands/implement-story.md`](../../commands/implement-story.md), [`commands/create-spec.md`](../../commands/create-spec.md)
