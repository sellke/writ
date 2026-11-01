---
category: lessons
tags: [uat, parallel-agents, safety]
created: 2026-10-22
related_artifacts: [.writ/issues/improvements/2026-10-21-uat-plan-helpers-can-write-to-the-repo.md]
---

# Parallel UAT agents never share scratch files

## TL;DR

Give each parallel agent its own temp folder and its own env file, and make every setup helper refuse a write outside that folder. On 2026-10-21, five UAT agents shared one scratchpad `env.sh`. One overwrote another's, an empty `$OLD` turned `git -C ""` into the current directory, and a helper committed `a8aa8d8 "old release"` onto the real `main`.

## Context

Recorded during the Phase 13 UAT close-out (176 scenarios, five plans).

- The commit was caught and removed with `git reset --keep b850e66` before any push.
- `git -C ""` does not fail. It runs in the current directory, which for an agent is usually the repo.
- First attribution was wrong: the agent that ran the commit was not the one blamed first. Check `git reflog` and each agent's own transcript before assigning a cause.
- Fix applied to the five plans: `cd "$W"` right after `mktemp`, and `gc` returns 1 for any path not under `$W`. The generator fix is the linked issue.

**Cited evidence:**

- `.writ/specs/2026-10-20-*/uat-plan.md` setup blocks (the guards)
- `.writ/issues/improvements/2026-10-21-uat-plan-helpers-can-write-to-the-repo.md`

## Related

- [UAT plan helpers can write to the repo](../../issues/improvements/2026-10-21-uat-plan-helpers-can-write-to-the-repo.md)
