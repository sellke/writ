# Story 5: Meta and Installation Command Contracts

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 1

## User Story

**As a** maintainer installing, updating, or extending Writ itself
**I want to** each of the seven meta and installation commands to declare its own problem, outcome, and exit criteria
**So that** the four commands that mutate a project's Writ installation declare what they preserve as well as what they change

## Scope

Seven commands: `new-skill`, `refresh-command`, `initialize`, `migrate`, `reinstall-writ`, `uninstall-writ`, `update-writ`.

`commands/new-command.md` belongs to this role group but is authored in Story 1 as the worked exemplar, so it is not in this batch.

Only `new-skill` carries a `## Completion` section today. The other six belong to Story 6.

## Acceptance Criteria

- [ ] Given all seven files carry `---` frontmatter with `name` and `description` and no `problem:`, when this story lands, then each carries `problem:`, `outcome:`, and `exit_criteria:` in the fixed key order, with 2–4 `exit_criteria` entries.
- [ ] Given `reinstall-writ`, `uninstall-writ`, `update-writ`, and `migrate` are destructive or state-mutating, when their `exit_criteria` are read, then each asserts a **preservation** invariant as well as a change — most importantly that `.writ/` content survives `uninstall-writ`, which is that command's stated defining property.
- [ ] Given `reinstall-writ` and `update-writ` differ precisely on whether local modifications survive, when their fields are read side by side, then that difference is stated in their `problem:` or `outcome:` lines and is not inferable only from prose.
- [ ] Given Business Rule 1, when any entry is pasted into another command in this batch, then it reads as false or nonsensical there. The `reinstall-writ` / `update-writ` / `migrate` cluster is the batch's boilerplate risk and must be checked explicitly.
- [ ] Given Business Rule 2, when any entry is compared against its own file's `description:`, then it asserts something the description does not already say.
- [ ] Given Business Rule 4, when each file is diffed, then frontmatter grew by at most 7 lines, and `grep -c '^---$'` still returns exactly 2.
- [ ] Given Business Rules 9 and 10, when `git diff --name-only` is read, then it lists only these seven files — no `scripts/` changes, no `## Completion` sections added, no command body prose rewritten, and `commands/_preamble.md` untouched.

## Implementation Tasks

- [ ] 5.1 Read `.writ/docs/component-contract.md` (Story 1) and `commands/new-command.md`'s frontmatter, which is this batch's own role-group exemplar
- [ ] 5.2 For each of the seven, identify the terminal artifact and the preservation invariant — which directories exist afterward, which survive untouched, which manifest or version file is updated
- [ ] 5.3 Author `problem:` and `outcome:` for all seven as single sentences; swap-test `reinstall-writ` / `update-writ` / `migrate` against each other first, then `initialize` against `migrate`
- [ ] 5.4 Author 2–4 `exit_criteria` per command, pairing each mutation assertion with a preservation assertion for the four state-mutating commands
- [ ] 5.5 Run the restatement test on every entry against its own `description:`
- [ ] 5.6 Verify per file: ≤7 added frontmatter lines, `grep -c '^---$'` = 2, key order correct; confirm `commands/_preamble.md` is unmodified (BR8)
- [ ] 5.7 Run `bash scripts/eval.sh`; confirm no new findings and no `scripts/` changes; record any scoping defect surfaced in the Notes without acting on it

## Notes

**Technical considerations:**

- `/uninstall-writ`'s defining property is that everything under `.writ/` survives. That is the clearest preservation invariant in the repo and exactly the kind of assertion `exit_criteria` exists to capture — a criterion asserting only what was removed would omit the command's whole point.
- `/reinstall-writ` and `/update-writ` are near-twins that differ on one axis: reinstall discards local modifications, update decides per file. If their fields do not encode that difference, the swap test has failed on the pair most likely to fail it.
- `/migrate` renames Code Captain directories to Writ with zero data loss. "Zero data loss" is an assertion — file counts before and after, no path unaccounted for — not a reassurance.
- `/refresh-command` runs the Evidence Gate and the parity check. ADR-020 mentions extending ADR-014's `status:`/`evidence:` vocabulary to commands and agents so that gate accrues per-component evidence — that is the governor spec's work, **not** this story's. Add only the three contract fields.
- `/new-skill` enforces the command/agent/skill boundary and already has a `## Completion` section. Derive from it (BR7).
- `/initialize` is infrastructure-only by design; product strategy belongs to `/plan-product`. A criterion implying it produces product docs would contradict the command.

**Risks / challenges:**

- These are the least-exercised commands in the repo, so their prose is the most likely to be stale. If a command's documented behavior does not match `scripts/install.sh` or `scripts/update.sh`, record the discrepancy in the notes and author against the *documented* behavior — reconciling them is a separate spec (BR10).
- `/refresh-command` is 492 lines and heavily cross-referential. Its `problem:` is genuinely hard to state in one line because it is a learning loop rather than an artifact producer. Resist a block scalar (BR5); if one line is genuinely impossible, that is the scoping defect BR10 says to record.
- `commands/_preamble.md` sits alphabetically among these files and is not a command. Verify it is untouched.

**Integration points:**

- Story 6 writes `## Completion` for six of these seven.
- `2026-08-11-governor-instrumentation` extends `status:`/`evidence:` to components and wires `/refresh-command`'s Evidence Gate to them — this story deliberately leaves that surface alone.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Every state-mutating command asserts a preservation invariant
- [ ] `reinstall-writ` and `update-writ` verified as non-interchangeable
- [ ] `commands/_preamble.md` confirmed unmodified
- [ ] `bash scripts/eval.sh` shows no new findings

## Context for Agents

- **Business rules:** [BR1 swap test, BR2 restatement test, BR3 observable requirement, BR4 line budget, BR5 one-line fields, BR7 no contradiction with `## Completion`, BR8 `_preamble.md` excluded, BR9 no eval checks, BR10 no substance rewrite] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The contract schema; Command batching → Meta & installation] — from spec.md → ## Detailed Requirements
- **Out of scope:** [`status:`/`evidence:` extension belongs to the governor spec, not this one] — from spec.md → ## Out of Scope
- **Contract:** [Must include: no new mechanism — commands extend the `---` YAML already present in 32/32 files] — from spec.md → ## Contract (Locked)
- **Technical spec:** [Carrier Analysis → Command frontmatter; Interaction Edge Cases → `_preamble.md`, `refresh-command.md`] — from sub-specs/technical-spec.md
