# Technical Specification: Phase 6 Autonomy Ceiling

> **Parent:** `../spec.md`
> **Status:** Not Started
> **Stories:** 1–7

## Architecture Summary

Phase 6 converts `/implement-phase` from an inline command loop into a platform-neutral orchestration state machine. Each spec executes inside a fresh subagent and isolated git lane. The parent session owns only dependency resolution, state transitions, merge/quarantine decisions, escalation, phase-close verification, and evidence writeback.

```text
roadmap + spec metadata
          │
          ▼
 resolve and validate DAG
          │
          ▼
 one confirmation gate
          │
          ▼
 create isolated spec lane ──► spawn fresh subagent
          │                           │
          │                      structured result
          ◄───────────────────────────┘
          │
     ┌────┴────┐
   success   terminal failure
     │             │
 verify + merge   preserve quarantine
     │             │
 generate UAT     block dependents
     └────┬────────┘
          ▼
 update state → next eligible spec → phase close
```

## Design Decisions

### D1 — Explicit Dependencies Are Authoritative

New spec headers use:

```markdown
> **Dependencies:** [2026-07-01-foundation, 2026-07-02-consumer]
```

Rules:

- Field is optional for legacy specs; `/create-spec` emits it for every new spec.
- `[]` means no declared cross-spec dependency.
- Values are exact folder IDs under `.writ/specs/`.
- Input order is preserved for display but graph order is determined topologically.
- Duplicate entries are invalid but auto-fixable by deduplication only when order is preserved.
- Missing references, self-reference, and cycles are blocking validation findings.
- Story dependency parsing remains unchanged and separate.

`/implement-phase` ordering precedence becomes:

1. Valid explicit `Dependencies` graph
2. Roadmap order among otherwise independent specs
3. Shared-surface/prose inference as warnings only

### D2 — Isolation Begins Before Work

For spec `{spec-id}` in phase `{phase-id}`:

- active branch: `writ/phase/{phase-id}/{spec-id}`
- worktree: implementation-selected path outside the primary checkout
- terminal failure branch: `writ/quarantine/{spec-id}`

The lane starts from the current phase branch head. Only a verified successful lane may merge back. The subagent never edits the parent checkout.

Collision policy:

- Existing matching active branch with matching state → resume candidate.
- Existing matching active branch without matching state → stop and report ownership ambiguity.
- Existing quarantine branch → create a deterministic suffixed branch only after surfacing the collision in the phase plan.
- Dirty phase branch before lane creation → stop before confirmation; do not hide unrelated changes in a lane.

### D3 — Fresh Subagent Contract

The orchestrator passes:

```yaml
phase_id: string
spec_id: string
spec_path: repo-relative path
phase_state_path: repo-relative path
lane_branch: string
lane_worktree: path
mode: standard | quick
inherited_answer_sources:
  - roadmap
  - spec contract
  - technical spec
  - story files
expected_result_schema: phase-spec-result-v1
```

The result contains:

```yaml
spec_id: string
status: succeeded | failed | challenge_required
stories_completed: integer
stories_total: integer
verification:
  summary: string
  evidence: [string]
files_changed: [path]
commit: string | null
failure:
  classification: transient | terminal | null
  summary: string | null
challenge: object | null
```

No prior conversational transcript is forwarded. Required context is loaded from repository artifacts by path.

### D4 — State Is the Resume Boundary

Recommended `phase-execution-v2` shape:

```json
{
  "schemaVersion": 2,
  "phase": "6",
  "phaseBranch": "phase/6-autonomy-ceiling",
  "startedAt": "ISO-8601",
  "updatedAt": "ISO-8601",
  "status": "executing",
  "specOrder": ["spec-a", "spec-b"],
  "specs": {
    "spec-a": {
      "dependencies": [],
      "status": "implementing",
      "attempts": 1,
      "laneBranch": "writ/phase/6/spec-a",
      "worktreePath": "/path",
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

State writes use a temporary file plus atomic rename where the platform supports it. Unknown fields are preserved during compatible updates. Version mismatch is reported before mutation.

### D5 — User Challenge Is a Structured Escalation

```yaml
trigger: scope_degradation | exit_criteria_degradation
roadmap_or_spec_said: string
recommendation: string
possibly_missing_context: string
cost_if_wrong: string
options:
  - id: string
    label: string
