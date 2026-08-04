# Technical Specification: Phase 7 Knowledge Consolidation

> **Parent:** `../spec.md`
> **Status:** Not Started
> **Stories:** 1–3

## Architecture Summary

Knowledge consolidation is a reducer plus a thin command wrapper. `scripts/knowledge-consolidate.py` reads the markdown ledger, detects duplicates/contradictions/stale entries, proposes merges, and — only on apply — rewrites files with lineage frontmatter. `/knowledge --consolidate` orchestrates: dry-run, present proposals, gate on human approval, apply. Markdown in git stays the canonical system of record (ADR-011); no index or database is introduced.

```text
.writ/knowledge/**  (markdown in)
          │
          ▼
   parse (tolerant) ── skip malformed with reason
          │
          ▼
 detect: duplicates | contradictions | stale
          │
          ▼
 propose merges + preview diff  ◄── dry-run (default): writes nothing
          │
   human approval gate  (AskQuestion, via /knowledge --consolidate)
          │
          ▼
 apply: canonical(replaces) + tombstones(superseded_by)
          │
          ▼
 reviewable working-tree diff  (markdown out → PR)
```

## Design Decisions

### D1 — Merge, Never Append

Consolidation reduces the ledger to fewer, richer documents. It never adds a parallel entry to cover an existing fact. A log grows unbounded; a merged document stays searchable (ADR-011). Every operation either merges, tombstones, or flags — none of them append a fresh net-new entry.

### D2 — Non-Destructive by Default

Both the reducer and the command default to dry-run. Dry-run emits a markdown proposal and a preview unified diff (`difflib.unified_diff`) and writes nothing. `--apply` is the only path that mutates files, and the command reaches it only after an explicit `AskQuestion` approval. There is no flag that retires an entry without a human-visible diff.

Invariant: every dry-run scenario asserts the ledger is byte-identical before and after.

### D3 — Duplicate Detection Reuses Phase-State Jaccard

Reuse the proven approach from `scripts/phase-state.py`:

```python
def _tokens(text):            # stopword-filtered, len>2, lowercased word set
    ...
overlap = len(a & b) / len(a | b)   # Jaccard
```

Phase 6 used this as a write-guard (candidate statement vs. every ledger entry, overlap ≥ 0.5 → reject). Consolidation applies the same metric **pairwise among existing entries within the same category**, above a conservative threshold, to nominate merge candidates. A conservative threshold plus mandatory human approval bounds false-positive risk. The metric stays consistent across the substrate deliberately.

### D4 — Lineage and Tombstone Policy

Provenance is bidirectional and uses the schema-ready optional fields the README already documents (`superseded_by`, `replaces`), currently unused by any entry.

```yaml
# surviving canonical entry
---
category: lessons
tags: [...]
created: 2026-04-24
related_artifacts: [...]
replaces:
  - 2026-04-24-superseded-a
  - 2026-04-24-superseded-b
---

# each merged-away entry becomes a tombstone
---
category: lessons
created: 2026-04-24
superseded_by: 2026-04-24-canonical-slug
---

# Superseded

Merged into [canonical title](../lessons/2026-04-24-canonical-slug.md).
```

Rules:

- Every `replaces` slug has a matching `superseded_by` tombstone, and vice versa (bidirectional consistency).
- Tombstones are retained by default (preserve inbound links + provenance; make the diff auditable).
- Glossary entries are **always** tombstoned on merge, never deleted, because the filename is an addressable identifier.
- Physical deletion of tombstones is a separate, explicit, later human action — out of scope here.
- The canonical entry is the richer/newer of the pair (or a synthesized union); the choice is shown in the proposal.

### D5 — Contradiction Surfacing, Never Auto-Resolve

Two entries with high subject overlap (tags + title Jaccard) but diverging TL;DR/Detail assertions are surfaced as a contradiction pair. The reducer proposes **no** resolution and applies **no** change; the human decides. False positives are acceptable (dismissed by a human); silent auto-resolution is forbidden. Contradiction detection is intentionally heuristic and conservative.

### D6 — Stale by Observable Signal

An entry is stale only when at least one observable signal holds:

1. It is already superseded (has a `superseded_by` tombstone).
2. All of its `related_artifacts` paths no longer exist on disk (dangling provenance).
3. It is dominated by a newer merged entry that fully covers it.

`created` age alone never qualifies. Stale entries are **flagged** for human review; the reducer never auto-prunes.

### D7 — Scope Spans All Four Categories

Detection and proposal run across `decisions`, `conventions`, `glossary`, and `lessons`. Phase 6 writeback only touches `lessons/`; consolidation is the broader maintenance loop. `README.md` and `.gitkeep` are ignored. Duplicate/contradiction comparisons are within-category (a decision and a glossary term are not merge candidates).

### D8 — Markdown In, Markdown Out; Reviewable Diff Is the Deliverable

Input is the markdown ledger; output is markdown. Dry-run shows a preview diff; apply produces the real git working-tree diff. The command does not commit — it leaves a reviewable diff for the human to inspect and PR. This is the roadmap's contract ("reviewable PR diff"), so both preview and applied diffs must honestly reflect what changed.

### D9 — Retro Hook Is a Read-Only Nudge

`commands/retro.md` gains one read-only step: when a ledger growth signal is present (entry count crosses a threshold, or a cheap dry-run reports pending duplicate candidates), print a nudge to run `/knowledge --consolidate`. It mutates no knowledge file and skips gracefully when `.writ/knowledge/` is absent or empty. Retro is a reporting command; auto-consolidation there would violate D2.

