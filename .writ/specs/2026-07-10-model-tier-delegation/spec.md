# Model-Tier Delegation Across Agents

> **Status:** Completed ✅ (4/4 stories complete)
> **Created:** 2026-07-10
> **Owner:** Adam Sellke
> **ADR:** `.writ/decision-records/adr-016-model-tier-delegation.md` (created in Story 1)

---

## Specification Contract

**Deliverable:** A portable model-tier convention for Writ where **agents** carry an enforceable tier (`orchestration` | `capability`), resolved per-platform via **native relative primitives** (Cursor `inherit` = anchor / `fast` = floor), with skills and commands carrying **advisory-only** tier metadata — so each spawned unit runs on the cheapest model that reliably does its job.

**Origin:** Promoted from issue `.writ/issues/features/2026-07-10-model-tier-delegation.md`.

**Must Include:** The correction that makes the whole thing work — the tier attaches to the **agent spawn boundary** (the only place Writ passes a `model` parameter), not to skills (inert loaded text) or commands (user-selected session model). Skills and commands get advisory tier for intent, not enforcement.

**Hardest Constraint:** Portability without rot. Resolution must lean on platform-native abstractions (no maintained model ranking in this spec), stay purely **relative** (anchor / floor via `inherit`/`fast`), and degrade gracefully (warn → fall back to parent) when a platform can't honor a tier — mirroring `required_skills:` handling.

### Experience Design

