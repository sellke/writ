# Recommended Delivery State Format

This document is authoritative for the single-spec runtime and audit contracts
used by `/create-spec --recommend` and `/implement-spec --recommend`. Story 3
owns planning through verified implementation; Story 4 activates the same v1
state through durable `production_approved`. Story 5 remains the only owner of
merge, release, and overall completion.

## Runtime File and Write Protocol

Canonical runtime state uses schema `recommend-execution-v1` at:

```text
.writ/state/recommend-execution-{execution-id}.json
```

- The execution ID is opaque, filesystem-safe, and generated once.
- Initial creation uses exclusive-create semantics. A collision returns
  `state_collision` before any other mutation; a later start attempt must use a
  different opaque execution ID.
- Each update re-reads the file and rejects a stale expected revision.
- Validate the complete next document, write a sibling temporary file, flush
  file data, and atomically rename it over the canonical path.
- `revision` increases by exactly one per successful replacement.
- Compatible readers and writers preserve unknown fields recursively.
- An unsupported major schema version blocks before mutation; never downgrade,
  rewrite, or partially interpret it.
- State and evidence are gitignored and contain no secrets, provider payloads,
  prompts, transcripts, or private chain-of-thought.

## `recommend-execution-v1`

All top-level keys are required. Unavailable scalar values use `null`; lists and
maps use empty collections. SHA values are lowercase full-length hashes.

