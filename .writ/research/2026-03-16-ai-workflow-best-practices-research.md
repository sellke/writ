# AI Workflow Best Practices for Writ

**Date:** 2026-03-16
**Researcher:** Writ (self-dogfooding)
**Status:** Complete
**Search tooling:** Exa (primary)

## Research Questions

1. What are the current best practices for AI coding agent workflows, rules, and context engineering?
2. Where does Writ's `writ.mdc` / `system-instructions.md` have gaps relative to industry best practices?
3. What should the roadmap prioritize based on where the ecosystem is heading?

## Executive Summary

The AI coding agent ecosystem has crystallized around several key patterns since early 2025. Three findings stand out:

**Context engineering has replaced prompt engineering as the dominant discipline.** Anthropic formalized it, the arXiv MSR 2026 paper taxonomized it (401 repos, 5 themes, 20 codes), and every major framework now treats context as the scarcest resource. Writ's rules files are good at defining personality and workflow, but weak on the specific, actionable, machine-parseable directives that research shows actually change agent behavior.

**AGENTS.md has become the universal cross-tool standard.** Governed by the Linux Foundation's Agentic AI Foundation (with Anthropic, Google, Microsoft, OpenAI as platinum members), adopted by 60,000+ repos. Writ currently generates only `.cursor/rules/writ.mdc` — it has no cross-tool story. This is a strategic gap as the market fragments across Cursor, Claude Code, Codex, Copilot, Windsurf, Amp, and others.

**The orchestrator-must-never-execute principle has been independently validated by every major AI lab.** Anthropic published orchestrator-worker separation; OpenAI's Agents SDK formalized hierarchical delegation; Google ADK shipped parent-child delegation. Writ already follows this pattern with its deterministic gate pipeline — this is strong validation of a core architectural decision. But Writ lacks the verification/reflection layer and scope governance mechanisms that production systems are converging on.

---

## Detailed Findings

### Finding 1: The Cursor Rules Taxonomy (arXiv MSR 2026)

**Source:** "Beyond the Prompt: An Empirical Study of Cursor Rules" — ACM MSR 2026, Rio de Janeiro

The first systematic study of AI coding rules analyzed 401 open-source repositories and developed a taxonomy of five high-level themes and 20 detailed codes:

| Theme | What It Covers |
|-------|---------------|
| **Conventions** | Naming, formatting, file organization, architectural patterns |
| **Guidelines** | Error handling, security practices, testing standards, performance |
| **Project Information** | Tech stack, dependencies, codebase structure, domain context |
| **LLM Directives** | Agent behavioral instructions, response format, thinking modes |
| **Examples** | Code snippets showing desired patterns, input/output pairs |

**Key insight:** Rules that combine Project Information + Conventions + Examples produce dramatically better agent output than rules with only LLM Directives (personality/behavioral instructions).

**Gap in Writ:** `writ.mdc` is almost entirely LLM Directives (personality, workflow, interaction patterns). It has minimal Conventions, zero Project Information, zero Examples, and no Guidelines. This is the single biggest improvement opportunity.

### Finding 2: Context Engineering as First-Class Discipline

**Sources:** Anthropic's "Effective Context Engineering for AI Agents" (2025-09); OpenDev arXiv paper (2026-03); Morph's Context Engineering Guide (2026-02)

The field has converged on several principles:

1. **Minimum Viable Context (MVC)** — "The smallest possible set of high-signal tokens that maximize the likelihood of desired outcomes." Not the most context. The *right* context.

2. **The 1M Token Wall** — SWE-rebench data shows performance degrades meaningfully past ~1M tokens regardless of window size. Context is finite and must be budgeted.

3. **Progressive/Just-in-Time Loading** — Instead of pre-loading everything, agents maintain lightweight references and dynamically load data at runtime. Claude Code's tool lazy loading reduces context by 95%.

4. **System Reminders to Counteract Attention Decay** — Models lose focus over long conversations. Event-driven reminders re-inject critical instructions at key moments.

5. **Adaptive Context Compaction** — Progressively compress older observations to reclaim token budget for fresh reasoning.

**Gap in Writ:** None of Writ's commands or agents explicitly address context budgeting. Long-running pipelines (like `/implement-spec` with 5+ stories) will degrade as context accumulates. The agent prompts load everything upfront rather than progressively. No compaction strategy exists.

