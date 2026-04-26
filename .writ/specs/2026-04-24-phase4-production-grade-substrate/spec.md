# Phase 4 — Production-Grade Substrate

> **Status:** Completed ✅
> **Created:** 2026-04-24
> **Completed:** 2026-04-26
> **Owner:** @adam (default — set automatically; team-readiness seed per Story 2)
> **Phase:** 4 (Production-Grade Substrate)
> **Roadmap:** [.writ/product/roadmap.md](../../product/roadmap.md) → Phase 4
> **Anchored ADRs:** [ADR-005](../../decision-records/adr-005-knowledge-substrate-markdown-over-database.md), [ADR-006](../../decision-records/adr-006-non-degrading-destination.md), [ADR-007](../../decision-records/adr-007-team-audience-sequencing.md), [ADR-008](../../decision-records/adr-008-spec-as-team-contract-moat.md)
> **Source research:** [.writ/research/2026-04-24-writ-vs-gstack-rigor-comparison.md](../../research/2026-04-24-writ-vs-gstack-rigor-comparison.md) (Findings 7–9 + addendum)
> **Changelog:** [CHANGELOG.md](CHANGELOG.md)

---

## Specification Contract

**Deliverable:** Five dual-use substrate features that strengthen Writ's non-degradation property — knowledge ledger, SKILL.md template generation, preamble enforcement, eval Tier 1 static checks, and a spec frontmatter `owner:` field. Every feature passes the dual-use test (per ADR-007): each pays off for solo developers today AND prepares Writ for the small-team-collaboration audience pivot when its trigger event arrives.

**Origin:** Phase 4 of the refreshed roadmap, written after the GStack rigor comparison and the four strategic ADRs (005–008) it produced.

**Must Include:**
- A plain-text knowledge layer at `.writ/knowledge/` with frontmatter schema, authoring command, agent context-loading hook, and 5–10 backfilled high-value entries (per ADR-005)
- A `SKILL.md` generator driven by a single-source-of-truth manifest, with a CI check that fails when generated output diverges from committed file
- A shared command preamble that eliminates duplicated standing instructions across the command surface, with enforcement that every command references it
- A bash-based static eval (Eval Tier 1) covering required sections, anti-sycophancy phrasing, broken references, and length sanity — run locally and in CI
- A spec frontmatter `owner:` field defaulting to git committer, present on every spec created post-ship

