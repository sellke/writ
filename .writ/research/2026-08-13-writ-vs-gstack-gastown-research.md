# Writ vs. GStack and Gas Town — And Why That Is the Wrong Comparison (August 2026)

**Date:** 2026-08-13
**Status:** Complete
**Subject:** [garrytan/gstack](https://github.com/garrytan/gstack) v1.62.0.0 (127,795 ★, 12 contributors, MIT) · [gastownhall/gastown](https://github.com/gastownhall/gastown) v1.2.1 (17,596 ★, 241 contributors, MIT) · Writ at `VERSION` 0.31.0
**Framing:** Writ evaluated as a **personal instrument** — an amplifier for one developer's output — not as a product seeking adoption. Adoption metrics are therefore reported as context, never as a scorecard.
**Method:** GitHub REST API read live 2026-08-13 for all counts. Repo-internal measurements re-run at authoring time and recorded with their commands (see [Measurement appendix](#appendix-b--measurement-commands)) per the lesson in `../knowledge/lessons/2026-08-11-technical-specs-written-from-unre-run-grep-counts-ship-wrong-measurements.md`. Competitive set surveyed across 16 spec-driven frameworks plus four academic papers. Vendor claims labeled as claims; third-party observation labeled as observation; anything I could not confirm labeled `unverified`.
**Supersedes for GStack:** `2026-04-24-writ-vs-gstack-rigor-comparison.md`, whose own "Honest Open Questions" asked whether to re-run this in six months. This is that re-run, and it lands harder.

---

## Research Questions

1. Where does Writ actually sit relative to GStack and Gas Town — and is that the right axis of comparison at all?
2. Judged as a personal instrument, does Writ make its single user more effective at shipping software?
3. Which of Writ's mechanisms are genuinely differentiated, and which are ceremony?
4. What should be borrowed from the field, and what should be deleted from Writ?

---

## Executive Summary

**The supplied comparison asks the wrong question of Writ.** GStack is a 53-skill prompt-and-process pack that borrows nearly all its parallelism from an external Mac app; Gas Town is a Go binary with a scheduler, mail router, and Bors-style merge queue built to keep 20–30 agents busy at roughly $100/hour. They are not competitors of each other in any clean sense, and neither is a competitor of Writ. Writ's actual category is spec-driven development, and that category's members are GitHub Spec Kit (127.8k ★, Microsoft-backed, with a Microsoft Learn training module), OpenSpec (64.8k ★), Amazon Kiro (GA, with Amazon Q Developer being sunset in its favor), Superpowers (271.6k ★, accepted into Anthropic's official plugin marketplace), and Agent OS. Read against *that* field, Writ is neither behind on rigor nor lost in the pile — it holds three mechanisms almost nobody else has.

**Those three mechanisms are real and worth naming precisely.** `scripts/exit-criteria.py` re-derives each exit criterion's verdict from disk and its verdict *overrides the run's own completion banner* — a run may report COMPLETE and be published as `unmet`. `scripts/story-deps.py` computes a deterministic topological batch order and halts before execution on an invalid graph. And drift-triage plus What Was Built records give structured spec↔implementation reconciliation. In a June 2026 survey of 16 frameworks, deterministic dependency graphs scored "No" across every single tool; drift reconciliation exists only partially in Kiro and GSD; and machine-checked exit criteria exist meaningfully only in Kiro, by a different mechanism (property-based tests). Writ is not a lesser Spec Kit. On verification architecture it is ahead of the institutional leader.

**And none of it has ever run against application code.** All 57 specs in the archive are about Writ. All 21 knowledge-ledger entries are about Writ's own meta-tooling — lane worktrees, byte metrics, governor tests. Not one is about building software. `CLAUDE.md` states the dogfood repo has "no application code, no build step, no test suite, and no dependencies," which means Gate 2 (typecheck/lint), Gate 4 (mandatory ≥80% coverage), Gate 4.5 (visual QA), and `/implement-spec`'s Phase 4 full-suite run have never once fired against the workload they exist for. Meanwhile the apparatus that governs the markdown is **2.7× the size of the product itself** (2.20 MB of `eval*` and tests against 803 KB of commands, agents, skills, and adapters), 265 UAT scenarios have been written of which **exactly one** has been executed, and 302 of 445 commits landed in the last six weeks on work whose every subject was Writ governing Writ.

**The primary recommendation is therefore singular and uncomfortable: stop building Writ and use it.** Not as a metaphor — as the next unit of work. Run Writ on a codebase with a build, tests, dependencies, and users for four to six weeks, touching the framework only through `/refresh-command` with evidence cited from that use. Two independent sources, one academic and one community-analytic, identify the absent efficacy benchmark as the largest gap in the entire spec-driven category. Writ already owns the instrumentation to produce one. It has never pointed it outward.

---

## Part I — The Category Error

### Finding 1: GStack and Gas Town sit at layers Writ does not occupy

The supplied document's central correction is right and worth keeping: these two are not symmetric alternatives. But the taxonomy needs one more axis to locate Writ.

| | GStack | Gas Town | Writ |
|---|---|---|---|
| Layer | Prompt/process pack | Process-model orchestrator | Contract/verification layer |
| Optimizes | Velocity per human-hour | Throughput per fleet | Durability of intent |
| Unit of work | A slash command = a persona | A bead on an agent's hook | A story under a locked spec contract |
| Parallelism | Mostly external (Conductor) | Native (Mayor spawns Polecats, capacity scheduler) | Deterministic batches; sequential phase lanes by choice |
| Persistence | Git + `learnings.jsonl` + gbrain | Beads on Dolt + hooks | Markdown in git, canonical by [ADR-011](../decision-records/adr-011-memory-interop-markdown-canonical.md) |
| Stated ceiling | "10–15 parallel sprints… practical max" | "20–30 agents" | One supervised phase, session-bound ([ADR-010](../decision-records/adr-010-supervised-autonomy-ceiling.md)) |
| Concepts to learn | ~7 | ~20 | ~21 (Finding 6) |

Writ's own [mission.md](../product/mission.md) already declines both fights explicitly — "Not a velocity-first sprint flow… Parallel-sprint frameworks (GStack) target a different problem" and "Not an opaque, unbounded loop runner." Those calls remain correct, and the evidence for them has strengthened since they were written:

- **Gas Town's cost is structural, not a bug.** DoltHub's Tim Sehn, a paying user, wrote in [A Week In Gas Town](https://www.dolthub.com/blog/2026-03-24-a-week-in-gas-town/): *"I previously reported Gas Town spends about $100/hours and this seems about right"* — $3,000 for one week at 6–8 hours a day. Neil Macneale reported [~$6,000 over two weeks](https://www.dolthub.com/blog/2026-04-16-two-weeks-in-gastown/) at a peak of 13 polecats. Both explicitly noted they were on API pricing, not a Max subscription, and both flagged that as an untested cheaper path.
- **Gas Town's release cadence has stalled.** Live check today: `pushed_at` is 2026-08-13, but **main's HEAD is 2026-07-23**, there has been **no release since 2026-06-06** (v1.2.1), and the CHANGELOG's `## [Unreleased]` section is **empty** despite 302 commits on main since June 1. High commit volume across 138 branches, stalled releases, unmaintained changelog. Do not model it as a fast-moving target.
- **GStack's breadth does not convert.** GStack's own telemetry, published in its v1.58.5.0 release notes (~23,839 distinct installs, March–June 2026): **~21% of installs never run any skill** and **~30% are one-and-done**. A third-party reviewer who [used it for a month](https://claude-codex.fr/en/content/garry-tan-stack-claude-code/) found only **6 of 35 commands delivered lasting value** for non-startup teams. This is the strongest available evidence that command-surface breadth is not the same as command-surface use — and it is evidence Writ should read as being about Writ.

**Implication.** The supplied document's "do both" recommendation (Gas Town as substrate, GStack as per-agent process) is architecturally sound and irrelevant to Writ. What Writ should absorb from it is not the architecture but the cost-and-blast-radius discipline: the reason to reject the Gas Town shape is not distaste for orchestration, it is that a $100/hour autonomous merge authority is a bad trade for one person, and Writ's human production boundary ([ADR-013](../decision-records/adr-013-recommended-autonomous-delivery.md), [ADR-022](../decision-records/adr-022-autonomy-gate-classes.md)) already encodes that judgment.

### Finding 2: The real field, and where Writ places in it

| Framework | Adoption | Executable gates | Dependency DAG | Drift reconciliation |
|---|---|---|---|---|
| [Superpowers](https://github.com/obra/superpowers) | 271.6k ★, Anthropic marketplace | Process interlocks: tests must pass, critical review blocks, plan-compliance precedes quality review | No | No |
| [Spec Kit](https://github.com/github/spec-kit) | 127.8k ★, Microsoft | **Artifact existence only** (`check-prerequisites.sh`); `/speckit.analyze` is LLM-judged | No | No — filled by third-party [spec-kit-reconcile](https://github.com/stn1slv/spec-kit-reconcile), [spec-kit-sync](https://github.com/bgervin/spec-kit-sync) |
| [OpenSpec](https://github.com/Fission-AI/OpenSpec) | 64.8k ★ | **Structure only** — Zod schemas; explicitly "does not run tests" | No | No — [open proposal #880](https://github.com/Fission-AI/OpenSpec/issues/880) |
| [Amazon Kiro](https://kiro.dev/blog/property-based-testing/) | GA; Q Developer sunset in its favor | **Yes** — EARS criteria → Hypothesis properties → pytest, shrunk counterexamples | No | Partial — surfaces conflict, human triggers refresh; [git-ref drift is issue #9435, unshipped](https://github.com/kirodotdev/Kiro/issues/9435) |
| [BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) | ~49k ★ | None — persona role-play | No | No |
| [Agent OS](https://github.com/buildermethods/agent-os) v3 | ~4.8k ★ | None | No | No |
| GSD | ~60k ★ | Formal gate taxonomy | No | Partial — adversarial verifier |
| **Writ** | 8 ★, 1 contributor | **Yes** — `exit-criteria.py`, checker verdict governs; 41 blocking/warning eval checks; coverage-gated Gate 4 | **Yes** — `story-deps.py` topological batches, halts on invalid graph | **Yes** — drift-triage severity → amend/warn/pause; What Was Built |

Two independent assessments support the "almost nobody" reading. A [competitor's 16-tool matrix](https://github.com/nino-chavez/blueprint/blob/main/research/03-sdd-landscape-2026-06.md) (June 2026 — an interested source, positioned to find whitespace for its own tool, so treat its negatives as informed-but-motivated) scores **dependency graphs "No" across all 16 tools it assessed**. And an academic process taxonomy, [arXiv 2606.04967](https://arxiv.org/abs/2606.04967), assessed six frameworks across six dimensions and concluded verbatim: *"no framework strongly covers all six dimensions, exposing a structural trade-off between process depth and portability across agents"* — with **"drift between specification and code"** leading its list of recurring risks.

**The honest boundary on Writ's advantage.** Writ's gates are markdown instructions interpreted by an LLM. What is genuinely deterministic is the Python underneath: `exit-criteria.py` (read-only by construction, exit codes 0/1/2), `phase-state.py` (fail-closed reducer, atomic writes, enforced status vocabulary), `story-deps.py`, `spec-status.py validate`. Kiro's advantage is the inverse and should not be minimized — it *executes spec-derived properties against code*, which is a stronger claim than anything Writ makes, even though Kiro's oracle is itself LLM-authored and its specs are IDE-only, unavailable in CLI mode. Writ verifies that the *process* reached its declared criteria. Kiro verifies that the *code* satisfies the spec. Those are different guarantees and Writ should stop conflating them.

### Finding 3: The threat model is not GStack or Gas Town — it is subtraction

Two events in the last seven months matter more to Writ than anything in the supplied document.

**Agent OS v3 deleted the layer Writ has invested most in.** In [discussion #310](https://github.com/buildermethods/agent-os/discussions/310), Brian Casel shipped a version that *retires the v2 implementation and orchestration phases entirely* and *defers spec writing to Claude Code's native Plan Mode*, contributing only `/shape-spec` for standards-aware elicitation. His stated rationale: *"Today's frontier models handle spec implementation well on their own — this is the recommended approach in 2026+."* A framework author cut his own features on that reasoning. Writ's single largest investment is exactly that layer: `implement-story.md` (354 lines, 11 gates), `implement-spec.md` (329), `implement-phase.md` (353), plus `phase-state.py` (1,139 lines) and `recommend-state.py` (3,807 — the largest script in the repo).

**Tessl abandoned the purest form of Writ's thesis.** Guy Podjarny (Snyk founder) raised [$125M](https://tessl.io/blog/announcing-our-series-a-for-ai-native-software-development/) at a reported [~$750M valuation](https://finance.yahoo.com/news/exclusive-tessl-worth-reported-750-080100819.html) for spec-as-source: generated code marked `// GENERATED FROM SPEC - DO NOT EDIT`. On 2026-01-29 Tessl repositioned as ["Skills on Tessl: the package manager for agent skills."](https://www.tessl.io/) The Framework remains in beta roughly nine months on, not formally deprecated but no longer the company's position. Martin Fowler's framing explains the failure: spec-as-source buys near-zero drift by construction at the cost of high organizational friction and total dependence on a non-deterministic compiler.

Writ never made Tessl's bet — [ADR-005](../decision-records/adr-005-knowledge-substrate-markdown-over-database.md) and mission both keep code as code and markdown as contract. That was correct. But Agent OS is a live, directly adverse hypothesis about Writ's gated pipeline, and Writ has no evidence against it, because it has never measured the pipeline against the alternative.

---

## Part II — Findings Against Writ

The user asked for maximum candor and the Prime Directive applies to Writ itself. Every number below is re-derived at authoring time; the commands are in [Appendix B](#appendix-b--measurement-commands).

### Finding 4: The instrument has only ever been sharpened on itself

| Measurement | Value |
|---|---|
| Archived specs | 57 — every one about Writ |
| Knowledge-ledger entries | 21 — every one about Writ's meta-tooling |
| Application code in the dogfood repo | None, by `CLAUDE.md`'s own statement |

The knowledge ledger is the clearest evidence, because it is the artifact whose entire purpose is to compound. Its 21 entries are about lane-worktree gitignoring, phase-branch namespace collisions, byte metrics overstating load by an order of magnitude, governor silence needing its own test, and extraction-target selection by branchiness. These are lessons about maintaining Writ. There is not one entry about API design, schema migration, error handling, deployment, caching, auth, or any other subject a solo builder shipping a real product accumulates lessons about.

This is not dogfooding. Dogfooding means using a product for its stated purpose, and Writ's stated primary customer in [mission.md](../product/mission.md) is "solo builders shipping real products with AI," whose named pain is that "AI-generated code works in isolation but breaks at integration." Writ has been validated exclusively on a repository that cannot integrate, because it has nothing to integrate.

The consequence is mechanical, not rhetorical. These gates have never executed against the workload they were written for:

| Gate | Requirement | Status in the dogfood repo |
|---|---|---|
| Gate 2 | `tsc --noEmit` / `eslint` / `mypy` / `cargo check` | No typed source to check |
| Gate 4 | **≥80% line coverage on new files, mandatory**; coverage must not decrease | No coverage instrument for markdown |
| Gate 4.5 | Playwright capture vs. mockups, ≥85% match | No UI |
| `/implement-spec` Phase 4 | `npx tsc --noEmit && npm test` | No suite to run |

Writ's most stringent, most confidently specified gate — the one that produces the `⚠️ DEGRADED` terminal state and is documented as unrelabellable — has never run.

### Finding 5: The governance apparatus is 2.7× the product

| Surface | Bytes | Files |
|---|---|---|
| Product: `commands/` + `agents/` + `skills/` + `adapters/` | 802,974 | 59 |
| Governance: `scripts/eval*` + `scripts/tests/` | 2,195,039 | 85 |
| **Ratio** | **2.73×** | |

41 registered eval checks, 30 `eval-*.py` implementations, 53 test files — to verify markdown instruction files. `eval-leanness.py` alone is 1,752 lines. And Phase 10's own closure records that this apparatus was measuring the wrong quantity for months.

For a personal instrument this is the single most expensive line item in the repo, and its beneficiary is the instrument, not the user. A useful test: if the eval suite vanished tomorrow, what would break for someone shipping a product with Writ? The honest answer is that `gen-skill.sh --check` prevents a real drift class and the `structural` contract checks bite by mutation proof — and most of the remaining 39 checks guard properties only a maintainer of Writ can perceive.

### Finding 6: Writ built the conceptual surface it faults Gas Town for

The supplied document scores GStack at ~7 concepts and Gas Town at ~20, and identifies Gas Town's conceptual surface as "the single most-cited complaint about it," quoting Maggie Appleton's "baptism by fire" and colleagues finding it fit "the shape of Yegge's brain and no one else's."

Writ's vocabulary: spec, story, phase, lane, quarantine, drift log, boundary map, change surface, What Was Built, context hint, spec-lite, User Challenge, gate class, reversibility precondition, exit criteria, component contract, loop bound, skill lifecycle, leanness ratchet, byte budget, recommend-state. That is **~21** — parity with Gas Town, for one user, without Gas Town's 20–30 agent throughput to amortize the learning cost. Gas Town's complexity at least buys fleet coordination. Writ's buys self-verification of a methodology used by one person on one repository.

Relevant community data point: a reception analysis of Hacker News and r/ClaudeCode found *"spec-driven development" is lexicalized, but "gates" is NOT* — practitioners say phase, pipeline, verify, review, constitution. Writ's README leads with "Automated quality gates." Low stakes for a personal instrument, but it indicates the vocabulary was built inward.

### Finding 7: Four byte instruments — all non-blocking, one breached, one unwired

[ADR-023](../decision-records/adr-023-stakes-proportional-diligence.md) removed the byte budget's authority and kept it computed. That compromise has aged badly in one day.

| Instrument | Threshold | Live value | Severity |
|---|---|---|---|
| `BASE_BYTE_CAP` | 25,600 | **26,437** — over by 837 | `warnings` |
| `COMMAND_BYTE_BUDGET` | 24,960 | 6 recorded violators | `warnings` |
| ADR-019 per-surface ratchet | baseline deltas | commands rose to ~560k | `warnings` |
| `KNOWN_OVER_BUDGET` ratchet | one-way | 3 regressions in v0.31.0 | **not wired to CI** |

The base cap is the sharpest item. `eval-leanness.py` describes it as "the constraint the original rule was reaching for, pointed at the surface that actually deserves it" and its own fix text says *"Do not raise it to fit whatever was just added."* It is currently breached by 837 bytes (`system-instructions.md` 20,779 + `_preamble.md` 5,658 = 26,437) and nothing stops it, because the check ships `warnings`.

And `test_governor_enforcement.py`'s ratchet — the second-order guard over the recorded violators — appears in neither `scripts/eval.sh` nor `.github/workflows/eval.yml`, which runs exactly two steps. Commit `0d1f35f`'s own message records the consequence: *"it silently went red rather than blocking anything… This test caught all three only because it was run by hand."*

The pattern is a metric formally declared invalid, still computed, permanently warning, and partly unenforced. That is worse than deletion: it manufactures findings that must be triaged and dismissed forever, and it trains the maintainer to ignore the governor's output — which is precisely the ADR-021 reason-2 failure the whole apparatus was built to prevent.

### Finding 8: 265 UAT scenarios written; one executed

| Measurement | Value |
|---|---|
| `uat-plan.md` files | 15 |
| Scenarios | 265 |
| `**Status:** [ ] Pass [ ] Fail` — unexecuted template | **264** |
| Executed, with a recorded result | **1** |

The single execution is Scenario 20 of `2026-08-12-disclosure-implement-story`, run 2026-08-12 — and the roadmap records that it ran *after* the phase closure was written. Phase 9's 53 scenarios "await manual execution." Phase 8's GBrain round-trip awaits a machine that does not exist.

`/create-uat-plan` is, on this evidence, a generator of documents nobody reads. It is the literature's rubber-stamp failure in its purest form — *"specifiers becoming like overworked clerks blindly signing off on documents"* — except the sign-off never occurred at all. 0.4% execution over five months is not a backlog; it is a decision that has not been admitted.

This also quietly weakens several phase closures. Phase 6's first exit criterion was met "mechanically only," Phase 7's consolidation is "mechanism-complete only," Phase 8's first two criteria were "handed off to UAT" and "true by construction." Those are honest labels — Writ deserves real credit for writing them down rather than reframing them — but stacked up they mean a substantial fraction of declared capability has never been observed working.

### Finding 9: Recursive self-improvement became the work

445 commits total; **302 since 2026-07-01** — 68% of the project's history in six weeks. It is the most productive stretch by a wide margin. Its entire subject matter:

component-contract · loop-bounds · governor-instrumentation · autonomy-gate-classes · retire-dead-prescription · disclosure ×6 · phase-closure-status · governor-enforcement · machine-evaluable-exit-criteria · recalibrate-implement-loop · refactor-dirty-tree-guard

Every one is Writ governing Writ. Not one delivers capability to the stated user. Five releases shipped on 2026-08-12 alone.

Phase 10 is the clearest case, and it deserves a genuinely split verdict. It falsified its own central premise twice — the 516KB token alarm was a measurement artifact (worst real invocation 77,669 bytes, 7.2× smaller), and ADR-021's `required_skills:` mechanism turned out to pre-load eagerly rather than on demand, defeating the entire progressive-disclosure design. It then stopped its long pole on evidence, closed five sibling specs unimplemented with contracts kept as design records, and **voided its own central success criterion** via ADR-023 rather than quietly restating it. That intellectual honesty is rare and is the strongest evidence in the repo that the methodology can catch a maintainer's own bad idea.

But the counter-reading is equally supported: an entire phase, five releases, and a new ADR were consumed discovering that a metric the project invented was measuring the wrong thing. The pilot that did ship cut `implement-story`'s floor 35.9% *while adding eight decision points, five of which fire unconditionally and buy nothing*. A methodology whose most productive six weeks produced a better-instrumented version of itself and a correct retraction has demonstrated that its self-correction works. It has not demonstrated that its self-correction was worth six weeks.

### Finding 10: The one high-value borrow, with real published evidence

[arXiv 2606.30689](https://arxiv.org/html/2606.30689v1) (Panda, June 2026) is the most rigorous empirical work I found in the category: two controlled studies, 840 implementations across Claude Sonnet 4.6 and GLM-5-turbo, comparing mandatory per-line requirement-ID citations against Spec Kit's artifact-level traceability, OpenSpec's post-hoc YAML sidecars, and an uncited control.

- Mandatory inline citations enable automated hallucination detection via orphan-requirement checks at **86.4% (Claude) / 88.0% (GLM) true-detection rate, at 0% false positives**.
- **Uncited code, Spec Kit, and OpenSpec all score 0%** — their traceability granularity is too coarse to support detection at all.
- The cost, stated by the author: citations **significantly reduce output determinism** (d = −0.76, p = 0.003; d = −0.72, p < 0.001).
- Author-stated limits: Python only, 50–1,000 lines, hallucinations were *injected* with known-fake IDs, the Claude study is underpowered at N=20. Not production-validated.

Writ has story-level provenance — a commit SHA written into the story header (`story-commit-provenance` skill) and 7 live `refs/notes/writ` audit entries. It has no per-criterion IDs. Its specs already carry numbered acceptance criteria, so the gap is emission plus an orphan check. This lands squarely on the thing Writ claims as its moat — the contract layer — and makes it mechanically verifiable rather than merely reviewable. It is the only borrow in this document backed by a controlled study.

Worth noting what this finding implies about the rest of the field: what buys verifiability is *requirement-ID traceability*, not process ceremony. Spec Kit and OpenSpec both have extensive ceremony and score zero.

### Finding 11: The efficacy benchmark nobody has published

I looked specifically for evidence that spec-driven workflows beat ad-hoc prompting on delivery outcomes. **There is none for any named framework.** What exists:

- **Kiro's** property-based verification — vendor claim, no independent replication.
- **Spec Kit's** "order-of-magnitude fewer regenerate-from-scratch cycles" — I could not locate a GitHub primary source with methodology. `unverified`.
- **BMAD's** "90% token savings" — single-author anecdote, no methodology.
- The closest real result is [arXiv 2606.00167](https://arxiv.org/abs/2606.00167), which found richer security-requirement conditioning reduced failures against a hidden 221-test suite from 50 → 36 — a ~28% improvement, testing requirement conditioning rather than a full workflow.
- The productivity literature cuts both ways: GitHub's RCT found 55.8% faster completion; **METR's RCT found a 19% slowdown for experienced developers who nonetheless perceived a speedup**; DORA associates 25% AI adoption with a 7.2% drop in delivery stability.
- A [hands-on three-way test](https://dabase.com/blog/2026/sdd-framework-comparison/) of Spec Kit, OpenSpec, and GSD concluded **none substantially outperformed the author's existing informal approach**, citing slower iteration than direct conversation and alarming token burn.

Both [arXiv 2606.04967](https://arxiv.org/abs/2606.04967) (naming "a lack of benchmarks for the complete process") and the community reception analysis (listing "efficacy evidence with benchmarks" as the top unmet need) independently identify this as the field's central deficiency.

**This is the opportunity.** Writ is uniquely equipped to produce that evidence for itself: it has machine-checked exit criteria, per-invocation load measurement, a deterministic story graph, drift classification, and a `/prototype` path that deliberately skips the ceremony. The A/B is already built. It has never been run.

---

## Options Analysis

| Option | Pros | Cons | Effort | Risk |
|---|---|---|---|---|
| **A. Use Writ on a real product; measure gate value** | Only option that can falsify six months of work; produces the category's missing benchmark; fills the knowledge ledger with lessons about software | Requires a real project and a 4–6 week commitment; may return an unwelcome verdict on the pipeline | 4–6 weeks | Low technical, high ego |
| **B. Continue inward hardening** (eval Tier 2, cross-project corpus) | Extends existing momentum; comfortable; every tool already in hand | Compounds Findings 4–9; Tier 2 was already priced at "weeks" and deferred twice on cost | Weeks–months | High — deepens the trap |
| **C. Harness-native pivot** (Claude Code plugin, hooks, marketplace) | Superpowers proves the path at 271.6k ★; `claude-code/agents/` already has worktree isolation and model tiers | Contradicts adapter neutrality and [ADR-009](../decision-records/adr-009-command-agent-skill-boundary.md); irrelevant to a personal instrument; distribution is not the bottleneck | 1–2 weeks | Medium — solves a problem the user does not have |
| **D. Subtraction pass** (delete byte instruments, resolve `/create-uat-plan`) | Removes standing noise; applies Writ's own evidence standard to Writ; cheap | Deletes work recently built; feels like retreat | 2–4 days | Low |
| **E. Add per-criterion traceability + orphan check** | Only borrow backed by a controlled study; strengthens the actual moat | Measured determinism cost; unproven above 1,000 lines | 3–5 days | Low–medium |
| **F. Build orchestration** (Gas Town shape) | Higher theoretical throughput | ~$100/hr, autonomous merge blast radius, ~20 new concepts, contradicts ADR-010/013; Gas Town's own releases have stalled | Months | Severe |

---

## Recommendations

### Primary: Option A — stop building Writ and use it

**Take a codebase with application code, a build, a test suite, dependencies, and users. Run Writ on it for four to six weeks. Touch the framework only through `/refresh-command`, with evidence cited from that use.**

Chosen over **Option B** (continue inward hardening), which is the path of least resistance and would compound every finding in Part II; over **Option D** (subtraction alone), which is correct but insufficient — deleting the byte instruments removes noise without producing knowledge; and over **Option C** (harness-native pivot), which optimizes distribution for an instrument that has explicitly declined to seek users.

Option A is the only option that can *falsify* anything. Writ's own [mission](../product/mission.md) claims "Self-Improvement With Evidence" and its `/refresh-command` gate requires cited transcript evidence. Six months of refinements have been evidenced by transcripts of Writ building Writ. That is a closed loop, and a closed loop cannot detect that it is closed.

Concretely, what makes it a real experiment rather than a vibe:

1. **Run the ceremony A/B while you build.** Route roughly half the stories through the full 11-gate `/implement-story` pipeline and half through `/prototype` plus native Plan Mode. Record per story: wall-clock, gate failures caught, defects that escaped to integration, and rework. Agent OS v3's claim — that frontier models handle spec implementation unaided — is falsifiable, and Writ owns the instrumentation to falsify it. Nobody in the category has published this comparison.
2. **Success is a filled ledger, not a green eval.** The criterion worth holding: ≥5 knowledge-ledger entries about building software rather than about Writ. If four weeks of real product work produces zero such entries, the compounding-knowledge claim is disconfirmed and that is the most valuable finding available.
3. **Expect the gates to fail differently.** Gate 4's coverage mandate, Gate 2's typecheck, and Gate 4.5's visual QA will fire for the first time. Treat their first real contact as data about the gates, not only about the code.

### Supporting recommendations

4. **Delete the byte instruments — all four** (Option D). ADR-023 already removed their authority; leaving them computed manufactures permanent warnings against a quantity the project has formally declared wrong, and trains the maintainer to ignore the governor. Apply `/refresh-command`'s own standard: no evidence of value, remove. If anything survives, let it be the ADR-019 ratchet alone, wired to CI, blocking — one instrument that bites beats four that warn.
5. **Resolve `/create-uat-plan` rather than accumulating a sixth month of unread scenarios.** Two honest options: delete it and accept that manual UAT is not happening, or convert it to Kiro's executable pattern (acceptance criteria → properties → pytest via Hypothesis), which is the only path in the category where a spec assertion actually executes. For a solo builder, deletion is probably right and is certainly more honest than 264 unchecked boxes.
6. **Add per-criterion traceability IDs and an orphan check** (Option E, Finding 10). Small, evidence-backed, and it lands on the moat. Do this *during* the real-project run so it is validated against code that exists.
7. **Hold the lines already drawn.** No orchestration, no browser daemon, no memory database. ADR-010/013's supervised ceiling is correct and the evidence for it strengthened this quarter. Writ's declined fights are among its best decisions.
8. **Housekeeping, noted rather than scheduled.** Four issue files are stale — two describe work already shipped (`refactor-has-no-dirty-tree-guard`, `phase-execution-closed-unimplemented-status`) and one has a broken roadmap anchor (`#beyond-phase-8-parking-lot`, renamed to *Beyond Phase 10*). ADR-005 has sat at `Proposed` for five months while [ADR-006](../decision-records/adr-006-non-degrading-destination.md) and ADR-011 both build on it. `.writ/manifest.yaml` lists 14 skills while 16 exist on disk, so `SKILL.md` is generated missing two. And `package.json` is at 0.15.0 against `VERSION` 0.31.0, last published 2026-04-29.

### What I am explicitly not recommending

**Do not restructure command files.** Phase 10 measured this: ~1,017 bytes of irreducible overhead per extracted skill and a +9.7% worst-path regression against a projected +4.1%. The five closed specs were closed correctly. Byte count is not the problem; the problem is that 550KB of command prose has only ever been exercised against markdown.

---

## Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| The real-project run reveals the 11-gate pipeline is net-negative on velocity, invalidating the largest investment | **Medium** | High | This is the point. Pre-commit to publishing the result either way. Agent OS shows the graceful response is subtraction, not defense |
| No suitable real project exists, so Option A never starts | Medium | High | Any codebase with a build and tests qualifies — it does not need users on day one. A four-week scope beats a perfect scope |
| Framework work resumes mid-run because friction is immediately visible | **High** | Medium | Hard rule: friction becomes a `/create-issue` entry, not a commit. Framework changes land only after the run, only via `/refresh-command`, only with cited evidence |
| Deleting the byte instruments loses genuine runaway-growth detection | Low | Low | Keep one — the ADR-019 ratchet — and wire it to CI as blocking. The failure mode being avoided is four warnings, not one gate |
| Per-criterion citations degrade output quality | Medium | Medium | The study measures it: d ≈ −0.72 to −0.76 on determinism. Pilot on one spec during the real-project run and compare drift rates before generalizing |
| This document becomes another inward artifact — analysis substituting for the experiment | **High** | High | Its only success criterion is that Option A starts. A second research document on this subject would be the failure |

---

## Further Research

Honest about what remains open:

1. **Does the 11-gate pipeline beat `/prototype` + Plan Mode on real code?** Unanswered, and the highest-value open question in this document. Only Option A answers it.
2. **Is Kiro's property-based verification transferable to markdown-and-git?** EARS criteria → Hypothesis properties is the strongest verification mechanism in the category and Writ's specs already carry structured acceptance criteria. Whether the pattern survives without an IDE is unknown.
3. **What is Writ's actual per-invocation cost on real work?** `measure-invocation.py` measures loaded bytes, not tokens spent reaching exit criteria — which ADR-023 correctly identified as the quantity that matters and then left unmeasured. No instrument replaced it.
4. **Would `/implement-phase`'s sequential-by-default choice survive a codebase with real file overlap?** The decision was made on reasoning ("parallel spec execution multiplies conflict risk… for little gain at this scale"), never on measurement, and `assess-spec` Check 5's overlap detection has never had real overlap to detect.
5. **Does the knowledge ledger compound, or merely accumulate?** Phase 7's consolidation is mechanism-complete only, because in five months the ledger produced no honest duplicate, contradiction, or stale entry to merge. That may indicate a healthy ledger or a ledger too small to test. Real-project use distinguishes these.

---

## Appendix A — Corrections to the Supplied Comparison Document

Verified live against the GitHub REST API, 2026-08-13.

| Claim | Status | Correction |
|---|---|---|
| GStack: "twenty-three specialists and eight power tools" (31) | **Wrong** | **53** top-level skill directories containing `SKILL.md` (62 including nested). The "23" is stale self-description in GStack's own README |
| GStack stars | — | **127,795**; 12 contributors, 956 open issues. Blog citations of 89.7k are stale |
| Gas Town: "v1.2.0 (May 30, 2026)" | **Outdated** | **v1.2.1, published 2026-06-06**. CHANGELOG dates v1.2.0 as 05-27; the GitHub release was 05-30 |
| Gas Town: 15.7k stars, 311 contributors | **Wrong** | **17,596 ★**; **241** contributors. 311 is not a figure GitHub's API reports |
| "Dogs / Boot" as peer roles | **Imprecise** | Boot **is a Dog** — per the glossary, "a special Dog that checks the Deacon every 5 minutes" |
| "Dolt SQL ledger" | **Conflates layers** | The ledger is **Beads**; Dolt is the storage engine; **sqlite3 is separately required** for convoy queries. Beads is its own project (26,277 ★) and is pushed more actively than gastown |
| "~10× the cost of a normal Claude Code session per unit time" | **Unverified** | No primary source states it. The $100/hour figure *is* sourced (Sehn, March 2026) but was measured at API pricing without a Max subscription. No cost data exists after April 2026 |
| "Parallelism borrowed from an external tool… no agent spawning" | **Overstated** | The *no scheduler / no message bus / no supervisor* claim is solid. But `/spec --execute` spawns `claude -p` in a fresh worktree (`lib/worktree.ts`), `/autoplan` fans out in-session subagents, and `/pair-agent` coordinates cross-vendor through a shared browser |
| "MIT, active; released March 2026" (GStack as pure markdown) | **Incomplete** | GStack ships Bun/TypeScript runtime components: a Chromium CDP daemon, a design daemon, an `ios-qa` daemon driving a real iPhone over USB, standalone CLIs, and a branded Chromium with a bundled 22MB ML prompt-injection classifier |
| Gas Town "13 releases… active" | **Needs qualification** | Main's HEAD is **2026-07-23**; no release since **2026-06-06**; `## [Unreleased]` is **empty** despite 302 commits on main since June 1 |

**Material omissions.** **Gas Town by Kilo** — hosted, GA 2026-05-19, running 20–30 agents on Kilo Cloud/Gateway ([kilo.ai/gastown](https://kilo.ai/gastown), [The New Stack](https://thenewstack.io/steve-yegges-ai-agent-orchestration-project-gas-town-comes-to-the-cloud-and-brings-the-wasteland-with-it/)) — removes the entire infrastructure objection and changes the cost regime. **Wasteland** federation over DoltHub. On the GStack side: the `/spec` **Codex gate that blocks below 7/10**, `/health`'s weighted 0–10 score, and GStack's own activation telemetry (~21% of installs never run a skill).

**Also worth correcting in the document's favor:** its recency caveat is well-judged and its cost-and-blast-radius section is the part most worth keeping. The specific January–February 2026 Gas Town incidents are better replaced with defects from Gas Town's own CHANGELOG, which are stronger evidence: a silent Dolt data split where "beads written from the rig could land in the orphan while the mayor read from the canonical DB" (gh#3562), and a daemon crash-loop that killed rate-limited agents instead of rotating accounts (gh#3398).

## Appendix B — Measurement Commands

Every repo-internal figure in this document, with the command that produced it on 2026-08-13 at `main` = `0d1f35f`.

```bash
# Finding 5 — surface ratio: 802,974 product vs 2,195,039 governance = 2.73x
find commands agents skills adapters -type f -exec cat {} + | wc -c
cat scripts/eval*.py scripts/eval.sh $(find scripts/tests -type f) | wc -c

# Finding 7 — base cap: 20,779 + 5,658 = 26,437 vs BASE_BYTE_CAP 25,600 (over by 837)
wc -c system-instructions.md commands/_preamble.md
grep -n 'BASE_BYTE_CAP\|COMMAND_BUDGET_SEVERITY' scripts/eval-leanness.py
# ratchet absent from CI:
grep -n 'scripts/tests\|unittest\|pytest' scripts/eval.sh .github/workflows/eval.yml   # no output

# Finding 8 — 265 scenarios, 264 unexecuted templates, 1 executed
for f in $(find .writ/specs/archive -name 'uat-plan.md'); do grep -cE '^#{3,4} Scenario' "$f"; done
grep -hoE '^\s*\*\*Status:\*\*.*' $(find .writ/specs/archive -name 'uat-plan.md') | sort | uniq -c

# Findings 4, 9 — 57 specs, 21 knowledge entries, 445 commits (302 since 2026-07-01)
ls -d .writ/specs/archive/*/ | wc -l
find .writ/knowledge -name '*.md' ! -name 'README.md' | wc -l
git rev-list --count HEAD; git rev-list --count --since=2026-07-01 HEAD

# Finding 10 — 7 live audit notes
git notes --ref=writ list | wc -l
```

---

## Sources

**Subjects.** [garrytan/gstack](https://github.com/garrytan/gstack) · [gstack docs/skills.md](https://github.com/garrytan/gstack/blob/main/docs/skills.md) · [ON_THE_LOC_CONTROVERSY.md](https://github.com/garrytan/gstack/blob/main/docs/ON_THE_LOC_CONTROVERSY.md) · [garrytan/gbrain](https://github.com/garrytan/gbrain) · [conductor.build](https://conductor.build) · [gastownhall/gastown](https://github.com/gastownhall/gastown) · [Gas Town glossary](https://github.com/gastownhall/gastown/blob/main/docs/glossary.md) · [gastownhall/beads](https://github.com/gastownhall/beads) · [kilo.ai/gastown](https://kilo.ai/gastown)

**Cost and third-party observation.** [A Day in Gas Town](https://www.dolthub.com/blog/2026-01-15-a-day-in-gas-town/) · [A Week In Gas Town](https://www.dolthub.com/blog/2026-03-24-a-week-in-gas-town/) · [Two Weeks in Gas Town](https://www.dolthub.com/blog/2026-04-16-two-weeks-in-gastown/) · [Maggie Appleton on Gas Town](https://maggieappleton.com/gastown) · [The New Stack: Gas Town cloud](https://thenewstack.io/steve-yegges-ai-agent-orchestration-project-gas-town-comes-to-the-cloud-and-brings-the-wasteland-with-it/) · [Cloud Native Now](https://cloudnativenow.com/features/gas-town-what-kubernetes-for-ai-coding-agents-actually-looks-like/) · [TechCrunch on GStack](https://techcrunch.com/2026/03/17/why-garry-tans-claude-code-setup-has-gotten-so-much-love-and-hate/) · [claude-codex.fr: a month with GStack](https://claude-codex.fr/en/content/garry-tan-stack-claude-code/)

**The actual competitive set.** [github/spec-kit](https://github.com/github/spec-kit) · [Microsoft: Diving into SDD](https://developer.microsoft.com/blog/spec-driven-development-spec-kit/) · [Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) · [OpenSpec validate reference](https://thedocs.io/openspec/cli/validate/) · [OpenSpec #880](https://github.com/Fission-AI/OpenSpec/issues/880) · [Kiro: Does your code match your spec?](https://kiro.dev/blog/property-based-testing/) · [Kiro correctness docs](https://kiro.dev/docs/specs/correctness/) · [Kiro #9435](https://github.com/kirodotdev/Kiro/issues/9435) · [obra/superpowers](https://github.com/obra/superpowers) · [buildermethods/agent-os](https://github.com/buildermethods/agent-os) · [Agent OS v3 discussion #310](https://github.com/buildermethods/agent-os/discussions/310) · [bmad-code-org/BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) · [Tessl Series A](https://tessl.io/blog/announcing-our-series-a-for-ai-native-software-development/) · [tessl.io current positioning](https://www.tessl.io/) · [Tessl valuation](https://finance.yahoo.com/news/exclusive-tessl-worth-reported-750-080100819.html)

**Academic.** [Citation Discipline in SDD, arXiv 2606.30689](https://arxiv.org/html/2606.30689v1) · [SDD Benchmark: Security Knowledge Transition, arXiv 2606.00167](https://arxiv.org/abs/2606.00167) · [From Prompt to Process: a process taxonomy, arXiv 2606.04967](https://arxiv.org/abs/2606.04967) · [The Productivity-Reliability Paradox, arXiv 2605.01160](https://arxiv.org/html/2605.01160v1) · [SpecOps 2026 @ SPLASH/ISSTA](https://conf.researchr.org/home/splash-issta-2026/specops-2026)

**Critical / skeptical.** [dabase.com: spec-kit vs OpenSpec vs GSD, hands-on](https://dabase.com/blog/2026/sdd-framework-comparison/) · [Punnen: SDD is not a silver bullet](https://pub.towardsai.net/why-specification-driven-development-sdd-is-not-a-silver-bullet-for-ai-assisted-sdlc-491c71bcf835) · [Yeret: step forward or back?](https://yuvalyeret.com/blog/is-spec-driven-development-a-step-forward-or-back-for-product-development/) · [nino-chavez/blueprint SDD landscape, June 2026 — competitor research, interested source](https://github.com/nino-chavez/blueprint/blob/main/research/03-sdd-landscape-2026-06.md) · [LWN discussion on Dolt/Beads lineage](https://lwn.net/Articles/1070995/)

**Writ internal.** [mission.md](../product/mission.md) · [roadmap.md](../product/roadmap.md) · [ADR-005](../decision-records/adr-005-knowledge-substrate-markdown-over-database.md) · [ADR-007](../decision-records/adr-007-team-audience-sequencing.md) · [ADR-009](../decision-records/adr-009-command-agent-skill-boundary.md) · [ADR-010](../decision-records/adr-010-supervised-autonomy-ceiling.md) · [ADR-011](../decision-records/adr-011-memory-interop-markdown-canonical.md) · [ADR-013](../decision-records/adr-013-recommended-autonomous-delivery.md) · [ADR-019](../decision-records/adr-019-full-surface-leanness-measurement.md) · [ADR-021](../decision-records/adr-021-progressive-disclosure-token-budget.md) · [ADR-022](../decision-records/adr-022-autonomy-gate-classes.md) · [ADR-023](../decision-records/adr-023-stakes-proportional-diligence.md) · [2026-04-24 GStack comparison](2026-04-24-writ-vs-gstack-rigor-comparison.md) · [2026-08-03 OpenSpec analysis](2026-08-03-writ-vs-openspec-analysis.md)