### Finding 3: AGENTS.md — The Universal Standard

**Sources:** Linux Foundation AAIF announcement; GitHub analysis of 2,500+ repos; Blake Crosley's "AGENTS.md Patterns" (2026-02); VibeMeta comparison (2026-03)

AGENTS.md is the cross-tool standard for AI agent project configuration:

- **Governed by:** Linux Foundation's Agentic AI Foundation
- **Platinum members:** Anthropic, Google, Microsoft, OpenAI, AWS
- **Adoption:** 60,000+ repos, growing rapidly
- **Read by:** Codex CLI, GitHub Copilot, Cursor, Windsurf, Amp, Devin, Gemini CLI, and many more

GitHub's analysis of 2,500+ repos identified **six core areas** that make the biggest difference:

1. **Executable Commands** — Exact install/build/test/lint invocations (not descriptions)
2. **Testing Instructions** — Framework, patterns, where tests live, how to write them
3. **Code Style** — With concrete examples, not abstract principles
4. **Codebase Structure** — Directory map with responsibilities
5. **Security Considerations** — Explicit boundaries and prohibitions
6. **Dos and Don'ts** — "Nitpicky" specific guidelines beat vague principles

Blake Crosley's research found that **files organized by task (coding, review, release) outperform files organized by category (style, testing, deployment)**. The key insight: structure rules around what the agent is *doing*, not what domain the rule belongs to.

**Gap in Writ:** Writ has no AGENTS.md generation or support. For a tool whose mission is to be the "reference methodology for AI-assisted development," not having a cross-tool story is a strategic blind spot. The install script could generate an AGENTS.md alongside `.cursor/rules/writ.mdc`.

### Finding 4: What Actually Changes Agent Behavior

**Sources:** Agentic Coding Best Practices 2026 (Medium); Codegen blog; Developer Toolkit; Rephrase-it prompt guide (2026-03)

Across all sources, the patterns that reliably improve agent output:

| Practice | Why It Works |
|----------|-------------|
| **Negative rules** ("DO NOT") | Models respond strongly to explicit prohibitions |
| **Examples over descriptions** | A 2-line code snippet > a paragraph of description |
| **Scope boundaries** | "Only modify files in X. Do not change Y." |
| **Definition of done** | Explicit exit criteria, not feelings |
| **Error taxonomy loop** | After 2-3 bad attempts, add "Common failure modes to avoid" |
| **Front-loaded constraints** | Put requirements BEFORE the code in prompts (top of context gets more attention) |
| **Plan-first for multi-file** | Agent states which files it will create/modify before acting |
| **Fresh sessions over long threads** | Quality degrades after ~15+ messages; restart with accumulated learnings |
| **Git as safety net** | Branch/commit before every agent task — non-negotiable |

The ETGPO paper (2026) formalizes the error taxonomy approach: collect agent failures, categorize them, then add targeted guidance against the most frequent error categories. This is essentially what Writ's `/refresh-command` does — but the research suggests it should be more systematic.

**Gap in Writ:** `writ.mdc` has no negative rules, no examples, no scope boundaries, no definition of done, and no error taxonomy. These are all high-leverage additions.

### Finding 5: Orchestrator-Worker Separation Is Industry Consensus

**Sources:** "Why Your AI Orchestrator Should Never Write Code" (Towards AI, 2026-03); Microsoft Agent Framework; Composio Agent Orchestrator; SpecWeave architecture

Every major AI lab independently converged on the same structural boundary:

- **Anthropic:** Orchestrator-worker separation as recommended topology
- **OpenAI:** `agent.as_tool()` hierarchical delegation in Agents SDK
- **Google:** Parent-child delegation with LLM-driven routing in ADK

The "Delegated Reasoning" paper (40+ production workflows, 3 months, 6 agents) distilled one rule: **"The orchestrator must never execute. It decomposes, delegates, validates, and escalates."**

Key operational patterns from production:
- **30% scope threshold** — If an agent changes >30% more files than its task specified, flag it
- **30-second rule** — If the orchestrator can answer in 30 seconds of reasoning, don't spawn an agent
- **Model routing by cognitive task** — Use different models for planning vs. coding vs. review

