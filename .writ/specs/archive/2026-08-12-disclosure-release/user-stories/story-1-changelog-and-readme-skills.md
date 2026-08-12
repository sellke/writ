# Story 1: Changelog Generation and README Freshness Skills

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** maintainer running `/release` on a repo that needs no changelog work
**I want to** the changelog-authoring and README-drift procedures to live in skills the command names but does not carry
**So that** a gate-blocked or `--no-tag` run stops paying 3.7 KB for prose it never reaches

## Scope

Two skills, created via `/new-skill`. Three extraction-map ranges, 3,212 bytes of relocated prose.

| Skill | Absorbs | Bytes |
|---|---|---|
| `changelog-generation` | E2 (`release.md:78–97`, Step 1.2 Analyze Changes) · E5 (`release.md:236–292`, Steps 2.1–2.2) | 2,354 |
| `readme-freshness-audit` | E3 (`release.md:167–200`, Step 1.4) | 1,858 |

**This story does not touch `commands/release.md`.** It reads it. Story 4 is the only story that writes it.

## Acceptance Criteria

- [ ] Given `/new-skill` is the authoring path, when both skills exist, then each carries `disable-model-invocation: true` and `status: candidate` in its frontmatter and `bash scripts/lint-skill.sh skills/<name>/SKILL.md` exits 0.
- [ ] Given Business Rule 2, when each skill body is compared against its source range via `git show <base>:commands/release.md | sed -n '<range>p'`, then every step, table row, format block, and priority ordering is present with a `semantic delta` of `none (verbatim)` or `contracted: <reason>` — no step added, removed, reordered, or re-defaulted.
- [ ] Given Business Rule 4, when either skill body is grepped for `--skip-gate`, `AskQuestion`, `Block release`, or `Proceed with this release`, then there are no matches — neither skill contains a gate-crossing decision.
- [ ] Given `release.md:88` contains `Read skills/conventional-commits/SKILL.md`, when `changelog-generation` is written, then that line does **not** appear in it (`scripts/lint-skill.sh:52` rejects skill chaining), the vocabulary is **not** copied into it (ADR-021 clause 4), and the read instruction is instead flagged for Story 4 to retain in `commands/release.md` **at the Step 1.2 anchor** — not on a phase-list table row, and not converted into a `required_skills:` entry. The E2 drift-ledger row records `contracted: read instruction retained in the command at its own step`.
- [ ] Given the loading mechanism is an inline `Read` in the command (spec.md → *Approved scope change*, BR3), when either skill is written, then neither contains any `Read skills/` line at all — `grep -n 'Read skills/' skills/changelog-generation/SKILL.md skills/readme-freshness-audit/SKILL.md` returns nothing, including inside code fences, and each skill's `Read` anchor is recorded in the story evidence for Story 4 to place (`changelog-generation` → Step 1.2; `readme-freshness-audit` → Step 1.4).
- [ ] Given Business Rule 9, when either body is scanned, then no line begins with a slash command and no line contains `Read commands/`, `Read skills/`, or `Task(`.
- [ ] Given Business Rule 8, when the skills are named, then `ls skills/` and `.writ/manifest.yaml` were re-read immediately before scaffolding and no sibling spec already owns an equivalent capability; any rename against `2026-08-12-disclosure-implement-story`'s convention is recorded in the Notes.
- [ ] Given the manifest is shared, when `.writ/manifest.yaml` is edited, then this story appends exactly its own alphabetically placed entries and does **not** run `scripts/gen-skill.sh` in write mode — Story 4 regenerates the root `SKILL.md` once.
- [ ] Given Business Rule 10, when `git diff --name-only` is read, then it lists only `skills/changelog-generation/SKILL.md`, `skills/readme-freshness-audit/SKILL.md`, and `.writ/manifest.yaml`.

## Implementation Tasks

