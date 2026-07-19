# Logical-Unit Revert (Lite)

> Source: .writ/specs/2026-07-18-logical-unit-revert/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** New `/revert <unit>` command (story|spec) that maps a logical unit to its commits, offers safe/hard revert, and restores Writ artifacts. Prerequisite: record story commit SHA in `/implement-story`.

**Implementation Approach:**
- Product-source only: markdown command + one python helper (`revert-resolve.py`, patterned on `spec-deps.py`/`phase-state.py`).
- Layered resolver: recorded story SHA → `/ship` `Ref:` footer grep → phase-state JSON → ghost-commit fuzzy match (confirmed).
- Plan-before-mutate: confirmation gate showing exact commits + strategy before any git op.
- Full restoration: status→Not Started, WWB annotated (not deleted), drift-log entry, regenerate context.md.

**Files in Scope:**
- `commands/revert.md` (new)
- `commands/implement-story.md` — Step 4 records `> **Commit:** <sha>` into story file
- `scripts/revert-resolve.py` (new)
- `scripts/eval.sh` (+ helper)
- `.writ/docs/what-was-built-format.md` — "Reverted" annotation convention

**Error Handling:**
- Dirty tree → halt before any git op
- Missing/rewritten SHA → ghost-commit search + confirm
- Revert conflict → halt with manual-resolution guidance
- Hard reset → second destructive confirmation

**Integration Points:**
- Reads `/ship` `Ref:` footer, `phase-state.py` state; writes story files, drift-log, context.md. Optional: attach revert note (spec #1).

---

## For Review Agents

**Acceptance Criteria:**
1. `/revert story-N` (shipped or un-shipped) resolves all commits, undoes them (safe default), resets story → Not Started.
2. Rewritten (ghost) SHA recovered via confirmed message-similarity match.
3. Dirty tree halts before any git op.
4. Hard reset requires second destructive confirmation.
5. Post-revert: context.md + story status/WWB/drift-log consistent.

**Business Rules:**
- Plan-before-mutate confirmation gate.
- Dirty-tree guard.
- Safe (git revert) default; hard reset second confirmation.
- Ghost-commit substitution requires confirmation.
- Full artifact restoration.
- Story+spec only; phase-lane reverts out of scope.

**Experience Design:**
- Entry: `/revert` guided menu, or `/revert story-3` / `/revert spec <id>`.
- Happy path: resolve → plan → confirm+strategy → execute → restore → report.
- Moment of truth: pre-execution plan of commits+artifacts before mutation.
- Error: dirty tree halt; ghost-commit confirm; conflict halt; hard-reset double confirm.

---

## For Testing Agents

**Success Criteria:**
1. Resolver returns correct ordered commit list per unit.
2. Ghost-commit fallback finds + flags a rewritten SHA.
3. Guards fire (dirty tree, destructive confirm).
4. Artifacts restored consistently.

**Shadow Paths to Verify:**
- **Happy:** story with recorded SHA → resolved + reverted.
- **Nil:** no recorded SHA → falls back to `Ref:` footer / ghost-commit.
- **Empty:** unit with no commits → halt with explanation.
- **Upstream error:** revert conflict → halt with guidance, repo left mid-revert.

**Edge Cases:**
- Rebased/squashed history → ghost-commit confirmed substitution.
- Spec revert → union of story commits + spec-scaffold commit.
- Dirty tree → refuse to start.
- Hard reset → parent-of-earliest base, double confirm.

**Verification Strategy (methodology repo):**
- `revert-resolve.py` is real code → unit-testable; target ≥80% on the resolver.
- Command rules verified via `scripts/eval.sh` static checks + manual dogfood on this repo.
