# Technical Specification: Recommended Autonomous Delivery

> **Parent:** `../spec.md`
> **Status:** Not Started
> **Stories:** 1–5
> **Scope:** Platform-neutral orchestration contract

## Purpose and Constraints

This sub-spec defines the durable state machine behind `/create-spec --recommend` and `/implement-spec --recommend`. It turns one locked specification into an observable sequence of local and provider-backed operations: implementation, verified PR creation, required-check completion, preview discovery, explicit human approval, protected merge, and versioned release.

The design assumes Writ remains a methodology implemented through command and adapter instructions. The core defines schemas, invariants, capabilities, and transition rules; it does not introduce a hosted Writ control plane.

### Explicit Exclusions

- Provisioning staging infrastructure, hosting accounts, deployment projects, environments, or secrets
- Bypassing branch protection, required reviews, provider approvals, authentication, or authorization
- Publishing `@sellke/writ` or any other package to npm
- Multi-spec `/implement-phase --recommend` or cross-spec delivery orchestration
- Raw chain-of-thought, hidden reasoning, transcript dumps, prompt bodies, or model scratch-space storage
- Post-production monitoring and automated rollback

## Architecture and Ownership Boundaries

```text
session-started command
        │
        │ parses --recommend once
        ▼
recommended-delivery orchestrator
        ├── recommendation policy ──► tracked recommendation-log.md
        ├── state reducer ──────────► .writ/state/recommend-execution-{id}.json
        ├── command delegates
        │     ├── create-spec
        │     ├── implement-spec / implement-story
        │     ├── ship --test
        │     ├── create-uat-plan
        │     └── release
        └── provider capability adapter
              ├── PR + checks
              ├── preview discovery
              ├── protected merge
              └── provider release
```

### Ownership Matrix

| Surface | Owns | Must Not Own |
|---|---|---|
| Top-level recommended-delivery orchestrator | Execution ID, current state, mode propagation, transition ordering, reconciliation, blocker routing, approval validation, final report | Story implementation details, provider-specific command syntax, hidden deliberation |
| Shared recommendation policy | Recommendation labels, evidence threshold, pause taxonomy, simpler/reversible tie-breaker, log entry semantics | Phase-specific evidence collection or external mutations |
| `/create-spec` | Contract discovery, spec package validation, initial state creation when it is the entry point | Continuing in normal mode; provider operations |
| `/implement-spec` | Story DAG, structured story outcomes, integration verification | Opening a second delivery execution; clearing recommendation mode after a question |
| `/ship` | Test evidence, commit grouping, push, idempotent PR open-or-find result | Merge completion, production approval, release |
| `/create-uat-plan` | Regenerating tester-facing UAT from completed artifacts and attaching preview instructions | Provisioning a preview or recording production approval |
| `/release` | Release gate, SemVer evidence, changelog, version mutation, release commit, tag, tag push, provider release | Running before merge ancestry is verified; npm publishing |
| State reducer | Validating and atomically persisting runtime state | Editing tracked audit history or inferring external success |
| Recommendation log writer | Concise tracked decision audit | Runtime locking, secrets, raw reasoning, full provider payloads |
| Provider adapter | Mapping neutral capabilities to available tools/CLIs/APIs and normalizing results | Choosing policy, weakening required checks, bypassing protections |
| Human | Explicit approval or rejection at the production boundary; answers to critical ambiguity | Reconfirming routine evidence-supported choices |

### Core Invariants

1. One execution owns one spec path and one feature branch.
2. The spec package is structurally valid before implementation begins.
3. `recommend` mode is explicit in every nested invocation and structured result.
4. An external mutation is attempted only after a lookup and is persisted only from observable provider or git evidence.
5. A saved identifier is a reconciliation hint, not proof that an operation still exists or succeeded.
6. Required checks and preview evidence apply to the exact PR head SHA presented for approval.
7. Approval is valid only for that immutable PR head SHA.
8. No merge or release mutation occurs before valid explicit approval.
9. Release starts only after the approved PR is merged and its merge commit is confirmed on the default branch.
10. Authentication and authorization failures stop; the workflow never searches for a bypass.
11. State may contain operational summaries but never credentials, secret values, raw prompts, or chain-of-thought.
12. The tracked recommendation log contains decisions and concise evidence, not a conversation transcript.

## Execution Identity and State Persistence

### File Identity

Canonical state is `.writ/state/recommend-execution-{id}.json`.

- `id` is an opaque, filesystem-safe execution identifier generated once at entry.
- Recommended format is `{spec-folder}-{UTC-basic-timestamp}-{random-suffix}`; consumers must treat it as opaque.
- The state file is created with exclusive-create semantics. Collision generates a new suffix before any other mutation.
- Resume by explicit ID loads that file. Resume by spec is allowed only when exactly one non-terminal execution matches the canonical spec path and branch; ambiguity blocks.
- `.writ/state/` remains gitignored. The spec's `recommendation-log.md` is tracked.
- Writes validate the complete document, write a sibling temporary file, flush where supported, and atomically rename. If atomic replacement is unavailable, the adapter must document an equivalent crash-safe strategy or block before autonomous execution.
- Compatible readers preserve unknown fields. Unsupported major schema versions block before mutation.

### State Schema: `recommend-execution-v1`

The following JSON is normative. Every top-level key is required; unavailable values use `null` or an empty collection as shown rather than omission.

