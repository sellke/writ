# Technical Spec: Artifact Integrity + Handshake

> Parent: [`../spec.md`](../spec.md)

## 1. `_preamble.md` — Artifact Integrity section

Add a new top-level section (after "File Organization"):

```markdown
## Artifact Integrity

Before doing work, verify the artifacts your command depends on. Commands may
declare a **Required Artifacts** block listing what they need, each marked
*required* or *optional*.

- **Required artifact missing** → HALT. State exactly what is missing and offer a
  bounded repair via AskQuestion, naming the command that creates it. Never
  auto-run a mutating repair without confirmation.
- **Optional artifact missing** → warn and continue in degraded mode.

Common artifact → creating command:
- `.writ/product/roadmap.md`, `mission.md` → `/plan-product`
- technical foundation docs (`.writ/docs/`) → `/initialize`
- a spec folder under `.writ/specs/` → `/create-spec`

This is adapter-neutral: pure existence checks, no platform hooks.
```

## 2. `context.md` — Artifact Map schema

Extend the `context.md` schema (currently defined in `commands/implement-story.md` Step 2) by adding a section after "Active Spec":

```markdown
## Artifact Map

- **Product:** {list present of roadmap.md, mission.md, mission-lite.md; mark missing}
- **Active spec:** .writ/specs/{id}/ — spec.md {+ spec-lite.md, user-stories/, sub-specs/ if present}
- **Knowledge:** .writ/knowledge/ ({N} entries, or "none")
- **Docs:** .writ/docs/ ({count} files)
- **Integrity:** {✅ all required present | ⚠️ missing required: <list>}
```

**Rules:**
- Present-conditional (omit sub-items whose files are absent; the Integrity line always renders).
- Rewritten wholesale on every `context.md` regeneration — never appended/patched.
- The same schema addition must be reflected everywhere the schema is documented/regenerated: `implement-story` Step 2 (canonical), `implement-spec` (regeneration call), `status` (regeneration call).

## 3. Required Artifacts blocks (per command)

Add a short block near the top of each of the 7 commands. Examples:

**implement-story.md**
```markdown
## Required Artifacts
- **Required:** active spec folder (`spec.md`, `user-stories/`)
- **Optional:** `.writ/context.md`, `.writ/knowledge/`, `spec-lite.md`, `mockups/`
```

**create-spec.md**
```markdown
## Required Artifacts
- **Required:** none (create-spec bootstraps a spec)
- **Optional:** `.writ/product/` docs (inform discovery), `.writ/context.md`
```

**implement-spec.md** — Required: target spec folder. Optional: context.md, knowledge.
**implement-phase.md** — Required: `.writ/product/roadmap.md`. Optional: existing specs, phase state.
**ship.md** — Required: a git repo + branch. Optional: matching spec folder (for `Ref:` footer + audit note).
**release.md** — Required: `VERSION`, git repo. Optional: completed specs (for changelog).
**status.md** — Required: none. Optional: everything (status degrades per-section, already does).

## 4. Eval check

Add to `eval.sh` (+ small helper):
- Assert `commands/_preamble.md` contains `## Artifact Integrity` with the required/optional distinction, HALT wording, and bounded-repair wording.
- Assert each of the 7 commands contains a `## Required Artifacts` block.
- Assert no `.writ/index.md` is introduced by this spec (guard against the rejected design).

## 5. Non-goals

- No `.writ/index.md` file.
- No declarations in the other ~23 commands (only the 7 high-traffic ones).
- No runtime file watchers or platform hooks.
- No integrity checks on `.writ/state/` (ephemeral, gitignored).
