# Story 4: The Thin `/release` Contract

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Stories 1, 2, 3

## User Story

**As a** maintainer reading `commands/release.md` to find out where the human gates are
**I want to** the command to be a contract — phases, gates, and the release gate itself — with its procedure declared rather than inlined
**So that** the shape of the release stays visible while 13.8 KB of procedure stops loading before anyone has decided to release anything

## Scope

**One file: `commands/release.md`.** The only story that writes it.

- Delete the fourteen relocated extraction-map ranges (E1–E12b).
- Contract E13 (`## Integration with Writ`, `548–563`) into `## References`.
- **Leave the frontmatter byte-for-byte alone.** `required_skills:` is not used (spec.md → *Approved scope change*, BR3).
- Replace `## Command Process`'s inlined procedure with the phase list carrying gate names and skill pointers, plus one short `Read` anchor per phase.
- Keep, unchanged, everything the retained-ranges table in `sub-specs/technical-spec.md` lists.
- Regenerate the root `SKILL.md` **once** from the merged manifest.

## Acceptance Criteria

- [ ] Given the budget, when `python3 scripts/measure-invocation.py --root . --command release` runs, then `command_bytes` is **≤ 24,960** (from 28,589), `unresolved_skills` is `[]`, `eager_bytes` is **0** with `eager_skills: []`, `conditional_skills` lists all six inline-read skills, and the tool emits no "loads both ways" warning.
- [ ] Given Business Rule 5, when `git show <base>:commands/release.md | sed -n '154,164p'` is diffed against the corresponding block in the rewritten file, then the diff is empty — Step 1.3c's archival hook is byte-identical and still nested inside the `LAST_MERGED_SHA == HEAD_SHA` branch, which is itself still nested inside the `Unless --skip-gate is set` block.
- [ ] Given Business Rule 6, when the pin-verification script in `sub-specs/technical-spec.md` runs, then it prints `PINS OK`, and `bash scripts/eval.sh --check=post-merge-archival --check=git-notes-audit --check=artifact-integrity --check=preamble` reports no findings.
- [ ] Given the phase constraint and the mechanism ruling, when the frontmatter and `## Completion` section are diffed against the base, then the **entire frontmatter block** and the whole `## Completion` section are byte-for-byte unchanged — no key is added, and in particular no `required_skills:` key appears anywhere in the file.
- [ ] Given Business Rule 4, when the rewritten file is read, then it still contains in full: the Step 1.3a/1.3b/1.3c release gate and its three-row decision table, every `--skip-gate` mention, both `AskQuestion` blocks (Step 1.5 and Step 2.3, with `abort` and `bump_only` intact), the `## Error Handling` prompts, and the rollup's non-blocking guarantee and `writ.auditNotes` opt-out.
- [ ] Given Business Rule 3, when the rewritten file is scanned, then each of the five extracted skills is reached by **exactly one** inline `Read skills/<name>/SKILL.md` placed at the step that consumes it — `semver-version-bump` at Step 1.1 (a second anchor at Phase 3 is permitted and free), `changelog-generation` at Step 1.2, `readme-freshness-audit` at Step 1.4, `git-tag-publication` at the Phase 4 anchor, `npm-package-publication` on the `## References` line marking the runtime-helper procedure manual and out-of-band — and each is also named in the `## Command Process` phase list.
- [ ] Given hoisting forfeits the saving, when the frontmatter, `## Overview`, and the `## Command Process` phase-list table are grepped for `Read skills/`, then there are no matches in any of them, and no "load these skills first" block exists anywhere in the file.
- [ ] Given ADR-021 clause 1, when the rewritten file's top-level headings are listed, then `## Monorepo Support`, `## Dry Run Mode`, `## Integration with Writ`, and `## Runtime Helper Publish (manual)` are gone, and `## Modes` has become `## Invocation` with all seven rows intact.
- [ ] Given E13 is contracted rather than relocated, when `## References` is read, then all four `## Integration with Writ` relationships (`/implement-spec`, `/ship`, `/verify-spec`, `/status`) and the recommended `--dry-run`-then-execute flow survive as reference lines.
- [ ] Given `changelog-generation` cannot chain to `conventional-commits`, when the Step 1.2 anchor is read, then it still carries the `Read skills/conventional-commits/SKILL.md` instruction from `release.md:88`, kept at its own step and **not** moved onto a phase-list table row — and `conventional-commits` is **not** converted into a `required_skills:` entry, which would move 9,985 B into the floor for no benefit.
- [ ] Given Business Rule 10, when `git diff --name-only` is read, then it lists only `commands/release.md`, `.writ/manifest.yaml` (if a rename landed), and `SKILL.md`.
- [ ] Given the secondary tripwire, when `wc -l commands/release.md` runs, then the count is reported; under 400 is the target and a miss is recorded, not failed.

