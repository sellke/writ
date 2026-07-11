# Phase 7: Knowledge Consolidation

> **Status:** Implemented — mechanism complete; roadmap real-entry criterion (Success Criterion 8) pending a genuine real-ledger duplicate. The real ledger currently yields an honest no-op, so no real entries were force-merged.
> **Created:** 2026-07-10
> **Owner:** @AdamSellke
> **Phase:** 7 — Compounding Layer
> **Dependencies:** []
> **Source:** `.writ/product/roadmap.md` Phase 7 — feature "Knowledge consolidation"
> **Governing ADRs:** `adr-011-memory-interop-markdown-canonical.md` (consolidation policy), `adr-005-knowledge-substrate-markdown-over-database.md` (junk-drawer risk at scale)

---

## Specification Contract

**Deliverable:** Add a consolidation pass to the knowledge ledger — `/knowledge --consolidate` (with an optional `/retro` advisory hook) that merges duplicate entries, surfaces contradictions, and prunes stale entries under a single principle: **merge, never append.** A log grows unbounded; a merged document stays searchable. Markdown in, markdown out, reviewable as a PR diff. Consolidation populates the schema-ready but currently-unused lineage frontmatter (`superseded_by` / `replaces`) to preserve provenance.

**Origin:** Phase 7 — Compounding Layer in `.writ/product/roadmap.md`, feature "Knowledge consolidation," governed by ADR-011 (which names the append-only-with-no-consolidation gap explicitly and sets the Phase 7 policy) and ADR-005 (which flags junk-drawer risk beyond ~100 entries — consolidation is the mitigation).

**Must Include:** A non-destructive-by-default reducer that reads the markdown ledger, proposes merges, surfaces contradiction pairs, flags stale entries on observable signals, and emits a reviewable diff — writing nothing until a human approves. Approved merges preserve provenance via bidirectional `replaces` / `superseded_by` lineage frontmatter.

**Hardest Constraint:** Nothing is retired, merged, or rewritten without an explicit human-approved, PR-reviewable diff. Consolidation must never silently discard a durable fact, never auto-resolve a contradiction, and never prune on age alone. "Reviewable PR diff" is the contract, not a nicety.

### Experience Design

- **Entry point:** `/knowledge --consolidate` (new Step-2 routing branch) inspects the whole ledger and proposes changes; an optional `/retro` step nudges toward it when growth signals appear.
- **Happy path:** Scan all four categories → detect duplicate pairs, contradiction pairs, and stale entries → present a proposal with a preview diff → human approves → apply approved changes with lineage frontmatter → the working tree carries a reviewable PR diff.
- **Moment of truth:** A ledger that was quietly accumulating near-duplicates becomes a smaller set of merged, provenance-linked documents that still answer every prior query — and the change is auditable line-by-line in a diff.
- **Feedback model:** A dry-run always precedes any write. The proposal report enumerates every merge, contradiction, and stale flag with the evidence that triggered it; the apply step reports the exact files written and the lineage recorded.
- **Error experience:** A malformed or unparseable entry is skipped with a named reason, never silently dropped or rewritten. A weak duplicate signal below threshold is left alone. Any ambiguity that would require judgment is surfaced to the human, not resolved by the reducer.
- **Non-destructive default:** `--consolidate` and the reducer both default to dry-run. Writing requires an explicit apply after approval. There is no flag that retires an entry without a human-visible diff.

### Business Rules