```json
{
  "schema": "recommend-execution-v1",
  "schemaVersion": 1,
  "executionId": "2026-07-10-recommended-autonomous-delivery-20260710T140000Z-a1b2",
  "revision": 12,
  "createdAt": "2026-07-10T14:00:00Z",
  "updatedAt": "2026-07-10T14:20:00Z",
  "entrypoint": {
    "command": "create-spec",
    "sourceMode": "from-issue",
    "recommend": true,
    "quick": false,
    "resumeRequested": false
  },
  "spec": {
    "id": "2026-07-10-recommended-autonomous-delivery",
    "path": ".writ/specs/2026-07-10-recommended-autonomous-delivery",
    "contractSha256": "hex-digest",
    "recommendationLogPath": ".writ/specs/2026-07-10-recommended-autonomous-delivery/recommendation-log.md",
    "uatPlanPath": ".writ/specs/2026-07-10-recommended-autonomous-delivery/uat-plan.md"
  },
  "repository": {
    "root": "/absolute/path/used-for-this-run",
    "remoteName": "origin",
    "remoteIdentity": "provider-neutral-owner/repository",
    "defaultBranch": "main",
    "featureBranch": "feat/recommended-autonomous-delivery",
    "startingSha": "40-char-git-sha",
    "currentLocalHeadSha": "40-char-git-sha",
    "provider": "github",
    "providerRepositoryId": "stable-provider-repository-id"
  },
  "mode": {
    "name": "recommend",
    "propagationToken": "opaque-non-secret-token",
    "requiredHumanGate": "production",
    "automaticSelectionPolicy": "evidence-simplest-reversible-v1"
  },
  "status": "waiting_ci",
  "resumeTarget": "waiting_ci",
  "blocked": {
    "active": false,
    "code": null,
    "summary": null,
    "operation": null,
    "recoverable": false,
    "resumeFrom": null,
    "firstObservedAt": null,
    "lastObservedAt": null
  },
  "storyExecution": {
    "executionStatePath": ".writ/state/execution-20260710T140200Z.json",
    "planDigest": "hex-digest",
    "baselineCompletedStoryIds": [],
    "completedStoryIds": ["story-1"],
    "activeStoryId": null,
    "failedStoryIds": [],
    "integrationVerification": {
      "status": "passed",
      "headSha": "40-char-git-sha",
      "packageManifestSha256": "hex-digest",
      "planDigest": "hex-digest",
      "completedStoryIds": ["story-1"],
      "command": "bash scripts/eval.sh",
      "exitCode": 0,
      "completedAt": "2026-07-10T14:10:00Z",
      "evidenceSummary": "Full suite passed",
      "evidenceArtifact": ".writ/state/evidence/integration-a1b2.txt",
      "evidenceArtifactSha256": "hex-digest"
    }
  },
  "delivery": {
    "test": {
      "command": "bash scripts/eval.sh",
      "status": "passed",
      "completedAt": "2026-07-10T14:11:00Z",
      "evidenceSummary": "All checks passed",
      "evidenceArtifact": ".writ/state/evidence/ship-test-a1b2.txt"
    },
    "commits": {
      "strategy": "split",
      "headSha": "40-char-git-sha",
      "commitShas": ["40-char-git-sha"],
      "decisionId": "REC-004"
    },
    "pr": {
      "providerId": "42",
      "number": 42,
      "url": "https://provider.example/pull/42",
      "state": "open",
      "baseBranch": "main",
      "headBranch": "feat/recommended-autonomous-delivery",
      "headSha": "40-char-git-sha",
      "mergeCommitSha": null
    },
    "checks": {
      "observedForHeadSha": "40-char-git-sha",
      "requiredCheckIds": ["check-1"],
      "requiredCheckNames": ["eval"],
      "status": "pending",
      "lastObservedAt": "2026-07-10T14:20:00Z",
      "completedAt": null,
      "evidenceUrl": "https://provider.example/pull/42/checks"
    },
    "preview": {
      "deploymentId": null,
      "provider": null,
      "url": null,
      "status": "unknown",
      "observedForHeadSha": null,
      "source": null,
      "lastObservedAt": null,
      "evidenceUrl": null
    },
    "approval": {
      "status": "not_requested",
      "decision": null,
      "approvedPrHeadSha": null,
      "approvedAt": null,
      "actor": null,
      "interactionId": null,
      "recommendationEntryId": null,
      "uatPlanSha256": null,
      "previewUrl": null,
      "recommendedVersion": null,
      "invalidatedAt": null,
      "invalidationReason": null
    },
    "merge": {
      "strategy": null,
      "providerOperationId": null,
      "mergeCommitSha": null,
      "mergedAt": null,
      "defaultBranchContainsMerge": false,
      "verifiedAt": null
    },
    "release": {
      "previousVersion": null,
      "bump": null,
      "version": null,
      "changelogDigest": null,
      "versionCommitSha": null,
      "tag": null,
      "tagObjectId": null,
      "tagPushed": false,
      "providerReleaseId": null,
      "providerReleaseUrl": null,
      "providerReleaseSupported": null,
      "status": "not_started"
    }
  },
  "capabilities": {
    "snapshotAt": "2026-07-10T14:12:00Z",
    "pr": "available",
    "checks": "available",
    "preview": "available",
    "merge": "available",
    "release": "available",
    "adapter": "cursor",
    "details": []
  },
  "transitions": [
    {
      "sequence": 12,
      "from": "pr_open",
      "to": "waiting_ci",
      "startedAt": "2026-07-10T14:19:00Z",
      "completedAt": "2026-07-10T14:20:00Z",
      "attempt": 1,
      "operationKey": "checks:provider-repository-id:42:head-sha",
      "evidenceSummary": "Required check set discovered",
      "persistedIdentifiers": ["check-1"],
      "outcome": "succeeded"
    }
  ]
}
```

### Field and Enum Rules

| Field | Rule |
|---|---|
| `revision` | Monotonically increases once per successful state replacement; stale writers must not overwrite a newer revision |
| `entrypoint.command` | `create-spec` or `implement-spec` |
| `entrypoint.sourceMode` | `standard`, `from-issue`, `from-prototype`, or `existing-spec` |
| `mode.name` | Must remain `recommend` for the execution lifetime |
| `status` / `resumeTarget` | One of the state tokens defined below |
| `spec.contractSha256` | Digest of the locked contract section; mismatch after planning blocks rather than accepting a silent rewrite |
| Git SHAs | Full immutable object IDs, never abbreviated |
| Provider IDs | Stored as strings even when the provider renders a number |
| Evidence artifacts | Repo-relative under gitignored `.writ/state/`; summaries must be secret-redacted |
| Timestamps | UTC RFC 3339 strings |
| `operationKey` | Deterministic non-secret idempotency key derived from repository identity, target, and operation |
| `interactionId` | Platform interaction/message identifier where available; otherwise a generated local event ID persisted before continuing |
| `actor` | Display-safe user/provider identity if available; otherwise `explicit-session-user` |