**Hardest Constraint:** Solo-maintainer capacity. Per the [research addendum's](../../research/2026-04-24-writ-vs-gstack-rigor-comparison.md) Risk #1, total Phase 4 effort must stay within ~5–9 days of focused work. Story scope must be defended against creep — anything beyond the dual-use test (per [ADR-007](../../decision-records/adr-007-team-audience-sequencing.md)) belongs in Phase 5 or the parking lot.

### 🎯 Experience Design

This spec ships methodology infrastructure, not user-facing UI. The "experience" being designed is what an agent or contributor sees when they touch the surface area Phase 4 builds.

- **Entry point — solo developer:** Runs an existing Writ command; the new substrate is invisible until they hit the value moment (an agent loads relevant `.writ/knowledge/` context unprompted; a stale `SKILL.md` is caught before merge; a preamble change propagates everywhere).
- **Entry point — new contributor (today: future-self; tomorrow: teammate):** Clones the repo, reads `.writ/knowledge/README.md`, and orients on conventions in under 30 minutes — the explicit ADR-005 success bar.
- **Happy path:**
  1. Maintainer notes a convention or lesson worth keeping → `/knowledge` writes a conformant entry to the right subdirectory in <60 seconds.
  2. Agent starts a task → orchestrator loads relevant `.writ/knowledge/` subdirectories into context → agent applies conventions without being prompted.
  3. Maintainer edits a command file → CI eval catches a missing required section / banned phrase / broken ref / SKILL.md drift before the PR merges.
- **Moment of truth — solo:** A `SKILL.md`-drift gate fires on a real PR and surfaces a doc that would have shipped wrong. A `/status` invocation shows the maintainer's own name on every active spec.
- **Moment of truth — team-readiness (future):** A second contributor lands on the project, runs eval locally, sees their git name on a new spec they create, reads `.writ/knowledge/` to onboard. Zero additional infrastructure required for any of this.
- **Feedback model:**
  - `/knowledge` → terse confirmation matching `/create-issue` voice (filename + back-to-work).
  - `gen-skill.sh` → quiet on success; structured diff on drift.
  - `eval.sh` → markdown report grouped by check category; non-zero exit on failure.
  - Owner field → silently present in frontmatter; surfaced by `/status` and `/verify-spec`.
- **Error experience:**
  - `/knowledge` invoked outside a Writ project → clear "no `.writ/` directory" message + suggest `/initialize`.
  - Agent's knowledge-loading hook finds no relevant entries → silent no-op, never blocks the task.
  - `gen-skill.sh` finds the manifest malformed → fail with specific YAML error pointing at the offending key.
  - `eval.sh` reports failures → each finding cites the file, line, and check that fired, with a one-line remediation hint.
  - `owner:` field missing on a new spec → `/verify-spec` warns (does not hard-fail) and offers to backfill from `git config user.name`.
- **Empty / first-use states:**
  - `.writ/knowledge/` empty after Story 1 ships → README + 5–10 backfilled entries make the directory feel populated from day one (the junk-drawer-vs-curated bar set by ADR-005's success criteria).
  - Old specs (pre-ship) without `owner:` → `/verify-spec` reports them as "legacy" without warning noise; backfill is opt-in, not required.

### 📋 Business Rules

Drawn directly from ADR-005, ADR-006, ADR-007, and ADR-008. These are the constraints every story must respect.

- **Plain-text + git only.** No databases, no external services, no proprietary formats as source of truth (ADR-005). Any indexing is a derived artifact, not source.
- **Dual-use test (ADR-007).** Every story's spec note must answer: "Does this benefit solo work AND set up team-readiness later?" Items that fail are deferred to Phase 6+ or the parking lot.
- **Substrate moves only.** No team-specific features in this spec — `/review-spec`, multi-developer drift reconciliation, multi-repo orchestration are all explicitly out of scope (ADR-007 deferred list).
- **Knowledge ledger boundaries (ADR-005 mitigation):**
  - `.writ/decision-records/` — architectural choices with serious blast radius (ADR template applies)
  - `.writ/research/` — investigations that produced specific recommendations (research format applies)
  - `.writ/knowledge/` — accumulating, cross-cutting, smaller facts that don't fit either (frontmatter-driven; categorized)
  - The Story 1 README must include a one-page "what goes where" decision tree.
- **Knowledge frontmatter schema (minimum, per ADR-005):** `category`, `tags`, `created`, `related_artifacts` — extensible but these four are required. Schema enforced by `/knowledge` and validated by Story 5's eval.
- **Filename convention:** `YYYY-MM-DD-short-slug.md` — matches `.writ/issues/`, `.writ/research/`, `.writ/decision-records/` (operator already familiar).
- **SKILL.md is a generated artifact post-ship.** Manual edits are prohibited; the manifest is the source of truth. Story 3 must include a header comment in `SKILL.md` declaring this and pointing at the manifest.
- **Preamble references are mandatory.** Story 4 enforces every command file in `commands/` includes a "References" section pointing at `commands/_preamble.md`. Story 5's eval enforces this on every PR.
- **Anti-sycophancy phrasing list extends the Prime Directive.** Story 5's anti-sycophancy check enforces what `system-instructions.md` already inlined (per the [Prime Directive spec](../2026-03-20-prime-directive/spec-lite.md)). The two files (`system-instructions.md` and `cursor/writ.mdc`) must stay in sync — Story 5 verifies this.
- **Owner field defaults to git committer, never enterprise UID.** Solo devs see their own name; teams see whoever ran `git config user.name`. No central directory, no auth, no migration of legacy specs.
- **Adapter neutrality.** All five features must work identically across `adapters/cursor.md`, `adapters/claude-code.md`, `adapters/openclaw.md`. No platform-specific runtime hooks; the integration mechanism is markdown-as-instructions and bash scripts.
- **Self-dogfooding.** Every Phase 4 feature must be exercised on the Writ repo itself before being declared done. The first PR each story produces must demonstrate the feature in its own diff (e.g., Story 1's PR adds backfilled entries; Story 5's PR includes the eval running clean against the full surface).

## Success Criteria

From the roadmap and the anchored ADRs:

1. **Knowledge ledger has ≥10 entries across ≥2 categories within 30 days of shipping** (roadmap Phase 4 success criterion; ADR-005 success criterion).
2. **`SKILL.md` generation eliminates command/agent doc drift** — `bash scripts/gen-skill.sh --dry-run && git diff --exit-code SKILL.md` exits 0 in CI for 60 days post-ship without a manual SKILL.md edit.
3. **Eval Tier 1 catches at least one regression before release within first 60 days** (roadmap criterion). Initial run against the current command/agent suite passes (any pre-existing violations are triaged and fixed as part of Story 5).
4. **Spec `owner:` field present on every spec created post-ship.** `/verify-spec` reports 100% presence on new specs; legacy specs are reported as "legacy" without blocking.
5. **Agent on a fresh task can find and load relevant knowledge entries without the maintainer prompting it** (ADR-005 success criterion). Implementation verified locally; organic confirmation tracked at [`2026-04-26-story-1-knowledge-loading-organic-validation`](../../issues/improvements/2026-04-26-story-1-knowledge-loading-organic-validation.md), recheckable at the 90-day ADR-005 review.
6. **New contributor (or returning future-self after >30 days) can read `.writ/knowledge/` and orient on project conventions in under 30 minutes** (ADR-005 success criterion). Validated by self-test 90 days post-ship.
7. **Zero external dependencies introduced.** No databases, no services, no auth.
8. **Phase 1 features validated in real use** — drift reports demonstrate the pipeline catches genuine deviations (entry condition, not output of this spec; tracked in roadmap).

## Scope Boundaries

### In Scope

- `.writ/knowledge/` directory + README + frontmatter schema + 5–10 backfilled entries
- `commands/knowledge.md` — micro-command for read/write entries (modeled on `/create-issue` for terseness)
- `.writ/manifest.yaml` (or equivalent format — see Implementation Approach for selection rationale) — single source of truth for command/agent metadata
- `scripts/gen-skill.sh` — generator; supports `--dry-run`, `--check`, default modes
- `commands/_preamble.md` — shared standing instructions; referenced by every command
- `scripts/eval.sh` — Tier 1 static checks across command/agent files
- Spec frontmatter `owner:` field — added to `commands/create-spec.md` template; surfaced by `/status` and `/verify-spec`
- Updates to `commands/implement-story.md`, agent files, and adapter docs to load knowledge context and reference the preamble
- `.github/workflows/eval.yml` (or equivalent) wiring `gen-skill.sh --check` and `eval.sh` into CI
- A "what goes where" decision tree distinguishing knowledge from ADRs/research/specs
- Self-dogfood validation as part of each story's Definition of Done

### Out of Scope (deferred per ADR-007's dual-use test, or to Phase 5)

- `/audit` command — Phase 5 (operationalizes the production-grade scorecard)
- `/lessons` micro-command — Phase 5 (`/knowledge` covers the authoring path for now; `/lessons` is mid-flow capture syntactic sugar)
- Per-story scorecards, drift-to-lesson auto-promotion, `/status` health score — Phase 5
- Spec `dependencies:` block, status board across `.writ/specs/` — Phase 5
- `/review-spec`, multi-developer drift reconciliation, multi-repo orchestration — Beyond Phase 5 (deferred until concrete team signal per ADR-007)
- Eval Tier 2 (LLM-as-judge), Tier 3 (E2E) — deferred indefinitely per cost analysis (research addendum, "Skills-Creation Infrastructure")
- SQLite index over `.writ/knowledge/` — explicitly deferred per ADR-005 Option 4; revisit only if grep retrieval becomes measurably inadequate
- Migration of legacy specs to add `owner:` — opt-in only; no backfill script

## Implementation Approach

### Architecture overview

This spec adds three new artifacts and modifies most of the existing ones:

```
NEW
├── .writ/knowledge/                (Story 1)
│   ├── README.md                   (decision tree + schema doc)
│   ├── decisions/                  (small "we chose X because Y")
│   ├── conventions/                (codebase patterns)
│   ├── glossary/                   (domain terminology)
│   └── lessons/                    (postmortem-style learnings)
├── .writ/manifest.yaml             (Story 3 — single source of truth)
├── commands/knowledge.md           (Story 1 — authoring command)
├── commands/_preamble.md           (Story 4 — shared standing rules)
├── scripts/gen-skill.sh            (Story 3 — manifest → SKILL.md)
├── scripts/eval.sh                 (Story 5 — Tier 1 static checks)
└── .github/workflows/eval.yml      (Story 5 — CI gate)

MODIFIED
├── SKILL.md                        (Story 3 — becomes generator output)
├── commands/create-spec.md         (Story 2 — owner field; Story 4 — preamble ref)
├── commands/implement-story.md     (Story 1 — knowledge-loading hook; Story 4 — preamble ref)
├── commands/verify-spec.md         (Story 2 — owner check)
├── commands/status.md              (Story 2 — owner display)
├── commands/{everything-else}.md   (Story 4 — preamble references; Story 5 — required sections)
├── agents/coding-agent.md          (Story 1 — knowledge context input)
├── agents/{other-agents}.md        (Story 4 — preamble references where applicable)
└── adapters/{cursor,claude-code,openclaw}.md (Stories 1, 4 — note new context-loading and preamble conventions)
```

### Story sequencing & parallelism

```
Story 1 (Knowledge Ledger)     Story 2 (Owner Field)     Story 3 (SKILL.md Gen)
        ↓                              ↓                          ↓
        └──────────────────────────────┴────────┬─────────────────┘
                                                ↓
                                       Story 4 (Preamble Enforcement)
                                                ↓
                                       Story 5 (Eval Tier 1)
```

- **Stories 1, 2, 3 are independent** — can run in parallel.
- **Story 4 depends on Story 3** — shares the manifest infrastructure (the manifest's command list is what Story 4's preamble-reference enforcement iterates over).
- **Story 5 depends on Story 4** — one of Story 5's checks verifies "every command references `_preamble.md`" (Story 4's enforcement mechanism). Story 5 also depends on Story 2 (checks for `owner:` field presence on new specs) and Story 3 (checks the manifest is well-formed).

### Manifest format selection

Story 3 needs a single source of truth for command/agent metadata. Three options were considered:

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| YAML manifest (`.writ/manifest.yaml`) | Human-readable, well-supported in bash via `yq`, terse | Adds `yq` dependency for the generator; one more file to keep in sync | **Chosen** — readability wins; `yq` is widely available |
| Frontmatter on each command file | No new file; metadata lives next to behavior | Generator must parse 30+ files per run; harder to do bulk operations | Considered |
| Inline JSON in a script | Zero parsing dependencies | Hostile to humans; defeats the "review in PR" benefit | Rejected |

**Decision:** YAML manifest at `.writ/manifest.yaml`. Schema includes per-command: `name`, `file`, `category`, `purpose`, `tags`, `aliases` (if any). Per-agent: `name`, `file`, `purpose`, `model`. Story 3's technical-spec covers the full schema. If the only system without `yq` is a contributor's machine, the generator falls back to a pure-bash YAML reader for the subset of YAML the manifest uses (no anchors, no flow style).

### Preamble injection mechanism

The research addendum says "injected at command-load time." Cursor (and most current adapters) lacks a clean runtime injection hook. The chosen mechanism is therefore *static reference* enforced by eval:

1. `commands/_preamble.md` holds the shared standing instructions (Plan Mode integrity, todo_write usage, `.writ/` org reminder, AskQuestion vs Plan Mode selection).
2. Every command file ends with a "## References" section that includes a line referencing `_preamble.md`.
3. The orchestrator (`commands/implement-story.md`) and `system-instructions.md` direct agents to read the preamble alongside the command file.
4. Story 5's eval enforces (a) every command file contains the reference and (b) the preamble file exists and is non-empty.

This is honest about the platform constraint while still preventing drift. A future Story (Phase 6+) can add adapter-level pre-load hooks if/when adapter primitives mature.

### Knowledge-loading hook

Per ADR-005's Implementation Notes Step 4: agents load relevant subdirectories at task start. Concretely:

- `commands/implement-story.md` — Step 2 (Context Loading) gains an explicit "Load `.writ/knowledge/` subdirectories matching task domain" sub-step.
- `agents/coding-agent.md` — gains a `knowledge_context` input parameter populated by the orchestrator from grep/keyword matches against the story's `## Context for Agents` block and the file paths it touches.
- `agents/architecture-check-agent.md` — receives `knowledge_context` for `decisions/` and `conventions/` subdirectories specifically.
- `agents/review-agent.md` — receives `knowledge_context` for `lessons/` (so prior failures inform the review).

The selection mechanism is grep-based at v1: orchestrator extracts keywords from the story title, files in scope, and context-hint targets, then greps `.writ/knowledge/` for matches. False-positive load is preferred over false-negative skip (cheap to ignore irrelevant context; expensive to miss relevant context).

### Eval Tier 1 — what it actually checks

Per the research addendum:

| Check | What it verifies | Failure mode |
|---|---|---|
| Required sections | Every command has `## Overview`, `## Invocation`, `## Command Process` (or equivalent — checked against pattern from existing 28 commands) | Lists files missing required sections |
| Anti-sycophancy phrasing | No banned phrases ("Great question!", "Excellent point!", "Absolutely!", etc.) in command/agent files; `system-instructions.md` and `cursor/writ.mdc` Prime Directive sections are byte-identical | Lists offending file:line |
| Broken references | Cross-file links resolve; agent names referenced by commands exist in `agents/`; command names referenced exist in `commands/`; ADR/spec references resolve | Lists broken refs |
| Length sanity | `spec-lite.md` files ≤100 lines; `_preamble.md` ≤80 lines; no command file >2000 lines | Lists files exceeding budget |
| Manifest well-formed (Story 3 dep) | Manifest YAML parses; every command/agent in manifest exists in filesystem; no orphan files | Lists discrepancies |
| Preamble references (Story 4 dep) | Every command file references `commands/_preamble.md` | Lists commands missing reference |
| Owner field (Story 2 dep) | Every spec created on/after ship date has `owner:` in frontmatter | Lists offending specs (legacy specs exempt) |

Output is a markdown report grouped by check; non-zero exit code on any failure. Wired to CI via `.github/workflows/eval.yml`.

### Backfill plan for the knowledge ledger

ADR-005 requires 5–10 high-value backfilled entries to validate the schema before declaring v1 done. Candidates from existing artifacts:

- `decisions/` — Adapter-neutrality conventions; "what goes where" rules; the platform-agnostic tool-naming principle from `agents/*.md`
- `conventions/` — Bash script style (matching `install.sh`, `ralph.sh`); markdown-as-instructions principle; symlink-vs-copy rule from `AGENTS.md`
- `glossary/` — "Spec," "drift log," "shadow path," "context hint," "dual-use test"
- `lessons/` — Lessons from the Context Engine spec's drift log (DEV-007 etc.); the Story 2 verification-vs-implementation overlap pattern from `2026-03-27-context-engine`

Backfill is part of Story 1's Definition of Done.

### Self-dogfooding through the existing pipeline

Per the roadmap's validation target: "Use Writ to build Phase 4 features through the existing pipeline." Each story flows through `/implement-story` (or `/prototype` for the smallest — Story 2). Every PR includes the drift log; the spec is updated if reality diverges. The Story 5 eval ships *clean against the post-ship surface* — meaning Stories 1–4 may surface eval violations that get triaged and fixed within Story 5's scope.

## Cross-Spec Overlap

Scanned non-complete `spec-lite.md` files. Touchpoints, all complementary rather than conflicting:

- **`2026-03-20-prime-directive` (shipped 0.7.0):** Inlined the Prime Directive into `system-instructions.md` and `cursor/writ.mdc`. Story 5's anti-sycophancy phrasing check **enforces** what that spec inlined, and additionally checks the two files stay byte-identical in the Prime Directive section. Complementary.
- **`2026-03-20-file-ownership-boundaries` (shipped 0.8.0):** Added boundary computation to `/implement-story`. No conflict; Story 1's knowledge-loading hook is a separate context-routing concern in the same Step 2.
- **`2026-03-22-suite-quality-polish` (shipped):** Renumbered `/verify-spec` checks. Story 2's owner-field check adds a new check; numbering must continue from current sequence, not reset.
- **`2026-03-27-context-engine` (Phase 3a — shipped 0.9.0):** Established `## Context for Agents` block in story files. Story 1's knowledge-loading hook **reads** that block to determine which knowledge subdirectories to load. Direct dependency, not conflict.

No active in-progress specs overlap.

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Junk-drawer drift in `.writ/knowledge/` (ADR-005 named risk) | Medium | Medium | Frontmatter schema enforced by `/knowledge`; eval Tier 1 validates schema; "what goes where" decision tree in README; 90-day review per ADR-005 |
| Knowledge ledger entries written but never loaded by agents (ADR-005 named risk) | Medium | High | Implementation reviewed locally; organic load-confirmation tracked at [`2026-04-26-story-1-knowledge-loading-organic-validation`](../../issues/improvements/2026-04-26-story-1-knowledge-loading-organic-validation.md); 90-day ADR-005 review is the formal recheck trigger |
| Manifest format selection wrong (YAML proves brittle) | Low | Medium | Story 3 includes a fallback pure-bash YAML reader for the subset used; can swap to JSON if needed without breaking the generator interface |
| Preamble static-reference mechanism feels fragile vs runtime injection | Medium | Low | Documented as v1 mechanism in Story 4 technical spec; Phase 6+ can layer on adapter-level pre-load hooks; the eval enforces no command drifts |
| Eval Tier 1 produces noisy false-positives on existing files | High | Medium | Story 5 includes a triage pass: every check is calibrated against the post-Story-1–4 surface before being declared green; pre-existing violations either fixed or explicitly grandfathered with a comment |
| Solo-maintainer capacity overrun (research Risk #1) | Medium | High | Stories sized to ~XS–S each; no story >2 days; bundling with Phase 5 explicitly forbidden; if any story grows mid-flight, scope-cut via spec-healing, not push through |
| Owner field gets backfilled retroactively, creating false ownership claims on legacy specs | Low | Medium | Story 2 explicitly excludes migration; legacy specs reported as "legacy" without warning; backfill is opt-in by author only |
| Adapter neutrality breaks (one adapter ends up with platform-specific hooks) | Low | High | Every story's review must verify the change works under all three adapters; adapter doc updates are part of Definition of Done |

## Definition of Done (Spec-Level)

- [x] All 5 stories marked `Completed ✅`
- [x] `bash scripts/gen-skill.sh --dry-run && git diff --exit-code SKILL.md` exits 0
- [x] `bash scripts/eval.sh` exits 0 against the full Writ surface
- [x] `.writ/knowledge/` contains ≥5 backfilled entries across ≥2 categories (7 entries across 4 categories at completion)
- [x] CI workflow `.github/workflows/eval.yml` runs `gen-skill.sh --check` and `eval.sh` on every PR (remote-CI organic confirmation tracked at [`2026-04-26-story-5-remote-ci-gate-organic-validation`](../../issues/improvements/2026-04-26-story-5-remote-ci-gate-organic-validation.md))
- [x] All three adapter docs (`cursor.md`, `claude-code.md`, `openclaw.md`) reference the preamble convention and the knowledge-loading hook
- [x] Drift log entries (if any) recorded — none required at this completion (see `CHANGELOG.md` for the 2026-04-26 cleanup edit)
- [ ] 90-day review against the success criteria above (target: ≈2026-07-24, per ADR-005 review trigger)

---

> **Dual-use note (per [ADR-007](../../decision-records/adr-007-team-audience-sequencing.md)):** Each of the five features passes the dual-use test. The per-story dual-use justification is captured in each story's "Notes" section.

> **Honest dissent recorded** ([ADR-005](../../decision-records/adr-005-knowledge-substrate-markdown-over-database.md) Recorded Dissent): No external user has asked for the knowledge ledger. This spec proceeds anyway because the ledger unblocks Phase 5 features (per the addendum) and because the cost (≤4 days for v1) is small enough that being wrong is cheap. The 90-day review will revisit.
