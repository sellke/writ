# Implement Spec Command (implement-spec)

## Overview

End-to-end specification execution. Reads a spec, builds a dependency-aware execution plan with parallel batches, confirms with the user, then calls `/implement-story` for each story — sequenced correctly, uninterrupted.

This is the **top-level orchestrator**. It owns the plan. `/implement-story` owns the per-story pipeline.

## Invocation

| Invocation | Behavior |
|---|---|
| `/implement-spec` | Interactive — presents spec selection |
| `/implement-spec 2026-02-22-feature` | Executes named spec |
| `/implement-spec --from story-3` | Starts from story 3 onward |
| `/implement-spec --quick` | Passes `--quick` to each `/implement-story` call |
| `/implement-spec --resume` | Resumes from last saved execution state |
| `/implement-spec --recommend <spec>` | Runs one locked spec through verified implementation without routine confirmations |

## Entry Branching and Recommended Delivery

Parse `--recommend` exactly once at command entry. Store `recommend_mode` and
choose one branch before discovery, state lookup, or mutation.

**Normal branch (authoritative): when `--recommend` is absent, follow Phases 1–4 and Resume Support below verbatim.**
Normal mode never discovers or resumes `recommend-execution-*.json` state
implicitly. Its existing `--resume` behavior remains limited to ordinary
`execution-*.json` state.

### Authoritative `--recommend` Invocation Matrix

| Invocation | Result before mutation |
|---|---|
| `/implement-spec --recommend <one-spec>` | Supported direct entry for one existing locked package |
| Internal recommended call with one valid `delivery_context` | Supported propagated entry; do not reparse or mint another execution |
| `/implement-spec --recommend` with no spec | Supported only when exactly one locked spec is selected through a bounded stable-ID question before state creation |
| `/implement-spec --recommend --resume <execution-id>` | Supported explicit durable resume |
| `/implement-spec --recommend --resume <one-spec>` | Supported only when exactly one nonterminal state matches canonical spec path and branch |
| `/implement-spec --recommend --quick` | Reject: full story gates are mandatory |
| `/implement-spec --recommend --force` | Reject: saved/repository contradictions cannot be overwritten |
| `/implement-spec --recommend --from <story>` | Reject: partial-DAG entry is unsafe until completed/dependent artifacts are fully reconciled |
| `/implement-spec --recommend --resume` without ID or spec | Reject unless exactly one nonterminal execution exists for the current branch |
| `--recommend` with multiple spec arguments | Reject: one execution owns one spec |
| `/implement-phase --recommend` | Reject: multi-spec recommended execution is out of scope |
| `--recommend` with `--dry-run`, `--draft`, `--no-split`, `--skip-gate`, or `--no-tag` | Reject: unsupported later-stage modifiers |

Validate the entire row and print valid supported forms before any file write,
state creation, story launch, or source mutation.

### Recommended Entry Context

A direct `/implement-spec --recommend` entry generates one execution ID and
non-secret propagation token only after package preflight, then invokes
`python3 scripts/recommend-state.py start` with entry command `implement-spec`
to exclusively create canonical state and return context. A propagated entry
accepts the parent's `delivery_context` and validates it through
`scripts/recommend-state.py validate-context` before comparing every field:

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

Missing or mismatched execution ID, canonical state path, spec path, mode,
token, parent, return schema, or manifest digest blocks as
`delivery_context_mismatch`. Never silently create a second execution to repair
the mismatch.

### Complete Locked Package Preflight

Before implementation or canonical state creation, read and validate:

1. `spec.md` exists and declares `Contract Locked: ✅`.
2. `spec-lite.md`, `user-stories/README.md`,
   `sub-specs/technical-spec.md`, `recommendation-log.md`, and every story
   indexed by the README exist.
3. Every story has parseable identity, status, dependencies, 3–5 acceptance
   criteria, and 5–7 implementation tasks; completed prototype stories may use
   checked forms.
4. Dependencies resolve to one acyclic DAG and README IDs, status, task counts,
   and progress agree with story files.
