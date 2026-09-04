# ADR-024: Model Delegation — Orchestrators Anchor, Executors Floor, Failures Escalate

> **Date:** 2026-09-03
> **Status:** Accepted
> **Category:** Framework Architecture
> **Supersedes:** [ADR-016](adr-016-model-tier-delegation.md) — its vocabulary, its advisory carriers, and its reserved ordinal ladder; its agent-as-carrier boundary and graceful degradation are kept
> **Extends:** [ADR-009](adr-009-command-agent-skill-boundary.md) (only agents are spawned, so only agents get a model), [ADR-023](adr-023-stakes-proportional-diligence.md) (the two-question triage shape)
> **Deciders:** @AdamSellke
> **Amended:** 2026-09-03 — origin capture, anchor-as-ceiling, and `entry_level` on commands (see § Amendments; Decision 5 is revised there)
> **Research:** [`2026-09-03-family-relative-model-routing-research.md`](../research/2026-09-03-family-relative-model-routing-research.md)

## Decision

**Writ delegates by role, not by depth. Judgment runs at the model the user chose. Bounded, checked work runs at that model's cheapest sibling. When the cheap result fails its check, the retry runs at the user's model.** That is the whole model. Everything below is its consequences.

1. **Two tiers, named for what they are.** `model_tier` keeps its field name and gets two values: **`anchor`** (the user's session model, via the platform's `inherit`) and **`floor`** (the cheapest same-family configuration the platform exposes). The old values `orchestration` and `capability` are accepted as aliases for one minor release, then rejected by lint. `capability` is retired because it reads as the opposite of what it meant — `adapters/claude-code.md` needed a paragraph to explain that "capability doesn't always mean the floor." A word that needs a paragraph is the wrong word.

2. **Which tier an agent gets is decided by two questions, in order, from what the author already knows:**

   | Question | If yes | If no |
   |---|---|---|
   | **Q1.** Does this agent decide anything for others — spawn agents, route context, or judge another agent's output? | **`anchor`.** Stop. | Ask Q2. |
   | **Q2.** Is its output *bounded* (a template, a checklist verdict, a summary) **and** checked by a later gate or a human before it takes effect? | **`floor`.** | **`anchor`.** |

   Applied to the seven agents today: `coding-agent` (open-ended → Q2 no), `review-agent`, `testing-agent`, `visual-qa-agent` (judges → Q1 yes), `documentation-agent` (bounded, but nothing checks it → Q2 no) are `anchor`; `architecture-check-agent` (checklist verdict, advisory, later gates catch a wrong PROCEED) and `user-story-generator` (templated, the user reviews every story before lock) are `floor`. **This reproduces the shipped assignment exactly.** No agent changes tier under this ADR; the assignment gains a rule it can be checked against.

