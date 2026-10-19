# Multiple Visual Drafts Before Spec: Reframing `/prototype` as Exploration

**Date:** 2026-10-19
**Status:** Complete — **revised 2026-10-19 after maintainer review (see Revision below)**
**Trigger:** "How might we make `/prototype` more robust at creating multiple looks (visual mock-ups) and drafts of an idea or a concept *before* we engage in full specification and implementation."
**Depth:** Standard 4-phase. Moderate stakes, reversible — this is a surface-placement decision inside an existing pipeline, not an architecture commitment.
**Writ version:** 0.41.0, docs branch off v0.41.0

---

## Revision — 2026-10-19

**The first draft recommended against hosting exploration in `/prototype`. That conclusion was wrong and is withdrawn.**

The original F1 argued from `/prototype`'s frontmatter — `outcome` says "the repository gained no planning artifact describing it," the terminal constraint forbids spec artifacts — to the conclusion that exploration does not belong there. That is circular. A contract line is a decision someone made and can amend; it is not evidence about where a capability belongs. The draft treated an amendable sentence as a boundary.

The maintainer's position, adopted here: **`/prototype` should be reframed as the early, preliminary exploration workflow** — one that invokes design and other skills to produce a broad but genuinely real sense of the end in mind, and stops before deep specification or planning. Three things support it that the first draft under-weighted:

1. `/prototype`'s own *When to Use* table already reads "Exploring an approach before committing to it | `/prototype` (then escalate if it works out)." The exploration intent is already declared; the implementation does not deliver it.
2. It already has the escalation hatch (`/create-spec --from-prototype`) and already has a visual step. It is the pre-spec front door in position, just not in capability.
3. "End in mind" is a stronger ask than mockups. A rendered mockup shows a look; a rough running thing shows whether the idea survives contact with the codebase. The original recommendation (`/design --explore`) produced only pictures, and was the weaker product for it.

The reframe is also *leaner* than the first draft's proposal: it needs no new `/design` mode, because `/prototype` loads the divergence skill directly. One fewer surface.

**What survives unchanged:** F3, F4, F5 and F6. The divergence evidence is about how models generate alternatives and is independent of which command hosts them. F6's defects get more urgent under the reframe, not less, because a reframed `/prototype` leans harder on the visual step.

**What changed:** F1, F2, the options analysis, and the recommendations. Sections below are revised in place; the superseded reasoning is summarized here rather than preserved line by line. The one concern the reframe does not dissolve is carried forward as the first row of Risks & Mitigation: a command that both explores and ships needs a single `outcome`, and ADR-020 will not let that be fudged.

---

## Research Questions

1. Where exactly does Writ's current surface fail to produce multiple visual drafts before a spec is locked?
2. Is multi-variant exploration actually better than single-draft-and-iterate, and what is the evidence?
3. Does that evidence survive the switch from human designers to AI-generated variants?
4. What do 2026 harnesses provide natively, and what is left for a methodology layer to own?
5. Which Writ primitive should own this, and where do pre-spec artifacts live when no spec exists yet?

---

## Executive Summary

**Reframe `/prototype` as Writ's early exploration workflow, and give it an evidence-backed divergence skill rather than a variant generator.**

Writ has no pre-spec divergence step anywhere in its 32 commands. `/design` cannot provide one — every mode routes output into `.writ/specs/<spec-name>/mockups/`, so it structurally requires a spec that does not exist yet. `/prototype` is already positioned as the pre-spec front door: its own usage table names "exploring an approach before committing to it" as its job, it already has a visual step, and it already has an escalation hatch into `/create-spec --from-prototype`. What it lacks is the capability, and a contract that admits to it.

