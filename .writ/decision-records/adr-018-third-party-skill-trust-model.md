# ADR-018: Third-Party Skill Trust Model (Reserve-Only)

> **Date:** 2026-07-18
> **Status:** Accepted (reserve-only — no consumer today)
> **Category:** Framework Architecture / Supply-Chain Security
> **Extends:** [ADR-009](adr-009-command-agent-skill-boundary.md) (command/agent/skill boundary), [ADR-014](adr-014-skill-lifecycle.md) (skill lifecycle)
> **Origin:** Recommendation #4 from [`2026-07-18-writ-vs-conductor-analysis.md`](../research/2026-07-18-writ-vs-conductor-analysis.md)

## Decision

Reserve a **provenance/trust axis** for Writ skills, to be activated only if and when Writ opens skill installation to **external (non-first-party) sources**. The axis has two parts:

1. **Party classification** — every skill is `party: 1p` (first-party: authored in the Writ repo, shipped and reviewed by Writ) or `party: 3p` (third-party: authored elsewhere, installed from an external source).
2. **Frozen-by-SHA installation for 3p skills** — a third-party skill is only ever installed **pinned to a specific commit SHA**, with an explicit user-facing trust warning at install and recommendation time. First-party skills carry no such gate (they are already in-repo and reviewed).

This is a **new orthogonal axis** alongside ADR-009 (*what* a skill is) and ADR-014 (*how mature* a skill is). This ADR answers *"where did this skill come from and how much do we trust the source?"*

**This is reserve-only.** As of today Writ ships **first-party skills exclusively** — there is no external skill installer, no catalog of external skills, and no consumer of the `party:` field. This ADR documents the posture now so that the first spec to open external installation inherits a defined trust model instead of inventing one under pressure. This mirrors the reserve-first discipline already used for `required_skills:` frontmatter (documented in `system-instructions.md`, adopted by no consumer) and ADR-016's reserved ordinal offsets.

## Context

Conductor (`gemini-cli-extensions/conductor`) ships a skill **catalog** (`skills/*/assets/catalog.md`) that recommends both first- and third-party skills to install. Its trust posture is notable:

- Each catalog entry declares a **`Party`** status: `1p` (official) or `3p` (community).
- Third-party skills are installed **frozen at a commit SHA**, with an explicit warning: *"This is a third-party skill. It will be installed as a frozen version (commit <sha>) for your safety."*
- Recommendations are driven by **detection signals** (dependency names + keywords) matched against project context.

Writ has no equivalent because it has no external skill ecosystem — all six current skills live in `skills/` and ship via `install.sh`. But the moment Writ allows installing a community skill (a plausible future, given the AgentSkills standard and cross-tool skill sharing), it inherits a **software supply-chain problem**: an external `SKILL.md` is executable instruction content loaded into an agent's context. An unpinned external skill can silently change between installs; a malicious or compromised one can inject instructions.

The cheapest time to decide the trust posture is **before** the first external-install feature is designed — not after community skills are already flowing in.

## The Reserved Model

### Party classification

| `party` | Meaning | Trust gate |
|---|---|---|
| `1p` | First-party: authored in the Writ repo, shipped via `install.sh`, reviewed like any product source | None — already in-repo and reviewed |
| `3p` | Third-party: authored outside the Writ repo, installed from an external URL/registry | Frozen-by-SHA + explicit warning (below) |

`party:` would be an **optional** frontmatter field. **Unset means `1p`** — every current in-repo skill is first-party by definition, so no existing skill needs editing when the axis activates. This matches ADR-014's graceful-default discipline (missing `status:` → `candidate`).

### Frozen-by-SHA installation (3p only)

When an external installer eventually lands, a `3p` skill MUST be:

1. **Pinned** — installed from an immutable reference (a commit SHA), never a moving branch/tag. The pinned SHA is recorded locally so re-installs and audits are reproducible.
2. **Warned** — the user sees an explicit trust disclosure before install *and* whenever the skill is recommended: it is third-party, it is being frozen at `<sha>`, and updating requires a deliberate re-pin.
3. **Never auto-updated** — a pinned 3p skill does not float; moving to a newer SHA is an explicit, disclosed user action (consistent with the Prime Directive's no-auto-mutation-without-confirmation posture and ADR-013's human-owned-mutation boundary).

