# Model Tiers — Anchor, Floor, Origin, Escalation

> **Status:** Contract shipped by `2026-09-03-model-delegation` Story 1; agent, adapter, and command migration land in Stories 2–5 of the same spec.
> **Source of truth for the mechanism:** [ADR-024](../decision-records/adr-024-model-delegation.md), including its § Amendments A1–A3. [ADR-016](../decision-records/adr-016-model-tier-delegation.md) is superseded history: its agent-as-carrier boundary and graceful degradation are kept; its vocabulary, advisory carriers, and ordinal ladder are not.

This document is the user-facing explainer. ADR-024 captures the *why*; the normative contract text lives in [`system-instructions.md`](../../system-instructions.md) → Model Tiers (mirrored in `cursor/writ.mdc`); this document captures the *what* and *how* with the full derivation tables.

---

## The Model in One Sentence

Writ delegates by role, not by depth: judgment runs at the model the user chose (**anchor**), bounded and checked work runs at that model's cheapest same-family sibling (**floor**), and a floor result that fails its check is re-run once at anchor.

---

## Who Carries What

Model tier rides on the three primitives [`.writ/docs/skills.md`](skills.md) and [ADR-009](../decision-records/adr-009-command-agent-skill-boundary.md) establish. Only agents are spawn points, so only agents get a model.

| Primitive | Field | Carrier | Meaning |
|---|---|---|---|
| **Agent** (noun) | `model_tier: anchor \| floor` | Existing fenced `## Agent Configuration` block (`visual-qa-agent.md`: `## Agent Specification`, `yaml` fence) | Which model the spawning command hands it — **resolved at spawn** |
| **Command** (verb) | `entry_level: high \| standard \| any` | Existing `---` frontmatter, after `outcome:` | What the command expects the *user* to have chosen — Writ cannot pick a command's model |
| **Skill** (tool) | — | — | Loads into its caller's context; carries nothing |

A concrete `model:` on an agent is the override and always wins over `model_tier:`.

---

## The Two Tiers

| Tier | Resolves to | Use for |
|---|---|---|
| `anchor` | The user's session model — the platform's `inherit` | Anything that decides for others, or whose output is open-ended or unchecked |
| `floor` | The cheapest same-family configuration **at or below** the anchor | Bounded output (a template, a checklist verdict, a summary) that a later gate or a human checks before it takes effect |

Neither tier names a model. Writ maintains no model ranking: family aliases and `inherit` are the platforms' own primitives.

---

## Deriving an Agent's Tier — Two Questions, in Order

| Question | If yes | If no |
|---|---|---|
| **Q1.** Does this agent decide anything for others — spawn agents, route context, or judge another agent's output? | **`anchor`.** Stop. | Ask Q2. |
| **Q2.** Is its output *bounded* (a template, a checklist verdict, a summary) **and** checked by a later gate or a human before it takes effect? | **`floor`.** | **`anchor`.** |

Applied to the seven agents (the blind-reader check — a reader who has not seen the assignment should reproduce this table):

| Agent | Q1 decides for others? | Q2 bounded + checked? | Tier |
|---|---|---|---|
| `coding-agent` | no | no — open-ended | `anchor` |
| `review-agent` | yes — judges | — | `anchor` |
| `testing-agent` | yes — judges | — | `anchor` |
| `visual-qa-agent` | yes — judges | — | `anchor` |
| `documentation-agent` | no | no — nothing checks it | `anchor` |
| `architecture-check-agent` | no | yes — checklist verdict; later gates catch a wrong PROCEED | `floor` |
| `user-story-generator` | no | yes — templated; the user reviews before lock | `floor` |

This reproduces the shipped assignment exactly (5 anchor, 2 floor). No agent changes tier under ADR-024.

---

## Deriving a Command's `entry_level` — Two Questions, in Order

| Question | If yes | If no |
|---|---|---|
| **Q1.** Does the command spawn agents, lock a contract (spec/ADR/roadmap/design), or render an unverified judgment the user acts on (review, audit, research, drift assessment)? | **`high`.** Stop. | Ask Q2. |
| **Q2.** Does it create or modify durable project artifacts (specs, issues, code, docs, git state)? Derived caches such as `.writ/context.md` do not count. | **`standard`.** | **`any`.** |

Applied to the 31 commands (proposed; Story 5 confirms with the maintainer before writing):

