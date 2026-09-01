# WritUS Fork Creation Plan

> **Date:** 2026-09-01
> **Status:** Complete (planning artifact — not a product change)
> **Subject:** How to create a team-facing customization of Writ for an existing development organization, without rewriting Writ
> **Inventoried against:** Writ `VERSION` 0.33.0; pipeline and overlay behavior as shipped in `commands/`, `agents/`, `skills/`, `adapters/`, `scripts/`, and `.writ/` docs/ADRs
> **This document is:** the starting plan for building WritUS later
> **This document is not:** the fork, a spec, or a rewrite of Writ product source

## Name

**WritUS means Writ + User Stories** — and, more broadly, the human story and ceremony layer that sits on top of Writ’s contract pipeline.

That reading is the default unless repo evidence forces another one. It does not. This repository’s atomic work unit is already the user story (`user-stories/story-*.md`, generated during `/create-spec` by `agents/user-story-generator.md`, executed by `/implement-story`). There is no geographic “US” framing in product docs, ADRs, or commands. ADR-008 already names *spec-as-team-contract* as the strategic moat; WritUS is the operationalization of that moat for a real team whose stories are written, socialized, refined, and planned by humans.

If a later discovery conversation with the team reveals a different expansion (for example a proper-noun squad name), amend this paragraph. Do not silently retcon it.

---

## Why this is a plan and not a fork

Writ’s own architecture already answers the “should we rewrite?” question:

- [ADR-002](../../decision-records/adr-002-evolution-over-fork.md) rejected a hard fork of Writ on maintenance, migration, and community grounds. The same drivers apply to WritUS: every upstream improvement would otherwise be ported by hand.
- [`.writ/docs/command-overlay.md`](../../docs/command-overlay.md) already defines the mechanism teams use to specialize: **local copies always win**, `install.sh` / `update.sh` preserve diffs, `/refresh-command` amends the local copy and never touches core `commands/`.
- [ADR-007](../../decision-records/adr-007-team-audience-sequencing.md) deferred team-only affordances until a concrete signal. A named team asking for role-owned ceremonies and human meeting checkpoints *is* that signal — for *this team*, not for Writ core.
- [ADR-008](../../decision-records/adr-008-spec-as-team-contract-moat.md) is already the contract substrate WritUS needs. The gap is ceremony, assets, and RACI, not a new spec format.
- [ADR-022](../../decision-records/adr-022-autonomy-gate-classes.md) already classifies which decisions stay human: product and spec direction, the production boundary, and design/UX judgment. WritUS extends those gates from “the user of the session” to “named human roles in meetings.”

The fundamental difference the team named is also already visible in Writ’s design, just aimed at a solo operator: roles in Writ are **AI agents spawned by commands**. In WritUS, the same primitive names are played by **real humans**, with agents as assistants. Human checkpoints continue as **meetings between humans**. Command outputs that today are AI-context artifacts (`spec-lite.md`, What Was Built, UAT plans) must grow a parallel layer of **concise, human-readable documents and presentations** that follow team protocols.

---

## Current Writ inventory (grounded)

Writ 0.33.0 is a markdown methodology. There is no application runtime to fork. The distributable surface is:

| Surface | Count / location | What it is |
|---|---|---|
| Commands | 31 invocable + `_preamble.md` in `commands/` | User-invoked workflows. Run at the session model. |
| Agents | 7 in `agents/` | Spawned roles. `model_tier` enforced at spawn. |
| Skills | 16 folders under `skills/` | Reusable capabilities. Explicit `Read`, not ambient. |
| Adapters | `cursor.md`, `claude-code.md`, `codex.md`, `openclaw.md` | Platform translation of generic tool names |
| Scripts | install/update/overlay, spec graph, eval, quality gates | Mechanics Writ still owns |
| Overlay | `.cursor/commands/` (local always wins) | How a project specializes without editing core |

### Pipeline Writ actually ships

```
/plan-product
    → /create-spec  (stories written here by user-story-generator; there is no /create-story)
        → /design  (optional, mockups into the spec)
        → /assess-spec  (optional, implementability)
        → /implement-phase  (roadmap phase orchestrator)
            → /implement-spec  (story batches)
                → /implement-story  (Gate 0 arch-check → … → Gate 5 docs)
            → /create-uat-plan  (auto-called per spec by implement-phase)
        → /verify-spec
        → /ship  (branch → PR)
        → /release
```

`/implement-phase` is the documented autonomy ceiling ([ADR-010](../../decision-records/adr-010-supervised-autonomy-ceiling.md)): human on the loop at phase level, in the loop at contract level. `--recommend` on `/create-spec` and `/implement-phase` auto-locks contracts from evidence; WritUS should treat that as **opt-in exception**, not default, because humans own those locks.

### There is no `/create-story` command

This is the most important inventory mismatch with the team’s example mapping. Story files are produced **inside** `/create-spec` Step 2.6 by parallel `user-story-generator` agents. `/edit-spec` can later change them. Many roles “invoking `create-story`” is a **WritUS additive command** (an overlay), not an existing Writ primitive. The plan below treats `/create-story` as a thin new overlay that writes `user-stories/story-*.md` into an already-locked spec, reusing the existing agent contract rather than inventing a second story format.

