# Story 1: Consolidation Reducer

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer whose knowledge ledger is quietly accumulating near-duplicates
**I want to** a reducer that reads the whole ledger and proposes merges, contradictions, and stale flags with a reviewable diff
**So that** the ledger can be consolidated — merge, never append — without any write happening before I approve it

## Acceptance Criteria

- [ ] Given a fixture ledger with a genuine duplicate pair in one category, when the reducer runs in dry-run, then it proposes a single merge into one canonical entry with a preview diff and writes no file.
- [ ] Given a fixture ledger with two entries that assert conflicting facts, when the reducer runs, then it surfaces the pair as a contradiction for human review and proposes no resolution.
- [ ] Given a fixture entry whose `related_artifacts` all point to missing paths, when the reducer evaluates staleness, then it flags the entry with the observable signal, while a merely-old-but-still-referenced entry is not flagged.
- [ ] Given the `--apply` mode runs on an approved merge, when it writes, then the canonical entry gains `replaces: [...]` and each merged-away entry becomes a tombstone with `superseded_by: <canonical-slug>`.
- [ ] Given a clean ledger or a malformed entry, when the reducer runs, then a clean ledger is a valid no-op that changes no file and a malformed entry is skipped with a named reason rather than crashing or being rewritten.

## Implementation Tasks

- [ ] 1.1 Write failing fixture ledgers and a driver that exercises the reducer: a duplicate pair, a contradiction pair, a stale entry (dangling `related_artifacts`), a clean ledger, and a malformed entry — asserting dry-run writes zero files.
- [ ] 1.2 Implement tolerant markdown parsing in `scripts/knowledge-consolidate.py`: frontmatter (`category`, `tags`, `created`, `related_artifacts`, optional `superseded_by`/`replaces`) and body sections, skipping malformed entries with a named reason.
- [ ] 1.3 Implement duplicate detection reusing the `_tokens` + Jaccard overlap approach from `scripts/phase-state.py`, comparing entries pairwise within each category above a conservative threshold.
- [ ] 1.4 Implement contradiction surfacing (high subject overlap, diverging assertions) and observable-signal stale flagging (superseded, all `related_artifacts` missing, dominated) — advisory only, no resolution or pruning.
- [ ] 1.5 Implement merge-proposal generation, tombstone/lineage construction (`replaces` ↔ `superseded_by`), and a preview unified diff via `difflib`; glossary merges always tombstone.
- [ ] 1.6 Implement the `--dry-run` (default, proposals + preview diff, no write) vs. `--apply` (writes approved changes) boundary and machine-readable output (JSON/TSV) for the command and eval to consume.
- [ ] 1.7 Run the reducer against every fixture, confirm all acceptance criteria pass, and confirm dry-run leaves the fixture ledgers byte-identical.

## Notes

- Reuse, do not reinvent: `scripts/phase-state.py` already proves `_tokens` (stopword-filtered token set) + Jaccard overlap for dedup. Phase 6 used it as a write-guard (candidate vs. ledger); consolidation applies the same metric pairwise among existing entries within a category.
- Consolidation spans all four categories (`decisions`, `conventions`, `glossary`, `lessons`), unlike Phase 6 writeback which only touches `lessons/`.
- Dry-run is the default and must be provably non-destructive. Every dry-run scenario asserts zero file changes.
- Contradiction detection is heuristic; false positives are acceptable (a human dismisses them) but silent auto-resolution is forbidden.
- Stale is signal-based only. `created` age alone never qualifies an entry as stale.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing (fixtures + reducer dry-run/apply)
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [`technical-spec.md` → `## Error & Rescue Map` → `Parse knowledge entry`, `technical-spec.md` → `## Error & Rescue Map` → `Malformed frontmatter`, `technical-spec.md` → `## Error & Rescue Map` → `Duplicate detection false-positive`, `technical-spec.md` → `## Error & Rescue Map` → `Contradiction detection`, `technical-spec.md` → `## Error & Rescue Map` → `Dry-run diff generation`]
- **Shadow paths:** [`technical-spec.md` → `## Shadow Paths` → `Duplicate detection`, `technical-spec.md` → `## Shadow Paths` → `Stale flagging`]
- **Business rules:** [`spec.md` → `### Business Rules` → Rule 1 (merge, never append), `spec.md` → `### Business Rules` → Rule 2 (non-destructive by default), `spec.md` → `### Business Rules` → Rule 6 (stale by signal), `spec.md` → `### Business Rules` → Rule 7 (reuse Jaccard), `spec.md` → `### Business Rules` → Rule 8 (all four categories)]
- **Experience:** [`spec.md` → `## Detailed Requirements` → R1 (reducer), `spec.md` → `## Detailed Requirements` → R5 (contradiction/stale semantics), `technical-spec.md` → `### D3 — Duplicate Detection Reuses Phase-State Jaccard`, `technical-spec.md` → `## File × Story Matrix` → S1 rows for scripts/knowledge-consolidate.py]
