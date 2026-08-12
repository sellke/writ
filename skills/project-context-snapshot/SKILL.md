---
name: project-context-snapshot
description: "Regenerate a whole-file project context snapshot from product, spec, drift, and issue sources."
disable-model-invocation: true
status: candidate
---

# Project Context Snapshot

## Purpose

Produce `.writ/context.md` — a single running snapshot of where a project
stands: mission, active spec and story, which artifacts exist, recent drift,
open issues. It is the first thing loaded when work resumes, so it must be cheap
to read and impossible to be stale in part. That comes from one rule: the file
is **always fully regenerated**, never patched or appended.

## When to Use

- After a unit of work changes status, so the next reader sees current progress
  rather than the previous state.
- When reporting current project state to a human.
- Any time the underlying sources (product docs, active spec, drift log, issues)
  have moved and the snapshot would otherwise disagree with them.

The file lives at `.writ/context.md` — project root, never inside a spec folder.

## How to Apply

### Schema

```markdown
# Writ Project Context

> Last Updated: {ISO 8601 timestamp}

## Product Mission

{1–3 sentences from `.writ/product/mission-lite.md` — omit section if file is absent}

## Active Spec

- **Spec:** {spec-folder-id} — {spec title}
- **Status:** {spec status}
- **Story:** {N} of {M} — {current story title} ({story status})
- **Progress:** {X}/{Y} tasks complete ({Z}%)

## Artifact Map

- **Product:** {list present of roadmap.md, mission.md, mission-lite.md; mark missing}
- **Active spec:** .writ/specs/{id}/ — spec.md {+ spec-lite.md, user-stories/, sub-specs/ if present}
- **Knowledge:** .writ/knowledge/ ({N} entries, or "none")
- **Docs:** .writ/docs/ ({count} files)
- **Integrity:** {✅ all required present | ⚠️ missing required: <list>}

## Recent Drift

{Last 3 entries from `.writ/specs/{spec}/drift-log.md` — omit section if absent or empty}

## Open Issues

{Count of files in `.writ/issues/` subdirectories — omit section if `.writ/issues/` absent}
```

### Fallbacks when sources are missing

- `mission-lite.md` absent → omit the "Product Mission" section entirely.
- No active spec → omit the "Active Spec" section.
- `drift-log.md` absent or empty → omit the "Recent Drift" section.
- `.writ/issues/` absent → omit the "Open Issues" section.

A missing source removes its section — never an empty heading, never a blocked
regeneration.

### Artifact Map rules (present-conditional, rewritten wholesale)

- Omit sub-items whose files are absent (e.g. no `spec-lite.md` → drop it); the
  **Integrity** line **always renders**.
- The Integrity line reflects the standing Required/Optional artifact semantics:
  `✅ all required present` when every required artifact exists, otherwise
  `⚠️ missing required: <list>`.
- Rewritten wholesale on every regeneration — never appended or patched, exactly
  like the rest of the file. **No separate index or pointer file is ever
  created.**

The always-renders and omit-absent rules are in tension by design: every other
line disappears when its source does; Integrity stays to say so.