## Implementation Tasks

- [ ] 4.1 Confirm Stories 1–3 have landed and all five skill files exist; re-read each skill so the phase list points at what was actually written, not at what this spec projected
- [ ] 4.2 Record the base SHA; take `git show <base>:commands/release.md > /tmp/release-before.md` as the diff reference for every later check
- [ ] 4.3 Delete E1–E12b from the file, working bottom-up so earlier line numbers stay valid; after each deletion re-run the pin-verification script — catching a pin loss at the deletion that caused it is cheaper than at the end
- [ ] 4.4 Leave the frontmatter untouched — no `required_skills:`, no added key of any kind. Verify with a diff against `/tmp/release-before.md`
- [ ] 4.5 Write the phase list per `sub-specs/technical-spec.md` → *The Phase List* — five phases, each naming its gate (or the gate that authorized it) and its skill — then write the per-phase `Read` anchors beneath it, one inline `Read skills/<name>/SKILL.md` at each consuming step, using the established *"the skill owns how; this command owns when and which"* phrasing. The table itself carries no `Read skills/` string
- [ ] 4.6 Rename `## Modes` to `## Invocation`, preserving all seven rows verbatim
- [ ] 4.7 Contract E13's table into `## References` and add one reference line per skill; the `npm-package-publication` line is the one that carries that skill's inline `Read`, marked manual and out-of-band. Keep the `commands/_preamble.md` link (pin 15) and the `conventional-commits` read instruction at the Step 1.2 anchor
- [ ] 4.7a Run Testing Strategy check 6 and 6b from `sub-specs/technical-spec.md`: every skill inline-read exactly once at a step, every skill named in the phase list, no `Read skills/` in the phase-list table or frontmatter, `eager_bytes: 0`, `unresolved_skills: []`, no dual-load warning
- [ ] 4.8 Run the pin-verification script, then `bash scripts/eval.sh --check=post-merge-archival --check=git-notes-audit --check=artifact-integrity --check=preamble --check=length`
- [ ] 4.9 Diff the archival hook, the frontmatter, and `## Completion` against `/tmp/release-before.md`; each must be identical
- [ ] 4.10 Run `bash scripts/gen-skill.sh` once to regenerate root `SKILL.md` from the merged manifest, then `bash scripts/gen-skill.sh --check` to confirm no delta
- [ ] 4.11 Run `python3 scripts/measure-invocation.py --root . --command release --format table` and record `command_bytes`, `floor_bytes`, `ceiling_bytes`, `resolved_skills`, `unresolved_skills` in the story evidence

## Notes

**Technical considerations:**

