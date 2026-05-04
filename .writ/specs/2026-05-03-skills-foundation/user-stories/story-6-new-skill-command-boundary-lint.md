# Story 6: `/new-skill` Command + `/refresh-command` Boundary Lint

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** Story 1 (manifest schema)
> **Estimated Effort:** Medium
> **Completed:** 2026-05-03 — All 7 acceptance scenarios verified via 11/11 fixture tests

## User Story

**As a** Writ contributor authoring a new skill,
**I want** a `/new-skill <name>` command that scaffolds a SKILL.md with the role convention, runs a boundary lint at authoring time, and appends the manifest entry — and `/refresh-command` to apply the same lint to existing skills,
**So that** the boundary ADR-009 draws (capability ≠ workflow ≠ role) is enforced by tooling at both author-time and review-time, not just by reviewer discipline.

## Acceptance Criteria

### Scenario 1: Valid skill scaffolds successfully
- **Given** the manifest schema (Story 1) supports skills
- **When** I run `/new-skill conventional-commits` and provide description "Write conventional commit messages from a diff"
- **Then** `skills/conventional-commits/SKILL.md` is created with `disable-model-invocation: true` frontmatter, scaffolded sections (Purpose, When to Use, How to Apply, Examples), and a `skills:` entry is appended to `.writ/manifest.yaml`

### Scenario 2: Workflow-shaped description is rejected
- **Given** I run `/new-skill bad-skill`
- **When** I provide description "Run the full security audit pipeline"
- **Then** the command rejects with `❌ Description starts with "Run the full" — skills describe a capability, not a workflow. Consider rephrasing as a verb-phrase like "Audit ..." or moving this to a /command.` and writes nothing

### Scenario 3: Role-shaped description is rejected
- **Given** I run `/new-skill bad-role`
- **When** I provide description "Acts as a senior reviewer who validates ..."
- **Then** the command rejects with `❌ Description starts with "Acts as" — skills describe a capability, not a role. Consider rephrasing as a verb-phrase like "Validate ..." or moving this to an agent.` and writes nothing

### Scenario 4: Body with workflow invocation is rejected
- **Given** a candidate skill body containing `/security-audit` or `Read commands/foo.md` or `Task(subagent_type: "review-agent")`
- **When** the lint runs (either via `/new-skill` or via `/refresh-command`)
- **Then** the offending pattern is flagged with `❌ Skill body contains "/security-audit" — skills do not invoke commands. Inline the steps or describe the capability.`

### Scenario 5: Code blocks in body are exempt from lint
- **Given** a skill body containing the rejected phrase "Run the full pipeline" inside a fenced code block
- **When** the lint runs
- **Then** the phrase is *not* flagged because the lint scope excludes code blocks

### Scenario 6: `/refresh-command` includes boundary check
- **Given** existing skills in `skills/`
- **When** I run `/refresh-command` and select boundary check
- **Then** the same lint runs against every `skills/*/SKILL.md` and reports per-file violations or "✅ All skills clean"; lint logic is shared with `/new-skill` (no divergence)

### Scenario 7: Skill name collision is caught
- **Given** I run `/new-skill plan-product` (collides with existing command `plan-product`)
- **When** the manifest validation runs
- **Then** the command rejects with `❌ Name "plan-product" conflicts with existing command. Skills must have unique names across commands, agents, and skills.` and writes nothing

## Implementation Tasks

