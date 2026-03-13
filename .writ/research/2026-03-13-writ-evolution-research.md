# Writ Evolution Research: Multi-Threading, Business Acumen & Visual Design

**Date:** 2026-03-13
**Researcher:** Writ (self-dogfooding)
**Status:** Complete
**Search tooling:** Exa (primary), web_search (supplementary)

## Research Questions

1. How can Writ become more robust and multi-threaded in its agent orchestration?
2. How can the `/create-spec` command incorporate deeper business acumen — competitive analysis, user personas, business model validation?
3. How can the `/prototype` command integrate richer visual design elements and mockups into its pipeline?

## Executive Summary

The AI agent orchestration landscape has matured rapidly. The Exa research surfaced a critical finding the initial pass missed: **Composio's Agent Orchestrator** is an open-source (MIT, TypeScript) production tool that already implements git-worktree-isolated parallel agent execution with CI auto-fix and review comment handling. Meanwhile, **Weave** provides entity-level merge (tree-sitter-based, 31/31 clean merges vs Git's 15/31) that directly solves the multi-agent merge conflict problem. These aren't research concepts — they're shipping tools.

For business acumen, the spec-driven development ecosystem has exploded. Six competing tools (Intent, Kiro, GitHub Spec Kit, OpenSpec, BMAD-METHOD, Cursor+rules) now exist with different approaches. The key insight: **living specs** that update bidirectionally as agents work have become the dominant paradigm. Writ's spec-healing agent is already on this trajectory. More importantly, the **Behavior-Driven Prompting** pattern (PRD → BDD → task specs) mirrors Writ's contract-first → user stories → implementation flow — but adds a "system spec" that records what *was actually built*, not what was planned.

For visual design, **MockFlow's "Export to AI Prompt"** feature converts wireframes into structured AI prompts for Claude Code/Cursor/Codex. **Figma's Claude Code MCP integration** now supports bidirectional flow — code to Figma and Figma to code. And **code-based wireframing** (building clickable prototypes in the actual codebase) has emerged as the preferred pattern over static mockups, with 20-minute wireframe-to-prototype cycles reported.

---

## Area 1: Multi-Threading & Robustness

### Finding 1: Composio Agent Orchestrator — The Reference Implementation

