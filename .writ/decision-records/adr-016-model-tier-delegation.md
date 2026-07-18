# ADR-016: Model-Tier Delegation — Portable Weight Intent, Agent-as-Carrier

> **Date:** 2026-07-10
> **Status:** Accepted
> **Category:** Framework Architecture
> **Extends:** [ADR-009](adr-009-command-agent-skill-boundary.md) (command/agent/skill boundary)

## Decision

Writ agents carry an **enforced** `model_tier` field — `orchestration` or `capability`
— in their existing Agent Configuration block, expressing *relative* model-weight
intent that each platform adapter resolves to its own native primitive
(`inherit`/`fast`, omitted TOML field, cheaper `sessions_spawn` model, etc.).
Commands and skills may carry the same field, but only as **advisory**
documentation — Writ has no mechanism to select a model for either, so their
`model_tier` never resolves to anything. Resolution is **relative, not
absolute**: Writ ships no maintained ranking of model names, and tiering is
staged — two bands are resolved today, with a reserved ordinal-offset form
documented for a future N-step resolver that is **not** built yet.

This is a new, narrow axis alongside ADR-009's primitive boundary. ADR-009
answers *"is this a command, an agent, or a skill?"* This ADR answers *"which
of the three can actually have its model chosen, and how is that intent
expressed portably?"* It does not change the primitive boundary or composition
rules ADR-009 established.

## Context

Writ agents are spawned by commands with a concrete `model:` value in their
Agent Configuration block today (e.g. `model: fast`, `model: gpt-5-mini`,
`model: inherit`) depending on which adapter authored the file. This bakes a
platform's model-selection vocabulary directly into a file meant to be
portable across Cursor, Codex CLI, Claude Code, and OpenClaw. Two problems
follow:

1. **Vocabulary rot.** Concrete model names and platform-specific keywords
   change as lineups evolve; every agent file that hardcodes one is a rot
   surface.
2. **Duplicated judgment.** Each agent author has to independently decide
   "should this run at full weight or a cheaper model?" with no single vocabulary
   for expressing that intent, so the same judgment gets re-litigated file by
   file with inconsistent wording.

The `2026-07-10-model-tier-delegation` spec introduces `model_tier` to let an
author state *intent* once — "this needs full reasoning weight" or "this is a
high-volume, low-complexity pass" — and let each platform adapter own the
mechanics of turning that intent into a real model selection.

## Mechanism

### Two named tiers, relative not absolute

- `orchestration` — anchor weight. Resolves to the platform's `inherit`/default
  primitive (Cursor: `inherit`; Codex: omit `model`; OpenClaw: omit `model`
  param; Claude Code: `inherit`).
- `capability` — floor weight. Resolves to the platform's fastest/cheapest
  available model (Cursor: `"fast"`; Codex: a concrete mini ID; OpenClaw: a
  cheaper model param; Claude Code: a concrete cheap name).

