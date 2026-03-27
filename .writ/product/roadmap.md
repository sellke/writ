# Writ — Product Roadmap

> Based on Product Contract: 2026-02-27
> Last Updated: 2026-03-22
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

## Phase 2: Reach (2-4 months)

**Goal:** Close remaining automation gaps in the workflow. Every step from idea to shipped PR has a Writ command with clear boundaries.

### Success Criteria

- `/ship` eliminates manual PR creation for 90%+ of pipeline completions
- `/ship` + `/review` + `/retro` in regular use across projects
- End-to-end workflow (plan → spec → implement → review → ship → retro → release) has zero manual gaps

### Features

- [~] **`/ship` command** — Unified shipping workflow (branch → PR) `Effort: M` — **Implemented, awaiting dogfood**
  - Absorbs the PR agent concept — one command owns the full "branch to merged" path
  - Merge origin/default-branch before tests (optional `--test` flag)
  - Bisectable commit splitting with approval gate (infra → models → logic → tests → version)
  - Structured PR body: summary, changes, spec reference, test results, spec health, drift report, review notes
  - Auto-labeling, draft/ready detection, dry-run mode
  - Convention detection with `.writ/config.md` persistence
  - Command file: `commands/ship.md` (520 lines)
  - Dogfood needed: run on a real feature branch, verify commit splitting and PR quality

- [~] **Standalone `/review` command** — Pre-landing code review `Effort: S` — **Implemented, awaiting dogfood**
  - Error & rescue map: method → what fails → exception class → rescued? → user sees
  - Shadow path tracing: happy, nil input, empty input, upstream error
  - Interaction edge cases: double-click, navigate-away, stale state, back button
  - Failure modes registry with critical gap detection (RESCUED=N, TEST=N, USER SEES=Silent)
  - Mandatory ASCII diagrams for non-trivial flows
  - Integration with `/ship`: saves report to `.writ/state/`, `/ship` reads it into PR body
  - Command file: `commands/review.md` (199 lines)
  - Dogfood needed: run on a real diff, verify failure mode detection quality

- [~] **`/retro` command** — Git-based retrospective with gstack-inspired depth `Effort: M` — **Implemented, awaiting dogfood**
  - Git-based metrics: commits, LOC, test ratio, session detection, streaks
  - Team-aware analysis with specific, commit-anchored praise
  - Persistent JSON snapshots in `.writ/retros/` with trend comparison
  - Ship of the week + tweetable summary
  - Integration with Writ specs: "Specs completed this period"
  - Auto-detect timezone and default branch (not hardcoded)
  - Command file: `commands/retro.md` (199 lines)
  - Dogfood needed: run on a real 7-day period, verify session detection and pattern quality

- [~] **Enhanced error mapping in `/create-spec`** — Failure-aware specs `Effort: S` — **Implemented, awaiting dogfood**
  - Error & rescue map as required section in technical sub-specs
  - Shadow paths for critical data flows
  - Interaction edge cases for user-facing features
  - Shared format with `/review` enables plan-vs-actual comparison
  - Implemented in: `commands/create-spec.md` (lines 504-530)
  - Dogfood needed: create a spec with data flow features, verify error mapping tables are generated

### Dependencies

- Phase 1 `/refresh-command` operational and producing useful refinements
- Phase 1 spec-healing generating drift reports

---

## Phase 3a: Context Engine (2-3 weeks)

**Goal:** Make spec context flow intelligently to every pipeline agent — the right context, to the right agent, at the right moment — so that the quality ceiling of AI-generated code is determined by spec quality, not context window luck.

### Success Criteria

- Coding agents produce code that handles error cases described in specs without explicit reminders
- Review agents catch business rule violations that are specified but would currently be missed
- Story 3's implementation correctly builds on what Stories 1-2 actually produced
- No increase in prompt length — better context, not more context
- UAT plans generated from specs enable human validation without reading implementation code

### Features

- [ ] **Per-story context hints** — `## Context for Agents` section in story files `Effort: S`
  - Indexes into full spec: error map rows, shadow paths, business rules, experience design elements
  - Generated by `user-story-generator` agent during `/create-spec`
  - Orchestrator pulls targeted context from full spec based on hints
  - Backward compatible: when absent, falls back to current behavior (pass full spec-lite)

- [ ] **"What Was Built" records** — Post-completion summary appended to story files `Effort: S`
  - Sourced from review agent output (more reliable than coding agent self-report)
  - Structure: files created/modified, implementation decisions, error handling, test count
  - Subsequent stories' coding agents receive these from completed dependency stories
  - Gives cross-story continuity — Story 3 knows what Stories 1-2 actually produced

- [ ] **Agent-specific spec views** — Restructure spec-lite.md with labeled sections `Effort: S`
  - `## For Coding Agents` — implementation approach, error maps, file scope
  - `## For Review Agents` — acceptance criteria, business rules, experience design
  - `## For Testing Agents` — success criteria, shadow paths, edge cases
  - Same <100 line budget, better targeting per agent role
  - Orchestrator passes relevant section to each agent instead of whole file

