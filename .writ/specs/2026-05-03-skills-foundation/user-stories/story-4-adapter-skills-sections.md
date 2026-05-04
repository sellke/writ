# Story 4: Adapter Skills Sections

> **Status:** Completed ✅
> **Priority:** Medium
> **Dependencies:** None
> **Estimated Effort:** Small
> **Completed:** 2026-05-03

## User Story

**As a** Writ user reading a platform adapter to understand how Writ maps to my IDE,
**I want** each adapter (`cursor.md`, `claude-code.md`, `openclaw.md`) to include a parallel-shaped `## Skills` section documenting where skills install, how they load, and how invocation behaves on that platform,
**So that** I can orient on skills as quickly as I orient on commands and agents — without having to cross-reference ADR-009.

## Acceptance Criteria

### Scenario 1: Cursor adapter has Skills section
- **Given** ADR-009 is accepted and `adapters/cursor.md` exists
- **When** I read `adapters/cursor.md`
- **Then** there is a `## Skills` section that documents (a) install path `.cursor/skills/<name>/SKILL.md`, (b) loading mechanism (Cursor's auto-discovery + `disable-model-invocation: true` semantics), (c) explicit-invocation pattern (`Read skills/<name>/SKILL.md`), (d) cross-reference to `.writ/docs/skills.md`

### Scenario 2: Claude Code adapter has Skills section
- **Given** the Cursor adapter has a Skills section
- **When** I read `adapters/claude-code.md`
- **Then** there is a `## Skills` section with the same four subsections (install path `.claude/skills/<name>/SKILL.md`, loading mechanism, explicit-invocation pattern, cross-reference) — parallel-shaped to the Cursor section

### Scenario 3: OpenClaw adapter has Skills section
- **Given** the Cursor and Claude adapters have Skills sections
- **When** I read `adapters/openclaw.md`
- **Then** there is a `## Skills` section with the same four subsections — parallel-shaped, with OpenClaw-specific install path and loading mechanism

### Scenario 4: All three adapters reference the same convention
- **Given** all three adapters have Skills sections
- **When** I diff the section structure across the three files (headers, subsection ordering)
- **Then** the structure is identical; only platform-specific *content* differs

### Scenario 5: Adapters note Writ vs community skill distinction
- **Given** ADR-009's invocation policy table
- **When** I read each adapter's Skills section
- **Then** each adapter explicitly notes that Writ-authored skills use explicit invocation (`disable-model-invocation: true`) while community skills installed by other means follow the platform's default invocation behavior

## Implementation Tasks

- [x] **Section structure design:** Canonical four-subsection template — `### Install Path`, `### Loading Mechanism`, `### Invocation`, `### Authoring & Reference` — applied uniformly to all three adapters.
- [x] **`adapters/cursor.md`:** Added `## Skills` section before "Project Initialization"; documents `.cursor/skills/<name>/SKILL.md` path, Cursor's `<agent_skills>` auto-discovery channel, `disable-model-invocation: true` opt-out, and explicit `Read skills/<name>/SKILL.md` invocation.
- [x] **`adapters/claude-code.md`:** Added parallel-shaped `## Skills` section before "CLI Usage"; documents `.claude/skills/<name>/SKILL.md` path, Claude Code's skill discovery, opt-out, and explicit invocation.
- [x] **`adapters/openclaw.md`:** Added parallel-shaped `## Skills` section before "Workflow Patterns"; documents conceptual `.openclaw/skills/<name>/SKILL.md` path with explicit "install fanout to OpenClaw is blocked on a future adapter spec" note, OpenClaw's session loader semantics, and `Read({ path: ... })` invocation.
- [x] **Cross-references:** All three adapters reference `.writ/docs/skills.md` (Story 7 — forward) and ADR-009 directly via relative links.
- [x] **Required skills note:** All three adapters mention `required_skills:` frontmatter convention with platform-specific harness behavior + forward reference to system-instructions.md (Story 5).
- [x] **Diff verification:** Python regex check confirms all three adapters have identical `Subsection headers: ['Install Path', 'Loading Mechanism', 'Invocation', 'Authoring & Reference']`.

## Definition of Done

- [x] All five acceptance criteria pass (Cursor, Claude Code, OpenClaw all have Skills section; structure identical; Writ vs community distinction noted)
- [x] All three adapter files have `## Skills` sections with identical subsection structure (verified programmatically)
- [x] Cross-references to `.writ/docs/skills.md` and `required_skills:` are present in all three (4 and 2 occurrences each, matched across files)
- [x] Self-review: Section length is 39–41 lines per adapter (within 30–60 budget); only platform-specific *content* differs while structure is identical

## Technical Notes

- **Don't duplicate ADR-009.** Adapters should *reference* the boundary (verb/noun/tool, role convention, `disable-model-invocation`) but not re-derive it. The ADR is the source of truth; adapters explain platform-specific install/loading mechanics.
- **Forward references are OK.** Story 5 (`Required skills:` convention) and Story 7 (`.writ/docs/skills.md`) ship in this same spec. Cross-referencing forward is fine; verify all references resolve at end of Story 7.
- **Section length budget:** Aim for 30–60 lines per Skills section per adapter. Adapters are reference docs, not tutorials — keep it terse.
- **OpenClaw note:** OpenClaw is one of the four ADR-009 target platforms but isn't currently part of `install.sh`'s `--platform` flag. Document the install path conceptually (`.openclaw/skills/`) for ADR consistency; actual install fanout to OpenClaw is out of scope for this spec (it's blocked on a future OpenClaw install adapter, separate concern).

## Context for Agents

- **Coding agent context:** spec.md → `## Implementation Approach → ### Install/Update Fanout` for the install paths. Reference `adapters/cursor.md`, `adapters/claude-code.md`, `adapters/openclaw.md` directly for current section structure and tone.
- **Review agent context:** spec.md → `## Business Rules` for the invocation convention; ADR-009 lines 41–52 for the Writ-authored vs community skill distinction the adapters must echo.
- **Testing agent context:** spec.md → `## Acceptance Criteria` Scenario 4 (parity check across adapters). Manual diff is sufficient.

---

## What Was Built

**Implementation Date:** 2026-05-03

### Files Modified

- **`adapters/cursor.md`** (+39 lines) — Skills section before "Project Initialization"
- **`adapters/claude-code.md`** (+41 lines) — Skills section before "CLI Usage"
- **`adapters/openclaw.md`** (+41 lines) — Skills section before "Workflow Patterns"

### Implementation Decisions

1. **Identical subsection structure across adapters** — `Install Path`, `Loading Mechanism`, `Invocation`, `Authoring & Reference`. Only platform-specific *content* differs. This honors the "parallel-shaped" requirement and gives readers identical scannability across platforms.
2. **OpenClaw conceptual path with explicit deferral note** — `.openclaw/skills/<name>/SKILL.md` is documented for ADR consistency, but the section explicitly notes that install fanout to OpenClaw is "blocked on a future OpenClaw install adapter (separate spec)." This avoids implying a feature that doesn't exist yet while preserving the four-platform conceptual symmetry from ADR-009.
3. **Forward references to `.writ/docs/skills.md` (Story 7) and `system-instructions.md` (Story 5)** — Both are created in this same spec, so the references will resolve at end of Story 7. The "Authoring & Reference" table format makes the forward reference explicit.
4. **Writ-authored vs community skill distinction is in the Loading Mechanism subsection of every adapter** — that's where the `disable-model-invocation: true` decision lives, so it reads in context.

### Test Results

**Verification:** Python regex check on all three adapters

- ✅ All adapters: `Subsection headers: ['Install Path', 'Loading Mechanism', 'Invocation', 'Authoring & Reference']`
- ✅ All adapters: `disable-model-invocation` mentioned (1× each in the Loading Mechanism subsection)
- ✅ All adapters: `required_skills` mentioned (2× each — once in Invocation subsection, once in cross-reference)
- ✅ All adapters: `.writ/docs/skills.md` referenced (4× each — Skills section intro, Loading, Invocation cross-ref, Authoring table)
- ✅ All adapters: ADR-009 referenced (2× each — Skills section intro, Authoring table)
- ✅ Section length: cursor 39, claude-code 41, openclaw 41 (within the 30–60 line budget)

### Review Outcome

**Result:** PASS (self-review)

- **Iteration count:** 1 iteration
- **Drift:** None — structure follows the spec's "parallel-shaped" requirement; ADR-009 boundary references are not duplicated, only cited
- **Security:** N/A (documentation-only changes)
- **Boundary Compliance:** Owned files only (`adapters/cursor.md`, `adapters/claude-code.md`, `adapters/openclaw.md`)

### Deviations from Spec

None.