1. Merge, never append: consolidation reduces the ledger to fewer, richer documents; it never adds a new parallel entry to "cover" an existing fact.
2. Non-destructive by default: the reducer and the command both dry-run first. No file is written, rewritten, or retired without explicit human approval.
3. The reviewable diff is the deliverable. Every applied change must be inspectable as a unified/working-tree diff before it becomes a commit.
4. Merges preserve provenance bidirectionally: the surviving canonical entry records `replaces: [slug, ...]`; each merged-away entry becomes a tombstone carrying `superseded_by: <canonical-slug>`.
5. Contradictions are surfaced, never auto-resolved. When two entries assert conflicting facts, the reducer flags the pair for human review and applies no change.
6. Stale is defined by observable signal, never by age alone. An entry is stale only when it is already superseded, all its `related_artifacts` paths no longer exist, or it is dominated by a newer merged entry. Stale entries are flagged, not auto-pruned.
7. Duplicate detection reuses the proven token-overlap (Jaccard) approach from `scripts/phase-state.py`; consolidation compares entry-to-entry within a category rather than candidate-to-ledger.
8. Consolidation spans all four categories (`decisions`, `conventions`, `glossary`, `lessons`), not just `lessons/` — Phase 6 writeback only touches `lessons/`; consolidation is broader.
9. Glossary entries (filename = addressable term slug) are always tombstoned on merge, never deleted, because their filenames are referenced identifiers.
10. The `/retro` hook is a read-only, opt-in advisory nudge. It never mutates the ledger and never runs consolidation automatically.
11. `/knowledge --consolidate` remains a knowledge-documentation command: it produces knowledge docs and diffs only, and does not offer to implement, build, or execute anything.
12. Eval registration is a shared-additive append: one `check_*` function plus one `CHECKS` array line, coordinated with the sibling evidence-bound-refresh spec by sequential phase execution.

### Success Criteria

1. A fixture ledger containing a genuine duplicate pair produces a proposed merge into one canonical entry with a preview diff, and no file changes in dry-run.
2. A fixture ledger containing two conflicting entries surfaces a contradiction pair for human review and applies no automatic change.
3. A fixture entry whose `related_artifacts` all point to missing paths is flagged stale; an entry that is merely old but still referenced is not.
4. On human approval, an applied merge writes `replaces` on the canonical entry and `superseded_by` on each tombstone, and the result is a reviewable working-tree diff.
5. Consolidation operates across all four categories, and a clean ledger with no duplicates, contradictions, or stale entries is a valid no-op that changes no file.
6. `scripts/eval-knowledge-consolidate.py` scenarios (dup merge proposed, contradiction surfaced, stale flagged, non-destructive default, lineage preserved, clean-ledger no-op) pass and are registered in `scripts/eval.sh`.
7. `/retro` offers the consolidation nudge only when a growth signal is present, and running `/retro` mutates no knowledge file.
8. The roadmap criterion — "first knowledge consolidation pass merges or prunes real entries with a reviewable PR diff" — is satisfied against real ledger entries, not only fixtures, before the spec is marked Complete.

### Scope Boundaries

**Included:**
- A markdown-in/markdown-out consolidation reducer (`scripts/knowledge-consolidate.py`) with dry-run and apply modes.
- Duplicate detection, contradiction surfacing, and stale flagging across all four knowledge categories.
- Merge-proposal generation and a reviewable preview diff.
- Bidirectional lineage frontmatter (`replaces` / `superseded_by`) and a tombstone convention.
- A `/knowledge --consolidate` command mode with a human approval gate.
- An optional, read-only `/retro` advisory hook.
- Eval scenarios plus a shared-additive `eval.sh` registration.
- Lineage and consolidation-workflow documentation in `.writ/knowledge/README.md`.

**Excluded:**
- Any external index, database, embedding store, or retrieval engine (ADR-011 Phase 8; ADR-005 zero-infrastructure driver).
- Automatic contradiction resolution or age-based pruning.
- Auto-mutation of the ledger from `/retro` or any unattended loop.
- Physical deletion of tombstones (a later, separate, explicit human action).
- Changes to Phase 6 writeback (`scripts/phase-state.py knowledge-writeback`) behavior beyond reusing its duplicate-detection approach.
- Skill lifecycle and evidence-bound `/refresh-command` work (sibling Phase 7 specs).

### Technical Concerns

- Contradiction detection is heuristic and cannot be trusted to auto-resolve; the reducer must stay conservative and defer to a human. False positives are acceptable (a human dismisses them); silent auto-resolution is not.
- Duplicate detection false-positives would merge two genuinely distinct facts. The threshold must be conservative and every proposed merge must be human-approved against a diff.
- The knowledge schema is loosely enforced markdown; entries may have missing or malformed frontmatter. The parser must be tolerant and skip-with-reason rather than crash or corrupt.
- The "reviewable PR diff" is only real once the working tree changes; dry-run shows a preview diff, apply produces the git-visible one. Both must be honest about what changed.
- The sibling evidence-bound-refresh spec also appends to `scripts/eval.sh`'s registry. Sequential phase execution makes both appends safe; parallel edits would collide.

