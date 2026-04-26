# Writ vs. GStack — Rigor, Quality, Efficiency, Autonomy (April 2026)

**Date:** 2026-04-24
**Status:** Complete
**Builds on:** [`2026-03-14-gstack-analysis-research.md`](./2026-03-14-gstack-analysis-research.md) — that doc compared 8 GStack commands. GStack has since shipped 23+ skills, 8 power tools, a Chromium browser daemon, gbrain (Postgres-backed memory), eval infrastructure, and reached v1.12.2.0 with ~11 minor releases in the last two weeks. This doc reassesses the comparison along four explicit dimensions.

---

## Research Questions

1. **Coverage** — What does GStack do that Writ doesn't, and where do they overlap with different philosophies?
2. **Rigor** — How does each framework enforce quality? What's automated vs. advisory?
3. **Autonomy** — How far can each run without human intervention? What are the human-in-the-loop gates?
4. **Efficiency** — What's the friction surface (commands, prompts, manual handoffs) per shipped change?
5. **Strategic** — What's worth borrowing into Writ, and what is *not*?

---

## Executive Summary

Writ and GStack now occupy similar territory but have diverged hard in execution philosophy. **GStack has become a horizontal platform** — browser daemon, persistent memory (gbrain), cross-AI agent coordination, eval infrastructure, 9-host distribution, parallel sprints via Conductor. **Writ has stayed a vertical methodology** — contract-first specs, multi-agent SDLC pipeline with 9 explicit gates per story, drift detection, living-spec amendment, autonomous CLI loops via Ralph.

On the four dimensions:

- **Rigor (process):** Writ wins. 9 gates per story (arch → boundary → code → lint → review → drift → test → visual → docs), drift severity classification, ≥80% coverage enforcement, contract-first specs that lock scope before code. GStack's rigor sits *inside* each skill, not enforced *across* them — except via `/autoplan`.
- **Rigor (engineering quality of the framework itself):** GStack wins decisively. Three-tier eval system (free static / $0.15 LLM-judge / $3.85 E2E via real Claude Code spawning), workspace-aware versioning (queue-collision detection across parallel PRs), schema-versioned config, telemetry, CI gates. Writ has none of this self-test infrastructure.
- **Quality signals:** GStack wins on diversity (real-browser QA, cross-model adversarial review via `/codex`, OWASP+STRIDE security with exploit scenarios, ML-based prompt-injection defense, Pretext-validated HTML). Writ wins on *integration* — those signals would be more valuable inside Writ's per-story pipeline than scattered across skills.
- **Autonomy:** GStack has more autonomy *mechanisms* (autoplan + Conductor + continuous checkpoint + sidebar agent + pair-agent). Writ has one disciplined autonomy mode (Ralph) with quarantine branching for large drift. GStack wins on parallelism (10–15 concurrent sprints); Writ wins on safety per autonomous run.
- **Efficiency:** GStack wins runtime efficiency — sub-second browser commands, `/autoplan` removing 15–30 questions, parallel sprints. Writ wins rework-avoidance efficiency — contract-first means less code thrown away, and the gate pipeline catches drift before it propagates.

**The strategic conclusion:** Writ should *not* try to become GStack. The vertical methodology is differentiated and defensible. But Writ should aggressively borrow from GStack's *engineering hygiene of itself* (eval infrastructure, telemetry, queue-aware shipping) and add a small number of high-leverage skills that fit the gate model (cross-model adversarial review, real-browser QA upgrade, persistent memory). What's *not* worth borrowing: the browser daemon, the 23-skill explosion, gbrain's Postgres dependency, and the sprint-flow philosophy that abandons spec discipline.

---

## Side-by-Side: Where the Frameworks Stand

| Dimension | Writ (v0.13.1) | GStack (v1.12.2.0) |
|---|---|---|
| **Surface area** | 29 commands, 7 agents, all markdown | 23+ skills, 8 power tools, gbrain (Postgres), browser daemon (Bun+Chromium), Chrome sidebar, Conductor integration |
| **Distribution** | install.sh / update.sh, copy mode, Cursor + Claude Code (OpenClaw deferred) | Auto-update throttled, 10 hosts (Claude Code, Codex, OpenCode, Cursor, Factory, Slate, Kiro, Hermes, GBrain, OpenClaw) |
| **Versioning** | SemVer, deliberate (~13 minor releases in 8 weeks) | 4-segment monotonic (~11 minor in 2 weeks); `/ship` is workspace-queue-aware |
| **Discovery** | `/create-spec` Plan Mode + AskQuestion (contract-first; spec is the durable artifact) | `/office-hours` 6 forcing YC-style questions (sprint-flow; design doc is the artifact) |
| **Quality gates** | 9 explicit gates per story enforced by `/implement-story` | Per-skill rigor; `/autoplan` orchestrates CEO → Design → Eng → DX with 6 decision principles |
| **Code review** | Review Agent (PASS/FAIL, 5 dimensions, drift severity, max-3 iterations) | `/review` (fix-first, auto-fix vs ask classification, evidence-or-flag, Greptile integration) + `/codex` (adversarial second opinion from OpenAI Codex CLI) |
| **Security** | `/security-audit` (deps, secrets, code, infra, auto-fix) | `/cso` (OWASP Top 10 + STRIDE, 17 FP exclusions, 8/10+ confidence gate, exploit scenarios) + ML-based prompt-injection defense for sidebar agent |
| **Testing** | Testing Agent + ≥80% coverage enforcement on new code | `/qa` (real browser bug-fix-and-regression-test loop) + `/benchmark` (Core Web Vitals diffs) + bootstraps test framework if absent |
| **Design** | `/design` (Excalidraw wireframes) + Visual QA agent (compares screenshots to mockups) | `/design-shotgun` (4–6 AI image variants + comparison board + taste memory) + `/design-html` (Pretext-computed-layout production HTML) + `/plan-design-review` (10-D rating per dimension) |
| **Autonomy** | `/ralph plan` + CLI loop with 5-phase pipeline (validate → review subagent → commit), quarantine branching for large drift | `/autoplan` (auto-decide via 6 principles, surface only taste decisions and User Challenges) + Conductor (10–15 parallel sprints) + continuous checkpoint mode (auto WIP commits) |
| **Cross-AI collab** | None — single-platform via adapters | `/pair-agent` (shared browser, scoped tokens, ngrok) + `/codex` (multi-model review) + sidebar handoff |
| **Persistence / memory** | `.writ/` (markdown), `.writ/state/` (gitignored), `.writ/context.md` auto-regenerated, "What Was Built" records | gbrain (Postgres via PGLite/Supabase), continuous checkpoint mode (WIP commits with `[gstack-context]` body), gstack-memory-sync (cross-machine via private git repo with secret scanner) |
| **Browser** | None | Persistent Chromium daemon: ~100–200ms per command after warmup, ref system via Playwright Locators (no DOM mutation), CSP-safe, ARIA-tree-based |
| **Self-test infrastructure** | None documented | 3-tier evals: Tier 1 free static (<5s, every `bun test`), Tier 2 LLM-as-judge (~$0.15 / 30s), Tier 3 E2E via spawned `claude -p` (~$3.85 / 20min, gated on `EVALS=1`) |
| **Telemetry** | None | Opt-in to Supabase, schema-validated, never sends code/paths/prompts; local `gstack-analytics` always available |
| **Self-improvement** | `/refresh-command` (transcript-based, batch-mode pattern detection across N sessions), `/retro` | `/learn` (gbrain-backed memory), per-skill operational reflection block in preamble, 3+ active sessions triggers "ELI16 mode" automatically |
| **Anti-sycophancy** | Prime Directive (4 hard constraints, 5 judgment principles), Plan Mode integrity constraint | "User Sovereignty" ETHOS (User Challenge classification in `/autoplan`: even when both Claude and Codex agree, never act — present and ask) |
| **Extensibility** | Per-project command overlays, `/new-command` | Template + resolver system with `{{PLACEHOLDER}}` generation; SKILL.md generated from `commands.ts` source-of-truth so docs can't drift from code |
| **Lifecycle ops** | `/initialize`, `/update-writ`, `/reinstall-writ`, `/uninstall-writ` | `setup`, `gstack-team-init`, `gstack-upgrade`, `gstack-uninstall`, plus per-host detection |
| **Mode of failure** | Drift quarantine branch (`ralph/quarantine/{storyKey}`) + escalation in `/ralph status` | `/qa` retries with regression test, `/codex` cross-checks, browser handoff when AI hits CAPTCHA |

