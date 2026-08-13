---
name: subagent-worktree-integration
description: "Reconcile a spawned agent's isolated git worktree with the orchestrator's own checkout, and detect when that worktree is stale."
disable-model-invocation: true
status: candidate
---

# Sub-Agent Worktree Integration

## Purpose

Some platforms isolate every spawned sub-agent — including nominally
read-only ones — in its own git worktree by default, regardless of whether
the gate asked for isolation. An agent's tool result naming a worktree path
or branch means its output lives outside the orchestrator's own checkout
until it is deliberately reconciled: diffed, copied over, re-verified, and
the worktree removed. Skipping any of those steps either loses the agent's
work when its worktree is discarded, or lets unverified changes reach the
orchestrator's checkout untested.

## When to Use

- After any spawned gate agent's turn completes and its result mentions a
  worktree path or a branch name distinct from the orchestrator's current
  checkout — architecture-check, review, and visual-QA agents are
  nominally read-only but can still be isolated this way.
- Before treating a spawned agent's file changes as present in the
  orchestrator's checkout — an isolated worktree's changes do not exist
  anywhere else until copied.
- Not needed when a spawned agent's result carries no worktree reference —
  some platforms run sub-agents directly in the caller's checkout, and nothing
  here applies.

## How to Apply

### 1. Recognize isolation

Check the spawned agent's returned result for a worktree path or a branch
name that differs from the orchestrator's own current branch/checkout path.
Its presence is the signal — do not assume isolation from the gate type
alone, since even read-only gates can be isolated.

### 2. Diff scoped to the story's owned files

Diff the isolated worktree against the orchestrator's checkout, scoped to
the files the story's task list and boundary map say it owns — not a
full-repository diff, which would surface unrelated drift from either side
moving independently. A change outside the story's owned scope is a signal
to inspect before copying it, not to copy it silently.

### 3. Copy changed and created files into the main checkout

Copy exactly the files the scoped diff reports as changed or newly created
in the isolated worktree into the corresponding paths of the orchestrator's
own checkout. Files present in the worktree but outside the story's owned
scope are not copied without inspection first.

### 4. Re-verify in the orchestrator's own checkout

Never trust the isolated worktree's own verification as sufficient — run
verification again in the orchestrator's checkout, after the copy, because
the copy is the step most likely to silently drop a file or leave a stale
one behind:

- **Minimum, every time:** lint and typecheck for the languages the touched
  files belong to.
- **When the story's own pipeline includes a test suite:** run it too,
  scoped to the same files, before treating the copy as trustworthy.

### 5. Remove the worktree

Once the copy is verified, remove the isolated worktree and any branch that
existed only to hold it. A worktree left behind after its output is already
reconciled is dead state with no further purpose.

### 6. Recognize and resolve a stale worktree

A worktree can be **behind** the orchestrator's checkout — missing commits
from earlier stories in the same spec that landed after the worktree was
created. This is a distinct, recognizable failure mode, not a silent
surprise: its symptom is a diff that looks larger than the story's actual
change (because the worktree is also missing unrelated prior work), or the
agent's output referencing files or behavior the orchestrator's checkout
already changed.

Two resolutions, either is valid depending on what already happened:

- **Fast-forward the worktree** to the orchestrator's current state before
  re-diffing, when the agent's own work has not yet started incorporating
  the missing commits.
- **Re-read the agent's output against the correct baseline** — treating
  its reported diff as relative to the commits it actually started from,
  rather than the orchestrator's current head — when re-running the agent
  from a fast-forwarded worktree would waste already-good work.

Do not silently copy a stale worktree's files over newer work already in the
orchestrator's checkout — that would revert the intervening commits without
anyone deciding to.

## Examples

**Recognizing isolation:**

```
Agent result: "...changes are in /tmp/worktrees/review-a1b2/ on branch
review-agent-a1b2..."
```
A worktree path and branch distinct from the orchestrator's checkout — this
skill applies before the result is treated as already present.

**Stale worktree symptom:**

A review agent's diff shows five files changed, but the story's task list
only names two. The other three match files an earlier story in the same
spec already modified in the orchestrator's checkout — the worktree was
created before that story's commit landed. Fast-forward the worktree, or
re-read the agent's report against its actual starting commit, before
copying anything.