5. If `user-stories/README.md` contains `## Totals`, it has exactly one
   `Stories`, `Acceptance criteria`, `Implementation tasks`, `Completed tasks`,
   and `Overall progress` claim, no malformed/unknown claims, and every value
   equals indexed story facts. Overall progress uses whole-percent
   round-half-up. Absence remains valid for legacy packages.
6. No unresolved `[UNPLANNED]` marker appears in required package artifacts.
7. A deterministic immutable `package_manifest` is built from lexicographically
   sorted locked planning artifact paths and lowercase SHA-256 identity hashes:
   `spec.md`, `spec-lite.md`, `user-stories/README.md`, indexed stories,
   `sub-specs/technical-spec.md`, and referenced planning sub-specs.
   `recommendation-log.md` is a required precondition but is excluded because
   its authorized append-only audit evolves during execution. Include validation
   evidence for contract lock, files, story parsing, AC/tasks, DAG, README
   consistency, and unresolved-marker absence. For mutable completion surfaces,
   hash the canonical planning projection defined in the state-format document:
   normalized status/progress/checkboxes and no WWB section. Retain the original
   byte hash separately for audit, then hash canonical UTF-8 manifest
   serialization as `package_manifest_sha256`.
8. Independently parse `recommendation-log.md`, verify unique ordered entry IDs
   and complete entry fields, and initialize or reconcile
   `spec.recommendationLog` with path, monotonic revision, current SHA-256,
   ordered entry IDs/digests, and pending entry IDs.

Failure returns a classified `blocked` result without regenerating, rewriting,
or silently repairing the locked package. Direct entry uses the package exactly
as found.

### Canonical State and Repository Snapshot

Use `.writ/docs/recommended-delivery-state-format.md` as authoritative. State
lives only at `.writ/state/recommend-execution-{id}.json`; exclusive creation
prevents collision. Each replacement re-reads the current revision, preserves
unknown fields, validates the complete document, increments `revision` once,
writes and flushes a sibling temporary file where supported, then atomically
renames it. Unsupported major schema versions, stale writers, invalid JSON, or
unavailable crash-safe replacement block before further mutation.

Capture repository root/remote identity, branch, full starting/current HEAD,
and an owned-path snapshot. Top-level `worktrees` is keyed by
`{storyId}::{delegatedExecutionId}::{ownershipToken}`. Each record persists path,
full branch/ref and launch HEAD, status, active gate/story, starting/current SHA,
launch mode, parent execution, canonical result digest, adoption state,
merge/adoption evidence, and timestamps. Parallel independent
stories may each own exactly one active record. Duplicate story, path, ref,
delegated execution, or token ownership blocks. Saved status markers are hints
rather than proof. Story 3 may set only `implementing`, `verifying`, or
`blocked`; fields reserved for PR, checks, preview, UAT/approval, merge, and
release remain inert null/false/empty values with future ownership.

### Read-Only Resume Reconciliation

Resume by explicit execution ID, or by exactly one nonterminal execution whose
canonical spec path and feature branch match. Zero or multiple matches block
with valid explicit-ID guidance. Reconciliation is read-only until all checks
finish:

1. Validate schema, supported major, JSON shape, and monotonic revision.
2. Verify repository root, canonical remote name/URL identity, feature
   branch/full ref, full HEAD, and owned-path snapshot; detached HEAD or
   unexpected branch/remote drift blocks and unrelated dirty work is preserved.
3. Run `python3 scripts/recommend-state.py reconcile`, which enumerates linked
   worktrees for every active keyed record and compares path, branch/ref, exact
   current HEAD, active gate/story, delegated execution ID, status, and
   ownership token. Adopt exactly one matching linked worktree per story and
   persist adoption evidence before continuing. Zero matches block as
   `stranded_worktree_missing`; multiple matching worktrees block as
   `worktree_ownership_ambiguous`; identity mismatch blocks as
   `worktree_identity_contradiction`; unexplained HEAD drift blocks as
   `worktree_identity_stale`. Resume must not relaunch stranded active work.