---

## Key Findings

### Finding 1: Two Different Theories of Rigor

**Writ's rigor is hierarchical.** Quality is enforced by *position in a sequence*: a story can't reach docs without passing review, can't pass review without satisfying acceptance criteria, can't even start coding without an architecture-check verdict. The contract precedes the code; the gates police the code; the drift log records every deviation.

> Evidence: `commands/implement-story.md` — 9 gates, max-3 review iterations, `change_surface` classification routes review depth proportionally, drift severity dictates whether to amend the spec or open a follow-up.

**GStack's rigor is networked.** Each skill is a self-contained quality unit (`/review` does fix-first auto-fix; `/qa` does real-browser bug-fix-and-regression; `/cso` does OWASP+STRIDE). Skills cite each other (`/ship` reads `/review`'s log; `/autoplan` orchestrates the four planning skills) but there's no enforced sequence. The user (or `/autoplan`) chooses what to invoke. Rigor depends on *which* skills run, not *that* they run in order.

> Evidence: `review/SKILL.md.tmpl` — fix-first heuristic, evidence-or-flag rule, Greptile integration, queue-status advisory, slop-scan advisory, cross-model dedup, persistent review log for `/ship` to consume. The skill is rigorous *internally*; it's silent on what should run before or after it.

**Honest assessment:** Both work. Writ's model is better when the project has spec discipline and a single executor. GStack's model is better when a single human (or 10 parallel Claude sessions) needs to flow through different cognitive modes without ceremony.

**The trade you're really making:** Writ's gates are guardrails that cost you flexibility. GStack's skills are tools that cost you guarantees. If a GStack user skips `/qa`, nothing reminds them. If a Writ user runs `/implement-story`, they cannot skip Gate 4 (testing) without `--quick`.

---

### Finding 2: GStack Has Engineered Itself Like a Production Product. Writ Has Not.

This is the single biggest gap, and it's not visible in the user-facing skill list.

**GStack ships with:**

- **Three-tier eval harness** (`test/skill-e2e-overlay-harness.test.ts`, `test/agent-sdk-runner.test.ts`) that can spawn real `claude -p` sessions, A/B test prompt overlays at N=10 trials per arm per fixture, and detect when Anthropic's own published best practices *hurt* model performance. v1.10.1.0 documented removing a "Fan out explicitly" overlay nudge after measurement showed it dropped parallel-tool-use rate from 70% baseline to 0%. **Cost of investigation: $7.**
- **canUseTool harness** built on Anthropic's Agent SDK to assert on `AskUserQuestion` shape and routing end-to-end. Previously E2E tests had to instruct the model to skip AskUserQuestion entirely. Now any interactive skill can be measured.
- **Workspace-aware shipping** (`bin/gstack-next-version`, v1.11.0.0): queries open PR queue, sees what versions other branches have claimed, picks the next free slot, fails open on bugs (a gstack bug never freezes a merge queue) but fails closed on confirmed collisions. CI gates: `version-gate.yml`, `pr-title-sync.yml`, plus GitLab parity.
- **Schema-versioned config** with deterministic migrations (`_schema_version: 2`, legacy `allow` → `read-write` migration runs on first read of any pre-D3 file).
- **Secret-sink test harness** (`test/helpers/secret-sink-harness.ts`): runs subprocess with seeded secret, captures stdout/stderr/files-under-HOME/telemetry-JSONL, asserts the seed never appears in any channel via four match rules (exact + URL-decoded + first-12-char prefix + base64).
- **SKILL.md template generation** with placeholder substitution from source code, so `gen:skill-docs --dry-run + git diff --exit-code` catches stale docs in CI before merge. Writ commands' "available commands" list could drift; GStack's structurally cannot.
- **Telemetry to Supabase** (opt-in, validated edge functions, schema-checked, never sends prompts/code/paths). 14 free-tier unit tests in `<250ms` cover the agent-sdk-runner alone.

**Writ ships with:**
- Manual validation via `/verify-spec`.
- No tests of Writ's own commands.
- No measurement of which prompt patterns work better.
- No queue-aware shipping (parallel `/release` across worktrees would collide silently).
- No telemetry.