### What each pipeline command produces today

These are the real artifacts. The WritUS asset layer wraps or summarizes them; it does not replace them.

| Command | Durable artifacts (today) | Human gate already in Writ |
|---|---|---|
| `/initialize` | `.writ/docs/tech-stack.md`, `code-style.md`, `.writ/config.md` | Agreement on stack before writing |
| `/plan-product` | `.writ/product/mission.md`, `roadmap.md`, `mission-lite.md`; 000-series ADRs under `.writ/decision-records/` | Plan Mode discovery; AskQuestion contract lock (ADR-022 class: product direction) |
| `/plan-product --reconcile` | Targeted edits to mission/roadmap; new ADRs only for genuine direction change | Same lock |
| `/research` | `.writ/research/<YYYY-MM-DD>-<topic>-research.md` | Scoped questions before deep dive |
| `/create-adr` | `.writ/decision-records/<NNNN>-<title>.md` | Alternatives analysis; high switching-cost only |
| `/create-spec` | `.writ/specs/<date>-<name>/spec.md`, `spec-lite.md` (<100 lines), `user-stories/story-*.md`, `user-stories/README.md`, `sub-specs/technical-spec.md` (+ api/db/ui as needed), optional `recommendation-log.md` | Contract lock before any file is written |
| `/design` | `mockups/*.excalidraw`, rendered PNG, `mockups/component-inventory.md` | ADR-022 design/UX judgment |
| `/edit-spec` | Updated spec package; `backups/<timestamp>/`; spec `CHANGELOG.md`; dropped stories under `user-stories/archived/` | Modification contract before files change |
| `/assess-spec` | In-session rating (Ready / Implementable with adjustments / Needs restructuring); not a committed file | Advisory; `/implement-spec` also runs a light pre-flight |
| `/implement-story` | Story status → Completed; tasks/AC checked; `## What Was Built`; `> **Commit:**` SHA; drift-log entries; `.writ/context.md` rewrite | Gate 0 ABORT and Gate 3.5 PAUSE ask the user; coverage ≥80% on new files |
| `/implement-spec` | `.writ/state/execution-*.json` (gitignored); all stories executed or skipped with reason | No execution-plan confirmation; invoking it *is* the instruction to run |
| `/implement-phase` | `.writ/state/phase-execution-*.json`; per-spec `uat-plan.md`; completion report (`COMPLETE` / `IMPLEMENTED pending human validation` / `PARTIALLY COMPLETE`) | One execution-plan confirmation; human-judgment exit criteria handed off, never self-certified |
| `/create-uat-plan` | `{spec}/uat-plan.md` — scenarios a person can run without reading code | The *plan* is generated; *execution* is already a human activity |
| `/verify-spec` | `{spec}/verification-YYYY-MM-DD.md`; `--product` writes `.writ/product/verification-YYYY-MM-DD.md` | Outstanding warnings need human judgment |
| `/review` | `.writ/state/review-<branch>.md` (ephemeral) | Ship / ship with caution / do not ship |
| `/ship` | Open PR with Summary, Changes, Spec Reference, Test Results; git-notes audit digest | Production boundary (ADR-022): opening/merging is a human gate in spirit; `/ship` currently opens the PR as last-mile automation — WritUS must decide who may invoke it |
| `/release` | `VERSION`, `CHANGELOG.md`, annotated tag, optional GitHub release; post-merge archival hook | Production boundary |
| `/create-issue` | `.writ/issues/{bugs,features,improvements}/<date>-<slug>.md` | Fast-capture, not a meeting |
| `/knowledge` | `.writ/knowledge/{decisions,conventions,glossary,lessons}/*.md` | Small facts; not ADRs |
| `/retro` | `.writ/retros/YYYY-MM-DD.json`, `trends.json`, human-readable report | Team-aware even in solo Writ |
| `/security-audit` | `.writ/security/audit-YYYY-MM-DD.md` | Compliance-adjacent |
| `/status` | Session report; rewrites `.writ/context.md`; `--archive` moves Complete specs | Orientation, not a ceremony |
| `/prototype` | Working-tree code, **no** spec artifacts | Escalates to `/create-spec --from-prototype` when scope grows |

Agents spawned inside `/implement-story` (architecture-check, coding, review, testing, visual-qa, documentation) remain AI roles. In WritUS they assist the human who owns the corresponding ceremony; they do not replace the meeting.

---

## 1. Fork strategy

### Recommendation: overlay product, not a hard fork

**Primary recommendation:** treat WritUS as a **named overlay** that consumes Writ as upstream. Specialize through (a) local command copies, (b) new overlay-only commands and skills, (c) a configuration and protocol pack the commands read. Do not copy `commands/`, `agents/`, `adapters/`, or `scripts/` into a second repository and start editing them.

This is Option A below. It is chosen over a git fork of this repo and over a new methodology that merely “uses Writ specs.”

### What stays shared (Writ upstream)

Keep identical to Writ, updated with `update.sh`:

- All core commands, agents, skills, adapters, scripts, `system-instructions.md`, eval harness
- Spec format, story format, What Was Built, UAT plan schema, ADR format, knowledge ledger, spec lifecycle/archival
- Overlay resolution rules (local always wins)
- Autonomy gate *classes* (ADR-022) — WritUS adds *who* sits in the class, not a new class taxonomy

