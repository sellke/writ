# Story 3: Verify the Precondition Is Applicable to Destructive-Class Commands

> **Status:** Complete
> **Priority:** Medium
> **Dependencies:** Story 2

## User Story

**As a** Writ maintainer who has just removed the human gate from destructive operations
**I want** a recorded, per-command answer to whether an agent can actually evaluate both precondition conditions before invoking `/revert`, `/refactor`, `/uninstall-writ`, or `/reinstall-writ`
**So that** the precondition is known to be a check something can perform, not a sentence that reads well and decides nothing

## Acceptance Criteria

- [x] Given the four destructive-class commands ADR-022 names, when this story completes, then the story file contains a filled applicability table with an explicit yes/no for **each condition** for **each command** — twelve cells, none blank, none "n/a".
- [x] Given any "no" answer, when it is read, then it is accompanied by one paragraph naming precisely what an agent reading `commands/_preamble.md` would be unable to determine before acting.
- [x] Given the `/uninstall-writ` row, when it is assessed, then the assessment explicitly addresses platform files that are untracked or gitignored in a target project — the case condition (1) exists to catch.
- [x] Given the `/revert` row, when it is assessed, then the assessment distinguishes the `git revert` path from the `git reset --hard` path, which have different reversibility properties.
- [x] Given this story's completion, when `git status` is inspected, then **no file under `commands/` has been modified** — this is a read-only pass.
- [x] Given any finding that warrants a behavior change, when it is recorded, then it is filed via `/create-issue` and referenced by ID from this story, not fixed here.

## Implementation Tasks

- [x] 3.1 Read the final `## Autonomy Gate Classes` section in `commands/_preamble.md` as shipped by Story 2 — the assessment is against the wording that actually landed, not against the draft in the technical spec.
- [x] 3.2 Read `commands/revert.md` and assess both conditions for both of its paths (`git revert` default; `git reset --hard` behind a second confirmation). Note its existing dirty-tree HALT guard (lines 56-62) — condition (1) implemented under a different name.
- [x] 3.3 Read `commands/refactor.md` and assess both conditions, including its one-verified-commit-per-concern discipline and its tests-green-either-side requirement.
- [x] 3.4 Read `commands/uninstall-writ.md` and assess both conditions, specifically for platform files that may be untracked or gitignored in a target project, and for the manifest it reads before deleting.
- [x] 3.5 Read `commands/reinstall-writ.md` and assess both conditions, specifically for local modifications discarded during the reinstall and whether the manifest baselines constitute a "restore path recorded before the mutation".
- [x] 3.6 Fill the applicability table in this story's "What Was Built" section, with a paragraph per "no".
- [x] 3.7 For each "no" that warrants a behavior change, file a `/create-issue` entry and reference its path here. Do not edit any command file.
- [x] 3.8 Record a one-paragraph honest verdict: does the precondition, as written, discriminate between recoverable and unrecoverable invocations of these four commands — or does it currently pass everything?

## Notes

**Technical considerations:**

- The question is deliberately narrow: **can both conditions be evaluated by an agent, before acting, from the command's own documented flow?** Not "is this command safe" and not "should this command be gated" — those are ADR-022's decisions, already made.
- Condition (1) fails on untracked files, uncommitted working-tree changes, operations reaching outside the repository, and any operation without a resolvable revert target. Test each command against all four failure modes, not just the first.
- Condition (2) is an ordering requirement. A command that reports what it deleted *after* deleting satisfies nothing; the restore path has to be written while the pre-mutation state still exists.
- `/revert` already resolves target commits and shows the plan before mutating (`scripts/revert-resolve.py`), which is close to a recorded restore path. Assess whether "close to" is enough, and say so plainly either way.
- The likeliest genuine "no" is `/uninstall-writ` in a target project where `.claude/` or `.cursor/` is gitignored — the files it deletes are then not git-revertable at all. That would be the precondition working as designed (pause), and it is worth recording as the concrete case that justifies the precondition's existence.