> Source: `CHANGELOG.md` for both repos; GStack's `ARCHITECTURE.md` sections "Template test tiers" and "Eval persistence."

**Honest assessment:** Writ's "Markdown is enough, no tests needed" was defensible at 8 commands. At 29 commands, 7 agents, and 3 platform adapters with cross-references, it's accumulating drift risk. The next time a Writ command changes (`/implement-story` recently grew Gate 0.5 boundary maps), there's no harness that can prove it didn't regress.

**This is the most valuable thing GStack has that Writ doesn't.**

---

### Finding 3: Quality Signals — GStack Has More, Writ Integrates Them Better

GStack covers a wider spectrum of quality signals than Writ:

| Signal | Writ | GStack |
|---|---|---|
| Acceptance-criterion verification | Review Agent | `/review` + `/qa` |
| Static code review | Review Agent | `/review` |
| Cross-model adversarial review | — | `/codex` (adversarial mode actively tries to break code) |
| Real-browser end-to-end | Visual QA Agent (screenshot comparison) | `/qa` (clicks, finds bugs, fixes them with atomic commits, generates regression tests) |
| Performance | — | `/benchmark` (Core Web Vitals before/after per PR) |
| Security audit | `/security-audit` | `/cso` (OWASP+STRIDE, exploit scenarios, FP gating) |
| Prompt injection (for AI-driven browsing) | N/A | 6-layer defense (datamarking, BERT classifier, Haiku transcript, canary token, ensemble combiner, kill switch) |
| Coverage enforcement | ≥80% via Testing Agent (gate failure) | Audit only, advisory |
| HTML / production output | — | `/design-html` with Pretext computed-layout (text reflows, heights adjust dynamically) |
| Slop scan | — | `slop:diff` scans for empty catches, `return await`, overcomplicated abstractions |
| Documentation drift | `/verify-spec` (spec-lite divergence) | `/document-release` (cross-references diff against every `.md`) + `/review` Step 5.6 |
| Operational learnings | `/refresh-command --batch` | Per-skill reflection block in preamble |

**Where Writ wins:** the signals it has are *enforced inline*. Coverage isn't a recommendation — `/implement-story` won't mark a story complete without ≥80% on new code. Drift severity isn't advisory — it triggers spec amendment or follow-up creation. The pipeline forces the gates.

**Where GStack wins:** the signals it has are *broader and battle-tested*. `/cso`'s 17 false-positive exclusions, 8/10+ confidence gate, and "concrete exploit scenario per finding" requirements are more sophisticated than Writ's `/security-audit`. `/qa` actually clicks through your app; Visual QA only compares screenshots. `/codex` brings a *different model* to the review — Writ has no equivalent.

**Honest assessment:** A Writ user who runs `/implement-story` cleanly is more likely to ship working code than a GStack user who only runs `/ship` (because Writ enforced testing, drift, and coverage in one command). But a GStack user who runs the full sprint (`/office-hours` → `/autoplan` → implement → `/review` → `/codex` → `/qa` → `/cso` → `/ship` → `/canary`) has crossed more rigor surface than any single Writ command path covers.

---

### Finding 4: Autonomy — Writ Has Discipline, GStack Has Mechanisms

**Writ's autonomy is `/ralph`.** A 3-loop nested model: Ralph Loop (epic, fresh context per iteration) → Story Pipeline (code → test → lint → review → commit) → Fix Loops (max 3 iters tests, max 2 iters review). The Ralph review subagent is read-only and gates each story before commit (PASS/FAIL/PAUSE). Large drift triggers a quarantine branch (`ralph/quarantine/{storyKey}`) and escalates via `/ralph status`. One disciplined autonomous mode, with explicit quality gates and explicit failure handling.

> Evidence: `commands/ralph.md`, `agents/review-agent.md`, CHANGELOG entry for v0.12.0 (Ralph review subagent + back-pressure caps).

**GStack's autonomy is plural.** `/autoplan` removes 15–30 intermediate questions via 6 decision principles (Boil Lakes, Pragmatic, DRY, Explicit-over-clever, Bias-toward-action, Choose-completeness) but classifies decisions as Mechanical / Taste / **User Challenge** — User Challenge is *never* auto-decided, even when both Claude and Codex agree. Conductor runs 10–15 parallel sprints. Continuous checkpoint mode auto-commits WIP between turns with structured `[gstack-context]` body. Sidebar agent runs in an isolated session for "go fill the parent portal directory" tasks. Pair-agent enables cross-vendor AI coordination through a shared browser.

> Evidence: `autoplan/SKILL.md.tmpl` — see Decision Classification section, particularly the User Challenge spec which requires explicit "What context we might be missing" and "If we're wrong, the cost is" framing.

**Honest assessment:** Different definitions of autonomy.

- **GStack's autonomy is "expand the human's bandwidth."** Run more sprints in parallel. Auto-decide more questions. Have an AI agent browse on your behalf while another reviews PRs while a third writes regression tests. The human is a *router*.
- **Writ's autonomy is "extend the human's session."** One agent, one task, run continuously through the night against a clean spec. The human is a *reviewer the next morning*.

Both are valid. They serve different mental models. **What's worth borrowing from GStack into Writ:** the User Challenge concept. Writ's Ralph loop currently has implicit decision points; making User Challenge explicit (and never-auto-decidable) would add a meaningful safety rail.

---

### Finding 5: Efficiency — Different Bottlenecks

**Writ's efficiency lever is rework avoidance.** The contract-first phase is slower at the start (Plan Mode discovery, structured contract, story decomposition with `assess-spec` sizing checks) but means less code thrown away after implementation. The gate pipeline detects drift before it propagates into downstream stories. "What Was Built" records prevent agents from re-scanning the codebase to figure out what an upstream story produced.

> Evidence: `commands/create-spec.md` (--from-prototype mode, --from-issue mode, contract proposal), `commands/implement-story.md` (context hint parsing, agent-specific spec-lite sections, `change_surface` classification for proportional review depth).

**GStack's efficiency lever is per-task latency.** The browser daemon is the canonical example: Playwright cold-start is 2–3s per command; the daemon makes every subsequent call ~100–200ms. Conductor lets you run 10–15 sprints in parallel because each sprint is a self-contained skill flow. `/autoplan` removes friction by auto-answering 15–30 intermediate questions. The sidebar agent isolates tool-using browsing from the main coding session. Voice triggers ("run a security check") avoid command memorization.