- [ ] **UAT plan generation** — Human-readable test scenarios from specs `Effort: M`
  - Generated after stories complete (new `/create-uat-plan` command or integrated into `/ship`)
  - Derives scenarios from acceptance criteria, error maps, shadow paths
  - Format: preconditions, steps, expected result, pass/fail checkbox
  - Lives at `.writ/specs/{spec}/uat-plan.md`
  - Bridges "AI says it works" and "human confirmed it works"

- [ ] **Context routing improvements** — Update all agent prompt templates `Effort: M`
  - Coding agent receives targeted error maps, not summaries
  - Review agent receives full business rules section
  - Testing agent receives structured edge cases
  - All agents receive "What Was Built" from dependency stories

### Dependencies

- Phase 1 and Phase 2 dogfooding complete — real context pain points inform design
- At least one full spec run on a real project to validate the context flow gaps

### Validation Targets

- Run the context engine on a complex spec (5+ stories with cross-dependencies)
- Measure: review agent catch rate for business rule violations improves by >30%
- Measure: coding agent error handling matches spec without explicit prompting
- Manual UAT execution on at least 2 features to validate checklist quality

---

## Phase 3b: Autonomous Execution (3-4 weeks)

**Goal:** Enable "describe it, walk away, come back to a PR" workflow through Ralph loop orchestration with progressive autonomy thresholds and external state management.

### Success Criteria

- Autonomous runs produce PRs with same quality as supervised runs
- Escalation to human happens <10% of runs (most succeed autonomously)
- External state enables overnight runs that survive context window resets
- Users opt into autonomous mode; supervised mode remains default

### Features

- [ ] **Ralph loop wrapper** — Outer loop around implement-story pipeline `Effort: M`
  - Wraps the 6-gate pipeline (arch-check → code → lint → review → test → docs)
  - Iteration tracking with external state files (`.writ/state/loop-N.json`)
  - Progressive autonomy thresholds: 3 soft iterations → meta-rethink → escalation to human
  - Stop conditions: max iterations, token budget, cost threshold
  - Verification gate: loop continues until review agent PASS + tests green

- [ ] **External state management** — Cross-context-window persistence `Effort: S`
  - `.writ/state/autonomous-run-{timestamp}.json` tracks: iteration count, agent outputs, review findings, escalation triggers
  - State survives context window resets — agents can run overnight
  - Checkpoint after every gate completion
  - Resumable from last checkpoint if interrupted

- [ ] **Progressive autonomy thresholds** — Escalation logic `Effort: S`
  - Soft iterations (1-3): coding agent → review agent → coding agent (standard feedback loop)
  - Meta-rethink (iteration 4): "Step back, reconsider approach, try different strategy"
  - Human escalation (iteration 5+): "I'm stuck, here's what I tried, here's the blocker"
  - Configurable per-project in `.writ/config.md`

- [ ] **"Come back to a PR" mode** — Full autonomous execution `Effort: M`
  - User runs `/implement-story story-3 --autonomous`
  - Pipeline runs without human gates, external state tracks progress
  - On success: auto-creates PR with structured body (summary, changes, test results, drift report)
  - On escalation: notifies user with status report, waits for guidance
  - On failure: detailed failure report with logs, state files preserved for debugging

- [ ] **Autonomous mode configuration** — Project-level settings `Effort: S`
  - `.writ/config.md` section for autonomous execution preferences
  - Autonomy level: `supervised` (default), `progressive` (escalate after 3), `full` (no escalation, hard fail only)
  - Stop conditions: max iterations (default: 5), max tokens (default: 100K), max cost (default: $5)
  - Notification preferences: Slack webhook, email, GitHub issue on escalation

### Dependencies

- Phase 3a (Context Engine) complete and validated
- External state management proven with at least 5 real autonomous runs
- Review agent reliability >90% (low false positive rate on PASS/FAIL decisions)

### Validation Targets

- 10 autonomous runs on real features (mix of simple and complex)
- Success rate >80% (produce mergeable PRs without human intervention)
- Escalation cases are legitimate blockers, not solvable issues
- External state files enable resume after context window reset

---

> **Beyond Phase 3:** Cross-project learning corpus, self-improving context routing, multi-spec parallelism, and autonomous refactoring are longer-horizon opportunities.

---

## Effort Sizing

| Size | Duration | Example |
|------|----------|---------|
| **XS** | 1-2 days | Bug fix, documentation update |
| **S** | 3-5 days | `/review` command, `/plan-product` enhancement, error mapping in specs |
| **M** | 1-2 weeks | `/prototype` command, `/retro`, `/ship`, PR agent, `/refresh-command` |
| **L** | 3-4 weeks | Spec-healing agent |
| **XL** | 1+ months | (reserved for future product extension) |

---

## Design Principles (Apply to Every Phase)

1. **Adaptive ceremony** — Every feature must justify its weight. More process only when more process is warranted.
2. **Local-first** — Improvements land in the project first. Upstream promotion is optional, never forced.
3. **Dogfood everything** — Use Writ to build Writ. Every feature goes through the pipeline.
4. **Commands are the unit** — Learning, improvement, distribution, customization all operate on commands.
5. **Aplomb** — Agents should handle complexity with grace, not grind through checklists.
6. **Opinionated by default** — Lead with the recommendation, explain why, then offer alternatives. Judgment, not menus.