```json
{
  "schema": "recommend-execution-v1",
  "schemaVersion": 1,
  "executionId": "opaque-id",
  "revision": 1,
  "createdAt": "2026-07-10T15:00:00Z",
  "updatedAt": "2026-07-10T15:00:00Z",
  "entrypoint": {
    "command": "create-spec",
    "sourceMode": "standard",
    "recommend": true,
    "resumeRequested": false
  },
  "spec": {
    "id": "2026-07-10-feature",
    "path": ".writ/specs/2026-07-10-feature",
    "packageManifest": {
      "schema": "recommend-package-manifest-v1",
      "specPath": ".writ/specs/2026-07-10-feature",
      "artifacts": [{
        "path": ".writ/specs/2026-07-10-feature/spec.md",
        "immutableProjectionSha256": "lowercase-hex",
        "byteSha256AtLock": "lowercase-hex",
        "projectionRule": "spec-contract-v1"
      }],
      "validation": {
        "contractLocked": true,
        "requiredFilesPresent": true,
        "storiesParseable": true,
        "acceptanceCriteriaValid": true,
        "tasksValid": true,
        "dagAcyclic": true,
        "readmeConsistent": true,
        "unresolvedUnplannedCount": 0
      },
      "digestSha256": "lowercase-hex"
    },
    "packageManifestSha256": "lowercase-hex",
    "recommendationLog": {
      "path": ".writ/specs/2026-07-10-feature/recommendation-log.md",
      "revision": 1,
      "digestSha256": "lowercase-hex",
      "entryIds": ["REC-001"],
      "entryDigests": {
        "REC-001": "lowercase-hex"
      },
      "pendingEntryIds": [],
      "lastReconciledAt": "2026-07-10T15:00:00Z"
    },
    "specLiteAmendments": {
      "path": ".writ/specs/2026-07-10-feature/spec-lite.md",
      "baselineSha256": "lowercase-hex",
      "currentSha256": "lowercase-hex",
      "driftLogPath": ".writ/specs/2026-07-10-feature/drift-log.md",
      "baselineDriftEntryIds": [],
      "baselineDriftEntryDigests": {},
      "amendments": [{
        "devId": "DEV-001",
        "priorSha256": "lowercase-hex",
        "resultingSha256": "lowercase-hex",
        "storyId": "story-3",
        "path": ".writ/specs/2026-07-10-feature/spec-lite.md",
        "driftEntrySha256": "lowercase-hex",
        "reviewResult": {
          "schema": "recommend-spec-lite-review-v1",
          "execution_id": "opaque-id",
          "story_id": "story-3",
          "outcome": "passed",
          "drift_severity": "small",
          "dev_ids": ["DEV-001"],
          "summary": "Small drift accepted by Gate 3.5."
        },
        "reviewResultSha256": "lowercase-hex",
        "recordedAt": "2026-07-10T15:10:00Z"
      }]
    }
  },
  "repository": {
    "rootIdentity": "canonical-repository-identity",
    "remoteName": "origin-or-null",
    "remoteIdentity": "canonical-remote-or-null",
    "featureBranch": "feature-branch",
    "startingHeadSha": "full-object-id",
    "currentHeadSha": "full-object-id",
    "ownedPathWorktreeSnapshot": {
      "capturedAt": "2026-07-10T15:00:00Z",
      "headSha": "full-object-id",
      "entries": []
    }
  },
  "worktrees": {
    "story-3::delegate-a1::owner-t1": {
      "storyId": "story-3",
      "delegatedExecutionId": "delegate-a1",
      "ownershipToken": "owner-t1",
      "path": "/absolute/linked-worktree/path",
      "branchRef": "refs/heads/writ/story-3",
      "headSha": "full-object-id",
      "launchMode": "linked_worktree",
      "parentExecutionId": "opaque-id",
      "resultDigestSha256": null,
      "status": "reserved",
      "activeGate": "launch",
      "activeStoryId": "story-3",
      "startingSha": "full-object-id",
      "currentSha": "full-object-id",
      "adoptionState": "not_required",
      "adoptionEvidence": {
        "adoptedAt": null,
        "path": null,
        "headSha": null
      },
      "mergeEvidence": {
        "status": "not_started",
        "sourceHeadSha": null,
        "targetHeadSha": null,
        "resultDigestSha256": null,
        "observedAt": null
      },
      "reservedAt": "2026-07-10T15:00:00Z",
      "updatedAt": "2026-07-10T15:00:00Z"
    }
  },
  "mode": {
    "name": "recommend",
    "propagationToken": "opaque-non-secret-token",
    "returnContract": "recommend-command-result-v1"
  },
  "status": "implementing",
  "resumeTarget": "implementing",
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
  "requiredAnswer": {
    "active": false,
    "decisionId": null,
    "questionId": null,
    "optionIds": [],
    "selectedOptionId": null,
    "resumeTransition": null,
    "interactionId": null
  },
  "storyExecution": {
    "executionStatePath": null,
    "planDigest": null,
    "baselineCompletedStoryIds": [],
    "completedStoryIds": [],
    "activeStoryIds": [],
    "failedStoryIds": [],
    "storyResults": {},
    "integrationVerification": {
      "status": "not_started",
      "headSha": null,
      "packageManifestSha256": null,
      "planDigest": null,
      "completedStoryIds": [],
      "command": null,
      "exitCode": null,
      "completedAt": null,
      "evidenceSummary": null,
      "evidenceArtifact": null,
      "evidenceArtifactSha256": null
    }
  },
  "delivery": {
    "pr": null,
    "checks": [],
    "preview": null,
    "approval": null,
    "merge": null,
    "release": null
  },
  "transitions": []
}
```

Active v1 status values through Story 4 are `planning`, `implementing`,
`verifying`, `committing`, `opening_pr`, `pr_open`, `waiting_ci`,
`discovering_preview`, `preview_ready`, `awaiting_approval`,
`production_approved`, and `blocked`. `verified_implementation` remains a nested
result value. Every transition records a monotonic sequence, from/to,
timestamps, outcome, concise evidence, and persisted identifiers.

### Active and Reserved Fields

Story 3 owns execution identity, spec/package identity, repository snapshot,
mode, blocker/required-answer data, story execution, integration verification,
and planning/implementation/verifying transitions.

`delivery.pr`, `delivery.checks`, `delivery.preview`, `delivery.uat`, and
`delivery.approval` are activated only after verified implementation by Story 4.
`delivery.merge` and `delivery.release` remain inert for Story 5. Story 3 still
performs no provider, PR, check, preview, UAT, approval, merge, release, or
publication probe or mutation.

### Story 4 Staging Activation

