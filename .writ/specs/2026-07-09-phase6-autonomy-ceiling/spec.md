# Phase 6: Autonomy Ceiling

> **Status:** Implemented — pending real-use User Challenge observation
> **Created:** 2026-07-09
> **Owner:** @AdamSellke
> **Phase:** 6 — Autonomy Ceiling
> **Dependencies:** [2026-07-10-recommended-autonomous-delivery]
> **Source:** `.writ/product/roadmap.md` Phase 6
> **Governing ADRs:** `adr-010-supervised-autonomy-ceiling.md` (historical), `adr-012-ralph-deprecation.md`, `adr-013-recommended-autonomous-delivery.md` (superseding)

---

## Specification Contract

**Deliverable:** Harden normal multi-spec `/implement-phase` execution using fresh isolated execution per spec, deterministic dependency sequencing, failure quarantine, evidence-bound phase learning, and fast health reporting—then fully deprecate Ralph.

**Origin:** Phase 6 — Autonomy Ceiling in `.writ/product/roadmap.md`, governed by ADR-010 and ADR-012 as reconciled by ADR-013.

**Must Include:** Every spec begins in an isolated branch/worktree and fresh subagent context. Successful work merges into the phase branch; unrecoverable partial work remains on `writ/quarantine/{spec}` without polluting the phase branch.

**Hardest Constraint:** Preserve one-session, one-confirmation normal multi-spec execution across Cursor, Claude Code, and Codex while keeping orchestration state resumable and git isolation behavior consistent. Single-spec `--recommend` delivery is a prerequisite but remains outside this phase command.

### Experience Design

- **Entry point:** `/implement-phase [phase]` resolves roadmap features to specs and presents one execution plan.
- **Happy path:** Validate explicit dependencies → confirm once → execute each spec in a fresh isolated lane → merge successful lanes → generate UAT → continue.
- **Moment of truth:** A multi-spec phase completes without context degradation, while the phase branch contains only successful work.
- **Feedback model:** `phase-execution-*.json` records transitions; `/status` shows phase progress and a categorical `Healthy / Warning / Attention` line with evidence freshness.
- **Error experience:** One transient retry is allowed. An unrecoverable spec failure preserves its branch as quarantine, blocks declared dependents, allows independent specs to continue, and reports recovery commands.
- **Scope-degradation decisions:** Use the four-part User Challenge format when a choice would weaken roadmap scope, the locked spec contract, or exit criteria; apply the evidence-based select-or-pause policy from ADR-013.

### Business Rules

1. Normal `/implement-phase` remains session-bound with one routine confirmation gate; multi-spec `/implement-phase --recommend` is unsupported.
2. Opaque, unbounded unattended loops remain an explicit non-goal.
3. `dependencies:` is an optional ordered array of exact spec-folder IDs.
4. Explicit dependencies are binding. Shared-file and prose overlap inference may warn but cannot silently reorder work.
5. `/verify-spec` extends its existing dependency check to validate missing references, self-reference, and cross-spec cycles; story and spec dependency graphs remain distinct.
6. Fresh subagents receive artifact-derived context and return structured results; the orchestrator retains only sequencing, state, escalation, and merge responsibility.
7. Quarantine occurs after the existing bounded retry policy is exhausted, not for recoverable failures.
8. Phase-close knowledge writeback creates only deduplicated, evidence-backed durable lessons or recurring drift patterns. No qualifying lesson means no write.
9. `/status` never runs mutating or heavyweight checks. It summarizes the newest available eval, verification, and drift artifacts and labels missing or stale evidence.
10. Ralph command, script, prompt templates, catalog entries, config, adapter guidance, README references, and status allowlist entries are removed from active surfaces and preserved under `archive/ralph/`.
11. No Ralph compatibility reader, in-flight-state detector, or automatic state migration is required.
12. Release and upgrade guidance must tell users with in-flight `ralph-*.json` state to finish or abandon those runs before upgrading; this repository currently has no such state.

### Success Criteria

1. A disposable sandbox phase with at least three specs runs end-to-end through fresh per-spec contexts.
2. A deliberately failed sandbox spec is retained on `writ/quarantine/{spec}`; its declared dependents remain blocked; independent specs continue; the phase branch remains clean.
3. Explicit spec dependencies produce deterministic order, and invalid, missing, self-referential, and cyclic declarations are diagnosed.
4. A scope-degrading sandbox decision renders the exact User Challenge structure and proves evidence-based selection for reversible choices or a human pause for critical ambiguity.
5. A real-use User Challenge observation remains explicitly pending until it occurs; sandbox behavior alone cannot satisfy that roadmap criterion.
6. Phase closure writes a knowledge entry only when evidence meets the durability and deduplication rules.
7. `/status` reports phase execution plus categorical health within its existing 10-second target without running `/verify-spec`.
8. Ralph is absent from active command discovery, generated catalogs, docs, adapters, config, README, and status suggestions; archived materials and changelog explain the replacement.
9. Existing eval checks and install/update dry runs remain clean.

