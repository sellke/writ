---
name: story-commit-provenance
description: "Record a completion commit SHA into a story file header idempotently and without amending it."
disable-model-invocation: true
status: candidate
---

# Story Commit Provenance

## Purpose

Write the SHA of the commit that completed a story into that story's own header,
so the story can later be mapped to its exact commit without guessing. Tooling
that unwinds work treats this field as its **highest-confidence resolution
layer** — everything else it falls back to is inference. The ordering is
awkward: the SHA does not exist until the commit does, so it cannot live inside
the commit it names.

## When to Use

- Immediately after the commit that closes out a story — the one carrying the
  status flip, the checked tasks and acceptance criteria, and the completion
  record.
- On a re-run or re-implementation of a story that already carries the field.

## How to Apply

1. **Capture the SHA:** `git rev-parse HEAD`. This is the completion commit —
   the revert target — not the bookkeeping commit that follows.

2. **Write it into the header:** add
   `> **Commit:** <full-sha>` to the story file's header block — the
   `> **Status:** …` metadata block near the top — so provenance sits beside
   status.

3. **Idempotent write:** if a `> **Commit:**` line already exists, **update it
   in place. Never append a duplicate.**

4. **Land the field in the next commit.** Fold the one-line header write into
   the immediately-following bookkeeping commit — the same small follow-up that
   carries any post-commit housekeeping, e.g.
   `git commit -am "chore(story): record commit SHA"`.

   **Do NOT `--amend` the completion commit — amending would rewrite the very
   SHA just recorded.** The reason is the rule: the recorded SHA points at the
   completion commit, while the tiny record-SHA commit is inert.

### Backward compatibility

The field is **optional**. Work completed before this convention — or reduced
runs that skip bookkeeping — simply lacks `> **Commit:**`. Resolution tooling
tolerates its absence and falls back to later layers (a merge footer reference,
recorded phase state, a ghost-commit match). **Never fail a story for a missing
SHA field.**