### Recommendations

- Reuse `scripts/phase-state.py`'s `_tokens` + Jaccard approach directly rather than inventing a new similarity metric; it is already proven for dedup and keeps behavior consistent across the substrate.
- Keep the reducer a standalone Python script with a stable JSON/markdown contract so the command orchestrates it rather than reimplementing detection in prose.
- Prefer tombstones over deletion by default; they preserve inbound links and make provenance auditable, and deletion can always follow later as an explicit human step.
- Keep `/retro`'s hook a nudge, not a mutation — retro is a reporting command, and consolidation demands human review, so auto-consolidation there would violate non-destructive-by-default.
- Model `scripts/eval-knowledge-consolidate.py` on `scripts/eval-phase-knowledge.py` (PASS/FAIL TSV consumed by a `check_*` bash function) for consistency.

### Cross-Spec Review

This spec is independent (`Dependencies: []`). Phase 6's knowledge writeback (`2026-07-09-phase6-autonomy-ceiling`) already shipped and provides the input: it appends evidence-bound lessons to `.writ/knowledge/lessons/` using a write-guard `_is_duplicate`; consolidation is the complementary maintenance loop that retires and merges what accumulates. The sibling Phase 7 evidence-bound-refresh spec shares an additive `eval.sh` registry edit — sequential execution keeps both appends safe. Skill-lifecycle and skill-extraction Phase 7 specs are disjoint in files and scope.

---

## Experience Design

### Primary User Journey

1. The maintainer runs `/knowledge --consolidate` (directly, or after a `/retro` nudge flags ledger growth).
2. Writ runs `scripts/knowledge-consolidate.py --dry-run` over `.writ/knowledge/`, reading every entry across all four categories.
3. The reducer returns a proposal: duplicate merge candidates (per category), contradiction pairs, and stale flags — each with the evidence that triggered it — plus a preview diff of the proposed file changes.
4. Writ presents the proposal and asks for approval, per category or per proposal, via `AskQuestion`. Contradictions are presented for human decision only; the reducer proposes no automatic resolution.
5. On approval, Writ invokes the reducer's apply mode, which writes the canonical merged entry with `replaces`, rewrites each merged-away entry into a tombstone with `superseded_by`, and leaves stale-flagged entries untouched unless the human explicitly approves retirement.
6. The working tree now carries a reviewable diff; the human inspects it and commits it as a PR.
7. A clean ledger with nothing to consolidate is a valid no-op: the command reports "nothing to consolidate" and writes no file.

### State Catalog

| State | User-visible behavior |
|---|---|
| No `.writ/` directory | Reuse the existing `/knowledge` guard: instruct to run `/initialize`, write nothing |
| Empty ledger | Report "no entries to consolidate" and stop |
| Clean ledger (no signals) | Valid no-op: "nothing to consolidate," no file written |
| Duplicate pair found | Propose a merge into one canonical entry with a preview diff; await approval |
| Contradiction pair found | Surface both entries and the conflicting assertions for human review; apply nothing |
| Stale entry found | Flag with the observable signal (superseded / dangling artifacts / dominated); await explicit retirement approval |
| Malformed entry | Skip with a named reason; never rewrite or drop it silently |
| Approval given | Apply approved changes, write lineage, report files changed and the reviewable diff |
| Approval declined | Write nothing; the ledger is unchanged |
| Retro growth signal | `/retro` prints a read-only nudge suggesting `/knowledge --consolidate`; mutates nothing |

### Interaction and Output Rules

- Output is concise, terminal-oriented Markdown; no new UI is introduced.
- Dry-run always precedes apply. The command never writes before an approval gate.
- Every proposed change names the entries involved and the signal that triggered it.
- Contradictions are presented as decisions, never as pre-resolved outcomes.
- Stale flags cite the observable signal; age alone is never shown as a reason.
- The apply step reports exactly which files were written and what lineage was recorded, so the diff is self-explanatory.

---

## Detailed Requirements

### R1 — Consolidation Reducer (`scripts/knowledge-consolidate.py`)

