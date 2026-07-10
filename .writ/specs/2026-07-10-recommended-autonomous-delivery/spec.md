# Recommended Autonomous Delivery

> **Status:** Not Started
> **Contract Locked:** ✅
> **Created:** 2026-07-10
> **Owner:** @AdamSellke
> **Priority:** High
> **Effort:** Large
> **Dependencies:** []
> **Origin:** Promoted from issue: `.writ/issues/improvements/2026-07-09-label-recommended-spec-options.md`
> **Blocks:** `2026-07-09-phase6-autonomy-ceiling` until governance conflicts are reconciled

---

## Specification Contract

**Deliverable:** Add an observable, resumable `--recommend` mode that carries a feature from specification through implementation, PR preview validation, one human production approval, merge, and versioned release.

**Origin:** Promoted from `.writ/issues/improvements/2026-07-09-label-recommended-spec-options.md`.

**Must Include:** Every automatic choice produces a concise, evidence-based entry in a tracked recommendation log inside the spec package. This records decisions and rationale, not private chain-of-thought.

**Hardest Constraint:** Coordinate provider-specific CI and preview deployments without claiming Writ can provision a universal staging environment.

### Experience Design

- **Entry:** `/create-spec --recommend …` for new work or `/implement-spec --recommend …` for an existing spec.
- **Happy path:** Deliberate → save contract and stories → implement and verify → commit and open PR → discover preview deployment → generate UAT → await one human approval → merge → release.
- **Moment of truth:** The user can inspect the working preview and complete decision history before authorizing production.
- **Feedback:** Each selected recommendation is briefly shown and appended to the spec's durable recommendation log.
- **Recovery:** Interruptions resume from persisted state without repeating completed external actions.
- **Human gate:** Stage approval authorizes both merge and the recommended release. Additional pauses occur only for critical ambiguity or hard platform blockers.

### Business Rules

1. Normal interactive mode marks every recommended option with `(Recommended)`.
2. `--recommend` selects only evidence-supported choices; it never treats the first or affirmative option as an implicit default.
3. Equivalent choices resolve toward the simpler, more reversible option.
4. The mode automatically resumes after a required human answer.
5. Security, data-loss, compliance, unexpected cost, destructive migration, unresolved contract ambiguity, failed CI, merge conflicts, and authentication failures still pause.
6. Preview/stage deployment reuses existing project CI or deployment integration; Writ does not provision infrastructure.
7. Missing preview capability pauses with setup guidance rather than silently promoting unvalidated work.
8. Production approval is explicit and cannot be inferred from inactivity.
9. Release begins only after the PR is merged into the default branch and required checks pass.
10. Semantic version and changelog choices are selected from change evidence and recorded.
11. The Writ runtime helper remains excluded from automatic publishing.
12. Platform approvals and branch protections are never bypassed.

### Planned Stories

1. **Governance and autonomy policy** — supersede ADR-010's contract-level gate, reconcile the active Phase 6 spec, and define auto-select versus pause rules.
2. **Recommendation semantics** — consistent `(Recommended)` labels and evidence-based selection behavior.
3. **Autonomous spec-to-implementation orchestration** — mode propagation, durable decision log, and resumable state.
4. **PR preview and staged UAT** — PR creation, CI/preview discovery, validation evidence, and the production approval gate.
5. **Merge and release completion** — idempotent merge, recommended SemVer release, external failure recovery, and completion reporting.

### Success Criteria

1. A fixture run completes from issue input to a saved spec, implemented changes, preview URL, approved merge, tag, and release.
2. Every automatic choice is auditable in the tracked spec package.
3. Normal mode consistently labels recommendations.
4. No irreversible production action occurs before stage approval.
5. Interrupted runs resume without duplicate PRs, merges, tags, or releases.
6. Missing deployment integration and failed CI stop safely.
7. Cursor, Claude Code, and Codex adapters preserve equivalent semantics.

### Scope Boundaries

**Included:**
- Single-spec recommended delivery from contract creation through release
- Shared recommendation policy and interactive recommendation labels
- Existing preview-provider discovery and staged UAT
- Durable recommendation evidence and resumable execution state
- PR creation, human production approval, merge, and methodology release
- Governance and active-spec reconciliation required to supersede ADR-010