3. **`floor` is family-locked.** It resolves, in order, to: (a) the anchor's own family at its lowest tier the platform exposes; (b) the anchor itself at reduced reasoning effort; (c) the anchor. It never crosses vendors. Reasons: agent prompts are tuned against the anchor's instruction-following idioms; a cross-family model may have a smaller context window and truncate the `spec_lite_*` payloads `/implement-story` routes to each gate (Claude Code documents that a subagent's window is sized by *its* model); and a same-family floor is predictable from the anchor alone, which keeps the ADR-017 audit trail legible.

4. **Floor results are provisional — the dynamic rule.** A `floor` result is acted on only after one of two things: its check accepts it, or — when the result would fail its check or would interrupt the human — it is re-run **once** at `anchor` and the anchor's result stands. The normal iteration caps (`loop.max_iterations`) count the pair as one attempt. Each re-run emits an `escalated` signal ([ADR-025](adr-025-friction-signals.md)). This is a cascade with Writ's existing gates as the verifier, not a classifier: nothing estimates task difficulty up front.

   Concretely, today: a generated story that fails `/create-spec`'s structural validation is regenerated at anchor; an `architecture-check-agent` verdict of **ABORT** is confirmed at anchor before the user is asked whether to proceed.

5. **Only agents carry `model_tier`.** The advisory-only carrier on commands and skills is removed — a field that never resolves to anything is, in ADR-023's terms, not a decision. Today 2 of 32 command files and 0 skills carry it; removal is a two-line change. Commands run at the session model. Skills run in their caller.

6. **Kept from ADR-016 unchanged:** agent-as-carrier (the spawn is the only place a model is chosen), `model:` as a concrete override that always wins, and graceful degradation — an unresolvable tier warns and runs at `anchor`, never fails.

7. **Removed from the contract:** the reserved `-1 / -2` ordinal ladder (already deprecated 2026-08-11 by `retire-dead-prescription`; this ADR is the forward record that resolution asked for), the "staged 2-band / N-step resolver" framing, and the "relative-not-absolute" theory. The family rule replaces all three with one sentence.

## Context

### What the maintainer asked for

> Commands are initiated from a specific chosen model. As the model reasons through a command and is prompted to delegate to other agents, I want to make sure that the model (n) is able to delegate lesser tasks to lesser models (n-1, n-2…) within the original model's family, so that we can be as efficient with delegation and token usage as possible. … ADR-016 maybe needs to be rewritten and reconsidered so that it's not a distraction but provides a clear model for model tiering and delegation.

Two of the three ideas in that request survive contact with the evidence intact — *delegate lesser tasks to lesser models* and *within the family*. The third — *n-1, n-2 by delegation level* — does not, and this ADR says why rather than quietly building something else.

### Why ADR-016 became a distraction

ADR-016 was correct on the boundary (only agents get a model) and wrong on emphasis. It spent most of its length on things that do nothing: a reserved ordinal grammar no adapter resolved, an "advisory" tier on commands and skills that could never resolve, a review trigger, and a theory of relative resolution. The two facts that matter — *which agents run cheap, and why* — were a table in an adapter. Its tier names required explanation. Twenty-three days ago `retire-dead-prescription` deprecated the ordinals and left the ADR standing with a live-looking trigger and no forward record. The research doc's Finding 1 documents the resulting inconsistency.

### What the evidence says (research doc, Findings 2–3)

- **Orchestrators must not step down.** Writer Inc. (July 2026) ran 22 enterprise tasks across six models under two orchestration layers: delegation held at ~0.85 only on the two strongest models and collapsed to ~0.45 on the fast tier. COPE (2025) found the same: larger planners lift smaller executors. Anthropic's Fable 5 → Sonnet 5 team kept 96% of an all-Fable BrowseComp score at 46% of the cost *because* the orchestrator stayed at full weight.
- **Writ's nesting is four deep and three of the four levels are orchestrators.** `/implement-phase` → spec-runner → `/implement-story` → gate agents. A per-level `n-1` would put `/implement-story` — which spawns five agents, routes context to each, and adjudicates their verdicts — at `n-2`. That is the configuration Writer measured at 0.45. Depth does not predict complexity; role does.
- **Cheaper per token is not cheaper per task.** In Databricks' merged-PR benchmark, Sonnet 5 was 1.7× cheaper per token than Opus 4.8 and cost *more* per task ($2.09 vs $1.94) because it consumed 1.9× the tokens. This is why Q2 requires *bounded* output: the floor is a bet that pays on templated work and loses on open-ended coding.
- **Routers do not beat single-best models reliably.** LLMRouterBench (ACL 2026 Findings) re-evaluated ten routing methods, including a commercial one, and found several fail to beat simply using the best model. A per-spawn difficulty classifier is therefore rejected; a verifier-driven cascade (FrugalGPT's shape, and the shape the routing survey identifies as the one that beats single-model on both axes) is adopted instead — and Writ's gates already are the verifier.
- **No platform exposes "one step down" as a model value.** Cursor accepts `inherit` or a concrete ID with `[effort=…]` brackets; Claude Code accepts the family aliases `haiku`/`sonnet`/`opus`/`fable`, a full ID, or `inherit`; Codex accepts a concrete ID and `model_reasoning_effort`, and picks a cost-balanced setup itself when unpinned. The family rule in Decision 3 is written against these primitives, not against a Writ-maintained ranking.

### Why escalation is cheap enough to be the default

Let the floor cost `f`, the anchor cost `a`, and the floor's failure-at-check rate `p`. Floor-first costs `f + p·a`; anchor-only costs `a`. Floor-first is cheaper whenever `p < 1 − f/a`. With a floor at roughly a fifth of the anchor's price — the usual gap between a family's smallest and largest tier — the break-even is `p ≈ 0.8`: a floor agent has to fail its check **four times in five** before anchor-only wins. That is why the rule is "floor, then escalate once" rather than "guess which model." The number that matters is `p` per agent, and ADR-025's `escalated` signal is how Writ learns it.

This arithmetic covers only failures the check *catches*. A floor error the check misses is a quality loss the cascade cannot see — which is exactly why Q2 admits to `floor` only work that *is* checked downstream.

### Platform resolution

The adapter tables are rewritten to this shape. Where a cell says *verify*, the value is inferred from documentation and must be confirmed by one real spawn before the spec that ships it closes.

| Platform | `anchor` | `floor` | escalation |
|---|---|---|---|
| Cursor | `inherit` | *verify:* `inherit[effort=low]` if brackets accept `inherit`; else the cheapest concrete ID sharing the anchor's vendor prefix from the runtime model list; else `inherit`. **`"fast"` is not a documented `model` value and is retired.** | `inherit` |
| Claude Code | `inherit` | `haiku` (same-family alias; a smaller window than the anchor — acceptable for the two floor agents' bounded payloads) or `inherit` + `effort: low` | `inherit` |
| Codex CLI | omit `model` | omit `model`, `model_reasoning_effort = "low"` — or leave both unpinned and let Codex's own cost-balancing choose (single vendor, so family-locked by construction) | omit / parent effort |
| OpenClaw | omit `model` | operator-configured cheaper model on `sessions_spawn`; else omit | omit |

**Two stale adapter claims are corrected in the same spec:** `adapters/cursor.md` maps `capability → "fast"`, which the Cursor docs do not list as a `model` value (research doc Finding 2 — medium confidence that both floor agents are silently running at anchor today); `adapters/claude-code.md` § Known Limitations says subagents cannot spawn subagents, and they now nest three deep.

## Decision Drivers (force-ranked)

1. **Clarity a new reader can hold in one sentence.** The maintainer's word was *distraction*. A model that needs a theory section is not a model.
2. **Evidence over the requested shape.** The request's *intent* (cheaper delegation, same family) is honored; its *mechanism* (depth ordinals) is replaced, with the evidence named.
3. **Nothing Writ has to maintain.** No model ranking, no release tracking. Family aliases and `inherit` are the platforms' own primitives.
4. **Zero regression at adoption.** Every agent resolves to the same tier it holds today; the ADR adds a rule and a cascade, not a re-assignment.
5. **Measurable, then tunable.** The one number that governs the bet (`p` per floor agent) is recorded by a signal, not estimated.

## Considered Options

### A. Keep ADR-016 as is
- **Pros:** No work.
- **Cons:** The maintainer has said it is a distraction; its ordinal section describes a mechanism that was deprecated three weeks ago; its tier names require explanation; the Cursor floor may be dead.
- **Risk:** Low today, compounding — every reader re-derives what the ADR should state.

### B. Rebuild the N-step ordinal ladder, depth-relative
- **Pros:** Matches the request literally; the grammar existed.
- **Cons:** Contradicted by Writer and COPE — it steps orchestrator layers down. Requires the per-platform ranking ADR-016 rejected. Reopens a 23-day-old deprecation without producing the consumer its Business Rule 6 demanded.
- **Risk:** Medium-high — quality loss at the layers that must stay strong, invisible until review iterations climb.

### C. A per-spawn complexity classifier
- **Pros:** Optimal in principle.
- **Cons:** LLMRouterBench; needs per-workload calibration Writ cannot ship; adds a judgment to every spawn (ADR-023). Writ already has the verifier half of a cascade — the classifier buys nothing the escalation rule does not.
- **Risk:** High.

### D. Role-based tiers, family-locked floor, escalate-on-failure — **chosen**
- **Pros:** Reproduces today's assignment from a stated rule. Family-preserving on every platform. The dynamic part is one sentence and uses existing gates. Break-even is derivable. Removes three inert constructs.
- **Cons:** Renaming tier values touches seven agent files, the manifest, the lint, and the docs (mechanical, one story). Cursor's floor needs a runtime check before it can be trusted. Escalation adds one re-spawn on the failure path.
- **Risk:** Low. Every path degrades to `anchor`, which is today's behavior.

### E. A third `execution` tier for tool-heavy bounded work
- **Pros:** Mirrors the Fable→Sonnet shape directly.
- **Cons:** No current agent fits it. A tier with no consumer is the condition that got the ordinals deprecated. Databricks shows mid-tier can cost more per task on open-ended coding.
- **Risk:** Low but premature. **Named as the first thing to revisit** if `escalated` signals show a floor agent near break-even — a middle tier is the natural response to a floor that is *almost* good enough.

## Decision Outcome

**Option D.** Driver 2 rejects B and C; driver 1 rejects A; driver 5 defers E until there is a number to act on.

**What is explicitly NOT decided:** any change to which agents are `anchor` or `floor` (none change); whether `coding-agent` could ever run at floor (it cannot under Q2 as written — revisit only with an `escalated`-signal record from a bounded coding role that does not exist yet); command consolidation; anything in ADR-022's gate classes.

## Worked Example — This Decision, Triaged (ADR-023)

*Should Writ rename `capability` to `floor`?* Does the answer change what happens — yes, every reader of every agent file. How bad if wrong — trivial: seven files, one alias line in lint, fully revertible. → **Decide, act, record.** Ruled: rename. That is the whole analysis it warranted.

*Should Writ ship a per-spawn router?* Does the answer change what happens — yes, every spawn. How bad if wrong — wide: silent quality loss across the pipeline, and the research says routers often lose. → **Full rigor**, which the research doc supplied, and which rejected it.

## Consequences

**Positive**

- A new reader gets the model in one sentence and can check every agent's tier against two questions.
- Delegation becomes *dynamic* in the only way the evidence supports — provisional cheap results, confirmed or escalated by gates that already exist.
- Writ maintains no model names for Cursor or Claude Code beyond the platforms' own family aliases; Codex and OpenClaw keep one row each.
- The Cursor floor stops being an untested assumption.
- The ordinal deprecation finally has a forward record, and ADR-016's dangling trigger is closed.

**Negative**

- **A vocabulary migration.** Seven agents, the manifest, `lint-skill.sh`, `.writ/docs/model-tiers.md`, `system-instructions.md` and its mirror, four adapters. *Mitigation:* aliases accepted for one release; the whole change is mechanical and lands in one story.
- **Escalation costs a second spawn on the failure path.** *Mitigation:* the break-even arithmetic above; and only two agents are floor today.
- **`floor` on Cursor may resolve to `inherit` for a while** if neither bracket form nor prefix-match is honored. *Mitigation:* that is today's probable behavior anyway, now visible via a `degraded` signal instead of silent.
- **Cost per task is not measurable from inside the harness** — no platform reports token counts to the agent. *Mitigation:* Writ measures the *outcome* that governs the bet (escalation rate) instead of the cost itself, and says so.

## Implementation Plan

Single spec, four stories, no new tooling beyond one adapter verification. **Prerequisite:** none; ADR-025 Story 1 makes the `escalated` signal recordable but Story 4 below may land first with the signal call as a no-op.

| # | Story | Files | Done when |
|---|---|---|---|
| 0 | **Verify the Cursor floor** (not a story — a 30-minute check that gates Story 3's table) | none | One real spawn each of `model: "fast"`, `inherit[effort=low]`, and a same-prefix concrete ID; the resolved model observed and recorded in the spec |
| 1 | **Contract** — rewrite § Model Tiers in `system-instructions.md` and byte-identical `cursor/writ.mdc`: two questions, `anchor`/`floor`, family rule, escalation rule, degradation; drop the advisory carrier prose. Rewrite `.writ/docs/model-tiers.md` to match. `scripts/lint-skill.sh` accepts `^(anchor\|floor)$` and warns on `orchestration`/`capability`. | `system-instructions.md`, `cursor/writ.mdc`, `.writ/docs/model-tiers.md`, `scripts/lint-skill.sh` | `bash scripts/eval.sh` Findings: 0; `prime-directive-sync` and manual mirror diff clean |
| 2 | **Agents & manifest** — seven `model_tier` values renamed; `model: "fast"` removed from the two `Task({...})` templates in favor of the adapter-resolved value; `.writ/manifest.yaml` mirrored; the two advisory `model_tier` lines removed from command frontmatter. | `agents/*.md`, `.writ/manifest.yaml`, 2 files under `commands/` | `rg "model_tier:" agents/` → 7 hits, all `anchor` or `floor`; `rg "model_tier" commands/ skills/` → 0 |
| 3 | **Adapters** — four resolution tables in the shape above; Cursor's `"fast"` replaced by Story 0's verified value; Claude Code nesting note corrected. | `adapters/cursor.md`, `adapters/claude-code.md`, `adapters/codex.md`, `adapters/openclaw.md` | Each adapter states `anchor`, `floor`, escalation, and degradation in one table |
| 4 | **Escalation** — `/create-spec` Step 2.6 regenerates a structurally invalid story at anchor once before reporting; `/implement-story` Gate 0 confirms an ABORT at anchor before the AskQuestion; both emit `escalated` (ADR-025). `loop.max_iterations` prose states the pair counts once. | `commands/create-spec.md`, `commands/implement-story.md` | `require_literal` pins in `eval.sh` for both sites; one real `/create-spec` run with a forced-invalid story shows the anchor retry |

**Success criteria**

- Every agent's tier is derivable from the two questions by a reader who has not seen the assignment — checked by having the spec's reviewer derive all seven blind.
- No Writ-maintained model name exists outside the Codex and OpenClaw adapter rows.
- After Story 3, the Cursor floor resolves to something other than the anchor, or a `degraded` signal says why not.
- ADR-016 shows `Superseded` with a link here; the roadmap parking lot carries the spec as a candidate.

**Review date: 2026-12-02** (90 days). The review reads `escalated` counts per floor agent from ADR-025's ledger. A floor agent whose escalation rate approaches the break-even (`1 − f/a`, roughly 0.8 at a five-to-one price gap) is moved to `anchor`; a floor agent that never escalates is left alone; a floor agent in between is the trigger to reopen Option E. If the ledger is empty because ADR-025 did not ship, the review question is why not.

## Amendments

**2026-09-03 — recorded during `/create-spec` for this ADR, at the maintainer's direction.** Three clarifications that the contract discussion showed the Decision left implicit. None changes an agent's tier; the Implementation Plan gains one story (entry-level check) and the spec is five stories, not four.

**A1. The anchor is the origin, and Writ knows it.** "The user's session model" was carried only implicitly, through the platform's `inherit`. That is sufficient for `anchor` and for escalation, but two paths need Writ to *know* the origin rather than inherit it: family-locking the floor (Decision 3a requires the family), and not stepping below where the user already is. So: at command entry, the commands that spawn agents capture the **origin** as the harness reveals it — `anchor.model` (name or `unknown`), `anchor.effort` (`low|medium|high|…` or `unknown`), `anchor.platform` — by *reading*, never by asking. The origin is stamped on every spawn decision and on every `escalated`/`degraded` line, which is what makes those lines legible. Per-platform origin sources belong in the adapter tables. Known limit: Claude Code reveals the model but not reliably the session effort; `anchor.effort` will usually be `unknown` there, and the effort path uses `low` absolute.

**A2. The anchor is the ceiling.** No spawn resolves above `anchor.model` or above `anchor.effort`. Escalation returns *to* the anchor, never past it — the user's choice of model and thinking level is a cost decision Writ does not override. Decision 3 is read with this constraint: the floor is the cheapest same-family configuration **at or below the origin**; when the origin already sits at the family floor, `floor` collapses to `anchor`, the run says so once, and that is correct behavior — not degradation.

**A3. Commands carry `entry_level`, not `model_tier` — Decision 5 revised.** If Writ can only step down from the entry point, the one useful thing a command can do about its own weight is tell the user when they have entered below what it needs. Every command therefore declares `entry_level: high | standard | any` in its existing frontmatter — the same carrier the advisory `model_tier` occupied, with a different meaning: not *what this command runs at* (Writ cannot choose) but *what it expects the user to have chosen*. The value is derived by two questions in Decision 2's shape: **Q1** — does the command spawn agents, lock a contract, or make a judgment the user acts on without a later gate? → `high`. **Q2** — does it create or modify artifacts? → `standard`. Otherwise → `any`. At entry the command compares the captured origin against its level and, if below, prints **one line and continues** — never a question, once per session — because the answer only changes what happens if the user restarts, which is the user's call. Writ maintains no model ranking to make that comparison: the running model self-assesses against plain guidance (`high` expects a frontier-class model of its family at a non-minimal thinking level; `standard` a non-smallest model or medium-plus effort; `any` nothing). Skills carry nothing, as before. The maintainer's example ordered `/implement-spec` above `/implement-story`; the rule places both at `high` and this ADR declines a finer ordering — `/implement-story` adjudicates five gates and there is no evidence for ranking the two, which ADR-023 forbids inventing.

## Dissent and Corrections

- **The request asked for `n-1, n-2`. This ADR does not deliver it**, and says so rather than relabeling the escalation rule as a ladder. The maintainer's stated intent — cheaper, same-family delegation — is delivered; the depth mechanism is refused on Writer's and COPE's evidence. If the maintainer, having read that evidence, still wants depth-relative stepping, that is a reversal this ADR records as a decision made against the evidence, not a discovery.
- **Two floor agents is a small footprint for a delegation ADR.** True. The savings ceiling under this ADR is bounded by how much bounded, checked work Writ's pipeline contains — and today that is story generation and the architecture pre-check. The honest expansion path is not lowering the bar in Q2 but adding bounded roles (a WWB formatter, a drift-log writer, a changelog drafter) that would qualify. None is decided here.
- **The author of this ADR recommended against reopening delegation in the research doc's Option B**, then wrote this ADR at the maintainer's request. The position did not reverse: Option B was the depth ladder, which is still rejected; this ADR is the research doc's Option A with the dynamic rule made explicit.

## References

- [ADR-016](adr-016-model-tier-delegation.md) — superseded; the agent-as-carrier boundary and degradation contract originate there and are kept
- [ADR-009](adr-009-command-agent-skill-boundary.md) — why only agents are spawn points
- [ADR-023](adr-023-stakes-proportional-diligence.md) — the two-question triage shape reused in Decision 2
- [ADR-025](adr-025-friction-signals.md) — the `escalated` and `degraded` signals this ADR's review depends on
- [`2026-09-03-family-relative-model-routing-research.md`](../research/2026-09-03-family-relative-model-routing-research.md) — platform primitives, cost evidence, and the option analysis this ADR closes
- `.writ/specs/archive/2026-08-11-retire-dead-prescription/spec.md` §(e), Business Rules 3, 6, 8 — the ordinal deprecation and its re-entry condition
- Cursor subagents: https://cursor.com/docs/agent/subagents · Claude Code subagents: https://code.claude.com/docs/en/sub-agents · Codex subagents: https://developers.openai.com/codex/subagents
- Arize, "How cheap models changed multi-agent economics" (Aug 2026): https://arize.com/blog/how-cheap-models-changed-multi-agent-economics/
