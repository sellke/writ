# Spec: Artifact Integrity + Handshake

> **Status:** Not Started
> **Owner:** @Adam Sellke
> **Created:** 2026-07-18
> **Origin:** Recommendation #3 from [`2026-07-18-writ-vs-conductor-analysis.md`](../../research/2026-07-18-writ-vs-conductor-analysis.md)

## Contract (Locked)

**Deliverable:** Two complementary robustness additions, **no new files**:

1. An **"Artifact Integrity"** standing rule in `commands/_preamble.md`: before doing work, a command verifies its declared **Required Artifacts** exist. Missing *required* artifact → **HALT + offer bounded repair**; missing *optional* artifact → warn + degrade.
2. An **"Artifact Map"** section added to the existing regenerated `.writ/context.md` — a single resolve point for product/spec/docs artifacts, kept current by the commands that already regenerate `context.md`.

Plus **"Required Artifacts"** declarations on seven high-traffic commands: `create-spec`, `implement-story`, `implement-spec`, `implement-phase`, `ship`, `release`, `status`.

**Must include:** Required vs optional distinction — only *required* absence halts.

**Hardest constraint:** Deliver Conductor's every-skill integrity discipline **without** adding a third pointer file (`index.md`) alongside the `.writ/` convention and `context.md` (ADR-015 leanness).

## Why This Exists

Conductor opens every skill with: read `index.md` → verify every linked artifact exists → HALT if any is missing, offering to repair. It's a genuinely robust pattern that prevents commands from running against a broken or uninitialized project.

Writ applies this **unevenly** — some commands check for `.writ/product/` docs or a spec folder, many assume they exist. But Writ already has three things Conductor lacks:

- `commands/_preamble.md` — standing rules referenced by every command.
- A strong `.writ/` directory **convention** (documented in the preamble's File Organization).
- A committed, auto-regenerated `.writ/context.md` project snapshot.

So the honest move is **not** to clone Conductor's separate `index.md`. It's to put the *behavior* (integrity check) in the preamble and the *map* (handshake) into `context.md`. Same value, no new surface.

## 🎯 Experience Design

### Entry Point

Automatic, at the top of any command that declares Required Artifacts (via the preamble convention).

### Happy Path

1. Command starts → reads its Required Artifacts declaration.
2. Verifies each exists.
3. All present → proceed. `context.md`'s Artifact Map is the single place to resolve product/spec/docs paths.

### Moment of Truth

A command that would otherwise fail cryptically mid-run instead stops immediately with: *"This needs `X`, which is missing — create it with `/Y`?"*

### Error Experience

| Situation | Behavior |
|---|---|
| Required artifact missing | HALT with a specific message + bounded AskQuestion repair offer naming the command that creates it |
| Optional artifact missing | Warn + continue degraded (existing graceful-degradation) |
| Repair declined | HALT cleanly; no mutation |
| `context.md` absent | Regenerate it (existing behavior) — the Map is part of that regeneration |

## 📋 Business Rules

1. **Required vs optional is explicit per command.** Only *required* absence halts; optional absence warns and degrades.
2. **Bounded repair only.** A repair offer names the specific creating command (`/initialize`, `/plan-product`, `/create-spec`); it never auto-runs a mutating repair without confirmation.
3. **No new pointer file.** The Artifact Map lives inside `context.md` (regenerated, never hand-patched). `.writ/index.md` is explicitly rejected.
4. **Adapter-neutral.** Pure artifact-existence checks; no platform-specific runtime hooks.
5. **Regeneration keeps the Map fresh.** The Map is rewritten wholesale whenever `context.md` is regenerated (`implement-story`, `implement-spec`, `status`) — never appended or patched.

## Detailed Requirements

### `_preamble.md` — "Artifact Integrity" section

A new standing section defining:
- The **Required Artifacts** convention: a command may declare a short list of artifacts it depends on, each marked *required* or *optional*.
- The check-then-HALT behavior: verify before work; required missing → HALT + bounded repair AskQuestion; optional missing → warn + degrade.
- A small mapping of common artifacts → their creating command (roadmap → `/plan-product`, tech foundation → `/initialize`, a spec → `/create-spec`).

### `context.md` — "Artifact Map" section

Extend the existing `context.md` schema (defined in `implement-story` Step 2) with:

```markdown
## Artifact Map

- **Product:** .writ/product/roadmap.md, mission.md, mission-lite.md {mark missing ones}
- **Active spec:** .writ/specs/{id}/spec.md (+ spec-lite.md, user-stories/, sub-specs/)
- **Knowledge:** .writ/knowledge/ ({N} entries)
- **Docs:** .writ/docs/ ({key docs})
- **Integrity:** {✅ all present | ⚠️ missing: <list>}
```

Fields present-conditionally, same graceful-degradation as the rest of `context.md`.

### Per-command Required Artifacts declarations

Add a short **Required Artifacts** block to the 7 high-traffic commands, e.g. for `implement-story`:

```markdown
## Required Artifacts
- **Required:** active spec folder (`spec.md`, `user-stories/`)
- **Optional:** `.writ/context.md`, `.writ/knowledge/`, `spec-lite.md`
```

### Eval check

`eval.sh` asserts:
- `_preamble.md` contains the Artifact Integrity section (required/optional + HALT + bounded repair).
- Each of the 7 commands has a Required Artifacts block.

## Implementation Approach

Product-source markdown edits + one eval check. No new files, no runtime code. Verify via `eval.sh` + manual command runs on this repo (which has a full `.writ/`).

- `commands/_preamble.md` — add Artifact Integrity section.
- `commands/implement-story.md`, `implement-spec.md`, `status.md` — update the `context.md` regeneration schema to include the Artifact Map; add Required Artifacts blocks.
- `commands/create-spec.md`, `implement-phase.md`, `ship.md`, `release.md` — add Required Artifacts blocks.
- `scripts/eval.sh` (+ helper) — the integrity/declaration check.

## Success Criteria

1. A high-traffic command run with a missing *required* artifact halts with a specific, actionable message + bounded repair offer.
2. A missing *optional* artifact warns and continues.
3. After regeneration, `context.md` contains an Artifact Map with an integrity line.
4. No `.writ/index.md` file is created.
5. `eval.sh` asserts the preamble rule and the 7 declarations, and passes.

## Scope Boundaries

**Included:** `_preamble.md` Artifact Integrity section; `context.md` Artifact Map schema + regeneration updates; Required Artifacts on 7 commands; eval check.

**Excluded:** a new `.writ/index.md` (rejected), declarations in all 30 commands, runtime file watchers, integrity checks on ephemeral `state/` files.

## Dependencies

None external. Internal order: Story 1 (preamble) → Story 2 (context.md map) → Story 3 (declarations + eval).
