# Model Delegation — Anchor, Floor, Origin, Escalation

> **Status:** Not Started
> **Created:** 2026-09-03
> **Owner:** @AdamSellke
> **Dependencies:** []
> **Origin:** [ADR-024](../../decision-records/adr-024-model-delegation.md) (Accepted 2026-09-03, incl. § Amendments A1–A3) · research [`2026-09-03-family-relative-model-routing-research.md`](../../research/2026-09-03-family-relative-model-routing-research.md)
> **Related:** [ADR-025](../../decision-records/adr-025-friction-signals.md) consumes the `escalated`/`degraded` lines this spec emits; its spec has not been created yet, so those calls land here as documented no-ops.

## Specification Contract

**Deliverable:** Implement ADR-024 — rename `model_tier` values to `anchor`/`floor`,
derive every agent's tier from the two-question rule, capture the user's **origin**
(model, effort, platform) at command entry and treat it as the **ceiling**, family-lock the
floor at or below that origin with a *verified* Cursor resolution, replace the inert
advisory `model_tier` on commands with a live `entry_level` check, and add the one dynamic
rule: a floor result that fails its check or would interrupt the human is re-run once at
anchor.

**Must Include:** Zero tier regression — all seven agents resolve to the same tier they hold
today (5 anchor, 2 floor), verifiable by a blind reader applying the two questions; a
*verified* Cursor floor, replacing `"fast"` with a value observed to resolve in a real spawn
(or a documented `degraded` fallback when none does); and a one-line, non-blocking entry
notice when a command is run below its `entry_level`.

**Hardest Constraint:** `system-instructions.md` and `cursor/writ.mdc` must stay
byte-identical outside the mirror's appendix, `commands/_preamble.md` is at its 95-line cap
and cannot absorb the new rules, and `bash scripts/eval.sh` must report `Findings: 0` after
every story. The vocabulary rename touches 7 agents, the manifest, the lint, both root
contract files, 4 adapters, the Claude Code agent definitions, the Codex TOML generator, and
two scaffolders — with the old values accepted as aliases for one minor release so nothing
already installed breaks.

**🎯 Experience Design (developer-facing):**
- **Entry point:** An agent author opens any `agents/*.md` and sees `model_tier: anchor` or
  `floor` with the two-question rule one link away. A command author sees
  `entry_level: high | standard | any` in the frontmatter they already edit.
- **Happy path:** Author asks Q1/Q2, writes the value, lint accepts it; the platform adapter
  resolves it without the author knowing which platform. A user runs `/create-spec` at their
  usual model and never sees any of this.
- **Moment of truth:** A `/create-spec` run whose generated story fails structural validation
  silently regenerates it at anchor instead of handing the user a malformed story; a
  `/implement-story` ABORT verdict is confirmed at anchor before the user is interrupted.
- **Feedback model:** Lint warns on `orchestration`/`capability` by their new names. A user who
  enters `/create-spec` at a small model on low effort sees one line — *"This command expects
  `high` entry; you're running `<model>/<effort>`. Floor-tier retries cannot escalate above
  this. Consider re-running at a higher thinking level."* — and the command continues. An
  unresolvable floor prints a `degraded` line and runs at anchor.
- **Error experience:** Nothing hard-fails. Every path degrades to today's behavior (`anchor`
  = `inherit`).

**📋 Business Rules:**
1. Only agents carry `model_tier`; values are `anchor` or `floor`. `orchestration` and
   `capability` are accepted as aliases (with a rename warning) until the next minor release
   after this spec ships, then rejected.
