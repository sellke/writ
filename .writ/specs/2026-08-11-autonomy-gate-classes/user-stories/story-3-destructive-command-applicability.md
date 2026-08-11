# Story 3: Verify the Precondition Is Applicable to Destructive-Class Commands

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 2

## User Story

**As a** Writ maintainer who has just removed the human gate from destructive operations
**I want** a recorded, per-command answer to whether an agent can actually evaluate both precondition conditions before invoking `/revert`, `/refactor`, `/uninstall-writ`, or `/reinstall-writ`
**So that** the precondition is known to be a check something can perform, not a sentence that reads well and decides nothing

## Acceptance Criteria

- [ ] Given the four destructive-class commands ADR-022 names, when this story completes, then the story file contains a filled applicability table with an explicit yes/no for **each condition** for **each command** — twelve cells, none blank, none "n/a".
- [ ] Given any "no" answer, when it is read, then it is accompanied by one paragraph naming precisely what an agent reading `commands/_preamble.md` would be unable to determine before acting.
- [ ] Given the `/uninstall-writ` row, when it is assessed, then the assessment explicitly addresses platform files that are untracked or gitignored in a target project — the case condition (1) exists to catch.
- [ ] Given the `/revert` row, when it is assessed, then the assessment distinguishes the `git revert` path from the `git reset --hard` path, which have different reversibility properties.
- [ ] Given this story's completion, when `git status` is inspected, then **no file under `commands/` has been modified** — this is a read-only pass.
- [ ] Given any finding that warrants a behavior change, when it is recorded, then it is filed via `/create-issue` and referenced by ID from this story, not fixed here.

## Implementation Tasks

- [ ] 3.1 Read the final `## Autonomy Gate Classes` section in `commands/_preamble.md` as shipped by Story 2 — the assessment is against the wording that actually landed, not against the draft in the technical spec.
- [ ] 3.2 Read `commands/revert.md` and assess both conditions for both of its paths (`git revert` default; `git reset --hard` behind a second confirmation). Note its existing dirty-tree HALT guard (lines 56-62) — condition (1) implemented under a different name.
- [ ] 3.3 Read `commands/refactor.md` and assess both conditions, including its one-verified-commit-per-concern discipline and its tests-green-either-side requirement.
- [ ] 3.4 Read `commands/uninstall-writ.md` and assess both conditions, specifically for platform files that may be untracked or gitignored in a target project, and for the manifest it reads before deleting.
- [ ] 3.5 Read `commands/reinstall-writ.md` and assess both conditions, specifically for local modifications discarded during the reinstall and whether the manifest baselines constitute a "restore path recorded before the mutation".
- [ ] 3.6 Fill the applicability table in this story's "What Was Built" section, with a paragraph per "no".
- [ ] 3.7 For each "no" that warrants a behavior change, file a `/create-issue` entry and reference its path here. Do not edit any command file.
- [ ] 3.8 Record a one-paragraph honest verdict: does the precondition, as written, discriminate between recoverable and unrecoverable invocations of these four commands — or does it currently pass everything?

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

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing (n/a — read-only story; the deliverable is the recorded assessment)
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** [Rule 5 (the precondition is an enforceable rule with two individually-checkable conditions), Rule 7 (the recorded dissent stays recorded — this assessment is part of the honest record), Rule 9 (no command files change; findings become issues)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [Applicability of the precondition to the destructive-class commands] — from spec.md → ## Detailed Requirements
- **Technical concerns:** [The precondition is prose, not enforcement — this story measures the gap, it does not fill it; the decision this records was contested] — from spec.md → ## Technical Concerns
- **Contract:** [Must include: the two conditions stated as an enforceable rule, not advice] — from spec.md → ## Contract (Locked)
- **Technical detail:** [Applicability table template and the known starting observations per command] — from sub-specs/technical-spec.md → ## Story 3
- **Governing ADR:** [`.writ/decision-records/adr-022-autonomy-gate-classes.md`] — the destructive-class command list, the "what the precondition protects against" paragraph, and the 2026-11-11 review trigger