### State Tokens

`deliberating`, `planning`, `implementing`, `verifying`, `committing`, `opening_pr`, `pr_open`, `waiting_ci`, `discovering_preview`, `preview_ready`, `awaiting_approval`, `merging`, `releasing`, `complete`, `blocked`, and `partially_released`.

`blocked` is resumable only through `blocked.resumeFrom`. `partially_released` is a terminal report state for a merged change whose release is incomplete; a later resume may re-enter `releasing` after reconciliation. The state machine does not persist a generic `failed` terminal because every failure must identify either a safe resume target or a partial-release boundary.

## Recommendation Log Schema

Tracked audit history lives at `{spec}/recommendation-log.md`. It is created before implementation and committed with the spec package. Entries are ordered by stable ID and never renumbered.

```markdown
# Recommendation Log: Recommended Autonomous Delivery

> **Spec:** `.writ/specs/2026-07-10-recommended-autonomous-delivery/spec.md`
> **Purpose:** Concise audit of recommendations and explicit production decisions
> **Privacy:** Decisions and evidence only; no private chain-of-thought or transcript content

## REC-001 — 2026-07-10T14:00:00Z — planning

- **Decision:** Use a single-spec delivery execution rooted at the locked contract.
- **Evidence:** The contract includes one spec; multi-spec recommend mode is excluded.
- **Alternatives:** Stop after spec creation; invoke multi-spec phase orchestration.
- **Risk:** Low — orchestration scope only.
- **Reversibility:** High — execution can stop before production approval.
- **Selection:** Automatic (`evidence-supported`).
- **Result:** Applied — execution `...-a1b2`; state transition `deliberating → planning`.
```

### Entry Contract

| Field | Required Content |
|---|---|
| Heading | Stable `REC-NNN`, UTC timestamp, and workflow phase |
| Decision | One concise statement of what was selected |
| Evidence | Observable repository, locked-artifact, provider, or project-convention facts; no hidden reasoning |
| Alternatives | Material alternatives actually evaluated, including pause when relevant |
| Risk | `Low`, `Medium`, `High`, or `Critical` plus a short impact statement |
| Reversibility | `High`, `Medium`, `Low`, or `Irreversible` plus the recovery boundary |
| Selection | `Automatic`, `Human answer`, `Human production approval`, or `Reconciliation`; include the policy/classification |
| Result | `Pending`, `Applied`, `Superseded`, `Invalidated`, `Blocked`, or `Failed`, followed by artifact/external identifier or state transition |

Entry creation is two-stage and crash-safe:

1. Append the complete entry before a selected mutation with `Result: Pending — operation key ...`; persist the entry ID in state.
2. After observing or reconciling the result, replace only that entry's `Result` line with a terminal result and identifier.
3. If resume finds a pending entry, reconcile the operation first. It finalizes the result, marks it `Blocked`, or records a new `Reconciliation` entry; it does not repeat the decision blindly.
4. Existing terminal entries are immutable. Corrections append a new entry that references and supersedes the old ID.

Never log credentials, environment values, provider payloads, raw model output, prompt text, chain-of-thought, or speculative claims. Evidence is summarized and may link to a redacted artifact or external URL.

## Mode Propagation Contract

`--recommend` is parsed only by the entry command and becomes an explicit structured execution context:

```yaml
delivery_context:
  execution_id: string
  state_path: repo-relative-path
  spec_path: repo-relative-path
  mode: recommend
  propagation_token: opaque-non-secret-token
  parent_command: create-spec | implement-spec | ship | create-uat-plan | release
  return_contract: recommend-command-result-v1
```

Every nested command receives this context and returns:

```yaml
schema: recommend-command-result-v1
execution_id: string
mode: recommend
command: string
status: succeeded | blocked | answer_required | failed
completed_state: state-token | null
resume_state: state-token | null
evidence:
  summary: string
  artifacts: [string]
identifiers: {}
blocker:
  code: string | null
  summary: string | null
```

Rules:

- A nested command rejects a missing or mismatched execution ID, mode, spec path, or propagation token.
- Nested commands return to the orchestrator; they do not print a terminal "next command" and end the delivery run.
- A required human answer returns `answer_required`. The parent records the answer, keeps `mode: recommend`, and automatically resumes the same transition.
- Normal invocations without `--recommend` preserve existing interactive and terminal behavior.
- `--recommend` with `--dry-run`, `--no-tag`, `--skip-gate`, `--draft`, `--no-split`, `/implement-phase`, or multiple spec arguments fails before mutation. `--from-issue` and `--from-prototype` remain valid create-spec source modifiers.
- Recommended delivery always delegates to `/ship --test --recommend`; tests cannot be omitted and a failing suite cannot be shipped as a draft.
- Recommended delivery calls the standard release gate; `--skip-gate` is prohibited.

## Provider Capability Contract

The neutral core requests capabilities. An adapter may satisfy them through an MCP tool, provider CLI, authenticated API, or a composition of read-only git/provider queries. It must normalize output and declare unavailable operations before their first mutation.

### Capability Envelope

```yaml
schema: recommend-provider-capabilities-v1
provider: string
repository_id: string
adapter: string
capabilities:
  pr: available | unavailable | needs_auth
  checks: available | unavailable | needs_auth
  preview: available | unavailable | needs_auth
  merge: available | unavailable | needs_auth
  release: available | unsupported | unavailable | needs_auth
constraints:
  merge_strategies: [merge, squash, rebase]
  can_observe_required_checks: boolean
  can_observe_preview_for_sha: boolean
  can_publish_provider_release: boolean
guidance:
  - capability: string
    setup: string
```

### Required Operations

