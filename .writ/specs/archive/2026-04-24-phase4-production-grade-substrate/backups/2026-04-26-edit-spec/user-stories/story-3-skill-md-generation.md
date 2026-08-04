# Story 3: SKILL.md Template Generation

> **Status:** Completed ✅
> **Priority:** High
> **Effort:** S (~1–2 days)
> **Dependencies:** None (independent of Stories 1, 2; required by Story 4)
> **Source recommendation:** Research addendum → "Skills-Creation Infrastructure" → "Build a minimal version"

## User Story

**As a** Writ maintainer
**I want** `SKILL.md` generated from a single source of truth (`.writ/manifest.yaml`) with a CI gate that fails on drift
**So that** command/agent docs cannot silently diverge from behavior, and a teammate (or future-self) can trust SKILL.md as accurate without spot-checking each command file

## Acceptance Criteria

- [x] Given the spec ships, when I inspect the repo, then `.writ/manifest.yaml` exists with one entry per command in `commands/` and one entry per agent in `agents/` (excluding `_*.md` infra files)
- [x] Given the manifest is valid, when I run `bash scripts/gen-skill.sh`, then `SKILL.md` is regenerated with the frontmatter preserved (lines 1–4) and the body replaced from manifest data, exit code 0
- [x] Given `SKILL.md` matches the manifest, when I run `bash scripts/gen-skill.sh --check`, then the script exits 0 with no diff output
- [x] Given `SKILL.md` has been hand-edited (or the manifest changed without regeneration), when `bash scripts/gen-skill.sh --check` runs, then it exits 1 and prints a structured diff
- [x] Given the manifest is malformed (e.g., a command entry missing required field `name`), when `gen-skill.sh` runs in any mode, then it exits 1 with a YAML error pointing at the offending key
- [x] Given `yq` is not installed on the contributor's machine, when `gen-skill.sh` runs, then it falls back to a pure-bash YAML reader and reports which mode is active

## Implementation Tasks

- [x] 3.1 Write a verification checklist covering all 6 acceptance criteria; commit as `.writ/specs/.../user-stories/story-3-verification.md`
- [x] 3.2 Author `.writ/manifest.yaml` with full schema (per `sub-specs/technical-spec.md` → Story 3); enumerate every current command and agent
- [x] 3.3 Author `scripts/gen-skill.sh` matching the bash style of `install.sh` and `ralph.sh`; implement default mode, `--dry-run`, `--check`; preserve `SKILL.md` frontmatter; emit the "do not edit by hand" header comment after frontmatter
- [x] 3.4 Implement the pure-bash YAML reader fallback for the limited subset the manifest uses (no anchors, no flow style); detect `yq` availability and report active mode
- [x] 3.5 Run `gen-skill.sh` once to regenerate `SKILL.md` from the manifest; commit the regenerated file
- [x] 3.6 Add CI gate `.github/workflows/eval.yml` (or extend existing CI) with `gen-skill.sh --check` step
- [x] 3.7 Verify all acceptance criteria via checklist (including a deliberate manifest edit + `--check` failure verification); capture results in `## What Was Built`

## Notes

**Dual-use justification (per ADR-007):** Solo dev: SKILL.md drift is already a real risk — the eval gate eliminates it now. Team-readiness: the manifest becomes the single truth a teammate can trust without spot-checking; preamble enforcement (Story 4) reuses the same iteration surface (manifest → for-each-command).

**Technical considerations:**
- YAML manifest selected over per-command frontmatter or inline JSON (per spec.md → Implementation Approach → Manifest format selection)
- `yq` is the preferred parser; the pure-bash fallback supports only the limited subset the manifest needs (flat keys, simple lists, no anchors). If the manifest grows beyond this, swap fallback for a require-yq check.
- `SKILL.md` frontmatter (4 lines) is preserved verbatim; only the body is regenerated. This protects the `name: writ` and `description:` fields that some platforms key on.
- The `<!-- generated; do not edit -->` header comment is the primary deterrent against manual edits; the CI check is the structural enforcement.
- Manifest schema is versioned (`version: 1`); future schema changes can detect old versions and migrate.