- Deleting bottom-up matters. The extraction map's line numbers are all against the pre-spec file; a top-down deletion invalidates every subsequent range and turns a mechanical edit into a judgment call.
- The archival hook sits at `154–164`, immediately above the `@sellke/writ` note at `165` that Story 3 relocated. Deleting line 165 must not disturb 164 or the blockquote structure the hook lives in — the hook's `>` continuation lines are load-bearing markdown, not decoration.
- `## Required Artifacts` (pin 14) sits at lines 20–26, above everything this story deletes. It should be untouched; verify anyway, because `check_artifact_integrity()` names `release.md` explicitly in its seven-command loop.
- The phase list and the `Read` anchors are the only genuinely *new* prose in this spec. ADR-021's stated reason for the list is that "the *shape* stays visible even when the detail does not" — a phase line that names a skill but not its gate fails that purpose for Phases 3 and 4, which mutate production state under an authorization granted two phases earlier.
- **Where each `Read` sits is the entire deliverable, not a formatting choice.** A `Read` at Step 1.4 is not issued by a run with no `README.md`; the same `Read` collected into a list at the top of the file is issued by every run, the floor absorbs it, and the spec has produced a smaller file and no disclosure. Anchor each read at the step that *uses* the procedure, not the earliest step that mentions it — spec.md → Technical Concerns records that a long gate interaction between the anchor and the use is the residual risk here.
- Story 4 is also where the count `commands/release.md` reads goes from one skill to six. That is expected: five new anchors plus the pre-existing `conventional-commits` read. `measure-invocation.py` deduplicates by name, so `semver-version-bump`'s second anchor at Phase 3 adds nothing to any figure.

**Risks / challenges:**

- This is where the spec fails if it fails. Every constraint — budget, pins, gates, hook, frontmatter, Completion — is verified against this one file. Budget the read; the file is 640 lines and skimming it produces exactly the silent pin loss Business Rule 6 exists to catch.
- The projection says `command_bytes` lands near 16,591 against a 24,960 budget (the extra ~460 B over the pre-ruling projection is the five `Read` anchors, which replace a `required_skills:` block that would have cost 140 B in the command and 17,029 B in the floor). Do not treat the headroom as licence to leave procedure inlined "just in case" — the extraction map is the contract, and an unextracted range is a Story 5 drift-ledger gap.
- If `command_bytes` overshoots 24,960, contract retained *prose*. Never close the gap by relocating a Business Rule 4 or Business Rule 6 item; if the gate and hook alone exceed the budget, that is a finding for ADR-021's owner.

**Integration points:**

- Story 5 re-runs every check here independently and adds the drift ledger, the ceiling justification, and the full `eval.sh` baseline comparison. Story 4 proving its own work is not the same as Story 5 certifying it.
- `2026-08-11-governor-instrumentation` will later assert `## Completion` presence and a 400-line command limit against this file.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `command_bytes` ≤ 24,960, measured and recorded
- [ ] Pin-verification script prints `PINS OK`; the four named eval checks report no findings
- [ ] Archival hook, frontmatter, and `## Completion` diff clean against the base
- [ ] `bash scripts/gen-skill.sh --check` reports no delta
- [ ] No file outside `commands/release.md`, `.writ/manifest.yaml`, and `SKILL.md` is modified

## Context for Agents

- **Business rules:** [BR1 ceiling reporting, BR2 no redesign, BR3 reachability, BR4 production boundary, BR5 archival hook placement, BR6 eval pins, BR7 `_preamble.md` is not a destination, BR10 owned surfaces] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The retained thin contract; Why `npm-package-publication` is declared anyway; Skill authoring mechanics] — from spec.md → ## Detailed Requirements
- **Technical concerns:** [ADR-021 clause 3 is wrong on its face and this spec no longer follows it; a conditional load can fail; the pins make part of this file un-extractable] — from spec.md → ## Technical Concerns
- **Contract:** [Must include: the thin contract retains only what ADR-021 permits. Hardest constraint: the release gate stays in the command contract] — from spec.md → ## Contract (Locked)
- **Technical spec:** [Eval Pin Inventory + verification command; Extraction Map; Retained ranges; The Phase List; Error & Rescue Map] — from sub-specs/technical-spec.md
