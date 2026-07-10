# Recommended Autonomous Delivery (Lite)

> Source: `.writ/specs/2026-07-10-recommended-autonomous-delivery/spec.md`
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Add observable `--recommend` delivery from spec creation through staged approval, merge, and release.

**Implementation Approach:**
- Supersede ADR-010's contract gate while preserving one explicit production approval.
- Use one explicit state machine: spec → implement → PR → CI → preview → approval → merge → release.
- Persist runtime state under `.writ/state/`; persist concise decisions in the tracked spec package.
- Reuse configured preview deployments; never provision hosting or bypass platform controls.
- Reconcile Phase 6 governance before implementing behavior.

**Files in Scope:**
- `commands/{create-spec,implement-spec,ship,release,create-uat-plan}.md`
- `system-instructions.md`
- `adapters/{cursor,claude-code,codex}.md`
- `.writ/docs/config-format.md` and new state-format docs as needed
- ADR-010, superseding ADR, Phase 6 spec artifacts, roadmap
- Manifest/catalog/README/eval surfaces when affected

**Error Handling:**
- No defensible choice or critical ambiguity → pause with bounded question.
- CI failure or changed PR SHA → invalidate approval and return to validation.
- Missing preview integration → keep PR open and provide setup guidance.
- Interrupted external action → reconcile provider reality before retrying.
- Merge/release conflict → stop without force or destructive cleanup.

**Integration Points:**
- `/create-spec --recommend` orchestrates `/implement-spec` → `/ship --test` → staged UAT → `/release`.
- `/implement-spec --recommend` starts from a locked spec and follows the same delivery tail.
- Provider adapters map PR checks, preview discovery, merge, and release operations.

---

## For Review Agents

**Acceptance Criteria:**
1. A fixture reaches a saved spec, verified implementation, preview, approved merge, tag, and release.
2. Every automatic choice has evidence, alternatives, risk, reversibility, and result in `recommendation-log.md`.
3. Normal mode adds `(Recommended)` consistently without changing interactive control.
4. No merge or release occurs before explicit approval of the exact PR head SHA.
5. Resume never duplicates a PR, merge, release commit, tag, or provider release.
6. All three adapters preserve equivalent semantics.

**Business Rules:**
- Recommendation is evidence-based, never positional or affirmative-by-default.
- Equivalent choices prefer the simpler or more reversible path.
- Required answers do not clear recommendation mode.
- Security, data integrity, compliance, unexpected cost, destructive change, and core-contract ambiguity pause.
- Stage approval authorizes merge plus recommended release for one immutable SHA.
- Required checks and branch protections are never bypassed.
- Preview infrastructure and npm publishing are out of scope.

**Experience Design:**
- Entry: `/create-spec --recommend …` or `/implement-spec --recommend …`.
- Happy path: deliberate → artifacts → implementation → preview → approve → merge → release.
- Moment of truth: preview and complete decision ledger are reviewable before production.
- Feedback: concise visible choice plus durable recommendation entry.
- Error: one blocker, preserved state, and an actionable resume path.

**Drift Anchors:**
- Raw chain-of-thought storage is forbidden; persist concise decision evidence.
- Opaque unattended loops and multi-spec recommend mode are out of scope.
- "PR created" is not completion; merge and release evidence are required.

---

## For Testing Agents

**Success Criteria:**
1. Recommendation labeling and automatic selection fixtures pass.
2. End-to-end state transitions are deterministic and resumable.
3. External mutations are idempotent under interruption and retry.

**Shadow Paths to Verify:**
- **Happy path:** issue → spec → implementation → preview → approval → merge → release.
- **Nil input:** no defensible recommendation → bounded pause, mode retained.
- **Empty input:** missing preview configuration → setup blocker, PR remains open.
- **Upstream error:** CI/provider/release failure → persisted blocker and safe resume.

**Edge Cases:**
- PR head changes after approval → approval invalidated.
- Existing PR/tag/release on resume → reuse after identity verification.
- Multiple valid options → simplest reversible option selected and logged.
- Branch protection rejects merge → no bypass; exact policy blocker reported.
- Release partially succeeds → preserve existing tag/release and reconcile.

**Coverage Requirements:**
- Decision and state transitions: 100% fixture coverage.
- External mutation idempotency: 100% happy and interrupted paths.
- Critical pause taxonomy: 100% representative cases.
**Test Strategy:**
- Static command-contract evals plus disposable git/provider fixtures.
- Adapter parity review and manual staged UAT.