> Evidence: `ARCHITECTURE.md` daemon model section ("First call starts everything (~3s). Every call after: ~100-200ms.")

**Honest assessment:** GStack is more efficient *per command invocation*. Writ is more efficient *per shipped change* — a clean Writ pipeline run produces tested, reviewed, drift-free code without rework. The asymmetry shows up at scale: a GStack user shipping 10 parallel features tolerates more rework because each task is cheap; a Writ user shipping 10 features wants each one to land clean because the pipeline isn't free.

**Where Writ has unforced inefficiency:** no queue-aware shipping (`/release` would collide silently if run in parallel worktrees). No persistent context across sessions other than `.writ/context.md` (regenerated, not accumulated). No skill-discovery shortcuts (no voice triggers, no proactive suggestions based on stage detection).

---

### Finding 6: The Anti-Sycophancy Principle — Both Have It, Different Architectures

This finding deserves its own section because it's structurally similar but tactically different.

**Writ's Prime Directive** (`system-instructions.md`): 4 hard constraints, 5 judgment principles. Hard constraints include "Never reverse a position without new evidence" and "Never let Plan Mode absorb a command's workflow" (added in v0.13.1 after `/refresh-command --batch` detected a recurring pattern of planning conversations being treated as deliverables). It's a meta-rule injected into every command via system instructions.

**GStack's User Sovereignty** (`ETHOS.md`): "Two AI models agreeing on a change is a strong signal. It is not a mandate." Tactically operationalized in `/autoplan` as **User Challenge** classification — when Claude and Codex both recommend changing the user's stated direction, the framing is required to include "What context we might be missing" and "If we're wrong, the cost is." Never auto-decided.

**Honest assessment:** GStack's User Challenge construct is stronger than anything in Writ. Writ's Prime Directive says "don't be sycophantic" at the meta-level. GStack's User Challenge says "here is the *exact decision shape* that triggers a stop, here is the *exact framing* the AI must use, and it's enforced by the autoplan flow."

This is borrowable — and it should be borrowed. Specifically into `/ralph plan`, `/implement-spec`, and `/edit-spec`.

---

## Options Analysis — What Writ Should Do With This

Before presenting options, the honest framing: every option below trades against Writ's identity. Writ's vertical methodology is its differentiation. Adding too much GStack-style horizontal tooling would dilute it. The question is: what's the *minimum* set of borrowings that closes the most consequential gaps?

### Option A — Engineering Hygiene Only (recommended primary)

Borrow GStack's *self-test infrastructure* without touching the user-facing surface.

**Add:**
1. Eval harness for Writ commands themselves (Tier 1: static parse + smoke; Tier 2: LLM-as-judge for clarity; Tier 3: gated paid E2E spawning real AI sessions to run a command end-to-end).
2. Workspace-aware `/release` (queue-collision detection across parallel worktrees, fail-closed on confirmed collisions, fail-open on bugs).
3. Schema-versioned `.writ/state/` config with deterministic migrations.
4. Generated `SKILL.md` from a source-of-truth (currently SKILL.md is hand-maintained — would prevent drift).

**Cost:** Medium. Requires bun/node infrastructure that Writ doesn't currently have. ~2–4 weeks of engineering. Marginally widens Writ's surface area for new contributors.
**Benefit:** High. The next major Writ refactor stops being a "hope nothing broke" exercise.
**Risk:** Low. Doesn't change user experience; pure infrastructure investment.

### Option B — Targeted Skill Adoption (recommended secondary)

Pick 3 GStack skills that fit Writ's gate model and integrate them as agents/gates.

**Add:**
1. **Cross-model adversarial review** (analog of `/codex`): a new agent that runs after the Review Agent and uses a *different model* to challenge the implementation. PASS/FAIL gate. Caches prior runs in the `.writ/state/` for `/ship`-time reference.
2. **Real-browser QA gate** (upgrade Visual QA Agent): Playwright-driven actual user-flow testing for stories with `## Visual References`. Auto-generates regression tests on bug fix.
3. **Persistent learnings via simple JSONL** (analog of `/learn`, but markdown/JSONL not Postgres): `.writ/learnings.jsonl` accumulates patterns observed across sessions; `/refresh-command --batch` already does the analysis layer.

**Cost:** Medium-High. Real-browser QA requires Playwright dependency (departs from "pure markdown" claim). Cross-model review requires multiple AI provider configs.
**Benefit:** High. Closes the diversity gap on quality signals while preserving the gate model.
**Risk:** Medium. Each new dependency widens the install footprint. Visual QA Playwright migration would be the biggest break.

### Option C — Steal the User Challenge Concept (recommended tertiary, near-zero cost)

Add a **User Challenge** classification to `/ralph plan`, `/implement-spec`, `/edit-spec`, and `/create-spec --from-prototype`. When the system would change the user's stated direction (drop a deliverable, merge two stories, abandon a constraint), it must surface explicitly with: "What you said / What we recommend / Why / What context we might be missing / If we're wrong, the cost is." Never auto-decided.

**Cost:** Near-zero. Adds ~30 lines to 4 commands.
**Benefit:** High. This is a Prime Directive enforcement mechanism Writ currently lacks.
**Risk:** None.

### Option D — Sprint-Flow Pivot (do NOT recommend)

Adopt GStack's full sprint-flow philosophy: dissolve `/implement-story`'s gate enforcement, ship 23+ skills, follow Conductor-style parallelism.

**Cost:** Massive. Effectively becomes a Writ-flavored GStack fork with 5x the surface area and 1% of the user base.
**Benefit:** Catches up to GStack on coverage.
**Risk:** Loses Writ's identity. Writ's contract-first vertical methodology is its only differentiation. Dropping it = dropping Writ.

### Option E — Chrome / Browser Integration (do NOT recommend)

Build a Writ-flavored persistent browser daemon.

**Cost:** Massive. Bun+Chromium daemon is months of engineering and ongoing maintenance. GStack's `ARCHITECTURE.md` documents non-trivial security surface (dual-listener tunnel, prompt-injection defense, cookie security, shell injection prevention, ref system). This is a product, not a feature.
**Benefit:** Real-browser QA for visual stories.
**Risk:** Pulls Writ off-mission. Better path: depend on Playwright for the narrow Visual-QA case (Option B item 2) instead of building infrastructure.

