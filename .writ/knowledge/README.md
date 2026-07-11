# Writ Knowledge Ledger

The knowledge ledger stores small, cross-cutting project facts that should survive chats, agent sessions, and future contributors. It is plain markdown in git; there is no database or generated source of truth.

## What Goes Where

Use this decision tree before creating an entry:

```text
Is this an architectural choice with serious blast radius
(reversal costs weeks, locks in a substrate, changes the system shape)?
-> YES: .writ/decision-records/ (ADR template)

Is this an investigation that produced specific recommendations
or evaluated multiple options against drivers?
-> YES: .writ/research/ (research template)

Is this a feature contract with stories, gates, and acceptance criteria?
-> YES: .writ/specs/ (spec template)

Otherwise — small, accumulating, cross-cutting:
- A choice we made about how the codebase looks?         -> knowledge/decisions/
- A pattern the codebase uses we want documented?        -> knowledge/conventions/
- A term whose meaning matters in this project?          -> knowledge/glossary/
- A thing we tried that failed or surprised us?          -> knowledge/lessons/
```

When in doubt, prefer the smallest durable home. Promote to an ADR or research note only when the entry needs heavier analysis, trade-off history, or formal approval.

## Categories

| Directory | Use For | Filename |
|---|---|---|
| `decisions/` | Small choices below ADR scale | `YYYY-MM-DD-short-slug.md` |
| `conventions/` | Reusable codebase or workflow patterns | `YYYY-MM-DD-short-slug.md` |
| `glossary/` | Writ-specific terms and meanings | `term-slug.md` |
| `lessons/` | Things tried, learned, or corrected | `YYYY-MM-DD-short-slug.md` |

## Required Frontmatter

Every entry must start with this schema:

```yaml
---
category: decisions | conventions | glossary | lessons
tags: [tag1, tag2]
created: YYYY-MM-DD
related_artifacts:
  - .writ/specs/example/spec.md
---
```

Rules:
- `category` must match the containing directory.
- `tags` must contain at least one lowercase slug.
- `created` uses `YYYY-MM-DD`.
- `related_artifacts` is always present. Use `[]` when there are no related files.
- Optional fields are allowed: `superseded_by`, `replaces`, `author`, `confidence`.

## Authoring Rules

Use `/knowledge "summary"` for fast capture. The command infers a category, prompts only for missing required fields, validates frontmatter before writing, and confirms with the created path.

Use `/knowledge --category=lessons "summary"` when inference would be ambiguous.

Use `/knowledge --list [category]` to scan entries and `/knowledge --read <slug>` to load one entry by filename slug.

Keep entries short. If the explanation needs a long comparison, write research. If it changes architecture, write an ADR.

## Consolidation and Lineage

The ledger is append-friendly for capture but must not grow into a junk drawer. `/knowledge --consolidate` runs a periodic maintenance pass under one principle: **merge, never append.** A log grows unbounded; a merged document stays searchable.

Consolidation is **non-destructive by default**. `scripts/knowledge-consolidate.py` scans all four categories, then:

- **proposes merges** of near-duplicate entries (within a category) using the same `_tokens` + Jaccard overlap the substrate already uses for dedup;
- **surfaces contradictions** — same-subject entries that assert conflicting facts — for a human to decide, never auto-resolving them;
- **flags stale entries** on observable signals only (already superseded, all `related_artifacts` missing on disk, or dominated by a newer entry) — never on age alone.

The reducer defaults to `--dry-run`: it prints a proposal plus a preview unified diff and writes nothing. Only an explicit, human-approved `--apply` mutates files, and the result is a reviewable working-tree diff you inspect and commit as a PR. Malformed entries are skipped with a named reason, never rewritten or dropped.

### Lineage Frontmatter (`replaces` / `superseded_by`)

Merges preserve provenance bidirectionally using the optional lineage fields:

```yaml
# The surviving canonical entry records what it absorbed:
---
category: lessons
tags: [retries, quarantine]
created: 2026-04-24
related_artifacts: [...]
replaces:
  - 2026-04-24-superseded-slug-a
  - 2026-04-24-superseded-slug-b
---

# Each merged-away entry becomes a tombstone pointing forward:
---
category: lessons
created: 2026-04-24
superseded_by: 2026-04-24-canonical-slug
---

# Superseded

Merged into [Canonical Title](../lessons/2026-04-24-canonical-slug.md).
```

Rules:

- Lineage is **bidirectional**: every `replaces` slug has a matching `superseded_by` tombstone, and vice versa.
- Tombstones are **retained by default** — they keep inbound links alive and make provenance auditable in the diff. Physical deletion is a separate, later, explicit human action.
- **Glossary** entries are always tombstoned on merge, never deleted, because the filename is an addressable identifier.
- Consolidation only *merges*; it never resolves a contradiction or retires a stale entry automatically. Those are surfaced for an explicit human decision.