- [x] **Boundary lint script:** Create shared lint logic — either as inline bash in `commands/new-skill.md` and `commands/refresh-command.md`, or as a standalone `scripts/lint-skill.sh`. Decide based on reuse pattern (recommend standalone script for testability)
- [x] **Lint grammar — description:** Implement description-shape rejection regex against the `description:` frontmatter value: `^(Acts as|Is responsible for|The .* agent|Run the full|Execute the entire)`
- [x] **Lint grammar — body:** Implement body-shape rejection patterns: `Read commands/`, `Read skills/`, `\bTask\(`, `^/[a-z-]+` — applied to first 200 chars per paragraph; explicitly skip fenced code blocks
- [x] **Remediation messages:** Each rejection includes a one-line remediation — either a suggested rewrite (when known, e.g. "Rephrase as a verb-phrase like 'Validate ...'") or the generic "Skills describe a capability; rephrase as a verb-phrase about what to do."
- [x] **`/new-skill` command file:** Create `commands/new-skill.md` with three phases (Capture → Lint → Write) and the standard Writ command structure (overview, invocation, process, completion criteria)
- [x] **`/new-skill` capture phase:** Use `AskQuestion` for skill name, category (optional, freeform), tags (optional). Use Plan Mode or freeform prompt for description (verb-phrase guidance shown).
- [x] **`/new-skill` write phase:** Generate scaffolded SKILL.md with frontmatter (`name`, `description`, `disable-model-invocation: true`) and standard sections (Purpose, When to Use, How to Apply, Examples). Append manifest entry.
- [x] **`/new-skill` validation:** Pre-flight check that the skill name is unique across commands, agents, and existing skills (read `.writ/manifest.yaml` and verify)
- [x] **`commands/refresh-command.md` boundary section:** Add a new section (or augment an existing one) that runs the same lint against `skills/*/SKILL.md`; document the invocation pattern parallel to existing checks
- [x] **Manifest update:** `/new-skill` appends a `skills:` entry to `.writ/manifest.yaml` in alphabetical order (within the skills section)
- [x] **Test fixtures:** Create test inputs — 5 description-shape rejection patterns, 4 body-shape rejection patterns, 1 valid skill — and verify all 9 rejections trigger and 1 valid passes
- [x] **Manual verification:** Run `/new-skill` against a throwaway test name; verify all happy-path and rejection scenarios; clean up test artifacts before story completion

## Definition of Done

- [x] All seven acceptance criteria pass via manual testing
- [x] `/new-skill` and `/refresh-command` share lint logic (no divergence — single source of regex grammar)
- [x] Lint rejection messages include offending phrase and remediation
- [x] Code blocks in skill bodies are correctly exempted from body-shape lint
- [x] Test fixtures cover all 9 rejection patterns + 1 happy path
- [x] No throwaway skill artifacts remain after manual verification (clean `git status` for `skills/` and `manifest.yaml`)
- [x] Code reviewed by `review-agent`; testing-agent verifies all rejection patterns trigger correctly

## Technical Notes

- **Standalone script vs inline.** Recommendation: `scripts/lint-skill.sh` so both commands invoke it identically. Bash script with regex grammar; exit codes follow Phase 4 eval pattern (0 = pass, 1 = lint failure, 2 = usage error).
- **Lint scope on body:** First 200 chars per paragraph captures the "headline" sentence where workflow/role language tends to live, while avoiding false positives on detailed examples deeper in the body. Code blocks are excluded entirely.
- **`AskQuestion` for capture:** Use bounded multi-select for tags and category. Description must be free-text (open-ended) — a multi-select would defeat the verb-phrase coaching.
- **Verb-phrase coaching in capture:** Before the description prompt, show a one-line hint: "Skills describe a capability. Start with a verb (Write, Validate, Audit, ...). Avoid 'Acts as', 'Run the full', 'The X agent'."
- **Manifest insertion:** Append in alphabetical order within `skills:` to keep diffs clean. Use awk or sed to insert in-place; verify with `bash scripts/gen-skill.sh --check` after every insertion.
- **`/refresh-command` integration:** The boundary check is a *new sub-feature* of `/refresh-command`. Don't replace existing functionality. Add a new menu option (via `AskQuestion`) for "Run skills boundary lint" or include it in the default checks list.

## Context for Agents

- **Coding agent context:** spec.md → `## Implementation Approach → ### /new-skill Command` and `### Boundary Lint Implementation`. The lint grammar is documented in `## Business Rules`. Reference existing commands (`commands/create-issue.md`, `commands/create-adr.md`) for the Writ command structure and tone.
- **Review agent context:** spec.md → `## Acceptance Criteria` Scenarios 2, 3, 4, 5, 7 (all rejection patterns). Boundary lint must reject everything ADR-009 specifies as out-of-shape; must accept verb-phrase capability descriptions.
- **Testing agent context:** spec.md → `## Risks & Mitigations` (boundary lint false positives row). Test fixture coverage is the critical signal — all 9 rejection patterns must trigger; 1 valid input must pass.