| Capability | Neutral Operation | Required Input | Normalized Output | Mutation |
|---|---|---|---|---|
| PR | `findPullRequest` | repository ID, base branch, head branch | zero or one canonical PR record; multiple matches are contradictory | No |
| PR | `createPullRequest` | operation key, head/base, title, body, ready status | provider ID, number, URL, head SHA, state | Yes |
| PR | `getPullRequest` | repository ID, PR ID | state, base, head branch/SHA, mergeability, merge commit | No |
| Checks | `listRequiredChecks` | repository ID, PR ID, head SHA | stable check IDs/names, status per check, evidence URL | No |
| Preview | `findPreview` | repository ID, PR ID, head SHA, configured conventions | deployment ID, URL, status, source, evidence URL | No |
| Merge | `mergePullRequest` | operation key, PR ID, approved head SHA, permitted strategy | provider operation ID, merge commit SHA, merged timestamp | Yes |
| Merge | `getMergeResult` | repository ID, PR ID | merged state, merge commit SHA, actual head merged | No |
| Release | `findRelease` | repository ID, tag | provider release ID/URL/state or absent | No |
| Release | `createRelease` | operation key, immutable tag object ID, title, notes | provider release ID and URL | Yes |

### Capability Semantics

- `findPullRequest` must use provider repository identity plus base/head, not title text. If a persisted PR ID exists, it is queried first and must match those branches.
- Required checks come from branch/provider policy when observable. A configured allowlist may narrow noisy informational checks but may not remove provider-required checks.
- An empty required-check set is a valid success only when the provider explicitly reports no required checks. Inability to discover requirements is `unavailable`, not an empty set.
- Preview evidence must bind to the current PR head SHA by deployment metadata, commit association, check output, or a configured URL extraction convention with matching build evidence.
- Preview discovery is read-only. No operation may create deployment infrastructure, accounts, projects, secrets, or environments.
- Missing preview capability or a preview that cannot be bound to the current SHA blocks with setup guidance and leaves the PR open.
- Merge uses only a strategy both configured and reported as permitted. Provider refusal, branch protection, required review, or policy failure blocks without fallback bypass.
- Provider release is optional only when the capability envelope reports `unsupported`. `unavailable` or `needs_auth` is a blocker after tag push and produces `partially_released`.
- Local release artifacts—version file, changelog, release commit, and tag—remain owned by `/release`; the provider adapter publishes the already-created immutable tag.

## State Transitions

Every transition follows: validate preconditions → reconcile target → append pending recommendation entry when a choice exists → persist transition attempt → perform at most one mutation → observe outcome → persist identifiers and evidence → finalize log result.

| From → To | Preconditions | Observable Evidence | Mutation | Persisted Identifiers | Retry / Idempotency |
|---|---|---|---|---|---|
| entry → `deliberating` | Supported invocation; git repository; no ambiguous active execution | Parsed flags, repository root, source input | Exclusive-create state | execution ID, state path, repo identity, mode token | Existing matching execution causes resume offer/automatic resume; never creates a second execution silently |
| `deliberating` → `planning` | Evidence supports bounded choices or required answers have been supplied | Source issue/prototype/idea, repository artifacts, selected recommendations | Start contract/spec generation | decision IDs, source mode | Existing valid spec artifacts are reconciled by digest; conflicting artifacts block |
| `planning` → `implementing` | Locked contract; complete spec package; structural validation passes; recommendation log exists | Contract digest and package validation report | Invoke implementation orchestration | contract digest, implementation state path, plan digest | Completed stories are skipped from artifact evidence; active story resumes through its own idempotent pipeline |
| `implementing` → `verifying` | All planned stories report success | Story files, structured results, commits/worktree evidence | Run integration verification | completed story IDs, evidence artifact | Same verification command may rerun; no external mutation |
| `verifying` → `committing` | Integration verification passed; clean ownership of feature branch | Test output, git diff/status, current branch | Select grouping and create commits | decision ID, commit SHAs, resulting head SHA | Reconcile existing commits against diff and messages; never duplicate commits when head already matches |
| `committing` → `opening_pr` | `/ship --test` evidence passed; feature head pushed or push is required; provider PR capability available | Test artifact, branch/head, remote identity, preflight PR lookup | Push branch if needed | pushed head SHA | Compare remote head first; push only missing commits; non-fast-forward blocks |
| `opening_pr` → `pr_open` | No contradictory existing PR; current head known | `findPullRequest` result | Create PR only if absent | PR provider ID, number, URL, base/head/SHA | Find by saved ID then base/head; existing matching PR is success; multiple or mismatched PRs block |
| `pr_open` → `waiting_ci` | PR open and current PR head equals persisted feature head | Provider PR record and required-check discovery | None | head SHA, required check IDs/names, evidence URL | Poll/read only; timeout preserves `waiting_ci`; changed head invalidates downstream evidence |
| `waiting_ci` → `discovering_preview` | Every provider-required check for the same head SHA is successful | Terminal check records and evidence URL | None | check completion time and observed SHA | Pending remains waiting; failed/cancelled checks block and route to repair; unknown status blocks |
| `discovering_preview` → `preview_ready` | Checks passed; preview capability available | Deployment/check metadata proving URL belongs to PR head SHA | None | deployment ID, URL, provider, source, observed SHA, evidence URL | Re-query by PR/head; same deployment is success; timeout preserves discovering state; missing capability blocks |
| `preview_ready` → `awaiting_approval` | UAT plan generated from completed implementation and enriched with preview; recommended version computed | UAT plan digest, PR URL/head SHA, check evidence, preview URL, warnings, release analysis | Regenerate `uat-plan.md`; present one approval prompt | UAT digest, recommendation entry ID, proposed version | Regeneration is deterministic and overwrites stale UAT; prompt may be re-presented but inactivity never approves |
| `awaiting_approval` → `merging` | Explicit approval event; PR/check/preview head all equal; approval bound to that full SHA | User action and fresh provider reconciliation | Persist approval first, then request protected merge | actor, interaction ID, approved SHA/time, UAT digest, version | Before merge, re-read PR. Any head change invalidates approval and returns to `waiting_ci`; repeated approval event is deduplicated by interaction ID |
| `awaiting_approval` → `implementing` | Explicit rejection or requested changes | Human decision and requested-change summary | None until bounded repair begins | interaction ID, rejection decision entry | Preserve recommend mode and PR ID; subsequent commits force CI/preview/approval refresh |
| `merging` → `releasing` | Valid approval; provider reports merged approved SHA; merge commit is on default branch; required checks still successful | PR merge record, merge commit, fetched default-branch ancestry | Merge PR if not already merged; fetch default branch | merge operation ID, merge commit SHA, verified timestamp | Query merge result before mutation; already merged approved SHA is success; merged different SHA blocks; never retry policy denial as another strategy |
| `releasing` → `complete` | Merge ancestry verified; standard release gate passed; SemVer/changelog decision logged | Version sources, changelog preview, gate evidence, git refs, provider release lookup | Update version/changelog, commit, tag, push commit/tag, create provider release when supported | version, bump, changelog digest, version commit, tag/object ID, push state, provider release ID/URL | Reconcile each substep independently; matching artifact advances, mismatch blocks; never delete/rewrite tags automatically |
| `releasing` → `partially_released` | Merge complete but one release substep cannot finish | Existing release artifacts plus exact failure evidence | No compensating deletion | all completed release identifiers and failed substep | Resume re-enters `releasing` after auth/permission/blocker is resolved |
| any nonterminal → `blocked` | Critical ambiguity, safety boundary, failed CI, missing preview, conflict, auth/permission error, contradiction, or timeout requiring user action | One classified blocker with exact operation and evidence | None beyond safe abort of incomplete local git operation | blocker code/timestamps, `resumeFrom` | Re-entry first reconciles; identical auth/permission failure is reported once per resume attempt |
| any resumable terminal → prior target | User resumes and reconciliation finds a safe consistent state | State, git, spec, and provider snapshot | None during reconciliation | reconciliation transition and changed external facts | Contradiction remains blocked; reconciliation may advance past already-completed operations but never assumes success |

