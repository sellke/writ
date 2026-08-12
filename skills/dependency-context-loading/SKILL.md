---
name: dependency-context-loading
description: "Load, filter, and truncate upstream stories' implementation records into dependency context."
disable-model-invocation: true
status: candidate
---

# Dependency Context Loading

## Purpose

Give work on a story visibility into what its **upstream dependencies actually
built**, rather than what their plans said they would. It locates completed
dependency stories, reads their "What Was Built" (WWB) records, discards the
ones no longer authoritative, truncates oversized ones by a fixed priority, and
aggregates the survivors into one `dependency_wwb_context` block. Deciding who
receives the block, and when, belongs to the consumer.

> **Format reference:** `.writ/docs/what-was-built-format.md` — the authority on
> the record's shape and on the `> **Reverted:**` banner convention. This
> capability reads that format; it does not restate it.

## When to Use

- Working a story that declares dependencies on other stories in the same spec,
  where the downstream work builds on files or decisions the upstream work
  produced.
- Assembling context for an implementer who would otherwise guess at an
  upstream interface.
- Any time cross-story continuity matters more than a clean-slate reading of
  the current story.

Skip it entirely when the story has no dependencies — there is nothing to load
and nothing to warn about.

## How to Apply

### 1. Parse dependencies from the story file

- Check the story metadata line: `> **Dependencies:** Story 1, Story 2`.
- Or parse the `## User Story` section for dependency mentions.
- Extract story numbers or IDs.

### 2. Locate the dependency story files

- Construct paths of the form
  `.writ/specs/{spec-folder}/user-stories/story-{N}-{slug}.md`.
- Read each dependency story file.

### 3. Check completion status

Look for `> **Status:** Completed ✅` in the story file header. If a dependency
is **not** complete, log the warning and continue anyway:

```
⚠️ Story 3 depends on Story 1 (not yet complete).
Proceeding anyway — some integration points may be unavailable.
```

### 4. Extract the WWB sections

For each **completed** dependency, locate its `## What Was Built` section and
read the whole thing — from the `## What Was Built` heading to the next `##`
heading or end of file.

**Skip reverted records.** If the section begins with a `> **Reverted:**`
banner, the work it describes was undone and the record is **not
authoritative**. Do NOT load it as live dependency context — skip it (or flag it
as reverted) and log:

```
ℹ️ Story N's "What Was Built" is marked Reverted — skipping as non-authoritative dependency context.
```

If a completed dependency has **no** WWB section, log:

```
⚠️ Story 1 is marked complete but has no "What Was Built" record.
Proceeding with reduced context — cross-story continuity may be degraded.
```

### 5. Apply size limits and truncation

Count the lines of each record. **If a record exceeds 1000 lines**, truncate it
using this priority order — the order *is* the rule:

1. **Files Created** — keep full (highest priority).
2. **Files Modified** — keep full.
3. **Implementation Decisions** — keep full if space allows, otherwise the
   first 20 lines.
4. **Test Results** — keep the summary line only; drop the detailed test list.
5. **Review Outcome** — keep full.
6. **Deviations from Spec** — keep DEV-IDs and titles; truncate details to the
   first 2 lines each.
7. **Lessons Learned** (if present) — drop if space is needed.

Log the truncation:
`⚠️ Truncated Story {N} "What Was Built" record ({original} → 1000 lines)`

**Preserve markdown structure** in the truncated version.

**Only load direct dependencies — never transitive.** Story 3 loads Story 2's
record, but not Story 1's, even if Story 2 depended on Story 1.

### 6. Aggregate

Collect every WWB section (full or truncated) from the completed, non-reverted
dependencies and format them as one block:

```markdown
## Dependency Context: What Was Built in Upstream Stories

### From Story 1: {story title}
{WWB content from Story 1}

### From Story 2: {story title}
{WWB content from Story 2}
```

### 7. Position the block

The aggregated `dependency_wwb_context` goes **after** the story content and
spec context and **before** the implementation tasks.

### Graceful degradation

| Case | Behavior |
|---|---|
| Dependency incomplete | Continue with the warning above |
| Dependency complete but no WWB section | Continue with a warning; note the context is degraded |
| Multiple dependencies, some with WWB and some without | Include the available records; log a warning per missing one |
| No dependencies | Skip the whole capability — nothing to load, nothing to warn |

None of these is a failure: missing upstream context degrades the payload, it
never blocks the work.
