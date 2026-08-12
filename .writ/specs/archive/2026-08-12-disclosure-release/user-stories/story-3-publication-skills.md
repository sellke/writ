# Story 3: Publication and Runtime-Helper Skills

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** maintainer running `/release --no-tag` or `/release --dry-run`
**I want to** tag, push, GitHub-release, rollup-composition, summary, and dry-run rendering detail to live in a skill Phase 4 loads
**So that** the command file stops carrying 6.4 KB of publication procedure, and the phase list still shows a reader that Phase 4 is where a release becomes public

## Scope

Two skills, created via `/new-skill`. Seven extraction-map ranges, 6,366 bytes.

| Skill | Absorbs | Bytes |
|---|---|---|
| `git-tag-publication` | E7 (`371–403`) tag/push/`gh release create` · E8a (`425–431`) rollup composition · E8b (`443–447`) summary confirmation line · E9 (`449–470`) Phase 5 summary · E10 (`473–518`) dry-run detail | 3,912 |
| `npm-package-publication` | E12a (`165`) the `@sellke/writ` decoupling note · E12b (`600–626`) `## Runtime Helper Publish (manual)` | 2,454 |

**Explicitly NOT in scope:** `release.md:405–424` and `433–441` — the rollup's opt-out gate, its non-blocking guarantee, and the `TAG_TARGET_SHA` attach block — stay in the command. They carry eval pins 9–13 and Business Rule 4's non-blocking promise.

**This story does not touch `commands/release.md`.**

## Acceptance Criteria

