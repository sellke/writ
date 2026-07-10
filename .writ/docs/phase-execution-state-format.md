# Phase Execution State Format

> **Schema:** `phase-execution-v2`
> **Owner:** `/implement-phase`
> **Executable reference:** `scripts/phase-state.py`
> **Location:** `.writ/state/phase-execution-{timestamp}.json` (ephemeral, gitignored)

This document is the canonical contract for the state file that
`/implement-phase` uses to orchestrate a roadmap phase across fresh, isolated
per-spec execution lanes. It is the **resume boundary**: on `--resume`, the
combination of this file and git reality is the only source of truth. The
platform-neutral command owns *sequencing, state, escalation, and merge/quarantine
decisions*; a fresh subagent owns each spec's *implementation* and reports back a
structured result. The state file is how the orchestrator remembers what it has
done without holding conversational history.

Later Phase 6 stories extend this schema:

- **Story 2 (this document's foundation)** — lanes, agent runs, verified merge, atomic writes.
- **Story 3** — persisted User Challenges (`challenges`).
- **Story 4** — retry attempts, quarantine branches, blocked dependents, resume reconciliation.
- **Story 5** — evidence-bound knowledge writeback (`knowledgeWritten`).
- **Story 6** — status-readable progress and health summaries.

## Runtime Shape

```json
{
  "schemaVersion": 2,
  "phase": "6",
  "phaseBranch": "phase/6-autonomy-ceiling",
  "startedAt": "2026-07-10T21:00:00Z",
  "updatedAt": "2026-07-10T21:05:00Z",
  "status": "executing",
  "specOrder": ["spec-a", "spec-b"],
  "specs": {
    "spec-a": {
      "dependencies": [],
      "status": "implementing",
      "attempts": 1,
      "laneBranch": "writ/phase/6/spec-a",
      "worktreePath": "/abs/path/.writ-lanes-6/spec-a",
      "agentRunId": null,
      "mergeCommit": null,
      "quarantineBranch": null,
      "blockedBy": [],
      "uatPlan": null,
      "evidence": []
    }
  },
  "challenges": [],
  "knowledgeWritten": []
}
```

## Field Contract (Story 2 slice)

| Field | Meaning |
|---|---|
| `schemaVersion` | Always `2` for this format. A reader that sees an unsupported major reports before mutating. |
| `phase` / `phaseBranch` | The roadmap phase ID and the git branch that accumulates only verified work. |
| `specOrder` | The topologically ordered spec list (see `scripts/spec-deps.py`). |
| `specs.{id}.status` | One of `pending`, `implementing`, `integrated`, `failed`, `quarantined`, `skipped_blocked`. |
| `specs.{id}.attempts` | Incremented on each lane launch; Story 4 bounds retries against it. |
| `specs.{id}.laneBranch` | The active lane branch `writ/phase/{phase}/{spec}`. |
| `specs.{id}.worktreePath` | The isolated worktree path while active; nulled after a successful merge removes it. |
| `specs.{id}.agentRunId` | The platform-native fresh-subagent run identifier when available. |
| `specs.{id}.mergeCommit` | The no-ff merge commit recorded on a verified success. |
| `specs.{id}.evidence` | Verification evidence strings copied from the structured result. |

Story 4 activates `quarantineBranch`, `blockedBy`, and failure records; Story 5
activates `knowledgeWritten`; Story 3 activates `challenges`. They are present and
inert until then.

## Lane Lifecycle (D2 — Isolation Begins Before Work)

1. **Create before work.** `phase-state.py create-lane` verifies the phase branch
   is clean, then creates branch `writ/phase/{phase}/{spec}` **and** a dedicated
   worktree from the current phase-branch head. A branch created only *after* a
   failure cannot prove the phase branch stayed clean, so creation is unconditional
   and up front.
2. **Fresh subagent runs in the lane.** The orchestrator never forwards
   conversational transcript; the subagent is seeded only from repository artifact
   paths (see the Fresh Subagent Payload below) and works only inside the lane
   worktree. The primary checkout is never mutated during lane work.
3. **Verify, then merge.** Only a validated `phase-spec-result-v1` with
   `status: succeeded`, a real `commit`, and non-empty verification evidence may be
   merged (`--no-ff`) into the phase branch; the worktree is then removed and the
   merge commit recorded.
4. **Preserve on anything else.** A missing, malformed, non-successful, or
   unverifiable result never touches the phase branch. Its lane is left intact for
   Story 4 to classify, quarantine, and recover.

### Collision policy

- Existing matching active branch **with** matching live state → resume candidate.
- Existing matching active branch **without** matching state → stop and report `lane_collision` (ownership ambiguity).
- Dirty phase branch before lane creation → stop with `dirty_base` before any subagent launch.

## Fresh Subagent Payload (D3)

The orchestrator passes only artifact paths and execution metadata — never prior
conversation:

```yaml
phase_id: string
spec_id: string
spec_path: repo-relative path
phase_state_path: repo-relative path
lane_branch: string
lane_worktree: path
mode: standard | quick
inherited_answer_sources: [roadmap, spec contract, technical spec, story files]
expected_result_schema: phase-spec-result-v1
```

### `phase-spec-result-v1`

```yaml
spec_id: string
status: succeeded | failed | challenge_required
stories_completed: integer
stories_total: integer
verification: { summary: string, evidence: [string] }
files_changed: [path]
commit: string | null            # required and non-null when succeeded
failure: { classification: transient | terminal, summary: string } | null
challenge: object | null         # required when challenge_required (Story 3)
```

`scripts/phase-state.py validate-result` is the authoritative validator. A
`succeeded` result without a commit or without verification evidence is rejected as
`invalid_result` and treated as a preserved (non-merged) lane.

## User Challenges (D5 — Story 3)

The `challenges` array persists every scope-degradation escalation for resume and
audit. Each entry:

```json
{
  "id": "CHAL-1",
  "spec": "spec-a",
  "status": "unresolved",
  "challenge": {
    "trigger": "scope_degradation",
    "roadmap_or_spec_said": "...",
    "recommendation": "...",
    "possibly_missing_context": "...",
    "cost_if_wrong": "...",
    "options": [{ "id": "auth-only", "label": "..." }],
    "decision": { "option_id": "auth-only", "decided_at": "2026-07-10T21:00:00Z" }
  }
}
```

Rules:

- A challenge qualifies **only** for `scope_degradation` or `exit_criteria_degradation`
  and must carry all four required parts. `scripts/phase-state.py validate-challenge`
  rejects a malformed challenge as `invalid_challenge` — a contract error, never a
  User Challenge and never an ordinary failure.
- An **unresolved** challenge blocks the challenged decision: the spec record moves to
  `challenge_required` and execution does not pass the decision until it is answered.
- An **audited** low-risk reversible selection is recorded already `resolved` with a
  `decision`. A paused challenge is recorded `unresolved` and answered with one explicit
  `AskQuestion`; `resolve-challenge` records the selected option and `decided_at`.
- On resume, an unresolved challenge remains persisted and re-presented; a resolved
  challenge is never re-asked.

## Quarantine and Resume (R4 — Story 4)

Failure disposition is bounded and evidence-preserving:

- **Bounded retry.** A `phase-spec-result-v1` failure classified `transient` on the
  first attempt is retried **once** in the same lane with a fresh subagent
  (`classify` → `retry`), without a new routine confirmation. A `terminal` failure,
  or a transient failure after the permitted retry, is a terminal disposition.
- **Quarantine.** On terminal disposition, `quarantine` removes the lane worktree
  and renames the lane branch to `writ/quarantine/{spec-id}` — using a deterministic
  suffix (`-2`, `-3`, …) on collision, with the mapping recorded. Because the failed
  lane never merged, the phase branch contains **none** of its commits; the reducer
  verifies `phaseBranchClean`. State records failure summary, retry count
  (`attempts`), `quarantineBranch`, and a `recovery` command.
- **Dependent blocking.** Direct and transitive dependents (from each spec's
  `dependencies`) become `skipped_blocked` with a `blockedBy` list; specs
  independent of the failure remain eligible and continue.
- **Attention, not corruption.** If the quarantine rename (or a nominal-success
  lane verification) fails, the reducer preserves recoverable lane work, records an
  attention-required state, and leaves the phase branch clean rather than forcing a
  mutation.

### Resume reconciliation

`phase-state.py reconcile` is **read-only**. On `--resume` it checks that the phase
branch, active lanes, worktrees, and quarantine branches recorded in state still
match git reality. If they agree it returns `consistent` and execution may continue
from the exact recorded step. If they disagree it returns `mismatch` (attention),
names each discrepancy, and **does not guess or mutate git** — state is joint
evidence with git, never permission to recreate, rename, delete, or merge branches
to "repair" reality.

## Knowledge Writeback (D6 — Story 5)

At phase close, `scripts/phase-state.py knowledge-writeback` evaluates candidate
lessons drawn from the phase report and per-spec drift logs. A candidate is written
to `.writ/knowledge/lessons/` (existing schema) **only** when **all** hold:

1. it **generalizes** beyond one story or spec;
2. it **cites** a phase report, drift-log entry, failure record, or repeated observation;
3. it is **not substantively duplicated** in the existing ledger (meaning-based dedup, not filename/exact text); and
4. it is **below ADR blast radius** (architectural decisions belong in ADRs, not auto-written lessons).

Each written entry's id is recorded in `knowledgeWritten` so a resumed phase close
never writes the same lesson twice. Rejected candidates are reported (with a terse
reason) but never written. **No qualifying candidate is a valid no-op**: no knowledge
file changes and an empty candidate set produces no report section.

## Atomic Writes

State is written with a sibling temporary file plus `os.replace` rename. An
interruption therefore leaves either the prior valid state or the next valid
state — never a torn or partially written JSON file. Compatible writers
**preserve unknown fields** so later stories (and future schema minor versions)
do not lose data written by a newer reducer.