**Evidence:** [Composio Agent Orchestrator](https://github.com/ComposioHQ/agent-orchestrator) (MIT, TypeScript, 3,288 tests, v0.2.0) does exactly what Writ's `/implement-spec` aspires to: spawn parallel AI coding agents, each in its own git worktree. Features:
- Agent-agnostic (Claude Code, Codex, Aider)
- Runtime-agnostic (tmux, Docker)
- Plugin architecture: 8 swappable slots (Agent, Runtime, Workspace, Tracker, SCM, Notifier, Terminal, Reactions)
- CI auto-fix: when CI fails, the agent gets logs and fixes it
- Review handling: when reviewers request changes, the agent addresses them
- Configuration via `agent-orchestrator.yaml`

**Implications for Writ:** This is validation that Writ's architecture is on the right track. Key differences: Composio operates at the *issue/PR* level (one agent per GitHub issue), while Writ operates at the *story/spec* level (richer context, multi-gate pipeline). Writ should study Composio's workspace plugin pattern and reaction system (CI-failed → auto-retry, changes-requested → auto-address).

### Finding 2: Weave — Entity-Level Git Merge for Multi-Agent Work

**Evidence:** [Weave](https://github.com/openai/codex/issues/13554) is a tree-sitter-based merge driver for Git that merges per-entity (function, class, method) instead of per-line. Benchmark: 31/31 clean merges vs Git's 15/31 on real-world scenarios. 14 languages supported. MIT/Apache-2.0 licensed. Install: `brew install ataraxy-labs/tap/weave`.

When two agents both add functions to the same file, Git creates false line-level conflicts. Weave recognizes them as different entities → clean merge. Only same-entity modifications produce real conflicts.

**Implications for Writ:** This is a game-changer for parallel story execution. Running `weave setup` in the repo before `/implement-spec` parallel batches would dramatically reduce merge conflicts. The deeper integration: use Weave's `sem-core` library for entity-aware task decomposition — "Agent A owns functions X, Y, Z. Agent B owns functions P, Q, R."

### Finding 3: Git Worktrees Are Now Industry Standard

**Evidence:** Exa surfaced overwhelming consensus:
- **Claude Code**: Native `--worktree` flag, `isolation: worktree` in subagent frontmatter, auto-cleanup on session exit
- **Cursor 2.0**: Up to 8 concurrent agents via git worktrees
- **VS Code 1.107**: Automatic worktree isolation for background agents
- **incident.io**: Runs 4-5 parallel Claude Code agents daily via worktrees
- **Kelly Chan pattern**: 9 worktrees managed via 4 automated commands (`/new-branch`, `/typecheck-lint`, `/typecheck-lint-commit-push`, `/commit-push`)
- **CodeRabbit git-worktree-runner**: Works with Claude, Cursor, Opencode, Copilot, Gemini
- **ccswarm**: Multi-agent orchestration with worktree-isolated specialized agent pools

**Implications for Writ:** Worktrees are no longer optional — they're expected infrastructure. Writ should make worktree isolation the default for parallel batch execution in `/implement-spec`, not an opt-in feature.

### Finding 4: Deterministic Orchestration Beats LLM-Controlled Flow

**Evidence:** ggondim's deterministic multi-agent pipeline inside OpenClaw demonstrates a critical principle: "Don't orchestrate with LLMs. Every time I tried to put flow control in a prompt, the agent would sometimes skip steps, loop infinitely, or route to the wrong agent." The solution: YAML-based workflow engine (Lobster) with deterministic step sequencing, while LLMs handle the creative work within each step.

**Implications for Writ:** Writ already follows this principle perfectly — the pipeline (arch-check → code → lint → review → drift → test → visual QA → docs) is deterministic, with LLMs doing creative work within each gate. This is validation of a core architectural decision.

### Finding 5: Five Orchestration Patterns Cover 95% of Use Cases

**Evidence:** Microsoft Agent Framework defines five patterns with clear tradeoffs:

| Pattern | Best For | Writ Mapping |
|---------|----------|--------------|
| Sequential | Ordered pipelines | `/implement-story` gate pipeline |
| Concurrent | Independent subtasks | `/implement-spec` parallel batches |
| Handoff | Role-based routing | Gate-to-gate transitions |
| Group Chat | Multi-perspective review | Review agent + visual QA debate |
| Magentic | Dynamic task decomposition | Future: self-decomposing stories |

**Implications for Writ:** Writ currently uses Sequential (per-story) and Concurrent (parallel batches). The Group Chat pattern could enhance the review process — imagine the review agent, architecture agent, and testing agent simultaneously evaluating code from different perspectives, then synthesizing a unified review.

### Finding 6: Merge Strategy Taxonomy

**Evidence:** Zylos Research catalogs four merge strategies for parallel worktree outputs:

| Strategy | Mechanism | Best For |
|----------|-----------|----------|
| Sequential Integration | Merge one at a time, fix conflicts before next | Dependency-ordered features |
| Rebase Before PR | Rebase each branch onto main before merging | Linear history, minimal conflicts |
| Pre-Merge Conflict Detection | `git merge-tree` to detect conflicts without modifying working tree | Early warning before agents start |
| Cherry-Pick Selection | Pick best commits from ensemble agents | Best-of-N patterns |

The **Clash** tool uses `git merge-tree` to perform three-way merges between worktree pairs *without* modifying the filesystem — pure conflict detection.

**Implications for Writ:** Add pre-merge conflict detection to `/implement-spec` Phase 2 (Dependency Resolution). Before dispatching a parallel batch, run `git merge-tree` between planned story branches to predict conflicts. If conflicts are predicted, serialize those stories instead.

---

## Area 2: Business Acumen in `/create-spec`

### Finding 7: Behavior-Driven Prompting — PRD → BDD → Task Specs

**Evidence:** The "Behavior-Driven Prompting" workflow (Ralph Loops) produces consistently better results with AI agents:
1. **`prd.md`** — What are we building and why? (outcomes, not implementation)
2. **`behaviors.md`** — Given/When/Then scenarios for each feature
3. **`system-spec.md`** — What the system *currently does* (updated after each implementation)

Key insight: the system spec records what *was actually built*, not what was planned. This makes it a living document that survives implementation reality. Google's DORA 2025 report found 90% AI adoption growth correlated with 9% increase in bug rates — structured specs are the antidote.

**Implications for Writ:** Writ's flow (contract → user stories → implementation) already parallels PRD → BDD → tasks. The missing piece is the `system-spec.md` equivalent — a post-implementation record of what was actually built. The drift log captures deviations, but not the final state. Add a "what was built" summary to the story completion output.

### Finding 8: Six Competing Spec-Driven Tools — Landscape Map

**Evidence:** Augment Code's comparison of six tools reveals the spectrum:

| Tool | Spec Type | Multi-Agent | Writ Comparison |
|------|-----------|-------------|-----------------|
| Intent | Living (bidirectional) | Coordinator + specialists | Closest competitor — living specs + multi-agent |
| Kiro | Static (EARS notation) | Single agent + hooks | Simpler, AWS-native |
| GitHub Spec Kit | Static (markdown) | None (agent-agnostic) | Similar format, no orchestration |
| OpenSpec | Semi-living (delta markers) | None | Brownfield focus, single spec file |
| BMAD-METHOD | Static (template-driven) | None | Template-heavy, no learning loop |
| Cursor + .cursorrules | Pseudo-specs (rules) | None | Writ runs *on* Cursor |

METR's study found developers using AI were 19% *slower* on average due to debugging loops from unstructured prompts. Spec-driven tools eliminate this.

**Implications for Writ:** Writ is competitive with Intent (the most sophisticated tool in this space) — both use multi-agent orchestration and evolving specs. Writ's advantages: adaptive ceremony (`/prototype` vs `/implement-story`), deterministic gate pipeline, and the `/refresh-command` learning loop. Writ's gap: no structured business validation phase.

### Finding 9: The 5-Stage Agent-Driven Spec Pipeline

**Evidence:** DevelopersVoice describes a production PRD-to-spec pipeline with five AI agent stages:
1. **Ingestion & Contextualization** — Parse PRD + RAG enrichment from existing codebase
2. **Disambiguation & Clarification** — AI generates clarifying questions, human answers
3. **Structured Specification** — Output as OpenAPI, state tables, Gherkin scenarios
4. **Validation & Consistency Check** — Cross-reference against existing architecture
5. **Synthesis & Review** — Human-in-the-loop checkpoints before finalization

Two explicit human checkpoints: after Clarifications (Stage 2) and before Synthesis (Stage 5).

**Implications for Writ:** Writ's `/create-spec` already has stages 1-2 (context scan + Plan Mode discovery) and stage 5 (contract review). The gaps are stage 3 (structured machine-readable output — currently plain Markdown) and stage 4 (formal consistency validation). Adding a validation step that checks the contract against existing specs, APIs, and database schemas would catch conflicts early.

### Finding 10: LeanPivot's Stage-Based Tool Architecture

**Evidence:** LeanPivot AI organizes 65+ tools across six stages: Ideation → Validation → MVP → Launch → Growth → Investment. Each stage unlocks new tools. Key tools relevant to Writ's `/create-spec`:
- **Problem Statement Generator** — Craft clear problem statements
- **Jobs to Be Done** — Identify customer jobs and desired outcomes
- **Lean Canvas** — One-page business model
- **Customer Persona Generator** — Detailed persona profiles
- **Competitive Deep-Dive** — Competitive analysis and strategy
- **PRD Generator** — Structured product requirements
- **Feature Prioritization** — RICE/Impact-Effort scoring

**Implications for Writ:** The "Phase 0: Business Validation" concept should include a curated subset of these: Problem Statement, JTBD, Lean Canvas Lite, and Competitive Quick-Scan. These can all be auto-generated from the feature description + web search in ~30 seconds via a subagent.

### Finding 11: Living Specs vs Static Specs — The Core Split

**Evidence:** The 2026 spec-driven ecosystem splits on one question: do specs update as agents work?

- **Living specs** (Intent, partially OpenSpec): Spec and code stay synchronized. Agents write results back. Documentation never drifts.
- **Static specs** (Kiro, Spec Kit, BMAD): Spec is written upfront, agents read it, but spec doesn't update. Drift accumulates.

Isoform's analysis: "Updating the code is much easier than updating the spec first." CMU's Cursor study: code complexity increased ~41% when developers trusted AI without structured validation.

**Implications for Writ:** Writ's spec-healing agent makes it a "semi-living" spec system — drift is detected and logged, but the spec itself isn't automatically updated. The evolution: when spec-healing auto-amends a Small deviation, actually update `spec-lite.md` with the amendment. Medium and Large deviations still require human approval. This makes Writ's specs progressively more accurate over time.

---

## Area 3: Visual Design in `/prototype`

### Finding 12: MockFlow "Export to AI Prompt" — Wireframe → Agent

**Evidence:** MockFlow WireframePro added "Export to AI Prompt" — converts any wireframe into a structured, optimized AI prompt for Claude Code, Codex, Cursor. The prompt includes component hierarchy, layout structure, spacing constraints, and interaction descriptions.

**Implications for Writ:** This is the inverse of what we need for `/prototype`. Rather than wireframe → prompt → code, we want description → code-based wireframe → refined code. But the MockFlow format is useful as a reference for *how* to structure visual context when passing it to the coding agent.

### Finding 13: Code-Based Wireframing > Static Mockups

**Evidence:** TDP's "AI wireframing" guide argues for building clickable prototypes *in the actual codebase* rather than in design tools:
- Low-fidelity validation catches structural problems before design polish masks logic gaps
- 20-minute wireframe-to-clickable-prototype cycles
- Designers working in production repos with existing component libraries
- Sprint cycles collapse into single working sessions

v0 by Vercel and Bolt.new both generate React+Tailwind prototypes from text prompts that are instantly deployable.

**Implications for Writ:** `/prototype` should generate code-based wireframes, not Excalidraw files. The canvas system in Cursor renders live HTML — this is the perfect medium. Step 1: generate a quick HTML wireframe in canvas. Step 2: user approves layout/flow. Step 3: coding agent implements production version matching the approved wireframe.

### Finding 14: Figma MCP — Bidirectional Design↔Code Flow

**Evidence:** Figma's official MCP integration now supports bidirectional flow:
- **Figma → Code**: Extract component hierarchy, layout rules, typography, design tokens. AI generates code referencing tokens.
- **Code → Figma**: Claude Code can send live UI renders back to Figma as editable layers. Designers iterate in Figma, developers iterate in code, both stay synchronized.

TJ Pitre (design systems strategist, 20+ years) describes using Figma MCP for "Contextual Engineering" — building design systems where AI understands the design system and generates code that references the correct tokens.

**Implications for Writ:** When Figma MCP is available in a project, the `/design` command should auto-detect it and use it for all visual operations (attach, capture, compare). The coding agent should receive Figma design tokens as part of its context so it generates `text-primary` not `#111827`.

### Finding 15: The Claude Code Designer Workflow

**Evidence:** Builder.io documents how Claude Code enables designers to ship code directly:
1. Designer spots a UI issue on production
2. Opens the repo in Claude Code
3. Prompts: "Fix the spacing on the header component"
4. Claude Code makes the edit, previews in browser
5. Designer pushes PR directly

The key insight: designers working in production repositories with existing component libraries produce better results than designers working in sandboxed tools, because the constraints are real.

**Implications for Writ:** The `/prototype` visual preview doesn't need to be a separate step — it can be the coding agent's own browser preview. When the coding agent implements a UI change, it should immediately capture a screenshot and present it for approval before committing. This is already possible via the cursor-ide-browser MCP tools.

---

## Options Analysis

### Option A: "Worktree + Weave" — Safe Parallel Execution (Recommended)

Add git worktree isolation + Weave entity-level merge to `/implement-spec`. Add pre-merge conflict detection via `git merge-tree`. Business validation phase for `/create-spec`. Canvas preview for `/prototype`.

- **Pros:** Solves the biggest practical problem (parallel agent collisions), uses proven open-source tools, ships incrementally
- **Cons:** Weave adds a dependency; worktree lifecycle management adds complexity
- **Cost/Effort:** Medium
- **Risk Level:** Low-Medium

### Option B: "Living Spec Evolution" — Spec-Healing + Business Layer

Evolve spec-healing into true living specs (auto-update spec-lite.md on Small deviations). Add Phase 0 Business Validation. Add Behavior-Driven Prompting's "system spec" concept. Adopt machine-readable YAML frontmatter for contracts.

- **Pros:** Addresses the biggest quality gap in the ecosystem; positions Writ alongside Intent
- **Cons:** Requires spec format changes; system spec adds another file to maintain
- **Cost/Effort:** Medium
- **Risk Level:** Medium

### Option C: "Visual-First Prototype" — Canvas + Figma MCP

Add canvas-based visual preview to `/prototype` for UI changes. Auto-detect Figma MCP and pull design tokens. Generate code-based wireframes instead of Excalidraw. Browser screenshot verification in the coding agent loop.

- **Pros:** Biggest UX improvement for day-to-day prototyping; zero external dependencies for canvas
- **Cons:** Only helps UI work; no benefit for API/backend changes
- **Cost/Effort:** Small-Medium
- **Risk Level:** Low

---

## Recommendations

### Primary Recommendation: All Three Options, Phased

These three improvements are independent and can ship in parallel. The recommended order maximizes value-per-effort:

#### Phase 1: Git Worktree Isolation + Weave (Effort: M, Impact: High)

1. **Worktree lifecycle in `/implement-spec`**: Before each parallel batch, create a worktree per story. After batch completion, merge sequentially with Weave as the merge driver.
2. **Pre-merge conflict detection**: Run `git merge-tree` between planned story branches before dispatch. Serialize conflicting stories.
3. **File-overlap detection in dependency graph**: Stories touching the same files → same batch = serial, not parallel.

```bash
# Setup (once per repo)
weave setup

# Before batch execution
git worktree add .writ/worktrees/story-3 -b writ/story-3
git worktree add .writ/worktrees/story-4 -b writ/story-4

# Each coding agent operates in its worktree
# After batch completes
git checkout main
git merge --no-ff writ/story-3  # Weave handles entity-level merge
git merge --no-ff writ/story-4  # Only real conflicts surface

# Cleanup
git worktree remove .writ/worktrees/story-3
git worktree remove .writ/worktrees/story-4
```

#### Phase 2: Pre-Contract Business Validation for `/create-spec` (Effort: S-M, Impact: High)

Add "Phase 0: Business Validation" that runs as a subagent before the Plan Mode discovery conversation:

```markdown
## Pre-Spec Business Validation

### Problem Statement
[Auto-generated from description — who has this problem, how painful is it]

### JTBD Statement
When [situation], I want to [motivation], so I can [outcome].

### Lean Canvas Lite
- **Problem:** [top 3 pain points from research]
- **Existing Alternatives:** [how people solve this today]
- **Solution:** [proposed approach]
- **Key Metrics:** [how we'll measure success]
- **Unfair Advantage:** [what makes this hard to copy]

### Competitive Quick-Scan
[Web search results summarized — 2-3 competitors/alternatives with strengths and gaps]

### Target Persona
- **Who:** [derived from project context + JTBD]
- **Struggle level:** [acute / moderate / mild]
- **Current workaround:** [what they do today]
```

#### Phase 3: Canvas-Based Visual Preview for `/prototype` (Effort: S, Impact: Medium)

Updated pipeline:

```
CONTEXT SCAN → [VISUAL PREVIEW] → CODING AGENT → LINT → SUMMARY
                     ↑
            Only for UI-touching changes
            Auto-detected from file patterns (*.tsx, *.vue, components/, pages/)
            Uses cursor-ide-browser canvas tool
            User sees and approves before production code
```

When the coding agent finishes implementation, it also captures a browser screenshot of the result and presents it alongside the summary. If Figma MCP is available, design tokens are loaded into the coding agent's context.

### Stretch Goal: "What Was Built" Summary

After each `/implement-story` completion, append a concise "what was actually built" section to the story file. This creates the "system spec" equivalent from Behavior-Driven Prompting — a record of implementation reality, not just the plan.

---

## Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| Weave isn't installed in user's repo | Graceful fallback to standard `git merge`. Log suggestion to install Weave. |
| Git worktree merge conflicts despite Weave | Review agent already handles code review; extend it to arbitrate merge conflicts. Add "merge failure" state to execution state machine. |
| Business validation adds overhead to `/create-spec` | Make it opt-in: `--with-validation` flag, or auto-trigger for new projects, skip for brownfield additions. |
| Canvas preview latency slows `/prototype` | Only trigger for UI-touching changes. Auto-detect from file patterns. Skip for API/backend work. |
| Figma MCP rate limits block pipeline | Cache design tokens locally in `.writ/docs/design-system.md`. Only re-fetch when tokens change. |
| Living spec auto-updates introduce errors | Only auto-update `spec-lite.md` for Small deviations (naming, minor API shape). Medium and Large still require human approval. |

---

## Further Research Needed

- **Weave benchmarks on real Writ specs**: Run `/implement-spec` with Weave enabled on a 5+ story spec and measure merge conflict reduction.
- **Composio Agent Orchestrator plugin architecture**: Study their 8-slot plugin pattern for potential adoption in Writ's adapter system.
- **Intent by Augment deep evaluation**: Test their living spec implementation to understand bidirectional sync mechanics.
- **`git merge-tree` performance**: Benchmark pre-merge conflict detection on repos with 10K+ files to validate it's fast enough for the planning phase.
- **Canvas creation benchmarks**: Time canvas-based mockup generation in Cursor for complex UI layouts. Target: <30 seconds for the preview to be worthwhile.
- **Clash (pre-merge conflict detection tool)**: Evaluate whether it's worth integrating vs. raw `git merge-tree` calls.

---

## Sources

### Multi-Threading & Robustness
- Zylos Research — AI Agent Fork-Merge Patterns (2026-03-10): https://zylos.ai/research/2026-03-10-ai-agent-fork-merge-patterns
- Composio — Agent Orchestrator (MIT, TypeScript): https://github.com/ComposioHQ/agent-orchestrator
- Developer Toolkit — Orchestrating Multiple Parallel Agents: https://developertoolkit.ai/en/codex/productivity-patterns/multi-agent-workflows/
- Developer Toolkit — Multi-Agent Parallel Feature Work: https://developertoolkit.ai/en/codex/lessons/parallel-development
- Genmind — Multi-Agent Orchestration Patterns (2026-02-25): https://genmind.ch/posts/Multi-Agent-Orchestration-Patterns-Building-Collaborative-AI-Teams/
- ShShell — Building Agentic Control Planes: https://www.shshell.com/blog/multi-agent-orchestration-patterns
- ggondim — Deterministic Multi-Agent Dev Pipeline in OpenClaw: https://dev.to/ggondim/how-i-built-a-deterministic-multi-agent-dev-pipeline-inside-openclaw-and-contributed-a-missing-4ool
- Weave — Entity-Level Merge for Multi-Agent (issue #13554): https://github.com/openai/codex/issues/13554
- Zylos Research — Git Worktree Isolation Patterns (2026-02-22): https://zylos.ai/research/2026-02-22-git-worktree-parallel-ai-development
- Agent Factory — Worktrees: Parallel Agent Isolation: https://agentfactory.panaversity.org/docs/General-Agents-Foundations/general-agents/worktrees
- Paperclip AI — RFC: Adapter-level Git Worktree Isolation: https://github.com/paperclipai/paperclip/issues/175
- Vibehackers — Git Worktrees: Real Multi-Agent Development: https://vibehackers.io/blog/git-worktrees-multi-agent-development
- Kelly Chan — 9 Git Worktrees in Parallel: https://medium.com/@mrkelly/i-run-9-git-worktrees-in-parallel-heres-how-i-survived-multi-agent-development-69d6f0d81966
- BranchFS / Fork-Explore-Commit paper: https://arxiv.org/html/2602.08199v1

### Business Acumen & Spec-Driven Development
- Xcapit — Spec-Driven Development with AI Agents: https://www.xcapit.com/en/blog/spec-driven-development-ai-agents
- DevelopersVoice — Agent-Driven Spec: PRD to Tech Specs: https://developersvoice.com/blog/ai/agent-driven-tech-specs/
- Ralph Loops — Behavior-Driven Prompting: PRD to BDD to Living Spec: https://www.ralphloopsarecool.com/blog/behavior-driven-prompting/
- Augment Code — Spec-Driven Development & AI Agents Explained: https://www.augmentcode.com/guides/spec-driven-development-ai-agents-explained
- Augment Code — 6 Best Spec-Driven Development Tools 2026: https://www.augmentcode.com/tools/best-spec-driven-development-tools
- Augment Code — Vibe Coding vs Spec-Driven Development: https://www.augmentcode.com/guides/vibe-coding-vs-spec-driven-development
- Augment Code — Intent vs Kiro: https://www.augmentcode.com/tools/intent-vs-kiro
- OpenSpec — Spec-Driven Development: https://intent-driven.dev/knowledge/openspec/
- IntentSpec — Functional Guardrails for AI Coding Agents: https://intentspec.org/
- Bito — Spec Driven Development Explained: https://bito.ai/blog/spec-driven-development-explained-for-ai-coding-teams/
- LeanPivot AI — 65+ Stage Tools: https://leanpivot.ai/features/stage-tools/
- Aakash Gupta — JTBD Complete Guide: https://www.aakashg.com/jobs-to-be-done/
- Aakash Gupta — What Is Lean Canvas: https://www.aakashg.com/what-is-lean-canvas/
- IdeaPlan — AI Product PRD Template: https://www.ideaplan.io/templates/ai-product-prd-template
- AI Agents Kit — Product Management AI Prompts: https://aiagentskit.com/blog/product-management-ai-prompts/

### Visual Design & Prototyping
- TDP — AI Wireframing: Code Prototypes in 20 Minutes: https://designproject.io/blog/ai-wireframing-code-prototypes/
- Figma — AI App Builders for 2026: https://www.figma.com/resource-library/ai-app-builders/
- Figma — Claude Code to Figma Integration: https://www.figma.com/blog/introducing-claude-code-to-figma/
- MockFlow — Export Wireframes as AI Prompt: https://mockflow.com/updates/export-wireframes-as-ai-prompt-for-agentic-tools-like-claude-code
- Builder.io — Claude Code for Designers: https://www.builder.io/blog/claude-code-for-designers
- Bolt.new — AI Builder: https://bolt.new/
- Mejba Ahmed — Figma MCP + Cursor AI Workflow Guide: https://www.mejba.me/public/index.php/blog/figma-mcp-cursor-ai-design-to-code-workflow-guide
- Sergei Chyrkov — Figma Designs to Apps with MCP: https://sergeichyrkov.com/blog/how-to-turn-your-figma-designs-into-real-apps-using-mcp-and-cursor-(step-by-step-guide)
- Aiverse — Design Systems with Figma MCP: https://www.aiverse.design/insights/tj-pitre-design-systems

### Previous Research (Initial Pass)
- PRDCreator — How to Write a PRD in 2026: https://www.prdcreator.ai/blog/how-to-write-a-prd
- BrainGrid — AI Product Planner: https://www.braingrid.ai/blog/ai-product-planner
- v0 by Vercel: https://vercelv0.app/
- AriseGTM — Competitive Intelligence Automation 2026: https://arisegtm.com/blog/competitive-intelligence-automation-2026-playbook
- OmniBound — Living AI-Driven Personas: https://www.omnibound.ai/blog/customer-persona-research-building-living-ai-driven-personas
