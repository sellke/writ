# Spec: Logical-Unit Revert (`/revert`)

> **Status:** Complete
> **Owner:** @Adam Sellke
> **Created:** 2026-07-18
> **Origin:** Recommendation #2 from [`2026-07-18-writ-vs-conductor-analysis.md`](../../research/2026-07-18-writ-vs-conductor-analysis.md)

## Contract (Locked)

**Deliverable:** A new `/revert <unit>` command (`unit` = `story` | `spec`; phase deferred) that safely unwinds a logical unit of Writ work. It maps the unit to its commits via a layered resolver (recorded story SHA → `/ship` `Ref:` footer → phase-state JSON → ghost-commit fuzzy-match fallback), offers safe `git revert` (default) or destructive `git reset --hard`, and performs full artifact restoration (story status → Not Started, WWB annotated, drift-log entry, `context.md` regenerated). A prerequisite change to `/implement-story` records each story's commit SHA into its story file so future work is cleanly revertible.

**Must include:** A confirmation gate presenting the exact resolved commit list + strategy before any mutation.

**Hardest constraint:** Writ has no per-story SHA record today, and history may be rewritten by rebase/squash — so mapping a logical unit to its real commits must be resilient (layered resolver + confirmed ghost-commit substitution).

## Why This Exists

Writ records commit SHAs in **phase execution state** (`scripts/phase-state.py`: `commit`, `mergeCommit`) and `/ship` writes a `Ref: <spec/story>` footer on commits that trace to a story. But:

- Single-story / single-spec work run via `/implement-story` / `/implement-spec` records **no SHA** in the story file (unlike Conductor's `plan.md`).
- There is **no command** to unwind a story or spec as a logical unit — only the commit-or-revert loop inside `/refactor` for individual refactor steps.

Conductor's `conductor-revert` demonstrated a proper git-aware logical-unit revert: map a track/phase/task to *all* associated commits (implementation + plan-update + creation), reconcile "ghost commits" whose SHA was rewritten (by searching for a similar commit message and confirming), and offer safe vs destructive strategies. This spec brings that capability to Writ's story/spec units and closes the SHA-recording gap so it works reliably.

## 🎯 Experience Design

### Entry Point

- `/revert` — guided selection menu (in-progress units first, then recently completed), max ~4 options, Conductor-style.
- `/revert story-3` — direct target (current spec).
- `/revert spec <folder-id>` — revert an entire spec.

### Happy Path

1. Resolve the target unit and its commits via the layered resolver.
2. Present a **revert plan**: the exact commits (SHA + subject), the strategy choices, and the Writ artifacts that will be reset.
3. User confirms and picks a strategy (safe default).
4. Execute the reverts; restore Writ artifacts; regenerate `context.md`.
5. Report what was reverted and the new state.

### Moment of Truth

The pre-execution plan — the user sees precisely which commits and artifacts will change **before** anything mutates. No surprise history rewrites.

### Feedback Model

Clear plan → confirm → execute → summary. Each phase is explicit.

### Error Experience

| Situation | Behavior |
|---|---|
| Working tree dirty | Halt: "commit or stash before reverting"; no git op runs |
| Recorded SHA missing from history (rewritten) | Ghost-commit search by message similarity → present candidate → require confirmation before using |
| No commits resolvable for the unit | Halt with explanation; offer manual target entry |
| `git revert` conflict | Halt with clear manual-resolution instructions; leave repo mid-revert for the user |
| Hard reset chosen | Require a second destructive confirmation naming the base SHA and warning about lost work |

## 📋 Business Rules

1. **Plan-before-mutate.** Never run a git-mutating command before the user confirms a plan showing the resolved commits + chosen strategy.
2. **Dirty-tree guard.** Refuse to start if the working tree has uncommitted changes.
3. **Safe by default.** `git revert` (history-preserving new commits) is the default; `git reset --hard` requires an explicit second destructive confirmation.
4. **Confirmed ghost-commit substitution.** A message-similarity match for a missing SHA is only used after explicit user confirmation.
5. **Full restoration keeps plan and reality in sync.** On success: story status → `Not Started`, its `## What Was Built` record annotated as reverted (not silently deleted), a revert entry appended to `drift-log.md`, and `context.md` regenerated.
6. **Scope guard.** First cut handles story + spec on the current branch only; phase-lane/worktree/quarantine reverts are out of scope (deferred to `phase-state.py`'s existing quarantine/reconcile).

## Detailed Requirements

### Commit resolution (layered)

`scripts/revert-resolve.py <unit> <id>` returns the ordered commit list to revert (newest → oldest) plus provenance for each. Resolution order:

1. **Recorded story SHA** — from the story file's new `> **Commit:** <sha>` field (added by Story 1).
2. **`/ship` `Ref:` footer** — `git log --grep "Ref: <spec/story>"` for shipped work.
3. **Phase-state JSON** — `commit`/`mergeCommit` for phase-orchestrated work (read-only lookup).
4. **Ghost-commit fuzzy match** — when a SHA from (1)/(3) is absent from history, search the log for the most similar commit subject; surface as a candidate requiring confirmation.

For a **spec** unit, union the commits of all its stories (+ the spec-scaffolding commit that created the spec folder, like Conductor's track-creation commit).

### Revert strategies

- **Safe (default):** `git revert --no-edit <sha>` for each resolved commit, newest → oldest.
- **Destructive:** `git reset --hard <base>` where `<base>` is the parent of the earliest resolved commit; second confirmation required.

### Artifact restoration

- Story status frontmatter → `Not Started`; uncheck tasks/AC.
- `## What Was Built` record → annotate with a `> **Reverted:** <date> — <reason/commit>` banner (preserve for history, don't delete).
- Append a `drift-log.md` entry recording the revert (unit, commits, strategy, date).
- Regenerate `.writ/context.md`.

## Implementation Approach

Product-source changes (markdown + one python helper). `scripts/revert-resolve.py` follows the existing pattern of `spec-deps.py` / `phase-state.py` (deterministic git logic in Python, testable via `eval.sh`). The `/revert` command orchestrates: selection, plan gate, strategy, execution, restoration.

- `commands/revert.md` (new)
- `commands/implement-story.md` — Step 4: record commit SHA into the story file
- `scripts/revert-resolve.py` (new)
- `scripts/eval.sh` (+ helper) — resolver tests + command-rule assertions
- `.writ/docs/what-was-built-format.md` — add the "Reverted" annotation convention

## Success Criteria

1. `/revert story-N` on shipped or un-shipped work resolves all associated commits and undoes them (safe default), then resets the story to Not Started.
2. A rewritten (ghost) SHA is recovered via a confirmed message-similarity match.
3. Dirty working tree halts the command before any git op.
4. Hard reset requires a second destructive confirmation.
5. After revert, `context.md` and the story's status/WWB/drift-log are consistent.
6. `scripts/eval.sh` gains passing checks for the resolver and the plan-before-mutate + dirty-tree rules.

## Scope Boundaries

**Included:** `/revert` (story|spec), `revert-resolve.py`, story-SHA recording in `/implement-story`, artifact restoration, dirty-tree guard, eval checks, WWB "Reverted" annotation.

**Excluded:** phase-lane/worktree/quarantine reverts, cross-base-branch reverts, auto-revert of a released version, undo-the-undo.

**Soft link:** If spec #1 (git-notes audit) has shipped, a revert may attach a revert audit note under `refs/notes/writ` — optional, not required.

## Dependencies

None external. Internal order: Story 1 → 2 → 3 → 4 (linear).
