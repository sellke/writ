# Skills Foundation (Lite)

> Source: .writ/specs/2026-05-03-skills-foundation/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Add `skills/` as a third primitive (peer to commands/agents) per ADR-009. Foundation infrastructure only — directory, manifest schema, install fanout, adapter docs, `/new-skill` command, `Required skills:` frontmatter convention. Smoke-verified end-to-end with throwaway `hello-writ` skill (deleted before merge). Pilot extraction deferred.

**Implementation Approach:**
- Extend `.writ/manifest.yaml` with `skills:` list (additive; required: name, file, description; optional: tags, aliases)
- Generalize `gen-skill.sh` parsers (yq + bash fallback) to render `## Available Skills` table; preserve `--check` parity
- Add Skills step to `install.sh`/`update.sh` with new `overlay_scan_skills` — overlay tracks SKILL.md hash; sidecars install-once
- `commands/new-skill.md` scaffolder: capture → boundary lint → write
- Boundary lint: description-shape regex on frontmatter; body-shape regex on first 200 chars of paragraphs (skip code blocks)
- `Required skills:` schema documented in `system-instructions.md` + `.writ/docs/skills.md` + 3 adapters; not wired yet

**Files in Scope:**
- New: `skills/` (dir), `skills/hello-writ/SKILL.md` (Story 3 only, deleted in Story 3 final task), `commands/new-skill.md`, `.writ/docs/skills.md`
- Modified: `.writ/manifest.yaml`, `scripts/gen-skill.sh`, `scripts/install.sh`, `scripts/update.sh`, `commands/refresh-command.md`, `adapters/cursor.md`, `adapters/claude-code.md`, `adapters/openclaw.md`, `system-instructions.md`, `cursor/writ.mdc`, `README.md`, `SKILL.md` (regenerated), `AGENTS.md`, `.writ/docs/self-dogfooding.md`

**Error Handling:**
- Missing `skills/` dir in product source → install skips skills step silently
- Empty `skills:` in manifest → `gen-skill.sh` renders no Skills section (not empty section)
- Malformed manifest skill entry → `gen-skill.sh` exits 1 with YAML error + line
- Boundary lint failure on `/new-skill` → reject with offending phrase + remediation, no file written
- Skill copy failure on install → surface in same overlay format as commands/agents

**Integration Points:**
- `gen-skill.sh --check` runs in CI alongside existing checks (Phase 4 pattern)
- `install.sh` skill manifest hashes written to `.cursor/.writ-manifest` parallel to commands/agents
- `/refresh-command` boundary-check section reuses `/new-skill` lint logic

**Line Budget Constraints:** N/A (markdown framework — no compiled code; lint scripts must stay under 300 lines bash)

---

## For Review Agents

**Acceptance Criteria:**
1. `bash scripts/install.sh --dry-run` against sandbox lists `Skills: 1 new` when `skills/hello-writ/SKILL.md` exists; full install places it at `.cursor/skills/hello-writ/SKILL.md` with `disable-model-invocation: true` frontmatter intact
2. `bash scripts/gen-skill.sh --check` exits 0 against manifest with populated `skills:` list; root `SKILL.md` includes `## Available Skills` table
3. `/new-skill foo` scaffolds `skills/foo/SKILL.md`, appends to manifest, and rejects malformed inputs with clear remediation; `/refresh-command` includes equivalent boundary check
4. `Required skills:` convention documented in `system-instructions.md`, `.writ/docs/skills.md`, and all three adapters — zero existing agent/command files modified to declare it yet
5. Hello-writ smoke skill is absent from `skills/` and `.writ/manifest.yaml` at PR merge

**Business Rules:**
- Flat layout: `skills/<name>/SKILL.md`; no category nesting; all Writ skills set `disable-model-invocation: true`
- Skills don't invoke workflows (lint rejects `Read commands/`, `Read skills/`, `/command-name`, `Task(`)
- Descriptions are verb-phrases (lint rejects "Acts as", "Is responsible for", "The X agent", "Run the full", "Execute the entire")
- Manifest schema additive; install fanout mirrors commands/agents three-way overlay
- Skills overlay tracks SKILL.md hash only; sidecar files install-once
- `Required skills:` schema is reserve-only this spec — no agent/command files modified