4. Recompute the immutable `package_manifest` and compare its digest and every
   locked planning path/hash; legitimate recommendation-log changes do not alter
   this identity. Story/README completion projections remain stable. A changed
   `spec-lite.md` is accepted only when an unbroken Gate 3.5 before/after digest
   chain and matching drift-log DEV ID prove the standard authorized amendment;
   otherwise it is a package contradiction.
5. Reconcile recommendation-log path, monotonic revision, current digest,
   ordered stable entry IDs, append-only prefix, per-entry digests, and
   `pendingEntryIds` independently. Adopt a valid unique append; reconcile a
   pending entry before retry; block an unexpected edit, rewrite, deletion,
   reorder, duplicate ID, terminal-entry change, or state-link mismatch as
   `recommendation_log_contradiction`.
6. Resolve `executionStatePath` only as an existing regular file inside
   `.writ/state` for the same spec. Its canonical plan contains every
   non-baseline story exactly once in dependency-valid batches, and SHA-256 of
   canonical plan JSON exactly equals `planDigest`.
7. Derive `completedStoryIds` exactly from unchanged, fully checked lock-time
   completion plus executed stories corroborated by complete indexed
   artifact/tasks/AC/dependencies, successful canonical story result, matching
   nested completion, plan membership, and exactly one mandatory pre-Gate-1
   ownership record. Linked worktrees require their exact integrated record;
   serial in-place work requires an explicit root/ref/start/current
   HEAD/parent-execution/result/integration binding. Completed, active, failed,
   result, nested-status, and ownership-record sets must agree.
8. Reconcile repository-local worktree merge/adoption evidence and passed
   integration evidence against exact current HEAD, immutable package digest,
   plan digest, exact completed set, non-empty command, `exitCode: 0`, completion
   time/summary, and a safe non-empty evidence artifact plus matching SHA-256.
   Never overwrite `currentHeadSha` to hide unexplained drift.

Contradictions block without mutation or inferred success. Completed story
artifacts may advance the earliest safe resume target; stale status alone may
not. WWB incompleteness is a warning only, matching `/implement-story`'s
graceful-degradation contract.

### Recommended DAG Execution

Build the same full dependency graph and batches as normal mode. Do not present
the routine execution-plan confirmation or advisory assessment choice. Invoke
every remaining story through the full `/implement-story` pipeline with
`delivery_context`; never pass `--quick` or bypass review, testing, or
documentation.

Before each delegated story reaches Gate 1, complete the canonical launch
handshake:

1. The child resolves an observable linked-worktree path, full ref/HEAD,
   starting SHA, story ID, delegated execution ID, and non-secret ownership
   token, then returns `recommend-worktree-launch-v1` without editing files.
2. Validate the launch against `git worktree list --porcelain` and call
   `python3 scripts/recommend-state.py reserve-worktree`. Persist the keyed
   record before returning `recommend-worktree-reservation-ack-v1`.
3. The child verifies the acknowledgment identity and may then enter Gate 1.
   Missing/mismatched acknowledgment blocks before edits.
4. After a successful normalized story result and local adoption/merge, call
   `scripts/recommend-state.py complete-worktree`; it rejects tracked or
   untracked dirt, requires committed story content after the reserved starting
   SHA, verifies the exact observed delegated HEAD is contained in the canonical
   parent feature-branch HEAD, binds the successful canonical result digest,
   persists source/target integration evidence, and
   only then changes ownership to `integrated` before another serial story may
   reuse that path. Committed-but-unintegrated, stale, and ambiguous targets
   block without releasing ownership.
5. If stable linked-worktree identity is unavailable, do not run that batch in
   parallel. Use one-at-a-time serial in-place execution only when root/ref/HEAD
   can use the same reservation handshake and retain an explicit ownership
   record through completion; otherwise block as
   `worktree_identity_unavailable`.

