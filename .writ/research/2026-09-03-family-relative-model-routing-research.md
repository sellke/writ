# Family-Relative Model Routing — Stepping Delegated Work Down Within the Orchestrator's Model Family

> Created: 2026-09-03
> Status: Complete
> Depth: Standard 4-phase (moderate stakes, reversible — a convention change, not a platform bet)
> Method: Repository archaeology of Writ's existing `model_tier` contract and its 2026-08-11 ordinal deprecation; primary-source reads of the Cursor, Claude Code, and Codex CLI subagent docs as of today; survey of the routing/cascade literature and the July–August 2026 orchestrator-executor cost evidence.
> Scope boundary: This document recommends; it changes no command, agent, adapter, or root-contract file. Any change it motivates goes through `/create-spec` or `/create-adr`.
> Follow-up (2026-09-03): the primary recommendation (Option A) was decided as [ADR-024](../decision-records/adr-024-model-delegation.md), which supersedes ADR-016 and makes the escalate-on-failure rule explicit; the instrumentation step (Recommendation 4) became the `escalated`/`degraded` signals in [ADR-025](../decision-records/adr-025-friction-signals.md).

## Research Questions

1. **Can an orchestrating model delegate to a strictly weaker model in its own family (`n-1`, `n-2`) on each platform Writ supports today — and what primitive expresses that?** (Cursor, Claude Code, Codex CLI; OpenClaw noted where evidence exists.)
2. **Is "step down one tier per delegation level" the right routing axis, or does the evidence point somewhere else?** Writ nests four deep (`/implement-phase` → spec-runner → `/implement-story` → gate agents); the question is whether depth predicts task complexity.
3. **What does Writ already have, what did it deliberately retire, and what is the honest gap** between the current 2-band `model_tier` and the request?
4. **What is the cheapest change that captures most of the token savings without regressing quality** — and what evidence would justify anything more?

## Executive Summary

**The request is sound in intent and partly wrong in shape.** Writ already enforces a 2-band `model_tier` (`orchestration` / `capability`) at the only place it can — the agent spawn boundary (ADR-016). The finer `n-1` / `n-2` ordinal ladder you are describing was declared in that same ADR as a reserved form and then **deprecated on 2026-08-11** (`retire-dead-prescription`, Story 2) for having zero consumers and no adapter ever resolving it. Its Business Rule 6 is explicit: reopening requires a real consumer, not an argument that offsets are harmless. This document is that argument's replacement — evidence for what *should* be built instead.

**Depth is the wrong axis; role is the right one, and family is the missing constraint.** Every credible 2026 data point says the same thing: cheap executors work only under a strong orchestrator. Anthropic's Fable 5 → Sonnet 5 team kept 96% of an all-Fable score at 46% of the cost; Writer Inc. found delegation collapsed from ~0.85 to ~0.45 when the *orchestrator* dropped to the fast tier; COPE found larger planners lift smaller executors. In Writ's nesting, the spec-runner and `/implement-story` layers are orchestrators — they decompose, route context, and judge gate verdicts — so a depth-relative `n-1` at each level would degrade exactly the layer the evidence says must stay strong. The current role-based assignment (five judgment agents at anchor, two mechanical fan-out agents at floor) is already the evidence-backed shape. What it lacks is (a) a **family-lock** — `capability` today resolves to a vendor-agnostic cheap model, not "the anchor's own smaller sibling," and (b) a **reasoning-effort axis**, which every platform exposes and which is the only step-down that is family-preserving by construction.

**Recommendation: keep two role-based bands, add a same-family resolution rule and an `effort` lever to `capability`, fix three stale platform claims the archaeology surfaced, and instrument spawns before adding any middle band.** Cursor's adapter maps `capability → "fast"`, but Cursor's own subagent docs list only `inherit` or a concrete model ID as legal `model` values, and the Task tool in this session exposes no `fast` slug — so the floor tier may already be silently degrading to `inherit`. Claude Code's adapter says subagents cannot nest; they now nest three deep. ADR-016 still describes the ordinal reservation with a 2026-10-16 review trigger that a later spec already resolved. None of these are the requested feature, but all three are cheaper than it and one of them may be costing tokens today.