**The consequential finding is that the obvious implementation does not work, wherever it lives.** Dow et al. (2010) measured parallel prototyping beating serial prototyping, but both conditions built five prototypes — the variable was *withholding feedback until several alternatives exist*, not producing more artifacts. That benefit does not transfer to AI variants. Models fixate on their own early outputs, repeated samples from one prompt converge, and independently trained models converge on each other. A CHI 2024 experiment (N=60) found designers using an AI image generator produced *fewer* ideas with *less* variety and *lower* originality than the no-AI baseline, with fixation displaced from the brief onto the AI's outputs. Asking one agent for "a few options" yields three samples from one mode, not parallel prototyping.

Divergence has to be constructed: orthogonal axes declared before generation, independent contexts so drafts cannot anchor each other, chain-of-thought before rendering, and ordinary rather than genius personas. That combination is the one measured to beat human diversity — and it is precisely output a model does not produce unprompted, which is Writ's own test for justified surface.

**Division of labour:** Writ owns the brief and the decision record, including why each rejected draft lost. The platform owns rendering — Claude Code shipped a native `/design` producing artboards before code in August 2026, so building a generator would violate Design Principle 4. The reframe adds zero commands: one skill, one amended command contract.

Two verified defects should be fixed regardless: `/prototype` hard-codes a Cursor-only tool name that no adapter translates, and Writ's `/design` now collides with a native Claude Code command of the same name.

---

## Key Findings

### F1. `/prototype` is already the pre-spec front door in position, not in capability

`commands/prototype.md` *When to Use* table, last row before the spec options:

> | Exploring an approach before committing | `/prototype` (then escalate if it works out) |

The command already claims the job. What it delivers is narrower: Step 2.5 Visual Preview produces **one** canvas mockup, binary approve / adjust / skip, nothing retained — its own guardrail says "It gathers layout feedback before coding; it is not a design deliverable." And it runs *after* Context Scan has detected the stack, located target files, and decided which files to modify, so it steers a change already scoped rather than helping choose a direction.

The frontmatter contradicts the reframe as written:

- `outcome`: "…and **the repository gained no planning artifact describing it**."
- `exit_criteria[0]`: "no spec folder, story file, or task list was created under `.writ/specs/`"
- Terminal constraint: "Do not open a PR, **write spec artifacts**, or escalate to the story pipeline without an explicit yes."

**This is a contract to amend, not a reason to refuse.** The distinction the current text misses is between a *spec artifact* — spec folder, stories, task list — and an *exploration record*. `exit_criteria[0]` already draws that line correctly by naming `.writ/specs/` specifically; `outcome`'s broader "no planning artifact" is the sentence that needs rewriting. Retaining three rejected looks and the reason each lost is not a spec, and the pipeline it must not start is still `/implement-story`.

**Implication.** The work is a contract amendment plus a capability, not a relocation.

### F2. `/design` cannot serve pre-spec exploration, and should not be stretched to

`commands/design.md` `exit_criteria[0]` requires "the selected mode's artifacts are under `.writ/specs/<spec-name>/mockups/`", and all five modes route output into a spec folder. There is no path for "I have a concept, no spec, and want three takes on it."

Mode A also generates *states* — default, loading, empty, error, named `{component}-{state}.excalidraw` — which is state coverage of one design, not alternative designs. Writ has no divergence step anywhere.

The roadmap parking lot (`.writ/product/roadmap.md`, *Beyond Phase 12*) carries "**`/design` Mode A modernization** — Excalidraw hand-authoring is a 2024 technique; revisit with AI image mockups or native design tools via `/refresh-command`." That item is real and still worth doing, but it is about modernizing how `/design` renders wireframes *for a spec that exists*. It is not the pre-spec exploration gap.

**Implication.** `/design` keeps its post-spec job. Adding an `--explore` mode would give Writ two commands that both do pre-spec divergence, which is the duplication ADR-015 exists to prevent. The skill both could load is the shared part.

### F3. Parallel prototyping is real, and the mechanism is not "make more things"

Dow et al., "Parallel Prototyping Leads to Better Design Results, More Divergence, and Increased Self-Efficacy," *ACM TOCHI* 17(4), Article 18 (2010). Novice designers created graphic web advertisements; the manipulation was whether critique arrived after each prototype (serial) or only after several existed (parallel).