- A standalone Python script that reads all entries under `.writ/knowledge/{decisions,conventions,glossary,lessons}/`, ignoring `README.md` and `.gitkeep`.
- Parses each entry's frontmatter (`category`, `tags`, `created`, `related_artifacts`, and optional `superseded_by` / `replaces`) and body sections (`# Title`, `## TL;DR`, `## Context`, `## Detail`, `## Related`), tolerating missing or malformed structure by skipping with a named reason.
- Detects duplicate merge candidates using the `_tokens` + Jaccard overlap approach reused from `scripts/phase-state.py`, comparing entries pairwise within the same category above a conservative threshold.
- Surfaces contradiction pairs (high subject overlap, diverging assertions) for human review without proposing a resolution.
- Flags stale entries on observable signals only: already superseded, all `related_artifacts` missing, or dominated by a newer merged entry.
- Defaults to `--dry-run`: emits a markdown proposal report plus a preview unified diff and writes nothing. `--apply` writes approved changes.
- Emits machine-readable output (JSON or TSV) sufficient for the command to present proposals and for `eval` scenarios to assert behavior.

### R2 — Merge, Provenance, and Tombstones

- A merge combines two or more duplicate entries into one canonical entry (the richer/newer entry, or a synthesized union) that gains `replaces: [superseded-slug, ...]`.
- Each merged-away entry is rewritten in place into a tombstone: its frontmatter retains `category`/`created` and gains `superseded_by: <canonical-slug>`; its body is replaced with a one-line pointer to the canonical entry.
- Tombstones are retained by default to preserve inbound links and provenance; physical deletion is out of scope.
- Glossary entries are always tombstoned on merge (never deleted), because their filenames are addressable identifiers.
- Lineage is bidirectional and consistent: every `replaces` entry has a matching `superseded_by` tombstone, and vice versa.

### R3 — Non-Destructive Default and Reviewable Diff

- Both the reducer and `/knowledge --consolidate` default to dry-run; no write occurs without explicit human approval.
- Dry-run produces a preview unified diff of proposed changes (via `difflib`); apply produces the real git working-tree diff.
- The apply step must leave the working tree in a state a human can review and commit as a PR; it does not commit.
- No flag or path retires, merges, or rewrites an entry without a human-visible diff.

### R4 — `/knowledge --consolidate` Command Mode

- Add a new Step-2 routing branch in `commands/knowledge.md` for `--consolidate` (alongside `--list` / `--read`).
- The mode runs the reducer dry-run, presents merges / contradictions / stale flags, and gates any write on `AskQuestion` approval.
- On approval, it invokes the reducer's apply mode and reports the files changed and lineage recorded.
- Update the Invocation table, and keep the Completion section's terminal constraint (knowledge docs and diffs only; do not implement).
- Update `.writ/knowledge/README.md` to document the lineage frontmatter (`superseded_by` / `replaces`) usage and the consolidation workflow.

### R5 — Contradiction and Stale Semantics

- Contradiction: two entries with high subject overlap but conflicting TL;DR/Detail assertions are surfaced as a review pair; the reducer proposes no resolution and applies no change.
- Stale: an entry qualifies only via an observable signal (superseded tombstone, all `related_artifacts` paths missing on disk, or dominated by a newer merged entry). Age/`created` alone never qualifies.
- Both are advisory in dry-run and require explicit human approval before any file changes.

### R6 — Optional `/retro` Advisory Hook

- Add a read-only step to `commands/retro.md` that, when a ledger growth signal is present (e.g., entry count crosses a threshold or a dry-run reports pending duplicate candidates), suggests running `/knowledge --consolidate`.
- The hook is opt-in and advisory: it prints a nudge and mutates no knowledge file, consistent with retro's read-only reporting nature.
- Gracefully skip when `.writ/knowledge/` is absent or empty.

### R7 — Eval Scenarios and Shared-Additive Registration

- Create `scripts/eval-knowledge-consolidate.py` emitting PASS/FAIL TSV scenarios: dup merge proposed, contradiction surfaced, stale flagged, non-destructive default (dry-run writes no file), lineage preserved (replaces + superseded_by), and clean-ledger no-op.
- Add one `check_knowledge_consolidate` function to `scripts/eval.sh` (scenario harness plus `require_literal` static assertions on the reducer, command, and README) and append one line to the `CHECKS` array.
- The registry edit is shared-additive with the sibling evidence-bound-refresh spec; sequential phase execution keeps both appends safe.