**Excluded:**
- Provisioning staging infrastructure
- Bypassing branch protection, platform approval, or authentication
- Automatic npm publishing of `@sellke/writ`
- Multi-spec `/implement-phase --recommend`
- Post-production observability or rollback automation
- Storage of private chain-of-thought

### Technical Concerns

- External CI and deployment waits require durable identifiers and idempotency checks.
- `/ship` currently opens but does not merge PRs despite language implying otherwise; this spec must correct that contract.
- Raw model deliberation cannot and should not be persisted. The durable artifact contains the decision, evidence, alternatives considered, and risk/reversibility.
- The modifier intentionally creates a narrow exception to the rule that planning commands stop before implementation.
- The documented date helper in `/create-spec` references the removed `@devobsessed/writ` package; implementation should use the repository's current deterministic helper contract.

### Cross-Spec Overlap

- **Phase 6: Autonomy Ceiling** (`Not Started`) directly conflicts with this contract and modifies `implement-spec`. Story 1 must reconcile it before either spec is implemented.
- **Phase 2a: Shipping & Review** (`Dogfooding Pending`) owns `/ship`. This work extends its incomplete "branch to merged PR" promise with actual staged validation and merge behavior.

### Recommendation

Keep this as a separate prerequisite to Phase 6. Implement single-spec autonomous delivery first; broadening it to multi-spec phase execution before the staging and release boundary is proven would multiply recovery risk.

---

## Experience Design

### Entry Points

`/create-spec --recommend [idea]` starts the complete workflow. Existing source modes compose with the modifier:

- `/create-spec --recommend --from-issue [path]`
- `/create-spec --recommend --from-prototype`

`/implement-spec --recommend [spec]` starts at implementation for an already locked spec. It must not regenerate or silently rewrite the contract.

Normal invocations remain interactive. Their behavior changes only by consistently labeling the evidence-backed recommendation in every bounded choice.

### Happy Path

1. Writ gathers evidence and chooses reversible, low-risk defaults while creating the contract.
2. The complete spec package and `recommendation-log.md` are written before implementation begins.
3. `/implement-spec` receives the active recommendation mode and executes all stories through review, testing, documentation, and integration verification.
4. `/ship --test --recommend` creates evidence-based commits, pushes the branch, and opens the PR.
5. Writ waits for required CI and discovers an existing preview or staging deployment.
6. Writ generates `uat-plan.md`, records the preview URL and checks, and asks for one explicit production approval.
7. Approval authorizes merge and the recommended versioned release.
8. Writ confirms the default branch contains the merge, runs the release gate, creates the changelog, version commit, tag, and GitHub release.
9. The final report links the spec, recommendation log, PR, deployment evidence, merge commit, and release.

### State Catalog

- **Deliberating:** Current question, selected recommendation, and concise rationale are visible.
- **Planning:** Spec artifacts are being generated; no implementation has started.
- **Implementing:** Story and gate progress is visible through existing pipeline state.
- **PR open:** Commit and PR identifiers are persisted.
- **Waiting for CI:** Required checks are pending; no production action is allowed.
- **Preview ready:** Preview URL and validation evidence are available.
- **Awaiting approval:** Human UAT is the only routine gate.
- **Merging:** Approved PR is being merged through the provider's supported path.
- **Releasing:** Merge ancestry is verified and release gate is running.
- **Complete:** All durable links and outcomes are recorded.
- **Blocked:** One actionable blocker and a safe resume path are shown.

### Feedback and Audit Model

The workflow emits concise progress in the active session and appends durable decisions to `{spec}/recommendation-log.md`. Each entry contains:

- Stable decision ID and workflow phase
- Decision made
- Evidence used
- Material alternatives considered
- Risk and reversibility classification
- Whether selection was automatic or human-approved
- Resulting artifact or external identifier

The log is an audit summary, not hidden reasoning or a transcript dump.

### Error Experience