| Level | Commands (count) | Derivation |
|---|---|---|
| `high` | `assess-spec`, `create-adr`, `create-spec`, `design`, `implement-phase`, `implement-spec`, `implement-story`, `plan-product`, `prototype`, `refactor`, `refresh-command`, `research`, `review`, `security-audit` (14) | Q1 yes |
| `standard` | `create-issue`, `create-uat-plan`, `edit-spec`, `initialize`, `knowledge`, `new-command`, `new-skill`, `release`, `retro`, `revert`, `ship`, `verify-spec` (12) | Q1 no, Q2 yes |
| `any` | `migrate`, `reinstall-writ`, `status`, `uninstall-writ`, `update-writ` (5) | Q1 no, Q2 no |

`_preamble.md` is not a command and carries no `entry_level`. `/implement-spec` and `/implement-story` are both `high`; ADR-024 A3 declines a finer ordering.

### The entry check

At entry, a command compares the captured origin (below) against its `entry_level`. If the origin is below it, the command prints exactly one line and continues — never a question, at most once per session, skipped when the origin is `unknown`:

> This command expects `<level>` entry; you're running `<model>/<effort>`. Floor-tier retries cannot escalate above this. Consider re-running at a higher thinking level.

"Below" is the running model's own assessment against plain guidance: `high` — a frontier-class model of its family at a non-minimal thinking level; `standard` — a non-smallest model, or medium-plus effort; `any` — nothing. The normative text lives in `system-instructions.md` § Model Tiers; commands do not repeat it.

---

## Origin — Read, Never Asked

