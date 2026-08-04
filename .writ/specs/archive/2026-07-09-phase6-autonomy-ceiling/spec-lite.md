# Phase 6: Autonomy Ceiling (Lite)

> Source: `.writ/specs/2026-07-09-phase6-autonomy-ceiling/spec.md`
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Harden normal multi-spec `/implement-phase`, then retire Ralph. Single-spec `--recommend` delivery is governed separately by ADR-013.

**Implementation Approach:**
- Require `2026-07-10-recommended-autonomous-delivery` before Phase 6 execution.
- Validate explicit spec dependencies before the single confirmation gate.
- Run every spec in a fresh subagent on an isolated branch/worktree.
- Merge successful lanes; preserve terminal failures as `writ/quarantine/{spec}`.
- Keep orchestration platform-neutral; adapters map native subagent mechanics.
- Persist lane, dependency, challenge, merge, quarantine, and UAT state.

**Files in Scope:**
- `commands/{implement-phase,implement-spec,create-spec,verify-spec,status,knowledge,_preamble}.md`
- `adapters/{cursor,claude-code,codex}.md`
- `.writ/docs/{config-format,phase-execution-state-format}.md`
- Ralph surfaces, `.writ/manifest.yaml`, `SKILL.md`, `README.md`, `CHANGELOG.md`

**Error Handling:**
- Invalid dependency graph → stop before confirmation with exact path.
- Transient spec failure → one retry; terminal failure → quarantine lane.
- Failed dependency → block declared dependents; continue independent specs.
- Missing/stale health evidence → `Warning`, never fabricated success.

**Integration Points:**
- `/implement-phase` orchestrates `/implement-spec` → `/create-uat-plan`.
- `/verify-spec` Check 4 validates both story and spec graphs separately.
- Phase close writes only durable, deduplicated lessons to `/knowledge` schema.

---

## For Review Agents

**Acceptance Criteria:**
1. A disposable 3+ spec phase uses a fresh context for every spec.
2. Failed partial work remains on quarantine; phase branch stays clean.
3. Explicit dependency order is deterministic; missing/self/cyclic refs fail.
4. User Challenge gates only proposed scope or exit-criteria degradation.
5. `/status` reports phase progress and categorical health in under 10 seconds.
6. Ralph is absent from active discovery and preserved under `archive/ralph/`.

**Business Rules:**
- One routine confirmation in normal multi-spec mode; session-bound and resumable.
- Multi-spec `/implement-phase --recommend` remains excluded.
- `dependencies:` uses exact spec folder IDs and is binding.
- Shared-file/prose inference warns but never silently reorders.
- The orchestrator retains state and escalation, not prior agent context.
- Knowledge writeback requires durable evidence and deduplication.
- Synthetic UAT cannot satisfy the roadmap's real-use observation criterion.
- Ralph upgrades warn users to finish/abandon in-flight runs; no state migration.

**Experience Design:**
- Entry: `/implement-phase [phase]`.
- Happy path: validate → confirm → isolate → fresh agent → merge → UAT.
- Moment of truth: successful phase branch contains no failed-spec work.
- Feedback: phase state plus `/status` progress and evidence freshness.
- Error: quarantine with blocked-dependency impact and recovery guidance.

**Drift Anchors:**
- Opaque unbounded loops, multi-spec recommend mode, and parallel spec execution are out of scope.
- Any numeric health score or synthetic “real-use” claim is contract drift.

---

## For Testing Agents

**Success Criteria:**
1. Sandbox includes 3+ specs and proves fresh-context execution.
2. Deliberate failure proves quarantine, clean branch, and dependency blocking.
3. Eval, generated catalog check, and install/update dry runs pass.

**Shadow Paths to Verify:**
- **Happy path:** all lanes succeed → ordered merges → UAT plans generated.
- **Nil input:** no phase/specs → existing fallback guidance, no state corruption.
- **Empty input:** `dependencies: []` → roadmap order without false errors.
- **Upstream error:** subagent terminal failure → quarantine and independent continuation.

**Edge Cases:**
- Dependency cycle → stop before confirmation with full cycle.
- Interrupted merge or stale worktree → resume reports mismatch before acting.
- Missing eval summary → health is `Warning — evidence unavailable`.
- Scope degradation → four-part User Challenge persists selected decision.

**Coverage Requirements:**
- Dependency and state transitions: 100% fixture coverage.
- Failure, quarantine, and resume paths: 100% sandbox coverage.
- Real-use User Challenge observation remains pending until genuine evidence.

**Test Strategy:**
- Disposable multi-spec sandbox plus manual UAT.
- `scripts/eval.sh`, `gen-skill.sh --check`, install/update dry runs.