Story 4 adds compatible v1 fields; it does not create a second state machine.
`delivery.capabilitySnapshot` binds provider, provider repository ID, delivery
remote/source, base/feature branches, full head SHA, capability results, and the
resolved configuration snapshot. `delivery.operations` records deterministic
operation keys and pending/observed canonical provider IDs. `delivery.test`,
`delivery.commits`, `delivery.pr`, `delivery.checks`, `delivery.checksEvidence`,
`delivery.preview`, `delivery.uat`, and `delivery.approval` all bind to the same
full PR head SHA.

The local helper accepts only normalized evidence through explicit operations:

```text
activate-staging       activate verified implementation with capability/config evidence
record-ship            persist mandatory test and evidence-based commit grouping
record-pr-lookup       reduce findPullRequest cardinality and authorize at most one create
mark-pr-create-attempt persist the attempted marker before the sole provider mutation
record-pr-created      persist an observed createPullRequest result
finalize-pr-audit      verify canonical finalized audit and enter waiting_ci
record-checks          reduce listRequiredChecks evidence and durable waits
record-preview         reduce findPreview evidence without provisioning
derive-uat             generate canonical UAT bytes from completed implementation sources
record-uat             verify source paths/digests, canonical bytes, enrichment, and head
record-approval        persist silence, rejection, deduplicated, or explicit approval
revalidate-staging     invalidate SHA-bound evidence when getPullRequest reports a new head
```

The helper performs no network, provider, browser, deployment, merge, or release
operation. Adapters perform the neutral provider operations and write bounded
normalized evidence files under `.writ/state/`; untrusted provider output never
becomes executable input.

Before `createPullRequest`, derive the operation key from provider repository
ID, base branch, and head branch; caller-supplied arbitrary keys are invalid.
Persist a Pending recommendation entry containing that exact key, reconcile its
path/digest/entry identity into state, then run `findPullRequest`. An absent
lookup may create one `authorized` marker only. Persist `attempted` through
`mark-pr-create-attempt` before the sole provider mutation. Observe and persist
`created`, `adopted`, or `reconciled` plus canonical provider IDs and enter
`pr_open`. Finalize the exact entry with provider ID, number, URL, outcome, and
operation key, reconcile the log, then call `finalize-pr-audit` to enter
`waiting_ci`. Every later staging reducer verifies zero unresolved
mutation-related audits. Unrelated Pending decision entries follow ordinary
decision policy but contain no mutation operation key and cannot authorize one.
Repeated absence after authorization/attempt blocks; a lost response
always re-enters lookup and may adopt one exact PR. Missing audit linkage,
multiple, mismatched, or closed matches block.
A lost response always re-enters lookup.

`record-ship` accepts no marker-only success. Its safe repo-local evidence
artifact is structured JSON containing the nonempty command, exit code zero,
passed status, and full current head SHA; exact bytes must match the supplied
SHA-256. Every listed commit exists in the canonical repository, each is an
ancestor of the next, and the final commit equals both git `HEAD` and persisted
current head. `single` has one commit; `split` has at least two. `decisionId`
equals finalized `auditEntryId`, whose Decision/Result contains the matching
strategy, ordered SHAs, head, and deterministic ship operation. Unrelated or
nonexistent SHAs and unbound IDs block.

Required checks are provider-required plus configured additive names. Evidence
records provider/repository identity, query timestamp, full head SHA, stable
provider-required IDs/names and canonical set digest, or an explicit provider
zero-required declaration. Normalized evidence explicitly states
`authenticated: true` and includes the concrete `listRequiredChecks` query
operation ID/provider/repository/head/start/completion. Missing or false
authentication blocks; caller success does not imply it. Config checks are separately classified and cannot
substitute for provider discovery. A successful terminal set advances only
after an explicit complete-set re-query (`querySequence >= 2`); this captures
late-added requirements. Discovery unavailable, authentication required, and
authorization denied remain distinct blockers. Pending, timeout, and
interruption preserve `waiting_ci`; failed, cancelled, or unknown block.

Preview evidence must match the normalized preview provider, evidence source,
provider repository ID, project ID, and URL convention in the immutable
capability/config snapshot. Observable provenance contains integration ID,
provenance kind, observation time, repository/project identities, and full head
SHA. URL-pattern-only evidence is insufficient. The URL must be safe shareable
HTTPS and match the optional pattern. Missing integration, fabricated or
unconfigured provenance, stale SHA, unsafe URL, timeout, authentication,
authorization, and provider errors leave the PR open with setup/resume guidance.
Configured source and provenance kind must match:
`deployment-status → provider-deployment|provider-status`,
`check-output → provider-check`, and
`project-convention → project-convention`.

