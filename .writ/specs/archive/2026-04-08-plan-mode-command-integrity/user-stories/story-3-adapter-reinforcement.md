# Story 3: Adapter Reinforcement

> **Status:** Not Started  
> **Priority:** Medium  
> **Dependencies:** Story 1

## User Story

**As a** Writ developer (AI system running on Cursor, Claude Code, or OpenClaw)  
**I want to** have platform-specific guidance preventing Plan Mode from absorbing command workflows  
**So that** the command workflow integrity principle is reinforced where each platform is most likely to violate it

## Acceptance Criteria

- [ ] **Given** `adapters/cursor.md`, `adapters/claude-code.md`, and `adapters/openclaw.md`, **when** each file is searched for a top-level section titled exactly `## Command Workflow Integrity`, **then** the section exists in all three files.
- [ ] **Given** each adapter’s `## Command Workflow Integrity` section, **when** the content is read, **then** it explicitly names that platform’s tendency (Cursor: Plan Mode as identity / conversation-as-output or premature “build”; Claude Code: post-planning pivot to spawning implementation subagents; OpenClaw: session continuation sliding from artifacts into implementation).
- [ ] **Given** each adapter’s `## Command Workflow Integrity` section, **when** checked for authority linkage, **then** it references the system-instructions hard constraint under Prime Directive → Hard Constraints (same substance as Story 1; wording may cite the constraint’s intent, e.g. Plan Mode must not absorb the command’s workflow).
- [ ] **Given** each adapter’s section, **when** compared to generic prose only, **then** countermeasure instructions use that platform’s terminology and concepts (e.g. Plan Mode vs Agent Mode and Task/AskQuestion on Cursor; subagents and session flow on Claude Code; OpenClaw session continuation and mapped tool equivalents where relevant).
- [ ] **Given** `adapters/claude-code.md` after edits, **when** Gotcha #6 (plan mode read-only) is still present, **then** the new section complements it without removing or contradicting it — workflow integrity covers command ownership end-to-end; the gotcha remains the write-barrier detail for plan sessions.

## Implementation Tasks

1. Read `adapters/cursor.md`, `adapters/claude-code.md`, and `adapters/openclaw.md` end-to-end; note existing headings (Workflow Patterns, Gotchas, tool mapping, etc.) and choose a natural insertion point per file for `## Command Workflow Integrity`.
2. Add `## Command Workflow Integrity` to `adapters/cursor.md`: state the rule (discovery phase → resume command phases → create documented artifacts), name the Cursor-specific failure modes, reference `system-instructions.md` Prime Directive → Hard Constraints as authority.
3. Add `## Command Workflow Integrity` to `adapters/claude-code.md`: same structural elements, tuned for subagent/session behavior and post-planning implementation offers; place near workflow or Gotchas without duplicating Gotcha #6’s read-only focus.
4. Add `## Command Workflow Integrity` to `adapters/openclaw.md`: same structural elements, tuned for session continuation bias and “what’s next” drift into implementation; align vocabulary with how OpenClaw maps Cursor concepts elsewhere in the file.
5. Cross-check all three sections: tendency named, rule and countermeasure clear, system-instructions hard constraint referenced, `/prototype` or downstream commands only where the adapter already discusses command routing (do not contradict Story 2’s per-command Completion language).
6. Verify Story 1 is satisfied before merge: `system-instructions.md` (and synced `cursor/writ.mdc` per Story 1) contains the fourth Hard Constraint so adapter references resolve to real text.
7. Final pass: grep `adapters/*.md` for `Command Workflow Integrity`; confirm three hits (one section per adapter), headings consistent, and no accidental edits outside these adapter files.

## Notes

- Each adapter has a different structure — place the new section where it fits naturally (e.g. after setup, before or within workflow guidance, or adjacent to Gotchas on Claude Code).
- Claude Code’s Gotcha #6 (“plan mode is truly read-only”) stays; the new section addresses command ownership and post-discovery / post-artifact behavior, not file writes during plan sessions.
- Countermeasure language should be adapted per platform; avoid pasting identical paragraphs into all three files if a short shared rule plus platform-specific “Common failure” text is clearer.

## Definition of Done

- [ ] All acceptance criteria checked.
- [ ] All implementation tasks completed.
- [ ] Only intended product files changed (`adapters/cursor.md`, `adapters/claude-code.md`, `adapters/openclaw.md`) unless a typo fix elsewhere is explicitly scoped.
- [ ] Story 1 dependency verified: hard constraint exists in `system-instructions.md` so adapter references are accurate.
- [ ] Story status updated to Complete when merged or accepted.

## Context for Agents

Use these hints to load the right spec slices without pasting the full spec into every turn.

| Hint | Path / anchor |
|------|----------------|
| Adapter tendency table (platform, tendency, countermeasure) | `.writ/specs/2026-04-08-plan-mode-command-integrity/spec.md` → `## 📋 Business Rules` → `### Adapter-Specific Tendencies` |
| Layer 3 requirements (section title, three bullets) | `.writ/specs/2026-04-08-plan-mode-command-integrity/spec.md` → `## Implementation Approach` → `### Layer 3: Adapter Reinforcement` |
| Section title and Cursor countermeasure markdown | `.writ/specs/2026-04-08-plan-mode-command-integrity/sub-specs/technical-spec.md` → `## Layer 3: Adapter Reinforcement` → `### Section Title`, `### Cursor Adapter` |
| Claude Code / OpenClaw tendency notes | `.writ/specs/2026-04-08-plan-mode-command-integrity/sub-specs/technical-spec.md` → `### Claude Code Adapter`, `### OpenClaw Adapter` |
| Root hard constraint (authority for “Reference:” lines) | `.writ/specs/2026-04-08-plan-mode-command-integrity/spec.md` → `### Hard Constraint (for system-instructions.md)`; implement Story 1: `system-instructions.md` → `## Prime Directive` → `### Hard Constraints` |
| Contract summary and success criteria (adapters bullet) | `.writ/specs/2026-04-08-plan-mode-command-integrity/spec.md` → `## Contract Summary` |

**Format reference:** `.writ/docs/context-hint-format.md`

**Files in scope (this story):** `adapters/cursor.md`, `adapters/claude-code.md`, `adapters/openclaw.md`

**Dependency:** Complete Story 1 first so adapter references to the Hard Constraints block are valid.