### Scope Boundaries

**Included:**
- Command and agent contracts for supervised phase orchestration
- Adapter mappings for Cursor, Claude Code, and Codex
- Phase-state schema, isolated git lanes, merge, retry, and quarantine semantics
- Cross-spec dependency metadata and validation
- Evidence-bound phase-close knowledge writeback
- Phase progress and categorical project-health reporting
- Ralph archival, active-surface cleanup, and migration documentation
- Disposable acceptance fixtures and a manual UAT plan

**Excluded:**
- Opaque, unbounded unattended execution or a Ralph successor
- Multi-spec `/implement-phase --recommend`
- Parallel spec execution
- Cloud-agent infrastructure or scheduled automation
- Knowledge consolidation and skill lifecycle work (Phase 7)
- Numeric health scoring
- Live CI, hosted service, or external-memory integrations
- Automatic approval of human-judgment UAT criteria

### Technical Concerns

- Artifact-based eval health can be unknown on a machine with no recent local result. `/status` must report unavailable or stale evidence rather than imply failure or fabricate health.
- Isolation must begin before implementation. Creating a branch only after failure cannot guarantee a clean phase branch.
- This umbrella spec cannot self-prove the roadmap's 3+ spec criterion. Disposable sandbox UAT supplies mechanical evidence; the real-use User Challenge criterion stays pending until observed.
- Ralph deprecation changes generated `SKILL.md`; regeneration and `scripts/gen-skill.sh --check` belong to the same story.

### Recommendations

- Extend `/verify-spec` Check 4 rather than add a ninth top-level check, preserving its eight-check public contract.
- Treat `phase-execution-*.json` as the canonical state boundary and add lane branch, worktree, merge, quarantine, dependency, and escalation fields.
- Keep platform-specific subagent mechanics in adapters and `commands/implement-phase.md` platform-neutral.
- Archive Ralph under one namespaced tree so historical references remain coherent without polluting active discovery.
- Keep the real-use roadmap criterion visibly open rather than treating a synthetic demonstration as product evidence.

### Cross-Spec Review

`2026-07-10-recommended-autonomous-delivery` is a binding prerequisite that supersedes conflicting autonomy governance before this phase begins. It owns single-spec `--recommend` delivery; this spec owns normal multi-spec phase orchestration. The incomplete Phase 2A shipping/review spec has a distinct `/ship` health concept. Completed Ralph, Context Engine, and Phase 4 specs are implementation references, not competing work.

---

## Experience Design

### Primary User Journey

1. The maintainer invokes `/implement-phase 6` or another roadmap phase.
2. Writ resolves specs, validates `dependencies:`, inventories progress, and displays one ordered execution plan.
3. After one confirmation, Writ creates an isolated lane for the first eligible spec and launches a fresh subagent with artifact-derived context.
4. The subagent runs `/implement-spec`, returns a structured result, and exits.
5. The orchestrator merges successful work into the phase branch, generates UAT, updates phase state, and advances.
6. On terminal failure, the lane is preserved under `writ/quarantine/{spec}`; declared dependents are blocked and independent specs continue.
7. At phase close, Writ verifies machine-checkable criteria, records only qualifying durable knowledge, and reports honest status plus pending human validation.

### State Catalog

| State | User-visible behavior |
|---|---|
| No roadmap phase | Explain the missing source and offer the existing `--specs` fallback |
| Unspecced feature | Ask once before execution; never silently drop roadmap scope |
| Invalid dependency graph | Stop before confirmation with exact missing, self, or cycle path |
| Ready | Show ordered specs, dependency reasons, lane model, and exit criteria |
| Executing | `/status` shows current spec, lane, progress, elapsed state, and evidence health |
| Transient failure | Record one retry and continue without a new routine confirmation |
| Terminal failure | Preserve quarantine branch, block dependents, continue independent work |
| Scope degradation proposed | Present User Challenge; select only with defensible evidence and low-risk reversibility, otherwise pause for explicit human choice |
| Interrupted | `--resume` reconstructs work from state and git reality |
| Implemented | Report machine evidence and hand off human UAT; do not claim completion early |
| Stale health evidence | Show `Warning — evidence stale` with the stale or missing inputs named |

### User Challenge Format

Every qualifying challenge must contain:

1. **What the roadmap/spec said**
2. **What Writ recommends**
3. **What context may be missing**
4. **Cost if the recommendation is wrong**