**Risks / challenges:**

- **The comfortable outcome is four yeses, and it is the one to distrust.** ADR-022 records this precondition as prose with no implementation — "until one exists, the precondition is prose, not enforcement". If this assessment concludes that everything passes cleanly, the likely explanation is that the conditions were read charitably, not that the commands are provably reversible.
- Scope drift into fixing what is found. Business Rule 9 makes this read-only for a reason: editing four command files inside an `Effort: XS` spec would collide with other Phase 10 work and grow a one-table change into a command-surface change.
- This story is not automatable and produces no test. Its value is entirely in the honesty of the record, which is also why the verdict in Task 3.8 is a required deliverable rather than a closing remark.

**Integration points:**

- Depends on Story 2's shipped wording.
- Feeds ADR-022's **2026-11-11 review trigger**: if this assessment finds conditions that cannot be evaluated for a command, that is early evidence relevant to the review, and it should be summarized in the story's verdict so the review does not have to rediscover it.
- Any issue filed here is a candidate input to a later Phase 10 spec (a mechanical revertability check, or per-command precondition wiring) — neither of which is in scope now.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing (n/a — read-only story; the deliverable is the recorded assessment)
- [x] Code reviewed
- [x] Documentation updated

## What Was Built

A read-only assessment of the four destructive-class commands ADR-022 names, against the precondition as it actually shipped in `commands/_preamble.md` (Story 2), not against the technical spec's draft. No file under `commands/` was modified.

### How each cell is scored

Columns (1) and (2) answer **does the condition hold for every documented path of this command?** A command with one failing path scores **No**, and the prose below names the path. That is the right framing for a gate: the precondition guards an invocation, so a class that holds "usually" does not hold. Column (3) answers the narrower question the story asks — **can an agent, before acting, determine the answers from the command's documented flow plus ordinary git inspection?**

### Applicability table

| Command | (1) Provably git-revertable? | (2) Restore path recorded before mutation? | Evaluable by an agent reading `_preamble.md`? |
|---|---|---|---|
| `/revert` | **No** — holds for `git revert`, fails for `git reset --hard` | **No** — the plan is presented, not persisted | **Yes** |
| `/refactor` | **No** — no dirty-tree guard; `--dead-code` can delete untracked files | **No** — nothing durable is written before the first edit | **Yes** |
| `/uninstall-writ` | **No** — deletes files that may be untracked or gitignored | **No** — a count of what will be lost is not a restore path | **Yes** |
| `/reinstall-writ` | **No** — untracked file set, plus a network clone outside the repo | **No** — manifest baselines are hashes, and the manifest is deleted | **Yes** |

Twelve cells, twelve explicit answers, no blanks and no `n/a`. Eight of them are No.

### `/revert` — the two paths differ, and only one is revertable

`/revert` is the strongest of the four, and it still fails both conditions.

| Path | (1) git-revertable? | Why |
|---|---|---|
| `git revert --no-edit` (default, Recommended) | **Yes** | Additive history. The reverted commits remain reachable; the revert commits are themselves revertable. Phase 3's `git status --porcelain` HALT (`commands/revert.md:56-62`) closes both the untracked-file and uncommitted-changes failure modes in one check — porcelain reports untracked entries as `??`, so the guard covers more than its name suggests. Phase 2's resolver halts when the commit list is empty, which closes the no-resolvable-revert-target mode. |
| `git reset --hard <base>` (behind a second confirmation) | **No** | Rewinds the branch and discards every commit after `base`. Those commits survive only in the reflog — local, expiring, and outside the tracked-file guarantee the precondition names. You cannot `git revert` a `git reset --hard`; there is no revert target by construction. |

So condition (1) is a per-invocation answer for `/revert`, decided at the Phase 3 strategy gate — which is *before* Phase 4 mutates. An agent can evaluate it. The precondition would permit the safe path unattended and pause the hard-reset path, which is exactly the discrimination ADR-022 wanted from replacing a name-based blocklist with a risk test.