## Key Findings

### Finding 1 — Writ's contract already encodes the evidence-correct split; the ladder you want was retired for lack of a consumer

| Artifact | What it says today | Source |
|---|---|---|
| ADR-016 (2026-07-10) | Two tiers, agent-as-carrier, relative-not-absolute; reserved `-1/-2` ordinal form "not built yet," review trigger 2026-10-16 | `.writ/decision-records/adr-016-model-tier-delegation.md` |
| `retire-dead-prescription` Story 2 (2026-08-11) | Ordinal offsets **deprecated now**: "zero consumers plus an unbuilt N-step resolver"; a `-1` written tomorrow is an unknown value → warn → inherit | `.writ/specs/archive/2026-08-11-retire-dead-prescription/spec.md` §(e), Business Rule 6 |
| Active surface | Schema is `^(orchestration\|capability)$`; no ordinal branch in `system-instructions.md`, `cursor/writ.mdc`, `.writ/docs/model-tiers.md`, `lint-skill.sh`, or the manifest | `system-instructions.md` § Model Tiers |
| Agent assignment | `architecture-check-agent`, `user-story-generator` → `capability`; `coding`, `review`, `testing`, `documentation`, `visual-qa` → `orchestration` | `agents/*.md`, `.writ/manifest.yaml:189-220` |
| Originally excluded and never built | per-platform family ranking, N-step resolution, anchor-model detection, quality-regression eval harness, auto-downgrade heuristics | model-tier spec § Out of Scope |

**Implication:** the request is not greenfield. It re-raises a decision Writ made 23 days ago with a stated re-entry condition. The rest of this document is written to meet that condition honestly — by naming a consumer (Finding 5) and by showing that the *shape* of the consumer differs from the ordinal ladder that was retired.

**Doc-consistency gap (verified):** ADR-016 is preserved as history per Business Rule 3 and correctly not rewritten, but no forward-recorded decision (ADR or amendment) states that the reservation was resolved. The `retire-dead-prescription` spec left this as "a maintainer call outside this spec's file set." A reader landing on ADR-016 today sees a live 2026-10-16 trigger that no longer exists.

### Finding 2 — Every platform exposes per-spawn model selection; only Claude Code exposes a family-native ladder

| Capability | Cursor | Claude Code | Codex CLI |
|---|---|---|---|
| Per-subagent `model` | Frontmatter or Task param: `inherit` or a **concrete ID** (`gpt-5.6-sol`, `composer-2`); brackets for options: `claude-opus-5[effort=high]`, `composer-2.5[fast=false]` | Frontmatter or Agent-tool param: **family aliases** `haiku` / `sonnet` / `opus` / `fable`, a full ID, or `inherit` | Agent TOML: `model`, `model_reasoning_effort`; `[agents].default_subagent_model` |
| Relative "cheap" primitive | None documented as a `model` value. `fast=` is a *variant flag on a concrete ID*, not a model. Built-in Explore subagent "uses a faster model by default" | None — aliases are absolute within the family; `CLAUDE_CODE_SUBAGENT_MODEL` sets a session-wide default | **Yes, natively**: if `model` / effort are unpinned, "Codex can choose a setup that balances intelligence, speed, and price for the task" |
| Reasoning-effort axis | `[effort=…]` bracket on the ID | `effort:` frontmatter (`low`…`max`), inherits session effort | `model_reasoning_effort` (`low` / `medium` / `high` / `xhigh`) |
| Resolution order | Frontmatter honored unless admin/plan blocks → "falls back to a compatible model" | Per-invocation param → frontmatter → `CLAUDE_CODE_SUBAGENT_MODEL` → session model (v2.1.251+) | Agent file → explicit spawn value → `[agents]` default → parent |
| Cap semantics | — | Built-in Explore **inherits, capped at Opus** — "never runs on a more expensive model than the one you already chose" | — |
| Nesting | Nested launches allowed if Task tool available in mode | **Up to three layers below main** (`adapters/claude-code.md` § Known Limitations item 5 is stale) | Multi-agent v2; `hide_spawn_agent_metadata=true` by default hides `model`/`reasoning_effort` from the spawn schema |
| Family lock | Requires knowing the anchor and prefix-matching IDs (`claude-*`, `gpt-*`, `composer-*`, `cursor-grok-*`) | Native — aliases are one family | Trivial — single vendor |

