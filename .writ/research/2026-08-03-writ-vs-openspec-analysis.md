# Writ vs. OpenSpec — Quality & Token-Efficiency Analysis, with a Focus on Agent/Model Routing (August 2026)

**Date:** 2026-08-03
**Status:** Complete
**Subject:** [Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) `@fission-ai/openspec` v1.7.0 (npm), 63.6k GitHub stars, 4.4k forks, 725 commits, MIT. "The most loved spec framework."
**Method:** Shallow clone of `main` (latest commit `45cca5d`, 2026-07-31). Read the actual protocol — all 12 core `SKILL.md` files, the `.agents/skills/release-openspec` skill, `openspec/specs/*` (34 spec files describing the CLI's own behavior, written *in* OpenSpec by OpenSpec), `docs/*.md` (30 pages: FAQ, overview, customization, supported-tools, existing-projects, editing-changes), `CHANGELOG.md`, `package.json`, and grepped the full `src/` TypeScript source (37.5k LOC, 119 test files) for model-selection/routing code. Compared against Writ product source at `VERSION` 0.24.0, `agents/*.md` model-tier assignments, and ADR-016.

---

## Research Questions

1. **What is OpenSpec, mechanically** — not the marketing (63.6k stars, "artifact-guided workflow"), the actual protocol?
2. Given the brief's focus — **how does each frame drive quality, and how does each manage token cost** — where do the two diverge, and why?
3. **Agent and model routing**, specifically: does either system route different tasks to different agents or different model weights, and on what basis?
4. What's genuinely remarkable that Writ should reconsider? Where does Writ hold durable advantages?

---

## Executive Summary

OpenSpec is a **real, compiled, tested CLI application** (37.5k LOC TypeScript, 119 Vitest files, ESLint, changesets, CI) that generates skill/command files for **30+ AI tools** from a **schema-driven artifact graph** — a declarative YAML dependency DAG (proposal → specs/design → tasks → apply → archive) resolved by deterministic code: topological build order, cycle detection, blocked/ready/all-done state computed by scanning the filesystem. This is genuinely more rigorous *engineering* than anything in Writ's product source, which is pure markdown interpreted by an LLM with no compiled validator standing behind it.

But mechanically, OpenSpec is **single-agent and single-model, by design**. One assistant session drafts the proposal, writes the specs, writes the design, implements every task, and self-verifies the result — sequentially, in one context, at whichever model the human happens to be running. There is no multi-agent gate, no subagent spawning, no built-in second opinion, and no model-cost tiering anywhere in the shipped product (confirmed by grep: zero routing/model-selection logic exists in `src/`). The project's own guidance is the opposite of tiering: *"OpenSpec works best with high-reasoning models. We recommend Codex 5.5 and Opus 4.7 for **both** planning and implementation"* — run the most expensive model you have, for everything, and manage token cost by **manually clearing your context window** before implementation. Quality assurance is a single heuristic self-review skill (`openspec-verify-change`) that does keyword search and "reasonable inference," explicitly biased to under-report ("prefer SUGGESTION over WARNING, WARNING over CRITICAL, when uncertain") — not test execution, not coverage measurement, not a second reviewer.

Writ is the inverse bet on both axes the user asked about. Quality is driven by a **6-gate multi-agent pipeline** (architecture check → TDD coding → lint → review-with-drift-classification → coverage-gated testing → visual QA → docs) where a FAIL loops back rather than self-reporting a severity and moving on. Token cost is managed by **two independent, automated mechanisms working together**: a budgeted `spec-lite.md` (<100 lines, hard limit) generated once per spec and re-read by every downstream agent instead of the full spec, and an **enforced `model_tier`** on every agent (`orchestration` vs `capability`, ADR-016) that actually routes read-only/high-fan-out steps (architecture scan, parallel user-story drafting) to a cheaper/faster model while reserving full weight for the steps where mistakes are expensive (coding, review, testing, docs). Neither is a suggestion the human has to remember to act on — both are structural.

**The sharpest, most consequential divergence in the entire comparison is architecture, not detail: OpenSpec's quality story runs through one model doing everything with self-graded honesty; Writ's runs through multiple models at different weights checking each other.** Everything else — token efficiency, drift handling, autonomy, extensibility — traces back to that one fork in the road.

---

## Side-by-Side

| Dimension | Writ (local 0.24.0) | OpenSpec (v1.7.0) |
|---|---|---|
| **What it is** | Markdown methodology, no build, no compiled code | Real npm CLI package: 37.5k LOC TypeScript, 119 test files, ESLint, changesets, CI |
| **Distribution / reach** | Cursor, Claude Code, Codex, OpenClaw (4 adapters) | 30+ AI tools via generated skill/command files (Cursor, Claude Code, Copilot, Codex, Gemini CLI, Devin Desktop, Amazon Q, Kimi Code, Qoder, Roo, Trae, ZCode, Hermes, shared `.agents/skills`, …) |
| **Community scale** | Solo/early-stage | 63.6k stars, 4.4k forks, 725 commits, Discord, `SECURITY.md`, `MAINTAINERS.md` |
| **Workflow state model** | Agent-interpreted `.writ/` convention + regenerated `.writ/context.md`; DAG expressed in story frontmatter | **Deterministic engine**: YAML `schema.yaml` → `ArtifactGraph` (topological order, cycle detection, blocked/ready/all-done via filesystem scan), exposed as JSON (`openspec status --json`, `openspec instructions <id> --json`) |
| **Unit of work** | Roadmap phase → spec → user story → agent gates | "Change" → schema-defined artifacts (proposal/specs/design/tasks by default) → tasks loop |
| **Agent model** | **Multi-agent**: 6 gated roles (arch-check, coding, review, testing, docs, visual-qa) spawned per story | **Single-agent**: one session does propose + design + implement + verify, sequentially, same context |
| **Model routing** | **Enforced `model_tier`** (ADR-016) per agent: `capability` (cheap/fast) for arch-check + parallel story drafting; `orchestration` (full weight) for coding/review/testing/docs/visual-qa | **None.** Zero routing logic in `src/` (verified by grep). Docs recommend the *same* top-tier model (Codex 5.5 / Opus 4.7) for planning **and** implementation |
| **Quality gate mechanism** | TDD + coverage ≥80% (enforced by testing-agent) + PASS/FAIL review agent (max 3 iterations) + drift severity classification | Heuristic self-review skill: keyword search + "reasonable inference" over Completeness/Correctness/Coherence; explicitly tolerant of false negatives; **no test-execution or coverage requirement in core** |
| **Second opinion / adversarial review** | Review Agent is a distinct gate, always runs | None in core. Exists only in a **third-party** community schema (`anvil`): "a second model when one is available," and even then "OpenSpec only checks that artifacts exist — enforce the gate with your own CI or hook" |
| **Token efficiency: content** | `spec-lite.md` <100 lines (hard budget, ~35/35/30 line split per agent section) + per-story indexed "Context for Agents" hints + What-Was-Built from dependencies only | `openspec instructions <id> --json` returns a **per-artifact** payload (`context`/`rules`/`template`/`instruction`/`dependencies`) instead of the whole doc tree — real and useful, but every dependency file is still read **in full** from disk each step; no compression tier |
| **Token efficiency: cost** | Automated — `capability`-tier agents run cheaper by construction, no user action required | **Manual** — FAQ instructs users to "clear your context before implementation," and to run the *most expensive* available model throughout; no automated cost-down path exists |
| **Contract negotiation** | Plan Mode discovery → locked contract before any file is written | Q&A-lite propose skill drafts all artifacts (proposal/specs/design/tasks) in one pass; user reviews after the fact, edits fluidly at any time |
| **Drift handling** | First-class Small/Medium/Large classification, auto-amends `spec-lite.md` for Small, logs it | None automated; `/opsx:verify` flags spec/code mismatches heuristically, human reconciles by hand |
| **Autonomy** | `--recommend` on exactly 2 commands, evidence-bound select-or-pause, audit trail, never auto-merge/release | None — always fully human-paced, no autonomous mode anywhere |
| **Governance / self-scrutiny** | Prime Directive (eval-enforced anti-sycophancy), leanness tripwire (ADR-015), `/refresh-command` requiring transcript evidence | None over methodology quality — CI/tests/lint are rigor for the **CLI's own code**, not for how well specs/code produced *through* it turn out |
| **Provenance / audit trail** | "What Was Built" records in story files + `.writ/state/*.json` | Archived changes move to `openspec/changes/archive/YYYY-MM-DD-<name>/`, preserved intact — coarse-grained, no per-step audit note |
| **Ceremony scaling** | `/prototype`, `--quick` (flag-based, no structured marker) | `skip_specs: true` change metadata — **schema-validated**, visible in `status` as "specs: explicitly skipped," rejected if a delta spec is also present |
| **Extensibility** | First-party skills only; ADR-018 reserves a 3p trust model, not yet built | Live today: `openspec schema fork` + a documented community-schema table (5 third-party schemas: adversarial review, PM-first, E2E runbooks, ADR bridge, Superpowers bridge) — no frozen-commit/trust label, just an editorial docs table |
| **Multi-repo / team** | Explicitly deferred (ADR-007) | **Stores (beta)**: a standalone planning repo any code repo can reference, shared via `git push` |
| **Fluid editing** | Supported via `/edit-spec`, somewhat exception-shaped | First-class design tenet — every skill's guardrails include a "Fluid Workflow Integration" section; editing artifacts *is* the steering mechanism, not a workaround |

---

## Deep Dive: The Three Dimensions the Brief Asked For

### 1. Driving quality

OpenSpec's quality theory of the case is **agreement, not verification**: get the human and the AI to write down the same plan before code exists, so the AI isn't filling gaps with silent guesses. That's a real and valuable failure mode to close — "AI assistants are confident even when they're wrong" (FAQ) — and the spec-first discipline (concrete Given/When/Then scenarios, delta specs for edits) is philosophically identical to Writ's contract-first stance. Where it stops is *after* the plan: `openspec-apply-change` has no TDD requirement, no coverage gate, and no instruction to run the test suite as a pass/fail condition before marking a task `[x]`. The only in-product check is `openspec-verify-change`, a **single-pass, single-model heuristic**: it greps the codebase for requirement keywords, "assesses if implementation likely exists," and is explicitly designed to avoid false positives by downgrading uncertainty to SUGGESTION. That is closer to a self-administered checklist than a review gate — there is no second party, human or model, who could disagree with the implementing agent's own account of its work, unless you install a third-party schema (`anvil`) that adds one, and even that schema's author notes the platform "only checks that artifacts exist" — the adversarial gate has to be enforced by your own CI, outside OpenSpec entirely.

Writ's quality theory of the case is **verification through disagreement**: a distinct Review Agent (PASS/FAIL, max 3 iterations) and a distinct Testing Agent (coverage ≥80%, enforced) sit downstream of the Coding Agent and can force rework, and an Architecture-Check Agent runs *before* any code exists specifically to catch a bad plan before it's expensive to unwind. That is categorically more expensive — every story pays for up to three extra agent invocations — and categorically harder to fool, because the reviewer is not the same session (and, by `model_tier`, not necessarily even the same model weight) that wrote the code.

**Honest read:** OpenSpec's approach is well-suited to its own recommended usage pattern (one very strong model, human reviews at natural pause points, git diff is the real gate). It under-specifies quality assurance if the human doesn't review carefully — the built-in "verify" skill is not a substitute for a human or a second model actually checking the work, and its own heuristics say so implicitly by erring toward silence. Writ pays a real token/latency cost to make that check structural rather than optional.

### 2. Token efficiency

Both systems solved the "don't reload the whole plan every step" problem, but at different layers and to different degrees. OpenSpec's `openspec instructions <artifact-id> --change "<name>" --json` is a clean piece of engineering: it returns exactly the `context`, `rules`, `template`, and `instruction` relevant to *one* artifact, not the whole `openspec/` tree — a real token savings over naively concatenating every doc every time. But it stops at *scoping*, not *compressing*: the agent is still told to "read any completed dependency files for context — always re-read them from disk," in full. There is no analogue to a budgeted digest. And the project's own FAQ concedes the residual cost is real: *"keep your context window clean... clear it before implementation for best results"* — a manual step the human has to remember and execute, with no tooling to enforce or even remind.

Writ's `spec-lite.md` is a compression artifact, not just a scoping API: capped at <100 lines with an enforced per-section budget (~35/35/30 lines), generated once during `create-spec` and re-read by every downstream agent instead of the full `spec.md`. Combined with per-story "Context for Agents" hints (indexed pointers into the fuller spec, not copies of it) and What-Was-Built records passed only from direct dependencies, the token bill for a downstream agent is a small, designed object — not "the full file, scoped to fewer files."

**Honest read:** this is not a close call. OpenSpec's per-artifact JSON API is good practice and better than dumping everything; Writ's spec-lite is a stronger token-efficiency mechanism because it compresses content, not just scope, and does so automatically rather than asking the human to manage the context window by hand.

### 3. Agent and model routing — the sharpest divergence

This is where the two frameworks stop resembling variations on a theme and become different architectures entirely. A grep of OpenSpec's full TypeScript source for `model` selection logic returns **nothing** — no routing table, no cost tier, no per-skill model hint. The product's own stance is explicit and is the opposite of routing: use one high-reasoning model, the same one, for both planning and implementation, and manage cost by clearing context rather than by choosing a cheaper model for cheaper work. The only place a second model appears anywhere in the OpenSpec ecosystem is a third-party community schema's design note ("a second model when one is available") — not a mechanism OpenSpec ships, resolves, or enforces.

Writ ships an enforced, if intentionally narrow (2-band), routing contract (ADR-016): every agent declares `model_tier: orchestration` or `model_tier: capability` in its Agent Configuration block, and a command spawning that agent actually passes a resolved model — not an intention, an enforced pass at spawn time. The assignment is not decorative: `architecture-check-agent` (read-only, pattern-matching a codebase) and `user-story-generator` (fanned out in parallel, one invocation per story, each individually low-stakes because downstream gates verify the output anyway) both run at `capability` — cheap and fast. `coding-agent`, `review-agent`, `testing-agent`, `documentation-agent`, and `visual-qa-agent` all run at `orchestration` — full weight, because that's where an under-powered model is most likely to produce a plausible-but-wrong result that later gates would then have to catch at higher cost. Graceful degradation (unresolvable tier → warn, fall back to inherit) means the routing never hard-fails; a dated review trigger (2026-10-16) keeps the reserved N-step ordinal form honest about being unbuilt rather than quietly rotting.

**Honest read:** OpenSpec's choice isn't unreasonable — a single frontier model doing everything, human-reviewed at natural checkpoints, is a legitimate and popular way to work, and it's the load-bearing assumption behind the whole product (hence the explicit "we recommend Codex 5.5 and Opus 4.7" guidance rather than a tiering feature). But it means OpenSpec has made zero investment in the specific dimension the user asked about. Writ has made a real, if currently coarse, investment: a structural place where "this task doesn't need the expensive model" and "this task absolutely does" are different, enforced facts about the pipeline rather than a human's implicit judgment about which chat window to open.

---

## What Is Genuinely Remarkable (Reconsider for Writ)

### 1. A compiled, deterministic engine behind DAG-critical state — worth a narrow borrow

OpenSpec's `ArtifactGraph` (topological build order, cycle detection, "invalid dependency reference," "duplicate artifact IDs rejected" — all backed by real code and tests, not agent judgment) is a structurally stronger guarantee than Writ's equivalent: user-story dependency frontmatter and phase sequencing that an LLM has to correctly parse and honor every time `implement-phase` batches work. Writ doesn't need OpenSpec's full schema-fork generality, but a small, focused validator — even a single `scripts/eval-story-deps.py`-style script that checks for cycles and dangling dependency references in a spec's user-story set before `implement-phase` starts batching — would move one of Writ's highest-consequence steps (parallel batch construction) from "the orchestrating agent has to get this right" to "a program already checked."

**Fit:** narrow, additive. Does not require adopting OpenSpec's schema/YAML model — Writ already has `eval-spec-deps.py` in the eval suite; worth checking whether it already does this and, if not, whether it should run pre-execution rather than post-hoc.

### 2. `skip_specs: true` — a validated ceremony-reduction marker, not just a flag

OpenSpec's `skip_specs` is schema-aware: `openspec validate` accepts it only for genuinely zero-delta changes, rejects it if a delta spec is also present (contradiction caught by code), and `openspec status` renders the specs stage as "explicitly skipped" rather than just absent. Writ's `/prototype` and `--quick` achieve a similar ceremony reduction but leave no structured, queryable record of *why* a step was skipped — `/status` or `/verify-spec` can't currently distinguish "never got around to it" from "deliberately and validly skipped."

**Fit:** a small enhancement to spec/story metadata (a `ceremony: reduced` or `skip_reason:` field readable by `/verify-spec` and `/status`) would close this gap without adopting OpenSpec's schema engine.

### 3. Stores (beta) — a live reference for the multi-repo scenario ADR-007 deferred

OpenSpec's Stores feature (a standalone planning repo any code repo can point at, resolved via `--store <id>` or a machine-level default) is a shipped, if beta, answer to exactly the cross-repo/team scenario ADR-007 explicitly declined to build ahead of demand. No action needed now — but it's worth knowing a working implementation exists to study if/when ADR-007's trigger fires, rather than designing from scratch.

### 4. Fluid editing as a first-class tenet, not an exception path

Every OpenSpec skill's guardrails include a "Fluid Workflow Integration" section stating plainly that the skill can be invoked "before all artifacts are done," "interleaved with other actions," and that artifact updates are expected mid-flow, not a special case. Writ has the equivalent capability (`/edit-spec`, drift classification) but it reads more like a recovery path than a designed-in expectation. Not a functional gap — a documentation/framing lesson: consider whether Writ's core commands should state their fluid-editing posture as plainly and as early as OpenSpec's skills do.

---

## Where Writ Holds Clear Advantages

1. **Enforced multi-agent, multi-tier quality pipeline** — architecture check, TDD coding, lint, review-with-drift, coverage-gated testing, visual QA, docs, with a real reviewer distinct from the implementer. OpenSpec has no analogue in core; the closest thing is a third-party schema note that even its own author says isn't platform-enforced.
2. **Enforced model-cost routing tied to role risk** (ADR-016) — the dimension the brief asked about most directly. OpenSpec has zero model-routing code anywhere in its shipped source.
3. **Automated token compression** (`spec-lite.md` budget + indexed context hints + scoped WWB) vs. OpenSpec's scoped-but-uncompressed per-artifact API plus a manual "clear your context" instruction to the human.
4. **Drift as a first-class, classified artifact** (Small/Medium/Large, auto-amend for Small) vs. OpenSpec's heuristic post-hoc mismatch flagging with no severity model.
5. **Governance over the methodology itself** — Prime Directive anti-sycophancy eval, leanness tripwire, evidence-bound `/refresh-command`. OpenSpec's considerable engineering rigor (Vitest, ESLint, CI) governs the CLI's own correctness, not the quality of specs/code produced through it.
6. **Bounded, audited autonomy** (`--recommend`) — OpenSpec has no autonomous mode of any kind; every step is always human-paced.
7. **Per-step provenance** (What Was Built records) vs. OpenSpec's coarse archive-folder-as-record.

---

## Where OpenSpec Holds Clear Advantages

1. **It's a real, tested, compiled program.** 37.5k LOC, 119 test files, ESLint, CI, changesets-based release train. Its own correctness (schema loading, dependency resolution, artifact-state detection) is machine-verified, not agent-interpreted. Writ's equivalent state logic is markdown an LLM has to read correctly every time.
2. **Platform reach.** 30+ generated tool integrations from one adapter-generation engine, versus Writ's 4 hand-maintained adapter docs. This is a genuine distribution and maintenance-leverage advantage.
3. **Battle-tested at massive scale.** 63.6k stars, 4.4k forks, 725 commits, an active Discord, `MAINTAINERS.md`, `SECURITY.md`. Whatever edge cases exist in a schema-driven artifact-graph CLI, a project this size has likely already hit and fixed many of them.
4. **Live, working extensibility.** `openspec schema fork` plus a documented community-schema table is a lower-friction path to third-party workflow variants (adversarial review, PM-first planning, E2E runbooks) than Writ's not-yet-built ADR-018 trust model.
5. **Stores (beta)** ships an answer to multi-repo/team planning that Writ has only deferred.
6. **Fluid-by-design framing**, stated plainly in every skill rather than positioned as a recovery path.

---

## Divergence Diagnosis

| Pressure | OpenSpec's response | Writ's response |
|---|---|---|
| "Is the AI's plan right?" | Agreement via written specs before code; single-model heuristic self-check after | Contract-first lock in Plan Mode; distinct multi-agent review gate after |
| "Is the AI's code right?" | No built-in TDD/coverage gate; trust the model + human review | TDD + coverage ≥80% enforced by a dedicated Testing Agent |
| Model cost | Recommend the strongest model for everything; manage cost by manually clearing context | Route cheap/fast model to low-stakes fan-out steps; full weight only where mistakes are expensive (ADR-016) |
| Token bloat | Scope context per-artifact via a JSON API; still read full dependency files | Compress context per-agent via a hard-budgeted `spec-lite.md` + indexed hints |
| Workflow correctness | Deterministic compiled graph engine (cycle detection, topological order) | Agent-interpreted markdown DAG (frontmatter + phase sequencing) |
| Extensibility | Forkable YAML schemas + documented community table | First-party skills only; 3p trust model reserved, not built |
| Autonomy | None — always human-paced | Bounded `--recommend` with audit trail on exactly 2 commands |
| Distribution | 30+ generated tool adapters from one engine | 4 hand-written adapter docs |

They are optimizing for different failure modes. OpenSpec is defending against **"the AI built the wrong thing because nobody wrote down what 'right' meant"** — and it defends that specific failure mode extremely well, with real engineering behind the bookkeeping. Writ is defending against **"the AI built the wrong thing (or a badly-tested thing) even though everyone agreed what 'right' meant"** — a failure mode OpenSpec's single-pass, self-graded model is structurally under-defended against unless the human catches it.

---

## Recommendations (Prioritized)

| Priority | Action | Rationale |
|---|---|---|
| **P1** | Do **not** move toward OpenSpec's single-model, single-agent default. Writ's enforced multi-tier routing (ADR-016) and multi-agent review gate are the more defensible quality/cost story for exactly the dimensions this brief asked about. | OpenSpec's own docs concede its model is "use the most expensive model for everything, manage cost by hand" — the opposite of a routing strategy. |
| **P2** | Add a small deterministic validator for user-story/spec dependency graphs (cycle + dangling-reference checks) that runs *before* `implement-phase` batches parallel work, if `eval-spec-deps.py` doesn't already run pre-execution. | Borrows OpenSpec's strongest idea (code-verified graph state) without adopting its schema/YAML generality. |
| **P3** | Consider a structured `skip_reason:`/`ceremony:` marker for `/prototype` and `--quick`, queryable by `/status` and `/verify-spec`. | Mirrors `skip_specs`'s validator-visible marker; closes a small observability gap at low cost. |
| **P4** | No action on Stores/multi-repo — continue treating ADR-007's trigger as the gate, with OpenSpec's Stores as a reference implementation if/when it fires. | Consistent with Writ's own market-signal discipline. |
| **P5** | State Writ's fluid-editing posture (drift classification, `/edit-spec`) as plainly and as early in relevant commands as OpenSpec states it in every skill's guardrails. | Framing lesson, not a functional gap. |

---

## Honest Caveats

- Analysis is of public `main` at commit `45cca5d` (2026-07-31); OpenSpec ships weekly-or-faster (`CHANGELOG.md` shows multiple minor releases in the days before this analysis), so specifics may already have shifted.
- OpenSpec's 63.6k-star scale means its single-model, heuristic-verification approach is clearly working well enough for a very large population of real users and real PRs — that's strong outside evidence its bet is viable, not merely untested. This analysis argues Writ's bet is *more defensible on the specific quality/cost axes the brief asked about*, not that OpenSpec's approach fails in practice.
- The `anvil` and other community schemas are third-party, unvendored, and not verified by this analysis beyond their description in `docs/customization.md` — the "second model when available" claim is read from documentation, not from running the schema.
- Writ's `model_tier` is a 2-band system today (ADR-016 documents a reserved N-step ordinal form with a 2026-10-16 review trigger that hasn't fired yet); this analysis credits the mechanism that exists and is enforced, not the reserved-but-unbuilt finer-grained version.
- Line-count/LOC comparisons across a markdown methodology (Writ) and a compiled TypeScript CLI (OpenSpec) measure different things and are not a quality proxy in either direction — cited here only to establish that OpenSpec's determinism claims are backed by real, tested code.

---

## Sources

- https://github.com/Fission-AI/OpenSpec (shallow clone, commit `45cca5d`, 2026-07-31)
- `README.md`, `CHANGELOG.md`, `package.json`, `docs/faq.md`, `docs/overview.md`, `docs/customization.md`, `docs/supported-tools.md`, `docs/existing-projects.md`, `docs/editing-changes.md`
- `skills/openspec-propose/SKILL.md`, `openspec-apply-change/SKILL.md`, `openspec-explore/SKILL.md`, `openspec-verify-change/SKILL.md`, `openspec-sync-specs/SKILL.md`
- `openspec/specs/artifact-graph/spec.md`, `openspec/specs/context-injection/spec.md` (OpenSpec's own self-authored specs)
- `src/` (37.5k LOC TypeScript, grepped for model-selection logic — none found)
- Writ: `agents/*.md` (model_tier assignments), `.writ/decision-records/adr-016-model-tier-delegation.md`, `commands/create-spec.md` (spec-lite budget), prior research `2026-07-20-writ-vs-code-captain-analysis.md`, `2026-07-18-writ-vs-conductor-analysis.md`