The choice is then presented through `AskQuestion`. The format is not used for ordinary progress, transient failures, or decisions already answered by artifacts.

### Interaction and Output Rules

- Output remains concise, terminal-oriented Markdown; no new UI is introduced.
- A phase plan is the only routine confirmation.
- Error messages include the affected spec, current lane, branch disposition, dependent impact, and one recovery path.
- Health is categorical, never a pseudo-precise score.
- Missing evidence is distinct from failing evidence.

---

## Detailed Requirements

### R1 — Cross-Spec Dependency Contract

- New specs support `> **Dependencies:** [spec-folder-id, ...]`.
- Empty dependencies are represented as `[]`.
- References use exact folder IDs under `.writ/specs/`; titles and fuzzy matches are invalid as dependency identifiers.
- `/create-spec` emits the field for all new specs.
- `/implement-phase` builds its graph from explicit metadata first.
- `/verify-spec` Check 4 validates reference existence, self-reference, duplicate entries, and cycles across the reachable spec graph.
- Prose overlap and shared-file inference remain warnings for missing declarations and cannot override explicit order.

### R2 — Fresh Isolated Per-Spec Execution

- Before invoking a spec, the orchestrator creates a dedicated branch and worktree from the current phase branch.
- The branch naming convention is `writ/phase/{phase-id}/{spec-id}` while active.
- A fresh subagent receives the spec path, phase state path, inherited answer rules, execution mode, and expected structured result schema.
- The orchestrator does not forward accumulated conversational history.
- On success, the orchestrator verifies the lane, merges it into the phase branch, removes the worktree, records the merge, and generates UAT.
- Adapter docs map the platform-neutral contract to native subagent primitives.

### R3 — User Challenge Escalation

- User Challenge is mandatory only when a proposed choice would weaken locked scope or exit criteria.
- Apply ADR-013's evidence-based select-or-pause boundary: defensible low-risk reversible choices may be selected and audited; critical ambiguity, missing evidence, or material irreversible risk requires explicit human choice.
- Existing ask-worthy conditions remain bounded; the new format changes framing, not frequency.
- Challenges and the selected decision are persisted in phase state for resume and audit.
- Nested commands return unresolved or critical scope-degradation decisions to the orchestrator; any evidence-supported local selection must include the structured challenge and durable audit evidence.

### R4 — Quarantine and Recovery

- One retry is permitted only for failures classified as transient.
- After terminal failure, the active lane branch is renamed or retained as `writ/quarantine/{spec-id}`.
- The phase branch must have no commits or working-tree changes from the failed lane.
- Explicit dependents become `skipped_blocked`; independent specs remain eligible.
- State records failure evidence, quarantine branch, blocked dependents, retry count, and recovery guidance.
- `--resume` detects whether quarantine, active lane, and phase branches still match recorded state and reports discrepancies before acting.

### R5 — Evidence-Bound Knowledge Writeback

- Phase close scans the phase report and per-spec drift logs for candidate lessons.
- A candidate qualifies only when it is durable beyond one spec, supported by a named artifact or repeated drift, and not substantively duplicated in `.writ/knowledge/`.
- Qualifying entries use the existing knowledge schema and normally target `lessons`.
- Decisions with architectural blast radius remain ADRs and are not auto-written as lessons.
- The phase report lists written entries and rejected candidates with terse reasons; no candidate means no section.

### R6 — Status and Health

- `/status` reads in-flight `phase-execution-*.json` in addition to existing story-batch state.
- It reports phase, current spec, completed/failed/blocked counts, active lane, and quarantine branches.
- The health line aggregates the newest available eval result, verification report, and relevant drift evidence.
- Categories:
  - `Healthy`: available evidence is current and passing, with no unresolved material drift.
  - `Warning`: evidence is missing/stale or non-blocking warnings exist.
  - `Attention`: a current check failed, material drift is unresolved, or phase state is inconsistent with git.
- The line names evidence age or missing inputs and does not execute `/verify-spec`, build, or test commands.
- Supporting producers may write lightweight summaries under `.writ/state/`; these remain ephemeral and gitignored.

### R7 — Ralph Deprecation

- Move Ralph implementation and reference material into `archive/ralph/`, preserving recognizable relative grouping.
- Remove Ralph from `.writ/manifest.yaml`, active generated `SKILL.md`, command discovery, config guidance, adapters, README, `/status` allowlists, and quick actions.
- Remove or redirect stale active references throughout product source.
- Document `/implement-phase` as the supported replacement and note the deliberate loss of unattended execution.
- Warn users with in-flight `ralph-*.json` state to finish or abandon those runs before upgrading; do not migrate that state automatically.
- Update `CHANGELOG.md`.
- Regenerate `SKILL.md` and verify generated output.

