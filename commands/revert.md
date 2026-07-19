# Revert Command (revert)

## Overview

Safely unwinds a **logical unit** of Writ work — a single `story` or an entire `spec` — on the current branch. `/revert` maps the unit to its real git commits with a layered, rewrite-resilient resolver, shows you the exact commits and artifacts that will change **before** anything mutates, then executes a history-preserving `git revert` (default) or, only behind a second destructive confirmation, a `git reset --hard`. On success it restores Writ's artifacts (story status, tasks/AC, `## What Was Built`, `drift-log.md`, `context.md`) so the plan and reality stay in sync.

**Core discipline:** Plan before mutate. No git-mutating command runs until the working tree is verified clean **and** you have confirmed a plan that names every resolved commit and the chosen strategy. Ghost (rewritten-SHA) substitutions are never auto-applied — each requires explicit confirmation.

**Scope boundary:** First cut handles `story` and `spec` units on the **current branch** only. Phase-lane, worktree, and quarantine reverts are out of scope — those are owned by `phase-state.py`'s reconcile/quarantine machinery. `/revert` also never reverts across base branches, auto-reverts a released version, or undoes a previous revert. For behavioral rollbacks of a single refactor step, use `/refactor`'s per-change revert loop instead.

## Invocation

| Invocation | Behavior |
|---|---|
| `/revert` | Guided menu — in-progress units first, then recently completed (max ~4, plus "Other") |
| `/revert story-3` | Revert story 3 of the active spec |
| `/revert spec <folder-id>` | Revert an entire spec (union of all its stories + scaffolding commit) |

## Command Process

The command runs five explicit phases. Each phase produces visible output; mutation happens only in Phase 4, only after the Phase 3 gate.

### Phase 1: Target Selection

If the invocation names a target (`story-3`, `spec <id>`), use it directly and proceed to Phase 2.

If no target is given, present a guided **AskQuestion** menu built from the active spec's `user-stories/README.md` and spec statuses:

1. List **in-progress / completed** units first (a unit is a candidate if it has a `## What Was Built` record or a `> **Commit:**` field, or a `Ref:`/phase-state commit).
2. Cap the list at ~4 options, most recent first, plus a trailing **"Other (enter a target)"** option.
3. Selecting "Other" prompts for a `story-N` or `spec <id>` target.

Follow `_preamble.md` interaction conventions — this is a bounded choice, so AskQuestion (not Plan Mode) is correct.

### Phase 2: Resolve

Invoke the resolver (read-only — it never mutates git or files):

```
python3 scripts/revert-resolve.py <unit> <id> [--spec <spec-id>] --json
```

The resolver returns the ordered commit list (newest → oldest), any `ghost` candidates, the `base` (parent of the earliest commit), and `warnings`. It layers four sources by confidence: recorded `> **Commit:**` SHA → `/ship` `Ref:` footer → phase-state JSON `commit`/`mergeCommit` → ghost-commit subject-similarity fallback.

**Ghost confirmation:** For every entry in the resolver's `ghost` array, present the recorded SHA, the candidate SHA + subject, and the similarity score, then **AskQuestion** to confirm each substitution individually. A ghost candidate is **never** auto-selected or silently promoted into the commit list. Decline → drop that commit from the plan and surface a warning that the unit may be only partially reverted.

If the resolver returns **no commits** (`commits` empty), halt with an explanation and offer manual target entry — there is nothing to revert.

### Phase 3: Plan Gate

**Dirty-tree guard FIRST — before presenting the plan and before any git operation:**

```
git status --porcelain
```

If the output is **non-empty**, HALT immediately: "Working tree has uncommitted changes — commit or stash before reverting. No git operation has run." Do not continue to the plan.

Only once the tree is clean, present the **revert plan**:

- **Commits** — each `sha` (short) + subject + source, in revert order (newest → oldest).
- **Confirmed ghost substitutions** — any candidates the user accepted in Phase 2.
- **Strategy choices** — safe vs. destructive, with the `base` SHA that hard reset would target.
- **Artifacts to reset** — the story/spec status, tasks/AC, WWB banner, drift-log entry, and `context.md` regeneration (Phase 5).
- **Warnings** — merge commits, possible cherry-pick duplicates, missing-SHA notes.

This pre-execution plan is the **moment of truth**: nothing has mutated yet. Then **AskQuestion**:

- **Safe (revert)** — history-preserving new commits. **[Recommended]**
- **Hard reset (destructive)** — rewinds the branch to `base`; discards later work.
- **Cancel** — exit without touching anything.

**Plan-before-mutate is mandatory:** never run `git revert` or `git reset` before this gate returns a confirmed strategy. The recommendation follows business-rule precedence (safety + reversibility): `git revert` is reversible and non-destructive, so it carries the `(Recommended)` label; hard reset is destructive and is never the default.

### Phase 4: Execute