**Risks:**
- **YAML format proves brittle for what the manifest needs:** mitigated by the pure-bash fallback covering the same subset; can swap to JSON if needed without breaking the generator interface
- **CI machine lacks `yq`:** mitigated by the snap-install step in the workflow; pure-bash fallback also works
- **Manifest entries drift from filesystem:** mitigated by Story 5's `manifest` eval check (every manifest entry exists in filesystem; no orphan files)

**Integration points:**
- Story 4 (preamble enforcement) reads the manifest to iterate over commands when verifying preamble references
- Story 5 (eval Tier 1) includes a `manifest` check that validates well-formedness and orphan-file detection
- The CI workflow is shared with Story 5's `eval.sh` step (single workflow file)

## Definition of Done

- [x] All tasks completed
- [x] All 6 acceptance criteria verified
- [x] `bash scripts/gen-skill.sh --check` exits 0 against committed `SKILL.md` after regeneration
- [x] CI gate is installed and the same `--check` command was verified locally against deliberate drift. Remote CI execution remains pending until a PR/push exists.
- [x] `SKILL.md` contains the "do not edit by hand" header comment
- [x] Drift log entries (if any) recorded — none required for Story 3
- [x] `## What Was Built` section appended

## Context for Agents

- **Error map rows:** Malformed manifest (`spec.md → 🎯 Experience Design → Error experience`); SKILL.md drift detected by `--check`
- **Shadow paths:** Happy path: edit manifest → run `gen-skill.sh` → SKILL.md regenerated → CI passes. Upstream error: malformed manifest → fail with YAML error + line (`spec.md → 🎯 Experience Design → Error experience`)
- **Business rules:** SKILL.md is generated post-ship; manual edits prohibited (header comment declares); manifest schema is versioned (`spec.md → 📋 Business Rules`)
- **Experience:** Quiet on success; structured diff on drift; preserves frontmatter (`spec.md → 🎯 Experience Design → Feedback model`)
- **Technical reference:** `sub-specs/technical-spec.md → Story 3` (manifest schema, gen-skill.sh interface, header comment, CI gate)
- **Source recommendation:** Research addendum → "Skills-Creation Infrastructure" table → first row → "Build a minimal version"

## What Was Built

Story 3 shipped the manifest-driven `SKILL.md` generation path:

- Added `.writ/manifest.yaml` as the single source of truth for Writ command and agent metadata. It enumerates all 30 current commands and all 7 current agents, with category labels used by generated documentation.
- Added `scripts/gen-skill.sh` with default write mode, `--dry-run`, and `--check`. It preserves the existing `SKILL.md` frontmatter, replaces the body with generated content, and emits the required do-not-edit header.
- Implemented parser selection: `yq` is preferred when available; otherwise the script uses a pure-bash fallback for the manifest subset Writ owns. The script reports the active mode on each run.
- Regenerated `SKILL.md` from the manifest.
- Added `.github/workflows/eval.yml` with the Story 3 `bash scripts/gen-skill.sh --check` gate. Story 5 will extend this workflow with the full `scripts/eval.sh` runner.
- Added `story-3-verification.md` with acceptance-criteria evidence, including deliberate drift and malformed-manifest simulations.

Verification performed:

- `bash scripts/gen-skill.sh --dry-run >/tmp/writ-skill-dry-run.md` — passed
- `bash scripts/gen-skill.sh` — passed and regenerated `SKILL.md`
- `bash scripts/gen-skill.sh --check` — passed clean after regeneration
- Deliberate `SKILL.md` drift simulation — `--check` exited 1 and printed a unified diff; `SKILL.md` was regenerated afterward
- Deliberate malformed manifest simulation missing command `name` — generator exited 1 with `YAML error: commands[0] missing required field 'name'`; manifest was restored afterward

Notes:

- `yq` was not installed in this environment, so the verified parser path was the pure-bash fallback.
- No remote CI run was performed because this task must not push or open a PR.
