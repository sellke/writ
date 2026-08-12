---
name: change-surface-classification
description: "Classify a change set as style-only, single-component, cross-component, or full-stack."
disable-model-invocation: true
status: candidate
---

# Change Surface Classification

## Purpose

Put a change set into one of four named surfaces so that whatever reads it next
can allocate attention proportionally. A style tweak and a migration are not the
same review, and the difference is decidable from the file list plus a short
ordered heuristic — no judgment about quality, only about reach. The output is
one value: `change_surface`.

## When to Use

- After a change is complete and mechanically clean, when the depth of the next
  review should depend on how far the change reaches.
- When a result can be cross-checked against a recorded file ownership map — an
  unexpected **full-stack** result for a path the map lists as read-only
  warrants a stricter posture.

## How to Apply

### The four classes

| Classification | Criteria | Examples |
|---|---|---|
| **style-only** | Only CSS/SCSS/Tailwind files changed, or only `className`/`style` props modified in component files | Adding `max-h-[85vh]`, changing colors, responsive tweaks, CSS module changes |
| **single-component** | Changes scoped to one component file (state, handlers, props, JSX) | Adding a form field, fixing a handler bug, new local state |
| **cross-component** | Shared code changed: hooks, utils, context, types used by multiple components | Refactoring a shared hook, changing a context shape, updating a utility |
| **full-stack** | API routes, schema, migrations, auth, middleware, or multiple system layers | New CRUD endpoint, auth changes, database migration, new middleware |

### The heuristic — six steps, in order

1. List all files created/modified from the implementation output.
2. If ALL changes are `.css`, `.scss`, `.module.css`, Tailwind config, or only
   `className`/`style` prop changes in `.tsx`/`.jsx` → **style-only**.
3. If changes touch exactly one component file (plus its test file) →
   **single-component**.
4. If changes touch shared code — files in `hooks/`, `utils/`, `context/`,
   `lib/`, or files imported by more than 3 other files → **cross-component**.
5. If changes touch API routes, database schema, migrations, auth, or
   middleware → **full-stack**.
6. **When ambiguous, classify UP one level** — prefer more scrutiny over less.

Step 6 is the rule that cannot be re-derived from the table, and it decides the
awkward cases: a change readable as single-component *or* cross-component is
**cross-component**.

Step 2's **ALL** is equally load-bearing — a change set touching a stylesheet
*and* a migration does not satisfy it, and falls through to **full-stack**.