### What WritUS specializes (overlay)

Live in the consuming team’s project (or a small `writus` overlay pack), never in Writ core:

| Layer | Location (proposed) | Contents |
|---|---|---|
| Org working agreements | `.writ/writus/org/working-agreements.md` | Org-wide ceremony rules, Definition of Ready/Done, meeting SLAs |
| Compliance pack | `.writ/writus/org/compliance.md` | Required stamps, retention, who can approve what |
| Asset protocols | `.writ/writus/org/protocols/` | Templates, length caps, audience, stamp fields |
| Role RACI | `.writ/writus/org/raci.md` | Owner vs invoker vs consulted vs informed per command |
| Squad overlays | `.writ/writus/squads/<slug>/` | Squad working agreements that *narrow* org rules, never silently contradict them |
| Command overlays | platform local dir, e.g. `.cursor/commands/` | Only the commands that must pause for a named meeting or emit a protocol asset |
| Additive commands | same local dir | `/create-story` and any meeting-brief emitters that have no Writ counterpart |
| Additive skills | platform local skills dir | How to author a protocol-compliant brief, slide outline, handoff packet — capability, not workflow |

### How working agreements inject without rewriting the core methodology

Do **not** splice team prose into upstream `commands/*.md`. Injection order:

1. **Read, don’t fork.** Overlay copies of `/create-spec`, `/implement-story`, `/implement-phase`, `/ship`, `/release` (and only those that must change control flow) add a short **WritUS checkpoint step**: “before lock / before coding / before PR, load `.writ/writus/` and pause if the required meeting artifact is missing.”
2. **Skills own the how.** A skill such as `meeting-brief-authoring` or `asset-protocol-stamp` describes length, audience, and stamp fields. Commands name *when* to load it. This matches [ADR-009](../../decision-records/adr-009-command-agent-skill-boundary.md): workflow → command, capability → skill.
3. **Knowledge owns the facts.** Squad conventions that are not ceremony (naming, environments, analytics taxonomies) go in `.writ/knowledge/conventions/` via `/knowledge`, which already exists.
4. **ADRs own irreversible org bets.** “We will not use `--recommend` in production squads” is an ADR in the team repo, not a patch to Writ.
5. **`/refresh-command` stays the learning loop** for overlay copies. Promotions back into Writ core happen only when a checkpoint is generally useful to solo users — which most meeting pauses will not be.

`system-instructions.md` and `writ.mdc` are **not** overlay-safe ([command-overlay.md](../../docs/command-overlay.md) states they are always updated from core). Do not put WritUS identity there. Put it in `.writ/writus/` and in overlay command preambles.

### Options considered

| Option | Approach | Verdict |
|---|---|---|
| **A. Overlay on Writ upstream** | Team repo installs Writ; overlay pack + local command copies; pin Writ version | **Chosen.** Matches ADR-002, existing overlay, and “do not rewrite Writ.” |
| **B. Git fork of sellke/writ** | Duplicate product source; rename; edit commands in place | Rejected as the *default*. Maintenance cost is the failure mode ADR-002 already named. A fork remains a last resort if overlay resolution cannot express meeting pauses. |
| **C. Separate product that consumes `.writ/specs/`** | New command vocabulary, Writ specs as an API | Rejected. Spec format would become a cross-product contract (the Option 3 ADR-002 already rejected). |
| **D. Rewrite Writ core to be multi-role** | Change `commands/` so every team gets RACI | Explicit non-goal. Violates ADR-007 (don’t ship team-only features into solo Writ) and this task’s constraint. |

### Versioning and update posture

- Pin the overlay pack to a **Writ VERSION** (today: 0.33.0) and re-test overlay diffs on each `update.sh`.
- Expect skipped files: every overlayed command will show as “local modifications preserved.” Budget a periodic `/refresh-command` pass to replay upstream intent onto the overlay.
- Additive overlay commands (`/create-story`) have no upstream counterpart, so updates will *copy nothing* for them — they are owned entirely by WritUS.
- Do not run `install.sh` against the Writ repo itself (dogfooding uses symlinks). WritUS is installed into the *team’s* application repos.

---

## 2. Role → primitive mapping

Legend for the tables: **O** = typically owns (accountable for lock/approval), **I** = may invoke, **C** = consulted in the associated meeting, **F** = informed via the asset. Squad vs org: **Squad** means the owning product leader’s squad; **Org** means the shared pack or a cross-squad forum.

### Commands — delivery pipeline