- **No defensible recommendation:** Pause with the missing evidence and bounded choices.
- **Critical ambiguity:** Explain the affected contract or risk boundary and await a human answer.
- **Interrupted session:** Resume from persisted state after reconciling repository and provider reality.
- **No preview deployment:** Keep the PR open and provide project-specific setup guidance.
- **CI failure:** Keep the PR unmerged, summarize failures, and route back to a bounded repair attempt.
- **Merge conflict or branch protection:** Stop without bypassing policy and show the exact recovery path.
- **Release failure:** Preserve the merged state, detect any existing version commit/tag/release, and resume idempotently.

---

## Detailed Requirements

### R1 — Governance Supersession

- Create a new ADR that explicitly supersedes ADR-010's contract-level human gate while preserving its accountability objective.
- Define the new ceiling as observable, session-started, resumable autonomous delivery with one human production boundary.
- Preserve the non-goal of an opaque, unbounded overnight loop.
- Amend the active Phase 6 contract, lite spec, and affected stories so they no longer claim that every contract or User Challenge must be human-decided.
- Make this spec a prerequisite of Phase 6 before implementation sequencing begins.
- Update `system-instructions.md` so `--recommend` is an explicit exception to the planning-command terminal boundary.

### R2 — Recommendation Policy

- Every AskQuestion recommendation in normal interactive mode ends with exactly `(Recommended)`.
- Recommendation labels reflect an evidence-backed assessment, not option order.
- At most one option is marked recommended unless the options are explicitly equivalent; equivalent options should normally collapse to the simpler choice.
- Automatic selection requires a concise rationale tied to repository evidence, locked artifacts, provider state, or established project conventions.
- Pause classifications include safety, security, data integrity, compliance, unexpected cost, destructive or irreversible behavior before the production gate, core-contract ambiguity, and subjective taste without usable evidence.
- Low-risk reversible ambiguity selects the simplest viable option.
- A required answer does not clear recommendation mode.

### R3 — Mode Propagation and Orchestration

- `--recommend` is parsed once and propagated explicitly through internal command calls.
- `/create-spec --recommend` owns the top-level state machine through release; nested commands return structured outcomes rather than independently terminating the workflow.
- `/implement-spec --recommend` begins at the implementation state and continues through staged delivery.
- The spec package must exist and pass structural validation before code implementation starts.
- Normal command behavior remains backward compatible when the modifier is absent.
- Unsupported command combinations fail before mutation with valid invocation guidance.

### R4 — Durable State and Recommendation Log

- Canonical runtime state lives at `.writ/state/recommend-execution-{id}.json`.
- Tracked audit history lives at `{spec}/recommendation-log.md`.
- State records the spec path, branch, story progress, PR, CI checks, preview deployment, approval, merge commit, version, tag, and release URL.
- Every external mutation has a preflight lookup and persisted completion identifier.
- Resume reconciles saved state against git and provider reality before acting.
- A stale or contradictory state stops with the mismatch; it never assumes success.

### R5 — PR, CI, and Preview Validation

- Recommended delivery always uses `/ship --test` semantics; it cannot omit the test evidence expected before staging.
- Commit grouping is automatically selected from the existing splitting heuristic and logged.
- PR creation is idempotent by branch and saved PR identifier.
- Required checks are discovered from provider state and must reach a successful terminal state.
- Preview discovery consumes existing CI/deployment output from configured project conventions or provider metadata.
- Writ does not create hosting accounts, deployment projects, environment secrets, or staging infrastructure.
- `uat-plan.md` is generated from the completed implementation and enriched with the preview URL and validation instructions.

### R6 — Production Approval

- The approval prompt presents the PR, preview URL, CI result, UAT plan, material warnings, recommended version bump, and release consequences.
- Approval must be an explicit user action.
- Approval authorizes both merge and the recommended release for the exact reviewed PR head SHA.
- Any change to the PR head after approval invalidates approval and returns to CI/preview validation.
- Rejection or requested changes returns the workflow to implementation while retaining recommendation mode.

### R7 — Merge and Release

- Merge uses the repository's configured provider and branch-protection-compatible strategy.
- The workflow never force-pushes, bypasses required checks, or overrides protected-branch policy.
- Release begins only after verifying the approved PR merge commit is present on the default branch.
- Semantic version selection follows existing release evidence: breaking change → major, feature → minor, fixes/docs/chore → patch.
- The selected bump and generated changelog are logged automatically.
- The standard release gate remains mandatory.
- Release creation is idempotent across version file, release commit, tag, pushed tag, and provider release.
- Runtime-helper npm publication remains manual and out of scope.

