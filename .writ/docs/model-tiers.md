# Model Tiers — Portable Weight Intent

> **Status:** Shipped (`2026-07-10-model-tier-delegation`). All 7 agents carry an enforced `model_tier`; skills and commands carry the same field name as advisory documentation only.
> **Source of truth for the mechanism:** [ADR-016](../decision-records/adr-016-model-tier-delegation.md)

This document is the user-facing explainer for `model_tier`. ADR-016 captures the *why* (decision, alternatives, consequences); this document captures the *what* and *how*.

---

## Verb / Noun / Tool, and Who Gets to Choose

Model tier rides on top of the same three primitives [`.writ/docs/skills.md`](skills.md) and [ADR-009](../decision-records/adr-009-command-agent-skill-boundary.md) already establish:

| Primitive | Grammar | Spawns a model? | `model_tier` behavior |
|---|---|---|---|
| **Command** (verb) | User-invoked workflow | No — runs at the user's own session model | Advisory only |
| **Agent** (noun) | Spawned role, instantiated per phase | Yes — a command hands it a resolved model | **Enforced at spawn** |
| **Skill** (tool) | Loaded capability, no execution context of its own | No — runs inside whatever model loaded it | Advisory only |

Only agents are spawn points. Commands run at the session model; skills are inert text loaded into a caller's context. Neither structurally has a model of its own to select — so only an agent's `model_tier` is ever resolved to a real model. This follows directly from ADR-009's composition rule: *"Skills do not call commands. Skills do not spawn agents."* Skills and commands aren't spawn points; agents are.

> **Advisory only (commands/skills run at the session/caller model).** A command's or skill's `model_tier` documents assumed execution weight for a human reader. It is never resolved to a concrete model.

---

## The Two Named Tiers

Tiers are **relative, not absolute** — Writ ships no maintained ranking of model names. Each platform adapter owns the mechanics of turning a tier into its own native primitive.

| Tier | Resolves to | Use for |
|---|---|---|
| `orchestration` | The platform's `inherit`/default primitive (anchor weight) | Heavy, cross-file reasoning; multi-phase orchestration; anything that shouldn't quietly regress in quality |
| `capability` | The platform's fastest/cheapest available model (floor weight) | Narrow, high-volume, low-complexity passes where a cheaper model carries no quality risk |

Neither tier names a specific model (no `gpt-5-mini`, no `haiku`). Cursor and OpenClaw resolve both tiers through native relative primitives — Writ ships **zero model names** for those two platforms. Codex CLI and Claude Code require a concrete model identifier today, so each keeps its own small resolution table in its own adapter document, isolating the one place a name can rot.

---

## Where `model_tier` Lives