- **Entry point (contributor):** A Writ contributor authoring or editing an agent declares `model_tier:` in the agent's Agent Configuration block and `manifest.yaml` entry, choosing `orchestration` or `capability` based on the agent's job.
- **Entry point (author of commands/skills):** A contributor may add an advisory `model_tier:` to a skill's frontmatter or as a prose note on a command (commands have no frontmatter mechanism) to document assumed execution weight — clearly labeled as advisory, since Writ can't enforce it there.
- **Happy path (contributor):** Author sets `model_tier: capability` on a narrow agent (e.g. `user-story-generator`) → at spawn, the adapter resolves it to the platform's floor model (`fast` on Cursor) → the agent runs cheaper with no quality regression on its narrow task.
- **Happy path (orchestration agent):** `coding-agent` declares `model_tier: orchestration` → resolves to `inherit` (runs at the user's anchor model) → heavy cross-file reasoning keeps its strong model.
- **Moment of truth:** A phase run (`/implement-phase` → spec-runner → `/implement-story` → coding/review/etc.) spends top-tier tokens only where reasoning demands it, and floor-tier tokens on narrow work — visibly cheaper without a felt drop in output quality.
- **Feedback model:** The tier is declared in one obvious place (frontmatter + manifest), greppable, and self-documenting. Resolution is traceable: an adapter's tier→model table shows exactly what a tier becomes on that platform.
- **Error experience:** A platform that can't honor a requested tier emits a **warning** and falls back to the parent/default model — never a hard failure. Same graceful-degradation shape as an unknown `required_skills:` entry.
- **Empty/unset state:** An agent with no `model_tier:` declared behaves exactly as today (inherits parent/default). The convention is additive; silence means "inherit."
- **Reserved state:** The frontmatter contract documents an **ordinal-offset vocabulary** for future finer stepping, marked reserve-only — declared now, resolved as 2-band now (like `required_skills:` was reserved before adoption).

### Business Rules

- **Agents carry the enforced tier.** `model_tier:` in the agent's Agent Configuration block and the agent's `manifest.yaml` entry is authoritative and applied at spawn time.
- **Two named tiers ship:** `orchestration` (→ anchor / `inherit`) and `capability` (→ floor / `fast`).
- **Commands and skills may declare `model_tier` as advisory documentation only.** A command runs at the user's session model (not Writ-selectable on Cursor); a skill runs in its caller's context (loading a skill is not a model invocation). Advisory declarations must be visibly labeled as such wherever they appear.
- **Relative, not absolute, semantics.** A capability-tier unit runs at or below its invoking unit. The boundary holds regardless of which concrete models a platform exposes — no absolute model-class names are baked into the portable contract.
- **Native resolution, no maintained ranking.** Tier → concrete model uses each platform's native abstraction (`inherit`/`fast` on Cursor; `model` param / omit on OpenClaw; concrete-or-mini IDs on Codex). This spec ships **no** per-platform model ranking.
- **Reserved ordinal offsets.** The contract documents an ordinal-offset form (anchor − N, clamped to floor) as reserve-only. No adapter resolves beyond 2 bands in this spec; authors may not expect >2-band resolution yet.
- **Graceful degradation.** Unknown or unhonorable tier → fall back to parent/default, **warn, never hard-fail**.
- **No behavioral regression.** Mapping today's ad-hoc `model:` settings to tiers must preserve current behavior exactly (`fast` → capability, `default`/`inherit` → orchestration/inherit).
- **An ADR records the decision** — agent-as-carrier, relative-not-absolute, staged (2-band now / N-step reserved) resolver.

## Current State

- **Model selection is per-agent and ad hoc.** In `.writ/manifest.yaml`: `architecture-check-agent` and `user-story-generator` are `model: fast`; `coding-agent`, `documentation-agent`, `review-agent`, `testing-agent` are `model: default`; `visual-qa-agent` is `model: inherit`.
- **Agent config block and manifest disagree in vocabulary.** The adapter docs describe `model: "fast"` / default / inherit, but there is no single portable tier concept — just three loosely-used string values.
- **No tier concept ties model choice to the verb/noun/tool boundary.** ADR-009 defines command/agent/skill roles but says nothing about which model tier each runs under.
- **No frontmatter (or equivalent config-block) contract for tier.** `required_skills:` exists as a reserved convention; there is no `model_tier:` (or equivalent) documented for commands, agents, or skills. Note: skills have real `---` frontmatter; agents have a fenced Agent Configuration block; commands have no config-block mechanism today (verified: 0/31 command files carry a `---` block).
- **Adapters map `model: "fast"` narrowly.** `adapters/cursor.md` (§ Sub-Agent Models) maps `"fast"` → Cursor fast model, default → inherit. `adapters/codex.md` maps agents to concrete model IDs (`gpt-5-mini`) in a TOML table. `adapters/openclaw.md` describes an optional `model` param on `sessions_spawn`. `adapters/claude-code.md` (§ Model Selection) already runs its own 3-way concrete mapping (`inherit`/`sonnet`/`haiku`). None frame this as a portable tier with graceful degradation.
- **Result:** everything tends to inherit the parent (often a top-tier model), even for narrow, well-scoped agent work a cheaper model could execute reliably.

## Expected Outcome

- All 7 agents declare an explicit `model_tier` (`orchestration` | `capability`) in their Agent Configuration block and `manifest.yaml`, mapped from today's settings with **zero behavioral regression**.
- Each adapter (`cursor`, `codex`, `openclaw`, `claude-code`) documents a tier → native-resolution table plus graceful-degradation behavior.
- `system-instructions.md` (and its `cursor/writ.mdc` mirror) documents the tiering convention alongside the verb/noun/tool boundary and `required_skills:`, including the reserved ordinal-offset vocabulary and the advisory-only status of command/skill tier.
- `/new-skill` scaffolds an advisory `model_tier:` frontmatter field; `/new-command` documents advisory `model_tier:` as a prose note (commands have no frontmatter mechanism); the shared frontmatter/boundary lint validates tier values wherever they appear.
- An ADR (`adr-016`) captures the relative / agent-carrier / staged-resolver design and the rejected alternatives.
- A `.writ/docs/model-tiers.md` explainer gives the user-facing framing, and root docs (`README.md`, `AGENTS.md`) reference the convention where model behavior is described.

## Success Criteria

1. `rg "model_tier:" agents/` returns an explicit tier for **all 7** agents; each value is `orchestration` or `capability`, and each matches the agent's `manifest.yaml` entry.
2. The tier mapping preserves current behavior: `architecture-check-agent` and `user-story-generator` resolve to the floor model (as `fast` does today); the other five resolve to inherit/anchor (as `default`/`inherit` do today). Verified by an adapter resolution table review — no agent changes which concrete model it runs on.
3. `adapters/cursor.md`, `adapters/codex.md`, `adapters/openclaw.md`, and `adapters/claude-code.md` each contain a tier → native-resolution table and a documented graceful-degradation rule (warn → fall back to parent).
4. `system-instructions.md` and `cursor/writ.mdc` document the `model_tier` convention (two named tiers, advisory-for-commands/skills, reserved ordinal offsets, graceful degradation) — byte-identical Skills/tiering content between the two files per Phase 4 parity discipline.
5. `/new-skill` scaffolds an advisory `model_tier:` frontmatter field, and `/new-command` documents advisory `model_tier:` as a prose note (commands have no frontmatter mechanism), each with an inline/adjacent "advisory only" label; `scripts/lint-skill.sh` (or the shared frontmatter lint) rejects a `model_tier` value outside the allowed set with a clear remediation.
6. `.writ/decision-records/adr-016-model-tier-delegation.md` exists, records agent-as-carrier + relative + staged-resolver, and lists the considered alternatives (skill-carrier, absolute tiers, full ranking).
7. `.writ/docs/model-tiers.md` exists with the user-facing explainer; `README.md` and `AGENTS.md` reference the convention.

## Scope Boundaries

**Included:**

- `model_tier` tier vocabulary (`orchestration` | `capability`) + frontmatter/config-block contract with reserved ordinal-offset form
- Agent adoption across all 7 agents (Agent Configuration block + `manifest.yaml`), mapped from current settings with no regression
- 2-band native adapter resolution + graceful-degradation docs in `cursor`, `codex`, `openclaw`, and `claude-code` adapters
- `system-instructions.md` + `cursor/writ.mdc` convention documentation (parity-mirrored)
- `/new-skill` advisory `model_tier:` frontmatter scaffolding; `/new-command` advisory `model_tier:` prose-note documentation; lint validation of tier values wherever they appear
- `.writ/decision-records/adr-016-model-tier-delegation.md`
- `.writ/docs/model-tiers.md` explainer + `README.md` / `AGENTS.md` references

**Excluded (deferred, evidence-gated):**

- The refreshable per-platform model-family **ranking** and **N-step (>2-band) resolution** — reserved by the contract, built only when band-collapse is shown to cost quality
- **Anchor-model detection** beyond native `inherit` (reading the concrete session model at runtime)
- A **quality-regression eval harness** measuring capability-tier output — this spec ships the convention on the `convention_only` posture (agents already run `fast` today with no measured regression)
- **Auto-downgrading** existing agents beyond preserving today's settings — no agent's effective model changes in this spec
- Enforcing tier on commands or skills (structurally not possible; advisory only)
- **Introducing a real frontmatter mechanism for commands** — verified absent today (0/31 command files); advisory command tier ships as a prose note instead, not YAML frontmatter
- `adapters/claude-code.md` model-tier section: Claude Code already runs a 3-way concrete model mapping (`inherit`/`sonnet`/`haiku`, verified in `adapters/claude-code.md` § Model Selection) rather than a clean binary fast/inherit primitive. Story 3 folds this in **using concrete model names, mirroring the Codex mini-ID pattern** — not a clean tier table, and not deferred.

## Implementation Approach

### Frontmatter contract (Story 1)

Add `model_tier` to the documented frontmatter vocabulary. **Note on carriers:** "frontmatter" here is the convention's umbrella term (matching the `required_skills:` precedent), not a literal `---` YAML block on every file type. The actual carrier per file type is:
- **Skills:** real `---` YAML frontmatter (already exists).
- **Agents:** the existing fenced **Agent Configuration** block in each `agents/*.md` file (`subagent_type:`, `model:`, `readonly:`) — `model_tier:` is added as a new line in that same block, not a new `---` header.
- **Commands:** commands have no frontmatter mechanism today (verified: 0/31 command files carry a `---` block). Advisory `model_tier:` for commands is documented as a **prose note** near the command's Overview/Invocation section, not YAML frontmatter. Introducing real command frontmatter is out of scope for this spec.

```yaml
# Agent Configuration block (ENFORCED at spawn) — agents/*.md
model_tier: orchestration   # → anchor / inherit
# or
model_tier: capability      # → floor / fast

# Skill frontmatter (ADVISORY ONLY — documentation of assumed weight)
model_tier: orchestration   # advisory: skills run in the caller's context

# Command prose note (ADVISORY ONLY — no frontmatter mechanism exists for commands)
# Model tier: orchestration — advisory only; commands run at the user's session model
```

- **Named tiers:** `orchestration` (anchor), `capability` (floor).
- **Reserved ordinal form (documented, not resolved):** `model_tier: -1` style offset from the anchor, clamped to floor — reserve-only, like `required_skills:` before adoption. A 90-day-style review note ties its fate to evidence.
- **Manifest field:** agent entries gain `model_tier:` alongside/replacing the ad-hoc `model:` (keep `model:` as the concrete-override escape hatch where a platform needs it; `model_tier:` is the portable intent). Story 1 documents the precedence: explicit `model:` overrides `model_tier:` where both exist.

### Agent adoption mapping (Story 2)

| Agent | Today (`manifest.yaml`) | `model_tier` | Rationale |
|---|---|---|---|
| architecture-check-agent | `fast` | `capability` | Narrow, bounded read-only design check |
| user-story-generator | `fast` | `capability` | Parallel boilerplate authoring |
| coding-agent | `default` | `orchestration` | Heavy cross-file TDD reasoning |
| review-agent | `default` | `orchestration` | Judgment-heavy quality gate |
| testing-agent | `default` | `orchestration` | Coverage reasoning + regression analysis |
| documentation-agent | `default` | `orchestration` | Framework-adaptive synthesis |
| visual-qa-agent | `inherit` | `orchestration` | Keeps inherit; orchestration maps to inherit/anchor |

This mapping is a **rename-to-portable, not a behavior change** — the resolved concrete model for each agent is identical to today.

### Adapter resolution, 2-band native (Story 3)

| Tier | Cursor | Codex | OpenClaw | Claude Code |
|---|---|---|---|---|
| `orchestration` | `inherit` (anchor) | omit `model` / inherit | omit `model` param | `inherit` |
| `capability` | `"fast"` | concrete mini ID (e.g. `gpt-5-mini`) | `model` param → cheaper model | concrete name (e.g. `haiku`) |

Claude Code has no clean binary fast/inherit primitive — its adapter already runs a 3-way concrete mapping (`inherit`/`sonnet`/`haiku`, verified in `adapters/claude-code.md` § Model Selection). Story 3 folds it in with concrete names, mirroring the Codex mini-ID pattern, rather than deferring it.

Each adapter documents: (a) the table above, (b) graceful degradation — if the platform can't honor a tier (no fast model available, unknown value), warn and fall back to the parent/default model; (c) a note that this is the 2-band resolution and the ordinal-offset form is reserved.

### Authoring + lint (Story 4)

- `/new-skill` scaffolds `model_tier:` frontmatter with an inline `# advisory only` comment. `/new-command` documents advisory `model_tier:` as a prose note near Overview/Invocation (commands have no frontmatter mechanism) with an adjacent "advisory only" label — neither form should be mistaken for enforcement.
- `scripts/lint-skill.sh` (and/or the shared frontmatter validation used by `/new-skill` and `/refresh-command`) validates that any `model_tier:` value is one of the allowed forms (`orchestration`, `capability`, or a reserved ordinal offset) and rejects others with a remediation message.
- `.writ/docs/model-tiers.md` explains the convention with the verb/noun/tool framing; `README.md` and `AGENTS.md` link to it where model behavior is described.

## Stories Plan

| # | Story | Dependencies |
|---|---|---|
| 1 | Tier contract + ADR-016 (vocabulary, `system-instructions.md`/`cursor/writ.mdc`, reserved ordinal offsets) | None |
| 2 | Agent adoption — `model_tier` on all 7 agents + `manifest.yaml`, mapped with no regression | Story 1 |
| 3 | Adapter resolution — 2-band native tables + graceful degradation (cursor, codex, openclaw, claude-code) | Story 1 |
| 4 | Authoring & lint integration + `.writ/docs/model-tiers.md` + root doc references | Stories 1, 2, 3 |

Stories 2 and 3 may run in parallel after Story 1. Story 4 is the synthesis story.

## Technical Decisions

- **Tier carrier is the agent, not the skill.** The `model` parameter only exists at the agent spawn boundary. A skill is loaded text with no independent model; a command runs at the user's session model. Putting an *enforced* tier on either would be inert. Skills/commands get advisory tier for intent. (This corrects the originating issue's headline framing; the issue's intuition — orchestration high, capability low — is preserved, only the carrier moves.)
- **Relative, native resolution — no ranking in this spec.** Cursor's `inherit`/`fast` already give a relative 2-band system for free. Building a maintained per-platform model ranking would rot (platforms reshuffle lineups constantly) and violate the roadmap's "delegate mechanics, own contracts" principle. The ranking + N-step resolution is reserved and evidence-gated.
- **Reserved ordinal offsets, resolved as 2-band now.** The 4-level orchestration nesting (`/implement-phase` → spec-runner → `/implement-story` → agents) is real, so the contract must be *able* to express per-level step-down. But most platforms expose ~3 reasoning bands, so deeper steps clamp to the floor anyway. Declaring the vocabulary now (inert until the ranking story lands) mirrors how `required_skills:` was reserved — authors annotate intent once; resolution deepens later without re-annotation.
- **`convention_only` evidence posture.** Agents already run `fast` today with no measured regression, so the spec ships the convention and wiring without a gating eval harness. A regression-evidence story is a documented follow-up, not a blocker.
- **Preserve `model:` as an escape hatch.** Where a platform genuinely needs a concrete model ID (Codex today), `model:` stays available and takes precedence over `model_tier:`. `model_tier:` is the portable intent; `model:` is the concrete override.

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Advisory command/skill tier read as enforceable | High | Medium | Label "advisory only" inline in every scaffold, doc, and adapter mention; the ADR states the enforcement boundary explicitly |
| Reserved ordinal vocabulary confuses authors (inert but present) | Medium | Low | Mark reserve-only with a review trigger, same as `required_skills:`; docs state "resolved as 2-band today" |
| Agent tier mapping silently changes a model | Low | High | Story 2 DoD includes an adapter-resolution review proving each agent resolves to the same concrete model as today |
| Graceful-degradation path untested across platforms | Medium | Medium | Each adapter documents the fallback rule; Story 3 DoD walks the "no fast model / unknown value → warn + inherit" path per adapter |
| Scope creep into building the ranking / eval harness | Medium | Medium | Scope Boundaries name both as excluded/deferred; drift anchors in spec-lite flag them |
| `cursor/writ.mdc` and `system-instructions.md` drift | Medium | Medium | Story 1 mirrors tiering content byte-identically; DoD verifies via `diff` (Phase 4 parity discipline) |

## References

- Issue — `.writ/issues/features/2026-07-10-model-tier-delegation.md` (this spec promotes it)
- ADR-009 — `.writ/decision-records/adr-009-command-agent-skill-boundary.md` (verb/noun/tool boundary this tiering extends; skills-don't-spawn-agents rule that grounds the agent-carrier correction)
- Spec 2026-05-03-skills-foundation — established `required_skills:` reserve-only convention this contract mirrors
- `adapters/cursor.md` § Sub-Agent Models, `adapters/codex.md` § Writ agents ↔ Codex TOML, `adapters/openclaw.md` § Spawning Sub-Agents, `adapters/claude-code.md` § Model Selection — existing model-mapping surfaces
- Roadmap Design Principle #4 — "Delegate mechanics, own contracts" (the no-ranking rationale)

## Out of Scope (Reserved for Follow-Up Specs)

- **Refreshable per-platform model-family ranking + N-step resolution** — the finer-grained resolver behind the reserved ordinal vocabulary
- **Anchor-model detection** — reading the concrete session model at runtime for true relative stepping beyond `inherit`
- **Quality-regression eval harness** — measured evidence that capability-tier agents don't regress on their narrow tasks
- **Adapter-level auto-downgrade heuristics** — automatically choosing tiers for new agents based on role signals
