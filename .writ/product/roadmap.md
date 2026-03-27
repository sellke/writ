# Writ — Product Roadmap

> Based on Product Contract: 2026-02-27
> Last Updated: 2026-03-27
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

## Phase 3a: Context Engine (2-3 weeks) ✅ Complete — v0.9.0

**Goal:** Make spec context flow intelligently to every pipeline agent — the right context, to the right agent, at the right moment — so that the quality ceiling of AI-generated code is determined by spec quality, not context window luck.

**Status:** Complete. All 5 stories implemented. Spec: `.writ/specs/2026-03-27-context-engine/`.

### Features

- [x] **Per-story context hints** — `## Context for Agents` section in story files `Effort: S` ✅
  - Indexes into full spec: error map rows, shadow paths, business rules, experience design elements
  - Generated by `user-story-generator` agent during `/create-spec`
  - Format reference: `.writ/docs/context-hint-format.md`

- [x] **"What Was Built" records** — Post-completion summary appended to story files `Effort: S` ✅
  - Sourced from review agent output (third-party verification, not self-reports)
  - Downstream coding agents receive these via `dependency_wwb_context` parameter
  - Format reference: `.writ/docs/what-was-built-format.md`

- [x] **Agent-specific spec views** — Restructure spec-lite.md with labeled sections `Effort: S` ✅
  - Three sections: `## For Coding Agents`, `## For Review Agents`, `## For Testing Agents`
  - Line budget: 35/35/30 — same <100 line total, better targeting per agent role

- [x] **UAT plan generation** — `/create-uat-plan` command `Effort: M` ✅
  - Generates test scenarios from acceptance criteria, error maps, shadow paths, edge cases
  - Enriched with "What Was Built" implementation details
  - Output: `.writ/specs/{spec}/uat-plan.md`

- [x] **Context routing improvements** — Full routing table in `/implement-story` `Effort: M` ✅
  - Each gate agent receives tailored spec-lite section + fetched context hints
  - Graceful degradation for legacy specs without agent-specific sections

---

## Phase 3b: Ralph Loop Orchestration (3-4 weeks) ✅ Complete — v0.10.0

**Goal:** Enable "plan it, walk away, come back to PRs" through Ralph loop orchestration — Cursor-based planning, CLI-based execution, file-based state management across fresh-context iterations.

**Status:** Complete. All 4 stories implemented. Spec: `.writ/specs/2026-03-27-ralph-loop-orchestration/`.

**Architecture evolved** from the original roadmap concept (progressive autonomy thresholds within `/implement-story`) to the [Ralph Wiggum technique](https://ghuntley.com/ralph/) — a CLI bash loop with fresh context per iteration, which research found outperforms continuous agents. Key design shift: human moves from *in the loop* to *on the loop*.

### Features

- [x] **`/ralph plan` command** — Cross-spec execution planning (Cursor) `Effort: M` ✅
  - Scans non-complete specs, resolves intra-spec and cross-spec dependencies
  - Codebase assessment with structured findings
  - Generates execution plan, CLI handoff artifacts, and initialized state file
  - Plan is disposable — regenerate anytime from current codebase reality

- [x] **CLI-adapted story pipeline** — `PROMPT_build.md` template `Effort: M` ✅
  - Orient → implement → validate → commit, with 3-iteration fix loop
  - Back pressure: tests + lint as quality gates (no separate review agent in CLI mode)
  - State update protocol: when and how the CLI agent writes `ralph-*.json`
  - Gate mapping docs: `.writ/docs/ralph-cli-pipeline.md`

- [x] **Loop script + configuration** — `scripts/ralph.sh` `Effort: M` ✅
  - Plan/build mode selection, max iterations, config-driven CLI agent invocation
  - Git push after each successful iteration
  - Stop conditions: max iterations, all complete, all blocked, stop-on-failure, environment error
  - 5 new Ralph config keys in `.writ/docs/config-format.md`

- [x] **`/ralph status` command** — Monitoring and Cursor re-entry `Effort: S` ✅
  - Reads `.writ/state/ralph-*.json`, presents progress dashboard
  - Surfaces blockers and escalation reports in plain language
  - Phase detection (planned, executing, paused, escalated, complete)
  - Next-step guidance for each phase

### Key Design Decisions

- **Fresh context per iteration** (not resumed context) — research finding: fresh-context agents outperform continuous agents
- **CLI for execution** (not Cursor) — headless, automated, fresh context natively
- **One story per iteration** (not one task) — stories are the natural unit of shippable value
- **Dependency graph + assessment** (not pure "choose most important") — safety rails for existing codebases

---

> **Beyond Phase 3:** Cross-project learning corpus, self-improving context routing, multi-repo orchestration, notification integrations (Slack/webhooks for escalation), and autonomous refactoring are longer-horizon opportunities.

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