decision:
  option_id: string
  decided_at: ISO-8601
```

Nested pipelines return `challenge_required`; only the parent orchestrator presents the choice. Ordinary failures use normal failure handling.

### D6 — Evidence-Bound Knowledge

A candidate lesson is written only when all are true:

1. It generalizes beyond one story or spec.
2. It cites a phase report, drift-log entry, failure record, or repeated observation.
3. It is not substantively duplicated in existing knowledge.
4. It is below ADR blast radius.

Written entries use the existing `.writ/knowledge/lessons/` schema. Rejected candidates stay in the phase report, not the ledger.

### D7 — Categorical Health

Inputs:

- latest available eval summary
- latest relevant `verification-*.md` report
- unresolved recent drift entries
- phase-state consistency with named git branches

Classification:

| Category | Condition |
|---|---|
| Healthy | Current available evidence passes; no material drift or state mismatch |
| Warning | Evidence missing/stale, or only non-blocking warnings exist |
| Attention | Current failure, unresolved material drift, or state/git mismatch |

The status output names each unavailable or stale source. No weighted score is calculated. `/status` does not invoke `/verify-spec`, builds, tests, network calls, or CI APIs.

### D8 — Ralph Upgrade Guidance Is Explicit

Ralph state is preserved but not migrated. Release notes and upgrade guidance must instruct users with in-flight `ralph-*.json` runs to finish or abandon them before upgrading. No compatibility reader or runtime detector is added because this repository has no active Ralph state and the locked contract rejects that extra surface.

## File × Story Matrix

| File | S1 | S2 | S3 | S4 | S5 | S6 | S7 |
|---|---:|---:|---:|---:|---:|---:|---:|
| `commands/create-spec.md` | ✓ |  |  |  |  |  |  |
| `commands/verify-spec.md` | ✓ |  |  |  |  | ✓ |  |
| `commands/implement-phase.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `commands/implement-spec.md` |  | ✓ | ✓ | ✓ |  |  |  |
| `commands/_preamble.md` |  |  | ✓ |  |  |  |  |
| `commands/knowledge.md` |  |  |  |  | ✓ |  |  |
| `commands/status.md` |  |  |  | ✓ |  | ✓ | ✓ |
| `adapters/cursor.md` |  | ✓ |  | ✓ |  |  | ✓ |
| `adapters/claude-code.md` |  | ✓ |  | ✓ |  |  | ✓ |
| `adapters/codex.md` |  | ✓ |  | ✓ |  |  | ✓ |
| `.writ/docs/phase-execution-state-format.md` |  | ✓ | ✓ | ✓ | ✓ | ✓ |  |
| `.writ/docs/config-format.md` |  |  |  |  |  |  | ✓ |
| `scripts/eval.sh` |  |  |  |  |  | ✓ | ✓ |
| Ralph/catalog/docs surfaces |  |  |  |  |  |  | ✓ |

## Error & Rescue Map

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| Parse spec dependencies | Missing/malformed field | Legacy absence becomes `[]`; malformed field blocks with file reference | Fixture headers: absent, empty, malformed |
| Resolve dependency graph | Missing/self/cyclic reference | Stop before confirmation; print exact edge or cycle | DAG fixture matrix |
| Create lane branch | Dirty base, collision, git error | Stop before subagent launch; preserve parent state | Dirty tree and collision sandbox |
| Create worktree | Path collision or unsupported state | Remove only confirmed stale owned path; otherwise stop with recovery | Existing owned/unowned path fixtures |
| Spawn fresh subagent | Platform launch failure | Record terminal orchestration failure; do not mutate phase branch | Adapter contract simulation |
| Execute spec | Transient pipeline failure | Retry once in same isolated lane with fresh subagent | Deliberate first-attempt failure |
| Execute spec | Terminal/second failure | Preserve lane as quarantine; block dependents | Partial commit then deliberate failure |
| Validate successful lane | Missing commit or failed verification | Treat as terminal failure; quarantine | Agent returns success without evidence |
| Merge successful lane | Conflict or interrupted merge | Abort merge safely; retain lane and mark attention required | Conflicting independent lane fixture |
| Update phase state | Interrupted write | Atomic replacement; retain last valid state | Kill between temp write and rename |
| Resume phase | State and git disagree | Report mismatch; do not guess or mutate | Rename/delete branches before resume |
| Present User Challenge | Nested agent omits required field | Reject malformed challenge and report contract error | Schema fixture per missing field |
| Generate UAT | Command fails after merge | Mark implementation succeeded/UAT failed; resume at UAT step | Deliberate UAT generation failure |
| Write knowledge | Candidate is duplicate or weak | Skip with reason; never append noise | Existing duplicate and one-off drift fixtures |
| Compute health | Evidence missing/stale | `Warning` with named unavailable evidence | Empty and aged artifact fixtures |
| Archive Ralph | Active references remain or upgrade warning is absent | Eval/catalog checks fail until active references are removed and finish-or-abandon guidance exists | Search allowlisted active paths and release text |

