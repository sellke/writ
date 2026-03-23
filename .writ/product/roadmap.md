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

> **Beyond Phase 2:** A separate product extension will pursue skill-based automation, self-improving agents, advanced delegation, cross-project pattern extraction, and autonomous loops. That work builds on Writ's workflow foundation but has its own scope, roadmap, and identity.

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