`derive-uat` reads actual completed story bytes, checked Given/When/Then
acceptance criteria, Context for Agents error/shadow references, What Was Built,
and technical Error & Rescue Map, Shadow Paths, and Interaction Edge Cases. It
sorts canonical source path/digest records and scenarios, then renders PR,
check, preview/provenance, validation instructions, warnings, proposed version,
and release consequences. `record-uat` re-derives and requires exact source
paths/digests, source digest, generated bytes/digest, enriched headings, and
current SHA. Arbitrary files and invented digests block; any source change
changes output and invalidates prior evidence.

Approval requires a stable interaction/event ID, persisted recommendation-log
entry bound to its deterministic operation key, and a fresh same-operation
reconciliation envelope immediately before approval. The envelope must match
the exact pre-event state revision/digest, capability/config snapshot digest,
current PR record/head, complete
required-set digest/IDs and successful statuses, preview provider/project/
provenance/status, and UAT digest. All timestamps are strict UTC RFC3339 seconds.
One reconciliation attempt ID binds PR/check/preview/UAT observations to the
same state revision/head. Presentation starts after latest persisted evidence;
observations follow presentation; approval follows observations. Evidence must
be no older than the smaller configured wait window or five minutes and no more
than 30 seconds in the future. Cached or stale year-2000 fields never approve. Silence
does not mutate; rejection returns to `implementing`; duplicate event IDs
deduplicate. A head change clears checks, preview, and UAT, invalidates approval,
and returns to `waiting_ci`.
Cached fields alone never approve.

## Package Manifest

`package_manifest` is the immutable identity of the locked planning artifacts
that implementation consumes. It deliberately excludes mutable runtime audit
history. Its canonical JSON form is:

```json
{
  "schema": "recommend-package-manifest-v1",
  "specPath": ".writ/specs/2026-07-10-feature",
  "artifacts": [
    {
      "path": ".writ/specs/2026-07-10-feature/spec.md",
      "immutableProjectionSha256": "lowercase-hex",
      "byteSha256AtLock": "lowercase-hex",
      "projectionRule": "spec-contract-v1"
    }
  ],
  "validation": {
    "contractLocked": true,
    "requiredFilesPresent": true,
    "storiesParseable": true,
    "acceptanceCriteriaValid": true,
    "tasksValid": true,
    "dagAcyclic": true,
    "readmeConsistent": true,
    "unresolvedUnplannedCount": 0
  },
  "digestSha256": "lowercase-hex"
}
```

Required artifacts are:

1. `spec.md`
2. `spec-lite.md`
3. `user-stories/README.md`
4. every story indexed by that README
5. `sub-specs/technical-spec.md`

Additional sub-specs referenced by required artifacts join the required set.
Normalize paths as repo-relative POSIX paths, reject duplicate or escaping
paths, and sort lexicographically by path. `byteSha256AtLock` records initial
bytes for audit; immutable identity uses only each path, projection rule, and
`immutableProjectionSha256`. Reconciliation never substitutes freshly computed
byte hashes into the identity digest.

Projection rules are deterministic:

- `spec.md`: retain the locked contract and planning requirements; normalize
  mutable overall status/date progress fields.
- `spec-lite.md`: hash exact lock-time bytes. A later standard Gate 3.5 drift
  amendment is accepted only through an unbroken persisted before/after digest
  chain tied to its drift-log DEV ID; the immutable lock identity does not
  change.
- technical sub-specs: hash exact bytes because Story 3 does not authorize their
  rewrite.
- story files: normalize task/AC checkbox markers to unchecked, normalize the
  mutable Status line, and exclude the terminal `## What Was Built` section.
- `user-stories/README.md`: normalize mutable status/progress/count cells while
  retaining story IDs, links, titles, priorities, dependencies, and task totals.

