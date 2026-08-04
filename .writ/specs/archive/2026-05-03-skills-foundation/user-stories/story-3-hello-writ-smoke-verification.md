# Story 3: Hello-Writ Smoke Verification

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** Story 1 (manifest schema), Story 2 (install fanout)
> **Estimated Effort:** Small
> **Completed:** 2026-05-03 — All 5 acceptance scenarios verified; smoke skill fully cleaned up

## User Story

**As a** Writ maintainer shipping the skills foundation,
**I want** an end-to-end smoke verification that authoring → manifest → install fanout actually delivers a SKILL.md to platform-native paths on at least Cursor and Claude Code,
**So that** I have empirical proof the integration works before any production skill is extracted — and the smoke artifact is then *removed* so the foundation ships clean.

## Acceptance Criteria

### Scenario 1: Smoke skill is authored cleanly
- **Given** Story 1 (manifest schema) and Story 2 (install fanout) are complete
- **When** I author `skills/hello-writ/SKILL.md` with a verb-phrase description ("Demonstrates the skill loading path end-to-end") and `disable-model-invocation: true` frontmatter, and add a `skills:` entry to `.writ/manifest.yaml`
- **Then** `bash scripts/gen-skill.sh --check` exits 0 and root `SKILL.md` includes the hello-writ entry in the Skills table

### Scenario 2: Cursor install delivers the skill
- **Given** the smoke skill exists in source and a fresh sandbox project at `/tmp/writ-smoke-cursor-*`
- **When** I run `bash scripts/install.sh --platform cursor --no-commit` from the sandbox
- **Then** `.cursor/skills/hello-writ/SKILL.md` exists with frontmatter intact (verified: `disable-model-invocation: true` is present); install summary reports `Skills: 1 new`

### Scenario 3: Claude Code install delivers the skill
- **Given** the smoke skill exists in source and a fresh sandbox project at `/tmp/writ-smoke-claude-*`
- **When** I run `bash scripts/install.sh --platform claude --no-commit` from the sandbox
- **Then** `.claude/skills/hello-writ/SKILL.md` exists with frontmatter intact; install summary reports `Skills: 1 new`

### Scenario 4: Skill is loadable on Cursor
- **Given** Cursor sandbox install from Scenario 2
- **When** I open the sandbox in Cursor and check the skill auto-discovery section (Cursor exposes installed skills via `<agent_skills>` system context)
- **Then** the smoke skill appears with its description and verb-phrase semantics intact (visual confirmation only — no automated assertion)

### Scenario 5: Smoke skill is fully removed before merge
- **Given** Scenarios 1–4 have all passed
- **When** I run the cleanup task (delete `skills/hello-writ/` directory, remove the manifest entry, regenerate `SKILL.md`)
- **Then** `git status` shows zero pending changes related to hello-writ; `bash scripts/gen-skill.sh --check` exits 0 against the cleaned-up state; `git diff main` shows no `skills/hello-writ` artifacts

## Implementation Tasks

- [x] **Author smoke skill:** Create `skills/hello-writ/SKILL.md` with the structure documented in Story 6's `/new-skill` scaffolder (Purpose, When to Use, How to Apply, Examples) and `disable-model-invocation: true` frontmatter
- [x] **Add manifest entry:** Append a `skills:` block with the hello-writ entry; regenerate root `SKILL.md` via `bash scripts/gen-skill.sh`
- [x] **Cursor sandbox test:** Create `/tmp/writ-smoke-cursor-$(date +%s)`, run install from this repo's `scripts/install.sh`, verify `.cursor/skills/hello-writ/SKILL.md` exists with frontmatter intact
- [x] **Claude Code sandbox test:** Create `/tmp/writ-smoke-claude-$(date +%s)`, run install with `--platform claude`, verify `.claude/skills/hello-writ/SKILL.md` exists with frontmatter intact
- [x] **Frontmatter assertion:** Programmatically verify (`grep "disable-model-invocation: true"`) that the platform-native files retain the frontmatter byte-for-byte
- [x] **Three-way overlay smoke test:** Edit the local `.cursor/skills/hello-writ/SKILL.md` in the sandbox, run install again, verify overlay preserves the local edit (covers Story 2's preservation guarantee with a real skill)
- [x] **Loadability check (Cursor):** Document a manual verification step where the maintainer opens a fresh Cursor session in the sandbox and confirms the skill appears in agent context (one paragraph in story DoD record)
- [x] **Cleanup — file system:** `rm -rf skills/hello-writ/`
- [x] **Cleanup — manifest:** Remove the `skills:` entry; if `skills:` becomes empty, leave the empty list (`skills: []`) for future entries
- [x] **Cleanup — root SKILL.md:** Run `bash scripts/gen-skill.sh` to regenerate; verify Skills section is absent
- [x] **Cleanup — sandboxes:** Delete `/tmp/writ-smoke-cursor-*` and `/tmp/writ-smoke-claude-*` directories
- [x] **Final verification:** `git status` shows no pending hello-writ artifacts; `git diff main -- skills/` shows nothing; `bash scripts/gen-skill.sh --check` exits 0

## Definition of Done

- [x] All five acceptance scenarios passed
- [x] Cursor and Claude Code sandboxes both installed cleanly with smoke skill present and frontmatter intact
- [x] Three-way overlay preservation verified on real skill (not just synthetic test fixture)
- [x] Smoke skill fully removed: `skills/hello-writ/` deleted, manifest entry removed, root `SKILL.md` regenerated, all sandbox directories deleted
- [x] `git diff main` shows zero hello-writ traces in any committed file
- [x] Story PR description includes evidence of all 5 scenarios (terminal output snippets, file existence checks, cleanup verification)

## Technical Notes

- **Smoke skill content:** Keep it minimal — a 30–40 line SKILL.md with verb-phrase description, brief Purpose, one example "How to Apply" section, no sidecar files. The point is to verify the *plumbing*, not to demonstrate skill authoring.
- **Sandbox lifecycle:** Sandboxes live entirely in `/tmp/`. Use `$(date +%s)` suffix to allow parallel runs without collision. Clean up at story completion regardless of pass/fail.
- **No CI integration:** This story is manually verified. Future specs may add a CI smoke test once the foundation is stable. (Adding it now would risk a `hello-writ` artifact being permanent in CI fixtures.)
- **Pre-merge gate:** This story's PR must not merge until cleanup is verified. A reviewer should check `git diff main` explicitly during review.

## Context for Agents

- **Coding agent context:** spec.md → `## Risks & Mitigations` (smoke skill accidentally committed row) and `## Business Rules → Smoke skill lifecycle`. The smoke SKILL.md content can be terse — verb-phrase description, minimal body. The point is plumbing verification.
- **Review agent context:** spec.md → `## Success Criteria` items 1, 2, 7. Cleanup verification is the highest-impact review check — confirm `git diff main` is empty for hello-writ before approving.
- **Testing agent context:** spec.md → `## Acceptance Criteria` Scenarios 1–5 and spec-lite.md "Test Strategy" Story 3 row. Both Cursor and Claude Code platforms must be exercised.