- [ ] Given `/new-skill` is the authoring path, when both skills exist, then each carries `disable-model-invocation: true` and `status: candidate` and `bash scripts/lint-skill.sh` exits 0 for both.
- [ ] Given eval pins 9–13, when `git-tag-publication` is written, then it does **not** become the only home for `refs/notes/writ`, `writ.auditNotes`, `git notes --ref=writ add -f -F`, `TAG_TARGET_SHA`, or the non-blocking phrase — Story 4 must still find each of them in `commands/release.md`. Duplicating a pinned string into the skill is permitted where the procedure needs it; removing it from the command is not.
- [ ] Given Business Rule 4, when `git-tag-publication` is read, then it contains no authorization: no `AskQuestion`, no `--skip-gate` handling, and no statement that a release may proceed. It describes how to execute Phase 4 after Step 2.3 already authorized it.
- [ ] Given the audit rollup is **strictly non-blocking**, when the composition procedure in `git-tag-publication` is read, then it restates that a composition or attachment failure never fails the release — the promise appears in both places, because a skill that silently drops it teaches the opposite.
- [ ] Given E12b applies only to the Writ source repository, when `npm-package-publication` is read, then that scoping survives, along with the reason `scripts/publish-writ-runtime.sh` is used instead of raw `npm publish` (npm always bundles the root `README.md`) and the `git checkout` trap that restores it.
- [ ] Given `npm-package-publication` is reached by an inline `Read` on the `## References` line that marks the runtime-helper procedure manual and out-of-band — its narrowest anchor, because that procedure is not a phase of `/release` (BR3, exemption reinstated 2026-08-12) — when Story 4 wires it, then no `/release` path issues that `Read`, the skill is still reachable and still counted in `measure-invocation.py`'s worst-path ceiling, and its byte count is handed to Story 5 as both a named ceiling lever and the line item that separates the tool's worst path from the worst *release* path.
- [ ] Given Business Rule 2, when each of E7, E8a, E8b, E9, E10, E12a, E12b is diffed against its destination, then the drift ledger records `none (verbatim)` or `contracted: <reason>` and nothing else.
- [ ] Given Business Rule 9, when either body is scanned, then no line begins with a slash command (E10's `Run /release minor to execute for real.` must not open a line) and no line contains `Read commands/`, `Read skills/`, or `Task(`.
- [ ] Given Business Rule 10, when `git diff --name-only` is read, then it lists only the two `SKILL.md` files and `.writ/manifest.yaml`.

## Implementation Tasks

- [ ] 3.1 Record the base SHA; dump E7, E8a, E8b, E9, E10, E12a, E12b via `git show <base>:commands/release.md | sed -n '<range>p'`
- [ ] 3.2 Re-read `ls skills/` and `.writ/manifest.yaml` (BR8); `/ship` is a sibling spec's surface and may have created an overlapping publication skill — consume it rather than forking if so
- [ ] 3.3 Scaffold `git-tag-publication`; write tag → push → `gh release create` → rollup composition → summary in source order, keeping the `gh`-unavailable fallback message and its manual-creation URL
- [ ] 3.4 Fold E10's dry-run detail into `git-tag-publication` as a `## When to Use` trigger plus a preview subsection; keep the eight-item "does / does NOT" list and the full "Commands that would run" block, including the `git notes` line and its `writ.auditNotes` caveat
- [ ] 3.5 Scaffold `npm-package-publication`; carry E12b's five-command sequence, the three decoupling bullets from E12a, the README-swap rationale, and the closing "no gate, no preflight, no orchestration" statement
- [ ] 3.6 Cross-reference the two halves of the `@sellke/writ` decoupling in prose — this skill for the publish procedure, `semver-version-bump` for the Step 3.1 skip guard — without either skill reading the other
- [ ] 3.7 Run `bash scripts/lint-skill.sh` on both; append manifest entries alphabetically; do not run `gen-skill.sh` in write mode
- [ ] 3.8 Apply Compression Ledger candidates C1 (dry-run restatement), C2 (summary/preview collapse) and C4 (`publish-writ-runtime.sh` rationale) and record the **measured** yield of each — estimates are not evidence
- [ ] 3.9 Write drift-ledger rows for all seven ranges; hand both skills' measured byte counts to Story 5; confirm `git diff --name-only` lists only the three expected files

## Notes

**Technical considerations:**

- E8a's composition rule — *reuse the changelog-from-completed-specs list already assembled in Phase 1/2, do not re-scan* — is a real constraint, not advice. Re-scanning `.writ/specs/` after Step 1.3c's archival hook has moved a folder produces a wrong rollup. Carry the sentence.
- E9's summary template has a `Audit rollup:` line with two states (attached / skipped on `writ.auditNotes=false`). Both states.
- E10's dry-run block is the only place the *whole* flow is described end to end. It is the most tempting range to "tidy" and the one where tidying is most visible as drift.

**Risks / challenges:**

- The rollup is split across a boundary: the opt-out gate and attach command stay in the command (pins), the composition detail moves. A reader of either half alone must not conclude the rollup is blocking. Both halves state non-blocking; that duplication is deliberate.
- `npm-package-publication` is ~2,754 B net (2,454 prose + ~650 scaffolding − C4) that **no `/release` run pays**, because no `/release` run issues its `Read`. An earlier draft of this spec exempted it, then withdrew the exemption under the pilot's "declare all" rule; the exemption is **reinstated as correct** now that the mechanism is an inline read rather than a static array (spec.md → *Why `npm-package-publication` costs no `/release` run anything*). Nothing is hidden: the tool's regex still finds the `## References` `Read` line and still counts the skill in the worst-path ceiling, which is why it remains the single largest lever if Story 5 needs that figure under 63,534. Dropping the extraction returns ~2,754 B of worst-path ceiling and costs ~2,454 B of floor — a trade of a number no run pays against one every run pays. Maintainer decision, recorded in Story 5, not made here.
- E10's dry-run block sits in this skill by dominance, not by clean fit: its substance is the "Commands that would run" list (`git add`/`commit`/`tag`/`push`/`gh release`/`git notes`), which is Phase 4. It is also Compression Ledger candidate C1 — ~60% of it restates procedure specified elsewhere in the same skill set. **Under conditional loading this placement has a visible cost:** `--dry-run` previews those commands, so a dry run reads `git-tag-publication` and saves nothing. Record it; do not relocate E10 to improve the number, which would be a redesign of the extraction map (BR2).

**Integration points:**

- Story 4 places both skills' inline `Read`s — `git-tag-publication` at the Phase 4 anchor, `npm-package-publication` on the manual/out-of-band `## References` line — and names both in the phase list. Neither is declared in `required_skills:`; that key is not used by this spec.
- Story 5 measures both against Business Rule 1 and works Compression Ledger candidates C1, C2, and C4, all of which live in these two skills.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `bash scripts/lint-skill.sh` exits 0 for both skills
- [ ] Drift-ledger rows for E7, E8a, E8b, E9, E10, E12a, E12b recorded
- [ ] `npm-package-publication`'s byte count recorded and handed to Story 5 as a named ceiling lever
- [ ] `commands/release.md` unmodified by this story

## Context for Agents

- **Business rules:** [BR2 no redesign + drift ledger, BR4 production boundary incl. the rollup's non-blocking guarantee, BR6 eval pin inventory, BR8 shared namespace, BR9 capability-not-workflow, BR10 owned surfaces] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [Why `npm-package-publication` is declared anyway; The extraction map] — from spec.md → ## Detailed Requirements
- **Technical concerns:** [The pins make part of this file un-extractable] — from spec.md → ## Technical Concerns
- **Contract:** [Hardest constraint: the release gate stays in the command contract, never in a conditionally-loaded skill] — from spec.md → ## Contract (Locked)
- **Technical spec:** [Eval Pin Inventory rows 9–13; Extraction Map E7–E12b; Interaction Edge Cases — `--no-tag`/`bump_only`] — from sub-specs/technical-spec.md
