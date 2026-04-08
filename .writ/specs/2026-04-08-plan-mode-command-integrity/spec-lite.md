# Plan Mode Command Integrity (Lite)

> Source: .writ/specs/2026-04-08-plan-mode-command-integrity/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Enforce that Writ planning commands own their workflow — Plan Mode is a discovery phase within commands, not a substitute for artifact creation.

**Implementation Approach:**
- Layer 1: Add Hard Constraint to `system-instructions.md` Prime Directive section (3-5 lines, absolute)
- Layer 2: Add/update `## Completion` sections in 9 planning commands with required artifacts and terminal constraint
- Layer 3: Add "Command Workflow Integrity" sections to 3 adapters with platform-specific countermeasures
- Verify `cursor/writ.mdc` sync with `system-instructions.md` (symlink or parallel edit)

**Files in Scope:**
- `system-instructions.md` — new Hard Constraint in Prime Directive
- `commands/{create-spec,plan-product,new-command,create-issue,create-adr,create-uat-plan,research,design,edit-spec}.md` — Completion sections
- `adapters/{cursor,claude-code,openclaw}.md` — Command Workflow Integrity sections

**Error Handling:**
- Missing `## Completion` section → create from template (see spec.md → Implementation Approach → Layer 2)
- Existing `## Completion` section → append terminal constraint, don't overwrite existing criteria

**Integration Points:**
- `cursor/writ.mdc` must stay in sync with `system-instructions.md`
- ADR-001 establishes the principle; this spec adds enforcement language

---

## For Review Agents

**Acceptance Criteria:**
1. `system-instructions.md` Hard Constraints section contains planning/implementation boundary rule
2. All 9 planning commands have `## Completion` sections with artifact requirements and terminal constraint
3. All 3 adapters have "Command Workflow Integrity" sections with platform-specific guidance
4. `/prototype` is referenced as escape valve in system instructions and per-command terminal constraints

**Business Rules:**
- Commands own the workflow; Plan Mode is a phase, not a replacement
- Conversation is not a deliverable; markdown files are
- Planning commands terminate with artifacts + next-step suggestion, never offer implementation
- Terminal constraint must name the downstream command (`/implement-spec`, `/create-spec`, etc.)

**Experience Design:**
- Entry: Any planning command invocation
- Happy path: Discovery → transition → artifact creation → completion with next-step
- Moment of truth: Command produces its documented artifacts instead of stopping at conversation
- Feedback: Final summary with file tree and next-step pointer
- Error: Plan Mode absorbs the command; artifacts never created

---

## For Testing Agents

**Success Criteria:**
1. All 13 files modified (1 system-instructions + 9 commands + 3 adapters)
2. Every `## Completion` section names specific artifact files/patterns
3. Every terminal constraint references `/prototype` as escape valve

**Edge Cases:**
- Command already has `## Completion` → extend, don't replace
- Command doesn't use Plan Mode → still needs Completion section with artifacts
- `cursor/writ.mdc` symlink → verify sync, don't create duplicate content

**Coverage Requirements:**
- All 9 planning commands verified for Completion section
- All 3 adapters verified for Command Workflow Integrity section
- System instructions verified for Hard Constraint

**Test Strategy:**
- Manual review: read each modified file and verify constraint language exists
- Cross-reference: each command's Completion section names artifacts consistent with command's documented phases
