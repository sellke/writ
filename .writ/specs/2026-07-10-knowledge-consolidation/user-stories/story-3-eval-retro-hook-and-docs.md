# Story 3: Eval, `/retro` Hook, and Docs

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Stories 1, 2

## User Story

**As a** Writ maintainer who needs the consolidation loop to be falsifiable
**I want to** executable eval scenarios, a shared-additive `eval.sh` registration, an optional read-only `/retro` nudge, and finalized docs
**So that** consolidation behavior is proven by evidence, discoverable at the right moment, and documented for future contributors

## Acceptance Criteria

- [ ] Given `scripts/eval-knowledge-consolidate.py` runs, when it emits PASS/FAIL TSV, then it covers dup merge proposed, contradiction surfaced, stale flagged, non-destructive default (no file written in dry-run), lineage preserved, and clean-ledger no-op.
- [ ] Given `scripts/eval.sh` is invoked, when checks run, then `check_knowledge_consolidate` executes the scenarios plus static assertions and is registered by exactly one line in the `CHECKS` array.
- [ ] Given `/retro` runs and a ledger growth signal is present, when it reaches the consolidation step, then it prints a read-only nudge to run `/knowledge --consolidate` and mutates no knowledge file.
- [ ] Given `/retro` runs with no growth signal or no `.writ/knowledge/`, when it reaches the consolidation step, then it skips gracefully with no nudge and no error.
- [ ] Given the docs are finalized, when a contributor reads `.writ/knowledge/README.md`, then the lineage frontmatter and consolidation workflow are documented consistently with the shipped command behavior.

## Implementation Tasks

- [ ] 3.1 Write `scripts/eval-knowledge-consolidate.py` modeled on `scripts/eval-phase-knowledge.py`, emitting PASS/FAIL TSV for: dup merge proposed, contradiction surfaced, stale flagged, non-destructive default, lineage preserved, and clean-ledger no-op.
- [ ] 3.2 Add a `check_knowledge_consolidate` function to `scripts/eval.sh` that runs the scenario harness and `require_literal` static assertions on the reducer, `commands/knowledge.md`, and `.writ/knowledge/README.md`.
- [ ] 3.3 Register the check by appending exactly one `knowledge-consolidate` line to the `CHECKS` array (shared-additive with the sibling evidence-bound-refresh spec).
- [ ] 3.4 Add the optional read-only `/retro` consolidation hook in `commands/retro.md`: nudge toward `/knowledge --consolidate` on a growth signal, mutate nothing, skip gracefully when absent.
- [ ] 3.5 Finalize `.writ/knowledge/README.md` and cross-doc consolidation-workflow guidance so lineage usage and the merge-never-append principle read consistently across surfaces.
- [ ] 3.6 Run `bash scripts/eval.sh --check=knowledge-consolidate` and the full `bash scripts/eval.sh`, then perform a real-ledger dry-run to confirm a reviewable diff (roadmap real-entry criterion).

## Notes

- Model the eval script on `scripts/eval-phase-knowledge.py`: temporary-directory fixtures, PASS/FAIL TSV consumed by a `check_*` bash function, `require_literal` static assertions.
- The `eval.sh` registry edit is shared-additive: one function definition plus one array line. Do not reorder or rewrite existing entries; sequential phase execution keeps this collision-free with the evidence-bound-refresh spec.
- The `/retro` hook is a nudge, not a mutation. Retro is a read-only reporting command; auto-consolidation there would violate non-destructive-by-default.
- The growth signal should be observable and cheap (e.g., entry count threshold or a dry-run reporting pending duplicate candidates) — never a heavyweight scan that slows retro.
- The parent spec and this story are not Complete until a real-ledger consolidation pass produces a reviewable PR diff; fixture evidence is mechanical only.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing (`scripts/eval.sh` green including the new check)
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [`technical-spec.md` → `## Error & Rescue Map` → `Dry-run diff generation`, `technical-spec.md` → `## Error & Rescue Map` → `Contradiction detection`, `technical-spec.md` → `## Error & Rescue Map` → `Malformed frontmatter`]
- **Shadow paths:** [`technical-spec.md` → `## Shadow Paths` → `Retro hook`, `technical-spec.md` → `## Shadow Paths` → `Eval scenarios`]
- **Business rules:** [`spec.md` → `### Business Rules` → Rule 10 (retro hook read-only, opt-in), `spec.md` → `### Business Rules` → Rule 12 (shared-additive eval registration), `spec.md` → `### Business Rules` → Rule 2 (non-destructive by default)]
- **Experience:** [`spec.md` → `## Detailed Requirements` → R6 (retro hook), `spec.md` → `## Detailed Requirements` → R7 (eval scenarios and registration), `technical-spec.md` → `### D9 — Retro Hook Is a Read-Only Nudge`, `technical-spec.md` → `### D10 — Eval Registration Is Shared-Additive`, `technical-spec.md` → `## File × Story Matrix` → S3 rows for scripts/eval-knowledge-consolidate.py, scripts/eval.sh, and commands/retro.md]