2. Tier is derived, not assigned: **Q1** — decides anything for others (spawns, routes context,
   judges another agent's output)? → `anchor`. **Q2** — output bounded *and* checked by a later
   gate or human before it takes effect? → `floor`; else `anchor`. No agent changes tier.
3. **Origin is read, never asked.** At entry, the spawning commands (`/create-spec`,
   `/implement-story`, and `/implement-phase`'s spec-runner) capture `anchor.model`,
   `anchor.effort`, `anchor.platform` as the harness reveals them, or `unknown`. No new state
   file: the origin is stamped on ADR-017 audit records and on `escalated`/`degraded` lines,
   and surfaced to the user only by the entry-level notice.
4. **Anchor is the ceiling.** No spawn resolves above `anchor.model` or `anchor.effort`.
   Escalation returns to the anchor, never past it.
5. **Floor resolves at or below origin**, in order: (a) the anchor's family at its lowest tier
   below the anchor, if the platform exposes one; (b) the anchor at the lowest effort below
   `anchor.effort` (`low` when effort is unknown); (c) the anchor. It never crosses vendors.
   When the origin already sits at the family floor, `floor` collapses to `anchor`, the run
   says so once, and no `degraded` line is emitted — that is correct, not degraded.
6. `model:` in an agent file remains the concrete override and always wins. The manifest drops
   its stale `model: fast|default|inherit` mirror and keeps `model_tier` only — which means
   `scripts/gen-skill.sh` (which today hard-requires `model` per agent, and which `eval.sh`
   runs as a gate) must make the field optional and read `model_tier`, and `SKILL.md` is
   regenerated.
7. **Escalation is once and counted.** A floor result that fails its check or would interrupt
   the human is re-run once at anchor; the anchor result stands; the pair counts as one attempt
   against `loop.max_iterations`; each re-run emits `escalated` (ADR-025 — a no-op call until
   that spec ships). Today's two sites: `/create-spec` Step 2.6 story validation and
   `/implement-story` Gate 0 ABORT.
8. **Commands carry `entry_level`, derived by two questions** in the same shape: **Q1** —
   spawns agents, locks a contract (spec/ADR/roadmap/design), or renders an unverified
   judgment the user acts on (review, audit, research, drift assessment)? → `high`. **Q2** —
   creates or modifies durable project artifacts (specs, issues, code, docs, git state;
   derived caches such as `.writ/context.md` do not count)? → `standard`. Otherwise → `any`.
9. **The entry check is one line, once per session, never a question.** The running model
   self-assesses the captured origin against plain guidance — `high`: a frontier-class model
   of its family at a non-minimal thinking level; `standard`: a non-smallest model or
   medium-plus effort; `any`: nothing. Writ maintains no model ranking.
10. Cursor's floor value is whatever Story 3's verification observes — no file asserts it
    ahead of the observation. `"fast"` is retired everywhere.
11. ADR-016 is history: not edited beyond the supersession header already in place.
12. Deferred, not decided here: any third tier; `coding-agent` at floor; OpenClaw live
    verification (no install available — documented as unverified).

**Success Criteria:**
- Every agent's tier is derivable from Q1/Q2 by a reader who has not seen the assignment — the
  spec reviewer derives all seven blind and matches.
- `rg "model_tier" commands/ skills/` → 0; `rg "entry_level:" commands/*.md` → 31 (every
  command, not `_preamble.md`); `rg '"fast"' agents/ adapters/ claude-code/ codex/` → 0.
- After Story 3, the Cursor floor resolves to something other than the anchor in a real spawn,
  or a `degraded` line says why not.
- One real `/create-spec` run with a forced-invalid story shows the anchor retry.
- `bash scripts/eval.sh` → `Findings: 0` after every story; `bash scripts/lint-skill.sh`
  clean; `system-instructions.md` § Model Tiers byte-identical to `cursor/writ.mdc`'s.

**Scope Boundaries:**
- **Included:** contract rewrite (root files, `.writ/docs/model-tiers.md`, lint); agent +
  manifest + scaffolder migration; four adapter tables with an *Origin source* column, the
  Cursor verification, the Claude Code nesting correction and its agent `model:` values, the
  Codex TOML generator; two escalation sites; `entry_level` on all 31 commands with the
  entry check.
- **Excluded:** any tier reassignment; a third tier; ADR-025's `signal.py` and ledger; a
  ranking of models; a blocking entry gate; any change to ADR-022's gate classes.

**⚠️ Technical Concerns:**
- Story 3 may find that *no* Cursor value resolves below anchor (neither `inherit[effort=low]`
  nor a same-prefix concrete ID is honored via `Task`). Then Cursor's floor is documented as
  `inherit` + `degraded`, and the spec still completes — that is a finding, not a failure.
- Story 4 edits `create-spec.md` and `implement-story.md`, both already over the non-blocking
  byte budget; additions are a few lines each and ADR-023's triage says leave the budget alone.
- Story 5's entry check is model self-assessment. It can be wrong in both directions; it is
  advisory and one line, so the cost of a wrong notice is one line of noise.
- Claude Code agent frontmatter is static: it cannot express "min(haiku, origin)". `haiku` is
  the family bottom, so it is always at or below any Claude origin — safe as a floor value.

**💡 Recommendations:**
- Run Story 3's Cursor verification *first* within Story 3, before touching adapter prose, so
  the tables name the observed value on first write.
- Live evidence already exists: this session's Cursor `Task` tool rejects `"fast"` as a `model`
  value and offers `inherit` plus concrete slugs whose names embed the effort level.
- Land Story 1 before Stories 2, 3 and 5 so every downstream file cites vocabulary that is
  already in the contract.

## Experience Design

### Personas
- **Agent author** — edits `agents/*.md`; needs the two questions and the value grammar.
- **Command author** — edits `commands/*.md` (or scaffolds via `/new-command`); needs the
  `entry_level` questions.
- **Platform maintainer** — edits `adapters/*.md`, `claude-code/agents/`, `codex/agents/`;
  needs the resolution table and the origin source per platform.
- **End user** — runs commands at whatever model and thinking level they chose; should notice
  nothing except cheaper story generation and, occasionally, one entry line.

### State catalog
| State | What happens | Who sees it |
|---|---|---|
| Normal spawn, floor resolves | Floor agent runs at family floor; result checked | nobody |
| Floor result fails check | One re-run at anchor; anchor result stands; `escalated` line | audit only |
| Floor unresolvable on platform | Runs at anchor; `degraded` line once | audit only |
| Origin already at family floor | Floor collapses to anchor; one line says so; no `degraded` | end user, once |
| Origin below `entry_level` | One notice line; command continues | end user, once |
| Origin unknown | `anchor.model`/`effort` = `unknown`; floor path (b) uses `low` absolute; entry check skipped (nothing to compare) | audit only |
| Alias value in a file | Lint warns with the new name; resolves as today | author |
| Unknown tier value | Lint fails (authoring) / warns and runs at anchor (runtime) | author / audit |

## Business Rules — Expanded

### Tier derivation applied (the blind-reader check)
| Agent | Q1 decides for others? | Q2 bounded + checked? | Tier |
|---|---|---|---|
| `coding-agent` | no | no — open-ended | `anchor` |
| `review-agent` | yes — judges | — | `anchor` |
| `testing-agent` | yes — judges | — | `anchor` |
| `visual-qa-agent` | yes — judges | — | `anchor` |
| `documentation-agent` | no | no — nothing checks it | `anchor` |
| `architecture-check-agent` | no | yes — checklist verdict, later gates catch a wrong PROCEED | `floor` |
| `user-story-generator` | no | yes — templated, user reviews before lock | `floor` |

### `entry_level` derivation applied (proposed; Story 5 confirms with the maintainer)
| Level | Commands (count) | Derivation |
|---|---|---|
| `high` | `assess-spec`, `create-adr`, `create-spec`, `design`, `implement-phase`, `implement-spec`, `implement-story`, `plan-product`, `prototype`, `refactor`, `refresh-command`, `research`, `review`, `security-audit` (14) | Q1 yes — spawns agents, locks a contract, or renders an unverified judgment |
| `standard` | `create-issue`, `create-uat-plan`, `edit-spec`, `initialize`, `knowledge`, `new-command`, `new-skill`, `release`, `retro`, `revert`, `ship`, `verify-spec` (12) | Q1 no, Q2 yes — creates or modifies durable artifacts |
| `any` | `migrate`, `reinstall-writ`, `status`, `uninstall-writ`, `update-writ` (5) | Q1 no, Q2 no — read-only reports or mechanical scripts |

`_preamble.md` is not a command and carries no `entry_level`. `/implement-spec` and
`/implement-story` are both `high`; the spec declines a finer ordering (ADR-024 A3).

### Platform resolution (target shape; Story 3 fills *verify* cells from observation)
| Platform | Origin source | `anchor` | `floor` | escalation |
|---|---|---|---|---|
| Cursor | model named in the harness prompt; effort from the slug suffix (`…-thinking-high`, `…-medium`) | `inherit` | *verify:* `inherit[effort=low]` → same-prefix cheapest concrete ID → `inherit` | `inherit` |
| Claude Code | reported model; effort `unknown` unless present in settings | `inherit` | `haiku` (family bottom, always ≤ origin) or `inherit` + `effort: low` | `inherit` |
| Codex CLI | `config.toml` `model` + `model_reasoning_effort` | omit `model` | omit `model`, `model_reasoning_effort = "low"` | omit / parent effort |
| OpenClaw | session config (unverified) | omit `model` | operator-configured cheaper model on `sessions_spawn`; else omit | omit |

## Implementation Approach

Five stories. Story 1 writes the contract; 2, 3 and 5 migrate the three carrier families
(agents+manifest+scaffolders, adapters+platform files, commands) against it in any order;
Story 4 wires escalation last because it cites the vocabulary and the adapter-resolved values.

| # | Story | Deps | Surface |
|---|---|---|---|
| 1 | Contract — vocabulary, origin, ceiling, two-question rules, lint aliases | none | `system-instructions.md`, `cursor/writ.mdc`, `.writ/docs/model-tiers.md`, `scripts/lint-skill.sh` |
| 2 | Agents, manifest, scaffolders — 7 renames, `model: "fast"` removed, manifest `model:` dropped (generator made tolerant, catalog regenerated), scaffolders emit `entry_level` | 1 | `agents/*.md`, `.writ/manifest.yaml`, `scripts/gen-skill.sh`, `SKILL.md`, `commands/new-command.md`, `commands/new-skill.md` |
| 3 | Adapters + Cursor verification — live spawns first, then 4 tables with origin column, Claude Code nesting fix + agent `model:` values, Codex generator | 1 | `adapters/*.md`, `claude-code/agents/*.md`, `scripts/gen-codex-agent-tomls.py`, `codex/agents/*.toml` |
| 4 | Escalation — Step 2.6 story regeneration, Gate 0 ABORT confirmation, iteration accounting, `require_literal` pins | 2, 3 | `commands/create-spec.md`, `commands/implement-story.md`, `scripts/eval.sh` |
| 5 | Entry-level check — 31 declarations, the one-line notice rule, lint grammar, non-blocking eval presence note | 1 | `commands/*.md`, `scripts/lint-skill.sh`, `scripts/eval.sh` |

Contract text lands in `system-instructions.md` § Model Tiers (paid once per invocation,
already the convention's home) — **not** `_preamble.md`. Old tier names stay resolvable
through Story 2's lint alias window. Every runtime path degrades to `anchor` = `inherit`,
which is today's behavior, so no story can make a target project worse than it is now.