---

## Recommendations

**Primary (next 4 weeks):** Option A — add eval infrastructure for Writ commands. The case is overwhelming: at 29 commands and 7 agents with multi-line cross-references, Writ is one bad refactor away from breaking silently. GStack proved this is solvable: $7 for an entire investigation run, three-tier cost discipline, free static checks on every test run. Without this, every Writ release is "hope" not "verify."

**Secondary (next quarter):** Option C — adopt User Challenge classification in `/ralph plan`, `/implement-spec`, `/edit-spec`, `/create-spec`. This is the highest-leverage borrowing: zero infrastructure, hardens Prime Directive enforcement, takes a day.

**Tertiary (medium term, ADR required):** Option B item 1 only — cross-model adversarial review as a new agent in the `/implement-story` pipeline. The `/codex` analog is a real gap; Writ has no defense against the failure mode "single model gets confidently wrong about the implementation." Defer items 2 and 3 of Option B until item 1 is proven.

**Explicitly reject:** Options D and E. Don't pivot the methodology, don't build a browser daemon. The vertical-methodology positioning is Writ's only distinctive asset; preserve it.

**Honest contradiction:** I'm recommending borrowing engineering hygiene from GStack while explicitly rejecting most of GStack's user-facing borrowings. That's not because GStack's user-facing skills are bad — many are excellent. It's because Writ's pipeline architecture *can't absorb 23 ad-hoc skills* without breaking its own integrity. The borrowings have to fit the gate model or they erode it.

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Building eval infrastructure delays user-facing work | Medium | Medium | Time-box to 4 weeks; ship Tier 1 (free static) first as standalone PR; defer Tier 3 paid E2E until Tier 1 proves value |
| Cross-model review requires multi-provider config that frustrates users | Medium | Low | Make optional (default off); configure via `.writ/config.md`; provide skip-if-unconfigured semantics |
| Borrowing too eagerly turns Writ into "GStack-but-worse" | High if unchecked | Catastrophic to identity | Apply this filter to every new borrowing: "Does this fit the per-story gate model?" If no, reject |
| GStack moves faster than Writ can catch up | Certain | Low | Explicitly compete on rigor and contract discipline, not surface area. Two specs running clean through Writ's pipeline beats 10 ad-hoc skill runs |
| Playwright dependency breaks "pure markdown" positioning | High if Option B-2 adopted | Medium | Make Playwright opt-in; gate on presence; degrade Visual QA gracefully when absent |

---

## Further Research

These questions remain unanswered and matter for follow-up:

1. **What's GStack's user retention?** 82.4k stars is impressive, but stars don't measure daily active use. Hard to judge "is GStack actually used end-to-end" from outside. Would inform how aggressively to mirror its patterns.
2. **What's the empirical quality of GStack's `/review` vs Writ's Review Agent?** No evidence here either way. A side-by-side eval (run both on the same PR with seeded bugs) would be definitive.
3. **Is GStack's eval infrastructure reusable, or does it require their template + resolver system as scaffolding?** If reusable independently, Option A becomes much cheaper.
4. **How does `/codex` actually perform?** Garry's CHANGELOG entries cite Codex catching real bugs (5 of 8 findings during one plan-ceo-review), but those are anecdotes. Worth running a real comparison.
5. **What did the prior `2026-03-14-gstack-analysis-research.md` recommend that Writ adopted, and what was the impact?** Cross-reference would tell us how well borrowings actually work in practice for this team.

---

## Sources

| Source | What it covered |
|---|---|
| `https://github.com/garrytan/gstack` (README) | Skill catalog, install flow, sprint philosophy, parallel sprints |
| `https://raw.githubusercontent.com/garrytan/gstack/main/ETHOS.md` | "Boil the Lake," "Search Before Building," "User Sovereignty" — ground-truth philosophy |
| `https://raw.githubusercontent.com/garrytan/gstack/main/ARCHITECTURE.md` | Browser daemon design, security model, eval tiers, SKILL.md template system, error philosophy |
| `https://raw.githubusercontent.com/garrytan/gstack/main/CHANGELOG.md` (v1.10.0–v1.12.2.0) | Engineering hygiene shipped in last 2 weeks: workspace-aware versioning, plan-mode handshake, overlay measurement harness, gbrain onboarding, secret-sink harness |
| `https://raw.githubusercontent.com/garrytan/gstack/main/office-hours/SKILL.md.tmpl` | YC discovery flow — dual-mode (startup vs builder), forcing questions |
| `https://raw.githubusercontent.com/garrytan/gstack/main/autoplan/SKILL.md.tmpl` | 6 decision principles, Mechanical/Taste/User-Challenge classification, sequential CEO→Design→Eng→DX |
| `https://raw.githubusercontent.com/garrytan/gstack/main/review/SKILL.md.tmpl` | Fix-first heuristic, evidence-or-flag rule, Greptile integration, queue advisory, slop scan |
| `commands/implement-story.md` (this repo) | 9-gate pipeline, context hints, change_surface routing, drift response |
| `commands/create-spec.md` (this repo) | Contract-first discovery, --from-prototype, --from-issue modes |
| `commands/ralph.md` (this repo) | 3-loop autonomous model, review subagent, quarantine branching |
| `commands/verify-spec.md` (this repo) | 7-check metadata diagnostic with auto-fix |
| `agents/review-agent.md`, `agents/coding-agent.md` (this repo) | Sub-agent contracts, change_surface, boundary maps |
| `system-instructions.md` (this repo) | Prime Directive, 4 hard constraints, 5 judgment principles |
| `.writ/research/2026-03-14-gstack-analysis-research.md` | Prior comparison baseline (8 GStack commands) — informed delta framing |
| `CHANGELOG.md` (this repo, v0.12.0–v0.13.1) | Recent Writ enhancements: Ralph review subagent, lifecycle commands, Plan Mode integrity |

---

## Addendum — Production-Grade Reframe & Team-Collab Lens

> **Added:** 2026-04-24 (later same day, after dialogue with stakeholder)
> **Status:** Supersedes the **Options Analysis** and **Recommendations** sections of the original doc. Findings 1–6 above remain valid; this addendum adds Findings 7–9, hedges Finding 5, and replaces the recommendations with a sequenced plan.