Mutable completion fields may change only when corroborated by nested story
state and repository evidence. Any other change to an immutable projection
blocks. Serialize the manifest as canonical UTF-8 JSON with sorted object keys
and no insignificant whitespace; its SHA-256 is `package_manifest_sha256`.
The canonical digest projection omits `byteSha256AtLock` and mutable validation
evidence so authorized status, checkbox, README progress, and WWB updates do not
change identity. Semantic contract, task, acceptance-criteria, dependency, or
indexed-artifact changes still change an immutable projection and block.

`spec.specLiteAmendments` preserves the lock-time baseline, current digest,
canonical spec-lite/drift-log paths, baseline drift-log IDs/digests, and an
ordered amendment chain. Each amendment binds one unique appended `DEV-NNN`
and its exact entry digest, prior/resulting digest, story ID, timestamp,
allowed spec-lite-only path, and
the canonical digest of an embedded `recommend-spec-lite-review-v1` result.
That review identifies the same execution/story, includes the DEV ID, and
reports passed Small drift. The chain must be contiguous from baseline to the
current bytes. Missing, duplicated, rewritten, reordered, or unlogged DEV IDs;
an unrecorded byte change; a broken digest link; or mutation of any other
immutable artifact blocks.

Validation requires an explicit contract lock, all files, parseable unique story
IDs and statuses, 3–5 AC and 5–7 tasks per actionable story, resolvable acyclic
dependencies, README/story status and count agreement, and no unresolved
`[UNPLANNED]`. A mismatch blocks; a direct implementation entry never rewrites
the package. If the README contains `## Totals`, it must contain exactly one
`Stories`, `Acceptance criteria`, `Implementation tasks`, `Completed tasks`,
and `Overall progress` claim and no malformed or unknown claims. Values are
derived from indexed story facts; progress is whole-percent round-half-up.
Legacy indexes without `## Totals` remain valid.

`recommendation-log.md` is still a mandatory precondition before implementation,
but it is not an immutable manifest artifact. A legitimate recommendation append
therefore changes log integrity state without invalidating
`packageManifestSha256`.

## Recommendation Log Integrity

`spec.recommendationLog` independently links canonical runtime state to the
tracked mutable audit:

- `path` is the canonical repo-relative log path.
- `revision` increases by one for each authorized append or pending-result
  finalization persisted in state.
- `digestSha256` hashes the exact current log bytes.
- `entryIds` is the ordered stable identity list. Existing IDs may not be
  removed, reordered, reused, or silently renumbered.
- `entryDigests` binds each complete entry to its current authorized content.
- `pendingEntryIds` identifies entries whose operation/result requires
  reconciliation before any retry.
- `lastReconciledAt` records the latest successful comparison.

Before changing the log, re-read and verify its path, revision, whole-file
digest, ordered IDs, per-entry digests, and append-only prefix against state.
Append one complete uniquely identified entry, or finalize only the Result line
of an ID already listed in `pendingEntryIds`. Replace the log crash-safely, then
replace state with the new digest/revision/linkage. A crash between those writes
is represented by a valid append-only suffix and is adopted on reconciliation.
Persist the pending entry identity in state before its selected mutation.

On resume, a valid append-only suffix with unique IDs is adopted by recording
its entry IDs/digests and incremented log revision. A pending entry is reconciled
from repository/story evidence before its result is finalized or any operation
is retried. An unexpected rewrite, deletion, reorder, duplicate ID, changed
terminal entry, digest mismatch outside the permitted pending finalization, or
state/log linkage disagreement blocks as `recommendation_log_contradiction`.
The immutable package manifest remains unchanged throughout legitimate log
evolution.

## Owned Paths and Linked Worktree Identity

The `owned-path/worktree snapshot` binds implementation evidence without
claiming ownership of unrelated dirty work. Each sorted entry records a
repo-relative path, status code, content hash when readable, and whether the
path is package-owned, planned implementation-owned, or unrelated. Also record
the full HEAD SHA and branch.

Top-level `worktrees` is a map keyed by
`{storyId}::{delegatedExecutionId}::{ownershipToken}`. This cardinality permits
parallel DAG stories while making each delegated owner explicit. Every record
persists path, full branch/ref, launch HEAD (`headSha`), starting/current SHA,
active gate/story, launch mode, parent execution ID, status, adoption state,
ownership token, delegated execution ID, canonical result digest,
merge/adoption evidence, and reservation/update timestamps.