For every Gate 3.5 Small drift, capture the pre-edit `spec-lite.md` SHA-256,
append one unique `DEV-NNN` drift-log entry, apply only the proposed
`spec-lite.md` edit, and persist the canonical
`recommend-spec-lite-review-v1` result. Immediately call
`scripts/recommend-state.py record-spec-lite-amendment` with state, repository,
story ID, DEV ID, prior digest, and review-result path. Do not continue until
the returned amendment acknowledgment is durable. Medium drift logs without a
spec-lite edit; Large drift remains paused. Any write to another immutable
planning artifact, missing/duplicate DEV ID, stale prior digest, or incomplete
review binding blocks.

Normalize every story response at this deterministic boundary:

- Pass nested output through
  `python3 scripts/recommend-state.py normalize-result`; accept only
  `recommend-command-result-v1` with matching execution ID and `mode: recommend`.
- `succeeded` records evidence and advances completed story IDs.
- `answer_required` persists stable decision, question, and option IDs, retains
  recommend mode, and resumes the same transition after the answer.
- `blocked` persists its classification and safe resume target.
- `failed`, malformed, missing, or mismatched outcomes normalize to classified
  `blocked`; dependents do not run. One canonical result factory validates the
  generated result. `failed` always becomes `nested_result_failed` with the
  canonical empty `required_answer`; only `answer_required` may carry complete
  stable non-empty answer identity. Invalid JSON, shapes, identity, evidence,
  operations, or arguments emit one blocked JSON object with exit code 2 and no
  argparse usage text or traceback.

After all stories reconcile as successful, set `verifying`, run the ordinary
Phase 4 integration verification against the full combined change, persist its
command, integer exit code, completion time, evidence summary, artifact path and
SHA-256, exact HEAD, immutable manifest digest, plan digest, and completed-story
set, then return:

