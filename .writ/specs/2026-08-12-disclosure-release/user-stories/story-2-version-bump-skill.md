# Story 2: Version Resolution and Bump Mechanics Skill

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** maintainer whose release stops at the gate or at the Step 2.3 confirmation
**I want to** version-source detection, bump derivation, version-file writes, and monorepo scope selection to live in one skill the command names
**So that** 3.2 KB of write-path mechanics is not loaded by runs that never reach the write path

## Scope

One skill, `semver-version-bump`, created via `/new-skill`. Four extraction-map ranges, 3,201 bytes.

| Range | Source | Content |
|---|---|---|
| E1 | `release.md:51–76` | Version-source detection chain (7 priorities) + release-context gather (`CURRENT_VERSION`, `LAST_TAG`, `COMMITS`, `SPECS`) |
| E4 | `release.md:203–209` | Automatic bump-determination table (breaking → major, features → minor, fixes → patch, docs/chore → patch) |
| E6 | `release.md:328–367` | Step 3.1 version-file updates across Node/Python/Rust/`VERSION`, the `@sellke/writ` skip guard, and Step 3.2 release commit |
| E11 | `release.md:520–545` | Monorepo scope selection and the `@scope/package@version` tag pattern |

**Explicitly NOT in scope:** `release.md:39–50` (the `.writ/config.md` convention load) stays in the command — the gate resolves `Test Runner` from it. `release.md:211–230` (the Step 1.5 `AskQuestion` proposal) stays in the command — Business Rule 4.

**This story does not touch `commands/release.md`.**

## Acceptance Criteria

- [ ] Given `/new-skill` is the authoring path, when the skill exists, then it carries `disable-model-invocation: true` and `status: candidate` and `bash scripts/lint-skill.sh skills/semver-version-bump/SKILL.md` exits 0.
- [ ] Given E1's detection chain is ordered, when the skill is read, then all seven priorities appear in the same order (`package.json`, `Cargo.toml`, `pyproject.toml`, `setup.py`/`setup.cfg`, `VERSION`, git tags, none → `0.1.0`) — the order *is* the behavior.
- [ ] Given E6 contains the `PKG_NAME != "@sellke/writ"` guard, when the skill is read, then the guard is present with its skip semantics intact, and the skill cross-references that the runtime helper's own publish procedure lives elsewhere (Story 3's `npm-package-publication`) without reading that skill.
- [ ] Given E6's parenthetical about `package-lock.json` and `bun.lock`, and the note that Step 2.3's "Files to update" preview omits `package.json` for `@sellke/writ`, when the skill is read, then both survive — the preview note is a behavior of the confirmation gate that this skill must state, since the gate itself stays in the command.
- [ ] Given Business Rule 4, when the skill body is grepped for `--skip-gate`, `AskQuestion`, `Proceed with this release`, or `Block release`, then there are no matches. The bump-determination table (E4) is a derivation, not an authorization — it may live here; the `AskQuestion` that presents it may not.
- [ ] Given Business Rule 2, when each of E1, E4, E6, E11 is diffed against the skill body, then the drift ledger records `none (verbatim)` or `contracted: <reason>` and nothing else.
- [ ] Given Business Rule 9, when the body is scanned, then no line begins with a slash command and no line contains `Read commands/`, `Read skills/`, or `Task(` — including inside code fences, which the lint exempts but this spec does not. The cross-reference to `npm-package-publication` (below) is prose, never a `Read`.
- [ ] Given Business Rule 10, when `git diff --name-only` is read, then it lists only `skills/semver-version-bump/SKILL.md` and `.writ/manifest.yaml`.

## Implementation Tasks

