# Writ — Product Roadmap

> Based on Product Contract: 2026-02-27, refreshed 2026-07-10 (2026 harness audit — see ADR-010, ADR-011, ADR-012, ADR-013)
> Last Updated: 2026-07-17
> Cadence: Steady — ongoing improvement alongside real projects, compounding over months

**Strategic frame (2026-07-09 refresh):** Harnesses natively absorbed much of what Writ's early phases built scaffolding for (memory, skills, subagents, planning modes, context management). Writ's posture going forward: **keep the harness light, own the contracts, delegate the mechanics** — prune what platforms do natively, expand where Writ compounds (supervised autonomy, evidence-based self-improvement, consolidating memory with external interop).

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

**Closure status:** All seven features shipped and verified by eval Tier 1 (`spec-dependencies`, `phase-lanes`, `phase-challenges`, `phase-quarantine`, `phase-knowledge`, `phase-health`, `ralph-retirement`), a disposable multi-spec sandbox UAT, and one real-use User Challenge — see [`acceptance-evidence.md`](../specs/2026-07-09-phase6-autonomy-ceiling/acceptance-evidence.md). Ralph is archived under `archive/ralph/`. **One honest caveat:** the "3+ spec phase runs end-to-end in real use" criterion is proven *mechanically* (sandbox) only — an umbrella spec cannot self-prove it; the first genuine multi-spec `/implement-phase` run (Phase 7 onward) will exercise it live. Not yet released — pending `/release`.

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

**Closure status:** All four features shipped as contract-first specs, each implemented in an isolated per-spec lane and merged only after independent verification (`b3dd3e4` skill-lifecycle, `3ee2b98` skill-extraction, `56207ac` evidence-bound-refresh, `32d1dca` knowledge-consolidation). Verified by the full eval Tier 1 suite on the merged phase branch (exit 0, 0 findings — including the three new checks `skill-lifecycle`, `refresh-evidence`, `knowledge-consolidate`), 79 UAT scenarios across four `uat-plan.md` files, and one evidence-bound knowledge lesson written at phase close. As the first genuine multi-spec `/implement-phase` run (the live exercise Phase 6 could only prove mechanically), it also surfaced and fixed a real orchestration defect — ephemeral lane worktrees weren't gitignored (`f06f405`) — and filed a tracked bug for `create-lane` worktree pathing. **Honest caveats:** (1) extracted skills are born `status: candidate` and wired to live consumers now; promotion to `proven` accrues via evidence later. (2) Knowledge consolidation is **mechanism-complete**: the loop is proven end-to-end on the real ledger with a reviewable diff (it surfaced and cleaned a malformed phase-close entry), but a literal merge/prune of duplicates awaits a genuine duplicate — the current ledger is honestly clean. Work lives on `phase/7-compounding-layer`; not yet merged to main or released — pending review and `/release`.

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

**Closure status:** Decomposed into two contract-first specs, each implemented in an isolated per-spec lane and merged only after independent verification (`f88c6f8` gbrain-compatibility-recipe, `477359c` native-memory-guidance) on `phase/8-memory-interop`. Machine-checkable exit criteria verified by the new `memory-interop` eval Tier 1 check (0 findings) and the full suite green; 21 UAT scenarios across two `uat-plan.md` files. The GBrain recipe is grounded in GBrain's *real* interface (`garrytan/gbrain`: `gbrain sources add`/`sync`/`doctor --json`/`search`/`serve`), not an invented API. **Honest caveat:** the "GBrain-equipped project answers retrieval queries" criterion and the *live* round-trip cannot be machine-verified here (no GBrain install; Writ ships none) — they are handed off as UAT scenarios 10–12. Recipe accuracy is verified against current docs; live behavior awaits a GBrain-equipped machine. Not merged to main or released — pending review and `/release`.

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

## Beyond Phase 8 (Parking Lot)

**Kept as candidates:**
- **Cross-project learning corpus** — extension of the knowledge ledger once consolidation is proven
- **`/design` Mode A modernization** — Excalidraw hand-authoring is a 2024 technique; revisit with AI image mockups or native design tools via `/refresh-command`
- **Eval Tier 2 expansion** — beyond the Phase 7 lightweight check, if it demonstrates value

**Deferred until concrete signal:**
- **Team affordances** (cross-dev drift reconciliation, `/review-spec`, multi-repo orchestration) — trigger: a second human on a shared Writ project. See [ADR-007](../decision-records/adr-007-team-audience-sequencing.md).

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
| **M** | 1-2 weeks | Fresh context per spec, skill extraction, evidence-bound `/refresh-command` |
| **L** | 3-4 weeks | (none currently planned) |
| **XL** | 1+ months | (reserved) |

### Pacing Discipline

Phases 6-8 total roughly 4-7 weeks of focused work at solo-maintainer pace. Each phase ships independently; bundling them is the failure mode to avoid (research addendum Risk #1: solo-maintainer asymmetry).

---

## Design Principles (Apply to Every Phase)

1. **Adaptive ceremony** — Every feature must justify its weight. More process only when more process is warranted.
2. **Local-first** — Improvements land in the project first. Upstream promotion is optional, never forced.
3. **Dogfood everything** — Use Writ to build Writ. Every feature goes through the pipeline.
4. **Delegate mechanics, own contracts** — If the harness does it natively, adapt to it; never re-implement it. New surface must pass the test: *does this drive output the model wouldn't produce unprompted?*
5. **Aplomb** — Agents should handle complexity with grace, not grind through checklists.
6. **Opinionated by default** — Lead with the recommendation, explain why, then offer alternatives. Judgment, not menus.
