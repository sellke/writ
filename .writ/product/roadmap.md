# Writ — Product Roadmap

> Based on Product Contract: 2026-02-27
> Last Updated: 2026-03-14
> Cadence: Steady — ongoing improvement alongside real projects, compounding over months

---

## Phase 1: Foundation (4-6 weeks)

**Goal:** Eliminate the biggest friction points — ceremony overhead and spec drift — while introducing the learning loop that makes everything else compound.

**Status:** 6/7 spec stories complete. All command files and agent modifications written. Structural validation passes. **Dogfooding is the remaining gate** — see `.writ/specs/2026-02-27-phase1-foundation/validation-report.md`.

### Success Criteria

- `/prototype` used on 5+ real changes with noticeably less friction than full pipeline
- Spec-healing catches and resolves at least 3 real drift incidents without manual intervention
- `/refresh-command` produces at least 2 meaningful command improvements from actual use
- Overall time-from-idea-to-shipped-feature decreases vs. current Writ v1

### Features

- [~] **`/prototype` command** — Lightweight execution for small-to-medium changes `Effort: M` — **Implemented, awaiting dogfood**
  - Reduced gate set: arch-check (optional) → code → lint → quick-review
  - Auto-detection heuristic: suggests `/prototype` vs. `/implement-story` based on change scope
  - Escape hatch: can escalate to full pipeline mid-flight if complexity warrants
  - Spec: Story 1 ✅ | Command file: `commands/prototype.md` (347 lines)
  - Dogfood needed: run on a real small change, measure < 5 min wall-clock target

- [~] **Tiered spec-healing agent** — Self-correcting pipeline `Effort: L` — **Implemented, awaiting dogfood**
  - Deviation detection: compare implementation against spec contract at each gate
  - Severity classification: small (naming, minor API shape) / medium (scope expansion, new dependency) / large (wrong approach, constraint violation)
  - Small: auto-amend spec, log change, continue
  - Medium: flag for post-implementation review, continue with warning
  - Large: pause pipeline, surface conflict, wait for human decision
  - Drift report: generated at end of every `/implement-story` run
  - Spec: Story 2 ✅ | Agent modified: `agents/review-agent.md` (+171 lines)
  - Dogfood needed: ≥3/5 real drift detections, zero false positives

- [~] **`/refresh-command` command** — The learning loop `Effort: M` — **Implemented, awaiting dogfood**
  - Scans a command-initiated thread (agent transcript or chat history)
  - Identifies: what worked, what caused friction, what was wrong, what was missing
  - Proposes specific amendments to the command file
  - Local-first: changes land in project's copy (`.cursor/commands/` or equivalent)
  - Promotion review: suggests which improvements are universal enough to upstream
  - Generates a changelog entry for the refinement
  - Spec: Stories 4+5 ✅ | Command file: `commands/refresh-command.md` (1047 lines)
  - Dogfood needed: ≥1 actionable improvement per command analyzed, bootstrap self-refresh

- [x] **`/plan-product` gstack enhancement** — Aspirational framing and opinionated posture `Effort: S` ✅ 2026-03-14
  - Planning posture selection (EXPANSION / HOLD / REDUCTION) before discovery
  - Mandatory premise challenge as opening move
  - Dream State Mapping for long-horizon thinking
  - Failure surface analysis and architecture diagrams in contracts
  - Opinionated recommendation format throughout ("I recommend X because Y")
  - Research: `.writ/research/2026-03-14-gstack-analysis-research.md`
  - Decision: DEC-006

### Technical Foundation

- [~] Deviation detection logic for spec-healing (usable across commands) — **Implemented, awaiting dogfood**
- [~] Thread scanning capability for `/refresh-command` — **Implemented, awaiting dogfood**
- [~] Command overlay system: project-local commands override Writ core when present — **Implemented** (Story 6 ✅)

### Validation Targets

- Use Writ to build Writ: every Phase 1 feature goes through the pipeline
- At least one external project (ioyoux or nsemble) uses `/prototype` and `/refresh-command`
- Measure: time saved per feature, drift incidents caught, commands refined

---

## Phase 2: Reach & Autonomy (2-4 months)

**Goal:** Extend agent capabilities beyond file operations. Build the skill and memory layer. Close remaining automation gaps.

### Success Criteria

- PR agent eliminates manual PR creation for 90%+ of pipeline completions
- At least 3 MCP-powered agent capabilities in active use
- Skill system has 5+ encoded competences that persist across sessions
- Cross-project patterns improve coding agent output measurably

### Features

- [ ] **PR agent** — Automated PR creation after pipeline completion `Effort: M`
  - Structured PR description: links to spec, test results, coverage delta, drift report
  - Auto-labels: based on spec category and change scope
  - Draft vs. ready: based on pipeline result (all gates pass = ready, warnings = draft)

- [ ] **MCP integration points** — External tool access for agents `Effort: M`
  - Browser automation: visual QA, deployment verification
  - Database access: migration validation, data integrity checks
  - Deployment APIs: staging deploy, smoke test, rollback
  - Framework for adding new MCP capabilities without modifying core commands

- [ ] **Skill system** — Persistent agent competences `Effort: L`
  - Skill format: structured markdown files in `.writ/skills/`
  - Skill acquisition: extracted from successful patterns via `/refresh-command` and cross-project analysis
  - Skill application: agents load relevant skills based on task context
  - Skill versioning: skills improve over time, old versions archived