| Writ primitive | Typical owner (O) | May invoke (I) | Consulted (C) | Scope |
|---|---|---|---|---|
| `/plan-product` | Product (org-level mission; squad product leader for squad roadmap slices) | Product | Stakeholders, BA, Data, Support, Ops | Org mission/roadmap; squads may propose phase items but do not lock org mission |
| `/create-spec` | Product (squad product leader) | Product; BA may co-run discovery | Dev, QA, UX, Data, Ops (feasibility), Stakeholders (check-in) | Squad, against org mission |
| `/create-story` **(WritUS additive)** | BA typically; Product when BA is not on the work | **BA, Product, Dev, QA, UX, Data, Support** (user’s “many roles may invoke”) | The roles who will refine and plan the story | Squad. Writes into an existing spec. Does not replace `/create-spec`. |
| `/edit-spec` | Product | Product, BA | Dev, QA, UX | Squad |
| `/design` | UX | UX, Product | Product, Dev, QA, Stakeholders (when customer-facing) | Squad |
| `/assess-spec` | Product + Dev | Product, Dev, BA | Data, Ops, UX | Squad (feeds feasibility conversations) |
| `/research` | whoever owns the decision the research informs | any role | — | Org or squad |
| `/create-adr` | Dev (technical) or Product (product ADRs) | Dev, Product | affected roles | Org if the decision crosses squads |
| `/implement-phase` | Product (phase call) with Dev executing | Product, Dev | QA (UAT handoff) | Squad or org phase |
| `/implement-spec` | Dev | Dev | QA, UX (UI specs) | Squad |
| `/implement-story` | Dev | Dev | QA (handoff), UX (visual QA) | Squad |
| `/prototype` | Dev | Dev | Product (escalation to spec) | Squad; still the escape hatch for work that must not get a spec |
| `/create-uat-plan` | QA | QA, Dev, Product | Support (scenario realism) | Squad |
| `/review` | Dev (pre-landing) and QA (failure-mode pass) | Dev, QA | — | Squad |
| `/verify-spec` | BA/Product (contract hygiene) | BA, Product, Dev | — | Squad; `--product` is org Product |
| `/ship` | Dev, with Product approval to open | Dev | QA (tests/UAT status) | Squad. WritUS should require the human checkpoint artifact before a ready-for-review PR. |
| `/release` | Product + Ops | Product | Support, Stakeholders, “product marketing” collaboration | Org cadence, even when the work is one squad’s |
| `/create-issue` | any | **all roles** | — | Squad or org triage |
| `/knowledge` | any | **all roles** | — | Prefer org ledger for cross-squad facts |
| `/status` | any | **all roles** | — | Session orientation |
| `/retro` | Product (squad) / org facilitator | Product, Dev, QA | whole squad | Squad; org retro is a separate cadence |
| `/security-audit` | Dev + Ops | Dev, Ops | Product (risk acceptance) | Org compliance pack may *require* this before `/release` |
| `/initialize` | Dev / Ops | Dev | — | Once per repo |

Meta commands (`/refresh-command`, `/new-command`, `/new-skill`, `/update-writ`, `/migrate`, uninstall/reinstall) stay with whoever maintains the WritUS overlay — not a squad ceremony.

### Agents — AI assistants to human roles, not replacements

| Agent | Writ job | Human counterpart in WritUS | Notes |
|---|---|---|---|
| `user-story-generator` | Parallel-write story files during `/create-spec` | BA (and any `/create-story` invoker) | Agent drafts; human socializes and refines |
| `architecture-check-agent` | Gate 0 PROCEED/CAUTION/ABORT | Dev (+ Product on ABORT) | ABORT already pauses for a human; WritUS routes that pause into a **feasibility conversation** |
| `coding-agent` | Gate 1 TDD | Dev | Unchanged: the human Dev owns the story in flight |
| `review-agent` | Gate 3 PASS/FAIL | Dev peer + QA | Does not replace `/review` or a human design review |
| `testing-agent` | Gate 4 coverage ≥80% | QA | Machine gate; QA still runs UAT |
| `visual-qa-agent` | Gate 4.5 optional | UX | Taste remains a human gate (ADR-022) |
| `documentation-agent` | Gate 5 | Dev, Support (for runbooks) | Support/ops training packets are a *WritUS asset*, not this agent’s current output |

### Skills — likely alignment (existing + overlay)

Existing skills stay capabilities, not roles. Likely wielders:

| Skill | Likely human wielder / consumer |
|---|---|
| `error-rescue-mapping` | BA, QA (AC and failure tables in specs) |
| `story-context-assembly`, `dependency-context-loading` | Dev (via `/implement-story`) |
| `tdd-cycle`, `safe-refactor-loop`, `conventional-commits` | Dev |
| `what-was-built-authoring`, `story-commit-provenance` | Dev; QA reads WWB at handoff |
| `change-surface-classification`, `boundary-map-computation` | Dev |
| `drift-triage` | Product, BA, Dev (Gate 3.5) |
| `code-explanation` | Dev, Support (training) |
| `project-context-snapshot` | any, via `/status` |

WritUS-only skills to author later (not in this effort): protocol stamping, meeting-brief authoring, working-agreement lookup, compliance-stamp verification. Boundary lint (`scripts/lint-skill.sh`) still applies: they must be verb-phrase capabilities, not sneaky commands.

### Ownership rules the overlay must enforce

1. **Product owns `/plan-product` and `/create-spec` locks.** Others may sit in discovery; they do not lock the contract. This is the user’s mapping and ADR-022.
2. **Story writing is BA-typical, not BA-exclusive.** `/create-story` is multi-role-invokable. The spec’s `Owner:` field ([spec-format.md](../../docs/spec-format.md)) stays a coordination signal, not an ACL. WritUS may add `Story author:` and `Squad:` as overlay header fields without changing Writ’s detector.
3. **Dev owns implementation commands.** QA does not invoke `/implement-story` as the accountable role; they invoke `/create-uat-plan` and `/review`.
4. **UX owns `/design`.** Product may invoke it; UX approves visual references before Gate 1 uses them.
5. **Support, Operations, Data, Stakeholders** are primarily **C/F** on delivery commands and **I** on capture commands (`/create-issue`, `/knowledge`, `/create-story` when they hold the domain fact). They become **O** on their own training and check-in assets.