**Writ's position:** Strong. The deterministic gate pipeline (arch-check → code → lint → review → drift → test → visual QA → docs) already implements this correctly. The validation is reassuring. Missing: the scope governance (30% threshold) and the reflection/verification layer.

### Finding 6: Reflection and Verification Layers

**Sources:** "Vibe Engineering: Reflection" (Medium, 2026-03); The Ralph Loop (Blake Crosley, 2026-02)

Production agent systems are adding structured self-assessment after every agent turn:

1. **Task type inference** — Classify task as coding/docs/research/ops
2. **Structured self-assessment** — Agent evaluates its own work against completion criteria
3. **Workflow gates** — Tests ran? Build passed? PR created? CI green?
4. **Escalating feedback** — 3 attempts max, each more direct, then yield to human
5. **Cross-model review** — Author model (Opus) + Reviewer model (different provider) + Auditor model (security-focused)

The Ralph Loop adds an outer loop: when an agent exhausts its context window, persist state to filesystem, spawn a fresh instance with the accumulated learnings. **Spawn budgets** (not depth limits) prevent exponential growth.

**Gap in Writ:** The coding agent has self-verification (run tests + typecheck), but no structured reflection against the task definition. The review agent evaluates the coding agent's work, but neither agent evaluates *itself* before handing off. Adding a lightweight self-assessment step would catch issues earlier in the pipeline.

### Finding 7: The `best-practices.md` Ghost Reference

`writ.mdc` line 32 references `.writ/docs/best-practices.md` — but this file doesn't exist. The rule says "Follow critical thinking guidelines in `.writ/docs/best-practices.md`" — pointing agents at a missing file wastes context and reduces trust in the instructions.

---

## Recommendations

### Priority 1: Strengthen `writ.mdc` (High Impact, Low Effort)

The current file is 93 lines and almost entirely LLM Directives (personality/workflow). Based on the MSR 2026 taxonomy and AGENTS.md best practices, add:

#### A. Project Information Section (new)

