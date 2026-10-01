# ADR-028: Behavioral Verification and Cross-Family Verdict Panels

> **Date:** 2026-10-01
> **Status:** Accepted
> **Category:** Framework Architecture
> **Extends:** [ADR-010](adr-010-supervised-autonomy-ceiling.md) review trigger (a) — names the evidence that trigger asks for; does not fire it. [ADR-027](adr-027-optional-judgment-provider.md) — reuses its verdict-source distinction.
> **Constrains:** [ADR-024](adr-024-model-delegation.md) Decision 3 — not amended; this ADR records why a panel reviewer is outside it. [ADR-013](adr-013-recommended-autonomous-delivery.md) — unchanged; no merge, PR, or release authority is added.
> **Deciders:** @AdamSellke
> **Part of:** `/plan-product --reconcile` 2026-10-01 (Phase 12: Behavioral Verification)
> **Origin:** pstack comparison (2026-10-01) against [`2026-09-05-goldilocks-assessment.md`](../product/2026-09-05-goldilocks-assessment.md) §1 and §2.3

## Decision

**Writ adds a verifier that proves the user's feature works by driving the running app, and lets high-stakes stories be reviewed by a panel of models from different vendors.** Both are verdict sources. Neither changes who decides a gate, and neither adds autonomy past ADR-013's boundary.

1. **A project verification skill is a Writ-owned verifier.** `/initialize` generates a project-local `verify-<app>` skill with five sections (launch, doctor, drive, evidence, cleanup) and a feature map of user-facing features. The skill drives the app through the project's own harness (Playwright, a PTY, HTTP) or the platform's native browser and terminal tools. Writ ships no runtime, daemon, or browser of its own. The generated skill must be run end to end once before it counts as delivered.

2. **UAT scenarios bind to evidence.** `/create-uat-plan` scenarios cite feature-map entries. Gate 4.5 runs the verify skill for the story's mapped features and writes evidence under the spec folder. `exit-criteria.py` checks that the evidence exists. A scenario the skill cannot drive stays a human UAT scenario and says why.

3. **Cross-family review is a panel, not a tier.** For stories that ADR-023 triage rates high-stakes, Gate 3 may add reviewers from other vendors. Each gets the same prompt and the story's acceptance criteria. A finding raised independently by two or more vendors blocks; a finding raised by one is advisory. The panel is opt-in per project and off by default.

4. **Every failure falls back to today's path.** No verify skill, an undrivable scenario, a panel model the platform rejects, or a platform that cannot spawn cross-vendor models: each leaves the gate exactly as it runs now and prints one line saying so.

## Context

### What forced the decision

The 2026-09-05 assessment measured that the eval harness's checks police Writ's own markdown and none assert that a user's feature works. Phase 11 put a script behind eight of ten `/implement-story` gates. The two left `prose-only` are Gate 1 (self-check) and Gate 4.5 (visual QA, a percentage the agent reports about its own work). UAT is still handed to a human at the end of every spec and phase.

ADR-010 names the condition for revisiting Writ's autonomy ceiling: "a concrete accountability mechanism … that makes unattended output reviewable at the rate it's produced (e.g., trustworthy machine-verifiable UAT)." Nothing in Writ produces that evidence today, so the trigger cannot be evaluated either way.

Gate 3's evaluator and review agent run on the session model's family. ADR-024 locks the floor tier to that family for good reasons, and the effect is that every verdict on a story comes from one vendor's models. Errors that vendor's models share are not caught by a second pass from the same vendor.

### External pattern

pstack (cursor/plugins, v0.15.5) ships both mechanisms in working form: `create-verification-skill` generates a project-local skill with a feature map and requires one live pass before handoff, and `interrogate` sends the same review prompt to Claude, GPT, and Grok and weights consensus findings highest. pstack pairs them with autonomous merging and an explicit rejection of planning. This ADR adopts the two verifiers and neither of those.

## Reconciliation With Existing Rules

**ADR-024 Decision 3 (floor never crosses vendors).** ADR-024 governs which model runs an *agent*: the family lock protects prompts tuned to the anchor, context windows sized for `/implement-story`'s payloads, and a predictable audit trail. A panel reviewer is not a tier assignment. It replaces no agent, receives the same review prompt the evaluator receives, and contributes findings that code counts across vendors. This is the distinction ADR-027 drew for Jev: a verdict source is outside Decision 3. Tier resolution and escalation are unchanged.

**"Cross-AI parallel coordination" (roadmap, Dropped).** That entry dropped multiple AI tools coordinating work in parallel. A panel coordinates nothing: reviewers run read-only on one finished diff and return findings. The entry stays dropped.

**"Not a browser daemon" (mission, What Writ Is Not Building).** The verify skill uses the project's harness or the platform's native tools through adapters. Writ adds a generated markdown skill and evidence files, not a process.

