# Story 1: Retire `/explain-code` into a Skill

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer pruning weak command surface
**I want to** retire the thin `/explain-code` command and lift its durable explanation template into `skills/code-explanation/SKILL.md`, wiring a live consumer
**So that** the ~10 durable lines survive as a reusable capability while the redundant command disappears from every active surface

## Acceptance Criteria

- [x] Given the retirement is complete, when I list active command surfaces, then `skills/code-explanation/SKILL.md` exists with `status: candidate` and an initial evidence note, `commands/explain-code.md` is deleted, and `bash scripts/lint-skill.sh skills/code-explanation/SKILL.md` exits clean.
- [x] Given `code-explanation` is `disable-model-invocation: true`, when I inspect its consumer, then `commands/research.md` contains a literal `Read skills/code-explanation/SKILL.md` directive at the point where it explains code, so the capability is reachable rather than orphaned.
- [x] Given every active reference, when retirement completes, then `/explain-code` is absent from `.writ/manifest.yaml`, the regenerated root `SKILL.md`, both `commands/status.md` allowlists, `README.md`, `adapters/cursor.md`, `claude-code/CLAUDE.md`, `codex/AGENTS.md.template`, and `commands/new-command.md`.
- [x] Given historical artifacts, when the retirement grep runs with the D6 allowlist, then `/explain-code` survives only in `.writ/specs/`, `.writ/decision-records/`, `.writ/explanations/`, `CHANGELOG.md`, and roadmap history, and nowhere on active product surfaces.
- [x] Given the manifest now registers `code-explanation`, when `bash scripts/gen-skill.sh` regenerates the catalog, then the root `SKILL.md` lists the skill and no longer lists the `/explain-code` command.

## Implementation Tasks

- [x] 1.1 Define the retirement allowlist and run a baseline grep for `/explain-code` across the repo, recording exactly which active surfaces must be rerouted versus which historical paths are exempt (per `technical-spec.md` → D6).
- [x] 1.2 Author `skills/code-explanation/SKILL.md` from the Step 3 template of `commands/explain-code.md` (Purpose → How It Works → Context → Diagrams [conditional] → Complexity Notes [conditional]) as capability prose, with frontmatter `status: candidate` and an evidence note; run `bash scripts/lint-skill.sh skills/code-explanation/SKILL.md` and rewrite any orchestration prose until it exits clean.
- [x] 1.3 Wire `commands/research.md` to `Read skills/code-explanation/SKILL.md` at its code-explanation point of use, with a D5-shaped orchestration note (skill owns the template; research owns when to explain and what target).
- [x] 1.4 Delete `commands/explain-code.md` and remove the `explain-code` command entry from `.writ/manifest.yaml`; add the `code-explanation` skill entry alphabetically under `skills:`.
- [x] 1.5 Reroute/remove `/explain-code` from `commands/status.md` (both allowlists, ~184 and ~344), `README.md` (~145), `adapters/cursor.md` (~48), `claude-code/CLAUDE.md` (~28), `codex/AGENTS.md.template` (~65), and `commands/new-command.md` (~146).
- [x] 1.6 Regenerate the root catalog with `bash scripts/gen-skill.sh` and confirm it lists `code-explanation` and omits `/explain-code`.
- [x] 1.7 Verify the story: `bash scripts/lint-skill.sh skills/code-explanation/SKILL.md`, the allowlisted `/explain-code` absence grep over active surfaces, and a grep confirming `commands/research.md` references the skill path.

## Notes

- The command is **deleted**, not archived in place — unlike Ralph, `/explain-code` has no runtime state or scripts to preserve, only a redirect to write.
- `code-explanation` is the extraction with the subtlest consumer story: retiring the command removes its wrapper, so `commands/research.md` must adopt the capability or the skill is dead under `disable-model-invocation: true`.
- Keep the skill body free of `/refactor`, `/research`, `/create-adr` as line-leading slash commands (lint rejects them); reference commands in running prose instead.
- The manifest edit is shared-additive with `2026-07-10-skill-lifecycle`; keep `skills:` alphabetical.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] `skills/code-explanation/SKILL.md` lints clean
- [x] `/explain-code` absent from active surfaces (allowlisted history excepted)
- [x] Root `SKILL.md` regenerated

## Context for Agents

- **Error map rows:** [`technical-spec.md` → `## Error & Rescue Map` → `Delete commands/explain-code.md`, `technical-spec.md` → `## Error & Rescue Map` → `Author skill body`, `technical-spec.md` → `## Error & Rescue Map` → `Wire consumer`]
- **Shadow paths:** [`technical-spec.md` → `## Shadow Paths` → `/explain-code retirement`, `technical-spec.md` → `## Shadow Paths` → `Catalog sync`]
- **Business rules:** [`spec.md` → `### Business Rules` → Rule 6 (deletion + reroute targets), `spec.md` → `### Business Rules` → Rule 2 (born candidate), `spec.md` → `### Business Rules` → Rule 4 (explicit load, live consumer)]
- **Experience:** [`spec.md` → `## Detailed Requirements` → R3 (retire into code-explanation), `technical-spec.md` → `### D6 — Retirement Is Deletion Plus Reroute`, `technical-spec.md` → `### D4 — Explicit Load, Explicit Consumer`]