```markdown
## Project Context

**Writ** is a command-driven AI development methodology delivered as configuration files
(commands, agents, rules) installed into IDE workspaces. Shell scripts handle installation.

- **Languages:** Markdown (commands, agents, specs), Shell (install.sh, scripts)
- **No runtime:** Writ has no compiled code — it's a methodology, not an application
- **Install:** `bash <(curl -fsSL https://raw.githubusercontent.com/.../install.sh)`
- **Test:** Dogfood on real projects; no automated test suite exists yet
```

#### B. Conventions Section (new)

```markdown
## Conventions

- Command files: `commands/*.md` — one file per command, self-contained prompt
- Agent files: `agents/*.md` — one file per agent, includes prompt template
- Specs: `.writ/specs/YYYY-MM-DD-<name>/` — date-prefixed, contain user stories
- Decision records: `.writ/decision-records/adr-NNN-<name>.md`
- Research: `.writ/research/YYYY-MM-DD-<topic>-research.md`
```

#### C. Explicit Boundaries (new — highest leverage)

```markdown
## Boundaries

- DO NOT modify files in `commands/` or `agents/` during story implementation — these are product source
- DO NOT run `scripts/install.sh` on this repo — it would overwrite symlinks
- DO NOT create files outside `.writ/` unless implementing a product feature
- DO NOT commit `.writ/state/` — it's gitignored ephemeral data
- ALWAYS use `.writ/` for specs, research, docs, and decision records
- ALWAYS prefer editing existing commands over creating new ones
```

#### D. Fix the Ghost Reference

Either create `.writ/docs/best-practices.md` with actual critical thinking guidelines, or remove the reference from `writ.mdc`. A missing file actively hurts agent behavior.

### Priority 2: Strengthen `system-instructions.md` (High Impact, Medium Effort)

`system-instructions.md` is currently identical to `writ.mdc` minus the Self-Dogfooding section. This is the file that ships to all Writ users. It should be the canonical, user-facing version.

#### A. Add Context Engineering Guidance

```markdown
## Context Management

- Front-load constraints: put requirements and boundaries BEFORE implementation details
- For multi-story pipelines: summarize previous stories, don't re-include full content
- When context grows large (>15 messages): consider fresh session with accumulated learnings
- Agent prompts should request minimum viable context, not everything available
```

#### B. Add Definition of Done for Commands

```markdown
## Completion Standards

Every command execution should end with a verifiable "done" state:
- `/implement-story`: All acceptance criteria checked, tests pass, lint clean, drift logged
- `/prototype`: Code compiles, lint passes, scope flags reported
- `/create-spec`: Contract approved, story files created, spec-lite generated
- `/research`: Research document written to `.writ/research/`, sources cited
```

#### C. Add Error Handling / Escalation Guidance

```markdown
## When Stuck

- If blocked after 2-3 attempts on the same issue: stop, diagnose what context is missing
- If the agent is modifying files outside the expected scope: pause, reassess
- If tests fail repeatedly: check if the test itself is wrong, not just the implementation
- Never silently swallow errors — surface them for human decision
```

### Priority 3: AGENTS.md Support in Writ (Strategic, Medium Effort)

**Roadmap item.** Writ should support generating an `AGENTS.md` file as part of its install process. This is the cross-tool play:

- `install.sh` generates `AGENTS.md` with Writ conventions + project-specific context
- The `AGENTS.md` contains: build commands, test commands, coding conventions, codebase structure, boundaries
- `.cursor/rules/writ.mdc` becomes the Cursor-specific overlay with Writ personality and workflow
- Users working in Claude Code, Codex, or Copilot benefit from Writ's conventions without Cursor dependency

This positions Writ as tool-agnostic — which aligns with the existing adapter concept in the roadmap.

### Priority 4: Roadmap Additions

Based on the research, these items are missing from the current roadmap and represent meaningful capabilities:

#### A. Context Engineering Layer (Phase 2)

```markdown
- [ ] **Context budgeting for agent prompts** — Track token usage, progressive loading `Effort: M`
  - Agent prompts load minimum viable context, not everything
  - Previous story summaries instead of full content for later stories in a batch
  - Adaptive compaction: compress older gate results as pipeline progresses
  - System reminders at key pipeline moments to counteract attention decay
```

#### B. Scope Governance (Phase 2)

```markdown
- [ ] **Scope governance in coding agent** — Prevent silent scope creep `Effort: S`
  - Track files modified against task definition
  - Flag when agent changes >30% more files than task specified
  - Definition of Done verification before handoff (not just self-check)
```

#### C. Cross-Tool Support via AGENTS.md (Phase 2)

```markdown
- [ ] **AGENTS.md generation** — Universal agent configuration `Effort: S`
  - Generate AGENTS.md during install with project conventions
  - Maintain .cursor/rules/writ.mdc as Cursor-specific overlay
  - Support Claude Code (CLAUDE.md), Codex (AGENTS.md), Copilot
```

#### D. Error Taxonomy Collection (Phase 2, feeds Phase 3)

```markdown
- [ ] **Error taxonomy collection in /refresh-command** — Systematic failure learning `Effort: S`
  - Categorize failures from agent transcripts (not just "what went wrong")
  - Build "Common failure modes to avoid" sections in command files
  - Track frequency: most common failure categories get highest-priority fixes
```

#### E. Reflection Layer for Agents (Phase 2)

```markdown
- [ ] **Structured self-assessment in agent handoffs** — Verification before delegation `Effort: S`
  - Coding agent assesses own work against acceptance criteria before handoff
  - Review agent verifies completeness of its own review before reporting
  - Escalating feedback: 3 attempts max, each more targeted, then yield to human
```

#### F. Persistent Memory Across Sessions (Phase 3)

```markdown
- [ ] **Session memory in .writ/state/** — Cross-session continuity `Effort: L`
  - Auto-extract key decisions, patterns, and learnings from each session
  - Inject relevant memories at session start based on current task context
  - Memory decay: older memories lose relevance over time
  - Privacy-aware: no code content in memory, only abstractions
```

---

## Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| Bloating `writ.mdc` past effective size | Keep under 150 lines total. Use progressive disclosure: link to detailed docs |
| AGENTS.md diverging from `.cursor/rules/` | Single source of truth in Writ source; generate both from same data |
| Context engineering adds complexity to commands | Start with the 3 highest-traffic commands: `/implement-story`, `/prototype`, `/create-spec` |
| Error taxonomy requires enough data | Bootstrap from existing agent transcripts in `.cursor/projects/` |
| Cross-tool support dilutes Cursor focus | AGENTS.md is additive — `.cursor/rules/` remains the primary Cursor mechanism |

---

## Further Research Needed

- **Quantify context usage in current Writ pipelines** — Run a 5-story `/implement-spec` and measure token consumption per gate to identify where compaction would help most
- **AGENTS.md generation prototype** — Build a minimal generator and test with Claude Code and Codex to validate cross-tool compatibility
- **Benchmark rule effectiveness** — A/B test current `writ.mdc` vs. enhanced version with Conventions + Boundaries + Examples on the same task
- **SpecWeave plugin architecture study** — Their skill/agent/hook/command taxonomy maps interestingly to Writ's command/agent structure; worth deeper analysis
- **OpenDev's dual-agent architecture** — Their planning/execution separation with adaptive context compaction is closest to what Writ needs for long-running pipelines

---

---

## Appendix: Self-Challenge — Revised Conclusions

After reviewing all 29 command files and 7 agent files against the research findings, several of the original recommendations were wrong or overstated. This section corrects the record.

### Correction 1: "writ.mdc is personality-heavy, substance-light" — WRONG

**Original claim:** `writ.mdc` lacks Conventions, Project Information, and Examples per the MSR 2026 taxonomy. Should be enriched.

**What the commands actually show:** Writ's architecture is deliberately layered. The always-applied `writ.mdc` (93 lines) provides identity and workflow guidance, loaded into every single interaction. The actual substance lives in 29 command files (some exceeding 800 lines) loaded on-demand when invoked. `/create-spec` has 806 lines of detailed prompt engineering with examples, conventions, error handling, and pushback patterns. `/implement-story` has 470 lines with 8 gates, fix loops, drift analysis, and recovery flows.

**Why the original recommendation was wrong:** Adding Project Information, Conventions, and Boundaries to `writ.mdc` would bloat every interaction — even a simple `/status` check would pay the token cost of conventions that only matter during `/implement-story`. This is the *opposite* of what the context engineering research recommends (minimum viable context, progressive loading).

**Writ's thin rule + thick command files IS progressive context loading.** The MSR 2026 taxonomy is correct about *what* content matters, but the original analysis was wrong about *where* it should live in Writ's architecture. The answer: it already lives in the right place — command files.

**What survives:** The ghost reference to `.writ/docs/best-practices.md` (which doesn't exist) is a real bug that wastes context and reduces trust. Fix that. The Self-Dogfooding section's boundaries are adequate for the writ repo itself.

### Correction 2: "Context engineering is not addressed" — PARTIALLY WRONG

**Original claim:** Writ's commands don't manage context as a finite resource.

**What the commands actually show:** Writ already practices several context engineering patterns:

1. **`spec-lite.md`** — explicitly described as "Condensed version for AI context windows." This is a compressed context artifact. The coding agent gets `spec-lite.md`, not the full `spec.md`.
2. **Subagent delegation** — Every gate in `/implement-story` spawns a fresh subagent with its own context window. The coding agent, review agent, testing agent, and docs agent each start with clean context.
3. **Parallel `model: "fast"` subagents** — `/create-spec` Phase 2 uses cheap, fast subagents for story generation. Each gets focused context.
4. **On-demand command loading** — Commands load only when invoked, not always-applied.

**Where the concern IS real — three specific hotspots:**

#### Hotspot 1: The Coding Agent Resume in Fix Loops

When Gate 3 (review) returns FAIL, the orchestrator *resumes* the coding agent rather than spawning fresh:

```markdown
Task({
  subagent_type: "generalPurpose",
  resume: "{coding_agent_id}",   ← RESUME, not fresh spawn
  ...
})
```

The resumed coding agent carries its entire previous context: original task, first implementation, all file reads/writes, all reasoning. Plus the new review feedback. If this fix loop runs 2-3 times (the max), the coding agent is operating with 2-3x the context of a fresh agent, with older reasoning potentially competing for attention against the latest review feedback.

**This is the highest-risk context pattern in Writ.** Research consistently shows that fresh context + accumulated learnings outperforms degraded long-context sessions. The Ralph Loop paper found that "fresh-context-per-iteration agents outperform continuous agents because each iteration allocates full cognitive budget to the current state."

**Consider:** Respawning the coding agent fresh with a compressed summary of its previous work + the review feedback, rather than resuming the full accumulated session. The tradeoff: fresh context vs. warm file knowledge. Worth measuring during dogfood.

#### Hotspot 2: The `/implement-story` Orchestrator Accumulation

The orchestrating agent (not the subagents, but the parent running the command) holds results from every gate sequentially:

```
Gate 0 output → Gate 1 output → Gate 2 output → Gate 3 output (possibly 200+ lines of review)
→ Gate 3.5 drift processing → Gate 4 output → Gate 4.5 output → Gate 5 output
```

By Gate 5 (docs), the orchestrator has the full output of 7 previous gates in its context window. Add fix loops (each adding a full review + coding cycle), and the orchestrator may be working with degraded attention by the final gates.

**Mitigation opportunity:** After each gate passes, the orchestrator could compress the previous gate's output to a single status line: `Gate 3: PASS (1 iter, Small drift: DEV-001 auto-amended)`. Full details are already persisted in subagent outputs and the drift-log. The orchestrator only needs the decision (PASS/FAIL/PAUSE) and key metadata to continue.

#### Hotspot 3: The `/implement-spec` Multi-Story Orchestrator

After each `/implement-story` completes, the parent `/implement-spec` orchestrator receives the full summary report. After 5 stories, it has 5 detailed reports. The execution state file (`.writ/state/execution-{timestamp}.json`) already stores per-story status — this could serve as the persistent memory while the orchestrator retains only summary lines.

**Current risk level: LOW.** The per-story summaries are compact (~15 lines each). The `/implement-spec` orchestrator's main job is sequencing and error handling, not deep reasoning about story content. This becomes a concern only at 10+ stories.

### Correction 3: "AGENTS.md is a strategic gap" — OVERSTATED

**Original claim:** Not having AGENTS.md is a strategic blind spot.

**Reality:** Writ is explicitly Cursor-native. Its commands use `SwitchMode`, `AskQuestion`, and `Task` — all Cursor-specific tools. The roadmap already has an adapter layer for other platforms. AGENTS.md is useful *only once adapters exist* — without the adapter layer, Writ's commands literally cannot execute outside Cursor.

**Revised:** AGENTS.md generation should be coupled to the adapter layer work, not a standalone Phase 2 item. It's a *future* consideration, not a current gap.

### Revised Priority Stack

Given the corrections, the actual priority order changes significantly:

| # | Item | Type | Effort | Why |
|---|------|------|--------|-----|
| 1 | Fix ghost `best-practices.md` reference | Bug fix | XS | Wastes context, reduces trust in instructions |
| 2 | Evaluate coding agent resume vs. fresh spawn | Architecture | S | Highest-risk context pattern; needs dogfood measurement |
| 3 | Add orchestrator context compression guidance to `/implement-story` | Enhancement | S | Prevent attention degradation in long pipelines |
| 4 | Scope governance (30% file threshold) in coding agent | Enhancement | S | Validated by Delegated Reasoning paper; complements existing scope flags |
| 5 | Error taxonomy collection in `/refresh-command` | Enhancement | S | Systematizes the learning loop; `/refresh-command` already scans for patterns |
| 6 | AGENTS.md generation | Strategic | M | Coupled to adapter layer, not standalone |

Items removed from original recommendations:
- ~~Add Project Information to writ.mdc~~ — Already in command files where it belongs
- ~~Add Conventions section to writ.mdc~~ — Already in command files
- ~~Add Boundaries to writ.mdc~~ — Already in Self-Dogfooding section
- ~~Add Definition of Done to writ.mdc~~ — Already in each command file
- ~~Context engineering guidance in system-instructions.md~~ — Belongs in orchestrating commands, not always-applied rules
- ~~Persistent session memory~~ — Speculative; wait for dogfood data on actual problems

### The Real Question for writ.mdc

The original research asked "what should be in the rules file?" The better question is: **"What must every interaction know, regardless of which command is running?"**

The current `writ.mdc` answers this correctly:
- Identity (Writ personality, critical thinking stance)
- File organization (where things go)
- Interaction tool selection (AskQuestion vs. Plan Mode)
- Session orientation (what to show when no command is given)
- Self-dogfooding context (for the writ repo only)

Everything else is command-specific and correctly lives in command files. The thin rule IS the right design. The only fix needed is the broken reference.

---

## Sources

### Taxonomies and Empirical Studies
- "Beyond the Prompt: An Empirical Study of Cursor Rules" — arXiv MSR 2026: https://arxiv.org/html/2512.18925v3
- "Building AI Coding Agents for the Terminal" (OpenDev) — arXiv 2026: https://arxiv.org/html/2603.05344v1

### Context Engineering
- Anthropic — "Effective Context Engineering for AI Agents": https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Morph — "Context Engineering: The Complete Guide": https://www.morphllm.com/context-engineering
- Eric Broda — "Minimum Viable Context": https://www.linkedin.com/posts/ericbroda_minimum-viable-context-activity-7430990796297781248-qiO8

### AGENTS.md and Rule Standards
- AGENTS.md Official Specification: https://agents-md.org
- Blake Crosley — "AGENTS.md Patterns: What Actually Changes Agent Behavior": https://blakecrosley.com/blog/agents-md-patterns
- Big Hat Group — "AGENTS.md Guide: The Universal Config File": https://www.bighatgroup.com/blog/agents-md-guide-enterprise-ai-coding/
- VibeMeta — "AGENTS.md vs CLAUDE.md vs .cursorrules": https://vibemeta.app/blog/agents-md-vs-claude-md-vs-cursorrules-2026
- DevTk — "The Complete Guide to AI Coding Rules": https://devtk.ai/en/blog/complete-guide-cursorrules/
- Hui Huang — "What CLAUDE.md, Cursor Rules, and AGENTS.md Are Really For": https://medium.com/@hui.huang_50580/what-claude-md-cursor-rules-and-agents-md-are-really-for-b56b3ca8a525

### Agent Architecture and Orchestration
- Mikhail Rogov — "Why Your AI Orchestrator Should Never Write Code": https://pub.towardsai.net/why-your-ai-orchestrator-should-never-write-code-a1b5d1a2807d
- Dzianis Vashchuk — "Vibe Engineering: Reflection — A Completion Verification Layer": https://medium.com/@dzianisv/vibe-engineering-reflection-a-completion-verification-layer-for-autonomous-ai-coding-agents-deb193d5a848
- Blake Crosley — "The Ralph Loop: How I Run Autonomous AI Agents Overnight": https://blakecrosley.com/blog/ralph-agent-architecture
- Self-Improving AI Agent Framework: https://github.com/rselvaguru/selfimprovingaiagent
- SpecWeave — Claude Code Architecture: https://spec-weave.com/docs/overview/claude-code-architecture/
- AIAgentsKit — "Agentic AI Frameworks: The Complete Guide 2026": https://aiagentskit.com/blog/agentic-ai-frameworks/

### Practical Workflow Guides
- Codegen — "How to Build Agentic Coding Workflows That Actually Ship": https://codegen.com/blog/how-to-build-agentic-coding-workflows/
- Abdus Muwwakkil — "Agentic Coding Best Practices 2026": https://abdus-muwwakkil.medium.com/agentic-coding-best-practices-fc167be3f7d5
- Developer Toolkit — "Best Practices for AI-Assisted Development": https://developertoolkit.ai/en/shared-workflows/best-practices/
- Rephrase-it — "How to Write Prompts for Cursor, Windsurf, and AI Code Editors in 2026": https://rephrase-it.com/blog/how-to-write-prompts-for-cursor-windsurf-and-ai-code-editors
- Ran Isenberg — "Agentic AI Prompting: Best Practices for Smarter Vibe Coding": https://ranthebuilder.cloud/blog/agentic-ai-prompting-best-practices-for-smarter-vibe-coding/
- Spark Agents — "Coding with AI: A Practical Workflow": https://www.sparkagents.com/blog/coding-with-ai

### Persistent Memory
- Sourabh Sharma — "Persistent Memory for AI Coding Agents": https://medium.com/@sourabh.node/persistent-memory-for-ai-coding-agents-an-engineering-blueprint-for-cross-session-continuity-999136960877
- Maisum Hashim — "The Claude Code Memory Crisis": https://www.maisumhashim.com/blog/claude-code-memory-crisis-persistent-context-systems
- Beam — "AI Agent Memory Management": https://getbeam.dev/blog/ai-agent-memory-management.html

### Previous Writ Research
- Writ Evolution Research (2026-03-13): `.writ/research/2026-03-13-writ-evolution-research.md`
- gStack Analysis Research (2026-03-14): `.writ/research/2026-03-14-gstack-analysis-research.md`