- [ ] 1.1 Record the base SHA (`git rev-parse HEAD`) in the story evidence; dump E2, E3, E5 with `git show <base>:commands/release.md | sed -n '<range>p'` as the drift-ledger source of truth
- [ ] 1.2 Re-read `ls skills/` and `.writ/manifest.yaml`; confirm both names are free — grep for the name **and its head noun** per the pilot spec's collision protocol — and that no sibling skill already covers changelog authoring or README drift
- [ ] 1.3 Scaffold `changelog-generation` with `/new-skill`; write `## Purpose`, `## When to Use`, `## How to Apply` from E2 + E5, resolving the `conventional-commits` chaining hazard per the acceptance criterion
- [ ] 1.4 Scaffold `readme-freshness-audit` with `/new-skill`; carry E3's four-row check table, the pass line, the discrepancy block, the recommendation, and the explicit "what this check does NOT do" limit — that last paragraph is the skill's boundary and is not optional prose
- [ ] 1.5 Run `bash scripts/lint-skill.sh skills/changelog-generation/SKILL.md skills/readme-freshness-audit/SKILL.md`; fix by restructuring sentences, never by dropping procedure
- [ ] 1.6 Append both manifest entries alphabetically; verify with `bash scripts/gen-skill.sh --check` (read-only — expect a delta until Story 4 regenerates)
- [ ] 1.7 Apply Compression Ledger candidates C3 (changelog skeleton placeholders) and C5 (README discrepancy example block) and record their **measured** yields
- [ ] 1.8 Write the drift ledger rows for E2, E3, E5 into the story evidence and confirm `git diff --name-only` lists only the three expected files

## Notes

**Technical considerations:**

- E5 carries the Keep a Changelog section vocabulary (`Added` / `Changed` / `Fixed` / `Security` / `Breaking Changes` / `Internal`), the four-level source priority, and the five quality rules. All three are procedure, not illustration — dropping the "don't list every commit" rule changes output.
- E3's final paragraph explicitly scopes the README check *out* of semantic validation ("descriptions are judgment calls"). Losing it turns a bounded structural check into an unbounded one — the exact drift Business Rule 2 forbids.
- E2's breaking-change detection has four probes (commit message, public API signatures, destructive migrations, environment variables). Four, not "several."

**Risks / challenges:**

- The `conventional-commits` chaining hazard is the one place where an obvious transcription produces a lint failure. Resolve it by **leaving the read instruction in the command at its own step**, not by duplicating the vocabulary and not by adding `conventional-commits` to `required_skills:`. A declaration would move 9,985 B into the floor for no benefit, and the corrected instrument already counts the inline read symmetrically on both sides (technical-spec → *Ceiling arithmetic*).
- `readme-freshness-audit` is the clearest example of what the mechanism change buys: a repo with no `README.md` never reaches Step 1.4, so its `Read` is never issued and its ~2,258 B are never paid. Under the withdrawn `required_skills:` mechanism that repo would have pre-loaded it on every run.
- `readme-freshness-audit` is Compression Ledger candidate **C6** — the structural lever if C1–C5's measured yields fall short of the ceiling bar. Write it so it can be folded into `changelog-generation` without a rewrite: self-contained sections, no forward references. Note the trade has a new cost under conditional loading: folding the two couples their paths, so a repo with no `README.md` would then load the README procedure anyway. Record that when handing C6 to Story 5.

**Integration points:**

- Story 4 places each skill's inline `Read` at its anchor (Step 1.2, Step 1.4) and names both in the phase list — reachability and placement (BR3) are proven there, not here. Neither skill is declared in `required_skills:`; that key is not used by this spec.
- Story 5 measures the ceiling these skills contribute to.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `bash scripts/lint-skill.sh` exits 0 for both skills
- [ ] Drift ledger rows for E2, E3, E5 recorded with `semantic delta` values
- [ ] `commands/release.md` unmodified by this story

## Context for Agents

- **Business rules:** [BR2 no redesign + drift ledger, BR4 production boundary, BR8 shared namespace, BR9 capability-not-workflow, BR10 owned surfaces] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The extraction map; Skill authoring mechanics] — from spec.md → ## Detailed Requirements
- **Technical concerns:** [Six specs share `skills/`, `.writ/manifest.yaml`, and the generated root `SKILL.md`] — from spec.md → ## Technical Concerns
- **Contract:** [Must include: skills authored through `/new-skill`, born `status: candidate`, lint-clean] — from spec.md → ## Contract (Locked)
- **Technical spec:** [Extraction Map E2/E3/E5; Skill Roster; Lint hazards in the extracted prose] — from sub-specs/technical-spec.md