### CI Repair Loop

A failed required check transitions to `blocked` with `resumeFrom: implementing`. One focused repair attempt may be recommended only after the failure output is summarized and mapped to the current diff. New commits update PR head, clear checks/preview/approval fields, and resume at `waiting_ci`. A check cannot be waived by recommendation mode.

### Release Sub-State Order

Within `releasing`, the fixed idempotent order is:

1. Reconcile current version and proposed SemVer.
2. Run the standard release gate.
3. Reconcile or write changelog and version files.
4. Reconcile or create the release commit.
5. Reconcile or create the annotated tag.
6. Reconcile or push the default-branch release commit.
7. Reconcile or push the tag.
8. Reconcile or create the provider release when supported.

Each step persists its identifier before continuing. A conflicting version, changelog digest, tag target, or provider release target blocks; no existing release artifact is overwritten or deleted.

## Approval Binding

The production prompt must display:

- PR number/URL and full current head SHA
- Required-check names and successful status for that SHA
- Preview URL and deployment evidence for that SHA
- `uat-plan.md` path and digest
- Material warnings and known limitations
- Recommended SemVer bump, resulting version, changelog summary, and release effects
- A statement that approval authorizes protected merge and the recommended methodology release for exactly that SHA

Approval persistence happens before merge. The orchestrator then performs a fresh `getPullRequest`, `listRequiredChecks`, and `findPreview`. If any observed head differs from `approvedPrHeadSha`, it:

1. Sets approval status to `invalidated`.
2. Records `invalidatedAt` and the changed-head reason.
3. Appends a recommendation-log invalidation entry.
4. Clears stale checks and preview evidence.
5. Returns to `waiting_ci`.

Approval is never inferred from silence, prior generic consent, contract lock, commit-plan approval, provider review approval, or a previous SHA's approval.

## Resume and Reconciliation

Resume is a read-only phase until all applicable facts are compared.

### Reconciliation Order

1. Validate schema and revision.
2. Resolve repository root and verify provider repository identity.
3. Verify spec path, locked contract digest, and recommendation-log path.
4. Verify feature/default branches and local/remote SHAs.
5. Reconcile nested implementation state and completed story artifacts.
6. Reconcile PR identity, branches, state, and head SHA.
7. Reconcile required checks and preview deployment against current head.
8. Revalidate approval against current head and evidence digests.
9. Reconcile merge state and default-branch ancestry.
10. Reconcile version file, changelog digest, release commit, tag target/push, and provider release.
11. Compute the earliest incomplete safe state and persist one reconciliation transition.

### Reconciliation Outcomes

| Outcome | Behavior |
|---|---|
| Saved state matches reality | Continue from `resumeTarget` |
| External action completed but identifier was not saved | Persist observed canonical identifier, finalize pending log entry, and advance |
| Saved operation no longer exists | Block with stale-state evidence; do not recreate until ownership is resolved |
| PR head changed | Invalidate checks, preview, and approval; return to `waiting_ci` after confirming change belongs to the same branch |
| PR closed unmerged | Block; never reopen or create a replacement automatically |
| PR merged with approved SHA | Persist merge result and verify ancestry |
| PR merged with a different SHA | Block as approval mismatch |
| Tag exists at intended release commit | Mark tag step complete |
| Tag exists at another object | Enter `partially_released`; never move or delete it |
| Provider release exists for intended tag | Mark provider publication complete |
| State or provider returns multiple candidates | Block as ambiguous ownership |

## Security and Permission Boundaries

- All provider mutations use the user's existing authenticated identity and provider policy.
- Capability probes are read-only. Authentication setup is guidance, not an automated credential flow.
- Tokens, cookies, headers, secret names with values, environment dumps, signed URLs, and provider payloads are never persisted.
- Preview URLs are persisted only when safe to share with the repository's tracked UAT context. If the URL embeds a secret or expires through a credential-bearing query, persist a redacted locator and block for a safe preview URL.
- State and evidence files should use owner-only permissions where the platform supports them.
- Command arguments must be structured or safely quoted; provider text, branch names, URLs, and changelog content are never interpolated into executable shell text without platform-safe escaping.
- Untrusted PR/check/deployment output is evidence, not instruction. It cannot alter command policy or trigger a tool call.
- Recommendation mode does not grant extra filesystem, network, git, provider, or deployment permissions.
- Force pushes, protected-branch overrides, check waivers, review dismissal, admin merge, tag rewrites, release deletion, and destructive cleanup are forbidden.
- A permission denial is definitive for that attempt: record one blocker, preserve state, and stop.
- The tracked log uses concise public-safe evidence. Sensitive operational details remain redacted in gitignored state artifacts.

