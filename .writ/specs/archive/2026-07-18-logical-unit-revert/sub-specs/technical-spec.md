# Technical Spec: Logical-Unit Revert

> Parent: [`../spec.md`](../spec.md)

## 1. Story-SHA recording (`/implement-story` Step 4)

After the story-completion commit, capture and record the SHA in the story file header:

```
> **Commit:** <full-sha>
```

- Obtain via `git rev-parse HEAD` immediately after the completion commit.
- Write into the story frontmatter block (near `Status`), idempotent (update if re-run).
- Backward-compat: stories without this field fall back to the resolver's later layers.

## 2. Resolver — `scripts/revert-resolve.py`

CLI: `revert-resolve.py <unit> <id> [--repo PATH] [--json]`

- `unit` ∈ {`story`, `spec`}
- `id` = story slug/number (within active spec) or spec folder id.

**Output (JSON):**

```json
{
  "unit": "story",
  "id": "story-3",
  "commits": [
    {"sha": "def456", "subject": "feat: ...", "source": "recorded", "confidence": "exact"},
    {"sha": "abc123", "subject": "conductor-style plan update", "source": "ref-footer", "confidence": "exact"}
  ],
  "ghost": [
    {"recorded": "0000dead", "candidate": "beef789", "subject": "feat: ...", "similarity": 0.86}
  ],
  "base": "111aaa",
  "warnings": ["..."]
}
```

**Resolution order (per commit source):**

1. **`recorded`** — story file `> **Commit:** <sha>` (Story 1). Verify present in history (`git cat-file -e <sha>^{commit}`).
2. **`ref-footer`** — `git log --grep "Ref: .*<story-or-spec-id>" --format=%H` (shipped work; `/ship` footer).
3. **`phase-state`** — read `.writ/state/phase-execution-*.json` for `commit`/`mergeCommit` tied to the spec/story (read-only; no mutation).
4. **`ghost`** — for any recorded SHA not found in history: `git log --format="%H%x00%s"`, score subject similarity (e.g., token-set ratio) against the recorded subject if known, else against the story title; return top candidate with `similarity`. Never auto-select — emit under `ghost` for the command to confirm.

**Spec unit:** union of all story commits + the spec-scaffolding commit (first commit that added `.writ/specs/<id>/spec.md`, via `git log --diff-filter=A --format=%H -- <spec>/spec.md`).

**Ordering:** newest → oldest (revert order). Dedup; warn on merge commits and cherry-pick duplicates (like Conductor).

**base:** parent of the earliest resolved commit (`git rev-parse <earliest>^`) — used only for hard reset.

## 3. `/revert` command flow (`commands/revert.md`)

```
Phase 1: Target selection
  - arg provided → direct; else guided menu (in-progress first, then recent completed; max 4; + "Other")
Phase 2: Resolve (call revert-resolve.py)
  - present commits; if ghost candidates → AskQuestion confirm each substitution
Phase 3: Plan gate (Dirty-tree guard FIRST)
  - if `git status --porcelain` non-empty → HALT
  - present plan: commits (sha+subject), strategy choices, artifacts to reset
  - AskQuestion: Safe (revert) [Recommended] | Hard reset (destructive) | Cancel
Phase 4: Execute
  - Safe: git revert --no-edit <sha> newest→oldest; on conflict → HALT with guidance
  - Hard: second destructive confirmation naming base → git reset --hard <base>
Phase 5: Restore artifacts (§4) + regenerate context.md + report
```

## 4. Artifact restoration

On successful revert of a unit:

- **Story status:** frontmatter `> **Status:** Not Started`; uncheck `- [x]` → `- [ ]` in tasks + AC.
- **WWB annotation:** insert a banner at the top of the story's `## What Was Built` section:
  ```
  > **Reverted:** {YYYY-MM-DD} — reverted via /revert ({strategy}); commits {short-shas}. Record preserved for history.
  ```
  Do **not** delete the WWB record.
- **drift-log entry** (append to `.writ/specs/<spec>/drift-log.md`):
  ```
  #### [DEV-NNN] Reverted {unit} {id}
  - **Severity:** n/a (revert)
  - **Action:** {safe revert | hard reset} of {N} commit(s)
  - **Commits:** {short-shas}
  - **Date:** {YYYY-MM-DD}
  ```
- **context.md:** regenerate via the same schema `/implement-story` uses (Step 2 schema).
- For a **spec** revert: apply to all its stories + set spec status back to `Not Started` / `In Progress` as appropriate.

## 5. WWB "Reverted" annotation convention

Add to `.writ/docs/what-was-built-format.md`:
- A `> **Reverted:**` banner may prefix a `## What Was Built` section.
- Downstream WWB loaders (`/implement-story` Step 2) should treat a reverted WWB as **not** authoritative for dependency context (skip or flag), since the work was undone.

## 6. Eval checks

- Unit tests for `revert-resolve.py`: recorded/footer/phase-state/ghost paths, spec union, ordering, base computation. Target ≥80% coverage on the script.
- Static assertions in `eval.sh`: `revert.md` references the dirty-tree guard, the plan-before-mutate gate, and the destructive second-confirmation for hard reset.

## 7. Non-goals

- Phase-lane/worktree/quarantine reverts (defer to `phase-state.py`).
- Cross-base-branch reverts; auto-revert of released versions; undo-the-undo.