- **Effort was held constant.** Subjects in *both* conditions created five prototype ads, then a final ad. The variable was feedback timing, not volume.
- Parallel ads significantly outperformed serial ads on click-through data and expert ratings.
- Independent raters judged parallel prototypes more diverse.
- Parallel participants reported a larger increase in task-specific self-confidence.
- The authors attribute the serial deficit to fixation — "continuously refining one option without considering others."
- A secondary aggregator reports ~445 clicks per million (parallel) vs ~397 (serial). **Unverified against the paper's own tables**; treat the direction as solid and the figure as indicative.

**Implication.** The payload is *comparison before commitment*. That maps exactly onto "before we engage in full specification" — the spec contract is the commitment, and the drafts must exist before it. It does not justify generating more artifacts per se.

### F4. AI-generated variants do not inherit the benefit by default

This is the finding that should shape the design.

- **Fixation is documented in LLMs.** Deng et al. (2026) identify two distinct mechanisms: individual-level fixation, where early outputs constrain later ideas as they do for humans; and collective-level homogenization, where LLMs merge knowledge into one unified distribution while human populations partition it across people. ([arXiv 2602.20408](https://arxiv.org/abs/2602.20408))
- **Same-prompt collapse.** Jiang et al. (2025) describe collapse on two axes: intra-model, where repeated samples converge on the same ideas, and inter-model, where independently trained models produce similar responses. ([arXiv 2604.01504](https://arxiv.org/pdf/2604.01504))
- **AI ideation support measurably reduced output quality.** CHI 2024, between-participants, N=60, visual ideation task: participants given an AI image generator showed *higher* fixation on an initial example and produced *fewer* ideas with *less* variety and *lower* originality than the baseline. The authors name the mechanism "fixation displacement" — fixation is not removed, it moves from the exemplar onto the AI's own outputs. ([arXiv 2403.11164](https://arxiv.org/abs/2403.11164))
- **Prompting alone is not sufficient.** IDEAFix (2026) finds specific briefs and keywords raise individual-idea novelty, but solutions stay bound within a shared semantic space. ([arXiv 2606.00875](https://arxiv.org/pdf/2606.00875))

**Interventions with evidence behind them:**

| Intervention | Effect | Source |
|---|---|---|
| Chain-of-thought before generating | Reduces fixation; effect appears in LLMs, not humans | Deng et al. 2026 |
| **Ordinary** personas (not "creative entrepreneur" personas) | Improves knowledge partitioning, acting as diverse sampling cues | Deng et al. 2026 |
| Both combined | Highest idea diversity measured — outperformed humans | Deng et al. 2026 |
| Morphological analysis (declare dimensions, then sample combinations) | Measurable fixation reduction, significant novelty and divergence increase | Reducing Design Fixation in Ideation by AI (2026); sample size not reported — weaker evidence |

**Implication.** "Generate three mockups" is contraindicated. Divergence has to be *constructed* — orthogonal axes declared before generation, independent contexts so outputs cannot anchor each other, and plain personas rather than genius framing. This is also the strongest argument that Writ should own something here at all: per Design Principle 4, new surface must "drive output the model wouldn't produce unprompted," and an unprompted model asked for options produces near-duplicates.

### F5. The harness now ships the renderer

Claude Code added a `/design` skill (research preview) the week of 17–21 August 2026. It takes a brief, publishes editable UI artboards built on artifacts, returns a canvas link, and implements the one the user picks — before any code is written. Available on Pro, Max, Team, Enterprise; one source cites v2.1.233+ as the floor. Claude Code Desktop separately ships a preview MCP that launches a dev server from `.claude/launch.json` against a headless browser.

Reported limitations: it does not auto-detect an existing design system — you must point it at your components; artboards can re-draw components the project already has unless named up front; and several artboards on top of a live session are token-heavy.

**Source quality caveat:** Anthropic's own changelog and docs did not surface in searches. This rests on secondary reporting ([the-decoder](https://the-decoder.com/claude-code-gets-a-design-command-that-lets-developers-create-ui-mockups-right-in-the-terminal/), [explainx](https://explainx.ai/blog/claude-code-design-command-artboards-research-preview-2026), [@ClaudeDevs](https://x.com/ClaudeDevs/status/2089471692762673408)) and should be verified against first-party docs before a spec locks.

**Implication, and it cuts two ways.** Writ must not build an artboard generator — Principle 4 is explicit, and Ralph is the cautionary precedent. But the harness's named weakness (no design-system awareness, re-draws existing components) is precisely the thing Writ already has files for: `.writ/docs/design-system.md` and `mockups/component-inventory.md`. The division is clean: the platform renders, Writ supplies the constraints and keeps the decision.

### F6. Two concrete defects in the current visual path

**`/prototype` names a Cursor-only tool that no adapter translates.** `cursor-ide-browser` appears twice in `commands/prototype.md` (lines 89 and 113) and in **zero** adapter files. `CLAUDE.md` states the convention it breaks: "commands use platform-agnostic tool names — each adapter translates them to one platform's APIs." On Claude Code, Codex, and OpenClaw, Step 2.5 names no runnable tool. The Claude Code adapter separately notes "There is no `visual-qa` equivalent here yet."

**`/design` now collides with a native Claude Code command.** Writ installs commands into `.claude/commands/` (`PLATFORM_DIR=".claude"`, `scripts/install.sh:76`). Claude Code ships its own `/design`. In this session — Claude Code 2.1.287, above the cited 2.1.233 floor — the skill listing resolves `design` to Writ's wireframe command, and no native artboard skill appears. That is consistent with shadowing but does not prove the mechanism; it needs a clean-room check. Either way a user on Claude Code typing `/design` cannot tell which they will get.

---

## Options Analysis

### Option A — Reframe `/prototype` as the exploration workflow *(recommended)*

Amend `/prototype`'s contract so exploration is its outcome. It loads a `design-divergence` skill, produces several structurally distinct looks, and — where cheap — a rough running thing that shows whether the idea survives contact with the codebase. It stops before spec and planning, and keeps its existing escalation into `/create-spec --from-prototype`.

- **Pros:** Delivers the job the command already advertises (F1). No new command — one skill plus a contract amendment, which is leaner than every alternative here. Carries the divergence evidence (F4) where the user already goes first. "End in mind" needs the code-adjacent realness only `/prototype` has; a mockup-only path cannot provide it. Keeps `/design` focused on its post-spec job.
- **Cons:** The contract amendment is load-bearing and must be done carefully — see the two-outcomes tension below. Writ's component contract (ADR-020) requires a single `outcome` per command, so "explore" and "ship a small change" cannot both be the outcome; one has to become a terminal state of the other. Raises the ceremony of a command whose selling point is having none, unless divergence is opt-in or stakes-gated.
- **Effort:** M
- **Risk:** Low-Medium. The risk is scope, not direction.

### Option B — Add multi-variant preview to `/prototype` Step 2.5 only

Generate N canvas mockups instead of one, keep everything else.

- **Pros:** Smallest diff. No contract change.
- **Cons:** Still runs after Context Scan has scoped files, so it decorates a decided change rather than helping choose. Nothing is retained, so the comparison that makes parallel prototyping work (F3) leaves no trace for the spec. Does nothing for the case where no code change is intended yet.
- **Effort:** XS
- **Risk:** Medium — looks like the ask, misses the mechanism.

### Option C — New `/explore` command

A dedicated pre-spec divergence command.

- **Pros:** Clean conceptual home; easy to give its own exit criteria.
- **Cons:** A 33rd command for something `/prototype` already advertises. ADR-015 exists to resist this, and its Tier B ritual asks "does the harness do this natively now?" — to which F5 answers partly yes. Writ's history (Ralph, `/audit`, `/lessons`, `/explain-code`) is a record of retiring commands like this.
- **Effort:** M
- **Risk:** High.

### Option D — Extend `/design` with a pre-spec `--explore` mode

*(This was the first draft's recommendation; see Revision.)*

- **Pros:** Closes the parking-lot item in the same pass.
- **Cons:** Produces pictures, not an end-in-mind. Leaves `/prototype` advertising exploration it does not do. Gives Writ two pre-spec divergence surfaces. The parking-lot item it closes is actually about rendering wireframes for an existing spec (F2) — a different problem.
- **Effort:** M
- **Risk:** Medium.

### Option E — Fix F6 only; let the harness explore

- **Pros:** Cheapest honest answer; subtraction before addition is Design Principle 1.
- **Cons:** The harness generates "a few options" from one context, which is the F4 failure mode. No decision record. Cursor, Codex and OpenClaw users get nothing.
- **Effort:** XS
- **Risk:** Low, but declines the part where Writ has something to add.

---

## Recommendations

### Primary: Option A

**1. Amend `/prototype`'s contract.** This is the gating work; the capability is straightforward once the contract is right.

- `outcome` becomes exploration-shaped. Replace "the repository gained no planning artifact describing it" with a line that forbids *spec* artifacts specifically, matching what `exit_criteria[0]` already says correctly. An exploration record is not a spec.
- Resolve the two-outcomes tension explicitly. ADR-020 allows one `outcome` per command. Recommended resolution: the outcome is **"the user can see several real takes on the idea and has chosen one, with the rejected takes and their reasons recorded"** — and shipped code becomes one terminal state of that, not the definition of done. A `/prototype` run that ends with three looks, a choice, and no code is a success, not an abandoned run.
- Keep the terminal constraint against starting `/implement-story`. That boundary is still right.

**2. Write `skills/design-divergence/SKILL.md`.** It owns *how to get genuinely different alternatives*, and is loadable by `/prototype`, `/design`, and `/create-spec`. Each rule traces to F4:

- **Declare axes before generating.** Two or three orthogonal dimensions the drafts must differ on — information density, navigation model, primary action placement — with each draft assigned a distinct combination. This is the morphological-analysis intervention and it is what converts "three samples" into "three alternatives."
- **Generate in independent contexts.** One subagent per draft, no shared scratch, no draft seeing another. Shared context is the fixation vector.
- **Reason before rendering.** Each generator states its axis commitment and the trade-off it accepts before producing anything.
- **Use ordinary personas.** "A developer who reads this screen forty times a day," not "a visionary designer." Genius framing measurably reduced diversity.
- **Cross-family where available**, reusing the Phase 12 panel's vendor plumbing (ADR-028) when a project opts in.
- **State the anti-pattern:** one agent, one call, "give me three options" is not divergence — and say why.
- **Keep it medium-agnostic.** Writ's persona is a solo builder, and not every concept is a screen. The same axes discipline applies to API shapes and data models; pstack's `architect` (two structurally distinct sketches from different models) is the non-visual precedent.

**3. Make divergence proportional, not default.** Per ADR-023, a one-line bug fix should not trigger three looks. Gate it on the same UI-surface detection Step 2 already does, plus an explicit flag, and default to **3** drafts rather than 5 — F5 reports artboards are token-heavy.

**4. Retain the record, not the pixels.** `.writ/prototypes/<date>-<concept>/exploration.md`: the axes, one row per draft, the selection, and **why each rejected draft was rejected**. Hosted canvas URLs are perishable and are never the system of record (ADR-005). `/create-spec --from-prototype` already exists — extend it to carry `exploration.md`'s rationale into the spec contract, where the rejected alternatives become the "what else did we consider" that Writ's ADRs demand everywhere else.

**5. Delegate rendering.** Claude Code's native `/design` artboards, Cursor canvas, self-contained HTML as the floor, Excalidraw below that. One adapter row per platform, with explicit degradation.

**6. Fix F6 in the same change**, because the reframe depends on it. Replace `cursor-ide-browser` with a platform-agnostic capability name and add translating rows to all four adapters; resolve the `/design` collision by renaming Writ's command or having it detect and delegate.

### Build order

Item 1 before item 2 — the contract decides what the skill is allowed to produce. Items 5 and 6 are the same work and should land together. Item 4's consumer (`--from-prototype` carrying rationale) ships in the same spec as its producer, per Writ's live-consumer rule.

### Explicitly not recommended

Option C. Writ does not need a 33rd command for something `/prototype` already advertises in its own usage table.

## Risks & Mitigation

| Risk | Mitigation |
|---|---|
| **The contract amendment makes `/prototype` two commands in a trench coat** — this is the main risk of the reframe | Resolve it in the frontmatter, not in prose: one `outcome` (exploration with a recorded choice), with shipped code as a terminal state rather than the definition of done. If the amended `exit_criteria` cannot be written as a short checkable list, the reframe is too big and Option B is the fallback. |
| **Ceremony creep in the command whose selling point is having none** | Divergence is stakes-gated and opt-in, never automatic (ADR-023). A one-line bug fix must still run exactly as it does today, and a regression test should pin that. |
| Claude Code's `/design` is a research preview and will change shape (F5) | Writ owns the brief and the record, not the renderer. Put the platform coupling in one adapter row per platform, so a breaking change is a four-line fix. Verify against first-party docs before locking a spec. |
| Divergence mechanics produce no measurable benefit | Make it falsifiable before building it out: run one concept through declared-axes generation and through a naive "give me three options" prompt, and have a human rate structural distinctness blind. If the axes version does not win, drop to Option E. This mirrors the Phase 12 panel trial, which was kept only on its measured verdict. |
| Token cost — several artboards on a live session is expensive (F5) | Default to 3 drafts, not 5. Make the count a flag. Gate on stakes rather than running it on every change. |
| `.writ/prototypes/` becomes dead weight nobody reads | Writ's live-consumer rule applies: if `/create-spec --from-prototype` is not extended to read `exploration.md`, do not create the directory. The consumer ships in the same spec as the producer. |
| Another Excalidraw — a format nothing reads | Require that the selected draft be loadable by the coding agent at Gate 1 before the capability is considered done. |
| Scope creep into a design tool | Hard boundary: Writ renders nothing itself and ships no runtime, consistent with ADR-028 and ADR-029. Where the platform cannot render, `/prototype` degrades to a written description of each option and says so. |

---

## Further Research

1. **First-party verification of Claude Code `/design`.** All of F5 is secondary reporting. Its exact output format, where artboards persist, and whether they can be pointed at a design system determine how the delegation is written. Highest-value open item.
2. **Does the `/design` collision shadow or conflict?** This session's listing is suggestive, not conclusive. Needs a clean-room install into a fresh project on 2.1.233+. Filed as [2026-10-19-design-command-name-collision](../issues/bugs/2026-10-19-design-command-name-collision.md).
3. **Does declared-axis divergence beat naive multi-prompt in practice?** The supporting morphological-analysis study did not report a sample size. Writ should produce its own measurement rather than cite a weak one — and the Phase 12 panel trial is the template for how.
4. **Cursor, Codex, and OpenClaw capability matrix.** F5 covers Claude Code only; searches returned nothing usable on Cursor canvas. The adapter rows cannot be written without this. Filed as [2026-10-19-prototype-visual-preview-cursor-only](../issues/bugs/2026-10-19-prototype-visual-preview-cursor-only.md).
5. **How much realness does "end in mind" require?** The reframe's distinctive claim is that a rough running thing beats a mockup for judging an idea. That is untested here. Worth settling early, because it sets whether exploration drafts are rendered-only, or code-backed and therefore much more expensive.
6. **Whether visual exploration is even the common case.** Writ's primary persona is a solo builder shipping real products; the question assumes UI work. Non-visual drafts — API shapes, data models — may be the larger need, and pstack's `architect` is the closer model. The skill should be written so it is not UI-only.

---

## Sources

**Parallel prototyping**
- Dow et al., "Parallel Prototyping Leads to Better Design Results, More Divergence, and Increased Self-Efficacy," ACM TOCHI 17(4) Art. 18, 2010 — [PDF](https://cs303.stanford.edu/papers/ParallelPrototyping2010-final.pdf), [Stanford HCI](https://hci.stanford.edu/publications/2010/parallel-prototyping/ParallelPrototyping2010-submitted.pdf), [seminar abstract](https://hci.stanford.edu/seminar/abstracts/09-10/100115-dow.html)
- [Cardinal Path summary](https://cardinalpath.com/web-design-the-case-for-parallel-prototyping) — source of the unverified 445/397 click-through figures

**LLM diversity and fixation**
- Deng et al., "Examining and Addressing Barriers to Diversity in LLM-Generated Ideas," 2026 — [arXiv 2602.20408](https://arxiv.org/abs/2602.20408)
- Jiang et al., "Magic, Madness, Heaven, Sin: LLM Output Diversity is Everything, Everywhere, All at Once," 2025 — [arXiv 2604.01504](https://arxiv.org/pdf/2604.01504)
- Wadinambiarachchi et al., "The Effects of Generative AI on Design Fixation and Divergent Thinking," CHI 2024 — [arXiv 2403.11164](https://arxiv.org/abs/2403.11164), [ACM DL](https://dl.acm.org/doi/full/10.1145/3613904.3642919)
- "IDEAFix: Evaluation Framework for Creative Defixation Prompting in LLMs," 2026 — [arXiv 2606.00875](https://arxiv.org/pdf/2606.00875)
- "Reducing Design Fixation in Ideation by AI, with the Intervention of the Morphological Analysis Method" — [ResearchGate](https://www.researchgate.net/publication/400934506_Reducing_Design_Fixation_in_Ideation_by_AI_with_the_Intervention_of_the_Morphological_Analysis_Method)

**Harness-native capability (secondary sources — verify against first-party docs)**
- [the-decoder, 18 Aug 2026](https://the-decoder.com/claude-code-gets-a-design-command-that-lets-developers-create-ui-mockups-right-in-the-terminal/)
- [explainx, Claude Code /design artboards](https://explainx.ai/blog/claude-code-design-command-artboards-research-preview-2026)
- [@ClaudeDevs announcement](https://x.com/ClaudeDevs/status/2089471692762673408)
- [Claude Code Desktop preview MCP](https://medium.com/@dan.avila7/claude-code-desktop-has-a-built-in-preview-mcp-heres-how-it-works-774809ff676f)

**Multi-variant design tooling landscape**
- [unite.ai, Best AI UX/UI Design Tools, Oct 2026](https://www.unite.ai/best-ai-ux-ui-design-tools/) — Google Stitch, Banani (3 variations per screen), Magic Patterns, Uizard
- [komposo, Best AI UI Generators 2026](https://www.komposo.ai/blog/best-ai-ui-generators-2026)

**Writ internal**
- `commands/prototype.md` (frontmatter, Step 2.5, lines 89 and 113), `commands/design.md` (frontmatter, Mode A), `commands/create-spec.md:512-521`
- `.writ/product/roadmap.md` — *Beyond Phase 12* parking lot, `/design` Mode A modernization
- ADR-005 (markdown canonical), ADR-009 (command/agent/skill boundary), ADR-015 (leanness self-governance), ADR-023 (stakes-proportional diligence), ADR-028 (runtime boundary, cross-family panel)
- `.writ/research/2026-10-19-writ-vs-pstack-research.md` — pstack `architect`: two structurally distinct sketches from different models
- `scripts/install.sh:76` (`PLATFORM_DIR=".claude"`), `adapters/*.md` (no `cursor-ide-browser` row)