**Condition (2) — why "No" despite the best plan machinery of the four.** Phase 3 presents the resolved commit list and the `base` SHA before anything mutates, and `scripts/revert-resolve.py` produces them read-only in Phase 2. That is *close to* a recorded restore path, and the story asks for a plain answer on whether close is enough: **it is not.** The plan is displayed in conversation, and conversation is not a record — it does not survive the session, and nothing downstream can read it. The only durable write is the Phase 5 git-notes audit entry, which is explicitly optional (*"may attach"*, *"skip silently if the channel is absent"*) and lands **after** Phase 4 executed. A restore path written after the mutation is what the precondition's emphasis on "before" exists to reject.

For the `git revert` path this is a formality — git's own preserved history is the restore path, and it exists before and after. For the hard-reset path it is the whole problem: the one moment the discarded SHAs are knowable is the moment before the reset, and nothing writes them down.

### `/refactor` — a green baseline is not a clean tree

Condition (1) fails, and the reason is a specific, fixable gap rather than an inherent property. `commands/refactor.md` Step 1.2 gates on tests, typechecker, and linter — git state is not among them, and `skills/safe-refactor-loop/SKILL.md` step 0 repeats the same trio. The skill's step 1 says *"Checkpoint — note the current clean git state so a revert is one step"*, which **assumes** a clean tree and prescribes nothing that establishes one. `/revert` runs precisely this check and lists it as its first safety guarantee; `/refactor` does not, despite its loop reverting on every red verification.

Two of the four condition-(1) failure modes are open here. **Uncommitted working-tree changes:** started dirty, the "revert immediately" step operates on a tree mixing the agent's edit with the user's uncommitted work, and cannot distinguish them. **Untracked files:** `--dead-code` removes "orphan files"; an untracked orphan, once deleted, has no git object to restore from at all.

Condition (2) fails for the same reason as `/refactor`'s condition (1) — the checkpoint is prose. Nothing durable is written before the first edit; the first record is the first refactor commit, which lands after the first mutation. One-verified-commit-per-concern makes each *completed* change revertable, but it says nothing about the state that existed before the first one.

Filed: [`.writ/issues/bugs/2026-08-11-refactor-has-no-dirty-tree-guard.md`](../../../issues/bugs/2026-08-11-refactor-has-no-dirty-tree-guard.md).

### `/uninstall-writ` — the case the precondition exists to catch

This is the genuine one, and it lands as the technical spec predicted.

Condition (1) fails on the file set. Step 3 deletes `[platform_dir]/commands/*.md`, `[platform_dir]/agents/*.md`, `CLAUDE.md`, the Writ block in `AGENTS.md`, and `.writ-manifest`. In a *target* project nothing guarantees those are tracked — `.claude/` and `.cursor/` are commonly gitignored, and Writ's own `install.sh` gitignores only `.writ/state/`, so the platform directory's status is entirely the target project's business. Step 4 then stages with `git add -u`, which the command documents as *"stage deletions without adding untracked files"*: the deletion of an untracked platform file is never captured in any commit, so there is nothing to revert and no warning that this happened. Error Handling documents a second outright failure — *"No git repo | Skip commit step"* — an invocation with no revert target whatsoever.

Condition (2) fails and the near-miss is instructive. Step 2's confirmation does compute the right number: *"Customized files: [K] (will be lost)"*. That is a warning computed before the mutation, and it is not a restore path — it tells the user how much they are about to lose without preserving any of it. The Step 5 summary prints a reinstall `curl` command, which restores **upstream defaults**, not the K customized files, and prints after the deletion regardless.

Both are evaluable. Step 2 already inventories the exact file list before Step 3 deletes it, so an agent can run `git ls-files --error-unmatch` or `git check-ignore` over that list while the files still exist. On a project that gitignores `.claude/`, condition (1) returns false and the operation pauses — the precondition working exactly as designed, and the concrete case that justifies its existence.