Every command that spawns agents (`/create-spec`, `/implement-story`, and `/implement-phase`'s spec-runner, which passes it down) captures the **origin** at entry, from whatever the harness reveals:

| Field | Values | Notes |
|---|---|---|
| `anchor.model` | model name, or `unknown` | the user's session model |
| `anchor.effort` | `low` \| `medium` \| `high` \| … or `unknown` | the user's thinking level; Claude Code usually reveals none |
| `anchor.platform` | `cursor` \| `claude-code` \| `codex` \| `openclaw` | |

Where it goes: stamped as `origin=<model>/<effort>@<platform>` on ADR-017 audit records, on `recommendation-log.md` entries in `--recommend` runs, and on every `escalated`/`degraded` line. Never a new file under `.writ/state/`. Never shown to the user except through the entry notice.

**The anchor is the ceiling.** No spawn resolves above `anchor.model` or `anchor.effort`. Escalation returns *to* the anchor, never past it — the user's choice of model and thinking level is a cost decision Writ does not override.

---

## Resolving `floor`

In order, never crossing vendors:

1. **(a)** the anchor's own family at its lowest tier below `anchor.model`, if the platform exposes one;
2. **(b)** the anchor itself at the lowest effort below `anchor.effort` (`low` when effort is `unknown`);
3. **(c)** the anchor.

When the origin already sits at the family floor, `floor` collapses to `anchor`, the run says so once, and **no `degraded` line is emitted** — that is correct behavior, not degradation. Reaching (c) for any other reason emits `degraded`.

### Platform resolution

Each adapter owns its table; this is the target shape. *Verify* cells are filled from a real spawn by Story 3 — no file asserts a Cursor value ahead of that observation.

| Platform | Origin source | `anchor` | `floor` | escalation |
|---|---|---|---|---|
| Cursor | model named in the harness prompt; effort from the slug suffix (`…-thinking-high`, `…-medium`) | `inherit` | (a) the listed `Task` slug sharing the anchor's vendor prefix, below the anchor's tier, with effort suffix ≤ `anchor.effort` (verified 2026-09-03: Fable 5.1/high → `claude-opus-5-thinking-high`); (b) `inherit[effort=…]` is rejected by the tool; else `inherit` | `inherit` |
| Claude Code | reported model; effort `unknown` unless present in settings | `inherit` | `haiku` (family bottom, always ≤ origin) or `inherit` + `effort: low` | `inherit` |
| Codex CLI | `config.toml` `model` + `model_reasoning_effort` | omit `model` | omit `model`, `model_reasoning_effort = "low"` | omit / parent effort |
| OpenClaw | session config (unverified) | omit `model` | operator-configured cheaper model on `sessions_spawn`; else omit | omit |

Adapter docs: [`adapters/cursor.md`](../../adapters/cursor.md), [`adapters/claude-code.md`](../../adapters/claude-code.md), [`adapters/codex.md`](../../adapters/codex.md), [`adapters/openclaw.md`](../../adapters/openclaw.md).

---

## Escalation — Once, and Counted

A `floor` result is provisional. It is acted on only after its check accepts it, or — when the result would fail its check or would interrupt the human — it is re-run **once** at `anchor` and the anchor's result stands. The floor attempt and its anchor re-run count as **one attempt** against `loop.max_iterations`. Each re-run emits an `escalated` signal ([ADR-025](../decision-records/adr-025-friction-signals.md); a no-op call until that spec ships).

Sites today:

- `/create-spec` Step 2.6 — a generated story that fails structural validation is regenerated once at anchor.
- `/implement-story` Gate 0 — an `architecture-check-agent` verdict of **ABORT** is confirmed at anchor before the user is asked.

---

## Graceful Degradation

Nothing hard-fails. Every path degrades to `anchor` = `inherit`, which is today's behavior.

| Condition | Behavior |
|---|---|
| `model_tier` unset | Inherit (`anchor`). No warning. |
| `model_tier: orchestration` / `capability` (ADR-016 names) | Lint warns, naming the replacement (`anchor` / `floor`); resolves as its new name. See *Alias window*. |
| `model_tier` value unrecognized | Lint fails at authoring. At runtime: warn `unknown model_tier '<value>'; running at anchor` and run at `anchor`. |
| `floor` unresolvable on the platform | Run at `anchor`; one `degraded` line (audit only). |
| Origin already at the family floor | `floor` collapses to `anchor`; one line says so; **no** `degraded`. |
| Origin `unknown` | Floor path (b) uses `low`; entry check skipped. |
| Both `model:` and `model_tier:` set | `model:` wins. No warning. |

### Alias window

`orchestration` → `anchor` and `capability` → `floor` are accepted with a `⚠️` rename warning (exit 0) until the next minor release after the one that ships `2026-09-03-model-delegation`; the header comment above `lint_model_tier()` in [`scripts/lint-skill.sh`](../../scripts/lint-skill.sh) names that release, and flipping the two alias branches into the reject branch is the whole change. Until Story 2 lands, the seven `agents/*.md` still carry the old names and the lint warns rather than fails.

---

## Authoring and Lint

- Agent authors: ask Q1/Q2, write `model_tier: anchor` or `floor` in the agent's config block.
- Command authors: ask the `entry_level` questions, write `entry_level: high | standard | any` after `outcome:` in the command's frontmatter. `/new-command` scaffolds the field (Story 2).
- Skill authors: nothing — skills carry neither field.

`scripts/lint-skill.sh` validates any `model_tier:` value it sees anywhere in a file against `anchor|floor` (aliases warn), and any `^entry_level:` line against `high|standard|any`. Tested by `scripts/tests/test_lint_model_tier.sh`.

---

## References

- **Mechanism and rationale:** [ADR-024](../decision-records/adr-024-model-delegation.md) — Decisions 1–7 and Amendments A1–A3
- **Superseded history:** [ADR-016](../decision-records/adr-016-model-tier-delegation.md)
- **Boundary this extends:** [ADR-009](../decision-records/adr-009-command-agent-skill-boundary.md); **two-question shape:** [ADR-023](../decision-records/adr-023-stakes-proportional-diligence.md)
- **Signals consumed:** [ADR-025](../decision-records/adr-025-friction-signals.md) — `escalated`, `degraded`
- **Normative contract text:** [`system-instructions.md`](../../system-instructions.md) → Model Tiers
- **Per-platform resolution:** [`adapters/cursor.md`](../../adapters/cursor.md), [`adapters/claude-code.md`](../../adapters/claude-code.md), [`adapters/codex.md`](../../adapters/codex.md), [`adapters/openclaw.md`](../../adapters/openclaw.md)
- **Lint grammar:** [`scripts/lint-skill.sh`](../../scripts/lint-skill.sh); **tests:** [`scripts/tests/test_lint_model_tier.sh`](../../scripts/tests/test_lint_model_tier.sh)
- **Research:** [`2026-09-03-family-relative-model-routing-research.md`](../research/2026-09-03-family-relative-model-routing-research.md)
