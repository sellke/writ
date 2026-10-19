# Multiple Visual Drafts Before Spec: Where It Belongs in Writ

**Date:** 2026-10-19
**Status:** Complete
**Trigger:** "How might we make `/prototype` more robust at creating multiple looks (visual mock-ups) and drafts of an idea or a concept *before* we engage in full specification and implementation."
**Depth:** Standard 4-phase. Moderate stakes, reversible — this is a surface-placement decision inside an existing pipeline, not an architecture commitment.
**Writ version:** 0.41.0 + `feature/agent-cli-contract` at `d6584c7`

---

## Research Questions

1. Where exactly does Writ's current surface fail to produce multiple visual drafts before a spec is locked?
2. Is multi-variant exploration actually better than single-draft-and-iterate, and what is the evidence?
3. Does that evidence survive the switch from human designers to AI-generated variants?
4. What do 2026 harnesses provide natively, and what is left for a methodology layer to own?
5. Which Writ primitive should own this, and where do pre-spec artifacts live when no spec exists yet?

---

## Executive Summary

**Do not build this into `/prototype`.** The premise that Writ needs pre-spec visual exploration is correct and backed by good evidence. The premise that `/prototype` should host it is wrong on Writ's own terms: `/prototype`'s stated outcome is that "the repository gained no planning artifact describing it," and its terminal constraint forbids writing spec artifacts. Pre-spec concept exploration is a planning artifact by definition. `/prototype` is a shipping command — Context Scan → Code → Lint → Summary — and its Step 2.5 Visual Preview exists to steer a coding agent that is about to run, not to explore a concept that may never be built. Hosting exploration there drags a TDD pipeline behind every sketch.

The gap belongs to `/design`, which already has it listed as unfinished work: the roadmap parking lot carries "`/design` Mode A modernization — Excalidraw hand-authoring is a 2024 technique; revisit with AI image mockups or native design tools." `/design` cannot serve pre-spec exploration today because its exit criteria require output under `.writ/specs/<spec-name>/mockups/` — it structurally requires a spec that does not exist yet.

**The more consequential finding is that the obvious implementation does not work.** Dow et al. (2010) measured that parallel prototyping beats serial prototyping, but that was human designers, and the mechanism was *withholding feedback until several alternatives exist*, not *making more artifacts* — both conditions built five prototypes. The LLM evidence says AI variants do not inherit the benefit. Models exhibit fixation where early outputs constrain later ones, repeated samples from one prompt converge, and independently trained models converge on each other. A CHI 2024 experiment (N=60) found designers using an AI image generator produced *fewer* ideas with *less* variety and *lower* originality than the no-AI baseline, with fixation displaced from the brief onto the AI's own outputs. Asking one agent for "a few options" is three samples from one mode, not parallel prototyping.