### Why This Addendum Exists

The original analysis treated Writ and GStack as two horizontal frameworks competing on the same axis. Two clarifications from the stakeholder changed the framing materially:

1. **Audience** — Writ is currently used by solo developers, but small-team collaboration is a near-term goal. GStack is explicitly a "team of one" tool. These are not the same target.
2. **Goal** — Writ's success criterion is *production-grade output that holds up over time*, not raw shipping velocity. Many of GStack's wins are velocity wins; not all of them transfer.
3. **Specific interest in two GStack subsystems** — GBrain (context management) and the skills creation infrastructure (execution).

The original doc also contained two analytical errors I want to correct in writing:

- **Survivor bias.** Most evidence I cited about GStack came from GStack-controlled sources (README, ETHOS.md, ARCHITECTURE.md, CHANGELOG, SKILL.md.tmpl files). Star count (82.4k) measures Twitter-driven attention, not in-anger production usage. Quality claims should be hedged accordingly until independent evidence is available.
- **Inverse comparison missing.** I documented six things GStack has that Writ does not. I did not document what Writ has that GStack does not, even though several of those gaps are more strategically important for the stated goal. Finding 7 corrects this.

### Production-Grade Criteria — The Lens Used Below

When I say "production-grade" in this addendum, I mean a system whose output meets all of the following:

| Dimension | Question |
|---|---|
| **Auditable** | Can a second engineer reconstruct *why* a decision was made, six months later, from the artifacts alone? |
| **Versioned** | Can the team see what changed, when, and revert if a change degrades quality? |
| **Reviewable** | Can knowledge and architecture be reviewed in a PR, not just executed by an LLM? |
| **Reproducible** | Does running the same input through the system tomorrow produce the same artifacts as today? |
| **Onboarding-friendly** | Can a new contributor get oriented in <1 day and productive in <1 week? |
| **Failure-isolatable** | When something goes wrong, can you find the broken part without re-running everything? |

Both context management *and* execution must satisfy all six. This is the bar against which GBrain and the skills infrastructure are evaluated below.

### Finding 7 — What Writ Teaches GStack (the inverse comparison)

The original doc enumerated GStack's wins. Here are Writ's, structured the same way. These are not minor — several are direct consequences of the production-grade lens above.

| # | Capability | Writ has | GStack has | Why it matters for production-grade |
|---|---|---|---|---|
| 1 | **Spec-as-team-contract** | Yes — `spec.md` + `spec-lite.md` + `tasks.md` + `drift-log.md` per feature, all human-readable, all in git | No — work is captured in slash-command invocations and ephemeral chat | Specs are the artifact a team negotiates *before* code is written. Without them, "review" happens after the fact and can only critique, not steer. |
| 2 | **Contract-first discovery** | Yes — `/create-spec` uses Plan Mode for shaping, AskQuestion for bounded decisions, then materializes files only after approval (ADR-001) | Partial — `/office-hours` produces design docs, but most skills produce code first | Forces the expensive thinking to happen when changes cost nothing. GStack's velocity wins partly come from skipping this. |
| 3 | **Drift logs** | Yes — every story records spec-vs-implementation deltas with severity (`drift-log.md`) | No equivalent | Closes the loop between "what we said we'd build" and "what we built." Critical for any team that has to defend decisions. |
| 4 | **Architecture-check gate** | Yes — read-only PROCEED/CAUTION/ABORT before code is written | No — review happens post-diff via `/review` | Catches structural mistakes before they become rework. Cheaper than the GStack model. |
| 5 | **Anti-sycophancy as a versioned root contract** | Yes — `system-instructions.md` with 4 hard constraints, 5 judgment principles, Plan Mode integrity guard | Distributed across skills, encoded in process not policy ("User Sovereignty" stated; mechanism unclear) | A team can review and amend the contract. With GStack, the behavior is implicit in the skills' construction. |
| 6 | **Adapter abstraction** | Yes — same commands run on Cursor, Claude Code, OpenClaw via `adapters/` | No — Claude Code only | Survives platform churn. A team that's standardized on Cursor today can move to a different agent runtime without rebuilding their workflow. |
| 7 | **Plain-text source of truth** | Yes — every artifact is markdown in git | Partial — knowledge lives in PGLite/Postgres (GBrain), browser daemon state, command invocations | Plain text + git is the lowest-common-denominator collaboration substrate. Databases are great for retrieval, terrible for review. |

**What this means for the strategic question:** Writ already has the harder pieces of production-grade infrastructure. GStack has the easier-to-add pieces (eval rigor, knowledge persistence, browser primitives). The original doc's framing of "Writ is behind on rigor" was not wrong, but it was incomplete and slightly misleading.

### Finding 8 — Context Management: GBrain vs Markdown Knowledge Ledger

GBrain is GStack's persistent memory layer. It is an interesting design and the right answer for *some* problems, but the wrong answer for production-grade team work. Worked out below.

#### What GBrain actually is

From `https://github.com/garrytan/gstack/tree/main/setup-gbrain` and the changelog entries for `/setup-gbrain`:

- **Storage:** PGLite (embedded Postgres) by default, optional Supabase for cross-machine sync
- **Access:** Skills query GBrain for prior context, write results back into it
- **Trust model:** Per-remote trust policy (which agents/machines can read/write which keyspaces)
- **Use case:** "AI agents that remember across conversations and machines"

#### Strengths (honest assessment)

| Strength | Why it matters |
|---|---|
| **Fast retrieval at scale** | Indexed queries beat grep over thousands of markdown files |
| **Cross-machine sync via Supabase** | Real for multi-device solo workflows |
| **Trust boundaries** | Genuinely thoughtful security model for a personal tool |
| **Solves a real problem** | Single-conversation context windows are a bottleneck for long-running work |

#### Weaknesses against the production-grade lens

| Dimension | GBrain score | Why |
|---|---|---|
| Auditable | **Fail** | Knowledge in a database is not browsable in a PR; you can't read GBrain on GitHub |
| Versioned | **Partial** | Postgres has change-data-capture, but no human-readable diff history per knowledge item |
| Reviewable | **Fail** | A team cannot review a teammate's GBrain entries the way they'd review a markdown file |
| Reproducible | **Conditional** | Cross-machine sync helps, but local-first PGLite means each developer's GBrain diverges silently |
| Onboarding-friendly | **Fail** | New team member arrives, runs `/setup-gbrain`, has nothing in their database; meanwhile the team's institutional knowledge lives in someone else's PGLite instance |
| Failure-isolatable | **Conditional** | Database queries fail in opaque ways; markdown grep does not |