**Safe strategy (default):**

Run `git revert --no-edit <sha>` for each resolved commit, **newest → oldest**. On a **conflict**, HALT and leave the repository mid-revert for the user with clear manual-resolution guidance ("resolve conflicts, then `git revert --continue`, or `git revert --abort` to back out"). Do not attempt automatic conflict resolution and do not proceed to Phase 5 until the revert sequence completes cleanly.

**Hard reset strategy (destructive):**

Require a **second destructive confirmation** — an explicit **AskQuestion** that names the exact `base` SHA and warns that all commits after it (including any uncommitted-but-now-committed work) will be permanently discarded. Only on affirmative confirmation run:

```
git reset --hard <base>
```

If the user declines the second confirmation, cancel without mutating. Never run `git reset --hard` on a single confirmation.

### Phase 5: Restore Artifacts & Report

After a clean revert (safe or hard), restore Writ's artifacts so no artifact claims work that was just undone. See "Artifact Restoration" below for the full contract. Then regenerate `context.md` and print a report:

- Unit reverted, strategy used, and the commits that were reverted (or reset past).
- Artifacts updated (status, tasks/AC, WWB banner, drift-log entry).
- New repository state and suggested next action.

**Optional audit note (soft link):** If the git-notes audit channel (`refs/notes/writ`) is present in this repo, the revert *may* attach a short audit note recording the unit, strategy, and commits under `refs/notes/writ`. This is optional and non-required — skip silently if the channel is absent.

---

## Artifact Restoration

On a successful revert, restore artifacts to match reality. For a **spec** revert, apply the per-story steps to **every** story in the spec and reset the spec's own status.

1. **Story status → `Not Started`.** In each affected story file, set `> **Status:** Not Started` and uncheck every `- [x]` back to `- [ ]` in the Implementation Tasks and Acceptance Criteria / Definition of Done lists.
2. **WWB "Reverted" banner (preserve, never delete).** Insert a banner at the top of the story's `## What Was Built` section — do **not** remove the record:

   ```
   > **Reverted:** {YYYY-MM-DD} — reverted via /revert ({strategy}); commits {short-shas}. Record preserved for history.
   ```

   A reverted WWB record is **not authoritative** for downstream dependency context (see `.writ/docs/what-was-built-format.md`). Loaders such as `/implement-story` Step 2 skip or flag it.
3. **drift-log entry (append-only).** Append to `.writ/specs/<spec>/drift-log.md`, continuing DEV-ID numbering from the highest existing entry:

   ```
   #### [DEV-NNN] Reverted {unit} {id}
   - **Severity:** n/a (revert)
   - **Action:** {safe revert | hard reset} of {N} commit(s)
   - **Commits:** {short-shas}
   - **Date:** {YYYY-MM-DD}
   ```
4. **Regenerate `context.md`.** Rewrite `.writ/context.md` in full using the **same schema** `/implement-story` Step 2 defines (Product Mission / Active Spec / Recent Drift / Open Issues) — never invent a new schema, never patch in place.
5. **Spec-level rollup.** For a spec revert, after all stories are reset, set the spec's own status back to `Not Started` (or `In Progress` if any unreverted work remains) and update `user-stories/README.md` progress counts.

---

## Safety Guarantees

Six invariants hold for every `/revert` operation:

1. **Dirty-tree guard** — refuses to start (before any git op) if `git status --porcelain` is non-empty.
2. **Plan-before-mutate** — the resolved commit list + strategy are confirmed before any `git revert`/`git reset` runs.
3. **Safe by default** — `git revert --no-edit` (history-preserving) is the recommended strategy; `git reset --hard` is opt-in.
4. **Second destructive confirmation** — hard reset requires an explicit second confirmation naming the `base` SHA.
5. **Confirmed ghost substitution** — a message-similarity match for a missing SHA is used only after explicit confirmation, never auto-selected.
6. **Full restoration** — status, tasks/AC, WWB annotation, drift-log, and `context.md` are restored so plan and reality stay in sync.

---

## Integration with Writ

| Command | Relationship |
|---------|-------------|
| `/implement-story` | Records the `> **Commit:**` SHA the resolver reads first; its Step 2 loader treats reverted WWB records as non-authoritative |
| `/ship` | Its `Ref:` footer is the resolver's second layer for shipped work |
| `/implement-phase` | Phase-state JSON is the resolver's third layer; lane/quarantine reverts remain owned by `phase-state.py` |
| `/refactor` | Use its per-change revert loop for a single behavioral rollback rather than a logical-unit revert |
| `/status` | Reflects the restored story/spec state after a revert |

---

## References

- Standing instructions: [`commands/_preamble.md`](_preamble.md)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)
- Resolver: `scripts/revert-resolve.py` · Technical spec: `.writ/specs/2026-07-18-logical-unit-revert/sub-specs/technical-spec.md`
