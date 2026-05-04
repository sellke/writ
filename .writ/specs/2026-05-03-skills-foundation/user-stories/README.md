# Skills Foundation — User Stories

> **Spec:** `.writ/specs/2026-05-03-skills-foundation/spec.md`
> **ADR:** `.writ/decision-records/adr-009-command-agent-skill-boundary.md`
> **Status:** Complete
> **Total Stories:** 7

## Overview

This spec adds the `skills/` primitive to Writ as a peer to `commands/` and `agents/` per ADR-009. Foundation infrastructure only — no production skills extracted in this spec. Pilot extraction (`tdd-cycle`, `conventional-commits`, `adr-writing`) is deferred to follow-up specs per ADR-009's "pilot proves integration before broader extraction" sequencing.

## Stories Summary

| # | Story | Status | Tasks | Priority | Dependencies |
|---|---|---|---|---|---|
| 1 | [Manifest Schema and Skills Table Generation](story-1-manifest-schema-skill-table.md) | Complete ✅ | 13/13 | High | None |
| 2 | [Install and Update Scripts Skills Fanout](story-2-install-update-skills-fanout.md) | Complete ✅ | 16/16 | High | None |
| 3 | [Hello-Writ Smoke Verification](story-3-hello-writ-smoke-verification.md) | Complete ✅ | 18/18 | High | Story 1, Story 2 |
| 4 | [Adapter Skills Sections](story-4-adapter-skills-sections.md) | Complete ✅ | 11/11 | Medium | None |
| 5 | [Required Skills Frontmatter Convention](story-5-required-skills-frontmatter-convention.md) | Complete ✅ | 13/13 | Medium | None |
| 6 | [`/new-skill` Command + Boundary Lint](story-6-new-skill-command-boundary-lint.md) | Complete ✅ | 19/19 | High | Story 1 |
| 7 | [Documentation Pass](story-7-documentation-pass.md) | Complete ✅ | 15/16 | Medium | Stories 1, 2, 4, 5, 6 |

**Progress:** 105/106 tasks complete. The single unchecked item is Story 7 DoD-6 (separate `review-agent` and `documentation-agent` passes), intentionally skipped under the single-agent serial execution model — documentation work was self-reviewed during the cross-reference audit. All other acceptance criteria, success criteria, and DoD items are verified.

## Dependency Graph

```
Story 1 (manifest schema) ──┬─→ Story 3 (smoke verification) ──┐
                            │                                   │
Story 2 (install fanout) ───┘                                   │
                                                                ▼
Story 1 ───────────────────→ Story 6 (/new-skill + lint) ──────┐│
                                                                ││
Story 4 (adapters) ────────────────────────────────────────────┐││
                                                               │││
Story 5 (required_skills convention) ──────────────────────────┴┴┴─→ Story 7 (docs)
```

**Parallel batches:**

- **Batch A (no deps):** Stories 1, 2, 4, 5 — can run concurrently.
- **Batch B (deps on Batch A):** Stories 3 (gates on 1+2), 6 (gates on 1).
- **Batch C (synthesis):** Story 7 — gates on 1, 2, 4, 5, 6.

## Story Descriptions

### Story 1 — Manifest Schema and Skills Table Generation
Extend `.writ/manifest.yaml` with an additive `skills:` section. Update `scripts/gen-skill.sh` (both `yq` and `parse_with_bash` branches) to validate skill entries and render a `## Available Skills` table in the root `SKILL.md`. Preserve `--check` mode parity for drift detection.

### Story 2 — Install and Update Scripts Skills Fanout
Add a Skills step to `scripts/install.sh` and `scripts/update.sh` with a new `overlay_scan_skills` function. Three-way overlay tracks SKILL.md hashes only; sidecar files inside skill folders install-once. Manifest writeback covers skill paths. Symlink-mode and force-reset paths handle skills consistently with commands and agents.

### Story 3 — Hello-Writ Smoke Verification
End-to-end integration test: author throwaway `skills/hello-writ/SKILL.md` with `disable-model-invocation: true` frontmatter, install into Cursor and Claude Code sandbox projects, verify the skill lands at platform-native paths with frontmatter intact, verify three-way overlay preserves local edits, then **delete the smoke skill and its manifest entry** before merge. The foundation ships clean.

### Story 4 — Adapter Skills Sections
Add a parallel-shaped `## Skills` section to `adapters/cursor.md`, `adapters/claude-code.md`, and `adapters/openclaw.md`. Each section documents install path, loading mechanism, explicit-vs-auto invocation behavior, and `Required skills:` convention reference. Section structure is identical across all three; only platform-specific *content* differs.

### Story 5 — Required Skills Frontmatter Convention
Define and document the `required_skills:` frontmatter convention for agents and commands. Schema is reserve-only this spec — documented in `system-instructions.md`, `cursor/writ.mdc`, `.writ/docs/skills.md`, and all three adapters; zero existing agent/command files are modified to declare it. 90-day review trigger (2026-08-03) ensures it doesn't bitrot.

### Story 6 — `/new-skill` Command + `/refresh-command` Boundary Lint
Author-time scaffolder for new skills with a boundary lint enforcing the role convention from ADR-009. Description-shape rejection regex catches workflow ("Run the full"), role ("Acts as"), and agent ("The X agent") shapes; body-shape rejection catches `Read commands/`, `Read skills/`, `Task(`, and `/command-name` invocations. Code blocks in skill bodies are exempt from lint. `/refresh-command` reuses the same lint via shared `scripts/lint-skill.sh`.

### Story 7 — Documentation Pass
Final synthesis story. Creates `.writ/docs/skills.md` (canonical user-facing explainer with verb/noun/tool framing). Updates `README.md`, `AGENTS.md` (Repository Structure table), and `.writ/docs/self-dogfooding.md` with skills coverage. Regenerates root `SKILL.md` against the final empty-skills state. Creates `.cursor/skills` symlink to `../skills` for self-dogfooding parity. Cross-reference audit confirms every link resolves.

## What's Out of Scope

Explicitly *not* in this spec — reserved for follow-up specs:

- **Pilot skill extraction** — `tdd-cycle`, `conventional-commits`, `adr-writing` each get their own follow-up spec
- **`adapters/codex.md`** — first-class Codex platform adapter is separate work
- **Wiring `required_skills:` into existing agents/commands** — happens organically as pilot skills are extracted
- **Skill discovery UI / CLI search**
- **Community skill installation flow** (e.g., `clawhub`, `agentskills.io` ingestion)

## How to Run This Spec

Recommended invocation:

```bash
/implement-spec .writ/specs/2026-05-03-skills-foundation/
```

`/implement-spec` will batch the parallel stories (Batch A: 1, 2, 4, 5), then unblock Batch B (3, 6), then run Story 7. Story 3 and Story 6 will gate on their respective dependencies before starting.

## Quick Links

- [Spec (full)](../spec.md)
- [Spec (lite)](../spec-lite.md)
- [Technical sub-spec](../sub-specs/technical-spec.md)
- [ADR-009](../../decision-records/adr-009-command-agent-skill-boundary.md)