| File type | Carrier | Example |
|---|---|---|
| Skill (`skills/*/SKILL.md`) | Real `---` YAML frontmatter | `model_tier: orchestration   # advisory only` |
| Agent (`agents/*.md`) | Existing fenced **Agent Configuration** (or `visual-qa-agent.md`'s **Agent Specification**) block — not a new header | `model_tier: capability` alongside `subagent_type:` / `model:` / `readonly:` |
| Command (`commands/*.md`) | Prose note near Overview/Invocation — commands carry no frontmatter mechanism (verified 0/31 files) | `> **Model tier (advisory only):** orchestration — commands run at the user's session model, not Writ-selectable.` |

"Frontmatter" is the umbrella term used loosely across Writ's docs; the literal carrier differs by file type as shown above.

---

## Native Relative Resolution Per Platform

Each adapter owns its own resolution table — this doc is a pointer, not a duplicate:

| Platform | Adapter doc |
|---|---|
| Cursor | [`adapters/cursor.md`](../../adapters/cursor.md) → Agent Configuration Notes → Sub-Agent Models |
| Codex CLI | [`adapters/codex.md`](../../adapters/codex.md) |
| Claude Code | [`adapters/claude-code.md`](../../adapters/claude-code.md) |
| OpenClaw | [`adapters/openclaw.md`](../../adapters/openclaw.md) |

Cursor and OpenClaw resolve through native relative primitives (`inherit`/`fast`-style keywords); Codex CLI and Claude Code each maintain a small concrete-model table local to their own adapter, flagged for periodic verification as model lineups shift.

---

## Graceful Degradation

An unset, unresolvable, or unknown tier never hard-fails — it warns and falls back to the parent/anchor model, mirroring the `required_skills:` degradation contract:

| Condition | Behavior |
|---|---|
| `model_tier` unset | Resolve to parent/default (inherit). No warning. |
| `model_tier: capability` but the platform exposes no fast/cheaper model | Warn: "capability tier unavailable on \<platform\>; running at parent model." Fall back to inherit. |
| `model_tier` value unrecognized at resolution time | Warn: "unknown model_tier '\<value\>'; running at parent model." Fall back to inherit. |
| Reserved ordinal offset beyond available bands | Clamp to floor (or inherit, if the platform has one band). No warning — documented clamp. |
| Both `model:` and `model_tier:` set | Use `model:` — a concrete override always wins. No warning. |

---

## Reserved Ordinal Offsets

The schema also allows a negative ordinal form (`-1`, `-2`, ...), intended for a future finer-grained resolver ("one band below anchor," "two bands below anchor"). **No adapter resolves ordinals beyond the 2-band clamp today** — any negative offset lands on the same floor as `capability` (or `inherit`, if a platform exposes only one band).

This is a **reserve-only** convention, the same pattern `required_skills:` used before adoption: declare the grammar now, keep it inert, and let a real N-step resolver earn the behavior later rather than having competing negative-offset conventions invented piecemeal.

> **Review trigger: 2026-10-16** (90 days post-ship). If no adapter has built N-step (>2-band) resolution by this date, deprecate or revisit the reservation.

---

## Authoring

`/new-skill` and `/new-command` both scaffold the advisory field automatically:

- **`/new-skill`** emits `model_tier: orchestration   # advisory only — skills run in the caller's context, not selectable` in the generated `SKILL.md` frontmatter (safe default — a skill assuming a strong caller is a more conservative default than assuming a cheap one).
- **`/new-command`** emits the locked prose note `> **Model tier (advisory only):** <tier> — commands run at the user's session model, not Writ-selectable.` near the generated command's Overview/Invocation section, with `<tier>` chosen contextually (`orchestration` for heavy multi-phase commands, `capability` for narrow ones; default `orchestration` if unclear).

`scripts/lint-skill.sh` validates any declared `model_tier` value — in skill frontmatter, an agent's Agent Configuration block, or a command's prose note — against the shared allow-list (`^(orchestration|capability|-[0-9]+)$`), whenever it's pointed at a file. It does not add a new automated sweep over `agents/*.md` or `commands/*.md` by default; that remains a deliberate, explicit choice per invocation.

---

## Allowed Values

- **Schema:** `^(orchestration|capability|-[0-9]+)$` — `orchestration`, `capability`, or a reserved negative ordinal offset.
- **Unset:** inherits parent/default — identical to today's behavior. No warning.
- **Precedence:** an explicit concrete `model:` always overrides `model_tier:`.

---

## References

- **Mechanism rationale:** [ADR-016](../decision-records/adr-016-model-tier-delegation.md)
- **Boundary this extends:** [ADR-009](../decision-records/adr-009-command-agent-skill-boundary.md)
- **Per-platform resolution:** [`adapters/cursor.md`](../../adapters/cursor.md), [`adapters/codex.md`](../../adapters/codex.md), [`adapters/claude-code.md`](../../adapters/claude-code.md), [`adapters/openclaw.md`](../../adapters/openclaw.md)
- **Authoring tools:** [`commands/new-skill.md`](../../commands/new-skill.md), [`commands/new-command.md`](../../commands/new-command.md)
- **Lint grammar:** [`scripts/lint-skill.sh`](../../scripts/lint-skill.sh)
- **Full schema and degradation table:** [`system-instructions.md`](../../system-instructions.md) → Model Tiers section
- **Skills explainer (companion doc, same shape):** [`.writ/docs/skills.md`](skills.md)