```yaml
schema: recommend-command-result-v1
execution_id: string
mode: recommend
command: implement-spec
status: succeeded | blocked | answer_required
completed_state: verified_implementation | null
resume_state: implementing | verifying | null
evidence:
  summary: string
  artifacts: [string]
identifiers:
  spec_path: string
  package_manifest_sha256: string
  recommendation_log_revision: integer
  recommendation_log_digest_sha256: string
  implementation_execution_state_path: string
  integration_evidence_artifact: string
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

`verified_implementation` is the handoff into the Story 4 staging continuation
below. Normal mode still returns at the ordinary boundary. Recommended mode
continues in the same execution and never claims overall delivery complete.

### Recommended Staging Continuation (Story 4)

After verified implementation, resolve the configured delivery provider,
provider repository/source remote/default branch, `Preview Provider`,
`Preview Project`, `Preview Evidence Source`, URL pattern, additive required
checks, and CI/preview wait timeouts. Normalize `Preview Project` exactly as
`config.previewProjectId` in the capability snapshot. Detection
may be used for this execution and logged, but is never silently saved to
`.writ/config.md`. Ask only for a critical missing choice; retain recommend mode.
Persist the complete capability/config snapshot through
`scripts/recommend-state.py activate-staging`. Unknown capability is not
equivalent to unavailable evidence or an empty result.

Invoke `/ship --test --recommend` with the same `delivery_context`. Reject any
result lacking a nonempty command, exit `0`, structured safe artifact plus exact
digest/head binding, evidence-backed allowed grouping strategy/basis, nonempty
decision and recommendation-log audit IDs, full commit SHAs/resulting head,
provider repository/source/base identity, and structured
`recommend-ship-result-v1`. Persist it with `record-ship`; marker-only or null
evidence blocks.

Provider adapters implement only these neutral operations:
`findPullRequest`, `createPullRequest`, `getPullRequest`,
`listRequiredChecks`, and `findPreview`. Before the sole PR mutation:

1. Derive—not accept—a SHA-256 operation key from provider repository ID, base,
   and head branch. Append a Pending recommendation entry containing that exact
   key and reconcile its path/digest/entry ID into state.
2. Run `findPullRequest` by saved ID when present, then repository/base/head.
3. Pass normalized lookup evidence to `record-pr-lookup`. Multiple, mismatched,
   or closed matches block. One matching open PR is adopted.
4. Only an explicit authorization from the reducer may continue. Call
   `mark-pr-create-attempt` to persist `attempted` before the sole
   `createPullRequest` mutation.
5. Observe with `getPullRequest` or the original lookup, pass the normalized
   record and same audit/key identity to `record-pr-created`, persist
   `created`/`reconciled`, and canonical ID/number/URL/full head SHA. Finalize
   that exact recommendation entry with those canonical values, reconcile the
   log, then call `finalize-pr-audit`; only it may advance from `pr_open` to
   `waiting_ci`. No subsequent staging transition may advance while a
   mutation-related entry remains Pending. Repeated absence after authorization or attempt blocks.
   A lost response always re-lookups and may adopt one exact PR.

Discover the complete provider-required check set and union it with configured
additive `Required Checks`. Pass provider/repository identity, query timestamp,
full head, stable provider-required IDs/names/set digest or explicit provider
zero declaration, separately classified config checks, statuses, and evidence
URL to `record-checks`. Include `authenticated: true` plus bounded
`listRequiredChecks` query-operation ID, provider, repository, head, start, and
completion evidence; missing/false authentication blocks and is never inferred
from a successful caller return. Config checks never substitute for provider discovery.
Before successful advancement, re-query the complete set and record reconciled
sequence `>= 2`, catching late-added checks. Pending/timeout/interruption persist
`waiting_ci`; failed/cancelled/unknown block. `unavailable`, `needs_auth`, and
`authorization_denied` remain distinct definitive outcomes with one report and
safe resume.

After successful checks, call `findPreview` read-only using configured existing
provider/project metadata or the documented project convention. Require
normalized provider, evidence source, provider repository/project identities,
integration ID, provenance kind/timestamp, and full SHA to match the persisted
capability/config snapshot. URL-pattern-only evidence is insufficient. Accept
only source/kind pairs from the explicit mapping:
`deployment-status → provider-deployment|provider-status`,
`check-output → provider-check`, and
`project-convention → project-convention`. Contradictions block. Accept
only a safe shareable HTTPS URL matching the optional pattern. Pass normalized
evidence to `record-preview`. Never call a deployment/provisioning operation, create an
account/project/environment/secret, fabricate a URL, or obtain an access-bypass
URL. Missing integration/capability, stale or unsafe evidence, timeout, and
provider errors leave the PR open and block or preserve `discovering_preview`
with project-specific setup/resume guidance.

Invoke `/create-uat-plan --recommend` only after preview readiness. It calls the
local `derive-uat` reference path to derive canonical scenarios from actual
completed story bytes: checked acceptance criteria, Context for Agents
error/shadow references, What Was Built, and technical error/shadow/edge
sections. It enriches canonical bytes with PR/head, complete successful checks,
preview provenance/instructions, warnings, proposed version, and consequences.
`record-uat` independently re-derives and requires exact source paths/digests,
source digest, generated bytes/digest, required enriched headings, and current
SHA. Arbitrary files or invented digests block; changed source inputs invalidate
and regenerate the output.

Present exactly one explicit production decision with stable IDs:

- PR number/URL and full current head SHA
- every required check and successful status for that SHA
- preview URL/deployment evidence for that SHA
- `uat-plan.md` path and SHA-256 plus warnings/instructions
- recommended version and concrete merge/release consequences
- approval and rejection options, with no default

Immediately before accepting the event, create one deterministic approval
reconciliation operation, append/reconcile its Pending or final recommendation
entry, then re-run `getPullRequest`, `listRequiredChecks`, and `findPreview`.
The normalized envelope must include query time and match the exact pre-event
state revision/digest, capability/config snapshot digest, PR record/head, required set digest/IDs and
all-success statuses, preview repository/project/provenance/status, and UAT
digest. Parse every observation as UTC RFC3339; one reconciliation attempt ID
binds PR/check/preview/UAT observations to the current revision/head. Require
presentation start after persisted evidence, observations after presentation,
the approval event after observations, at most 30 seconds future clock skew,
and freshness within the smaller configured wait window or five minutes.
Cached or stale evidence is invalid. Pass any head change to
`revalidate-staging`, which invalidates checks, preview, UAT, and approval and
returns to `waiting_ci`. Persist an explicit approval with actor, stable
interaction/event ID, full SHA, and time through `record-approval` before
returning. Silence stays `awaiting_approval`; duplicate IDs deduplicate;
rejection returns to implementation with recommend mode and PR identity
retained.

Successful Story 4 return is structured with
`completed_state: production_approved` and canonical PR/check/preview/UAT/
approval identifiers. It authorizes Story 5 but performs no merge, release,
provider release, or overall-complete transition.

## Command Process

### Phase 1: Spec Discovery & Loading

#### Step 1.1: Find Specs

If no spec argument provided:

```
AskQuestion({
  title: "Select Specification",
  questions: [
    {
      id: "spec",
      prompt: "Which specification do you want to implement?",
      options: [list of specs found in .writ/specs/]
    }
  ]
})
```

#### Step 1.2: Load Spec Context

1. **Read spec files:** `spec.md`, `spec-lite.md`, `user-stories/README.md`
2. **Read all story files:** Parse status, dependencies, task counts
3. **Identify already-completed stories** (skip them unless `--force`)

### Phase 2: Dependency Resolution & Planning

#### Step 2.1: Build Dependency Graph

Parse each story's dependency declarations and construct a DAG:

```
Stories: 1(none), 2(→1), 3(none), 4(→3), 5(→2,4)

