# Phase 7: Knowledge Consolidation (Lite)

> Source: `.writ/specs/2026-07-10-knowledge-consolidation/spec.md`
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** A consolidation pass over the knowledge ledger — `/knowledge --consolidate` plus a `scripts/knowledge-consolidate.py` reducer — that merges duplicates, surfaces contradictions, and prunes stale entries. Merge, never append. Markdown in, markdown out, reviewable as a PR diff.

**Implementation Approach:**
- Reducer reads all entries under `.writ/knowledge/{decisions,conventions,glossary,lessons}/`, tolerating malformed frontmatter by skipping with a reason.
- Reuse `scripts/phase-state.py`'s `_tokens` + Jaccard overlap for duplicate detection; compare entries pairwise within a category.
- Default to `--dry-run`: emit a markdown proposal + preview unified diff (`difflib`), write nothing. `--apply` writes approved changes.
- Merges write bidirectional lineage: canonical entry gains `replaces: [...]`; each merged-away entry becomes a tombstone with `superseded_by: <canonical-slug>`.
- Add a `--consolidate` Step-2 routing branch in `commands/knowledge.md` that runs the dry-run, presents proposals, and gates writes on `AskQuestion` approval.

**Files in Scope:**
- `scripts/knowledge-consolidate.py` (new), `scripts/eval-knowledge-consolidate.py` (new)
- `commands/knowledge.md`, `commands/retro.md`, `.writ/knowledge/README.md`
- `scripts/eval.sh` (shared-additive: one `check_*` fn + one `CHECKS` line)

**Error Handling:**
- Malformed/unparseable entry → skip with named reason; never rewrite or drop silently.
- Weak duplicate signal below threshold → leave alone.
- Contradiction → surface for human review; never auto-resolve.
- Stale only on observable signal (superseded / dangling artifacts / dominated); never age alone.
- No write without an explicit human-approved, reviewable diff.

**Integration Points:**
- Consumes Phase 6 writeback output (`.writ/knowledge/lessons/`) and spans all four categories.
- `/knowledge --consolidate` orchestrates the reducer; `/retro` only nudges (read-only).

---

## For Review Agents

**Acceptance Criteria:**
1. A duplicate pair produces a proposed merge with a preview diff; dry-run writes no file.
2. A conflicting pair surfaces a contradiction for human review and applies no change.
3. An entry with all `related_artifacts` missing is flagged stale; a merely-old-but-referenced entry is not.
4. On approval, an applied merge writes `replaces` + `superseded_by` and yields a reviewable diff.
5. A clean ledger is a valid no-op that changes no file; consolidation spans all four categories.
6. Eval scenarios pass and are registered in `scripts/eval.sh`; `/retro` nudge mutates nothing.

**Business Rules:**
- Merge, never append; non-destructive by default; the reviewable diff is the deliverable.
- Provenance is bidirectional (`replaces` ↔ `superseded_by`); glossary merges always tombstone, never delete.
- Contradictions are surfaced, never auto-resolved; stale is signal-based, never age-based.
- Duplicate detection reuses phase-state Jaccard; scope is all four categories.
- `/retro` hook is read-only and opt-in; `--consolidate` produces docs and diffs only.
- Tombstone deletion and any external index/database are out of scope.

**Experience Design:**
- Entry: `/knowledge --consolidate` (or a `/retro` nudge).
- Happy path: scan → detect → propose + preview diff → approve → apply lineage → reviewable diff.
- Moment of truth: an accumulating ledger becomes fewer merged, provenance-linked documents.
- Error: malformed entry skipped with reason; contradiction deferred to human.

**Drift Anchors:**
- Any auto-resolution of contradictions, age-based pruning, or write without a human-approved diff is contract drift.
- Any external index, database, or `/retro` auto-mutation is out of scope.

---

## For Testing Agents

**Success Criteria:**
1. Fixture ledgers prove dup merge, contradiction surfacing, stale flagging, non-destructive default, and lineage preservation.
2. Clean-ledger no-op changes no file; malformed entry is skipped, not corrupted.
3. A real-ledger dry-run produces a reviewable diff (roadmap real-entry criterion).

**Shadow Paths to Verify:**
- **Happy path:** duplicate pair → proposed merge → approved apply → lineage written.
- **Nil input:** no `.writ/knowledge/` → graceful skip, no error.
- **Empty input:** empty ledger → "no entries to consolidate," no file.
- **Upstream error:** malformed frontmatter → skip with reason, no corruption.

**Edge Cases:**
- Duplicate-detection false positive → conservative threshold + human approval against diff.
- Glossary merge → tombstone (never delete) because filename is an identifier.
- Contradiction pair → surfaced as a decision, no automatic resolution.

**Coverage Requirements:**
- Detection, proposal, and lineage-write paths: 100% fixture coverage.
- Non-destructive default: every dry-run scenario asserts zero file changes.

**Test Strategy:**
- `python3 scripts/knowledge-consolidate.py --dry-run` on fixtures.
- `python3 scripts/eval-knowledge-consolidate.py`, `bash scripts/eval.sh --check=knowledge-consolidate`, full `bash scripts/eval.sh`.
