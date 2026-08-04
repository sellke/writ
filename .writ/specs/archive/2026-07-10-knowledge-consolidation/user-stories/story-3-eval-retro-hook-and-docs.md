# Story 3: Eval, `/retro` Hook, and Docs

> **Status:** Completed ✅
> **Priority:** Medium
> **Dependencies:** Stories 1, 2

## User Story

**As a** Writ maintainer who needs the consolidation loop to be falsifiable
**I want to** executable eval scenarios, a shared-additive `eval.sh` registration, an optional read-only `/retro` nudge, and finalized docs
**So that** consolidation behavior is proven by evidence, discoverable at the right moment, and documented for future contributors

## Acceptance Criteria

- [x] Given `scripts/eval-knowledge-consolidate.py` runs, when it emits PASS/FAIL TSV, then it covers dup merge proposed, contradiction surfaced, stale flagged, non-destructive default (no file written in dry-run), lineage preserved, and clean-ledger no-op.
- [x] Given `scripts/eval.sh` is invoked, when checks run, then `check_knowledge_consolidate` executes the scenarios plus static assertions and is registered by exactly one line in the `CHECKS` array.
- [x] Given `/retro` runs and a ledger growth signal is present, when it reaches the consolidation step, then it prints a read-only nudge to run `/knowledge --consolidate` and mutates no knowledge file.
- [x] Given `/retro` runs with no growth signal or no `.writ/knowledge/`, when it reaches the consolidation step, then it skips gracefully with no nudge and no error.
- [x] Given the docs are finalized, when a contributor reads `.writ/knowledge/README.md`, then the lineage frontmatter and consolidation workflow are documented consistently with the shipped command behavior.

## Implementation Tasks

- [x] 3.1 Write `scripts/eval-knowledge-consolidate.py` modeled on `scripts/eval-phase-knowledge.py`, emitting PASS/FAIL TSV for: dup merge proposed, contradiction surfaced, stale flagged, non-destructive default, lineage preserved, and clean-ledger no-op. (Landed in Story 1 as the TDD driver; 11 scenarios.)
- [x] 3.2 Add a `check_knowledge_consolidate` function to `scripts/eval.sh` that runs the scenario harness and `require_literal` static assertions on the reducer, `commands/knowledge.md`, `commands/retro.md`, and `.writ/knowledge/README.md`.
- [x] 3.3 Register the check by appending exactly one `knowledge-consolidate` line to the `CHECKS` array (shared-additive with the sibling evidence-bound-refresh spec).
- [x] 3.4 Add the optional read-only `/retro` consolidation hook in `commands/retro.md`: nudge toward `/knowledge --consolidate` on a growth signal, mutate nothing, skip gracefully when absent.
- [x] 3.5 Finalize `.writ/knowledge/README.md` and cross-doc consolidation-workflow guidance so lineage usage and the merge-never-append principle read consistently across surfaces.
- [x] 3.6 Run `bash scripts/eval.sh --check=knowledge-consolidate` and the full `bash scripts/eval.sh`, then perform a real-ledger dry-run to confirm a reviewable diff (roadmap real-entry criterion — real ledger is an honest no-op; see note below).

## Notes

- Model the eval script on `scripts/eval-phase-knowledge.py`: temporary-directory fixtures, PASS/FAIL TSV consumed by a `check_*` bash function, `require_literal` static assertions.
- The `eval.sh` registry edit is shared-additive: one function definition plus one array line. Do not reorder or rewrite existing entries; sequential phase execution keeps this collision-free with the evidence-bound-refresh spec.
- The `/retro` hook is a nudge, not a mutation. Retro is a read-only reporting command; auto-consolidation there would violate non-destructive-by-default.
- The growth signal should be observable and cheap (e.g., entry count threshold or a dry-run reporting pending duplicate candidates) — never a heavyweight scan that slows retro.
- The parent spec and this story are not Complete until a real-ledger consolidation pass produces a reviewable PR diff; fixture evidence is mechanical only.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing (`scripts/eval.sh` green including the new check — full suite 0 findings, 0 run errors)
- [x] Code reviewed
- [x] Documentation updated

## Roadmap Real-Entry Criterion — Honest Status

The consolidation **mechanism** is complete and proven: the reducer, the gated command mode, bidirectional lineage, the eval scenarios (11/11), and the `/retro` nudge all ship and pass. A real-ledger dry-run (`python3 scripts/knowledge-consolidate.py --dry-run`) runs cleanly and produces a reviewable proposal.

Against the current 7 real ledger entries that proposal is an **honest no-op**: no two entries exceed the conservative duplicate threshold, no contradictions exist, and no entry meets a stale signal (every entry's `related_artifacts` still resolve). Per the technical spec's own edge case ("Real ledger has no duplicates yet → report an honest no-op; the roadmap real-entry criterion stays pending until real entries qualify"), no real entries were force-merged. An actual human-approved merge of real entries is a future demonstration/handoff once the ledger accumulates a genuine duplicate — forcing one now would violate the merge-never-append and non-destructive principles this spec exists to protect.

## Context for Agents

- **Error map rows:** [`technical-spec.md` → `## Error & Rescue Map` → `Dry-run diff generation`, `technical-spec.md` → `## Error & Rescue Map` → `Contradiction detection`, `technical-spec.md` → `## Error & Rescue Map` → `Malformed frontmatter`]
- **Shadow paths:** [`technical-spec.md` → `## Shadow Paths` → `Retro hook`, `technical-spec.md` → `## Shadow Paths` → `Eval scenarios`]
- **Business rules:** [`spec.md` → `### Business Rules` → Rule 10 (retro hook read-only, opt-in), `spec.md` → `### Business Rules` → Rule 12 (shared-additive eval registration), `spec.md` → `### Business Rules` → Rule 2 (non-destructive by default)]
- **Experience:** [`spec.md` → `## Detailed Requirements` → R6 (retro hook), `spec.md` → `## Detailed Requirements` → R7 (eval scenarios and registration), `technical-spec.md` → `### D9 — Retro Hook Is a Read-Only Nudge`, `technical-spec.md` → `### D10 — Eval Registration Is Shared-Additive`, `technical-spec.md` → `## File × Story Matrix` → S3 rows for scripts/eval-knowledge-consolidate.py, scripts/eval.sh, and commands/retro.md]