Graph:
  1 ──→ 2 ──→ 5
  3 ──→ 4 ──↗
```

#### Step 2.2: Compute Parallel Batches

Topological sort into batches of independent stories:

```
Batch 1 (parallel): Story 1, Story 3    — no dependencies
Batch 2 (parallel): Story 2, Story 4    — dependencies satisfied by batch 1
Batch 3 (sequential): Story 5           — depends on batch 2
```

If `--from story-3` is specified, prune the graph to story 3 and all downstream stories.

#### Step 2.3: Estimate Scope

For each story, count:
- Implementation tasks
- Acceptance criteria
- Estimated complexity (task count × avg)

#### Step 2.3b: Pre-Flight Assessment

Run lightweight sizing checks against remaining stories. Flag if: >8 stories, >50 tasks, dependency depth >3, bottleneck story with >3 dependents, or any story with >7 tasks / >8 AC. Estimate per-story context cost (task count × change surface breadth).

**If no flags:** Proceed silently. **If flags found:** Show concerns above the execution plan and add `{ id: "assess", label: "Run /assess-spec for full analysis first" }` to the confirmation options. Pre-flight is advisory — never blocks execution.

#### Step 2.4: Present Execution Plan

```
## Execution Plan: 2026-02-22-feature-name

Stories to implement: 5 (2 already complete, 3 remaining)
Estimated phases per story: arch-check → code → lint → review → test → docs

  Batch 1 (parallel):
    ├── Story 3: API Endpoints (5 tasks, 4 AC) — no dependencies
    └── Story 4: Rate Limiting (4 tasks, 3 AC) — no dependencies

  Batch 2 (sequential):
    └── Story 5: Integration Tests (5 tasks, 6 AC) — depends on 3, 4

