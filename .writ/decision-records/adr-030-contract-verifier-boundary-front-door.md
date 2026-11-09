# ADR-030: Contract, Verifier, Boundary, and One Front Door

> **Date:** 2026-10-20
> **Status:** Accepted
> **Amended:** 2026-10-30 — Design Principle 8, land before you add (see § Amendments)
> **Category:** Product Strategy
> **Deciders:** @AdamSellke
> **Evidence base:** [`2026-10-19-writ-vs-pstack-research.md`](../research/2026-10-19-writ-vs-pstack-research.md) (pstack 0.15.28 read at source), [`2026-10-19-prototype-visual-drafts-research.md`](../research/2026-10-19-prototype-visual-drafts-research.md), [`2026-09-05-goldilocks-assessment.md`](../product/2026-09-05-goldilocks-assessment.md)
> **Supersedes:** [ADR-025](adr-025-friction-signals.md) Decisions 1, 3, and 6 (the signal file, the nudge, and the `Signal:` evidence bridge) and its 2026-12-02 review
> **Amends:** [ADR-029](adr-029-agent-cli-contract.md) review trigger, which now reads `/retro` findings instead of friction signals
> **Keeps:** [ADR-010](adr-010-supervised-autonomy-ceiling.md), [ADR-013](adr-013-recommended-autonomous-delivery.md), and [ADR-022](adr-022-autonomy-gate-classes.md) unchanged at the time of writing. *2026-11-05: [ADR-033](adr-033-doubt-gated-autonomy.md) supersedes ADR-022's gate-class table and ADR-013's flag-scoped autonomy, and is the ceiling ADR this record left to Phase 16.*
> **Respects:** [ADR-015](adr-015-leanness-self-governance.md) (leanness), [ADR-020](adr-020-component-contract.md) (one outcome per command), [ADR-023](adr-023-stakes-proportional-diligence.md) (stakes triage), [ADR-024](adr-024-model-delegation.md) (family-locked tiers), [ADR-028](adr-028-behavioral-verification-and-cross-family-panels.md) (runtime boundary)

## Decision

**Writ owns three things and delegates or deletes the rest:**

1. **The contract:** the spec, its acceptance criteria and exit criteria, and the stakes of each decision.
2. **The verifier:** scripts that re-derive verdicts about the code and the running app, not only about Writ's own artifacts.
3. **The boundary:** what an agent may not do without a human.