### `/reinstall-writ` — manifest baselines are a detector, not a restore path

Condition (1) fails on everything `/uninstall-writ` fails on, plus one more failure mode: Step 4 runs `git clone` from `https://github.com/sellke/writ.git`, an operation reaching outside the repository. The command's own Error Handling then documents the terminal case explicitly — clone fails after Step 3's removal succeeded, and the published recovery is a manual `bash <(curl -s .../install.sh)`, not a git operation. A documented state whose only exit is re-downloading the internet is the definition of "no resolvable revert target".

Condition (2) is the question the story poses directly: do the manifest baselines constitute a restore path recorded before the mutation? **No.** The manifest records baseline **hashes**. A hash proves a file was customized; it cannot reconstruct one byte of the customization. And Step 3 deletes `.writ-manifest` along with everything else, so even the detector does not survive the operation. Local modifications are recoverable only if they were independently committed — which is a property of the user's git hygiene, not of anything the command records.

### Verdict (Task 3.8)

**The precondition discriminates — and the honest result is that it currently blocks all four commands, not that it passes everything.** Eight of the twelve cells are No, and the reasons differ per command rather than reducing to one generic complaint: `/revert` fails on one of its two strategies, `/refactor` on a missing guard its own sibling command already implements, `/uninstall-writ` on a file set that may not be in git at all, `/reinstall-writ` on a network operation with a documented unrecoverable failure state. That is a test doing work. A test that passed all four would have meant the conditions were read charitably, and that outcome was the one to distrust.

Two things follow, and both matter to ADR-022's **2026-11-11 review trigger**.

First, **the practical effect of the destructive-class row today is "pause", not "autonomous"**, because condition (2) is unsatisfiable by every one of the four — no command has any mechanism for recording a restore path before mutating, and the one durable audit channel that exists (`refs/notes/writ`) is optional and fires afterward. The safety regression the recorded objection warned about has not materialized, because the precondition as written holds the line. It also means the autonomy ADR-022 intended to unlock is not actually available yet. Filed as [`.writ/issues/improvements/2026-08-11-restore-path-recording-for-destructive-commands.md`](../../../issues/improvements/2026-08-11-restore-path-recording-for-destructive-commands.md), with the explicit note that it should be closed by building the mechanism, never by relaxing the precondition's wording to fit what the commands already do.

Second, **every "Evaluable" answer is Yes only because an agent can run checks none of these four commands document.** `git status --porcelain`, `git ls-files --error-unmatch`, `git check-ignore` — the information is all obtainable before mutating, but only `/revert` builds any of it into its own flow. This is precisely the gap ADR-022 names as a negative consequence: *"until one exists, the precondition is prose, not enforcement."* This assessment measures that gap and confirms it is real across all four; it does not fill it, and it should not be read as having done so.

### Read-only confirmation

`git status --porcelain commands/` is empty for this story, and `git log --stat` for its commit touches no path under `commands/`. Business Rule 9 held.

## Context for Agents

- **Business rules:** [Rule 5 (the precondition is an enforceable rule with two individually-checkable conditions), Rule 7 (the recorded dissent stays recorded — this assessment is part of the honest record), Rule 9 (no command files change; findings become issues)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [Applicability of the precondition to the destructive-class commands] — from spec.md → ## Detailed Requirements
- **Technical concerns:** [The precondition is prose, not enforcement — this story measures the gap, it does not fill it; the decision this records was contested] — from spec.md → ## Technical Concerns
- **Contract:** [Must include: the two conditions stated as an enforceable rule, not advice] — from spec.md → ## Contract (Locked)
- **Technical detail:** [Applicability table template and the known starting observations per command] — from sub-specs/technical-spec.md → ## Story 3
- **Governing ADR:** [`.writ/decision-records/adr-022-autonomy-gate-classes.md`] — the destructive-class command list, the "what the precondition protects against" paragraph, and the 2026-11-11 review trigger
