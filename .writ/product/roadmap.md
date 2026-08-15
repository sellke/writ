# Writ — Product Roadmap

> Based on Product Contract: 2026-02-27, refreshed 2026-07-10 (2026 harness audit — see ADR-010, ADR-011, ADR-012, ADR-013)
> Last Updated: 2026-08-15
> Cadence: Steady — ongoing improvement alongside real projects, compounding over months

**Current status (2026-08-12):** Phases 1–10 closed. **Phase 10 closed PARTIALLY COMPLETE (2026-08-12)** — the determinism half (component contract, loop bounds, gate classes, blocking governor checks) shipped and is enforced; progressive disclosure stopped on measured evidence; the byte goal withdrawn outright by [ADR-023](../decision-records/adr-023-stakes-proportional-diligence.md). **No phase is currently committed** — next candidates live in [Beyond Phase 10 (Parking Lot)](#beyond-phase-10-parking-lot), pulled forward on concrete signal.

**Strategic frame (2026-07-09 refresh):** Harnesses natively absorbed much of what Writ's early phases built scaffolding for (memory, skills, subagents, planning modes, context management). Writ's posture going forward: **keep the harness light, own the contracts, delegate the mechanics** — prune what platforms do natively, expand where Writ compounds (supervised autonomy, evidence-based self-improvement, consolidating memory with external interop).

**Posture addendum (2026-08-11, Phase 10):** *Self-improving, token-efficient, and maximally autonomous — except where taste and agency require humans.* Phase 10 turns "keep the harness light" from a stated intent into a measured, enforced property. The trigger was a maintainer concern raised as **explicitly unverified** ("too prescriptive in some ways, not deterministic enough in others"); per the Prime Directive it was measured before planning, and **both halves verified** — the command surface is 516,589 chars (~129k tokens) while **0 of 5** loop-bearing commands declare any iteration bound. See [ADR-020](../decision-records/adr-020-component-contract.md), [ADR-021](../decision-records/adr-021-progressive-disclosure-token-budget.md), [ADR-022](../decision-records/adr-022-autonomy-gate-classes.md). *(ADR-021 since superseded by [ADR-023](../decision-records/adr-023-stakes-proportional-diligence.md); the 516KB figure was later shown to be a measurement artifact — see the Phase 10 Closure.)*

### Revision Log

| Date | Change |
|---|---|
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

**Closure status:** All seven features shipped and verified by eval Tier 1 (`spec-dependencies`, `phase-lanes`, `phase-challenges`, `phase-quarantine`, `phase-knowledge`, `phase-health`, `ralph-retirement`), a disposable multi-spec sandbox UAT, and one real-use User Challenge — see [`acceptance-evidence.md`](../specs/2026-07-09-phase6-autonomy-ceiling/acceptance-evidence.md). Ralph is archived under `archive/ralph/`. **One honest caveat:** the "3+ spec phase runs end-to-end in real use" criterion is proven *mechanically* (sandbox) only — an umbrella spec cannot self-prove it; the first genuine multi-spec `/implement-phase` run (Phase 7 onward) will exercise it live. Released in **v0.19.0** (2026-07-11, jointly with Phase 7).

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
[`2026-07-11-product-reconciliation`](../specs/2026-07-11-product-reconciliation/spec.md).

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
  [`2026-07-18-git-notes-audit-channel`](../specs/2026-07-18-git-notes-audit-channel/spec.md).
  `/ship` attaches a spec-level audit digest (composed from "What Was Built"
  records) to the landed commit under a dedicated `refs/notes/writ` ref; `/release`
  attaches a version rollup; sync via configured refspecs; default-on, clean
  opt-out; `/status` read line. (Conductor's git-notes idea, adapted to Writ's
  squash-merge `/ship` — attach post-land so notes aren't orphaned.)
- [x] **Logical-unit revert (`/revert`)** `Effort: M` — Spec
  [`2026-07-18-logical-unit-revert`](../specs/2026-07-18-logical-unit-revert/spec.md).
  Single `/revert <unit>` (story|spec) with a layered commit resolver
  (`scripts/revert-resolve.py`: recorded SHA → `/ship` `Ref:` footer → phase-state
  → confirmed ghost-commit fuzzy match), safe/hard strategies, dirty-tree guard,
  and full artifact restoration. Prerequisite: `/implement-story` records each
  story's commit SHA. (Conductor's `conductor-revert` model; ghost-commit
  reconciliation is the borrowed robustness trick.)
- [x] **Artifact integrity + handshake (robustness rider)** `Effort: S` — Spec
  [`2026-07-18-artifact-integrity-handshake`](../specs/2026-07-18-artifact-integrity-handshake/spec.md).
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

## Beyond Phase 10 (Parking Lot)

**Kept as candidates:**
- **Cross-project learning corpus** — extension of the knowledge ledger once consolidation is proven
- **`/design` Mode A modernization** — Excalidraw hand-authoring is a 2024 technique; revisit with AI image mockups or native design tools via `/refresh-command`
- **Eval Tier 2 expansion** — beyond the Phase 7 lightweight check, if it demonstrates value

**Deferred until concrete signal:**
- **Team affordances** (cross-dev drift reconciliation, `/review-spec`, multi-repo orchestration) — trigger: a second human on a shared Writ project. See [ADR-007](../decision-records/adr-007-team-audience-sequencing.md).
- **Business-process sister pipeline** — same contract-first primitives applied to non-dev workflows; trigger: a concrete first business process to anchor the design. See `.writ/issues/features/2026-05-03-business-process-writ-pipeline.md`.

**Dropped:**
- **Opaque, unbounded autonomous loops (Ralph successor)** — deliberate non-goal per [ADR-013](../decision-records/adr-013-recommended-autonomous-delivery.md); recommended autonomy is confined to evidence-backed spec authoring (`/create-spec --recommend`) and the bounded end-to-end phase loop (`/implement-phase --recommend`), which ends at the completion report and never merges, opens PRs, or releases
- **`/audit`, `/lessons`, per-story scorecards** — cancelled at Phase 5 closure
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

---

## Design Principles (Apply to Every Phase)

1. **Adaptive ceremony** — Every feature must justify its weight. More process only when more process is warranted.
2. **Local-first** — Improvements land in the project first. Upstream promotion is optional, never forced.
3. **Dogfood everything** — Use Writ to build Writ. Every feature goes through the pipeline.
4. **Delegate mechanics, own contracts** — If the harness does it natively, adapt to it; never re-implement it. New surface must pass the test: *does this drive output the model wouldn't produce unprompted?*
5. **Aplomb** — Agents should handle complexity with grace, not grind through checklists.
6. **Opinionated by default** — Lead with the recommendation, explain why, then offer alternatives. Judgment, not menus.