---

## 3. Human checkpoint model

Writ already pauses for humans at contract lock, design taste, Gate 0 ABORT, Gate 3.5 PAUSE, phase execution confirmation, and production boundary. WritUS’s change is: **those pauses become named meetings with named roles**, and several additional meetings consume command *assets* without being command *gates*.

Two kinds of checkpoint:

| Kind | Behavior | “Done” means |
|---|---|---|
| **Blocking pause** | Overlayed command will not proceed to its mutating phase until the meeting artifact exists and carries the required stamps | Meeting held (or explicitly waived under the compliance pack); decision recorded; named approver stamped; protocol length/audience satisfied |
| **Asset for a meeting** | Command runs to completion and emits a brief/deck/packet the humans use in a ceremony that Writ does not schedule | The asset is filed; the meeting’s minutes/decision are written back (`/knowledge`, spec CHANGELOG, ADR, or overlay meeting log) |

`--recommend` auto-adopts locks that WritUS needs humans to keep. Default WritUS posture: **do not use `--recommend` on production specs.** If a squad later wants it, that is an ADR plus a compliance exception, not a silent default.

### Required human connection points → command/asset pairing

These nine meetings **must** appear in the workflow. Mapping is to *actual* Writ commands, not invented ones.

| Human connection point | Kind | Commands that pause or feed it | Asset the humans walk into the room with | RACI (O / C) | “Done” |
|---|---|---|---|---|---|
| **Stakeholder check-ins** | Asset for a meeting (cadence); blocking before org `/plan-product` lock and before `/release` | `/plan-product`, `/status`, `/verify-spec --product`, `/retro` | Mission/roadmap briefing; status one-pager; product verification report | Product O; Stakeholders C; BA, Support, Ops I | Stakeholders have seen current phase claims vs shipped evidence; direction changes recorded as ADRs |
| **Feasibility conversations** | Blocking before `/implement-spec` on anything `/assess-spec` rates below Ready, and on Gate 0 ABORT | `/assess-spec`, `/research`, `/create-adr`, Gate 0 `architecture-check-agent` | Assessment rating + decomposition; research note; draft ADR | Product + Dev O; Data, Ops, UX, QA C | Feasible path chosen or spec edited/closed (`Closed — Not Implemented` is a legitimate outcome) |
| **Design reviews** | Blocking before UI stories enter `/implement-story` Gate 1 | `/design`, later Gate 4.5 `visual-qa-agent` | Wireframes + `component-inventory.md`; comparison captures | UX O; Product, Dev C; Stakeholders C when customer-visible | UX stamp on mockups; visual references linked from stories |
| **Story socializations** | Asset for a meeting after stories exist; blocking for stories marked High or crossing squads | `/create-spec` Step 2.6 / WritUS `/create-story` | Story one-pagers (protocol: AC + intent, not task lists) | BA O (or the invoker); Product, Dev, QA, UX C | Squad can explain the story in one minute; open questions listed |
| **Story refinement** | Blocking before story planning if AC/tasks fail Definition of Ready | `/edit-spec`, `/verify-spec` | Spec CHANGELOG; updated story file; verification warnings | BA + Product O; Dev, QA, UX C | Modification contract locked; backups exist; AC IDs stable ([acceptance-criteria-ids.md](../../docs/acceptance-criteria-ids.md)) |
| **Story planning** | Asset for a meeting (sprint/iteration planning). `/implement-spec` today has **no** confirmation gate — WritUS overlay **adds** one at squad planning, or requires the planning minutes as a required artifact before invoke | `/assess-spec` pre-flight, story README, `/implement-spec` (overlay) | Planning board: batches from `scripts/story-deps.py`, sizing flags | Product O; Dev, QA C; Data C when the story is analytic | Batch plan accepted; WIP limits honored; unready stories stay out |
| **Dev to QA handoff** | Blocking before QA accepts the story/spec for UAT | `/implement-story` completion, `/create-uat-plan`, `/review` | WWB record; `uat-plan.md`; review recommendation | Dev O for handoff packet; QA O for acceptance | QA stamps “accepted for UAT” or returns with defects; coverage/review gates already green |
| **Support and ops training** | Asset for a meeting after merge/release, blocking for releases the compliance pack marks customer-impacting | `/ship`, `/release`, `/knowledge`, documentation-agent output | Training brief from WWB + UAT + runbook delta | Support + Ops O for the session; Product, Dev C | Training held or waived; knowledge entries filed; rollback path named |
| **Product marketing collaboration** | Asset for a meeting around `/plan-product` (positioning) and `/release` (what shipped) | `/plan-product`, `/release` changelog, `/retro` | Release narrative (from CHANGELOG + completed stories); audience-safe one-pager | Product O; Stakeholders (marketing) C; Support C (customer language) | Messaging agrees with what actually shipped (`/verify-spec --product` Check P4 is the honesty check) |