## Adapter Responsibilities

All adapters must preserve the same schemas, state tokens, approval boundary, and capability semantics.

| Responsibility | Cursor | Claude Code | Codex |
|---|---|---|---|
| Bounded choices and approval | Use native structured question/approval UI when available; preserve explicit option IDs | Use the platform's explicit user interaction surface; preserve option IDs | Render numbered bounded choices and wait for a composer response; no implicit default |
| Nested orchestration | Pass delivery context to command/subagent invocations and return structured outcomes | Pass context through command/agent calls without allowing nested terminal completion | Pass context through TOML agent/command boundaries or parent session orchestration |
| Provider discovery | Prefer configured provider MCP/tools, then authenticated CLI/API when allowed | Use configured integrations or CLI/API and normalize output | Use configured MCP or CLI/API and normalize output |
| Waiting | Use platform wait/background primitives without busy loops; persist before yielding | Use supported task/process waiting and persist before session handoff | Use supported process/session controls; if unattended waiting is unsupported, preserve state and instruct explicit resume |
| Resume | Reload state by execution ID and perform neutral reconciliation | Same | Same |
| Permissions | Respect IDE/tool approval and provider policy | Respect sandbox and permission modes | Respect sandbox/approval presets; read-only probes must remain read-only |
| Atomic state write | Use filesystem tools that replace validated content safely | Use safe temporary-write/rename support | Use safe temporary-write/rename support |

Adapter documentation must name the concrete mapping for every provider operation or mark it unavailable with setup guidance. An adapter may not claim semantic support merely because a generic shell exists. Browser automation is not a default provider adapter and must not be used to bypass absent PR, check, preview, merge, or release capabilities.

## Configuration Additions

Add the following optional keys to `.writ/docs/config-format.md` and `.writ/config.md` conventions:

| Key | Example | Purpose | Detection / Failure Rule |
|---|---|---|---|
| `Delivery Provider` | `github` | Select PR/check/merge/release provider mapping | Detect from canonical remote; ambiguity blocks |
| `Delivery Remote` | `origin` | Remote used for branch and tag pushes | Default to existing `origin` only when unambiguous |
| `Preview Provider` | `vercel` | Select existing preview metadata mapping | Detect only from existing project integration; no provisioning |
| `Preview URL Pattern` | `https://*.example.dev` | Validate discovered preview URLs when provider metadata is indirect | Pattern narrows discovery; it cannot fabricate a URL |
| `Preview Evidence Source` | `deployment-status` | Provider deployment, check output, or project convention used to bind preview to SHA | Unsupported source blocks |
| `Required Checks` | `eval, integration` | Optional project-required names in addition to provider-required checks | Never removes provider-required checks |
| `CI Wait Timeout` | `30m` | Maximum one-session wait before resumable timeout | Timeout preserves `waiting_ci` |
| `Preview Wait Timeout` | `20m` | Maximum one-session preview wait | Timeout preserves `discovering_preview` |
| `Merge Strategy` | `squash` | Existing key; now constrained by provider-permitted strategies | Unsupported strategy blocks; no automatic strategy hopping |
| `Release Provider` | `github` | Provider release publisher | `none` is valid only when provider releases are intentionally unsupported |
| `Release Tag Prefix` | `v` | Tag lookup and creation convention | Existing matching tags are authoritative |

Configuration values are never silently overwritten. Recommendation mode may use a detected value for the current execution and log its evidence, but saving a newly detected convention still follows the config file's explicit-consent rule. The resolved capability snapshot is persisted in execution state so resume can detect configuration drift.

## Story Traceability

| Story | Technical Ownership | Required Evidence |
|---|---|---|
| Story 1 — Governance and autonomy policy | Ownership matrix, core invariants, explicit production boundary, exclusions, security/permission boundaries | Superseding ADR and reconciled Phase 6 artifacts agree that one SHA-bound approval gates production |
| Story 2 — Recommendation semantics | Recommendation log schema, selection classifications, mode propagation, unsupported combinations | Fixtures prove `(Recommended)` labeling, evidence-based choice, reversible tie-break, and pause taxonomy |
| Story 3 — Autonomous spec-to-implementation orchestration | Execution identity, state schema, planning through verification transitions, nested result contract, resume reconciliation | Interrupted implementation resumes without regenerating contract or duplicating completed work |
| Story 4 — PR preview and staged UAT | Provider PR/check/preview capabilities, CI/preview transitions, UAT generation, approval binding | PR/check/deployment identifiers all bind to one head SHA and missing preview blocks safely |
| Story 5 — Merge and release completion | Protected merge contract, release sub-state order, partial-release recovery, final completion criteria | Duplicate-prevention fixtures cover merge, release commit, tag, tag push, and provider release |

## Test and Evaluation Strategy

### Layers

1. **Schema fixtures:** Valid state, each missing required field, invalid enum, stale revision, unknown compatible field, unsupported schema version.
2. **Pure transition fixtures:** Every allowed transition, every forbidden transition, blocker classification, approval invalidation, and partial-release re-entry.
3. **Command contract evals:** Mode propagation and structured outcomes across create-spec, implement-spec, ship, create-uat-plan, and release.
4. **Provider contract fakes:** Deterministic fake providers for absent/existing/ambiguous PRs, pending/failed/successful checks, preview binding, policy denial, merge, and release.
5. **Disposable git integration:** Real branches, commits, tags, interrupted writes, ancestry checks, conflicts, and non-fast-forward remotes in a sandbox repository.
6. **Adapter parity evals:** Cursor, Claude Code, and Codex render equivalent choices, preserve IDs, persist before waiting, and stop on the same blockers.
7. **End-to-end fixture:** Issue → locked spec → five-story implementation fixture → PR → checks → preview → explicit approval → merge → release.

### Critical Assertions

