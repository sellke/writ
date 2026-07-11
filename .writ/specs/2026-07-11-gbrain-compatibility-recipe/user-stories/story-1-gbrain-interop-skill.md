# Story 1: `gbrain-interop` Skill + Registration

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As an** agent retrieving prior knowledge on a project that may or may not run GBrain
**I want** a capability that detects a brain, prefers brain-first retrieval when one is present, and falls back to grep when it is absent
**So that** semantic recall improves when a brain exists without ever making GBrain a dependency or moving canonical data off markdown

## Acceptance Criteria

- [ ] Given `skills/gbrain-interop/SKILL.md`, when it is linted with `scripts/lint-skill.sh`, then it passes the role convention and lifecycle checks, carries `disable-model-invocation: true`, and declares `status: candidate` with a `## Evidence` section (0 entries valid).
- [ ] Given the skill body, when an agent reads it, then it specifies detection via `gbrain doctor --json` status (not a bare PATH probe), brain-first retrieval via `gbrain search` / MCP `mcp__gbrain__search` when detected, citing the canonical markdown path in results, markdown-first writes (edit `.writ/`, then `gbrain sync`), and grep fallback when absent or unhealthy.
- [ ] Given the skill body, when reviewed against the contract, then it never instructs writing durable knowledge only into GBrain and states that it changes retrieval routing, not the canonical store.
- [ ] Given `.writ/manifest.yaml`, when the `gbrain-interop` entry is added, then it has `name`, `file`, a verb-phrase `description`, `status: candidate`, and `tags`, placed in the `skills:` list.
- [ ] Given `scripts/gen-skill.sh` runs, when the root `SKILL.md` is regenerated, then `gbrain-interop` appears in the catalog and a second run produces no diff (`git diff --exit-code SKILL.md`).

## Implementation Tasks

- [ ] 1.1 Author `skills/gbrain-interop/SKILL.md` with role-convention frontmatter (`description:` verb phrase, `disable-model-invocation: true`, `status: candidate`) and body sections: Detect, Route (brain-first), Cite (markdown path), Write (markdown-first), Degrade (graceful absence).
- [ ] 1.2 Add a `## Evidence` lifecycle section (empty is valid for a candidate) per ADR-014.
- [ ] 1.3 Register `gbrain-interop` in the `skills:` list of `.writ/manifest.yaml` with `status: candidate` and appropriate tags (e.g., `[memory, retrieval, interop]`).
- [ ] 1.4 Run `bash scripts/gen-skill.sh` to regenerate root `SKILL.md`; verify idempotence with a second run and `git diff --exit-code`.
- [ ] 1.5 Run `bash scripts/lint-skill.sh skills/gbrain-interop/SKILL.md` and fix any findings.

## Notes

- Keep the skill routing-focused and short; setup mechanics belong in Story 2's recipe doc (ADR-009 boundary).
- Detection semantics: `ok`/`warnings` = present; `error` or missing = absent → grep.
- Model frontmatter on `skills/conventional-commits/SKILL.md` and `skills/tdd-cycle/SKILL.md`.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `scripts/lint-skill.sh` clean; `gen-skill.sh` idempotent
- [ ] Code reviewed

## Context for Agents

- **Business rules:** [`spec.md` → `### Business Rules` → Rules 3 (observable detection), 4 (brain-first only when detected), 6 (markdown-first writes), 9 (skill boundary)]
- **Design:** [`sub-specs/technical-spec.md` → `### D1`, `### D2`, `### D3`]
- **Grounding:** [`spec.md` → `## Implementation Approach` → "Grounding in GBrain's real interface"]