At most one `reserved`, `active`, or `adopted` record may own a story ID, path,
branch/ref, delegated execution ID, or ownership token. Different independent
stories may each own one record and execute in parallel. Duplicate ownership
blocks as `worktree_ownership_ambiguous`. `status` is `reserved`, `active`,
`adopted`, `integrated`, or `blocked`.
Every executed non-baseline story requires exactly one such pre-Gate-1 record;
absence is never a valid serialized fallback. `adoptionEvidence` records when
and by which identity fields an interrupted
worktree was adopted. `mergeEvidence` is repository-local worktree integration
evidence only—not PR merge behavior—and binds source/target HEADs plus the same
canonical successful story-result digest. Linked mode requires an exact
integrated linked-worktree record. Serial in-place mode additionally binds the
canonical repository root, saved branch/ref, launch/current HEADs, parent
execution, result, and integration evidence.

Completion rejects any tracked, staged, or untracked delegated-worktree change.
The exact observed worktree HEAD must contain at least one committed change
after its reserved starting SHA, and that exact commit must be an ancestor of
the canonical parent feature-branch HEAD. A committed but unintegrated branch,
an ambiguous parent target, stale identity, or marker-only claim blocks.
Ownership changes to `integrated` only after this evidence is observed and
persisted.

Resume enumerates linked git worktrees read-only for every active record and
matches canonical repository identity, persisted path, branch/ref, active story,
delegated execution/ownership token, and exact current HEAD. Exactly one match
per record is adopted and its evidence is persisted before work continues. Zero
matches for persisted active work blocks as `stranded_worktree_missing`;
multiple candidates or duplicate state ownership block as
`worktree_ownership_ambiguous`; mismatched path/ref/story/token blocks as
`worktree_identity_contradiction`; changed HEAD without nested transition
evidence blocks as `worktree_identity_stale`. Resume never launches a new agent
or worktree for persisted active work until reconciliation proves no owned work
is stranded.

The owned-path snapshot is then compared with current git and filesystem facts.
Unrelated dirty work is preserved. A changed owned path is acceptable only when
reconciled to the adopted active worktree, a completed story artifact, or the
active story's nested state; otherwise it is an ownership contradiction.

## Executable Validator and Reducer

`scripts/recommend-state.py` is the dependency-free Python 3 stdlib reference
implementation consumed by Story 3 and Story 4 commands:

```text
start              validate invocation + package, exclusively create state
validate-context   compare propagated delivery context with canonical state
reserve-worktree   validate a launch report and persist ownership before edits
record-spec-lite-amendment
                   persist one reviewed Gate 3.5 digest/DEV-ID amendment
reconcile          validate package/log/repository and adopt linked worktrees
complete-worktree  verify local ancestry and release active story ownership
normalize-result   fail-closed normalization to recommend-command-result-v1
activate-staging / record-ship / record-pr-lookup / mark-pr-create-attempt
record-pr-created / finalize-pr-audit / record-checks / record-preview / derive-uat / record-uat / record-approval
revalidate-staging explicit Story 4 normalized-evidence reducer operations
```

`scripts/install.sh`, `scripts/update.sh`, and `scripts/unlink.sh` distribute
and hash-track both this authoritative document and the reducer for Cursor,
Claude Code, and Codex installations. `.writ/manifest.yaml` and the generated
root catalog identify this file as the runtime contract.

Every operation returns one JSON object. Contract failures return exit code `2`
as a validated `recommend-command-result-v1` blocked result with a stable
blocker code and canonical empty `required_answer`. Invalid operations and
arguments never emit argparse usage text or tracebacks. State writes preserve
unknown fields, increment revision, and use sibling temporary-file replacement.
`start` in normal mode returns `no_recommended_state` and creates no state.

The helper is a repository methodology utility, not a publishing/runtime
package. It performs repository-only Story 3 behavior and local deterministic
Story 4 reduction. It has no network, provider, browser, deployment, merge, or
release capability. It fails closed when Python 3, identity, exact package
structure, normalized evidence, atomic replacement, or observable worktree
identity is unavailable. It does not infer provider state, recover secrets,
repair malformed packages, provision previews, or relaunch agents.