Neither tier names a specific model. Cursor and OpenClaw resolve both tiers
through native relative primitives, so Writ ships **zero model names** for
those two platforms. Codex and Claude Code require a concrete name today, so
each keeps its own resolution table in its own adapter document (isolating the
one place a name can rot to a single, flagged table per platform, per the
technical spec's §2).

### Enforcement boundary: agent-as-carrier

Only an **agent's** `model_tier` is enforced — a command, when it spawns an
agent, actually passes a resolved model. Commands and skills carry the same
field name for **documentation consistency**, but neither can ever have a
model selected for it:

- A **command** runs at the user's own session model. Writ has no supervisory
  hook to override that. Its `model_tier` is a prose note (`> **Model tier
  (advisory only):** ...`) because commands have no frontmatter or
  config-block mechanism at all (verified 0/31 command files).
- A **skill** is inert loaded text — it has no execution context of its own;
  it runs inside whatever model loaded it. Its `model_tier` (in real `---`
  frontmatter) documents the *assumed* weight a skill's author expects the
  caller to be running at, purely for a reader's benefit.

This mirrors ADR-009's directional composition rule directly: **"Skills do not
call commands. Skills do not spawn agents."** (ADR-009, Composition Rules).
Skills and commands are not spawn points — only agents are — so only agents
are the layer where a `model_tier` can attach to an actual model-selection
event. Advisory-only tier on the other two primitives keeps the vocabulary
consistent without pretending Writ can enforce something it structurally
cannot.

### Staged resolution: 2-band now, N-step reserved

Resolution today is **exactly two bands** — `orchestration` and `capability`.
The schema also allows a reserved negative ordinal-offset form (`-1`, `-2`,
...) intended for a future finer-grained resolver ("one band below anchor,"
"two bands below anchor"), but **no adapter resolves ordinals beyond the
2-band clamp today**: any negative offset lands on the same floor as
`capability` (or `inherit`, if a platform exposes only one band). This is a
documented clamp, not a bug — declaring the grammar now, and reserving it
inert, prevents later specs from inventing competing negative-offset
conventions the way `required_skills:` reserved its schema ahead of adoption.

### Graceful degradation (mirrors `required_skills:`)

| Condition | Behavior |
|---|---|
| `model_tier` unset | Resolve to parent/default (inherit). No warning. |
| `model_tier: capability` but platform exposes no fast/cheaper model | Warn: "capability tier unavailable on \<platform\>; running at parent model." Fall back to inherit. |
| `model_tier` value unrecognized at resolution time | Warn: "unknown model_tier '\<value\>'; running at parent model." Fall back to inherit. |
| Reserved ordinal offset beyond available bands | Clamp to floor (or inherit if platform has one band); no warning (documented clamp). |
| Both `model:` and `model_tier:` set | Use `model:` (concrete override wins). No warning. |

An unknown or unhonorable tier never hard-fails — it warns and falls back to
the parent/anchor model, exactly as an unknown `required_skills:` entry warns
and continues rather than breaking the consumer.

## Considered Alternatives

**A. Skill-carrier — let skills enforce their own `model_tier`.** Rejected.
A skill is inert loaded text with no independent execution context: it runs
inside whatever model loaded it (a command's session model, or an agent's
resolved model). There is no spawn event a skill's `model_tier` could attach
to, so "enforcing" it is a category error — ADR-009 already establishes that
skills are wielded, not spawned. Skill `model_tier` stays advisory-only, same
as commands.

**B. Absolute tiers / platform model-class names (e.g. `gpt-5-mini`, `haiku`,
`fast-4`).** Rejected. Naming concrete model classes in a file meant to be
portable across four platforms bakes vendor- and lineup-specific vocabulary
into the contract itself — exactly the rot this ADR exists to avoid. As model
lineups shift, every agent file naming a class would need editing in lockstep.
Relative tiers (`orchestration`/`capability`) let each adapter's resolution
table absorb that churn in one place instead of scattering it across every
agent file.

**C. A full maintained model ranking (ordered list of every known model
across every platform, continuously updated).** Rejected. This violates
Writ's "delegate mechanics, own contracts" posture (the same posture that
keeps adapters, not `system-instructions.md`, owning platform tool-call
syntax): a maintained ranking is exactly the kind of mechanics-heavy,
rot-prone artifact Writ delegates to the platform rather than owning itself.
It would also require Writ to track model releases and deprecations
indefinitely — an unbounded maintenance commitment with no natural review
trigger, unlike the reserved ordinal form's dated review.

## Consequences

**Positive:**

- Agent authors express weight intent once, in one obvious place
  (`model_tier:` in the Agent Configuration block), without knowing or caring
  which platform ultimately runs the agent.
- Cursor and OpenClaw need zero maintained model names — both resolve through
  native relative primitives.
- The enforcement boundary is structurally justified (agents spawn; commands
  and skills don't), not an arbitrary policy choice — it follows directly from
  ADR-009's composition rules.
- Graceful degradation means a typo or an unresolvable tier degrades to
  today's behavior (inherit) instead of breaking a run.
- The reserved ordinal form declares the grammar early, the same way
  `required_skills:` did, preventing competing conventions from being invented
  by a later, narrower spec.

**Negative:**

- Two carriers (agent enforced, skill/command advisory) with the same field
  name risks a reader assuming a command's or skill's tier does something at
  runtime. Mitigation: the advisory prose note and frontmatter both say
  "(advisory only)" explicitly, and this ADR + `system-instructions.md`
  document the boundary plainly.
- Codex and Claude Code still need a concrete model name in their own
  resolution tables — the rot surface is narrowed, not eliminated. Mitigation:
  each table is isolated to one file per platform and flagged for periodic
  `/model` verification, rather than duplicated across every agent file.
- The reserved ordinal form is inert today; a contributor could mistakenly
  assume `-2` resolves to something more granular than `capability`. Mitigation:
  the documented clamp behavior and the dated review trigger below.

## Reserve-Only Review Trigger

> **Review trigger: 2026-10-16** (90 days post-ship). If no adapter has built
> N-step (>2-band) resolution for the reserved ordinal-offset form by this
> date, deprecate or revisit the reservation. Mirrors the `required_skills:`
> 90-day review discipline in `system-instructions.md`.

## References

- [ADR-009](adr-009-command-agent-skill-boundary.md) — the command/agent/skill
  boundary this ADR extends; source of the "skills do not spawn agents" rule
  grounding agent-as-carrier
- [ADR-014](adr-014-skill-lifecycle.md) — structural precedent for a
  reserve-only convention with a dated review trigger
- Owning spec — [`2026-07-10-model-tier-delegation`](../specs/2026-07-10-model-tier-delegation/spec.md)
- Technical spec — [`sub-specs/technical-spec.md`](../specs/2026-07-10-model-tier-delegation/sub-specs/technical-spec.md)
- `required_skills:` graceful-degradation precedent — `system-instructions.md` § Skills