### Detection-signal recommendation (optional, later)

If Writ ever grows a recommendation catalog, entries carry detection signals (dependency names, keywords) matched against project context — the Conductor pattern. This is explicitly **out of scope for the reserved decision** and noted only so a future catalog design doesn't reinvent it.

## Relationship to the Existing Skill Axes

- **ADR-009 (boundary):** unchanged. `party:` says nothing about whether something is a command/agent/skill.
- **ADR-014 (lifecycle):** orthogonal. A 3p skill still declares `candidate/proven/promoted` earned from its own evidence. Provenance and maturity are independent — a `3p` skill can be `proven` in *this* project's usage while remaining third-party.
- **`required_skills:` reserve:** a consumer should arguably **not** be allowed to declare a `3p` skill in `required_skills:` without an explicit acknowledgment, since structural dependence on unreviewed external content is higher-risk. This interaction is flagged for the activating spec, not decided here.

## Activation Criteria

This axis activates **only** when a spec proposes external skill installation. That spec MUST, at minimum:

- Add `party:` handling to the skill schema and `lint-skill.sh` (default `1p`).
- Implement SHA-pinning + the trust warning in the external installer.
- Define where the pinned SHA is recorded and how re-pin/update works.
- Decide the `required_skills:` × `3p` interaction.
- Add an eval check asserting no `3p` skill is installed unpinned.

Until such a spec exists, `party:` is documentation only. No lint rule, no installer, no catalog consumes it.

## Considered Alternatives

**A. Do nothing until an external ecosystem exists.** Rejected: the trust posture is a *design constraint* on the first external-install feature. Deciding it reactively — after community skills are already being shared — invites an ad-hoc, weaker model. Reserving it now costs one ADR.

**B. Trust-on-first-use (install from a moving branch/tag, no pin).** Rejected: an unpinned external instruction file can change silently between installs, defeating reproducibility and auditability. Freezing by SHA is the minimum defensible posture.

**C. Full sandboxing / capability restrictions for 3p skills.** Rejected as over-engineered for a reserve decision — Writ skills are instruction content, not sandboxable processes, and the platform (Cursor/Claude Code/etc.) owns execution. SHA-pinning + disclosure is proportionate; deeper controls can be revisited if an ecosystem materializes.

**D. Blanket ban on third-party skills.** Rejected: it forecloses a plausibly valuable future (cross-tool skill sharing via the AgentSkills standard) with no upside over a disciplined trust model.

## Consequences

**Positive:**
- The first external-install feature inherits a defined supply-chain posture instead of improvising one.
- `1p`-default means zero migration cost for existing skills when the axis activates.
- Orthogonality keeps the boundary (ADR-009) and lifecycle (ADR-014) models untouched.
- Reserving-before-adopting matches Writ's established discipline (`required_skills:`, ADR-016 offsets).

**Negative:**
- A documented-but-unused axis carries a small "reserve rot" risk (see review trigger). Mitigation: the review date forces a keep-or-drop decision.
- The model is unvalidated by real usage — its exact shape may need revision when a real external installer is designed. Accepted: this ADR reserves *intent and constraints*, and explicitly defers implementation specifics to the activating spec.

## Review Trigger

**2026-10-16** (aligned with ADR-016's 90-day reserve-review discipline). If no spec has proposed external skill installation by this date, revisit: either extend the reserve or deprecate this ADR. A reserved decision with no path to adoption is leanness debt (ADR-015).

## References

- [ADR-009](adr-009-command-agent-skill-boundary.md) — command/agent/skill boundary (unchanged)
- [ADR-014](adr-014-skill-lifecycle.md) — skill lifecycle (orthogonal maturity axis)
- [ADR-015](adr-015-leanness-self-governance.md) — leanness self-governance (reserve-rot discipline)
- [ADR-016](adr-016-model-tier-delegation.md) — model-tier delegation (reserve-review precedent)
- `system-instructions.md` — `required_skills:` reserve-first convention
- Conductor catalog trust model — [gemini-cli-extensions/conductor](https://github.com/gemini-cli-extensions/conductor) (`skills/conductor-new-track/assets/catalog.md`)
- Source analysis — [`.writ/research/2026-07-18-writ-vs-conductor-analysis.md`](../research/2026-07-18-writ-vs-conductor-analysis.md)
