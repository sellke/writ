# Writ — Product Roadmap

> Based on Product Contract: 2026-02-27, refreshed 2026-07-10 (2026 harness audit — see ADR-010, ADR-011, ADR-012, ADR-013) and 2026-10-20 (pstack comparison — see [ADR-030](../decision-records/adr-030-contract-verifier-boundary-front-door.md))
> Last Updated: 2026-10-20
> Cadence: Steady — ongoing improvement alongside real projects, compounding over months

**Current status (2026-10-20):** Phases 1–11 closed. **Phase 12 (Behavioral Verification) is implemented and released in v0.40.0 (2026-10-02), pending human UAT**: all four success criteria are met — a fixture app exercises the full loop with machine-captured evidence, Gate 4.5's `prose-only` count dropped 2 → 1, the missing-evidence mutation reports `unmet`, and the cross-family panel's trial returned `keep` (6 of 8 panel-only findings valid on four stories). The phase's own UAT plan is unticked, so the open item is human UAT, not more building. **v0.41.0 (2026-10-12)** shipped inter-phase: `/retro` rewritten as a transcript review, and the consumer-less `gbrain-interop` skill removed. **v0.42.0 (2026-10-20)** shipped the **agent CLI contract** ([ADR-029](../decision-records/adr-029-agent-cli-contract.md)) and **`/prototype` as the exploration workflow** (PR #59). **Phases 13–16 are committed (2026-10-20, [ADR-030](../decision-records/adr-030-contract-verifier-boundary-front-door.md)):** Subtract and Repair, Front Door and Distribution, Code-Level Rigor, and Verified Landing, the last gated on Phase 12's human UAT. Candidates live in [Beyond Phase 16 (Parking Lot)](#beyond-phase-16-parking-lot).

**Strategic frame (2026-10-20 refresh):** The first full pstack comparison ([research](../research/2026-10-19-writ-vs-pstack-research.md)) found Writ ahead on durable intent and on enforcement in code. It found Writ behind on four things: entry (32 commands), the last mile after a PR opens, rigor about the code itself, and Claude Code parity. Writ's surface was also past its own justified ceilings. The posture is now: **Writ owns the contract, the verifier, and the boundary, reached through one front door. It subtracts before it adds.**

**Strategic frame (2026-07-09 refresh):** Harnesses natively absorbed much of what Writ's early phases built scaffolding for (memory, skills, subagents, planning modes, context management). Writ's posture going forward: **keep the harness light, own the contracts, delegate the mechanics** — prune what platforms do natively, expand where Writ compounds (supervised autonomy, evidence-based self-improvement, consolidating memory with external interop).

**Posture addendum (2026-08-11, Phase 10):** *Self-improving, token-efficient, and maximally autonomous — except where taste and agency require humans.* Phase 10 turns "keep the harness light" from a stated intent into a measured, enforced property. The trigger was a maintainer concern raised as **explicitly unverified** ("too prescriptive in some ways, not deterministic enough in others"); per the Prime Directive it was measured before planning, and **both halves verified** — the command surface is 516,589 chars (~129k tokens) while **0 of 5** loop-bearing commands declare any iteration bound. See [ADR-020](../decision-records/adr-020-component-contract.md), [ADR-021](../decision-records/adr-021-progressive-disclosure-token-budget.md), [ADR-022](../decision-records/adr-022-autonomy-gate-classes.md). *(ADR-021 since superseded by [ADR-023](../decision-records/adr-023-stakes-proportional-diligence.md); the 516KB figure was later shown to be a measurement artifact — see the Phase 10 Closure.)*

### Revision Log

| Date | Change |
|---|---|
| 2026-10-20 | **Strategic refresh** (`/plan-product --reconcile`) after the first full pstack comparison ([research](../research/2026-10-19-writ-vs-pstack-research.md)) and the `/prototype` exploration research. **Direction change**, recorded in [ADR-030](../decision-records/adr-030-contract-verifier-boundary-front-door.md):<br>• Writ owns the contract, the verifier, and the boundary, reached through one front door.<br>• Phases 13–16 committed: Subtract and Repair, Front Door and Distribution, Code-Level Rigor, and Verified Landing, the last gated on Phase 12's UAT.<br>• Phase 13 covers every defect both research documents found.<br>• `/prototype` as exploration (PR #59) recorded in the condensed history.<br>• Parking lot: plugin distribution and the empirical-fork rule promoted to Phase 14; friction signals retired (ADR-025 Decisions 1, 3, 6 superseded; ADR-029 review trigger amended); four candidates added.<br>• Parking lot renamed *Beyond Phase 12* → *Beyond Phase 16*.<br>• Design Principle 7 added.<br>• Derivatives regenerated. |
| 2026-10-19 | **Reconcile pass** (`/plan-product --reconcile`) after v0.41.0: the four P1/P4 items the 2026-10-02 product check handed over are closed — `mission.md` Phase 12 status realigned to the roadmap, the Phase 11 gate bullet given a forward note, Phase 12 success criteria 1–3 marked met against re-derived evidence, and the header dated. New: v0.41.0 recorded in the condensed history (`/retro` as a transcript review; `gbrain-interop` removed); the agent CLI contract recorded as Complete-but-unreleased; `mission.md`'s self-improvement differentiator credits `/retro` as a second evidence channel; GBrain demoted from *the* integration to *an* example. Friction-signals parking-lot entry narrowed to what `/retro` did not absorb. **No direction change, no new ADR** — the ADR-025 amendment and ADR-029 already covered both shifts. Derivatives regenerated. |
| 2026-10-02 | Recorded `2026-10-01-product-check-direction` as inter-phase infrastructure (v0.40.0). |
| 2026-10-01 | **Reconcile pass** (`/plan-product --reconcile`): Phase 11 promoted from six inter-phase rows to a closed phase with its caveats (single-model baseline; spec analysis advisory); model delegation recorded as shipped (v0.34.0) and removed from the parking lot; friction signals marked unblocked. **Direction change:** Phase 12 (Behavioral Verification) committed with [ADR-028](../decision-records/adr-028-behavioral-verification-and-cross-family-panels.md). Parking lot renamed *Beyond Phase 10* → *Beyond Phase 12*; Cursor plugin distribution and the empirical-fork rule added as candidates. Derivatives regenerated. |
| 2026-09-26 | Recorded `2026-09-26-arch-lint-and-follow-ups` as inter-phase infrastructure (v0.39.0). |
| 2026-09-26 | Recorded `2026-09-26-drift-arch-guards` as inter-phase infrastructure (v0.39.0). |
| 2026-09-25 | Recorded `2026-09-25-jev-judgment-pilot` as inter-phase infrastructure (v0.38.0). |
| 2026-09-25 | Recorded `2026-09-24-flagged-harness-cuts` as inter-phase infrastructure (v0.37.0). |
| 2026-09-09 | Recorded `2026-09-09-phase11-stage4b-pipeline-demote` as inter-phase infrastructure (v0.36.0). |
| 2026-09-09 | Recorded `2026-09-09-phase11-stage4-goal-emit` as inter-phase infrastructure (v0.36.0). |
| 2026-09-09 | Recorded `2026-09-08-phase11-stage3-spec-analysis` as inter-phase infrastructure (v0.36.0). |
| 2026-09-09 | Recorded `2026-09-08-phase11-stage2b-mechanize-the-gates` as inter-phase infrastructure (v0.36.0). |
| 2026-09-09 | Recorded `2026-09-07-phase11-stage2-prune-the-base` as inter-phase infrastructure (v0.36.0). |
| 2026-09-09 | Recorded `2026-09-05-phase11-repair-and-baseline` as inter-phase infrastructure (v0.36.0). |
| 2026-08-15 | Recorded `2026-08-14-script-backed-quality-gates` as inter-phase infrastructure (vv0.33.0). |
| 2026-08-15 | Recorded `2026-08-13-acceptance-criteria-traceability-ids` as inter-phase infrastructure (vv0.32.0). |
| 2026-08-13 | **Reconcile pass** after v0.31.0: two inter-phase infrastructure specs recorded in the condensed history (machine-evaluable exit criteria; implement-loop recalibration) — neither was a roadmap parking-lot candidate before it was built, matching the same "unrecorded direction" pattern the 2026-08-12 pass caught. No direction change — routine "shipped what was needed" bookkeeping, no new ADR. Derivatives (`mission.md` header, `mission-lite.md`) regenerated. |
| 2026-08-12 | **Reconcile follow-ups:** the closure's "Scenario 20 not yet run" claim corrected — the probe ran and passed later the same day (lazy loading confirmed on the full path; `--quick` + degradation probes still open); `.writ/manifest.yaml` `metadata.version` gained a maintainer in `/release` Step 3.1 after drifting again (0.29.0 vs v0.30.2) within a day of its one-time Phase 10 fix. |
| 2026-08-12 | **Reconcile pass** (`/plan-product --reconcile`) after Phase 10 closure: header status, Phase 10 heading, and mission Phase 10 / Next Horizon blocks aligned to the closure record; four stale "pending `/release`" closure claims corrected (Phases 6–9 released in v0.19.0/v0.20.0/v0.23.0); Leanness Guardian annotated with its v0.24.0 full-surface successor (ADR-019); inter-phase infrastructure recorded in the condensed history. Derivatives regenerated. |
| 2026-08-12 | **Phase 10 closed PARTIALLY COMPLETE.** Determinism half shipped and enforced; progressive disclosure stopped after the pilot measured ~1,017 B overhead per skill and a +9.7% worst-path regression. Five specs closed unimplemented. |
| 2026-08-11 | **Phase 10 added** (Component Contract & Progressive Disclosure) via `/plan-product`. Parking lot renamed *Beyond Phase 9* → *Beyond Phase 10*; effort-sizing `L` row filled (was "none currently planned"); pacing discipline extended. Three new ADRs: 020, 021, 022. Phase 10's `## Completion` mandate framing corrected the same day — `new-command.md` never mandated it; see [ADR-020 Amendments](../decision-records/adr-020-component-contract.md#amendments). |
| 2026-07-19 | Phase 9 (Git-Native Provenance & Recovery) recorded as implemented. |
| 2026-07-10 | Strategic refresh from the 2026 harness audit (ADR-010 → ADR-013). |

---

## Shipped Phases (condensed history)

| Phase | Delivered | Version |
|---|---|---|
| **1 — Foundation** | `/prototype`, tiered spec-healing, `/refresh-command`, `/plan-product` posture enhancement | v0.5–0.8 |
| **2 — Reach** | `/ship`, `/review`, `/retro`, enhanced error mapping in `/create-spec` | v0.8+ |
| **3a — Context Engine** | Per-story context hints, "What Was Built" records, agent-specific spec views, `/create-uat-plan` | v0.9.0 |
| **3b — Ralph Loop Orchestration** | `/ralph plan`, CLI loop, fresh-context iterations, quarantine branching — *deprecated in Phase 6; durable inventions migrate to `/implement-phase`* | v0.10.0 |
| **4 — Production-Grade Substrate** | Knowledge ledger, SKILL.md generation, preamble enforcement, eval Tier 1 CI gate, spec `owner:` field | v0.14.0 |
| **— Skills primitive** | Third primitive (command/agent/skill), `/new-skill`, boundary lint, `conventional-commits` pilot | v0.17.0 |
| **— Codex adapter** | Third platform adapter with full lifecycle script parity | v0.18.0 |
| **— Leanness instrumentation** | Full-surface measurement, reduction ratchet, per-invocation `story_context_bytes` — supersedes the Leanness Guardian's Tier A tripwire ([ADR-019](../decision-records/adr-019-full-surface-leanness-measurement.md)) | v0.24.0 |
| **— Deterministic story substrate** | Story-graph validator gates `/implement-spec` before parallel batches; context-hint resolution collapsed to one budget-enforced assembler | v0.25.0 |
| **— Spec lifecycle & archival** | Format-tolerant status detection (27/39 specs were misclassified), archive sweep to `specs/archive/` + `LEDGER.md`, status-alone eligibility, post-merge archival hook | v0.26–0.28 |
| **— Phase-closure status vocabulary** | Terminal `Closed — Not Implemented` status, `phase-state.py close-spec`, load-bearing vocabulary enforcement — the machinery Phase 10's own closure used | v0.30.0–0.30.1 |
| **— `/refactor` dirty-tree guard** | Porcelain guard HALTs before mutation; executable `safe-refactor-loop` checkpoint — promoted from a bug Phase 10's UAT filed | v0.29–0.30 |
| **— Machine-evaluable exit criteria** <!-- 2026-08-12-machine-evaluable-exit-criteria --> | `scripts/exit-criteria.py` read-only checker re-derives `met`/`unmet`/`unknown`/`impossible` for `/implement-phase` + `/implement-spec` exit criteria from disk state instead of self-report; wired into completion reports and the Claude Code `/goal` Stop hook | v0.31.0 |
| **— Implement-loop recalibration** <!-- 2026-08-12-recalibrate-implement-loop --> | Fixes to real friction from running the exit-criteria spec end-to-end: `/implement-spec` spawn-mechanism clarity, required execution-state writes, `spec.md` header sync; two new skills (`subagent-result-completeness`, `subagent-worktree-integration`) closing gaps in how `/implement-story` gates handle mid-task stops and isolated worktrees | v0.31.0 |
| **— Per-criterion AC traceability** <!-- 2026-08-13-acceptance-criteria-traceability-ids --> | Stable `[AC-N.M]` IDs assigned at story-generation time, with `scripts/ac-trace.py` detecting orphaned, untested, duplicate and dangling criteria; wired into `/verify-spec` as a blocking check and `/edit-spec` as a renumbering-churn guard | v0.32.0 |
| **— Script-backed quality gates** <!-- 2026-08-14-script-backed-quality-gates --> | Coverage, test authenticity, build smoke and quality-config audit become read-only checkers whose verdicts override the agent self-report; wired into `/implement-story` Gate 2 and Gate 4 with no new gate number, plus `/initialize` baselining and a `/status` health line | v0.33.0 |
| **— Model delegation** <!-- 2026-09-03-model-delegation --> | Anchor/floor tiers with a family-locked floor, origin capture at command entry, escalate-once on a failed floor check, and `entry_level` on every command ([ADR-024](../decision-records/adr-024-model-delegation.md)) | v0.34.0 |
| **11 — Contract-and-Verifier Layer** <!-- 2026-09-05-phase11-repair-and-baseline 2026-09-07-phase11-stage2-prune-the-base 2026-09-08-phase11-stage2b-mechanize-the-gates 2026-09-08-phase11-stage3-spec-analysis 2026-09-09-phase11-stage4-goal-emit 2026-09-09-phase11-stage4b-pipeline-demote --> | Six stages, one spec each: repair and Fable 5.1 baseline; base pruned under 10 KB with a ledger; eight of ten gates script-backed; advisory `spec-analyze.py`; Goal Card to `/goal` emit; two-agent default pipeline. Closure record in the Phase 11 section below | v0.36.0 |
| **— Flagged harness cuts** <!-- 2026-09-24-flagged-harness-cuts --> | Three harness cuts ship default-off, and become the default only when a same-model baseline keeps every exit-criteria row at 2/2 and driver cost_usd drops against that model's own flag-off control. | v0.37.0 |
| **— Jev Judgment Pilot** <!-- 2026-09-25-jev-judgment-pilot --> | Opt-in TypeSafe Jev judgment provider (TypeSafe direct or Vercel AI Gateway): ADR-027, stdlib client, Step 2.6c cascade, calibration, Gate 3 shadow, one-time setup prompt. | v0.38.0 |
| **— Drift and Architecture Guards** <!-- 2026-09-26-drift-arch-guards --> | Boundary crossings route Gate 3 to review-agent; drift judged against the locked contract; spec-end drift roll-up. | v0.39.0 |
| **— Architecture Lint and Drift-Guard Follow-ups** <!-- 2026-09-26-arch-lint-and-follow-ups --> | Gate 2 architecture-ruleset detection with a shipped guide and ADR hook; Codex TOML freshness check; issue closure via ## Resolution. | v0.39.0 |
| **— Product Check Direction** <!-- 2026-10-01-product-check-direction --> | Product-doc verification reads as a post-implementation check whose findings feed realignment; /implement-phase and /release each suggest /verify-spec --product in one line. | v0.40.0 |
| **— Transcript `/retro`** | `/retro` reads Claude Code, Cursor and Codex transcripts for a story, spec, phase or `--since` window, ranks where the agent struggled, and proposes fixes to the *environment* — steering files, navigation hints, lint rules, skills, docs — never to source or tests. Each finding cites a transcript path and an observable signal; command and agent changes route to `/refresh-command`. Replaces the git-metrics retro ([ADR-025](../decision-records/adr-025-friction-signals.md) amended). Shipped alongside the removal of the consumer-less `gbrain-interop` skill (the recipe doc stays; the adapters link it). | v0.41.0 |
| **— Agent CLI Contract** <!-- 2026-10-12-agent-cli-contract --> | Every shipped script follows one documented, test-enforced agent contract — data tools emit one JSON document, check tools lead with `pass`/`fail`/`unverifiable` — with the contract test reading the shipped set from `install.sh` so no second list can drift. Six dev-only scripts stop shipping ([ADR-029](../decision-records/adr-029-agent-cli-contract.md)). | v0.42.0 |
| **— `/prototype` as Exploration** | `/prototype` becomes the early exploration workflow. It declares axes, generates up to three code-portable drafts in independent contexts, and records the choice and why each rejected draft lost in `.writ/prototypes/<date>-<slug>/exploration.md`. A recorded choice with no code is a complete run. `/create-spec --from-prototype` reads the record (Directions Considered; Story 1 status from the source matrix). Merged in PR #59, [research](../research/2026-10-19-prototype-visual-drafts-research.md). | v0.42.0 |

> Rows below the phase rows are inter-phase infrastructure — shipped through the normal spec pipeline between roadmap phases, recorded here so no Complete spec lacks a roadmap home (added 2026-08-12 reconcile pass).

---

## Phase 5: Operationalize the Destination — ✅ Closed (spirit met, 2026-07-09)

**Original goal:** Make the production-grade claim falsifiable.

**Closure rationale:** The spirit of this phase was met by work that shipped through other channels: eval Tier 1 runs as a CI gate on every PR, `/verify-spec` is an 8-check diagnostic with auto-fix, drift logs quantify spec-vs-reality per story, and the knowledge ledger exists. Building a separate `/audit` command, `/lessons` micro-command, and per-story scorecards on top would add surface without adding falsifiability.

**Disposition of original features:**

- [x] Falsifiability substrate — met by eval Tier 1 + `/verify-spec` + drift logs (shipped in Phase 4)
- [→] `dependencies:` spec frontmatter — **relocated to Phase 6**, where `/implement-phase` sequencing actually consumes it
- [→] `/status` health score — **relocated to Phase 6** as a one-line summary derived from existing checks (no new `/audit` command)
- [✗] `/audit` command — cancelled (duplicates existing checks)
- [✗] `/lessons` micro-command — cancelled (duplicates `/knowledge`)
- [✗] Per-story scorecards, drift-to-lesson flag — cancelled (ceremony without evidence of need)

---

## Phase 6: Autonomy Ceiling — ✅ Complete (2026-07-10)

**Goal:** Harden normal multi-spec `/implement-phase` as a session-bound, single-confirmation orchestrator and retire Ralph. Recommended delivery is governed by [ADR-013](../decision-records/adr-013-recommended-autonomous-delivery.md), which supersedes ADR-010's conflicting contract-level gate. As revised 2026-07-17, `--recommend` extends to `/implement-phase` as the end-to-end loop; autonomous production delivery stays deferred.

**Closure status:** All seven features shipped and verified by eval Tier 1 (`spec-dependencies`, `phase-lanes`, `phase-challenges`, `phase-quarantine`, `phase-knowledge`, `phase-health`, `ralph-retirement`), a disposable multi-spec sandbox UAT, and one real-use User Challenge — see [`acceptance-evidence.md`](../specs/archive/2026-07-09-phase6-autonomy-ceiling/acceptance-evidence.md). Ralph is archived under `archive/ralph/`. **One honest caveat:** the "3+ spec phase runs end-to-end in real use" criterion is proven *mechanically* (sandbox) only — an umbrella spec cannot self-prove it; the first genuine multi-spec `/implement-phase` run (Phase 7 onward) will exercise it live. Released in **v0.19.0** (2026-07-11, jointly with Phase 7).

### Dependencies

- `2026-07-10-recommended-autonomous-delivery` — governance reconciliation and the bounded single-spec delivery policy must land before Phase 6.
- Multi-spec `/implement-phase --recommend` was excluded at Phase 6 closure; per [ADR-013 (revised 2026-07-17)](../decision-records/adr-013-recommended-autonomous-delivery.md) it is now the supported end-to-end loop, while autonomous **production delivery** stays deferred.

### Success Criteria

- A 3+ spec phase runs end-to-end through `/implement-phase` without orchestrator context degradation (fresh subagent per spec) — ✅ mechanical evidence (disposable multi-spec sandbox UAT in the phase6 spec `acceptance-evidence.md`); a genuine 3+ spec real-use run is outside this umbrella spec and will land with the next real phase
- A deliberately failed spec lands on a quarantine branch without polluting the phase branch — ✅ verified (sandbox UAT + `phase-quarantine` eval)
- At least one mid-run scope decision surfaces in User Challenge format during real use — ✅ satisfied: a real mid-run exit-criteria decision (the stale eval baseline fixture) surfaced to the maintainer, who chose to fix it; recorded in four-part User Challenge format in the phase6 spec `acceptance-evidence.md`
- Ralph fully deprecated: command, script, and docs archived; changelog and README updated; `/status` no longer reports ralph state — ✅ verified (`ralph-retirement` eval + allowlisted search)

### Features

- [x] **Fresh context per spec** `Effort: M` — Each `/implement-spec` iteration runs in a fresh subagent; the orchestrator holds only state, sequencing, and escalation. Ralph's core research finding (fresh-context agents outperform continuous agents), ported into the supervised orchestrator.
- [x] **Quarantine branching on spec failure** `Effort: S` — Failed spec's partial work lands on `writ/quarantine/{spec}`; phase branch stays clean. Inherited from Ralph.
- [x] **User Challenge framing for mid-run decisions** `Effort: XS` — When a condition proposes degrading scope: what the roadmap said / what we recommend / what context we might be missing / cost if we're wrong. Apply ADR-013's evidence-based select-or-pause rule: low-risk reversible choices require observable support and an audit summary; critical ambiguity or material risk pauses. (Borrowed from GStack's autoplan; hardens the Prime Directive where autonomy is highest.)
- [x] **`dependencies:` spec frontmatter** `Effort: S` — Declared cross-spec dependencies replace prose-overlap inference in Step 2.1 sequencing; `/verify-spec` validates references. (Relocated from Phase 5.)
- [x] **Knowledge writeback at phase close** `Effort: S` — Phase report appends durable lessons and drift patterns to `.writ/knowledge/`; the loop feeds the memory.
- [x] **Ralph deprecation** `Effort: S` — Archive `commands/ralph.md`, `scripts/ralph.sh`, PROMPT templates, and docs; record [ADR-012](../decision-records/adr-012-ralph-deprecation.md); point users to `/implement-phase`.
- [x] **`/status` health line** `Effort: XS` — One-line production-grade summary derived from existing checks (eval Tier 1, `/verify-spec`, drift logs). (Relocated from Phase 5.)

---

## Phase 7: Compounding Layer — ✅ Complete (2026-07-11)

**Goal:** Make Writ's self-improvement falsifiable and its skills primitive actually adopted. The learning loop moves from anecdote to evidence.

**Closure status:** All four features shipped as contract-first specs, each implemented in an isolated per-spec lane and merged only after independent verification (`b3dd3e4` skill-lifecycle, `3ee2b98` skill-extraction, `56207ac` evidence-bound-refresh, `32d1dca` knowledge-consolidation). Verified by the full eval Tier 1 suite on the merged phase branch (exit 0, 0 findings — including the three new checks `skill-lifecycle`, `refresh-evidence`, `knowledge-consolidate`), 79 UAT scenarios across four `uat-plan.md` files, and one evidence-bound knowledge lesson written at phase close. As the first genuine multi-spec `/implement-phase` run (the live exercise Phase 6 could only prove mechanically), it also surfaced and fixed a real orchestration defect — ephemeral lane worktrees weren't gitignored (`f06f405`) — and filed a tracked bug for `create-lane` worktree pathing. **Honest caveats:** (1) extracted skills are born `status: candidate` and wired to live consumers now; promotion to `proven` accrues via evidence later. (2) Knowledge consolidation is **mechanism-complete**: the loop is proven end-to-end on the real ledger with a reviewable diff (it surfaced and cleaned a malformed phase-close entry), but a literal merge/prune of duplicates awaits a genuine duplicate — the current ledger is honestly clean. Merged and released in **v0.19.0** (2026-07-11, jointly with Phase 6).

### Success Criteria

- 3-5 skills extracted from the highest-traffic commands (`/create-spec`, `/implement-story`, `/ship`, `/refactor` are first candidates), each lint-clean and in real use — ✅ 4 extracted (`code-explanation`, `tdd-cycle`, `error-rescue-mapping`, `safe-refactor-loop`), all lint- and lifecycle-clean and wired to live consumers; born `candidate`, promotion to `proven` accrues later
- Every skill carries lifecycle state (candidate / proven / promoted) with recorded evidence — ✅ enforced by `lint-skill.sh` lifecycle checks (ADR-014); `conventional-commits` = `proven` with evidence, new skills scaffold `candidate`
- At least one `/refresh-command` refinement merged with cited transcript evidence and passing evals — and at least one *rejected* for lacking evidence — ✅ both real acceptance records exist in `.writ/refresh-log.md`; the pre-merge evidence + eval gate is enforced
- First knowledge consolidation pass merges or prunes real entries with a reviewable PR diff — ⚠️ **mechanism-complete:** the pass ran on the real ledger and produced a reviewable diff (surfaced + fixed a malformed writeback entry); a literal merge/prune awaits a genuine duplicate, as the ledger has no honest duplicate/contradiction/stale entry

### Features

- [x] **Skill lifecycle** `Effort: S-M` — `status:` field in skill frontmatter (candidate → proven → promoted) with evidence recorded per transition; `/new-skill` starts at candidate; `/refresh-command --lint-skills` checks lifecycle hygiene. (Pattern borrowed from GStack's domain-skill quarantine → active-after-3-successes.)
- [x] **Skill extraction from high-traffic commands** `Effort: M` — Pull reusable capability out of the heaviest commands into skills; commands shrink to orchestration. Targets the essential surface where refinement pays off most. Also resolves the weak content in `/explain-code` (retire the command; its ~10 durable lines become a skill).
- [x] **Evidence-bound `/refresh-command`** `Effort: M` — Proposed refinements must cite transcript evidence and pass eval Tier 1 (plus a lightweight Tier 2 check for high-traffic commands) before merging. The learning loop becomes falsifiable. (GBrain's `skillopt` sets the industry bar: skills as trainable parameters, keep only measurably better edits.)
- [x] **Knowledge consolidation** `Effort: S-M` — `/knowledge --consolidate` (or a `/retro` step): merge duplicates, surface contradictions, prune stale entries. Merge, never append — a log grows unbounded; a merged document stays searchable. Markdown in, markdown out, reviewable in PRs.

### Dependencies

- Phase 6 knowledge writeback (gives consolidation real input)

---

## Phase 8: Memory Interop (1-2 weeks) — ✅ Implemented (2026-07-11)

**Goal:** Writ's markdown stays the canonical system of record; external memory layers become documented, optional, disposable indexes over it. Interoperate, never re-implement. Per [ADR-011](../decision-records/adr-011-memory-interop-markdown-canonical.md).

**Closure status:** Decomposed into two contract-first specs, each implemented in an isolated per-spec lane and merged only after independent verification (`f88c6f8` gbrain-compatibility-recipe, `477359c` native-memory-guidance) on `phase/8-memory-interop`. Machine-checkable exit criteria verified by the new `memory-interop` eval Tier 1 check (0 findings) and the full suite green; 21 UAT scenarios across two `uat-plan.md` files. The GBrain recipe is grounded in GBrain's *real* interface (`garrytan/gbrain`: `gbrain sources add`/`sync`/`doctor --json`/`search`/`serve`), not an invented API. **Honest caveat:** the "GBrain-equipped project answers retrieval queries" criterion and the *live* round-trip cannot be machine-verified here (no GBrain install; Writ ships none) — they are handed off as UAT scenarios 10–12. Recipe accuracy is verified against current docs; live behavior awaits a GBrain-equipped machine. Merged and released in **v0.20.0** (2026-07-11, alongside Leanness Guardian and Product Reconciliation).

### Success Criteria

- A GBrain-equipped project can register `.writ/` as a source and answer retrieval queries against specs, ADRs, and knowledge entries — ⚑ handed off (requires a GBrain install; recipe grounded in the real interface, live query is UAT scenario 10)
- Removing GBrain (or any index) loses zero canonical data — verified by round-trip — ◐ true by construction (canonical data never enters the index) and asserted by the eval check; live round-trip is UAT scenario 11
- Each adapter documents how Writ's ledger relates to that platform's native memory — ✅ all four adapters carry the identical two-place rule (`memory-interop` eval check)

### Features

- [x] **GBrain compatibility recipe** `Effort: S-M` — Shipped as the `gbrain-interop` skill (routing: detect → brain-first → cite markdown → write markdown-first → degrade) + `.writ/docs/gbrain-recipe.md` (register `.writ/` via `gbrain sources add`, artifact→page tag mapping, MCP registration, round-trip removal, version boundary). Zero new Writ infrastructure; grounded in the real GBrain interface.
- [x] **Native-memory guidance per adapter** `Effort: S` — "Native Memory & the Writ Ledger" section in all four adapters (Cursor Memories + semantic index; Claude Code `CLAUDE.md` + `.claude/agent-memory/`; Codex `AGENTS.md`; OpenClaw sessions): session prefs/trivia → native memory; negotiated decisions/conventions/lessons → the reviewable ledger; external brain → disposable index.
- [x] **Mission language update** `Effort: XS` — Verified: active mission reads "not a memory database or retrieval engine"; no stale "persistent-database knowledge layer" framing survives on any active surface (asserted by the `memory-interop` eval `forbid_literal`).

## Product Reconciliation — ✅ Shipped (2026-07-11)

**Ships to all Writ users.** Closes the gap where Writ can verify and revise a
*spec* but had no equivalent for the *product* layer — even though mission/roadmap
drift silently across the four files that describe strategy (the live example that
prompted this: roadmap marked Phases 6–7 complete while mission still framed
Phase 6 as "next"). Adds the missing before/after pair plus a nudge, as **mode
additions to existing commands** — no new command files. Per
[`2026-07-11-product-reconciliation`](../specs/archive/2026-07-11-product-reconciliation/spec.md).

- [x] **`/verify-spec --product`** `Effort: S` — a consistency lint (the *before*)
  with its **own** ~4-check set (P1–P4: phase-status parity, ADR reference
  resolution, derivative freshness, shipped-claim sanity) over
  `.writ/product/` + `.writ/context.md`. Hybrid disposition: auto-fix regenerates
  derivatives (`mission-lite.md`, `.writ/context.md`); authoritative divergence
  (mission ↔ roadmap) is **report-only** — a human decides. Explicitly *not* spec
  checks 1–8 pointed at product docs.
- [x] **`/plan-product --reconcile`** `Effort: S` — a revision posture (the *after*):
  scan existing docs → diff vs. reality (shipped specs, roadmap statuses, git) →
  propose *targeted* edits in Plan Mode; new ADRs only for genuine direction
  changes. Not a from-scratch regeneration; greenfield flow untouched.
- [x] **`/retro` product-drift nudge** `Effort: XS` — read-only advisory (mirrors
  the Step 5.5 knowledge-consolidation nudge) that points to the two remedies when
  a cheap drift signal is present; silent with no signal or no `.writ/product/`.

**Boundary discipline (the core risk):** `--product` checks consistency *before*;
`--reconcile` revises *after*. Both command files state the boundary and
cross-reference each other — the same discipline that keeps `/assess-spec` and
`/verify-spec` distinct.

**Deliberately out of scope:** any new command file, `scripts/`/eval changes,
auto-editing authoritative mission/roadmap prose (only derivatives regenerate), and
`/status` allowlist changes (all three commands already listed).

---

## Self-Governance: Leanness Guardian — ✅ Shipped (2026-07-11)

**Dogfooding-only — does not ship to users.** Writ's value proposition *is*
leanness ("keep the harness light… delegate the mechanics"), so bloat is an
existential threat, not cosmetic debt. Before this, that discipline was enforced
only culturally (Design Principles #1/#4 and the maintainer's prune instinct that
retired `/audit`, `/lessons`, Ralph, `/explain-code`). The guardian makes it
systematic. Per [ADR-015](../decision-records/adr-015-leanness-self-governance.md).

> **Since superseded in part:** the Tier A tripwire below was rewritten 2026-07-26 to measure the **full product surface** with a downward reduction ratchet and per-invocation story context cost ([ADR-019](../decision-records/adr-019-full-surface-leanness-measurement.md), spec `2026-07-26-leanness-instrumentation`, v0.24.0 — see the condensed-history table). [ADR-023](../decision-records/adr-023-stakes-proportional-diligence.md) later demoted all byte measurement from architecture-driving to drift-detecting.

- [x] **Tier A — leanness tripwire** `Effort: S` — `scripts/eval.sh --check=leanness`
  (backed by `scripts/eval-leanness.py`) measures aggregate command weight and
  cross-registry parity that nothing else covered: README `## Commands` table ↔
  `commands/*.md` (bidirectional) and the `/status` allowlist → files
  (phantom-only — the allowlist is a curated suggestion subset, see DEV-001).
  Registry drift hard-FAILs; count/weight growth warns non-blockingly against
  `.writ/leanness-baseline.json` (seeded 31/7/6, 10,659 lines). Defers manifest
  parity, per-file length, and skill boundary to their existing owners.
- [x] **Tier B — audit ritual** `Effort: XS` — `.writ/docs/leanness-audit-format.md`
  re-applies the "does the harness do this natively now?" test on a cadence
  (per-phase-close or quarterly, never per-release) and routes prune candidates
  to ADR/roadmap/issues. Recommends, never deletes. First dated audit:
  `.writ/docs/leanness-audit-2026-07-11.md`.

**Deliberately out of scope:** any user-facing command (the guardian is internal
governance), auto-pruning, LLM-as-judge overlap detection, and generalizing the
tripwire for users' own projects.

## Recommend Redistribution — ✅ Complete (2026-07-17)

**Ships to all Writ users.** Redistributes the `--recommend` capability after
experience showed a single command carrying one spec all the way through a
production-approval boundary was the wrong first cut. Per
[ADR-013 (revised 2026-07-17)](../decision-records/adr-013-recommended-autonomous-delivery.md).
Spec: `2026-07-17-recommend-redistribution` (all three stories complete; full
eval suite green).

- [x] **`--recommend` on exactly two commands** — `create-spec --recommend`
  (autonomously author + lock a validated spec package from evidence, then stop)
  and `implement-phase --recommend` (end-to-end phase loop that auto-authors
  missing specs via `create-spec --recommend` and runs `implement-spec` per spec
  through the isolated-lane flow). Removed from `implement-spec`, `ship`, and
  `create-uat-plan`; `implement-spec` is now a plain execute command with no
  confirmation gate and no flag.
- [x] **Autonomous production delivery deferred** — the staging →
  production-approval flow is not reached by any current command. Staging
  machinery (`scripts/recommend-state.py`,
  `.writ/docs/recommended-delivery-state-format.md`) kept **dormant** as the
  preserved design for that future "bigger loops" work, not deleted, and still
  guarded by the eval suite.
- [x] **Eval falsifiability gate reconciled** — `autonomy-governance`,
  `recommended-spec-implementation`, and `recommended-staging` assert the
  two-command policy on active surfaces and guard the dormant machinery.

**Boundary preserved:** both recommended flows end at their normal terminal scope
— neither merges, opens PRs, nor releases. Production stays a human decision.

---

## Phase 9: Git-Native Provenance & Recovery — ✅ Implemented (2026-07-19)

**Goal:** Make git itself Writ's durable audit and recovery substrate, and harden
command robustness — adopting the strongest ideas surfaced by the Conductor
competitive analysis without cloning its structure. Three contract-first specs:
an immutable audit trail bound to shipped commits, a logical-unit revert, and an
artifact-integrity discipline. Per
[`.writ/research/2026-07-18-writ-vs-conductor-analysis.md`](../research/2026-07-18-writ-vs-conductor-analysis.md)
and [ADR-018](../decision-records/adr-018-third-party-skill-trust-model.md) (a
reserved, out-of-phase decision from the same analysis).

**Closure status:** All three features shipped as contract-first specs on `phase/9-git-native-provenance`, each implemented in an isolated per-spec lane and merged only after independent verification (`8cbc187` git-notes-audit-channel, `2f501d1` logical-unit-revert, `46ea900` artifact-integrity-handshake). Verified by full eval Tier 1 (`Findings: 0`) including `git-notes-audit` (26/26), `revert` (23/23), and `artifact-integrity` (19/19); 53 UAT scenarios across three `uat-plan.md` files await manual execution. **Honest caveats:** (1) live `git log --notes=writ` evidence requires a real `/ship` land (mechanism + eval gate shipped). (2) Live required-artifact HALT is a UAT scenario (static contract asserted by eval). Merged and released in **v0.23.0** (2026-07-19).

**Honest release caveat (resolved):** at scheduling time, Phases 6–8, Product
Reconciliation, and Memory Interop were merged-pending/unreleased, and Phase 9 was
scheduled deliberately anyway. The gap has since been cleared: v0.19.0 released
Phases 6–7, v0.20.0 released Phase 8 with Leanness Guardian and Product
Reconciliation, and v0.23.0 released Phase 9 itself. *(Corrected 2026-08-12
reconcile pass — this block and four closure-status sentences above had claimed
"pending `/release`" through eleven subsequent tagged releases.)*

### Success Criteria

- After `/ship` of a spec, `git log --notes=writ` on the base branch shows an
  immutable audit digest on the **landed** commit (survives squash-merge); a
  fresh clone with the configured fetch refspec sees it; opt-out leaves no
  git-config residue.
- `/revert <unit>` (story|spec) resolves a logical unit to its real commits —
  recovering rewritten SHAs via a confirmed ghost-commit match — undoes them
  (safe `git revert` default), and restores Writ artifacts (status, WWB, drift
  log, `context.md`) consistently.
- A high-traffic command run with a missing **required** artifact halts early
  with a specific, actionable repair offer; a missing optional artifact degrades
  gracefully; no new `.writ/index.md` file is introduced.
- Eval Tier 1 gains passing checks for all three (audit refs/notes rule,
  revert-resolver + guards, artifact-integrity + index-guard).

### Features

- [x] **Git-notes audit channel** `Effort: M` — Spec
  [`2026-07-18-git-notes-audit-channel`](../specs/archive/2026-07-18-git-notes-audit-channel/spec.md).
  `/ship` attaches a spec-level audit digest (composed from "What Was Built"
  records) to the landed commit under a dedicated `refs/notes/writ` ref; `/release`
  attaches a version rollup; sync via configured refspecs; default-on, clean
  opt-out; `/status` read line. (Conductor's git-notes idea, adapted to Writ's
  squash-merge `/ship` — attach post-land so notes aren't orphaned.)
- [x] **Logical-unit revert (`/revert`)** `Effort: M` — Spec
  [`2026-07-18-logical-unit-revert`](../specs/archive/2026-07-18-logical-unit-revert/spec.md).
  Single `/revert <unit>` (story|spec) with a layered commit resolver
  (`scripts/revert-resolve.py`: recorded SHA → `/ship` `Ref:` footer → phase-state
  → confirmed ghost-commit fuzzy match), safe/hard strategies, dirty-tree guard,
  and full artifact restoration. Prerequisite: `/implement-story` records each
  story's commit SHA. (Conductor's `conductor-revert` model; ghost-commit
  reconciliation is the borrowed robustness trick.)
- [x] **Artifact integrity + handshake (robustness rider)** `Effort: S` — Spec
  [`2026-07-18-artifact-integrity-handshake`](../specs/archive/2026-07-18-artifact-integrity-handshake/spec.md).
  An "Artifact Integrity" standing rule in `_preamble.md` (verify Required
  Artifacts before work; required-missing → HALT + bounded repair; optional →
  warn+degrade) plus an "Artifact Map" section in the regenerated `context.md`.
  **Deliberately no new `index.md`** — the map rides in `context.md`, respecting
  ADR-015 leanness. (Conductor's integrity-halt discipline, minus its extra file.)

### Dependencies

- **Internal (soft):** `/revert` may attach a revert audit note if the git-notes
  channel has shipped — kept optional so the two ship independently. No hard
  ordering; the artifact-integrity rider is fully independent.
- **Origin:** the Conductor analysis
  ([`2026-07-18-writ-vs-conductor-analysis.md`](../research/2026-07-18-writ-vs-conductor-analysis.md))
  and its leanness follow-up ([`leanness-audit-2026-07-18.md`](../docs/leanness-audit-2026-07-18.md)).

### Out of Scope (deliberately)

- Per-story branch-local notes (dropped by squash), a bespoke `writ notes` reader,
  historical backfill (git-notes spec).
- Phase-lane/worktree/quarantine reverts (deferred to `phase-state.py`), cross-base
  reverts (revert spec).
- A new `.writ/index.md` file; forcing Required-Artifacts blocks into all 30
  commands (integrity spec).
- Activating the third-party skill trust model — ADR-018 is reserve-only, **not** a
  Phase 9 deliverable; it is referenced, not built.

---

## Phase 10: Component Contract & Progressive Disclosure — ◐ Partially Complete (closed 2026-08-12)

> Planned 2026-08-11 (3-5 weeks est.); closed the next day at a fraction of the estimate because the determinism half shipped whole and the disclosure half was stopped on its own pilot's evidence — see [Phase 10 Closure](#phase-10-closure-2026-08-12) and the [Postscript](#postscript-2026-08-12--the-byte-goal-is-withdrawn-not-deferred). The section below is preserved as the plan-time record.

**Posture:** Self-improving framework that is token-efficient and maximally autonomous — except where taste and agency require humans.

**Problem (measured, not assumed).** The framework is simultaneously *over-specified in prose* and *under-specified in contract*. The driving concern was raised as explicitly unverified; per the Prime Directive it was measured before planning:

| Measure | Value |
|---|---|
| `commands/` surface | 516,589 chars / 10,996 lines / 32 files (≈129k tokens at chars/4) |
| Top 6 command files | 205,104 chars = **40% of all command bytes** |
| Worst offender | `commands/implement-story.md` — 49,360 chars / 961 lines (≈12.3k tokens loaded before any work begins) |
| Commands declaring a goal/problem heading | **2 of 32** (`new-skill`, `status`) |
| Commands with `## Completion` | **13 of 32** — an emergent convention: `new-command.md` does not mandate it and nothing checks it |
| Loop-bearing commands declaring an iteration bound | **0 of 5** (`implement-phase`, `implement-spec`, `implement-story`, `refactor`, `verify-spec`) |

**Why the existing governor did not catch this.** `eval-leanness.py` measures the full surface and `eval.sh check_length` bounds per-file length — but the command limit is **2000 lines against a worst offender of 961**, so it can never bind (`_preamble.md` gets 80; `spec-lite.md` gets 100). Surface growth lands in `warnings` (non-blocking, exit 0) and is a *delta ratchet against a baseline*, not an absolute budget — four unjustified-growth warnings are live and have been ignored. Nothing anywhere asserts that a command declares a goal, exit criteria, or a loop bound.

**Mission alignment.** `mission.md` positions Writ as *"the **thin**, portable methodology layer."* 516KB of command prose falsifies "thin" by measurement. Phase 10 is not a new direction — it is the phase that makes the existing mission true.

### Success Criteria

Machine-checkable unless marked otherwise:

- `eval.sh` exits 0 with **0 findings and 0 unjustified growth warnings**
- ~~No command file exceeds **400 lines** without a tracked exemption~~ — **void, [ADR-023](../decision-records/adr-023-stakes-proportional-diligence.md) (2026-08-12).** Retained as a non-binding tripwire; no file is restructured to satisfy it.
- **All 31 commands** declare `problem` / `outcome` / `exit_criteria` in frontmatter
- **All 31 commands** carry a `## Completion` section, and `new-command.md` mandates it for generated commands (18 sections written; the mandate is created, not enforced)
- **All 5** loop-bearing commands declare `loop.max_iterations` + `on_exhaustion`
- Every `required_skills:` entry resolves to a real `skills/<name>/SKILL.md`
- `bash scripts/gen-skill.sh --check` passes (manifest/SKILL.md consistency restored)
- ~~`per_surface.commands.chars` drops materially from 516,589~~ — **void, [ADR-023](../decision-records/adr-023-stakes-proportional-diligence.md) (2026-08-12).** This was the phase's central byte goal. It is withdrawn, not merely unmet: byte count measures file size, while the stated aim is economy of *steps and ruminations to reach exit criteria*. Where the two diverge the byte metric points the wrong way — extraction cut `implement-story`'s floor 35.9% while adding eight decision points, five of which fire unconditionally and buy nothing. Bytes remain measured as drift signal; they no longer drive architecture, and no replacement number is adopted.
- *(manual)* One real `/implement-story` run completes with progressive disclosure active and every gate firing — ✅ **run and passed 2026-08-12, after the closure below was first written** (Scenario 20, `disclosure-implement-story` UAT plan): lazy loading confirmed on the full path; the `--quick` and missing-skill probes remain open

### Features

- [x] **Component contract** `Effort: M` — `problem:` / `outcome:` / `exit_criteria:` in the frontmatter that already exists in 32/32 commands; same fields in agents' existing fenced Agent Configuration block (the `model_tier` carrier — no new mechanism). Skills already comply in shape; lint asserts `## Purpose` + `## When to Use`. See [ADR-020](../decision-records/adr-020-component-contract.md).
- [x] **Loop bounds** `Effort: S` — `loop.bound` / `max_iterations` / `on_exhaustion` on the five verified-unbounded commands, wired to `phase-state.py`'s existing `retry` / `quarantine` paths rather than new failure handling. Highest-severity gap; independent of the token work.
- [✗] **Progressive disclosure** *(stopped 2026-08-12 on measured evidence — one command converted, five specs closed unimplemented; see Phase 10 Closure)* `Effort: L` — thin command contract (frontmatter, Overview, Invocation, phase list with gate names, Completion, References); per-phase procedural detail extracts to `skills/<name>/SKILL.md` via `/new-skill`, loaded on demand through `required_skills:`. Top 6 files in descending size order, `implement-story` first. See [ADR-021](../decision-records/adr-021-progressive-disclosure-token-budget.md).
- [x] **Make the governor bite** *(contract checks enforced as blocking `structural`; the absolute byte budget ships measured and non-blocking because five of six target commands are unconverted — see Phase 10 Closure)* `Effort: S-M` — `check_length` command limit 2000 → 400 (single highest-leverage line change in the phase); new blocking `structural` checks for contract presence, Completion presence, loop bounds, and `required_skills:` resolution; absolute `per_surface.commands.chars` cap so growth fails rather than warns; extend `status:`/`evidence:` (ADR-014 vocabulary) to commands and agents so `/refresh-command`'s existing Evidence Gate accrues per-component evidence.
- [x] **Retire dead prescription** `Effort: XS-S` — correct the stale no-frontmatter claim in `system-instructions.md` (32/32 commands carry it); resolve the **8-days-overdue** `required_skills:` review trigger (2026-08-03) by **adoption rather than deprecation**; re-decide `model_tier` ordinal-offset reservation ahead of its 2026-10-16 trigger; fix `.writ/manifest.yaml` (`version: 0.13.1` → `0.28.0`, 44 entries → 31 commands); formally deprecate `.writ/product/decisions.md`.
- [x] **Autonomy boundary** `Effort: XS` — gate-class table in `_preamble.md` extending ADR-013's evidence-based select-or-pause boundary rather than replacing it. See [ADR-022](../decision-records/adr-022-autonomy-gate-classes.md).

### Autonomy Gate Classes

| Class | Behavior |
|---|---|
| Product & spec direction | **Human gate** — contract lock stays an explicit human action |
| Production boundary (merge / PR / release / tag) | **Human gate** — already Prime Directive |
| Design & UX judgment | **Human gate** — taste is not evidence-decidable |
| Destructive / irreversible | **Autonomous with reversibility precondition** — provably git-revertable and restore path recorded before acting |
| Everything else | **Autonomous** within ADR-013's evidence boundary, with audit rationale |

> The destructive class is deliberately *not* a human gate — a maintainer decision recorded in [ADR-022](../decision-records/adr-022-autonomy-gate-classes.md). The reversibility precondition is what keeps it inside ADR-013's "low-risk, reversible, defensible evidence" boundary instead of punching a hole in it.

### Dependencies

- **Retire dead prescription** and **component contract** land first — correcting the stale root contract and defining the contract are prerequisites for everything else.
- **Loop bounds** next; independent of the token work.
- **Governor checks land as `warnings` first**, flipping to `structural` only once the contract/disclosure work brings the surface into compliance. Landing them blocking on day one turns every eval run red, and a permanently-red gate becomes invisible — which is precisely how the current four growth warnings were ignored.
- **Progressive disclosure** is the long pole: one spec per file, 6 files. First planned `L` in this roadmap.

### Out of Scope (deliberately)

- Rewriting commands' *substance*. This phase relocates and contracts procedure; it does not redesign workflows.
- Activating the third-party skill trust model (ADR-018 remains reserve-only).
- Cutting commands from the surface. The goal-orientation audit may *reveal* redundancy, but consolidation is a separate decision, not a Phase 10 deliverable.
- Building any new validation harness — `eval.sh`, `eval-leanness.py`, `lint-skill.sh`, `check-agent-parity.sh`, and `phase-state.py` already exist and are extended, not replaced.

### Honest Caveats (recorded at plan time)

1. **chars/4 is an estimate, not a tokenizer count.** If exact accounting matters for the budget number, tokenize before fixing 400 lines as the cap.
2. **Progressive disclosure can raise total tokens.** It trades one large upfront load for several conditional loads; a command that ends up needing every skill costs *more*. The success criterion must be measured per-invocation load, and `implement-story` is the likeliest case to bite.
3. **400 lines is derived from current distribution** (median ~250, max 961), not from a measured quality threshold. Expect to tune it after 2-3 real extractions.
4. **Extracted skills are born `status: candidate`.** Promotion to `proven` accrues from real use afterward, so this phase does not close the lifecycle loop by itself.

---


### Phase 10 Closure (2026-08-12)

**Status: PARTIALLY COMPLETE.** The determinism half shipped in full; the token
half was measured and stopped on evidence.

**Shipped (merged to `main`, PRs #35/#36):** component contract (31/31 commands
and 7/7 agents declare `problem`/`outcome`/`exit_criteria`; 13 → 31 carry
`## Completion`), loop bounds (0 → 5, each citing calibration evidence), autonomy
gate classes, dead prescription retired, governor instrumented — and its
`justification` field fixed, which had silenced a whole surface at any magnitude
forever. Enforcement then flipped the contract checks to **blocking `structural`**,
proven to bite by mutation.

**Stopped on evidence:** progressive disclosure. One command was converted
(`implement-story`, 52,709 → 24,837 bytes, floor −35.9%, zero drift across a
281-row inventory). It measured **~1,017 bytes of irreducible overhead per
extracted skill** and a **+9.7% worst-path regression** against a projected
+4.1%. The five sibling specs were closed unimplemented, contracts intact, as
the design record.

**Two premises the phase falsified in its own artifacts:**

1. **The token alarm was largely a measurement artifact.** `commands/` measured
   560,772 chars, but no invocation loads the directory. The worst real
   invocation was **77,669 bytes (~19.4k tokens), 7.2× smaller**, and 24,960 of
   it is a shared base no restructuring reduces. `scripts/measure-invocation.py`
   exists because nothing measured this.
2. **ADR-021's mechanism could not do what ADR-021 claimed.** §12 promised skills
   "loaded on demand"; §18 specified `required_skills:`, which the harness
   pre-loads eagerly. Corrected to inline `Read` at point of need.

**Unmet criteria, stated plainly:** `per_surface.commands.chars` did not drop —
it rose to ~560k, and the absolute byte budget ships **non-blocking** because
five of six target commands are unconverted (39,829 bytes total overage, named
in every eval report). The manual criterion — one real `/implement-story` run
with disclosure active — was written here as **not yet run**, and was then **run
and passed later the same day** (`uat/disclosure-harness-probe`, story-1 of the
dirty-tree-guard spec, commit `56f43b3`): all eight applicable skill reads fired
lazily at their own steps, none early, and the story completed — so the −35.9%
floor reduction is real, not paper. Recorded in Scenario 20 of that spec's UAT
plan, with three caveats and two probes still open: the `--quick` path (whether
`boundary-map-computation` and `drift-triage` stay unread — the entire claim of
the skipped path) and the missing-skill degradation probe (steps 5 and 7).
*(Corrected 2026-08-12 — the closure predated the probe by a few commits.)*

### Postscript, 2026-08-12 — the byte goal is withdrawn, not deferred

[ADR-023](../decision-records/adr-023-stakes-proportional-diligence.md) closes the
byte program outright. The two byte/line success criteria above are **void**, and
no number replaces them.

The reason is not that the target was missed. It is that **the target measured the
wrong quantity.** The stated aim is economy of *steps and ruminations to reach exit
criteria*; bytes measure file size. Where they diverge, bytes point the wrong way —
extraction cut `implement-story`'s floor by 35.9% while adding **eight decision
points**, of which **five fire unconditionally on every run and buy nothing**. No
byte instrument can see that trade: it counts what is loaded, never what must be
decided.

The attempt to replace bytes with a step or decision-count threshold was also
abandoned, and this is the durable lesson: **no universal exchange rate exists
between a decision and its cost**, because that cost is a function of the stakes
being weighed. Diligence is now triaged per decision against two questions — does
the answer change what happens, and how bad if it's wrong — recorded in
`commands/_preamble.md` beside ADR-022's gate classes.

Writ therefore has **no mechanically enforced efficiency constraint** as of this
date. That is a deliberate cost, not an oversight: an unenforceable true rule was
judged better than an enforceable wrong one. Reviewed 2026-11-11 alongside ADR-021
and the `required_skills:` trigger.

---

## Phase 11: Contract-and-Verifier Layer — ✅ Complete (2026-09-09)

**Goal:** Rebalance Writ for Fable 5.1-class models: remove behavior instruction
the models no longer need, and put a script behind every quality guarantee that
was prose. Planned in [`2026-09-05-goldilocks-assessment.md`](2026-09-05-goldilocks-assessment.md)
and run as one loop-able Goal Card
([`writ-contract-and-verifier-layer`](../issues/goals/2026-09-05-writ-contract-and-verifier-layer.md)),
one spec per stage. *Promoted to a phase in the 2026-10-01 reconcile pass; it
shipped as six inter-phase rows because the promotion step the assessment named
was never run.*

**Closure status:** All six stage specs Complete and archived; released in
**v0.36.0**.

### Success Criteria

- Dead ends closed and a Fable 5.1 pipeline baseline committed — ✅ two baselines in `.writ/eval/baselines/` over the four-story yuss.app set
- `system-instructions.md` + `_preamble.md` at most 10,000 bytes, every cut in the pruning ledger — ✅ 9,676 bytes; [`pruned-instructions-ledger.md`](../decision-records/pruned-instructions-ledger.md) per [ADR-026](../decision-records/adr-026-constraint-test-pruning.md)
- At most two `implement-story` gates `verification: prose-only` — ✅ exactly two (Gate 1 self-check, Gate 4.5 visual QA)
- `spec-analyze.py` runs at `create-spec` Step 2.6 with an eval check — ✅ advisory
- Default `implement-story` spawns at most two subagents; a `loop: yes` Goal Card converts to a `/goal` invocation with no manual edits — ✅ `--full-pipeline` is the explicit six-agent path

**Honest caveats:** (1) the baseline is single-model; GPT-6 Astra was never
runnable from this workspace, and the Goal Card's own constraint says so.
(2) Spec-analysis findings remain advisory; no precision figure has promoted
them to blocking. (3) The two `prose-only` gates are the input to Phase 12.

### Features

- [x] **Repair and baseline** — `2026-09-05-phase11-repair-and-baseline`
- [x] **Prune the base** — `2026-09-07-phase11-stage2-prune-the-base`
- [x] **Mechanize the gates** — `2026-09-08-phase11-stage2b-mechanize-the-gates`
- [x] **Spec analysis** — `2026-09-08-phase11-stage3-spec-analysis`
- [x] **Goal emit** — `2026-09-09-phase11-stage4-goal-emit`
- [x] **Pipeline demote** — `2026-09-09-phase11-stage4b-pipeline-demote`

---

## Phase 12: Behavioral Verification — ◐ Implemented and released, v0.40.0 (2026-10-02) — human UAT open

**Goal:** A Writ verifier proves the user's feature works by driving the running
app, not only that Writ's own artifacts are well formed. This is the evidence
[ADR-010](../decision-records/adr-010-supervised-autonomy-ceiling.md) review
trigger (a) asks for ("trustworthy machine-verifiable UAT"). Per
[ADR-028](../decision-records/adr-028-behavioral-verification-and-cross-family-panels.md).

**Why now:** the 2026-09-05 assessment measured zero checks that assert a user's
feature works, and Phase 11 left Gate 4.5 (visual QA) as agent self-report. UAT
is still a human handoff at the end of every spec and phase.

### Success Criteria

- A fixture app's UAT scenarios pass end to end with machine-captured evidence and no human step (real-project trials, yuss.app or any other, happen outside the phase at the developer's discretion) — ✅ met, re-derived 2026-10-19: `scripts/tests/fixtures/app-verify/` holds a stdlib app plus pass / fail / not-ready / safety-refused recipes, driven end to end by `scripts/tests/test_app_verify.py`
- Gate 4.5 leaves `verification: prose-only`; the count in `implement-story.md` drops from 2 to 1 — ✅ met, re-derived 2026-10-19: one `verification: prose-only` declaration in `commands/implement-story.md` and one in the `.lean` twin
- `exit-criteria.py` reports `unmet` for a UAT scenario whose cited evidence file is missing (proven by mutation) — ✅ met, re-derived 2026-10-19: `scripts/tests/test_exit_criteria.py::test_missing_evidence_file_is_unmet_naming_spec_and_scenario`
- The cross-family panel raises at least one valid finding the single-vendor evaluator missed on the Phase 11 baseline set, or its promotion step closes `Closed — Not Implemented` and the path is removed — ✅ met 2026-10-02: verdict `keep`, 6 of 8 panel-only findings valid, 4 of them caught by another vendor only ([trial-report](../specs/archive/2026-10-01-cross-family-review-panel/trial-report.md); small sample, not a cost case)

### Features

- [x] **Behavioral verification** `Effort: M-L` — a per-project recipe at `.writ/docs/app-verification.md` (launch, safety, login, feature map, evidence, cleanup) names the project's own checks; `/create-uat-plan` drafts it once and binds scenarios to feature IDs; Gate 4.5 runs the checks for the features a story touched through `scripts/app-verify.py` and writes evidence under the spec folder; `exit-criteria.py` checks the cited evidence exists and passed. A machine verdict (exit code) decides; features no check can decide stay human scenarios and say why. Writ ships no runtime. (Merged from the former "Project verification skill" and "Evidence-bound UAT" features at contract lock, 2026-10-01: the recipe's only consumers are the UAT binding and Gate 4.5.)
- [x] **Cross-family review panel** `Effort: S-M` — opt-in per project, high-stakes stories only (ADR-023 triage): Gate 3 adds reviewers from other vendors with the same prompt; findings raised by two or more vendors block, single-vendor findings are advisory. Cursor-only today; every other platform falls back to the current Gate 3. Spec: [`2026-10-01-cross-family-review-panel`](../specs/archive/2026-10-01-cross-family-review-panel/spec.md) (additive: the panel only adds blocks; `gate3_route` or `--panel` is the stakes signal).

### Dependencies

- The Gate 3 evaluator, and the Phase 11 baseline story set (yuss.app) for the panel's removal measurement
- The two features are independent and can run in parallel

### Deliberately out of scope

Raising the autonomy ceiling (needs its own ADR citing this phase's results),
autonomous merge or PR creation, a Writ-owned browser or test runner, per-role
model configuration for agents.

---

## Phase 13: Subtract and Repair (1-2 weeks) — 📋 Committed (2026-10-20)

**Goal:** Writ ships only what it uses and installs the same root contract on every platform. It fixes every defect the 2026-10-19 research found before anything new lands. Per [ADR-030](../decision-records/adr-030-contract-verifier-boundary-front-door.md).

**Why now:**
- The pstack comparison ([research](../research/2026-10-19-writ-vs-pstack-research.md), F6, F7, and the defect table) and the prototype research ([F6](../research/2026-10-19-prototype-visual-drafts-research.md)) found ten defects.
- `eval-leanness.py` reports every surface past its own justified ceiling: commands 13,335 lines against 11,081, and scripts 87,066 against 46,748.
- Dormant code still ships: `recommend-state.py` is 3,807 lines and no command calls it.
- Design Principle 7 applies: subtract before you add.

### Success Criteria

- A fresh Claude Code install carries the Prime Directive. Its `CLAUDE.md` block is generated from the command registry, and an eval check fails when a registered command is missing from it.
- CI runs `pytest` on the 3.9 floor and the bash tests on every PR, alongside `eval.sh`.
- `update.sh` keeps a locally modified stale file on every run and keeps the Codex config baseline. Each is proven by a test that fails on today's script.
- No shipped command names a tool that no adapter translates; `cursor-ide-browser` is replaced. Writ's `/design` no longer collides with Claude Code's native `/design`, verified by a clean-room install.
- `adapters/claude-code.md` documents only commands and flags that exist, and its worktree guidance agrees with `skills/subagent-worktree-integration`.
- None of the following is left in what `install.sh` ships:
  - a `*.lean.md` file or a `WRIT_HARNESS_LEAN` branch
  - a `(no-op until ADR-025 Story 1)` line
  - `recommend-state.py`'s dormant staging path
- Shipped commands link none of Writ's own development artifacts: archived specs, research documents, Writ's ADR files, or `calibrated_against` citations of Writ's calibration state. An eval check enforces it. Runtime paths such as `.writ/state/` are legitimate and stay.
- `create-spec.md` gets the reduction pass PR #59 deferred. Its recorded overage falls instead of being repinned upward. The figure is drift signal per ADR-023, not a design target.
- The phase-close leanness audit (Tier B) runs and is dated. None has run since July.

### Features

- [ ] **Claude Code parity** `Effort: S`
  - Install the Prime Directive and base rules.
  - Generate the `CLAUDE.md` block from `.writ/manifest.yaml`.
  - Correct `adapters/claude-code.md`: remove the nonexistent `/implement-story --all` and agent teams, and align its worktree text with the worktree skill.
- [ ] **CI runs every suite** `Effort: XS`: `pytest` (3.9 floor) and `scripts/tests/test_*.sh` join `eval.sh` in `.github/workflows/eval.yml`.
- [ ] **Update-path bugs** `Effort: S`
  - [`2026-10-12-update-deletes-modified-stale-files`](../issues/bugs/2026-10-12-update-deletes-modified-stale-files.md)
  - [`2026-10-12-codex-config-baseline-dropped-on-update`](../issues/bugs/2026-10-12-codex-config-baseline-dropped-on-update.md)
- [ ] **Platform-neutral names** `Effort: S`
  - [`2026-10-19-prototype-visual-preview-cursor-only`](../issues/bugs/2026-10-19-prototype-visual-preview-cursor-only.md)
  - [`2026-10-19-design-command-name-collision`](../issues/bugs/2026-10-19-design-command-name-collision.md): rename Writ's `/design`, or detect and delegate.
- [ ] **Cuts** `Effort: S-M`
  - Delete the five lean siblings and the flag. The null result stays in `.writ/decision-log.md`.
  - Move `recommend-state.py`'s staging reducers and the state-format doc out of the shipped set. The design stays preserved in ADR-013 and the source repo. One live caller exists: `skills/drift-triage` calls `record-spec-lite-amendment` in recommended mode. The spec decides whether that branch goes too.
  - Remove the ADR-025 no-op lines and their `check_model_escalation` pins.
  - Strip Writ-internal references from shipped commands.
  - Correct `/ship`'s description, which says "merged PR" while its exit criteria stop at an open PR.
  - Replace the highest-churn `require_literal` pins with structural checks.
- [ ] **`create-spec` reduction pass** `Effort: S`

### Dependencies

- None. The agent CLI contract (v0.42.0) already settled which scripts ship. The cuts start from that list.

### Deliberately out of scope

New capability of any kind, and any change to gate behavior. Every item here removes, corrects, or aligns.

---

## Phase 14: Front Door and Distribution (3-4 weeks) — 📋 Committed (2026-10-20)

**Goal:** A new user goes from install to a correctly routed first task with one command, on Cursor or Claude Code, from one generated source. Per [ADR-030](../decision-records/adr-030-contract-verifier-boundary-front-door.md).

**Why now:**
- Writ ships 32 commands, and `README.md` says five are enough.
- The mission's Adaptive Ceremony differentiator claims Writ suggests the right level of process, but no command does.
- pstack's quickstart is two steps and one router (research F1).
- `/prototype` is now the exploration workflow (PR #59, v0.42.0). The front door routes to it and does not duplicate it.

### Success Criteria

- A front-door command exists with one outcome: the request is restated in Writ's own words and routed to the existing command whose ceremony fits. It writes nothing beyond what the routed command writes.
- It routes as follows:
  - an unsettled idea goes to `/prototype`
  - a bug or a small change goes to `/prototype --no-diverge`
  - a feature goes to `/create-spec`
  - roadmap work goes to `/implement-phase`
  - a "why" or "how" question goes to `/why` (Phase 15), or to `/research` until `/why` exists
  - a fork that running something could answer goes to `/prototype`, not to a question
- The routed command's phases appear in the todo list, and a skipped phase shows as `skip: <reason>`.
- Writ installs as a plugin in Cursor and in Claude Code. Scripts run from the plugin directory, and `/initialize` scaffolds `.writ/`. `install.sh` stays until both plugin installs pass the same smoke test.
- Per-platform trees are generated from one source. CI fails when a command uses a platform term its adapter does not map, and when a generated tree is stale.
- The README's start section is the front door, not the command table.

### Features

- [ ] **Front door** `Effort: M`
  - Absorbs [`2026-10-13-in-your-own-words`](../issues/features/2026-10-13-in-your-own-words.md) as its restate step.
  - Absorbs the empirical-fork rule (promoted from the parking lot) as a routing rule.
- [ ] **Plugin distribution** `Effort: M`
  - Promoted from the parking lot.
  - Resolves [`2026-10-12-script-install-location`](../issues/improvements/2026-10-12-script-install-location.md).
  - Verify Claude Code's plugin format first (pstack research, Further Research 1).
- [ ] **Generated trees and adapter coverage check** `Effort: S-M`: pstack's `generate-pstack-harness-trees.mjs` is the reference. This check is the structural fix for the `cursor-ide-browser` class of defect.
- [ ] **Rendering-delegation rows** `Effort: S`
  - Cursor, Codex, and OpenClaw rows for `/prototype`'s draft rendering.
  - First-party verification of Claude Code's native `/design` (prototype research, Further Research 1 and 4).
- [ ] **Prompting guide** `Effort: XS`: what a request should carry (goal, done check, proof), recipes, and pitfalls.

### Dependencies

- Phase 13. Parity and the cuts make the generated trees correct and smaller.

### Deliberately out of scope

Model routing, new verification, and any rewrite of the commands the front door routes to.

**Review at phase close (ADR-030):** if work still starts from direct commands, remove the front door.

---

## Phase 15: Code-Level Rigor (2 weeks) — 📋 Committed (2026-10-20)

**Goal:** Writ's verifier reaches the design and the fix on high-stakes routes, and Writ answers "why is this like this?" from its own ledger. Per [ADR-030](../decision-records/adr-030-contract-verifier-boundary-front-door.md).

**Why now:**
- Writ's gates check that artifacts are well formed and that tests pass.
- pstack's `architect`, `interrogate`, `blast-radius`, and bug-fix playbook ask whether the design and the fix are right (research F3).
- Writ owns the best evidence for "why", but has no command that reads it (F4).
- `/prototype`'s divergence rules are inline until a second caller exists. Gate 0 is that caller (prototype research, Recommendation 2).

### Success Criteria

- **`/why`:**
  - Reads Writ's ledger first (ADRs, drift logs, specs, What Was Built records, git notes), then git history, then available MCPs.
  - Gives every claim a confidence tier.
  - When a change follows, ends with Preserve / Change / Avoid / Risk, and `/create-spec` discovery reads that list.
- **Design divergence:**
  - `skills/design-divergence/SKILL.md` has two live callers: `/prototype` Step 2.5, and Gate 0 on the boundary-crossing route.
  - The Gate 0 route writes the caller's usage first, then produces two independent sketches on declared axes.
  - The skill covers API shapes and data models as well as UI.
- **Divergence trial:** declared-axes generation against a naive "give me three options" prompt, rated blind for structural distinctness. The trial also records whether render-only drafts were enough. The skill stays only if declared axes win.
- **Gate 2.5:** on the review-agent route, it names the one fact the change is safe because of and the evidence rung that fact reached.
- **`tdd-cycle` for bugs:** a failing repro on the surface where the bug shows, committed before the fix, with failing-then-passing output in the report.
- **Reviewer prompts** carry lead-judgment filters:
  - all nits means the code is fine
  - trace the call site before accepting a hypothetical
  - be slow to dismiss security findings
- **`/retro` output:**
  - Orders fixes as architecture, then types, then a lint, then a test, then docs.
  - Proves each new check fails on a real past mistake.
  - Keeps a rule-to-enforcer table.
- **Removal measurement:** on the Phase 11 baseline story set, each gate upgrade catches at least one defect the current gates passed. Any upgrade that does not is removed.

### Features

- [ ] **`/why`** `Effort: M`: ledger first, confidence tiers, a Preserve / Change / Avoid / Risk handoff.
- [ ] **`design-divergence` skill and the usage-first Gate 0** `Effort: M`: includes the blind trial.
- [ ] **Blast-radius safety fact at Gate 2.5** `Effort: S`
- [ ] **Repro-first bug fixing in `tdd-cycle`** `Effort: S`: reaches both `/prototype` and `/implement-story`.
- [ ] **Reviewer lead-judgment filters** `Effort: XS`
- [ ] **`/retro` fix ladder and rule-to-enforcer table** `Effort: S`: replaces the retired friction-signal design. `/refresh-command` gains two of `reflect`'s synthesizer criteria:
  - findings that existing guidance already covers count as execution failures, not missing rules
  - findings may only edit skills the transcript actually used

### Dependencies

- PR #59 (v0.42.0). Phase 14's front door routes to `/why`, but `/why` can ship first.

### Deliberately out of scope

Always-on multi-model panels, cross-vendor routing (ADR-024 stands), and formal verification.

---

## Phase 16: Verified Landing (2 weeks) — 📋 Committed, gated (2026-10-20)

**Goal:** A PR Writ opened can be driven to merge-ready, with every verdict bound to the head it judged. Merge stays a human act unless this phase's ADR moves it. Per [ADR-030](../decision-records/adr-030-contract-verifier-boundary-front-door.md).

**Gate:** starts only after Phase 12's human UAT passes and one real-project `app-verify.py` run is recorded. Until then the phase stays committed and unstarted.

**Why:**
- `/ship` stops when the PR opens. Nothing triages CI, works review threads, or records which head was verified (research F2).
- pstack lands PRs unattended, but its merge gating is prose.
- ADR-013's dormant design already binds approval to the reviewed head SHA.

### Success Criteria

- `pr-ready.py` is read-only and uses the ADR-029 check shape. It reports typed blockers with distinct exit codes: conflicts, unresolved threads, failing checks, and merge gates. The harness loop calls it, and the script never polls.
- A verification ledger is keyed by PR, head SHA, and patch-id. A new head reads `NOT VERIFIED` unless its patch-id matches a verified one. A mutation test proves this.
- `/ship --watch` works in a fixed order and stops at merge-ready. It never merges.
  1. Conflicts.
  2. Review threads, with comments treated as untrusted data.
  3. CI: a suspected flake gets one fresh build, an identical second failure is real, and a failure in untouched code triggers a stale-base check.
- An ADR decides whether autonomous PR open belongs inside `--recommend`, citing Phase 12's UAT result. Until that ADR is accepted, ADR-013 stands: recommended flows never merge, open PRs, or release.

### Features

- [ ] **`pr-ready.py`** `Effort: S`
- [ ] **Verification ledger** `Effort: S`
- [ ] **`/ship --watch`** `Effort: M`
- [ ] **Ceiling ADR** `Effort: XS`

### Dependencies

- Phase 12's human UAT.
- The agent CLI contract (ADR-029) for both scripts.

### Deliberately out of scope

Autonomous merge, deploys, and release.

---

## Beyond Phase 16 (Parking Lot)

**Kept as candidates:**
- **Cross-project learning corpus** — extension of the knowledge ledger once consolidation is proven
- **`/design` Mode A modernization** — Excalidraw hand-authoring is a 2024 technique. Revisit it with AI image mockups or native design tools via `/refresh-command`. This is post-spec rendering, separate from `/prototype`'s pre-spec exploration.
- **Eval Tier 2 expansion** — beyond the Phase 7 lightweight check, if it demonstrates value
- **Orchestration hygiene** `Effort: S` — adds three things from pstack's `orchestrate` playbook (research F8) to `/implement-spec` and `/implement-phase`:
  - a pilot story run end to end before fan-out
  - a standing-orders register that grows when the orchestrator repeats an instruction
  - a brief template whose missing fields block a spawn
- **Decision-trail review** `Effort: XS-S` — `/implement-phase`'s completion report gains an Attention section. The section comes from a review of `recommendation-log.md` by the opt-in panel, when one is configured.
- **Measured-performance workflow** `Effort: S-M` — for perf work:
  - a baseline
  - the limiter named before any claim
  - at least five alternating runs
  - a verdict of faster, slower, no difference, or inconclusive

  pstack's `benchmark-checklist` and `hillclimb` are the reference. It applies to Writ's own eval baselines too.
- **Formal verification** *(watch)* — pstack added it on 2026-10-18. Revisit in November 2026.

**Promoted 2026-10-20:** Cursor plugin distribution and the empirical-fork rule, both into Phase 14.

**Deferred until concrete signal:**
- **Team affordances** (cross-dev drift reconciliation, `/review-spec`, multi-repo orchestration) — trigger: a second human on a shared Writ project. See [ADR-007](../decision-records/adr-007-team-audience-sequencing.md).
- **Business-process sister pipeline** — same contract-first primitives applied to non-dev workflows; trigger: a concrete first business process to anchor the design. See `.writ/issues/features/2026-05-03-business-process-writ-pipeline.md`.

**Dropped:**
- **Opaque, unbounded autonomous loops (Ralph successor)** — deliberate non-goal per [ADR-013](../decision-records/adr-013-recommended-autonomous-delivery.md); recommended autonomy is confined to evidence-backed spec authoring (`/create-spec --recommend`) and the bounded end-to-end phase loop (`/implement-phase --recommend`), which ends at the completion report and never merges, opens PRs, or releases
- **`/audit`, `/lessons`, per-story scorecards** — cancelled at Phase 5 closure
- **Friction signals & Improvement Requests** — retired 2026-10-20 by [ADR-030](../decision-records/adr-030-contract-verifier-boundary-front-door.md), never started. `/retro`'s transcript review (v0.41.0) covers the purpose, and Phase 15 gives it a fix ladder. `scripts/signal.py`, `signals.jsonl`, the `/status` nudge, and `Signal:` evidence will not be built. The no-op emit lines come out in Phase 13.
- **Notification integrations, cross-AI parallel coordination, browser daemon** — carried over from prior refresh; still out of scope

---

## Effort Sizing

| Size | Duration | Example |
|------|----------|---------|
| **XS** | 1-2 days | `/status` health line, User Challenge framing |
| **S** | 3-5 days | Quarantine branching, `dependencies:` frontmatter, adapter memory guidance |
| **M** | 1-2 weeks | Fresh context per spec, skill extraction, evidence-bound `/refresh-command`, component contract |
| **L** | 3-4 weeks | Progressive disclosure of the top 6 command files (Phase 10) |
| **XL** | 1+ months | (reserved) |

### Pacing Discipline

Phases 6-8 total roughly 4-7 weeks of focused work at solo-maintainer pace. Each phase ships independently; bundling them is the failure mode to avoid (research addendum Risk #1: solo-maintainer asymmetry).

Phase 10 is 3-5 weeks, and its long pole (progressive disclosure) decomposes into **one spec per command file** for exactly this reason — six independently shippable units rather than one bundled rewrite. The phase's own sequencing note (governor checks land as warnings before blocking) is the same discipline applied to enforcement.

Phases 13–16 total about 8–10 weeks at the estimates above. Phase 11's six specs shipped in five days and Phase 12 in about two weeks, so the real pace may be faster. Each phase ships on its own, and each phase's features decompose into one spec per feature. Phase 16 waits on Phase 12's human UAT, not on Phase 15. If the UAT lands early, Phase 16 can run beside Phase 15.

---

## Design Principles (Apply to Every Phase)

1. **Adaptive ceremony** — Every feature must justify its weight. More process only when more process is warranted.
2. **Local-first** — Improvements land in the project first. Upstream promotion is optional, never forced.
3. **Dogfood everything** — Use Writ to build Writ. Every feature goes through the pipeline.
4. **Delegate mechanics, own contracts** — If the harness does it natively, adapt to it; never re-implement it. New surface must pass the test: *does this drive output the model wouldn't produce unprompted?*
5. **Aplomb** — Agents should handle complexity with grace, not grind through checklists.
6. **Opinionated by default** — Lead with the recommendation, explain why, then offer alternatives. Judgment, not menus.
7. **Subtract before you add** — Each phase opens by removing what no longer earns its place: dormant code, null-result experiments, and references users cannot resolve. A phase that only adds says why nothing could be removed. *(Added 2026-10-20, [ADR-030](../decision-records/adr-030-contract-verifier-boundary-front-door.md).)*