### `/implement-phase` already hands UAT to humans

The phase completion report ends in `IMPLEMENTED pending human validation` when machine criteria pass and human-judgment criteria remain. WritUS should keep that sentence and attach it to **Dev to QA handoff** plus stakeholder UAT, not invent a second phase orchestrator.

### What “done” is not

- An agent verdict (Gate 3 PASS, testing-agent coverage) is **necessary and not sufficient** at human checkpoints.
- A generated `uat-plan.md` is not UAT. `/create-uat-plan`’s own design principle: the plan is generated after implementation so a *person* can validate behavior without reading code.
- Silence is not lock. ADR-013 forbids inferring contract lock from silence; WritUS meetings must record an explicit stamp.

---

## 4. Asset / protocol layer

Writ artifacts are optimized for **agents and git**. WritUS adds a parallel layer optimized for **humans in rooms**. The two layers point at each other; they do not duplicate the spec.

### Principle

| Layer | Audience | Length | Source of truth? |
|---|---|---|---|
| Writ contract artifacts | Agents + future-self + PR review | `spec.md` unbounded; `spec-lite.md` <100 lines | **Yes** — always |
| WritUS protocol assets | A named meeting, a named role | Protocol caps (below) | **No** — derived. If they disagree with the spec, the spec wins and the asset is regenerated |

Regenerate assets from contracts (`/create-uat-plan` already works this way for UAT). Do not let slide decks become a second spec.

### Proposed protocol set (to be confirmed with the team)

Lengths are starting constraints so the layer stays readable. The discovery phase must replace them with the team’s real templates.

| Asset | Produced after | Audience | Length / form | Compliance stamps |
|---|---|---|---|---|
| Stakeholder briefing | `/plan-product`, `/status`, `--product` verify | Stakeholders | ≤2 pages or ≤8 slides | Product owner, date, phase, “claims vs shipped” |
| Feasibility note | `/assess-spec` + research | Product, Dev, Ops | ≤1 page: rating, risks, recommendation | Assessor, Product, Dev |
| Design review pack | `/design` | UX, Product, Dev | Wireframe set + inventory table; no essay | UX approver |
| Story one-pager | `/create-story` or `/create-spec` stories | Squad socialization | ≤1 page: persona, intent, 3–5 AC, open questions — **not** the 7 implementation tasks | Author role, spec owner |
| Refinement delta | `/edit-spec` | Squad | CHANGELOG excerpt + what changed in AC | Product |
| Planning board | story graph + assess flags | Sprint planning | Batch list from `story-deps.py`; WIP; unready list | Product |
| Dev→QA handoff packet | story Complete + UAT plan + `/review` | QA | WWB summary, how to run UAT, known drift, review recommendation | Dev, QA accept/reject |
| UAT execution record | humans running `uat-plan.md` | QA, Product, Stakeholders | Pass/fail per scenario; evidence links | QA |
| Support/ops training brief | `/ship` / `/release` | Support, Ops | What changed, how to see it, how to roll back, who to call | Ops, Support |
| Release / marketing narrative | `/release` changelog | Product marketing, Stakeholders | What shipped in customer language; explicit non-claims | Product; must cite completed specs |

### Stamps

Minimum fields on every protocol asset:

- `squad:` one of the three slugs
- `protocol:` id (filename in `.writ/writus/org/protocols/`)
- `meeting:` one of the nine connection points, or `none`
- `approver:` role + name
- `writ_source:` path to the contract artifact
- `compliance:` list of org rules satisfied, or `n/a`

Store assets under `.writ/writus/assets/<squad>/<date>-<protocol>.md` (markdown canonical, same as ADR-005). Slide exports are optional derivatives, not the record.

### What not to protocol

Do not wrap `spec-lite.md`, context hints, or agent prompt routing. Those exist to keep tokens down ([`.writ/docs/model-tiers.md`](../../docs/model-tiers.md), context-hint format). Humans should not be asked to “approve spec-lite.”

---

## 5. Squad topology

Three squads, each led by one of three product people. Shared org functions (Support, Operations, Stakeholders, often Data and UX) sit across squads unless discovery says otherwise.

```
Organization
├── Org Product contract     — /plan-product mission + roadmap; compliance pack; asset protocols
├── Squad A  — Product leader A   — specs, stories, planning, build, QA handoff
├── Squad B  — Product leader B   — same primitives, squad working agreements
├── Squad C  — Product leader C   — same primitives, squad working agreements
└── Shared   — Support, Ops, Stakeholders; Data/UX as org or embedded (open question)
```

### Org-wide (one copy)

- `.writ/product/mission.md` and the org roadmap (phases that span squads)
- Compliance pack and asset protocols
- Knowledge ledger conventions that apply to every squad
- `/release` cadence, `/security-audit` bar, production boundary
- Stakeholder check-in and product-marketing templates
- Writ VERSION pin and overlay pack version

### Squad-local

- Specs under `.writ/specs/` with overlay header `Squad:` (or a per-squad specs dir — default to **one repo, one `.writ/specs/`**, distinguished by metadata, unless the team already has three codebases)
- Working agreements that add ceremony (e.g. Squad B requires Data at every feasibility conversation)
- Sprint planning, story socialization, refinement, Dev→QA handoff
- `/implement-phase` for that squad’s slice of the roadmap