**Recommendation: ship a `design-divergence` skill, not a command, and delegate rendering to the platform.** Writ should own the *brief* — pre-declared orthogonal divergence axes, independent generation contexts, and a decision record naming what was rejected and why — and delegate pixels to whatever the harness provides (Claude Code's native `/design` artboards, Cursor canvas, plain HTML fallback). The brief is the part that does not happen unprompted, which is exactly Writ's own test for justified surface. This adds zero commands, satisfies ADR-009 and ADR-015, and closes a parking-lot item instead of opening a new one.

Two concrete defects surfaced along the way and should be fixed regardless of which option is chosen: `/prototype` hard-codes a Cursor-only tool name that no adapter translates, and Writ's `/design` now collides with a native Claude Code command of the same name.

---

## Key Findings

### F1. `/prototype`'s contract forbids what is being asked of it

`commands/prototype.md` frontmatter:

- `outcome`: "The change sits in the working tree with tests written first and lint plus typecheck run, and **the repository gained no planning artifact describing it**."
- `exit_criteria[0]`: "no spec folder, story file, or task list was created under `.writ/specs/` for this change"
- Terminal constraint: "Do not open a PR, **write spec artifacts**, or escalate to the story pipeline without an explicit yes."

Step 2.5 Visual Preview is consistent with that contract precisely because it is ephemeral and singular: one canvas, approve / adjust / skip, nothing saved. Its own guardrail says so — "It gathers layout feedback before coding; it is not a design deliverable."

Making `/prototype` produce several retained drafts of a concept that may never be built requires contradicting all three lines. The pipeline is also wrong-shaped for it: Visual Preview sits *after* Context Scan has already detected the tech stack, located target files, and decided which files to modify. That is a step for a change already scoped to a codebase, not a concept still being chosen.

**Implication.** This is a placement error, not a capability gap in `/prototype`.

### F2. `/design` already owns this and already knows it is behind

`commands/design.md` Mode A generates Excalidraw wireframes, including per-state variants (`{component}-{state}.excalidraw`). But its `exit_criteria[0]` requires "the selected mode's artifacts are under `.writ/specs/<spec-name>/mockups/`", and every mode routes output into a spec folder. There is no path for "I have a concept, no spec, and want to see three takes on it."

The roadmap parking lot (`.writ/product/roadmap.md`, *Beyond Phase 12*) already carries the modernization item: "**`/design` Mode A modernization** — Excalidraw hand-authoring is a 2024 technique; revisit with AI image mockups or native design tools via `/refresh-command`."

Mode A also generates *states* (default, loading, empty, error), which is state coverage of one design, not alternative designs. Writ has no divergence step anywhere in its 32 commands.

**Implication.** The work the user is asking for is an already-identified, already-prioritized `/design` item. Routing it to `/prototype` would build it in the wrong place while the right place stays stale.

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

### Option A — Add multi-variant preview to `/prototype` Step 2.5

Generate N canvas mockups instead of one; let the user pick before coding.

- **Pros:** Smallest diff. Uses a step that already exists. Matches the literal request.
- **Cons:** Contradicts `/prototype`'s `outcome` and `exit_criteria[0]` (F1). Exploration still happens inside a shipping pipeline, after Context Scan has scoped files. Nothing is retained, so the comparison that makes parallel prototyping work (F3) leaves no trace for the spec. Does nothing for the real pre-spec case where no code change is intended yet. Leaves `/design` Mode A stale.
- **Effort:** XS
- **Risk:** Medium — ships a contract violation into the command whose whole job is staying small.

### Option B — New `/explore` (or `/concept`) command

A dedicated pre-spec divergence command: brief in, N drafts out, selection recorded, hand off to `/create-spec`.

- **Pros:** Clean conceptual home. Honest about being a planning step. Easy to give its own exit criteria.
- **Cons:** A 33rd command. ADR-015 exists specifically to resist this, and its Tier B ritual re-applies "does the harness do this natively now?" — to which F5 answers yes. Overlaps `/design` almost entirely. Writ's own history (Ralph, `/audit`, `/lessons`, `/explain-code`) is a record of retiring commands like this.
- **Effort:** M
- **Risk:** High — most likely of the four to be deleted within two quarters.

### Option C — Extend `/design` with a pre-spec mode, backed by a `design-divergence` skill *(recommended)*

Add a mode to `/design` that runs before a spec exists, and factor the divergence discipline into a skill that `/design`, `/create-spec`, and `/prototype` can all load.

- **Pros:** Closes a parking-lot item rather than opening a new one (F2). No new command — satisfies ADR-015 and ADR-009's "reusable capability multiple commands need" test for a skill. The skill carries the evidence-backed divergence mechanics from F4, which is the part that does not happen unprompted. Rendering delegates to the platform per Principle 4 (F5). The retained decision record is what makes the comparison durable, which is Writ's actual product.
- **Cons:** Requires resolving where pre-spec artifacts live (`/design`'s current exit criteria assume a spec). Requires an adapter row per platform for the render step — real work, but work F6 shows is already overdue. Must resolve the `/design` name collision.
- **Effort:** M
- **Risk:** Low-Medium — the uncertainty is the platform capability matrix, not the design.

### Option D — Do nothing structural; fix F6 only

Repair the `cursor-ide-browser` reference and the name collision, and leave exploration to the harness's own `/design`.

- **Pros:** Cheapest honest answer. If Claude Code's artboards are good enough, Writ adding anything is re-implementation. Subtraction before addition is Writ's own Design Principle 1.
- **Cons:** Loses the divergence brief (F4), which the harness does *not* do — it generates "a few options" from one context, which is the failure mode. Loses the decision record. Cursor, Codex, and OpenClaw users get nothing. Leaves pre-spec exploration undefined in a contract-first methodology.
- **Effort:** XS
- **Risk:** Low, but it declines the one part of the problem where Writ has something to add.

---

## Recommendations

### Primary: Option C

**1. Write a `skills/design-divergence/SKILL.md`.** It owns *how to get genuinely different drafts*, and nothing else. Contents, each traceable to F4:

- **Declare axes before generating.** Name two or three orthogonal dimensions the drafts must differ on — information density, navigation model, primary action placement — and assign each draft a distinct combination. This is the morphological-analysis intervention, and it is what converts "three samples" into "three alternatives."
- **Generate in independent contexts.** One subagent per draft, no shared scratch, no draft seeing another. Shared context is the fixation vector (Deng et al.).
- **Reason before rendering.** Each generator states its axis commitment and the trade-off it accepts before producing anything — chain-of-thought is the measured fixation reducer.
- **Use ordinary personas.** "A developer who reads this screen forty times a day," not "a visionary designer." Genius framing measurably reduced diversity.
- **Cross-family where available.** Reuse the Phase 12 cross-family panel's vendor plumbing (ADR-028) when a project opts in. Inter-model convergence is real but weaker than intra-model.
- **State the anti-pattern explicitly:** asking one agent for N options in one call is not divergence, and the skill should say why.

**2. Add `/design --explore` (pre-spec mode).** Takes a concept description or an issue file. Runs the skill, renders through the platform, presents the drafts side by side, and records the selection. It is the only `/design` mode that does not require an existing spec.

**3. Resolve the artifact home.** Pre-spec drafts cannot go in `.writ/specs/<name>/mockups/`. Recommend `.writ/design/<date>-<concept>/` holding:
- `exploration.md` — the axes, one row per draft, the selection, and **why each rejected draft was rejected**
- whatever renderable files the platform produced (HTML, SVG, artboard links)

Then `/create-spec --from-exploration` graduates the selected draft into the spec's `mockups/` and carries `exploration.md`'s rationale into the contract. The rejected alternatives are the durable asset: they are the "what else did we consider" that Writ's ADRs already demand everywhere else, and the thing a reader six months out cannot reconstruct. **Persist the reasoning even when the artboard links rot** — treat hosted canvas URLs as perishable and never as the system of record (ADR-005).

**4. Fix F6 in the same change.** Replace `cursor-ide-browser` in `prototype.md` with a platform-agnostic capability name, add the translating row to all four adapters, and resolve the `/design` collision — rename Writ's to `/writ-design`, or make it detect and delegate to the native skill. Adapter rows should degrade explicitly: artboards where available, plain self-contained HTML where not, Excalidraw only as the floor.

**5. Leave `/prototype` Step 2.5 alone**, except for the tool-name fix. One preview to steer one coding agent is the right scope for a shipping command. Add one line pointing at `/design --explore` for the case where the user has not chosen a direction yet.

### Alternative if Option C is too much

Option D plus item 1 only: ship the `design-divergence` skill and let the native `/design` consume it. Gets the evidence-backed part for XS effort and defers the artifact-home question. Weaker, because nothing retains the rejected alternatives.

### Explicitly not recommended

Option B. Writ does not need a 33rd command for something the harness ships natively and `/design` already half-owns.

---

## Risks & Mitigation

| Risk | Mitigation |
|---|---|
| Claude Code's `/design` is a research preview and will change shape (F5) | Writ owns the brief and the record, not the renderer. Put the platform coupling in one adapter row per platform, so a breaking change is a four-line fix. Verify against first-party docs before locking a spec. |
| Divergence mechanics produce no measurable benefit | Make it falsifiable before building it out: run one concept through declared-axes generation and through a naive "give me three options" prompt, and have a human rate structural distinctness blind. If the axes version does not win, build Option D instead. This mirrors the Phase 12 panel trial, which was kept only on its measured verdict. |
| Token cost — several artboards on a live session is expensive (F5) | Default to 3 drafts, not 5. Make the count a flag. Gate on stakes per ADR-023 rather than running it on every change. |
| `.writ/design/` becomes dead weight nobody reads | Writ's live-consumer rule applies: if `/create-spec --from-exploration` is not built, do not create the directory. The consumer ships in the same spec as the producer. |
| Another `/design` Mode A — a format nothing reads | The existing Excalidraw path is the precedent. Require that the selected draft be loadable by the coding agent at Gate 1 before the mode is considered done. |
| Scope creep into a design tool | Hard boundary: Writ renders nothing itself and ships no runtime, consistent with ADR-028 and ADR-029. If the platform cannot render, `/design --explore` degrades to a written description of each option and says so. |

---

## Further Research

1. **First-party verification of Claude Code `/design`.** All of F5 is secondary reporting. Its exact output format, where artboards persist, and whether they can be pointed at a design system determine how item 4 is written. This is the highest-value open item.
2. **Does the `/design` collision shadow or conflict?** This session's listing is suggestive, not conclusive. Needs a clean-room install into a fresh project on 2.1.233+.
3. **Does declared-axis divergence beat naive multi-prompt in practice?** The supporting study did not report a sample size. Writ should produce its own measurement rather than cite a weak one.
4. **Cursor, Codex, and OpenClaw capability matrix.** F5 covers Claude Code only; searches returned nothing usable on Cursor canvas. Option C's adapter rows cannot be written without this.
5. **Whether visual exploration is even the common case.** Writ's primary persona is a solo builder shipping real products; the question assumes UI work. Non-visual concept drafts — API shapes, data models — may be the larger need, and pstack's `architect` (two structurally distinct sketches from different models) is the closer model for those. The skill should be written so it is not UI-only.

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
