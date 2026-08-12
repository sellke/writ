# ADR-021: Progressive Disclosure — Thin Command Contracts, On-Demand Skills, and a Budget That Binds

> **Date:** 2026-08-11 (amended 2026-08-12 — see Amendments)
> **Status:** Superseded by [ADR-023](adr-023-stakes-proportional-diligence.md) (2026-08-12)
> **Category:** Framework Architecture
> **Superseded:** The **Decision** below is void. Byte count is no longer a design constraint at any threshold, and progressive disclosure is closed as a program — not because the target was missed, but because it measured the wrong quantity. Extraction cut `implement-story`'s floor 35.9% while adding eight decision points, five of which fire unconditionally and buy nothing; no byte instrument can see that trade. **What remains valid and is deliberately preserved:** every measurement in this ADR and its two amendments, the extraction technique itself, the correction that `required_skills:` is an eager pre-load, and the five archived specs' contracts as design records. This ADR is the reason ADR-023 could be written — its own honest amendments are what falsified it.
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

## Amendments

### 2026-08-12 — The binding instrument is bytes, not lines

**Correction:** Decision point 5 makes `check_length`'s command limit (2000 → 400 lines) the binding instrument. It is superseded as the *binding* instrument by an **absolute byte budget of 24,960** — the measured shared base that every invocation pays before a command file is opened (`system-instructions.md` 20,153 + `commands/_preamble.md` 4,807). A command file may not cost more to load than the shared contract it runs inside. The 400-line cap is retained as a **secondary, non-binding tripwire**.

**Rationale:** Lines are a poor proxy for load, and the ADR said so itself — *"400 lines is derived from the current distribution … not from a measured quality threshold. Expect to tune it after 2-3 real extractions."* This is that tuning, arriving after extraction 1 of 6 rather than 3, because the first extraction measured the spread rather than assuming it. Nothing about the Decision is reversed: thin contracts, extracted skills loaded on demand, and an absolute budget alongside the ratchet all stand, as does the 2026-11-11 review trigger. Only the *unit* changes.

**Measured:** `python3 scripts/measure-invocation.py --root .`, 2026-08-12, on branch `phase/10-progressive-disclosure`. Bytes per command line vary **2.63×** across the 31 command files — 34.5 for `migrate` (13,656 bytes / 396 lines) at the narrow end, 90.8 for `implement-phase` (29,136 bytes / 321 lines) at the wide end. A 400-line cap therefore **exempts `implement-phase` entirely** — 321 lines, under the cap, yet the 4th-heaviest command file in the product — while **firing on `create-uat-plan`** at 417 lines and 16,239 bytes, a file barely half its weight. An instrument that misses the 4th-largest file and fires on a compliant one is not measuring load.

**Originating work:** Story 1 of [`2026-08-12-disclosure-implement-story`](../specs/2026-08-12-disclosure-implement-story/spec.md). Implementing the byte cap in `scripts/eval.sh` and `scripts/eval-leanness.py`, and correcting `.writ/product/roadmap.md` Phase 10's now-stale 400-line success criterion, belong to `2026-08-12-governor-enforcement`, which owns those files.

### 2026-08-12 — `required_skills:` cannot deliver "on demand"; the mechanism is an inline `Read`

**Correction:** This entry corrects a **premise**, not an instrument, and it is the entry a reader of this ADR needs first.

1. **The internal contradiction.** The Decision's opening line promises *"procedural detail moves into **skills loaded on demand**"*. Decision point 3 selects `required_skills:` as the mechanism that delivers it and claims the harness *"pre-loads only what that invocation needs."* Those cannot both be true. `required_skills:` is a **static frontmatter array**: [`system-instructions.md`](../../system-instructions.md) → *Harness contract* loads it *"before any phase work begins"* and [`adapters/claude-code.md:396`](../../adapters/claude-code.md) *"before the consumer's first phase begins."* Selection is per **command**, never per **run** — no adapter provides a per-invocation selection mechanism, and a static array cannot express one. Decision point 3's mechanism does not implement the Decision's own "on demand".

2. **The correction.** The six Phase 10 disclosure specs load each extracted skill through an inline `Read skills/<name>/SKILL.md` placed at the narrowest step or gate that needs it. That form is genuinely conditional — the agent issues the call only if execution reaches the line, so a skipped gate is free. It already ships in seven commands (`create-spec`, `implement-story`, `new-skill`, `refactor`, `release`, `research`, `ship`), and `system-instructions.md` documents it as the standing alternative to the field: *"Without the field, agents and commands continue to inline `Read skills/<name>/SKILL.md` instructions in their prompts at the point where the skill is needed."* **`required_skills:` is not used by the disclosure specs.** The Decision's *outcome* — thin contracts, extracted skills, load only what a run needs — is preserved; only the mechanism named in point 3 is replaced.

3. **Why this ADR picked the wrong one, stated plainly.** *Why `required_skills:` gets adopted instead of deprecated* argues the choice partly on the grounds that *"the convention has 0 real adoptions"*, that its review trigger *"fired on 2026-08-03 — 8 days before this ADR"*, and that *"deprecating it would mean designing the same thing again under a new name within the same phase."* A convention needing a consumer is a reason to **evaluate** a mechanism; it is not evidence that the mechanism meets the requirement. The field was adopted on its stated contract without that contract being measured against the requirement. Recording this is most of the entry's value: the failure mode is reusable.