### Cross-squad rules

- A spec that touches another squad’s files is an org concern: `/create-spec` overlap check already exists; WritUS should route that to a feasibility conversation with both product leaders.
- `Owner:` remains the spec creator; WritUS `Squad:` says who plans and builds it.
- Do not triplicate overlay command files per squad. Squad differences belong in `.writ/writus/squads/<slug>/`, read at checkpoint time.

If the team actually has three repositories, install Writ + the same overlay pack in each; org protocols still live in one place (a shared docs repo or a git submodule). That choice is an open question, not a decision in this plan.

---

## 6. Phased creation workflow

This is the workflow for **building WritUS**, not the development workflow WritUS will run (that is the diagram).

Do not start by copying `commands/`. Start by capturing how this team already meets.

### Phase 0 — Frame (this document)

- [x] Inventory Writ primitives and artifacts (this plan)
- [x] Record overlay-not-fork as the default strategy
- [x] Draw the target workflow (commands × assets × meetings × roles)
- [ ] Socialize this plan with the three product leaders before Phase 1 interviews freeze the wrong vocabulary

### Phase 1 — Discovery with the real team

Timebox: a series of interviews and one observed week of existing ceremonies, not a greenfield `/plan-product` for WritUS itself.

For each role (BA, Product ×3, Dev, QA, UX, Data, Support, Ops, Stakeholders):

1. Which meetings do you already attend? Map them onto the nine required connection points. Rename if the team’s names differ; do not drop a connection point.
2. Which documents do you actually read before those meetings? Length, tool (Confluence, slides, tickets), compliance stamps that already exist.
3. Which Writ-like work do you already do (story writing, spec review, UAT) and in what system (Jira, Azure DevOps, Figma, etc.)?
4. What must never be automated or auto-locked?

Outputs: a discovery note under `.writ/research/writus/` (team-confidential redaction as needed) and a gap table: existing ceremony vs Writ pause vs missing overlay.

**Halt condition:** if the team’s unit of work is not a user story, revisit the name and the `/create-story` proposal before writing overlays.

### Phase 2 — Capture working agreements and compliance

1. Org Definition of Ready / Done, meeting SLAs, who can stamp what.
2. Compliance rules that constrain assets (audit retention, customer-communication review, change-management IDs).
3. Squad deltas. Record contradictions as decisions, not as three silent variants.
4. Write `.writ/writus/org/` markdown. No command overlays yet.

Exit: three product leaders agree the org pack is accurate enough to pilot.

### Phase 3 — Map primitives (confirm tables in §2)

Walk the inventory with the team. For each command: keep / overlay-pause / hide / wrap in an asset. Explicitly decide:

- Is `/create-story` the right additive command, or do they want stories only inside `/create-spec` plus Jira?
- May Dev invoke `/create-spec`, or is that a hard Product-only lock?
- Who is allowed to run `/ship` and `/release`?
- Is `--recommend` forbidden, gated, or unused?

Exit: a signed RACI (still markdown) and a list of **overlay command names** — expected to be small: `/create-spec`, `/create-story` (new), `/design`, `/implement-spec` or `/implement-phase`, `/ship`, `/release`, plus asset emitters if those are separate commands.

### Phase 4 — Design asset protocols

For each of the ten protocol assets in §4, produce one worked example from a **past** shipped feature (so nobody is inventing fiction). Confirm length caps against real attention. Drop any asset the team will not read.

Exit: `protocols/*.md` templates with stamp fields; examples in `assets/_examples/`.

### Phase 5 — Pilot one squad

Pick one product-led squad. Install Writ into that squad’s repo if it is not already there. Install the overlay pack:

1. Copy only the overlayed commands into the platform local dir.
2. Add `/create-story` if Phase 3 confirmed it.
3. Add WritUS skills for briefing/stamping.
4. Leave all other commands as vanilla Writ (update.sh will keep them current).

Run **one real spec** through: Product `/create-spec` → BA/others `/create-story` as needed → socialization → refinement → design review if UI → feasibility if flagged → planning → `/implement-story` with Dev/QA handoff → UAT → `/ship` → support/ops brief. Stakeholders attend the check-ins they already attend; do not invent extra ones for the pilot.

Measure: extra minutes per ceremony, assets actually opened, overlay conflicts with `update.sh`, any command the squad still wanted to rewrite.

**Do not** roll the other two squads during the pilot. **Do not** promote overlay diffs into Writ core.

### Phase 6 — Adjust, then roll out

1. Fix protocols and RACI from pilot evidence.
2. Install the same pack on squads B and C (same org pack, their squad files).
3. Train Support/Ops on the training-brief protocol once, not per squad.
4. Set a Writ upgrade cadence (e.g. after each Writ minor release, replay overlays).
5. Only then consider whether any overlay pause is generally useful to upstream Writ — almost always the answer is no (ADR-007).

### What each phase produces (WritUS-the-product, later)

| Phase | Artifacts in the *team* repo |
|---|---|
| 1 | Discovery notes |
| 2 | `.writ/writus/org/*` |
| 3 | `raci.md`, overlay command list |
| 4 | `protocols/`, examples |
| 5 | Local `.cursor/commands/` (or platform equivalent), first `/create-story`, pilot spec |
| 6 | Squad folders for B and C; upgrade runbook |