GBrain is optimized for **a single agent acting on behalf of a single user across a long time horizon**. It is anti-optimized for **a team building a product that will be inspected, reviewed, and onboarded into**.

#### The recommended alternative — markdown knowledge ledger

The *idea* GBrain encodes (knowledge accumulates across sessions and should not have to be re-derived) is correct. The *implementation* (database) is wrong for Writ's audience.

Proposed: **`.writ/knowledge/` directory of timestamped markdown files**, written by commands and read by agents at task start.

```
.writ/knowledge/
├── decisions/        # "We chose X because Y" (one file per decision)
├── conventions/      # "This codebase uses pattern Z for tests"
├── glossary/         # Domain terminology, one file per concept
└── lessons/          # Postmortem-style "we tried X, it failed because Y"
```

Properties — checked against the production-grade lens:

| Dimension | Score | Why |
|---|---|---|
| Auditable | **Pass** | Every entry is a markdown file; entire history visible in `git log` |
| Versioned | **Pass** | Git is the version system |
| Reviewable | **Pass** | Knowledge changes ship in PRs alongside code; teammates can comment line-by-line |
| Reproducible | **Pass** | Clone the repo, get the knowledge |
| Onboarding-friendly | **Pass** | New contributor reads `.writ/knowledge/` like documentation |
| Failure-isolatable | **Pass** | If retrieval breaks, it's a grep problem, not a database problem |

**Trade-off accepted:** retrieval is slower than indexed Postgres. For a solo dev with hundreds (not millions) of knowledge entries, grep + agent context loading is fast enough. If the corpus ever grew beyond grep's comfort zone, an *index* over the markdown could be added without changing the source of truth — same pattern as `tantivy` over a markdown wiki.

This is the **right kind of borrow**: take GStack's recognition that knowledge persistence is essential, reject GStack's storage choice as misaligned with the audience.

### Finding 9 — Spec-as-Team-Contract: Writ's Unspoken Wedge

Reframing Finding 7 #1 because it is, in my best assessment, the single most important thing Writ has and GStack does not.

#### The thesis

Solo dev workflows can be built around chat history, ephemeral commands, and a strong individual. Team workflows cannot — they require a **negotiated, versioned contract** between humans before agents act.

Writ's `spec.md` + `spec-lite.md` + `tasks.md` + `drift-log.md` is exactly that contract. GStack does not have one.

This means:
- **GStack is competing in the solo-dev velocity market**, where it is excellent.
- **Writ is competing in a smaller market today** (solo devs willing to be methodical) **but is positioned for a market GStack cannot enter without rebuilding from scratch** (small teams that need shared context).

The strategic implication: do not chase GStack on velocity. Chase production-grade output and team readiness, where Writ's existing contract substrate is the moat.

#### What "team-ready" means concretely (not yet built in Writ)

The contract substrate exists. The team-collaboration affordances on top of it are mostly absent. Concrete gaps:

| Gap | What's needed | Effort |
|---|---|---|
| Spec ownership / assignment | `spec.md` frontmatter field for owner, status board across `.writ/specs/` | Small (1–2 hr) |
| Cross-spec dependency tracking | `dependencies:` block listing other spec slugs; `verify-spec` extension to validate | Medium (1 day) |
| Multi-developer drift reconciliation | When two devs work on overlapping specs, tooling to surface conflicts pre-merge | Large (≥1 week) |
| Spec review handoff | A `/review-spec` command that does for specs what `/review` does for code | Medium (2–3 days) |
| Knowledge ledger (Finding 8) | The shared substrate teams reason against | Medium (2–4 days) |

The first item is borderline trivial. The fifth is the keystone — without shared knowledge, none of the other team affordances matter.

### Hedging on GStack Quality Claims (correcting survivor bias in original)

The original Findings 1, 4, and 5 cited GStack capabilities as established facts. They are *documented* facts — present in GStack's own materials. They are not *independently verified* facts. Specifically:

| Claim | Actual evidence base | Adjusted confidence |
|---|---|---|
| "Three-tier eval harness produces high-quality skills" | GStack's own ARCHITECTURE.md describes the harness | Medium — design is sound; output quality not measured externally |
| "Persistent browser daemon yields sub-second commands" | GStack's README claims this; no third-party benchmark cited | Medium-high — physically plausible; likely true |
| "/autoplan produces good architectural decisions" | Skill template describes the process; output examples not surveyed | **Low** — the design is interesting; no evidence the outputs are actually good |
| "82.4k stars indicates production usage" | Star count is real | **Low** — stars measure attention, not adoption |

This does not mean GStack is bad. It means I should not have written about its quality outcomes with the confidence I did. The *designs* are reviewable and assessable; the *outcomes* are not, from where we're standing. For the purpose of deciding what to borrow, design quality is sufficient.

### Skills-Creation Infrastructure — Sharper Recommendation

Finding 5 and Option B in the original doc treated GStack's skills-creation infrastructure as a single thing to consider. With the production-grade lens, it splits into three pieces with very different cost/value profiles:

| Piece | What it does | Value for Writ | Cost | Recommendation |
|---|---|---|---|---|
| **`SKILL.md` template generation** (template + source code → final SKILL.md, prevents drift) | Auto-generates command/agent docs from a single source, so docs cannot drift from behavior | **High** — drift between command files and `SKILL.md` is already a real risk in this repo | Low (1–2 days) — manifest file + simple generator script | **Build a minimal version** |
| **Preamble enforcement** (every skill includes a consistent preamble describing context, conventions, behavior) | Prevents agents from missing standing instructions | Medium-high — Writ's commands all share standing assumptions today, manually | Low-medium (2–3 days) — single preamble file + injection at command-load time | **Build a minimal version** |
| **Three-tier eval harness** (static checks → LLM-as-judge → E2E) | Catches regressions in skill behavior quantitatively | **High value, but only Tier 1 is cheap** | Tier 1: 1 day. Tier 2: weeks (judge model, prompt eng, infra). Tier 3: weeks-months. | **Build Tier 1 only. Defer Tier 2/3.** |