Skipping (already complete): Story 1, Story 2
```

#### Step 2.5: Confirm

```
AskQuestion({
  title: "Confirm Execution Plan",
  questions: [
    {
      id: "proceed",
      prompt: "Proceed with this execution plan?",
      options: [
        { id: "yes", label: "Execute the plan" },
        { id: "edit", label: "Change which stories to include" },
        { id: "reorder", label: "Change execution order" },
        { id: "quick", label: "Execute in quick mode (skip review + docs)" },
        // Include only when Step 2.3b found flags:
        { id: "assess", label: "Run /assess-spec for full analysis first" }
      ]
    }
  ]
})
```

If the user selects "assess," run `/assess-spec` with this spec pre-selected. After assessment completes, the user re-invokes `/implement-spec` for a fresh plan.

### Phase 3: Execution

#### Step 3.1: Initialize State

```json
// .writ/state/execution-{timestamp}.json
{
  "spec": "2026-02-22-feature-name",
  "startedAt": "2026-02-22T17:40:00Z",
  "plan": {
    "batches": [
      { "parallel": true, "stories": ["story-3-api", "story-4-rate-limit"] },
      { "parallel": false, "stories": ["story-5-integration"] }
    ]
  },
  "stories": {
    "story-3-api": { "status": "pending", "phase": null },
    "story-4-rate-limit": { "status": "pending", "phase": null },
    "story-5-integration": { "status": "pending", "phase": null }
  }
}
```

#### Step 3.2: Execute Batches

For each batch in order:

**If parallel batch:**
- Spawn `/implement-story {story-id}` for each story in the batch concurrently
- Wait for all to complete before proceeding to next batch
- If any story fails, decide: continue with independent stories or halt

**If sequential batch:**
- Run `/implement-story {story-id}` one at a time

**Pass-through flags:**
- `--quick` → each `/implement-story` runs in quick mode

#### Step 3.3: Update State After Each Story

After each `/implement-story` completes:
- Update execution state file with result
- Log: pass/fail, review iterations, test count, coverage
- **Regenerate `.writ/context.md`** — full rewrite using the schema defined in `implement-story.md` Step 2, reflecting the updated story progress. Each write replaces the entire file.

**On story failure:** Present remaining issues and offer: retry, skip (continue with independent stories), skip with all dependents, or abort.

**On dependency blocked:** Present the dependency chain and offer: skip, attempt anyway (dependencies incomplete), retry failed dependency, or abort.

### Phase 4: Completion

#### Step 4.1: Integration Verification

After all stories complete, run a single integration check to catch cross-story breakage. Per-story tests already ran in each `/implement-story` Gate 4 — this step only verifies that the stories work *together*.

```bash
# 1. Typecheck — catches cross-story type conflicts (always fast)
npx tsc --noEmit

# 2. Full test suite — catches integration breakage between stories
npm test    # or equivalent (pytest, cargo test, go test ./...)
```

If integration failures: identify which story likely broke it, report to user.

> **Why not proportional?** Each story's Gate 4 already ran targeted tests and coverage. At the spec level, multiple stories have landed — the risk of cross-story breakage justifies one full-suite run regardless of individual change surfaces.

#### Step 4.2: Summary Report

```
✅ Specification Complete: feature-name

| Story | Status | Review Iterations | Tests | Coverage | Docs |
|-------|--------|-------------------|-------|----------|------|
| 3: API | ✅ | 1 | 15/15 | 91% | Updated |
| 4: Rate Limit | ✅ | 2 | 8/8 | 87% | Updated |
| 5: Integration | ✅ | 1 | 12/12 | 94% | Updated |

Execution Stats:
- Total time: ~X minutes
- Stories: 3/3 complete
- Total tests: 35 passing
- Average coverage: 91%
- Review iterations: 4 total (1.3 avg)
- Integration tests: ✅ passing

Next steps:
- Optional: `/verify-spec` if you want a standalone metadata pass
- Run `/security-audit` for a security review
- `/ship` to open a PR, then `/release --dry-run` → `/release` when ready to publish
```

---

## Resume Support

If a session is interrupted mid-execution:

```
/implement-spec --resume
```

1. Finds most recent execution state file in `.writ/state/`
2. Identifies last completed story/phase
3. Picks up from next pending story
4. Re-runs current story from the beginning of its pipeline (idempotent)

---

## Integration with Writ Ecosystem

| Command | Relationship |
|---------|-------------|
| `/create-spec` | Creates the spec that `/implement-spec` executes |
| `/assess-spec` | Pre-flight sizing check runs automatically in Step 2.3b; full assessment available on demand |
| `/implement-story` | Called per-story by `/implement-spec` for the 6-gate pipeline |
| `/verify-spec` | Optional metadata diagnostic anytime (especially after `/implement-spec`) — not a release prerequisite |
| `/ship` / `/release` | `/ship` opens the PR; `/release` cuts the version with its own inline gate |
| `/status` | Shows progress of in-flight executions |

---

## References

- Standing instructions: [`commands/_preamble.md`](_preamble.md)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)