Install, update, and unlink place this helper at the project-root
`scripts/recommend-state.py` for Cursor, Claude Code, Codex, and generic command
consumers. It is executable, hash-tracked in the Writ installation manifest,
three-way updated, previewed by dry-run, and converted from symlink to copy with
the rest of a linked installation.

## Recommended Worktree Launch Handshake

Before Gate 1 can edit, an internally invoked `/implement-story` returns:

```yaml
schema: recommend-worktree-launch-v1
execution_id: string
story_id: string
delegated_execution_id: string
ownership_token: opaque-non-secret-token
path: absolute-path
branch_ref: refs/heads/name
head_sha: full-object-id
starting_sha: full-object-id
active_gate: launch
mode: linked_worktree | serial_in_place
```

The parent validates observable git identity and calls
`scripts/recommend-state.py reserve-worktree`. Only after durable state
replacement does it return `recommend-worktree-reservation-ack-v1` with the
canonical worktree key and persisted revision. The story must compare execution,
story, delegated execution, token, and key before entering Gate 1.

Platforms without stable linked-worktree path/ref/HEAD identity must not launch
recommended parallel stories. They may run a documented serial in-place mode
only one story at a time, using the repository root/ref/HEAD as the same
observable reservation handshake. If neither identity can be persisted, block
as `worktree_identity_unavailable`.

## Mode Transport

The parent creates and passes `delivery_context`:

```yaml
delivery_context:
  execution_id: string
  state_path: .writ/state/recommend-execution-{id}.json
  spec_path: repo-relative-path
  mode: recommend
  propagation_token: opaque-non-secret-token
  parent_command: create-spec | implement-spec
  return_contract: recommend-command-result-v1
  package_manifest_sha256: lowercase-hex
```

Every field is required. The receiver compares it with canonical state. Missing
or mismatched identity, path, mode, token, parent relationship, schema, or
manifest blocks. The token is non-secret correlation data and grants no
filesystem, git, network, or provider permission.

## Structured Command Result

Nested results and the direct `/implement-spec --recommend` outcome use
`recommend-command-result-v1`:

```yaml
schema: recommend-command-result-v1
execution_id: string
mode: recommend
command: string
status: succeeded | blocked | answer_required
completed_state: verified_implementation | production_approved | null
resume_state: planning | implementing | verifying | waiting_ci | discovering_preview | awaiting_approval | null
evidence:
  summary: string
  artifacts: [repo-relative-path]
identifiers: {}
required_answer:
  decision_id: string | null
  question_id: string | null
  option_ids: [string]
  selected_option_id: string | null
  resume_transition: string | null
  interaction_id: string | null
blocker:
  code: string | null
  summary: string | null
```

The implement-spec boundary may wrap an unchanged `/implement-story` report:
it validates observed gate output and constructs the canonical result before
persisting it. Thus `implement-story.md` need not become delivery-aware.
Malformed, missing, mismatched, or nested `failed` output becomes a classified
`blocked` result; it never becomes success by omission. One canonical result
validator/factory handles every path. `failed` always becomes
`nested_result_failed`; only `answer_required` may contain complete, stable,
non-empty answer identity. `succeeded` and `blocked` require the canonical empty
answer object. Malformed JSON, shape, identity, evidence, or answer data returns
a validated canonical blocked result rather than preserving untrusted fields.

An answer-required result persists the stable decision ID, stable question ID,
stable option IDs, mode, and exact resume transition before yielding. After an
answer, the parent records the selected stable identity, retains recommend mode,
and resumes that same transition without repeating the completed decision.

## Recommendation Log

Tracked audit history lives at `{spec}/recommendation-log.md`; runtime state does
not replace it. The file exists before implementation and begins with:

```markdown
# Recommendation Log: Feature Name

> **Spec:** `.writ/specs/.../spec.md`
> **Purpose:** Concise audit of recommended-delivery decisions
> **Privacy:** Decisions and evidence only; no private chain-of-thought or transcript content
```

Entries are append-ordered and never renumbered:

```markdown
## REC-001 — 2026-07-10T15:00:00Z — planning

- **Decision:** Concise selected action.
- **Evidence:** Observable repository or locked-artifact facts.
- **Alternatives:** Material bounded alternatives.
- **Risk:** Low — short impact.
- **Reversibility:** High — recovery boundary.
- **Selection:** Automatic (`evidence-supported`) | Human answer | Reconciliation.
- **Result:** Pending | Applied | Superseded | Invalidated | Blocked | Failed — identifier or transition.
```

Before a selected mutation, append the complete entry with a deterministic
operation key and `Pending` result. After observable reconciliation, replace
only that entry's Result line. Terminal entries are immutable; corrections
append a superseding entry. A pending entry is reconciled before retry.

## Repository-Only Reconciliation

Story 3 resume performs repository-only reconciliation and remains read-only
until every applicable check succeeds:

1. Validate JSON, schema major, required shape, and revision.
2. Resolve canonical repository root, branch/full ref, remote name, and
   credential-free normalized remote URL/identity. Detached HEAD or unexpected
   branch/remote drift blocks.
3. Verify full HEAD and owned-path snapshot.
4. Enumerate linked worktrees and adopt exactly one matching persisted active
   worktree, or block missing, ambiguous, or contradictory ownership.
5. Recompute the immutable package manifest; accept spec-lite projection drift
   only through the complete contiguous amendment and append-only DEV-ID chain.
6. Reconcile recommendation-log path, revision, digest, ordered entry identity,
   append-only prefix, entry digests, and pending entries independently.
7. Reconcile the nested ordinary execution state and plan digest without
   relaunching stranded active work.
8. Compare story files, statuses, checked tasks and AC, dependency completion,
   and recorded structured story results.
9. Bind integration evidence to current HEAD and immutable package digest.
10. Compute the earliest safe incomplete state, then persist one reconciliation
   transition.

Saved markers are hints only; story status, nested state, test evidence, and
current repository facts decide whether work is complete. Contradictory
identity, hashes, branch/HEAD, story completion, task/AC state, plan, or
integration evidence blocks. WWB incompleteness is warning-only because the
existing per-story pipeline explicitly permits partial What Was Built records.

`baselineCompletedStoryIds` is captured once from completed, fully checked story
bytes at lock time. On every reconciliation, `completedStoryIds` must exactly
equal unchanged baseline completion plus executed stories proven by a complete
indexed artifact, fully checked tasks and AC, completed dependencies, a
successful canonical story result, matching nested completed state, membership
in the canonical dependency-valid plan, and integrated worktree evidence when
reserved. The nested path must be an existing regular file inside
`.writ/state`, identify the same spec, and contain every non-baseline story
exactly once. `planDigest` is SHA-256 of canonical JSON for that plan.
Completed, active, failed, result, nested-status, and ownership-record sets must
agree. Every executed non-baseline completion requires exactly one integrated
ownership record whose parent execution and canonical result digest match.
Unexplained HEAD drift blocks; reconciliation never rewrites `currentHeadSha`
merely to make drift disappear.

A passed `integrationVerification` binds the exact current HEAD, immutable
package-manifest digest, plan digest, exact completed-story list, non-empty
command, integer `exitCode: 0`, completion time, summary, and a safe non-empty
regular artifact under `.writ/state/evidence/` whose bytes match
`evidenceArtifactSha256`.

Resume uses an explicit execution ID or exactly one nonterminal execution whose
canonical spec path and branch match. Zero or multiple matches require an
explicit ID and cause no mutation. Normal-mode commands never select this state.

## Compatibility and Versioning

- Schema names end in `-v{major}`. `schemaVersion` is the numeric major.
- Readers support only documented majors and block an unsupported major.
- Additive fields within a supported major are compatible and must survive
  read/replace cycles unchanged.
- Removing fields, changing meaning/types, changing canonical hashing, or
  broadening active transitions requires a new major.
- Missing required v1 fields are invalid, not defaulted during autonomous
  execution.
- A migration is a separately authorized operation; resume never migrates state
  implicitly.
- Recommendation-log entry syntax is append-compatible. Existing terminal
  entries are never rewritten for schema upgrades.