- [ ] 2.1 Record the base SHA; dump E1, E4, E6, E11 via `git show <base>:commands/release.md | sed -n '<range>p'`
- [ ] 2.2 Re-read `ls skills/` and `.writ/manifest.yaml` (BR8); confirm no sibling spec has created a versioning skill this range should consume instead
- [ ] 2.3 Scaffold `semver-version-bump` with `/new-skill`; description must be a verb-phrase that survives the lint's role- and workflow-shape grammar
- [ ] 2.4 Write `## How to Apply` in the source order — resolve source, gather context, derive bump, write files, commit — and keep the four ecosystem write blocks (`npm version`/`jq` fallback, `pyproject.toml`, `Cargo.toml`, `VERSION`) as code, which the lint exempts
- [ ] 2.5 Add the monorepo section (E11) as a distinct `## When to Use` trigger plus its own `## How to Apply` subsection, so a single-package repo can skip it by reading rather than by loading
- [ ] 2.6 Run `bash scripts/lint-skill.sh`; append the manifest entry alphabetically; do not run `gen-skill.sh` in write mode
- [ ] 2.7 Apply Compression Ledger candidate C7 (E1's gather-block comments) and record its **measured** yield
- [ ] 2.8 Write drift-ledger rows for E1, E4, E6, E11; confirm `git diff --name-only` lists only the two expected files

## Notes

**Technical considerations:**

- E1's `SPECS=$(scan .writ/specs/ for specs completed after last release date)` is deliberately pseudo-code in the source. Keep it pseudo-code. Turning it into a concrete command is a redesign and would also collide with the archival hook's sequencing note (Step 1.3c may have moved a spec folder to `.writ/specs/archive/` before Phase 2 reads it).
- E6's `sed -i` lines are GNU-flavored and will not run as written on BSD `sed`. That is a pre-existing defect in the source. **Carry it across unchanged and record it in the Notes** (BR2, BR10) — fixing it here is a behavior change smuggled inside a relocation.
- The `@sellke/writ` guard and the runtime-helper publish procedure are two halves of one decoupling. The guard is version-bump behavior and belongs here; the publish procedure is Story 3's. Both skills must say so in prose or a reader of either gets half the rule.

**Risks / challenges:**

- E4 is a table that *decides* the version bump, which reads like a gate. It is not — the human gate is the `AskQuestion` in `release.md:211–230` that presents the table's suggestion alongside five alternatives and an abort. Keeping that distinction crisp is this story's main correctness risk under Business Rule 4.
- This is the largest single skill in the spec at 3,201 B of relocated prose. If it drifts past ~4 KB it is worth checking whether monorepo scope should split out — but only against a measured ceiling, not on feel, and a sixth skill costs ~650 B of scaffolding to save 588 B of prose.

**Integration points:**

- Story 4 places this skill's inline `Read` at the Step 1.1 anchor and names it at Phase 1 and Phase 3 in the phase list (it is the one skill spanning two phases). A second `Read` at the Phase 3 anchor is permitted and costs nothing — `measure-invocation.py` deduplicates by name. It is **not** declared in `required_skills:`; that key is not used by this spec (spec.md → *Approved scope change*, BR3).
- This skill is read on nearly every `/release` path, so its 3,201 B behave close to floor-like in practice even though they are formally conditional. That is a fact for Story 5's path table, not a reason to relax the extraction.
- Story 3's `npm-package-publication` carries the other half of the `@sellke/writ` decoupling.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `bash scripts/lint-skill.sh skills/semver-version-bump/SKILL.md` exits 0
- [ ] Drift-ledger rows for E1, E4, E6, E11 recorded
- [ ] The pre-existing `sed -i` portability defect is recorded in the Notes and not fixed
- [ ] `commands/release.md` unmodified by this story

## Context for Agents

- **Business rules:** [BR2 no redesign + drift ledger, BR4 production boundary, BR8 shared namespace, BR9 capability-not-workflow, BR10 owned surfaces] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The retained thin contract — Step 1.5 `AskQuestion` stays; The extraction map] — from spec.md → ## Detailed Requirements
- **Technical concerns:** [`/release` is a sequential pipeline — this skill loads on nearly every path] — from spec.md → ## Technical Concerns
- **Contract:** [Hardest constraint: no production-boundary decision in a conditionally-loaded skill] — from spec.md → ## Contract (Locked)
- **Technical spec:** [Extraction Map E1/E4/E6/E11; Retained ranges; Interaction Edge Cases — the `@sellke/writ` guard] — from sub-specs/technical-spec.md