Sources: [Cursor subagents](https://cursor.com/docs/agent/subagents), [Claude Code subagents](https://code.claude.com/docs/en/sub-agents), [Codex subagents](https://developers.openai.com/codex/subagents), [Codex multi-agent v2 routing](https://codex.danielvaughan.com/2026/07/24/codex-cli-sub-agent-model-routing-multi-agent-v2-hidden-schema-cost-control-configuration/).

**Implications:**

- **Writ's Cursor floor may be dead code.** `agents/architecture-check-agent.md:48` and `user-story-generator.md:56` pass `model: "fast"` in their `Task({...})` templates, and `adapters/cursor.md:160` documents `capability → "fast"`. Cursor's current docs do not list `fast` as a `model` value; `fast` appears only as a bracket option on a concrete ID. If Cursor treats an unknown value as "fall back to a compatible model," the graceful-degradation path is firing on every `capability` spawn and both floor-tier agents run at the anchor. **Confidence: medium** — inferred from documentation; not observed at runtime. Verifying it is a five-minute check and is the first action in the recommendations.
- **The "one step down" primitive does not exist anywhere as a `model` value.** Every platform requires either an absolute pick or `inherit`. A family-relative step therefore needs one of: (i) the orchestrator knowing its own model (Cursor's harness names it in the system prompt; Claude Code exposes `/model`), (ii) a family alias ladder (Claude Code only), or (iii) delegating the choice to the platform (Codex unpinned). Writ's "delegate mechanics, own contracts" posture (ADR-016 Alternative C) points at (ii) and (iii) where available and a narrow, runtime-read rule for (i) on Cursor — not a maintained ranking.
- **Effort is the family-preserving step-down.** `inherit` + lower effort keeps the vendor, the tokenizer, the tool-calling conventions, and the context window (Claude Code: "a subagent's context window is sized by its own model, not the parent's" — a real risk when swapping to a smaller sibling), while cutting reasoning tokens. It is available on all three platforms.

### Finding 3 — The evidence favors role-based orchestrator/executor over depth-based step-down

| Evidence | Finding | Bearing on Writ |
|---|---|---|
| Anthropic, via Arize (Aug 2026) | Fable 5 orchestrator + Sonnet 5 workers: **96% of all-Fable BrowseComp score at 46% cost** | Same-family step-down works for bounded executor roles |
| Writer Inc. (Jul 2026, 22 enterprise tasks, 6 models, 2 orchestration layers) | Delegation reliable only on the two strongest models (~0.85); **fell to ~0.45 on the fast tier** | Orchestrator layers must not step down — this kills depth-relative `n-1` |
| COPE (2025 planner-executor study) | Larger planners improve smaller executors | Same conclusion, academic form |
| Databricks merged-PR benchmark (via Arize) | Sonnet 5 is 1.7× cheaper per token than Opus 4.8 but **cost more per task** ($2.09 vs $1.94) because it consumed 1.9× the tokens | "Lesser model" ≠ cheaper for open-ended coding; `coding-agent` at anchor is correct |
| LLMRouterBench (ACL 2026 Findings, via Arize) | Several routers incl. OpenRouter's "fail to reliably beat simply using the single best model" | Do not build a per-spawn complexity classifier |
| Routing/cascade survey (arXiv 2603.04445) | Quality estimation is "the critical factor for model selection success"; cascades work when a verifier decides escalation | Writ's gates *are* verifiers — cheap generator + strong reviewer is the cascade shape Writ already has |
| Practitioner reports (byteiota, MindStudio) | ~25–35k tokens per subagent just to initialize; over-fragmentation erases savings; 60% spend cuts reported from two frontmatter fields | Fan-out count matters as much as model choice; Writ's own measured base is ~19.4k tokens per invocation |

Sources: [Arize — How cheap models changed multi-agent economics](https://arize.com/blog/how-cheap-models-changed-multi-agent-economics/), [Dynamic Model Routing and Cascading survey](https://arxiv.org/html/2603.04445v2), [RouteLLM](https://github.com/lm-sys/RouteLLM), [RouteNLP](https://arxiv.org/html/2604.23577), [byteiota — Claude Code subagent model routing](https://byteiota.com/claude-code-subagent-model-routing/), [MindStudio — smart orchestrator, cheaper subagents](https://www.mindstudio.ai/blog/smart-orchestrator-cheaper-sub-agent-models-claude-code).

**Implication for the `n-1, n-2` framing.** In Writ's four-level nest, levels 1–3 are orchestrators (they spawn, route context, and adjudicate) and only level 4 holds leaf executors. A per-level ordinal would put `/implement-story` at `n-2` — precisely the "fast tier orchestrator" Writer measured at 0.45. The savings you want live almost entirely at level 4, and mostly in the two agents already at the floor plus whichever *new* mechanical roles get added. Vendor-reported numbers dominate this evidence base (Arize says so itself); the direction is consistent across independent sources, the magnitudes are not to be trusted for Writ's workload without measurement.

### Finding 4 — "Within the family" is a real constraint Writ does not express, and it matters for more than cost

Nothing in `model_tier` says "same vendor as the anchor." On Cursor, a Claude-anchored session with `capability → "fast"` (if it ever resolved) could hand story generation to a Composer or Grok variant. Three concrete reasons to lock the family:

1. **Prompt-format fidelity.** Writ's agent prompts are long, structured, and tuned in-session by the anchor. Cross-vendor handoff changes tool-call conventions and instruction-following idioms mid-pipeline; same-family siblings share them.
2. **Context window continuity.** Claude Code documents that the subagent's window is sized by *its* model. A cross-family cheap model with a smaller window truncates the `spec_lite_*` payloads `/implement-story` routes to each gate.
3. **Auditability.** ADR-017's git-notes audit channel records decisions; a spawn that lands on an unexpected vendor is a cost *and* a provenance surprise. Family-lock makes the resolved model predictable from the anchor alone.

Where the platforms stand: Codex is single-family by construction; Claude Code's aliases are single-family; Cursor is the only platform where the lock has to be *computed* (vendor prefix of the anchor ID → lowest-cost ID with the same prefix from the runtime slug list, else `inherit`). OpenClaw depends on the operator's configured model set — unverified in this research.

### Finding 5 — There is a consumer now, and it is not an ordinal

Business Rule 6 asked for "a real consumer." Three candidates surfaced during this research, in descending strength:

1. **The two floor-tier agents on Cursor** — if Finding 2's inference holds, they are the consumer of a *working* `capability` resolution and currently have none. Fixing the resolution is a prerequisite for any finer routing and is worth doing on its own.
2. **A same-family `effort` step-down for `capability`** — `inherit[effort=low]` (Cursor), `effort: low` (Claude Code), `model_reasoning_effort = "low"` (Codex). This is the only `n-1` that is family-preserving on every platform and needs no ranking. It has no consumer today only because the contract cannot express it.
3. **A middle `execution` band** (orchestration / execution / capability) for tool-heavy bounded work — the Sonnet-under-Fable role Anthropic measured. Plausible, but Writ has no agent that fits it today: `coding-agent` is open-ended (and Databricks shows a mid-tier model can cost *more* per task there), and the current floor agents are mechanical. **Defer until an agent needs it.**

## Options Analysis

### Option A — Keep 2 bands; add family-lock + effort axis to `capability`; repair stale platform claims (recommended)

- **Shape:** `capability` resolves to "the anchor family's lowest tier, or the anchor at reduced effort where no smaller sibling is exposed." Per adapter: Claude Code `haiku` (unchanged) or `inherit` + `effort: low`; Codex `gpt-5.6-terra`-class or unpinned + `model_reasoning_effort = "low"`; Cursor prefix-match against the runtime slug list, else `inherit[effort=low]` if brackets accept `inherit` (unverified), else `inherit`. Contract adds one optional field (e.g. `effort_floor`) or folds effort into the `capability` resolution rule — a `/create-spec` decision.
- **Pros:** Family-preserving by construction on every platform. No maintained ranking. Fixes a probable live regression on Cursor. Zero change to the role assignment the evidence supports. Compatible with ADR-016's alternatives analysis.
- **Cons:** Cursor's family rule needs the anchor identity; the cleanest source (harness system prompt) is not a Writ-controlled contract. Effort semantics differ subtly per platform.
- **Effort:** S–M. **Risk:** Low; every change degrades to `inherit`.

### Option B — Rebuild the N-step ordinal ladder, depth-relative (`n-1` per nesting level)

- **Pros:** Matches the request literally; reserved grammar already existed.
- **Cons:** Contradicted by Writer/COPE — steps orchestrator layers down. Requires the per-platform ranking ADR-016 rejected. Re-deprecates a 23-day-old decision without meeting its stated re-entry condition. Adds a decision point per spawn against ADR-023's stakes-proportional posture.
- **Effort:** M–L. **Risk:** Medium-high (quality regression at orchestration layers).

### Option C — Dynamic complexity router in the orchestrator

- **Pros:** In principle routes every spawn optimally.
- **Cons:** LLMRouterBench: routers frequently fail to beat single-best; requires per-workload calibration Writ cannot ship; makes every spawn a judgment call. Writ's gates already provide the verifier half of a cascade — the generator side is the only lever, and Option A pulls it.
- **Effort:** L. **Risk:** High.

### Option D — Delegate entirely to platform-native routing

- **Shape:** Codex unpinned (platform picks); Claude Code `opusplan`-style hybrids or `CLAUDE_CODE_SUBAGENT_MODEL`; Cursor built-in Explore's fast default.
- **Pros:** Purest "delegate mechanics." Zero Writ maintenance.
- **Cons:** Uneven — Codex has it, Claude Code only session-wide, Cursor only for built-ins. Removes Writ's ability to *state* role intent portably, which is the whole point of `model_tier`.
- **Effort:** XS. **Risk:** Low but forfeits control. Reasonable as the *fallback* inside Option A where a platform offers it.

### Option E — Add a third `execution` band now

- **Pros:** Matches the Fable→Sonnet shape directly; small schema change.
- **Cons:** No current agent fits it; Databricks evidence says mid-tier can cost more per task for open-ended coding. Would be a band with no consumer — the exact condition that got the ordinals deprecated.
- **Effort:** S. **Risk:** Low, but premature.

## Recommendations

**Primary: Option A, sequenced so the cheapest, highest-certainty fixes land first and gate the rest.**

1. **Verify the Cursor floor (30 minutes, no spec needed).** Spawn `user-story-generator` with `model: "fast"` and observe the resolved model; then try a concrete same-family cheap ID and `inherit[effort=low]`. This converts Finding 2's medium-confidence inference into a fact and tells you whether Cursor accepts brackets on `inherit`.
2. **Record the ordinal resolution forward.** A short ADR (or an "Amended by" note on ADR-016 if the maintainer prefers) stating the reservation was deprecated 2026-08-11 and why, so the live-looking 2026-10-16 trigger stops misleading readers. Pure hygiene; `/create-adr`.
3. **Spec the family-lock + effort rule** (`/create-spec`). Deliverables: contract prose in `system-instructions.md` and mirror; three adapter tables rewritten around "same family, lowest tier, else anchor at low effort, else inherit"; `agents/*.md` `Task({...})` templates updated from `"fast"` to whatever step 1 proves resolvable; `lint-skill.sh` accepting any new field; `adapters/claude-code.md` nesting note corrected while the file is open. This spec is the "real consumer" Business Rule 6 asked for.
4. **Instrument before widening.** Record the resolved model and token count per gate spawn into the ADR-017 audit channel (`/implement-story` already emits per-gate records). After ~10 stories, you have Writ's own cost-per-task table. Only then decide on Option E's middle band — the model-tier spec's excluded "quality-regression eval harness" becomes a measured artifact instead of a promise.

**If the primary is infeasible:** Option D on Codex immediately (unpin the two floor agents and let Codex choose), Claude Code aliases as-is, Cursor `inherit` — and accept that Cursor has no working floor until step 1 is done.

**What this does not do, deliberately:** it does not give you `n-2`. The evidence says a second step down belongs on effort, not on a third model, and not at any orchestrator layer.

## Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Cursor rejects `[effort=…]` on `inherit`, leaving no family-preserving step-down there | Medium | Medium | Step 1 tests it first; fallback is prefix-match on the runtime slug list, then `inherit` |
| Anchor identity on Cursor read from the harness prompt drifts or is absent | Medium | Low | Rule degrades to `inherit`; never a hard failure (existing contract) |
| Same-family cheap model has a smaller context window and truncates `spec_lite_*` payloads | Low–Medium | High for review/coding, low for story-gen | Family-lock keeps floor agents mechanical; documentation agent stays at anchor; record window size in the audit note |
| Effort step-down degrades `architecture-check-agent` verdicts (it is a judgment role at the floor) | Medium | Medium | It is read-only and its ABORT path asks the user; measure via step 4 before lowering effort on it specifically |
| Re-litigating a 23-day-old deprecation looks like reversal under pressure | Low | Medium | This document names a consumer and changes the shape (role + family + effort, not depth ordinals); Business Rule 6 is met, not overridden |
| Vendor-reported savings (96%/46%) do not transfer to Writ's workload | High | Low | Step 4 replaces external numbers with Writ's own before any further band is added |

## Further Research

- **Does Cursor accept model parameters on `inherit`?** Unanswered by the docs; decisive for whether the effort lever is portable to Cursor. A single spawn answers it.
- **OpenClaw's model set and effort exposure.** Not investigated; `adapters/openclaw.md` documents a `model` param on `sessions_spawn` but this research did not verify current OpenClaw primitives.
- **Writ's own cost-per-task by gate.** No measurement exists. The model-tier spec excluded the eval harness on a `convention_only` posture; Finding 3 shows external numbers cannot substitute.
- **Whether the spec-runner layer (level 2) ever benefits from effort reduction.** It is an orchestrator by the evidence's definition, so this document assumes no — but it is the one layer whose work is mostly bookkeeping between `/implement-story` calls, and it is worth one measured trial.
- **Anthropic's original BrowseComp numbers.** Cited here via Arize; the primary post was not fetched. Treat 96%/46% as reported, not verified.

## Sources

**Writ repository (verified at v0.33.0, commit `5b9082d`)**
- `.writ/decision-records/adr-016-model-tier-delegation.md` — tiers, agent-as-carrier, reserved ordinals, 2026-10-16 trigger
- `.writ/specs/archive/2026-08-11-retire-dead-prescription/spec.md` — §(e) ordinal deprecation; Business Rules 3, 6, 8; Out of Scope "Rewriting ADR-016"
- `.writ/specs/archive/2026-07-10-model-tier-delegation/` — original spec, Out of Scope list, `convention_only` posture
- `system-instructions.md` § Model Tiers; `.writ/docs/model-tiers.md`; `.writ/manifest.yaml:189-220`
- `adapters/cursor.md:155-167` (`capability → "fast"`); `adapters/claude-code.md:122-141, 527`; `adapters/codex.md:149-165`
- `agents/architecture-check-agent.md:46-49`, `agents/user-story-generator.md:54-57` — `Task({ model: "fast" })` templates
- `commands/implement-story.md` § Step 3 — gate structure, sub-agent spawn sites
- `.writ/research/2026-08-03-writ-vs-openspec-analysis.md` § 3 — prior framing of Writ's routing contract
- `CHANGELOG.md:194` — release note recording the ordinal deprecation

**Platform documentation (fetched 2026-09-03)**
- Cursor — Subagents: https://cursor.com/docs/agent/subagents (model field, bracket parameters, fallback conditions, nesting)
- Claude Code — Subagents: https://code.claude.com/docs/en/sub-agents (aliases, resolution order, `effort`, Explore cap, three-layer nesting, context window sizing, fallback chain)
- Claude Code — Workflows: https://code.claude.com/docs/en/workflows (per-stage model selection order, `availableModels` substitution)
- OpenAI Codex — Subagents: https://developers.openai.com/codex/subagents (unpinned auto-selection, `model_reasoning_effort`, `[agents]` defaults, precedence)
- Codex multi-agent v2 model routing: https://codex.danielvaughan.com/2026/07/24/codex-cli-sub-agent-model-routing-multi-agent-v2-hidden-schema-cost-control-configuration/
- Codex custom agent TOML reference: https://codex.danielvaughan.com/2026/04/27/codex-cli-custom-agent-definitions-toml-specialised-subagents/
- OpenAI community — restoring subagent model/reasoning in multi_agent_v2: https://community.openai.com/t/restoring-subagent-roles-model-and-reasoning-in-multi-agent-v2/1386513

**Evidence on orchestrator-executor economics and routing**
- Arize AI — "How cheap models changed multi-agent economics" (Aug 2026; cites Anthropic BrowseComp, Writer Inc., COPE, Databricks, LLMRouterBench, MinionS): https://arize.com/blog/how-cheap-models-changed-multi-agent-economics/
- Dynamic Model Routing and Cascading for Efficient LLM Inference: A Survey (arXiv 2603.04445): https://arxiv.org/html/2603.04445v2
- RouteLLM (lm-sys): https://github.com/lm-sys/RouteLLM
- RouteNLP: Closed-Loop LLM Routing with Conformal Cascading (arXiv 2604.23577): https://arxiv.org/html/2604.23577
- LeanLM — LLM model routing overview (FrugalGPT / RouteLLM summary): https://leanlm.ai/blog/llm-model-routing
- byteiota — Claude Code sub-agent model routing (init overhead, 60% reports, `opusplan`): https://byteiota.com/claude-code-subagent-model-routing/
- MindStudio — Smart orchestrator, cheaper sub-agents in Claude Code: https://www.mindstudio.ai/blog/smart-orchestrator-cheaper-sub-agent-models-claude-code
- ClaudeWorld — The Claude 5 family and model strategy (alias ladder, per-stage tiering): https://claude-world.com/tutorials/s25-the-claude-5-family-and-model-strategy/

**Session observation (not a durable source)**
- The Cursor Task tool available in the authoring session listed `inherit` plus seven concrete slugs (`claude-fable-5-1-thinking-high`, `claude-opus-5-thinking-high`, `composer-2.5-fast`, `cursor-grok-4.5-high-fast`, `cursor-grok-4.6-medium-fast`, `gpt-5.6-sol-medium`) and no `fast` value. Slug lists change; this is recorded as the observation that prompted Finding 2's inference, not as evidence in itself.
