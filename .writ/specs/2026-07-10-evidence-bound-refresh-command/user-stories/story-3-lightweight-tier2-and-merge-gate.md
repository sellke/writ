# Story 3: Lightweight Tier 2 and Merge Gate

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Stories 1, 2

## User Story

**As a** Writ maintainer refining a high-traffic command
**I want to** a pre-merge eval gate that only lets evidenced, eval-passing refinements merge — with a bounded structural Tier 2 check for the heaviest commands — and two real acceptance records proving the loop works
**So that** the roadmap's falsifiability bar is met: at least one refinement merged with cited evidence and passing evals, and at least one rejected for lacking evidence

## Acceptance Criteria

- [ ] Given a proposed amendment, when Phase 4 runs the pre-merge gate (`bash scripts/eval.sh --check=refresh-evidence`), then an unevidenced or eval-failing amendment is rejected before any file write and recorded with reason `no evidence` or `eval failed`.
- [ ] Given the target is a high-traffic command (`create-spec`, `implement-story`, `ship`, `refactor`), when the gate runs, then it additionally runs a lightweight structural check on the refreshed command file, reusing existing Tier 1 structural primitives and introducing no LLM-as-judge.
- [ ] Given the target is not on the high-traffic allowlist, when the gate runs, then only the base evidence check applies.
- [ ] Given the loop has run, when `.writ/refresh-log.md` is inspected, then it contains one entry for a refinement merged with cited transcript evidence and passing evals, and one entry rejected for lacking evidence.
- [ ] Given all changes are in place, when `bash scripts/eval.sh` and `bash scripts/gen-skill.sh --check` run, then both are clean and CI remains green.

## Implementation Tasks

- [ ] 3.1 Add FAILING Tier 2 fixtures to `scripts/eval-refresh-evidence.py`: the high-traffic allowlist is recognized; a high-traffic refresh that skips the structural check fails; a non-allowlisted refresh uses the base check only; the gate rejects an unevidenced or eval-failing amendment.
- [ ] 3.2 Define the bounded Tier 2 check: the allowlist (`create-spec`, `implement-story`, `ship`, `refactor`) and a structural validation that reuses existing Tier 1 primitives (required-sections, broken-refs, length, preamble reference, diff-anchor); explicitly exclude the LLM-judge variant.
- [ ] 3.3 Wire the pre-merge gate into `commands/refresh-command.md` Phase 4 Apply: run `bash scripts/eval.sh --check=refresh-evidence` (plus the structural Tier 2 for high-traffic targets) before writing; on failure reject and log; only evidenced, eval-passing refinements merge.
- [ ] 3.4 Document the two-example acceptance and the Tier 2 boundary in `commands/refresh-command.md`, and add `require_literal` assertions in `check_refresh_evidence()` for the gate, the allowlist, the structural-not-LLM boundary, and the two-example documentation.
- [ ] 3.5 Add the Technical-Concerns caveat inline where Tier 2 is defined (structural/opt-in only; LLM-judge deferred behind an explicit future decision per `.writ/research/2026-04-24-writ-vs-gstack-rigor-comparison.md`).
- [ ] 3.6 Produce the two real `.writ/refresh-log.md` entries — one refinement merged with cited transcript evidence and a clean gate, one rejected for lacking evidence — conforming to the reconciled `.writ/docs/refresh-log-format.md` schema.
- [ ] 3.7 Run `bash scripts/eval.sh`, `bash scripts/gen-skill.sh --check`, and the drift greps; confirm all clean and CI green.

## Notes

- Tier 2 is deliberately conservative (parent spec D8): a lightweight structural reuse of Tier 1 primitives scoped to high-traffic commands, not an LLM-as-judge. Building an LLM judge now would contradict the research's deferral and the roadmap's pacing discipline.
- Tier 2 adds fixture scenarios and static assertions to the SAME `refresh-evidence` check — it is not a second registry entry.
- Enforcement is layered: the in-command Apply-time gate is fast feedback; CI (`.github/workflows/eval.yml`) is the backstop and needs no change.
- The two acceptance entries are the product deliverable that satisfies the roadmap success criterion; do not mark the spec complete without both.
- This story shares `commands/refresh-command.md` with Story 1 and `scripts/eval.sh`/`eval-refresh-evidence.py` with Story 2 — apply edits as clean, append-only additions.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Pre-merge gate rejects unevidenced/eval-failing amendments
- [ ] Structural Tier 2 scoped to the allowlist; no LLM-judge introduced
- [ ] Two real acceptance entries present in `.writ/refresh-log.md`
- [ ] `bash scripts/eval.sh` and `bash scripts/gen-skill.sh --check` clean; CI green

## Context for Agents

- **Error map rows:** [`technical-spec.md` → `## Error & Rescue Map` → `Eval check crash`, `Tier 2 scope miss`, `Missing transcript citation`]
- **Shadow paths:** [`technical-spec.md` → `## Shadow Paths` → `Eval gate`, `Tier 2 (high-traffic)`, `Log audit trail`]
- **Business rules:** [`spec.md` → `### Business Rules` → Rules 4, 5, 11]
- **Decisions:** [`technical-spec.md` → `### D7 — Two Enforcement Points, No New CI Wiring`, `### D8 — Tier 2 Is Structural, Bounded, and Not an LLM Judge`]
- **Concerns:** [`spec.md` → `### Technical Concerns` → Tier 2 cost/scope caveat]
- **Experience:** [`spec.md` → `### Primary User Journey` → Steps 4, 5, `spec.md` → `### State Catalog` → `Eval gate fails`, `High-traffic target`]