4. **The measured consequence.** `scripts/measure-invocation.py` was itself wrong for one day and was corrected on 2026-08-12 (`e8f2a09`): declared skills now land in `eager_bytes` → the **floor**, inline reads in `conditional_bytes` → **above** the floor, and a skill carried both ways warns and is charged as eager. Under the eager mechanism, extraction is byte-neutral at best — bytes leaving a command reappear in the floor plus per-skill scaffolding, so *"progressive disclosure can increase total tokens"* stops being a risk and becomes arithmetic. Under the inline mechanism the floor falls by the full extracted weight and the ceiling is paid only on the path that fires every gate. The pilot's measured figures, `commands/implement-story.md` on 2026-08-12: **floor 49,797** (from 77,669 — **−27,872 / −35.9%**); **full-path ceiling 91,903** against a corrected pre-spec baseline of 83,770 (**+8,133 / +9.7%**); **`--quick` ceiling 82,223** against the 83,770 such a run pays today (**−1,547 / −1.8%**), and **77,365 on a `--quick` run of a dependency-free story** (**−6,405 / −7.6%**). *(The pre-`e8f2a09` figure of 77,669 was produced by an instrument blind to inline reads and must not be quoted as the ceiling baseline.)*

**Tracked exemption — the full-path ceiling regressed, and by more than the plan projected.** The projection was +3,461 (+4.1%); the measurement is +8,133 (+9.7%), exceeding it by 4,672 bytes. The justification is recorded in Story 5 of the originating spec and is summarized here because this ADR's review trigger is its destination. Every Compression Ledger target landed and five of six beat their projected yield (~4,230 bytes total), plus ~3,974 bytes of further prose compression in the command and the skills. **No gate, threshold, degradation row, fallback or always/never clause was deleted to close the gap** — the no-drift inventory verifying that is `.writ/specs/2026-08-12-disclosure-implement-story/no-drift-inventory.md`, 281 rows, zero unaccounted. The residual is **per-skill scaffolding**: eight files × (frontmatter + title + `## Purpose` + `## When to Use` + `## How to Apply`) ≈ 7,600 bytes that did not exist in the monolith, which is very nearly the whole overage. `change-surface-classification` is the extreme case — 1,896 source bytes became 2,761, roughly 34% scaffolding.

**What the pilot therefore tells the 2026-11-11 review.** Per-invocation load did drop, materially and on every run, but only the **floor** moved that way; the all-gates path costs more than the monolith. Both numbers are real and neither offsets the other — they are different runs. Two conclusions follow for the remaining five extractions: prefer **fewer, larger skills**, because the overhead is per *file* and not per byte; and treat a command whose gates nearly always all fire as the weakest candidate, since it realizes the ceiling and never the floor. ADR-021 sequenced `implement-story` first so a failure here would stop the phase rather than surface after five easier wins; this is that signal arriving on schedule, and it is a signal about the approach, not about this file.

**What this entry does not do.** It does **not** deprecate `required_skills:` — the convention remains correct for a skill a consumer genuinely needs on *every* invocation, and its status is [`system-instructions.md`](../../system-instructions.md)'s to change, not this ADR's. It does **not** reopen Decision points 1–5, the Context, the Considered Alternatives, or the Consequences. It does **not** move the **2026-11-11 review trigger** — it attaches evidence to it. That trigger already asks whether measured per-invocation load dropped for at least 4 of the 6 targeted commands; this entry tells it which number to read and why a single "ceiling" no longer describes a run.

**Measured:** `python3 scripts/measure-invocation.py --root . --command implement-story`, 2026-08-12, post-`e8f2a09`; `grep -n 'Read skills/' commands/*.md` for the seven inline adoptions; `scripts/eval-leanness.py` → `metrics.required_skills_declarations`, which reports **0** today and is expected to report 0 after all six disclosure specs land.

**Originating work:** Stories 1 and 6 of [`2026-08-12-disclosure-implement-story`](../specs/2026-08-12-disclosure-implement-story/spec.md), following a maintainer scope ruling recorded in that spec's *Approved Scope Change — 2026-08-12*. A consequence with **no owner**: `system-instructions.md`'s `required_skills:` *Status: adopted* paragraph and `adapters/claude-code.md:396` both name Phase 10 progressive disclosure as the convention's first consumer, and both become false. Neither file is in that spec's file set; the correction is recorded there and unassigned.

## References

- Roadmap: [Phase 10 — Component Contract & Progressive Disclosure](../product/roadmap.md)
- Paired decision: [ADR-020](adr-020-component-contract.md)
- Governor being extended: [ADR-015](adr-015-leanness-self-governance.md), [ADR-019](adr-019-full-surface-leanness-measurement.md)
- Skill lifecycle for extracted skills: [ADR-014](adr-014-skill-lifecycle.md)
- Boundary that keeps skills from becoming workflows: [ADR-009](adr-009-command-agent-skill-boundary.md)
- Files: [`scripts/eval.sh`](../../scripts/eval.sh) (`check_length`), [`scripts/eval-leanness.py`](../../scripts/eval-leanness.py), [`commands/_preamble.md`](../../commands/_preamble.md), [`commands/implement-story.md`](../../commands/implement-story.md), [`commands/create-spec.md`](../../commands/create-spec.md)
