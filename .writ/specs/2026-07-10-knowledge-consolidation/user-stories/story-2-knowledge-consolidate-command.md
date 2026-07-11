# Story 2: `/knowledge --consolidate` Command Mode

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer ready to tidy the ledger
**I want to** run `/knowledge --consolidate`, review proposed merges/contradictions/stale flags, and approve them before anything is written
**So that** consolidation happens through a human-gated, PR-reviewable diff rather than a silent mutation

## Acceptance Criteria

- [x] Given `/knowledge --consolidate` is invoked, when Step 2 routes it, then it runs the reducer dry-run and presents proposed merges, contradiction pairs, and stale flags without writing any file.
- [x] Given proposals are presented, when the user is asked to proceed, then the command gates every write on explicit `AskQuestion` approval and writes nothing if approval is declined.
- [x] Given the user approves a merge, when the command applies it, then it invokes the reducer's apply mode, records `replaces` on the canonical entry and `superseded_by` on each tombstone, and reports the exact files changed.
- [x] Given a contradiction pair is surfaced, when it is presented, then the command asks the human to decide and never applies an automatic resolution.
- [x] Given the command completes, when `.writ/knowledge/README.md` is consulted, then it documents the lineage frontmatter (`superseded_by`/`replaces`) usage and the consolidation workflow.

## Implementation Tasks

- [x] 2.1 Create a fixture ledger (duplicate pair + contradiction pair + stale entry) and an expected proposal transcript to drive manual walk-through and later eval assertions. (Fixtures live in `scripts/eval-knowledge-consolidate.py`; a manual throwaway-fixture walk-through confirmed the preview/apply diff.)
- [x] 2.2 Add the `--consolidate` Step-2 routing branch in `commands/knowledge.md`, alongside `--list` / `--read`, that runs `scripts/knowledge-consolidate.py --dry-run`.
- [x] 2.3 Define proposal presentation (merges / contradictions / stale flags with triggering evidence) and the `AskQuestion` human approval gate, with contradictions presented as decisions only.
- [x] 2.4 Wire the approved-apply path to the reducer's `--apply` mode, writing `replaces`/`superseded_by` lineage and reporting the reviewable working-tree diff.
- [x] 2.5 Update `.writ/knowledge/README.md` to document lineage frontmatter (`superseded_by`/`replaces`) usage and the consolidation workflow.
- [x] 2.6 Update the `commands/knowledge.md` Invocation table and Completion section (terminal constraint: knowledge docs and diffs only; do not implement).
- [x] 2.7 Verify the command mode against the fixture ledger, run the reducer apply, and confirm the resulting `git diff` is a clean, reviewable PR diff.

## Notes

- The command orchestrates; the reducer (Story 1) does the mechanical detection and file rewriting. Do not reimplement detection in command prose.
- Dry-run always precedes apply. There is no path from `--consolidate` to a write that skips the approval gate.
- Approval may be per-category or per-proposal; declining leaves the ledger unchanged.
- The Step-2 routing branch lives with the existing read-only modes (`--list`, `--read`) but consolidation is a gated write mode — its default behavior (dry-run) is read-only, and only the approved apply mutates files.
- Keep the terminal constraint intact: `/knowledge --consolidate` produces knowledge docs and diffs, and does not offer to implement what was captured.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing (fixture walk-through + apply diff review)
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [`technical-spec.md` → `## Error & Rescue Map` → `Merge conflict (proposal)`, `technical-spec.md` → `## Error & Rescue Map` → `Lineage write`, `technical-spec.md` → `## Error & Rescue Map` → `Dry-run diff generation`]
- **Shadow paths:** [`technical-spec.md` → `## Shadow Paths` → `Command routing`, `technical-spec.md` → `## Shadow Paths` → `Approval and apply`]
- **Business rules:** [`spec.md` → `### Business Rules` → Rule 2 (non-destructive by default), `spec.md` → `### Business Rules` → Rule 3 (reviewable diff is the deliverable), `spec.md` → `### Business Rules` → Rule 4 (bidirectional provenance), `spec.md` → `### Business Rules` → Rule 5 (contradictions surfaced), `spec.md` → `### Business Rules` → Rule 9 (glossary tombstones), `spec.md` → `### Business Rules` → Rule 11 (terminal constraint)]
- **Experience:** [`spec.md` → `## Detailed Requirements` → R3 (non-destructive default and reviewable diff), `spec.md` → `## Detailed Requirements` → R4 (command mode), `spec.md` → `### Primary User Journey`, `technical-spec.md` → `### D2 — Non-Destructive by Default`, `technical-spec.md` → `### D4 — Lineage and Tombstone Policy`, `technical-spec.md` → `## File × Story Matrix` → S2 rows for commands/knowledge.md and .writ/knowledge/README.md]