**ADR-013 and ADR-010.** No merge, PR, or release authority changes. This ADR names the evidence ADR-010 trigger (a) asks for. Revisiting the ceiling requires a separate ADR that cites Phase 12's measured results.

## Decision Drivers (force-ranked)

1. **Prove the artifact, not the report.** A gate verdict about user behavior must come from observing that behavior.
2. **No silent new failure mode.** Every new path falls back to today's behavior.
3. **Delegate mechanics, own contracts.** Writ owns the feature map, the evidence contract, and the consensus rule; drivers and model access belong to the project and the platform.
4. **Evidence before promotion.** The panel must show it catches what the single-vendor evaluator misses, or it is removed.
5. **Cost.** Panels run only where ADR-023 says the stakes justify them.

## Considered Options

### A. Keep human UAT and same-family review
- **Pros:** Nothing to build.
- **Cons:** Gate 4.5 stays self-report; ADR-010's trigger stays unevaluable; shared-vendor blind spots stay uncaught.
- **Risk:** Low breakage, high opportunity cost.

### B. Ship a Writ-owned browser or test runner
- **Pros:** One driver for every project.
- **Cons:** Contradicts the browser-daemon non-goal and the delegate-mechanics principle; Writ would own a runtime across every stack.
- **Risk:** High maintenance.

### C. Generated verify skill plus evidence-bound UAT, no panel
- **Pros:** Closes the larger gap; smaller scope.
- **Cons:** Leaves every review verdict with one vendor.
- **Risk:** Low.

### D. Generated verify skill, evidence-bound UAT, and an opt-in cross-family panel with a removal rule — **chosen**
- **Pros:** Meets all five drivers. The panel's cost is bounded by ADR-023 triage and its value is measured before it stays.
- **Cons:** Three specs instead of two. The panel is unavailable on platforms whose subagents cannot run other vendors' models.
- **Risk:** Low. Every path falls back.

## Decision Outcome

**Option D.** Driver 1 rejects A. Driver 3 rejects B. C meets the drivers but leaves the single-vendor gap open when a measured, removable test of it costs one spec.

**What is explicitly NOT decided:** raising the autonomy ceiling; making the panel default-on or applying it below high stakes; replacing the evaluator with the panel; per-role model configuration for agents.

## Consequences

### Removal rule for the panel

The panel is kept after Phase 12 only if, on the Phase 11 baseline story set, it raises at least one valid finding the single-vendor evaluator did not, judged by the maintainer against the story's acceptance criteria. If it does not, the panel spec is closed `Closed — Not Implemented` for the promotion step and the code path is removed.

### Platform reach

| Platform | Panel | Reason |
|---|---|---|
| Cursor | Available | The Task tool accepts concrete model IDs across vendors |
| Claude Code | Unavailable; falls back | Subagent `model` accepts Anthropic aliases, full Anthropic IDs, or `inherit` |
| Codex CLI | Unavailable by default; falls back | Subagents run the configured provider's models, OpenAI unless the user configures another |
| OpenClaw | Per adapter | Depends on the configured providers |

The verify skill is available on every platform; only its install path differs per adapter.

### Positive

- Gate 4.5 can leave `prose-only`, cutting the count from 2 to 1.
- UAT moves from a handoff list toward recorded evidence a reviewer can rerun.
- ADR-010 trigger (a) becomes measurable.

### Negative

- **Generated skills drift as the app changes.** *Mitigation:* the feature map is the maintained source; `/create-uat-plan` reports scenarios whose mapped feature no longer drives.
- **Driving an app can touch real state.** *Mitigation:* the skill's doctor step refuses a shared instance; cleanup kills only what it started and keeps evidence.
- **The panel sends the diff to other vendors.** *Mitigation:* opt-in per project in `.writ/config.md`; same path exclusions as ADR-027's diff slices.
- **Cursor-only panel.** *Mitigation:* stated in each adapter; fallback is today's path.

## Implementation Plan

Phase 12 in [`roadmap.md`](../product/roadmap.md), one spec per feature:

1. Project verification skill (`/initialize` generation, feature map, first live pass).
2. Evidence-bound UAT (`/create-uat-plan` binding, Gate 4.5 rewrite, `exit-criteria.py` evidence check).
3. Cross-family review panel (Gate 3 high-stakes path, consensus rule, config line, removal measurement).

## References

- [`2026-09-05-goldilocks-assessment.md`](../product/2026-09-05-goldilocks-assessment.md) §2.3 — gate verdict sources
- [ADR-010](adr-010-supervised-autonomy-ceiling.md) — review trigger (a)
- [ADR-023](adr-023-stakes-proportional-diligence.md) — stakes triage
- [ADR-024](adr-024-model-delegation.md) Decision 3 — family-locked floor
- [ADR-027](adr-027-optional-judgment-provider.md) — verdict source vs agent tier
- pstack: https://github.com/cursor/plugins/tree/main/pstack (`create-verification-skill`, `interrogate`)