### R8 — Acceptance Evidence

- Create a disposable UAT fixture outside active product discovery or generate it during UAT in a temporary directory.
- The fixture contains at least three specs: one succeeds, one fails after partial work, and one is explicitly dependent on the failure; include an independent spec if needed to prove continuation.
- Verify clean merge, quarantine preservation, dependency blocking, independent continuation, resume state, User Challenge rendering, and categorical health.
- Sandbox evidence may satisfy mechanical criteria only.
- The roadmap's “during real use” User Challenge criterion stays pending until a real phase produces evidence.

---

## Implementation Approach

### Architecture

`/implement-phase` remains the platform-neutral state machine:

`resolve → validate graph → confirm → create lane → spawn fresh agent → verify result → merge or quarantine → UAT → close`

Platform adapters own the translation from “spawn fresh agent” to Cursor Task, Claude Code subagent, or Codex agent thread. Git state and `.writ/state/phase-execution-*.json` are the cross-platform source of truth.

### Phase State Extensions

Each spec record should include:

- dependency IDs and resolved status
- lane branch and worktree path
- fresh agent run identifier when available
- attempt count and last transition time
- result status and verification evidence
- merge commit on success
- quarantine branch and failure summary on terminal failure
- blocked dependents
- unresolved and resolved User Challenges
- UAT plan path

Writes must be atomic enough that interruption leaves either the prior valid state or the next valid state, never malformed partial JSON.

### Health Evidence

Health aggregation consumes summaries rather than rerunning deep diagnostics. Verification reports already persist under specs. Drift logs are append-only. Eval should expose a lightweight latest-result summary when run locally; absent evidence is explicitly `Warning`, not `Attention`.

### Validation Strategy

This repository has no application test suite. Verification is contract and script based:

- focused fixture parsing for dependency metadata
- manual/sandbox orchestration UAT
- `bash scripts/eval.sh`
- `bash scripts/gen-skill.sh --check`
- `bash scripts/install.sh --dry-run`
- `bash scripts/update.sh --dry-run`
- targeted searches proving Ralph is absent from active surfaces

---

## Files in Scope

### Primary

- `commands/implement-phase.md`
- `commands/implement-spec.md`
- `commands/create-spec.md`
- `commands/verify-spec.md`
- `commands/status.md`
- `commands/knowledge.md`
- `commands/_preamble.md`
- `adapters/cursor.md`
- `adapters/claude-code.md`
- `adapters/codex.md`
- `.writ/docs/config-format.md`
- `.writ/docs/phase-execution-state-format.md` (new)

### Ralph Retirement

- `commands/ralph.md`
- `scripts/ralph.sh`
- `scripts/PROMPT_build.md`
- `.writ/docs/ralph-cli-pipeline.md`
- `.writ/docs/ralph-state-format.md`
- `.writ/manifest.yaml`
- `SKILL.md`
- `README.md`
- `CHANGELOG.md`
- `archive/ralph/**` (new)

### Supporting Validation

- `scripts/eval.sh`
- `scripts/gen-skill.sh`
- `.github/workflows/eval.yml` only if evidence-summary behavior requires clarification
- `.writ/specs/2026-07-09-phase6-autonomy-ceiling/uat-plan.md` (generated after implementation)

---

## Story Plan

1. **Authoritative cross-spec dependencies** — Dependencies: None
2. **Fresh isolated execution lanes** — Dependencies: Story 1
3. **Contract-preserving User Challenges** — Dependencies: Story 2
4. **Failure quarantine and resumable recovery** — Dependencies: Stories 2, 3
5. **Evidence-bound phase knowledge** — Dependencies: Story 4
6. **Phase progress and production health** — Dependencies: Stories 4, 5
7. **Ralph retirement and autonomy acceptance** — Dependencies: Stories 1–6

---

## Deliverables

- [ ] `dependencies:` emitted, consumed, and validated across spec workflows
- [ ] Fresh per-spec subagent contract documented for all three adapters
- [ ] Isolated lane success path merges cleanly into the phase branch
- [ ] Terminal failure path preserves `writ/quarantine/{spec}`
- [ ] User Challenge framing implemented for scope-degradation decisions
- [ ] Extended phase execution state documented and resumable
- [ ] Evidence-bound phase-close knowledge writeback implemented
- [ ] `/status` phase progress and categorical health line implemented
- [ ] Ralph archived and removed from active discovery surfaces
- [ ] Sandbox UAT demonstrates 3+ spec execution and failure isolation
- [ ] Real-use User Challenge roadmap criterion explicitly tracked as pending until observed