The original Option B bundled all three. Splitting them changes the calculus considerably — the first two are weekend projects; the third is a multi-month commitment that may not justify its cost for a solo maintainer.

### Risks Updated

Adding to the original Risks section:

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Solo-maintainer asymmetry** — GStack ships at the rate of a fully resourced project; Writ does not. Borrowing too much in one cycle stalls the maintainer. | High | High | Sequence borrows over multiple cycles. The recommendation below schedules over ~6 weeks, not 6 days. |
| **Borrowing the wrong abstraction** — implementing GBrain-style storage when markdown ledger is the right fit, then having to rip it out | Medium | High | Default to plain-text + git; only introduce a database if grep over the markdown becomes a measurable bottleneck. |
| **Production-grade slogan decay** — claiming "production-grade output" without measurable criteria | Medium | High | Operationalize the 6-criteria lens above into a `verify-spec` extension or a `/audit` command in a future cycle. |
| **GStack envy** — chasing velocity wins that compromise the contract substrate | Medium | Medium | Use Finding 9 as a gate: does this borrow strengthen the spec-as-team-contract, or weaken it? Reject borrows that weaken it. |

### Revised Options & Recommended Sequence (supersedes Recommendations section)

The original Recommendations were: borrow A (eval Tier 1), borrow B (skills infra), borrow C (User Challenge), defer D (browser), defer E (GBrain). I'm updating and resequencing.

**Recommended sequence**, in priority order, calibrated for a solo maintainer:

| # | Move | Rationale | Effort | Order | Spec-worthy? |
|---|---|---|---|---|---|
| 1 | **Markdown knowledge ledger** (`.writ/knowledge/`) — design + minimal command for writing/reading entries | Foundation for both team collaboration and accumulated context. Cheapest big lever. | 2–4 days | First | Yes — small `/create-spec` candidate |
| 2 | **`SKILL.md` template generation** — manifest file + generator script | Eliminates a drift risk that already exists; prerequisite for any team contributor to trust the docs | 1–2 days | Second | Maybe — small enough for an issue + direct PR |
| 3 | **Preamble enforcement** for commands | Pairs with #2; small additional lift | 1 day | Second (bundle with #2) | Same as #2 |
| 4 | **Eval Tier 1** (static checks for command/agent files: required sections, anti-sycophancy phrasing, broken refs, length sanity) | Cheap quality floor; gives confidence to ship changes faster; sets up Tier 2/3 if ever justified | 1 day | Third | Yes — small spec |
| 5 | **Spec-as-team-contract enhancements** (start with: owner field + dependency block + status board) | Operationalizes Writ's strategic moat; prepares the audience pivot | 1–2 days for first slice | Fourth | Yes — separate spec |
| 6 | **`/audit` command** (operationalize the 6 production-grade criteria as a checkable diagnostic) | Makes "production-grade" measurable; this is the quality assertion that makes Writ defensible | 2–3 days | Fifth | Yes — separate spec |
| ~~ | ~~GBrain storage~~ | Wrong shape for the audience (see Finding 8). Knowledge ledger covers the underlying need. | — | Don't do | No |
| ~~ | ~~Browser daemon~~ | Defer per original analysis — only matters once Writ is doing significant browser work | — | Defer | No |
| ~~ | ~~Eval Tier 2/3~~ | Cost grossly exceeds value for current scale | — | Defer indefinitely | No |
| ~~ | ~~Cross-AI agent collaboration (`/pair-agent`, `/codex`)~~ | Adapter abstraction already gives multi-platform; pair-agent is a parallel feature, not a quality-floor feature | — | Defer | No |

**Aggregate effort for items 1–6:** roughly 8–13 days of focused work. Spread over 6–8 calendar weeks at solo-maintainer pace, this is realistic.

### What I'm Recommending Next (concrete)

| Action | Why now |
|---|---|
| **Spec for the markdown knowledge ledger** (`.writ/specs/2026-04-25-knowledge-ledger/`) | Highest leverage, smallest dependency, sets up everything else |
| **ADR for "knowledge as plain text, not database"** in `.writ/decision-records/` | Records the GStack divergence with reasoning; future contributors will ask "why didn't we use GBrain?" |
| **Issue (not spec) for SKILL.md template generation** | Small enough to skip the spec ceremony |

Proposing these three as the immediate output of this research, in that order. The spec for the knowledge ledger should be the next `/create-spec` invocation; the ADR can be drafted alongside.

### Honest Open Questions

These remain open and should not be resolved by me alone:

1. **Is "production-grade" the actual goal, or is it a stated goal masking a different actual goal?** If the unstated goal is "ship faster," the recommendations above are wrong and GStack-style velocity borrows are right. Asking aloud.
2. **What's the actual time horizon for "small team collaboration"?** If it's >12 months, building team affordances now is premature. If it's <6 months, item 5 should move up.
3. **Is the knowledge ledger valuable enough to justify building it before any user has asked for it?** It's an engineering investment based on extrapolation, not user research. Worth surfacing.
4. **Should this comparison be re-run in 6 months against a then-current GStack?** GStack ships fast; the assessment will go stale.

### Original Recommendations: What Changed

For traceability, here is what changed between the morning analysis and this addendum:

| Original recommendation | Status | Reason |
|---|---|---|
| Borrow A: Eval Tier 1 — high priority | **Kept, repositioned to #4** | Still valuable, but downstream of the knowledge ledger |
| Borrow B: Skills creation infrastructure — medium priority | **Split into 3 pieces (#2, #3, deferred Tier 2/3)** | Bundling them obscured very different cost profiles |
| Borrow C: `/autoplan` User Challenge — low priority | **Dropped from active list** | The Plan Mode integrity guard already covers the equivalent need; not enough additional value |
| Defer D: Browser daemon | **Same** | No change |
| Defer E: GBrain | **Same conclusion, different reasoning + new alternative** | Original deferred on cost grounds; the real reason is shape mismatch with audience. Markdown ledger added as the right alternative. |
| (Not in original) Spec-as-team-contract | **New: #5** | The inverse-comparison gap that the original missed |
| (Not in original) `/audit` command | **New: #6** | Operationalizes the production-grade claim; makes it falsifiable |