**Users reach Writ through one front door.** A single entry command restates the request, classifies it, and routes it to the existing command at the right level of ceremony. An idea that is not settled goes to `/prototype`, which is now the exploration workflow (PR #59).

**The roadmap after Phase 12 is four phases, in this order:**

| Phase | Scope |
|---|---|
| 13 Subtract and Repair | Every defect the two research documents found, plus the cuts, before anything new lands |
| 14 Front Door and Distribution | The entry command; plugin distribution for Cursor and Claude Code; generated per-platform trees with an adapter coverage check |
| 15 Code-Level Rigor | `/why`; design divergence beyond UI; blast radius; repro-first bug fixing; reviewer judgment filters; `/retro`'s fix ladder |
| 16 Verified Landing | A PR-readiness check and a verification ledger bound to the PR head SHA. Starts only after Phase 12's human UAT passes. |

**Friction signals are retired.** `/retro` already reads transcripts on Claude Code, Cursor, and Codex (v0.41.0) and is Writ's learning channel. `scripts/signal.py`, `.writ/state/signals.jsonl`, the `/status` nudge, `/retro --friction`, and the `Signal:` evidence type will not be built. The `(no-op until ADR-025 Story 1)` lines and their eval pins are removed in Phase 13. Until then they stay, because the eval pins them.

**Positioning.** A skill pack such as pstack makes each agent rigorous. Writ keeps the project's intent and checks the result against it, across sessions, agents, and platforms. The two can run in the same project.

### What Writ takes from pstack, and what it declines

| Take | Into | Decline | Why |
|---|---|---|---|
| One router; playbook steps mirrored in the todo list with `skip: <reason>` | Phase 14 front door | Proceeding without asking on team chat and ticket updates | ADR-022 gate classes |
| Empirically answerable forks go to a prototype, not a question | Phase 14 front door, routed to `/prototype` | The no-planning stance | It removes the contract users come for |
| Generated harness trees; fail on an unmapped platform term | Phase 14 | Bun and TypeScript tools | ADR-029 rule 5 |
| `why`: evidence per source, confidence tiers, Preserve / Change / Avoid / Risk | Phase 15 `/why`, ledger first | `why`'s seven-source sweep by default | Cost; ADR-023 |
| `architect`: caller usage first, two independent sketches | Phase 15 Gate 0, via the extracted `design-divergence` skill | A 1,000-line file as a presumptive blocker | One author's taste |
| `blast-radius` evidence ladder; `interrogate` lead-judgment filters | Phase 15 Gate 2.5 and reviewers | Always-on multi-model panels | ADR-024; ADR-028 keeps panels opt-in |
| `correct` fix ladder and rule-to-enforcer table | Phase 15 `/retro` output | `reflect` filing backlog items without approval | ADR-022 |
| `babysit`, `shipping`, `watch-pr`, `orch` ledger | Phase 16 | Autonomous merge | ADR-010 and ADR-013 stand until Phase 16's ADR |
| Continuous subtraction | Phase 13 and every phase close | Style rules as universal rules | `plain-prose` already covers the useful part |

## Context and Problem Statement

Writ took pstack's mechanisms one at a time: behavioral verification and the cross-family panel (ADR-028), and the agent CLI contract (ADR-029). The first full comparison (2026-10-19) found a consistent picture:

- **Writ is ahead** on durable intent (contract lock, `[AC-N.M]` traceability, drift logs, ADRs, the knowledge ledger, product docs) and on enforcement in code. pstack's most dangerous invariants, such as merging only after a verdict, are prose.
- **Writ is behind** on four things:
  - **Entry.** Writ has 32 commands, and its README concedes five are enough.
  - **The last mile.** `/ship` stops when the PR opens.
  - **Code-level rigor.** Writ's gates check that artifacts are well formed and tests pass. They do not ask whether the design or the fix is right.
  - **Platform parity.** Claude Code installs ship without the Prime Directive.
- **Writ's surface** is past its own justified ceilings on every measured axis, and it still ships dormant code.

Separately, the 2026-10-19 prototype research reframed `/prototype` as the early exploration workflow, and PR #59 shipped that reframe in v0.42.0. That makes `/prototype` the place where an unsettled idea goes, so the front door must route to it rather than duplicate it. The research left two items open: extracting a `design-divergence` skill once a second caller exists, and measuring whether declared-axis divergence beats naive prompting.

The 2026-09-05 goldilocks assessment named the same three-part core (contract, verifier, boundary). It was never promoted to the mission. This ADR promotes it.

## Decision Drivers (force-ranked)

1. **A methodology nobody can start with compounds nothing.** Entry cost and platform parity bound every other benefit.
2. **Prove the artifact, not the report** (ADR-028). Extend it from the running app to the design and the fix.
3. **Subtract before adding.** This is Design Principle 1, and it is pstack's demonstrated practice.
4. **Accountability over volume** (ADR-010). Any move toward landing PRs needs code-enforced binding to the verified head, not prose.

## Considered Options

### Option A: Cherry-pick inside the current roadmap

Add `/why` and a PR-readiness checker as inter-phase specs. Leave the mission unchanged.

- **Pros:** Smallest change. No ADR needed.
- **Cons:** Leaves entry cost, Claude Code parity, and surface growth untouched. Continues piecemeal adoption.

### Option B: Refresh around contract, verifier, boundary, and one front door (chosen)

Run four phases: subtract first, then the front door and distribution, then code-level rigor, then verified landing, the last gated on Phase 12 evidence.

- **Pros:** Addresses Writ's weakest areas first. Makes Adaptive Ceremony a mechanism rather than a claim. Raises rigor where Writ checks least.
- **Cons:** Largest change. Adds one command. Phase 16 needs another ADR.

### Option C: Compose with pstack

Detect pstack and route design, review, and PR work to its skills.

- **Pros:** Least new Writ surface.
- **Cons:**
  - Ties Writ to a fast-moving, single-author, Cursor-first pack. pstack's panels collapse to one model in Claude Code.
  - Activates ADR-018's reserve-only trust model.
  - Writ cannot gate on prose skills it does not control.

## Decision Outcome

**Option B**, with the maintainer's two additions at contract lock:

1. Phase 13 fixes every defect both research documents found, not only the cuts.
2. The roadmap builds on `/prototype`'s exploration reframe:
   - The front door routes unsettled ideas, small changes, and empirically answerable forks to `/prototype`.
   - The `design-divergence` skill is extracted in Phase 15, when Gate 0's design sketches become its second caller.
   - The research's divergence trial decides whether the skill stays.

## Consequences

### Positive

- One documented starting point. The README's 32-command table stops being the onboarding path.
- Claude Code users receive the same root contract as Cursor users. An adapter coverage check in CI stops the class of defect that left `cursor-ide-browser` untranslated.
- The verifier reaches the design and the fix, on the routes where ADR-023 rates the stakes high.
- A planned subsystem (friction signals) is deleted before it was built, together with its no-op emit lines.

### Negative, with mitigations

- **One more command.**
  - *Mitigation:* it routes only to existing commands and owns one outcome, the routed request.
  - *Review at Phase 14 close:* if work still starts from direct commands, remove it.
- **OpenClaw loses the planned signal path.** OpenClaw keeps no transcripts, so `/retro` cannot read it.
  - *Mitigation:* OpenClaw has a mapping guide and no installer. Accepted.
- **ADR-029's Option C trigger loses its counter.**
  - *Mitigation:* the trigger now reads `/retro` findings that cite an agent failing to find or call a Writ tool, in three or more sessions.
- **Phase 16 may not start.** If Phase 12's human UAT fails, Phase 16 stays parked and the ceiling stays where ADR-013 put it.
- **Code-level rigor adds spawns and cost.**
  - *Mitigation:* it runs only on high-stakes routes (`gate3_route` names review-agent, or `--panel`). Each upgrade is kept only if a removal measurement on the Phase 11 baseline set shows it catching something the current gates passed.

## Review

- **Phase 14 close:** keep or remove the front door. The question is whether it is the place work actually starts. *Due as of 2026-10-30:* the acceptance pass (2026-10-24) found `/writ` matched its route on 10 of 20 real requests, below the bar of 16, and the Phase 15 run started from `/implement-phase` directly.
- **Phase 15 close:** keep or remove each code-level upgrade and the `design-divergence` skill, on its measurement.
  - *Removal measurement, 2026-11-04* ([trial-report.md](../specs/2026-10-25-gate-upgrade-removal-measurement/trial-report.md)). Stories (yuss): `2026-07-24-per-event-fee-revenue-model/story-2-event-creation-payment-flow`, `2026-07-24-per-event-fee-revenue-model/story-3-fee-sharing-pro-exemption`, `2026-07-24-per-event-fee-revenue-model/story-4-messaging-migration-quick-split-guard`, and `2026-07-23-quick-split-single-transaction/story-3-settlement-view-share-link`.
    - **Gate 0 Divergence:** keep. Exercised on 3 of 4 stories; 2 of its 3 upgrade-only findings were valid.
    - **Safety Fact:** keep. 4 of 4; 2 of 2 valid.
    - **Reviewer Filters:** keep. 4 of 4; 1 of 1 valid.
    - **Repro First:** unverifiable. Never exercised: all four stories are feature work, so no bug-fix path ran. The ack is `amend`, so the upgrade stays unchanged until a substitute baseline of bug-fix stories is added.
    - **Caveats:** four stories and one run per upgrade arm, so one valid catch keeps an upgrade. The Gate 0 and Repro First arms are retrospective proxies, not replays. The labels are the assistant's assessments, made at the maintainer's request (drift-log DEV-012), so the measurement rests on a model judging model-raised findings.
    - **Gate 0 and the blind trial:** the design-divergence note below records the blind trial's outcome (Business Rule 12).
  - *Repro First substitute trial, 2026-11-09* ([trial-report-repro-first.md](../specs/2026-10-25-gate-upgrade-removal-measurement/trial-report-repro-first.md)): **remove**. Repro First was removed the same day (that spec's Story 6).
    - Stories (yuss): `2026-09-20-custom-covers-not-saving/story-1-production-cover-origin-save` @ `ed15bba`, `2026-04-16-event-limit-upgrade-modal-wiring/story-1-wire-limit-error-to-upgrade-modal` @ `d0f5f1a`, and `2026-03-03-days-present-stretch-miscount/story-1-fix-counting-logic` @ `403a9cc`. `2026-05-13-event-settlement-role-invariants` @ `73f34d4` was excluded because its spec was committed after the fix (drift-log DEV-014).
    - Exercised on 3 of 3 stories. 0 upgrade-only findings, so 0 valid.
    - **Selection rule** (Business Rule 14): a story qualifies when (1) its spec passes `tdd-cycle`'s bug test, (2) a product-code `fix(...)` commit is matched to it by hand, (3) the Phase 11 rules hold (Completed, a parent commit, a unit test file with no unmocked live-service import), and (5) its story file and spec contract exist at the fix commit. Rule (4) takes the four most recent by fix date. Only three stories qualified.
    - **Caveats:** the trial leans toward remove. A catch needs a repro that still fails at the story commit, and accepted fixes rarely do, so this does not prove Repro First adds nothing. The labels were delegated to the assistant (drift-log DEV-018). There were zero findings, so no label was judged; `label` only set `labeled_by`. Three stories and one run per arm make a small sample.
  - *Divergence trial, 2026-11-04* ([trial-report.md](../specs/archive/2026-10-25-design-divergence/trial-report.md)): **remove**.
    - Declared axes won 2 of 6 briefs; keeping the skill needed 4. Distinct-structure count: 17 for the axes arm, 16 for the naive arm.
    - Render-only drafts were enough to choose a direction on 6 of 6 briefs (ui 2 of 2).
    - **Caveats:** six briefs and one rater make a small sample, not a general result. The ratings are a blind agent's, made at the maintainer's request (design-divergence drift-log DEV-012).
    - **Gate 0:** removal-measurement Business Rule 12 applies, so the skill and its Gate 0 wiring are removed together, overriding that measurement's Gate 0 keep. `/prototype` Step 2.5 now asks for up to three drafts and what each commits to.
- **Phase 16 start:** write the ceiling ADR, citing Phase 12's UAT result and one real-project `app-verify.py` run. *Written 2026-11-05 as [ADR-033](adr-033-doubt-gated-autonomy.md), ahead of Phase 16 and citing the 2026-10-31 agent UAT run; the real-project run stays Phase 16's gate, and Phase 17 now runs first.*

## Amendments

### 2026-10-30 — Land before you add

**Decision:** Add Design Principle 8 to the roadmap: no new phase starts while two or more finished phases wait on human validation or merge.

**Evidence (reconcile pass, 2026-10-30):**
- Phase 12 was released in v0.40.0 on 2026-10-02; 3 of its 89 UAT scenarios have been run since.
- Phase 14 is implemented; [PR #63](https://github.com/sellke/writ/pull/63) has been open since 2026-10-24.
- Phase 15 is implemented on a branch built on Phase 14's, with 201 UAT scenarios and two human ratings outstanding.
- Two Phase 13 PRs are open: #61 (closure docs) and #62 (the fix for the one UAT regression), whose commits are in no other branch.
- `main` is still v0.43.0.

**Why:** Built work that nobody validates is not shipped, and every new phase adds to the queue. Principle 7 (subtract before you add) keeps the surface from growing; Principle 8 keeps unvalidated work from growing.

**Consequence:** Phase 16, or any new phase, starts only once fewer than two finished phases wait. The roadmap's *Current focus* section lists the queue in order. Phase 16 keeps its own gate (Phase 12's UAT and one real-project `app-verify.py` run) on top of this rule.

### 2026-11-05 — Ceiling ADR written early; Phase 17 added

**Decision:** [ADR-033](adr-033-doubt-gated-autonomy.md) replaces the gate-class table this record kept with one rule, ask on doubt, and commits Phase 17 (Doubt-Gated Autonomy) ahead of Phase 16. Phase 16's merge step is now defined by that rule.

**Evidence (reconcile pass, 2026-11-05):** the land-and-validate queue was worked by handing the gated steps back to agents (Phase 12's UAT, the removal-trial labels, the divergence ratings), and Phase 14 merged with its five person checks unrecorded. The gates by category were delays, not decisions.

**Consequence:** § Keeps and § Review are annotated above. The front-door review stays open; the recommendation on record is keep, with its confirm step doubt-gated.

## References

- [`2026-10-19-writ-vs-pstack-research.md`](../research/2026-10-19-writ-vs-pstack-research.md): findings F1 to F9, the defect table, and options A to C
- [`2026-10-19-prototype-visual-drafts-research.md`](../research/2026-10-19-prototype-visual-drafts-research.md): F4 (constructed divergence), F6 (defects), and the build order
- [`2026-09-05-goldilocks-assessment.md`](../product/2026-09-05-goldilocks-assessment.md): §1, the three-part core
- [ADR-025](adr-025-friction-signals.md), [ADR-029](adr-029-agent-cli-contract.md): the records this ADR supersedes in part and amends
- pstack: https://github.com/cursor/plugins/tree/main/pstack (0.15.28, `d457567`)