---

## Implementation Approach

### Architecture

`/knowledge --consolidate` orchestrates; `scripts/knowledge-consolidate.py` does the mechanical work:

`scan ledger → detect (duplicates | contradictions | stale) → propose + preview diff → human approval → apply lineage → reviewable working-tree diff`

The reducer is the single writer of detection and file rewriting. The command owns presentation and the approval gate. Markdown in git remains the canonical system of record (ADR-011); the reducer never introduces an index or database.

### Detection Reuse

Duplicate detection reuses `scripts/phase-state.py`'s `_tokens` (stopword-filtered token set) and Jaccard overlap. Phase 6 used it as a write-guard (candidate vs. ledger) to reject noisy appends; consolidation applies the same metric pairwise within a category to find merge candidates among existing entries. Consistency of the similarity metric across the substrate is deliberate.

### Provenance Model

```yaml
# canonical (surviving) entry gains:
replaces:
  - 2026-04-24-superseded-slug-a
  - 2026-04-24-superseded-slug-b

# each merged-away entry becomes a tombstone:
superseded_by: 2026-04-24-canonical-slug
```

Bidirectional lineage makes provenance auditable and keeps inbound links alive. Tombstone bodies point forward in one line.

### Validation Strategy

This repository has no application test suite. Verification is script and fixture based:

- `python3 scripts/knowledge-consolidate.py --dry-run` against fixture ledgers
- `python3 scripts/eval-knowledge-consolidate.py` (PASS/FAIL TSV)
- `bash scripts/eval.sh --check=knowledge-consolidate` and full `bash scripts/eval.sh`
- a real-ledger dry-run to satisfy the roadmap's real-entry criterion before Complete

---

## Files in Scope

### Primary (single-writer for this spec)

- `commands/knowledge.md` — add the `--consolidate` Step-2 routing branch
- `scripts/knowledge-consolidate.py` (new) — the consolidation reducer
- `commands/retro.md` — optional read-only consolidation advisory hook
- `scripts/eval-knowledge-consolidate.py` (new) — eval scenarios
- `.writ/knowledge/README.md` — lineage frontmatter + consolidation workflow docs

### Shared-Additive

- `scripts/eval.sh` — append one `check_knowledge_consolidate` function + one `CHECKS` array line

### Reference (read-only, not edited)

- `scripts/phase-state.py` — reuse `_tokens` + Jaccard duplicate-detection approach
- `scripts/eval-phase-knowledge.py` — model the eval script on it
- `.writ/knowledge/{decisions,conventions,glossary,lessons}/*.md` — real ledger input

---

## Story Plan

1. **Consolidation reducer** — Dependencies: None
2. **`/knowledge --consolidate` command mode** — Dependencies: Story 1
3. **Eval, `/retro` hook, and docs** — Dependencies: Stories 1, 2

---

## Deliverables

- [x] `scripts/knowledge-consolidate.py` detects duplicates, contradictions, and stale entries across all four categories
- [x] Reducer defaults to dry-run and emits a reviewable preview diff; `--apply` writes approved changes
- [x] Merges write bidirectional `replaces` / `superseded_by` lineage with tombstones
- [x] `/knowledge --consolidate` Step-2 routing presents proposals and gates writes on human approval
- [x] Contradictions surfaced for review, never auto-resolved; stale flagged on observable signal only
- [x] `.writ/knowledge/README.md` documents lineage frontmatter and the consolidation workflow
- [x] `scripts/eval-knowledge-consolidate.py` scenarios pass and are registered in `scripts/eval.sh`
- [x] Optional `/retro` advisory hook nudges toward consolidation without mutating the ledger
- [ ] A real-ledger consolidation pass produces a reviewable PR diff (roadmap criterion) before Complete — **pending:** the mechanism produces a reviewable dry-run against the real ledger, but the current 7 entries yield an honest no-op (no genuine duplicate/contradiction/stale). Awaits a real qualifying duplicate; not force-merged.