### D10 — Eval Registration Is Shared-Additive

`scripts/eval-knowledge-consolidate.py` is modeled on `scripts/eval-phase-knowledge.py` (PASS/FAIL TSV consumed by a `check_*` bash function). Registration adds exactly:

- one `check_knowledge_consolidate` function in `scripts/eval.sh`
- one `knowledge-consolidate` line in the `CHECKS` array

The sibling evidence-bound-refresh spec also appends to the same registry. Sequential phase execution serializes the two appends; neither reorders nor rewrites existing entries, so both are safe.

## File × Story Matrix

| File | S1 | S2 | S3 |
|---|---:|---:|---:|
| `scripts/knowledge-consolidate.py` (new) | ✓ | ✓ |  |
| `commands/knowledge.md` |  | ✓ |  |
| `.writ/knowledge/README.md` |  | ✓ | ✓ |
| `scripts/eval-knowledge-consolidate.py` (new) |  |  | ✓ |
| `scripts/eval.sh` (shared-additive) |  |  | ✓ |
| `commands/retro.md` |  |  | ✓ |
| `scripts/phase-state.py` (reference only) | ✓ |  |  |
| `scripts/eval-phase-knowledge.py` (reference only) |  |  | ✓ |

Story 2 touches `scripts/knowledge-consolidate.py` only to wire the approved `--apply` path if Story 1 left it stubbed; detection remains Story 1's contract.

## Error & Rescue Map

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| Parse knowledge entry | Missing sections, unreadable file | Skip with a named reason; never rewrite or drop silently | Fixture: entry missing `## TL;DR`, unreadable path |
| Malformed frontmatter | Absent/invalid YAML, wrong category | Treat as unparseable; skip with reason; exclude from merge candidates | Fixture: broken YAML, category ≠ directory |
| Duplicate detection false-positive | Two distinct facts exceed threshold | Conservative threshold; proposal only; human approves against a diff | Fixture: near-topic but distinct entries below/above threshold |
| Contradiction detection | Heuristic flags a non-contradiction, or misses one | Surface as a review pair; never auto-resolve; human dismisses false positives | Fixture: conflicting pair surfaced; unrelated pair not surfaced |
| Merge conflict (proposal) | Canonical choice ambiguous, overlapping `related_artifacts` | Show the chosen canonical + union in the proposal; defer to human | Fixture: two entries with different artifact lists merged |
| Lineage write | `replaces`/`superseded_by` become inconsistent | Write bidirectionally in one apply; verify every `replaces` has a tombstone | Apply fixture asserts both fields and their symmetry |
| Dry-run diff generation | Preview diff diverges from applied result | Generate preview from the same proposed content apply would write | Compare dry-run preview to post-apply `git diff` on a fixture |

No `[UNPLANNED]` operations remain. No external retrieval, index, or database is introduced; consolidation is markdown-only and local.

## Shadow Paths

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| Duplicate detection | Pair above threshold → proposed merge | No `.writ/knowledge/` → graceful skip | Empty ledger → "no entries," no-op | Malformed entry → skip with reason, excluded |
| Stale flagging | Dangling `related_artifacts` → flagged | Entry has no `related_artifacts` → not stale by that signal | `related_artifacts: []` → not stale by that signal | Path check error → treat as present, do not over-flag |
| Command routing | `--consolidate` → dry-run → proposals | No `.writ/` → `/initialize` guard, write nothing | Nothing to consolidate → report no-op | Reducer error → report and abort before any write |
| Approval and apply | Approve → apply lineage → reviewable diff | Decline → ledger unchanged | No proposals → nothing to approve | Apply fails mid-write → report; leave partial tombstones? never — write is per-merge atomic |
| Retro hook | Growth signal → read-only nudge | No `.writ/knowledge/` → skip, no nudge | Empty/small ledger → no nudge | Signal check error → skip silently, never block retro |
| Eval scenarios | All scenarios PASS | No fixtures → harness creates temp dirs | Empty candidate set → clean-ledger no-op PASS | Reducer nonzero exit → scenario FAIL with reason |

## Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| Three or more near-duplicate entries | Propose one canonical with `replaces: [all others]`; each other becomes a tombstone |
| Glossary term merge | Always tombstone the merged-away term file; never delete (filename is an identifier) |
| Entry already a tombstone | Skip from detection; it is already superseded (a stale signal, not a new merge candidate) |
| Contradiction where one entry is newer | Still surface both; recency is not authority — the human decides |
| Duplicate pair spanning two categories | Not a merge candidate; comparisons are within-category only |
| `related_artifacts` points to a moved file | Do not over-flag: only flag stale when the path is genuinely absent, and defer to human |
| User approves some proposals, declines others | Apply only approved merges; declined pairs remain untouched |
| Real ledger has no duplicates yet | Report an honest no-op; the roadmap real-entry criterion stays pending until real entries qualify |

## Verification Commands

```bash
python3 scripts/knowledge-consolidate.py --dry-run          # preview proposals + diff, writes nothing
python3 scripts/eval-knowledge-consolidate.py               # PASS/FAIL TSV scenarios
bash scripts/eval.sh --check=knowledge-consolidate          # the new check in isolation
bash scripts/eval.sh                                        # full eval suite
```

Also perform a real-ledger dry-run against `.writ/knowledge/` to satisfy the roadmap's "merges or prunes real entries with a reviewable PR diff" criterion before the spec is marked Complete. Dry-run must leave the ledger byte-identical; only an explicitly approved apply changes files.