**Experience Design:**
- Entry: `/new-skill <name>` (contributor) or `bash install.sh` (user)
- Happy path: scaffold → lint pass → manifest append; OR install → `Skills: N new/M updated/K preserved` in summary
- Moment of truth: User opens `.cursor/skills/`, reads one to learn how to do something well — without invoking workflow or assuming role
- Feedback: identical overlay summary format to commands/agents — muscle memory carries
- Error: lint failure shows offending phrase + remediation; install errors share command/agent format

**Drift Analysis Anchors:**
- Pilot skill extraction creep, `Required skills:` wired mid-spec, `adapters/codex.md` request → all out of scope; do not absorb
- Boundary lint relaxation requests → flag medium drift; revisit grammar in ADR-009 review (90 days)

---

## For Testing Agents

**Success Criteria:**
1. `gen-skill.sh --check` clean against committed `SKILL.md` post-Story 1 (with empty `skills:`) and post-Story 7 (final state, empty after smoke skill deletion)
2. Install/update overlay preserves user modifications to `.cursor/skills/<name>/SKILL.md` byte-for-byte (verified via overlay smoke test in Story 2 DoD)
3. `/new-skill` boundary lint catches all 5 description-shape rejection phrases and all 4 body-shape rejection patterns; zero false positives on `hello-writ` smoke skill
4. `/refresh-command` boundary check produces same results as `/new-skill` lint when run against the same input
5. Hello-writ smoke skill workflow: created in Story 3 → installed to `.cursor/skills/hello-writ/SKILL.md` in test sandbox → verified loadable → deleted from `skills/` and manifest in Story 3 final task → verify via `git diff` no smoke skill artifacts remain

**Shadow Paths to Verify:**
- **Happy path:** `/new-skill foo` with verb-phrase description → file scaffolded, manifest entry appended, lint passes
- **Nil input:** `bash install.sh` against project with no `skills/` directory in source → step skipped silently, no errors, commands/agents continue installing normally
- **Empty input:** `bash gen-skill.sh --check` with `skills: []` in manifest → exits 0, `SKILL.md` has no Skills section (not empty section), no validation errors
- **Upstream error:** Malformed `skills:` entry in `.writ/manifest.yaml` (missing `file` field) → `gen-skill.sh` exits 1 with `YAML error: skills[N] missing required field 'file'`

**Edge Cases:**
- Skill name collision with existing command/agent name → `/new-skill` rejects with "name conflicts with existing command/agent"
- User's local `.cursor/skills/<name>/SKILL.md` modified, manifest hash matches baseline → overlay correctly identifies as modified, preserves
- Sidecar file added to `.cursor/skills/<name>/helper.sh` after first install → overlay never overwrites helper.sh on update, even if upstream skill folder changes
- `gen-skill.sh` runs without `yq` installed → bash fallback parser handles `skills:` correctly (Phase 4 parity)
- Boundary lint encounters skill with code block containing rejected phrase ("Run the full pipeline") → does not flag because lint skips code blocks

**Coverage Requirements:**
- Verification = `bash` exit codes + manual smoke tests under each adapter (markdown/bash project — no test framework)
- Critical paths (install fanout, boundary lint regex, overlay preservation): manual sign-off in story DoD
- Self-dogfood validation: each story's PR demonstrates the feature in its own diff

**Test Strategy:**
- Story 1: deliberately edit `SKILL.md` Skills table; verify `--check` fires; revert
- Story 2: install hello-writ skill, modify it locally, run install again; verify three-way overlay preserves modification
- Story 3: full smoke test on Cursor and Claude Code platforms (Cursor primary, Claude Code parity check); verify both load `disable-model-invocation` correctly
- Story 6: feed `/new-skill` 5 description-shape rejection patterns and 4 body-shape rejection patterns; all 9 rejected with remediation; one valid input scaffolds successfully
- Story 7: final `gen-skill.sh --check` and self-dogfood validation across full spec surface
