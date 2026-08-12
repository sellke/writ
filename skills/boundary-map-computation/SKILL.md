---
name: boundary-map-computation
description: "Compute an owned / readable / out-of-scope file ownership map from tasks, imports, and overlap data."
disable-model-invocation: true
status: candidate
---

# Boundary Map Computation

## Purpose

Turn a story's task list, its spec's file map, the repository's import graph and
any recorded cross-story overlap into an explicit **file ownership map** — which
paths this work may create or modify, which it may only read, and which are out
of scope. A data transformation, not a judgment call: the same inputs yield the
same map.

Boundaries are **advisory**. Whoever edits outside them flags the edit; whoever
reviews the work verifies compliance. **There is no hard file locking.**

## When to Use

- Before implementation begins on a story whose spec allocates files across
  several stories, so parallel work does not silently collide.
- When a review needs a stated scope to check compliance against, rather than
  inferring intent from the diff.
- When recorded overlap data should raise scrutiny on specific paths rather
  than on the whole change.

## How to Apply

### The schema

Emit a markdown block with three headings. Use **file paths or globs** (e.g.
`src/auth/*.ts`); annotate entries when needed:

```markdown
### File Ownership Boundaries

**Owned** (create or modify):
- `path/to/owned.ts`
- `path/to/owned.test.ts`

**Readable** (import/reference; do not modify unless you emit a BOUNDARY_DEVIATION):
- `path/to/types.ts` _(imported by owned files)_
- `path/to/shared.ts` _(overlap: also touched by Story N — READABLE unless tasks above explicitly modify this path)_
- `path/to/hot.ts` _(⚠️ high-overlap: assess-spec Check 5 warn — extra scrutiny at review)_

**Out-of-scope** (do not modify; if you must, emit BOUNDARY_VIOLATION):
- Everything not listed above as Owned or Readable
```

The annotations are the only statement of the flag semantics.
`_(imported by owned files)_` marks an entry added by the import scan.
`_(overlap: …)_` marks an area recorded as shared between stories — still
**Owned** if this story's tasks explicitly name that path, otherwise prefer
**Readable** with the note. `_(⚠️ high-overlap: …)_` marks an area whose recorded
severity was **warn** (e.g. three or more stories share it); a reviewer treats it
as **higher scrutiny** for boundary compliance and integration.

### The algorithm — run in order

1. **Collect candidate OWNED paths.**
   - From the **story file**'s `## Implementation Tasks` (and inline task
     bullets): extract paths matching common phrasing — `` `path` ``,
     "Modify `path`", "Create `path`", "Update `path`", "Add to `path`", and
     file paths in fenced or inline code that look like project paths (contain
     `/` or `.`).
   - From **`sub-specs/technical-spec.md`** (or `technical-spec.md` in the spec
     folder): the **File Map** / architecture sections — if a row ties a file to
     **this** story, treat it as OWNED; if it ties the file to **another**
     story, treat it as an **overlap hint** for step 5.

2. **Normalize.** Deduplicate; preserve globs as written. If a path is listed
   as both owned and readable, **Owned wins — unless step 3 or 4 demotes it.**

3. **Import graph, depth 1.** For each **existing** OWNED file in the repo, list
   the **direct** imports/references that can be resolved (language-aware scan:
   `import`, `require`, `#include`, etc.). Imported files not already OWNED are
   added to **Readable** with `_(imported by owned files)_`.

4. **Architecture-review overrides.** Parse the upstream architecture review's
   `### Warnings for Coding Agent` section. For each path the warning says
   **not** to modify (e.g. "Do NOT modify `src/middleware/auth.ts`"), **demote**
   it: if it was OWNED → move to **Readable** and append
   `_(arch-check: do not modify — boundary override)_`; if it must not be edited
   even with a deviation → mark it out-of-scope in the narrative (list under
   Readable with strong wording, or exclude it from Owned and treat it as
   readable-only for review). Prefer matching explicit `` `...` `` paths from
   the warnings.

5. **Recorded overlap data (optional).** If persisted overlap data exists (see
   *Persistence* below), merge it:
   - Paths/areas flagged as shared → if **not** explicitly OWNED by this story's
     tasks, classify as **Readable** with `_(overlap: …)_`.
   - Items marked **warn** / "three+ stories" / **⚠️** → add
     `_(⚠️ high-overlap: …)_` to the **Readable** line (or to the Owned line if
     the tasks own the path but the overlap remains).
   - If **no** persisted data exists → skip this step; the baseline map is
     steps 1–4 only.

6. **Fallback — no extractable paths.** If steps 1–2 yield **no** OWNED paths:
   - Infer **approximate** directories from task wording (e.g. "auth", "billing
     module") and list **candidate Owned** globs such as `src/auth/**` **only**
     if the story clearly implies that directory.
   - Emit a visible warning:
     **`⚠️ boundary_map approximate — no concrete file paths in tasks; review agent should use extra caution.`**

7. **Readable / out-of-scope.** **Readable** is the union of the step 3, 4 and 5
   additions plus any spec "other story" files, minus anything still OWNED.
   **Out-of-scope is implicit** — everything else. Do not enumerate the whole
   tree; the schema's out-of-scope sentence is enough.

**Performance:** heuristic string extraction plus a shallow import scan only.
Target **&lt; 10 seconds**.

### Persistence of the overlap data step 5 reads

Spec-assessment output is often chat-only. To make Check 5 overlap data
available, persist it in either place:

1. **Recommended:** `.writ/specs/{spec-folder}/assessment-report.md`, containing
   a section headed exactly:

   `## Check 5 — File overlap`

   with a table (optional, for tooling):

   | File / area | Stories sharing | Severity (note / warn) |
   |-------------|-----------------|-------------------------|
   | `src/lib/utils.ts` | 1, 2, 3 | warn |

   **warn** maps to the high-overlap annotation on the map.

2. **Optional:** the same `## Check 5 — File overlap` section embedded in
   `user-stories/README.md` or in `spec.md` / `spec-lite.md` notes after
   assessment recommendations are applied — same parsing rules.

If **no** such section exists in the active spec folder, computation proceeds
**without** Check 5 data. That is graceful degradation, not an error.