None of those artifacts are created by *this* planning effort except the plan and diagram in `.writ/research/writus/`.

---

## 7. Risks and open questions

### Risks

| Risk | Why it is real | Mitigation |
|---|---|---|
| Hard fork drift | ADR-002’s exact failure mode | Overlay + VERSION pin; overlay only commands that must pause |
| Overlay vs stale-core | `update.sh` cannot tell “we customized this” from “this is an old copy” ([command-overlay.md](../../docs/command-overlay.md)) | After each Writ upgrade, diff overlay vs new core and replay the checkpoint steps |
| Second source of truth | Slide decks that diverge from `spec.md` | Assets are derived; spec wins; regenerate; stamp `writ_source` |
| `--recommend` bypasses humans | Auto-lock is designed to skip Phase 1 gates | Default off in WritUS; compliance exception if ever enabled |
| `/ship` opens PRs without a meeting | Last-mile command is non-interactive by default | Overlay requires handoff + planning stamps before ready-for-review; draft PR is allowed |
| Ceremony bloat | Nine meetings on every tiny change | Stakes-proportional diligence ([ADR-023](../../decision-records/adr-023-stakes-proportional-diligence.md)): `/prototype` remains the no-spec path; waivers in the compliance pack for Low stories |
| Role/agent confusion | Humans ignore meetings because “the review agent passed” | Checkpoint “done” definition: agent verdict ≠ meeting stamp |
| Three-squad contradiction | Squad agreements silently override org compliance | Squad files may only narrow; contradictions require an org ADR |
| Ticket-system dual running | Team lives in Jira; WritUS lives in markdown | Phase 1 must decide system of record for stories. Writ stories are git-reviewable contracts; tickets may remain the board. Dual-write is a skill-sized problem, not a command rewrite |

### Open questions (must be learned from the real team)

These are not decided in this plan. Implementing overlays before answering them will guess wrong.

1. **Where does work already live?** Jira / Azure DevOps / Linear / GitHub Issues / nowhere. That decides whether `/create-story` writes only markdown or also a ticket.
2. **One repo or three?** Spec metadata vs separate `.writ/` trees.
3. **Are UX, Data, Support, Ops embedded per squad or org pools?** Changes RACI columns, not the command set.
4. **What is the existing Definition of Ready/Done and change-management ID format?**
5. **Who currently runs sprint planning — Product, a scrum master (not in the role list), or BA?**
6. **Is “product marketing” a person, a team, or Product wearing another hat?**
7. **Regulatory/compliance regime** (if any): SOX, SOC2, HIPAA, internal audit. Determines whether `/security-audit` is a release gate.
8. **Can a BA lock a spec today, or only Product?** User said `/create-spec` is typically a product leader — confirm whether that is exclusive.
9. **UI density.** How much of the backlog is UX-bearing? Controls how often design review is blocking vs waived.
10. **Platform.** Cursor vs Claude Code vs both. Overlay paths differ (`.cursor/commands/` vs `.claude/commands/`); the overlay *principle* does not.

---

## 8. Explicit non-goals

This effort — and the later fork it plans — will not:

1. **Rewrite Writ product source** (`commands/`, `agents/`, `adapters/`, `scripts/`, `system-instructions.md`, root `SKILL.md`, or this repo’s `.cursor/` symlinks).
2. **Run `install.sh` on the Writ repo.**
3. **Treat this plan as the overlay.** No `.writ/writus/` org pack is shipped here; that is Phase 2 of the *creation* workflow, after talking to the team.
4. **Invent a parallel pipeline** with new stage names that do not map to `/plan-product` → `/create-spec` → `/implement-*` → `/create-uat-plan` → `/verify-spec` → `/ship` → `/release`.
5. **Replace human meetings with agent gates.** Agents assist; checkpoints stay meetings.
6. **Replace Writ contract artifacts with slides.** Protocol assets are derivatives.
7. **Promote team-only pauses into upstream Writ** unless ADR-007’s trigger is being answered *for all Writ users* (it is not).
8. **Decide the team’s working agreements in the abstract.** Length caps and RACI in this plan are hypotheses for Phase 1–4 to confirm.
9. **Build `/create-story` in this PR.** It is specified as a future overlay command because it does not exist in Writ 0.33.0.
10. **Reopen ADR-002 for Writ itself.** Evolution-over-fork remains Writ’s decision. WritUS is a *consumer overlay*, which is how a team customizes without forking the methodology core.

---

## Primary recommendation

**Create WritUS as a version-pinned overlay pack on Writ 0.33.0+**, injecting human meeting pauses and protocol assets through local command copies and new skills, adding `/create-story` as the multi-role story-writing verb the team already assumes exists, and piloting one of three product-led squads before any org-wide rollout.

Alternatives considered and rejected as the default: a git fork of `sellke/writ` (maintenance), a new executor that consumes specs (split brain), and rewriting Writ core for multi-role teams (violates ADR-007 and this task).

The diagram beside this plan is the target operating picture those overlay steps should eventually make true — not a picture of software that exists today.