### R8 — Completion and Recovery

- Completion requires: spec complete, implementation verified, PR merged, release gate passed, version updated, tag pushed, and provider release created when supported.
- Authentication or authorization failures are reported once and stop without workaround.
- CI and deployment timeouts preserve resumable waiting state.
- A failed release never rewrites or deletes an existing tag without explicit human intervention.
- Final output distinguishes complete, blocked, and partially released states.

---

## Implementation Approach

### Shared Policy, Thin Command Integration

Define recommendation semantics once in `system-instructions.md` and a dedicated reusable product artifact if extraction materially reduces duplication. Commands should own phase-specific evidence and choices, while the shared policy owns labeling, auto-selection, pause classification, and resumption.

### Explicit State Machine

Model the workflow as:

`deliberate → write spec → implement → verify → commit → open PR → await CI → discover preview → await approval → merge → release → complete`

Each transition has:

1. Preconditions
2. Observable evidence
3. Mutation, if any
4. Persisted result identifier
5. Safe retry behavior

### Provider-Neutral Core

Command files describe required capabilities rather than hard-code Vercel or GitHub behavior. Adapters map:

- PR and required-check discovery
- Preview deployment URL discovery
- Merge operations
- Release publication
- Waiting and resume mechanics

Projects without an integration receive a blocker with configuration guidance.

### Governance Sequence

Story 1 lands first. It creates the superseding ADR and reconciles Phase 6 before behavioral implementation begins. This prevents two simultaneously active specs from giving agents contradictory autonomy rules.

---

## Files in Scope

### Product Source

- `commands/create-spec.md`
- `commands/implement-spec.md`
- `commands/ship.md`
- `commands/release.md`
- `commands/create-uat-plan.md`
- `system-instructions.md`
- `adapters/cursor.md`
- `adapters/claude-code.md`
- `adapters/codex.md`
- `.writ/docs/config-format.md`
- Additional state-format documentation if the implementation introduces a new schema

### Governance and Planning Artifacts

- `.writ/decision-records/adr-010-supervised-autonomy-ceiling.md`
- New superseding ADR
- `.writ/specs/2026-07-09-phase6-autonomy-ceiling/spec.md`
- `.writ/specs/2026-07-09-phase6-autonomy-ceiling/spec-lite.md`
- Affected Phase 6 story and README files
- `.writ/product/roadmap.md`

### Generated and Validation Surfaces

- `.writ/manifest.yaml` only if command invocation metadata changes
- `SKILL.md` regenerated if the manifest changes
- `README.md` and `CHANGELOG.md` where user-facing workflow descriptions require updates
- `scripts/eval.sh` fixtures for recommendation and resume behavior

---

## Story Plan

1. `story-1-governance-and-autonomy-policy.md` — Supersede ADR-010 and reconcile Phase 6. Dependencies: None.
2. `story-2-recommendation-semantics.md` — Define labels, selection evidence, and pause taxonomy. Dependencies: Story 1.
3. `story-3-autonomous-spec-implementation.md` — Propagate mode from spec creation through verified implementation with durable state. Dependencies: Story 2.
4. `story-4-preview-deployment-and-uat.md` — Open the PR, await CI, discover preview deployment, and collect production approval. Dependencies: Story 3.
5. `story-5-merge-release-and-recovery.md` — Merge the approved SHA and complete an idempotent release. Dependencies: Story 4.

---

## Definition of Done

- [ ] Superseding ADR and Phase 6 reconciliation are complete
- [ ] Normal interactive recommendations are consistently labeled
- [ ] `--recommend` behavior is evidence-based, auditable, and resumable
- [ ] Spec-to-implementation orchestration works without intermediate routine gates
- [ ] Preview deployment and UAT evidence precede production approval
- [ ] One explicit approval authorizes merge and release for an immutable PR SHA
- [ ] Merge and release paths are idempotent and policy-preserving
- [ ] Cross-platform adapter guidance is complete
- [ ] Eval fixtures cover happy, blocked, interrupted, and duplicate-prevention paths
- [ ] Source issue references this specification