- Critical state transitions, external mutation preflights, approval binding, and release idempotency have 100% scenario coverage.
- New executable helper code, if any, meets at least 80% line/branch coverage; markdown-only behavior is validated through `scripts/eval.sh` fixtures.
- Controlled interruption occurs once before and once after every external mutation. Resume produces no duplicate PR, merge, release commit, tag, push, or provider release.
- Approval tests use SHA A, then move the PR to SHA B and prove merge cannot occur until checks, preview, UAT evidence, and approval are refreshed for B.
- Provider-required check discovery failure is not treated as zero required checks.
- Missing preview integration leaves the PR open and emits setup guidance without provisioning anything.
- Authentication, authorization, branch-protection, and required-review failures produce one blocker and no workaround attempt.
- Recommendation-log snapshots contain all required fields and no prompts, secrets, transcripts, or chain-of-thought.
- Normal mode remains backward compatible except for consistent `(Recommended)` labels.
- Eval search asserts no recommended path invokes `npm publish`, `--admin`, force push, check bypass, tag deletion, multi-spec phase mode, or staging provisioning.

### Completion Fixture Evidence

The golden end-to-end fixture must retain:

- execution state and transition history
- tracked recommendation log
- locked contract digest
- implementation and `/ship --test` evidence
- PR provider ID/URL and approved head SHA
- required-check IDs and evidence URL
- preview deployment ID/URL bound to the same SHA
- UAT plan digest
- explicit approval interaction ID
- merge operation ID and merge commit ancestry proof
- version, changelog digest, release commit, tag object, tag push evidence, and provider release URL when supported

## Error & Rescue Map

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| Parse recommended invocation | Unsupported flag combination or multiple specs | Fail before mutation with valid single-spec invocation guidance | Invocation matrix for every accepted and rejected modifier |
| Create execution state | ID collision, unwritable state directory, partial write | Generate collision suffix; otherwise stop before work; use validated atomic replacement | Collision fixture, read-only directory, kill before rename |
| Load state | Malformed JSON, unsupported version, stale writer revision | Preserve file and block with schema/revision diagnostic | Corrupt, future-version, and concurrent-writer fixtures |
| Resolve execution on resume | Zero or multiple active candidates | Require explicit execution ID; make no mutation | Empty and ambiguous state inventories |
| Validate locked contract | Missing package, structural error, digest mismatch | Block before implementation; never silently regenerate existing contract | Missing file, malformed story, edited contract fixtures |
| Append recommendation entry | File conflict, duplicate ID, interrupted pending entry | Re-read, choose next stable ID, atomic edit; reconcile pending result before action | Concurrent edit and crash-after-pending fixtures |
| Select recommendation | Evidence absent or critical ambiguity | Pause with missing evidence and bounded choices; resume with mode intact | Safety and no-defensible-choice fixtures |
| Propagate mode | Missing/mismatched context or nested command clears mode | Reject nested result and block as contract error | Context mutation fixtures per nested command |
| Execute story plan | Story/review/test/docs failure | Use existing bounded repair; persist story outcome; block dependents as applicable | Failure at each implementation gate |
| Run integration verification | Typecheck/test command fails or tool unavailable | Failed configured check blocks; absent unconfigured tool is recorded per standard gate rules | Failing suite and absent-tool fixtures |
| Group and create commits | Dirty unrelated files, staging mismatch, commit hook failure | Block ownership ambiguity; preserve hook changes; retry from observed git state | Dirty tree, hook mutation, interrupted commit fixtures |
| Push feature branch | Auth failure, non-fast-forward, wrong remote | Report once and stop; never force push; require remote reconciliation | Fake auth denial and diverged remote |
| Find existing PR | Multiple matches or saved ID points to another branch/repo | Block contradictory ownership; do not create another PR | Ambiguous and mismatched PR fixtures |
| Create PR | Timeout after provider accepted request | Re-run lookup by repository/base/head before retry; adopt one matching PR | Lost-response fake with created PR |
| Discover required checks | Provider cannot identify requirements or returns unknown states | Block as capability failure; never interpret as empty/success | Unavailable, empty-explicit, and unknown-status fakes |
| Wait for CI | Pending timeout, failed/cancelled check, check set changes | Persist resumable wait; failed/cancelled blocks repair; re-evaluate changed set | Timeout, failure, cancellation, late-added check |
| Discover preview | No integration, timeout, stale deployment, unsafe URL | Keep PR open; provide setup guidance; require same-SHA safe URL | Missing provider, stale SHA, signed-URL, timeout fixtures |
| Generate UAT plan | Missing source map, write failure, stale implementation evidence | Block approval; regenerate only after sources are complete and writable | Missing technical spec, read-only path, stale digest |
| Record approval | Inactivity, duplicate event, missing actor/event ID | Inactivity remains waiting; dedupe event; generate local ID only for explicit action | Silence, double-submit, platform-without-ID fixtures |
| Revalidate approved SHA | PR head/check/preview changed after approval | Invalidate approval, clear stale evidence, return to CI | Push SHA B after approving SHA A |
| Merge PR | Conflict, policy denial, required review, timeout, already merged | Query first; adopt matching merge; otherwise block without bypass or strategy hopping | Policy, conflict, lost-response, already-merged fakes |
| Verify default-branch ancestry | Merge commit absent or remote stale | Fetch and recheck once; block if still absent | Delayed remote and wrong-commit fixtures |
| Select SemVer | Conflicting breaking/feature evidence or no releasable change | Apply documented precedence; pause only for core ambiguity; log evidence | Major/minor/patch and contradictory evidence fixtures |
| Run release gate | Build, test, or spec validation blocks | Stop before version/changelog mutation and preserve merged state | Failure at each gate stage |
| Update changelog/version | Dirty tree, conflicting version, interrupted write | Reconcile exact expected content; block mismatch; atomic file edits where supported | Dirty tree and half-written files |
| Create release commit | Commit exists, hook failure, unrelated changes | Adopt exact matching commit; otherwise preserve changes and block | Lost-response, hook, mixed-diff fixtures |
| Create tag | Existing matching tag, existing conflicting tag, signing failure | Adopt matching tag; conflicting tag enters partial release; never move/delete | Matching/conflicting tag and signing failure |
| Push release commit/tag | Auth failure, non-fast-forward, timeout after acceptance | Query remote refs; adopt match; block mismatch; never force | Lost-response and diverged remote fixtures |
| Create provider release | Unsupported capability, auth failure, timeout after creation, conflicting release | Unsupported is recorded completion; otherwise lookup by immutable tag before retry; conflicts partially release | Unsupported, auth, lost-response, wrong-tag fakes |
| Persist evidence | Secret-bearing output or oversized provider payload | Redact and summarize; store only bounded safe artifact; block unsafe preview locator | Secret canary and payload-size fixtures |
| Finalize execution | Required identifier missing or state/log disagree | Report blocked/partial, reconcile before claiming complete | Delete one identifier and alter log result |