No `[UNPLANNED]` operations remain. External CI retrieval is explicitly out of scope; health uses local artifacts only.

## Shadow Paths

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| Dependency sequencing | Valid DAG → deterministic plan | No phase/spec path → fallback guidance | `Dependencies: []` → roadmap order | Missing dependency → blocking diagnostic |
| Fresh spec execution | Lane → agent → verified merge | Agent result missing → quarantine as invalid result | Spec has no remaining stories → skip with evidence | Agent launch/failure → retry or quarantine |
| Quarantine | Failure preserved; dependents blocked | No partial commit → branch still retained with failure record | No dependents → continue all remaining specs | Git rename failure → keep active lane and mark attention |
| Resume | State matches git → continue exact step | No state → normal phase resolution | Completed phase → report current result | State/git mismatch → stop with recovery |
| Knowledge writeback | Durable novel lesson written | No report evidence → no write | No qualifying candidates → silent no-op | Invalid generated entry → reject and report |
| Status health | Current passing artifacts → Healthy | No artifacts → Warning with missing sources | No drift entries → neutral input | Failed current artifact → Attention |
| Ralph deprecation | Active discovery points to implement-phase | No Ralph state → no migration action | No archive consumer → archive remains historical | Generated catalog stale → check fails |

## Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| User invokes phase twice | Existing matching live state triggers resume guidance, not a second lane |
| User interrupts during subagent work | State remains implementing; resume reconciles agent-independent git state |
| User interrupts during merge | Resume detects merge state and requires safe resolution before continuing |
| Two specs declare each other | Validation shows full cycle and stops before confirmation |
| Dependency listed twice | Report duplicate; safe dedupe may be offered without changing order |
| Shared files but no dependency | Warn in phase plan; do not silently reorder |
| Independent spec conflicts at merge | Retain lane, mark attention; never discard successful work |
| Quarantine branch already exists | Surface collision and use deterministic suffix only with recorded mapping |
| Scope challenge during retry | Retry stops; challenge is presented before any scope-changing action |
| Health evidence is mixed age | Category cannot exceed Warning; output names oldest required source |
| Real-use criterion lacks evidence | Phase remains implemented/pending validation, never Complete |

## Sandbox UAT Design

Create temporary specs in an isolated test repository or disposable directory:

1. `fixture-a-foundation` — succeeds and creates a harmless artifact.
2. `fixture-b-terminal-failure` — creates partial committed work, then fails twice.
3. `fixture-c-dependent` — declares dependency on B and must remain blocked.
4. `fixture-d-independent` — no dependency on B and must continue successfully.

Run `/implement-phase` against the fixture phase and collect:

- phase execution plan and one confirmation
- per-spec fresh run evidence
- merge commits for A and D
- absence of B changes on phase branch
- `writ/quarantine/fixture-b-terminal-failure`
- blocked status for C
- rendered User Challenge from a separate scope-degradation fixture
- resume behavior after a controlled interruption
- status health output with current, stale, and absent evidence

The fixture is disposable and does not count as the roadmap's real-use User Challenge observation.

## Verification Commands

```bash
bash scripts/eval.sh
bash scripts/gen-skill.sh --check
bash scripts/install.sh --dry-run
bash scripts/update.sh --dry-run
```

Also search active product surfaces for stale Ralph references, excluding `archive/`, historical specs, ADRs, changelog history, and roadmap history.