- [ ] **Cross-project pattern extraction** — Learning across projects `Effort: L`
  - Pattern detection: common review findings, recurring drift types, successful approaches
  - Pattern encoding: structured format that agents can consume
  - Feedback loop: patterns feed into coding agent prompts to prevent repeat mistakes
  - Privacy-aware: patterns are abstracted, no project-specific code leaks across boundaries

- [ ] **`/retro` command** — Git-based retrospective with gstack-inspired depth `Effort: M`
  - Git-based metrics: commits, LOC, test ratio, session detection, streaks
  - Team-aware analysis with specific, commit-anchored praise
  - Persistent JSON snapshots in `.writ/retros/` with trend comparison
  - Ship of the week + tweetable summary
  - Integration with Writ specs: "Specs completed this period"
  - Auto-detect timezone and default branch (not hardcoded)

- [ ] **`/ship` command** — Unified shipping workflow (branch → PR) `Effort: M`
  - Merge origin/default-branch before tests
  - Run test suites (auto-detect test runner from project)
  - Pre-landing diff review (lightweight checklist, not full `/review`)
  - Bisectable commit splitting (infra → models → logic → version bump)
  - Auto-generate PR body from commits/diff
  - Push and open PR — non-interactive by default, momentum over ceremony
  - Sits between `/implement-story` and `/release`

- [ ] **Standalone `/review` command** — Pre-landing code review `Effort: S`
  - Error & rescue map: method → what fails → exception class → rescued? → user sees
  - Shadow path tracing: happy, nil input, empty input, upstream error
  - Interaction edge cases: double-click, navigate-away, stale state, back button
  - Failure modes registry with critical gap detection (RESCUED=N, TEST=N, USER SEES=Silent)
  - Mandatory ASCII diagrams for non-trivial flows

- [ ] **Enhanced error mapping in `/create-spec`** — Failure-aware specs `Effort: S`
  - Error & rescue map as required section in technical sub-specs
  - Shadow paths for critical data flows
  - Interaction edge cases for user-facing features

### Dependencies

- Phase 1 `/refresh-command` operational and producing useful refinements
- Phase 1 spec-healing generating drift reports that inform pattern detection
- MCP server infrastructure available in target platforms

---

## Phase 3: Intelligence (6+ months)

**Goal:** Agents that genuinely improve through use. Advanced delegation. The framework becomes a learning system, not just an execution system.

### Features

- [ ] **Self-improving agent behaviors** — Adaptive agent prompts `Effort: XL`
  - Review feedback → coding agent improvement loop
  - Per-project agent tuning: agents adapt to codebase patterns and conventions
  - Confidence calibration: agents learn when to proceed vs. when to ask for help
  - Anti-pattern detection: agents flag approaches they've seen fail before

- [ ] **Advanced delegation** — Agent autonomy `Effort: XL`
  - Sub-agent spawning: primary agents can delegate subtasks
  - Coordination: parallel sub-agent work with dependency awareness
  - Escalation: sub-agents can escalate to parent agent or human
  - Task breakdown: agents decompose complex work without human micro-management

- [ ] **Promotion pipeline** — Local → upstream flow `Effort: M`
  - Review process for graduating local command refinements to Writ core
  - Automated diff generation: shows exactly what changed and why
  - Impact assessment: how many projects would benefit from the change
  - PR generation: auto-creates upstream PR with context and rationale

- [ ] **Adaptive context loading** — Context window management `Effort: L`
  - Progressive loading: agents receive only relevant context, expanding as needed
  - Command compression: `/refresh-command` also optimizes commands for token efficiency
  - Dynamic spec-lite: context-aware summaries that expand sections relevant to current task
  - Smart agent prompts: load skills, patterns, and context based on task signature

- [ ] **Browser QA integration** — Diff-aware visual testing `Effort: L`
  - Analyze git diff → identify affected routes → auto-test them
  - Screenshot comparison and console error detection
  - Integration with Cursor MCP browser tools (or equivalent)
  - Route-aware test generation from spec

### Market Position

- Writ is the reference methodology for AI-assisted development
- "Commands that improve through use" is a unique and defensible differentiator
- Community contributions (if any) flow through the promotion pipeline naturally

---

## Effort Sizing

| Size | Duration | Example |
|------|----------|---------|
| **XS** | 1-2 days | Bug fix, documentation update |
| **S** | 3-5 days | `/review` command, `/plan-product` enhancement, error mapping in specs |
| **M** | 1-2 weeks | `/prototype` command, `/retro`, `/ship`, PR agent, `/refresh-command` |
| **L** | 3-4 weeks | Spec-healing agent, skill system, cross-project patterns |
| **XL** | 1+ months | Self-improving agents, advanced delegation |

---

## Design Principles (Apply to Every Phase)

1. **Adaptive ceremony** — Every feature must justify its weight. More process only when more process is warranted.
2. **Local-first** — Improvements land in the project first. Upstream promotion is optional, never forced.
3. **Dogfood everything** — Use Writ to build Writ. Every feature goes through the pipeline.
4. **Commands are the unit** — Learning, improvement, distribution, customization all operate on commands.
5. **Aplomb** — Agents should handle complexity with grace, not grind through checklists.
6. **Opinionated by default** — Lead with the recommendation, explain why, then offer alternatives. Judgment, not menus.