No `[UNPLANNED]` operations remain.

## Shadow Paths

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| Start from `/create-spec --recommend` | Idea/source → locked package → implementation continues | No idea/source → bounded feature selection, then resume | Empty source artifact → validation error with valid input guidance | Source issue/prototype read failure → no stateful delivery mutation |
| Start from `/implement-spec --recommend` | Existing locked spec → implementation state | No spec argument → bounded single-spec selection | Spec has no remaining stories → verify existing completion, then delivery | Spec package unreadable → blocker with file path |
| Recommendation choice | Evidence → automatic selected option and log entry | No evidence → human answer required | Equivalent options → simplest reversible choice | Evidence source unavailable → pause rather than guess |
| Implementation | Stories complete → integration verification | Missing story result → structured contract blocker | Zero remaining stories → proceed from artifact verification | Agent/test failure → persisted bounded repair state |
| PR open | Matching branch PR found/created → URL shown | No provider repository ID → setup blocker | No prior PR → create exactly one | Provider timeout → lookup before retry |
| Required checks | Required set passes for head SHA → continue | Requirement discovery unavailable → blocker | Provider explicitly reports no required checks → continue with evidence | Failure/cancel/timeout → repair or resumable wait |
| Preview discovery | Same-SHA deployment URL → UAT | No preview capability → setup blocker | Provider reports no deployment → keep PR open and block | Provider error/timeout → resumable discovery state |
| Production approval | User approves displayed SHA/evidence → merge | No explicit action → remain awaiting approval | User rejects without notes → return to implementation with rejection record | Interaction surface fails → preserve awaiting state |
| Protected merge | Approved SHA merges under policy → ancestry verified | Missing approval event → merge forbidden | Merge already completed for approved SHA → adopt result | Conflict/protection/auth error → block without bypass |
| Release | Gate → version/changelog/commit/tag/release → complete | No version source → standard release creates supported source per existing rules | Provider release unsupported → complete with local/tag release evidence | Failure after merge → partially released, exact-step resume |
| Resume | Reconcile all identifiers → earliest safe incomplete state | No state ID and no unique candidate → request ID | Already complete → report durable links, no mutations | Contradiction → blocker; never infer or duplicate |

## Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| User invokes the same recommended flow twice | Resolve unique active execution by spec/branch and resume it; ambiguous executions require explicit ID |
| User double-submits production approval | Deduplicate by interaction ID; only one merge operation key is used |
| User approves, then pushes another commit | Invalidate approval and all SHA-bound CI/preview evidence; return to waiting CI |
| Bot or provider updates the PR branch after approval | Treat exactly like any head change; provenance does not preserve approval |
| User requests changes at approval | Return to implementation with recommend mode intact; preserve PR identity and append rejection result |
| Session closes while waiting | Persist wait target and timestamps before yielding; explicit resume reconciles current provider state |
| Session closes after provider accepted a mutation but before state write | Lookup by deterministic target and adopt the single matching result |
| Back button or repeated prompt exposes an old approval card | Reject events whose displayed SHA or interaction ID is not current |
| State file is manually edited during a run | Revision mismatch stops the stale writer; next resume validates the edited document |
| Recommendation log has a merge conflict | Stop before the next mutation; never discard either tracked audit history |
| Feature branch is renamed | Block identity mismatch until the user explicitly reconciles state and provider branch |
| PR is manually closed | Block; do not reopen or replace automatically |
| PR is manually merged while awaiting approval | If no valid SHA-bound Writ approval exists, report external policy-boundary violation and do not release automatically |
| Required checks are added after initial success | Fresh pre-merge lookup must include them; approval becomes invalid if evidence set is stale |
| Preview URL redirects to authentication or expires | Approval blocks until a usable preview or explicit existing-project access guidance is available |
| Preview URL contains credential material | Redact, do not track it, and block for a safe provider locator |
| Provider reports merge success before default branch is fetchable | Persist merge result, retry one read-only fetch, then block with ancestry resume target |
| Merge strategy configured but disallowed | Block with allowed strategies; do not switch automatically after approval because merge consequences changed |
| Existing release tag matches version but not release commit | Enter partial-release blocker; never move or delete the tag |
| Provider release exists as draft | Reconcile provider state; publish only if the approved release operation explicitly targets draft finalization and policy permits it |
| Normal mode is invoked after a recommended run | Normal behavior remains interactive; it may inspect state but must not silently continue recommended delivery |
| Multi-spec phase command receives `--recommend` | Fail before mutation with single-spec invocation guidance |
| User asks to bypass protection or publish npm package mid-run | Refuse the out-of-scope/forbidden action, preserve state, and report the supported manual boundary |

## Completion Criteria

The orchestrator may set `complete` only when:

1. The spec and all stories are complete and structurally valid.
2. Integration and `/ship --test` evidence passed.
3. The PR was merged for the explicitly approved head SHA.
4. The merge commit is present on the fetched default branch.
5. The standard release gate passed.
6. Version and changelog changes match their logged recommendation.
7. The release commit and immutable tag exist and are pushed.
8. A provider release exists when the provider reports support, or unsupported capability is explicitly recorded.
9. Recommendation-log pending entries are finalized.
10. The final report links the spec, recommendation log, PR, preview evidence, UAT plan, merge commit, tag, and provider release when present.
