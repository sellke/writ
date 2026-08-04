# Technical Specification: Plan Mode Command Integrity

> Parent: `.writ/specs/2026-04-08-plan-mode-command-integrity/spec.md`
> Type: Documentation-only (all deliverables are markdown files)

## Architecture Overview

Three layers of enforcement, each reinforcing the others:

```
┌─────────────────────────────────────────────┐
│  Layer 1: system-instructions.md            │
│  Hard Constraint (read every session)       │
│  "Commands own the workflow"                │
├─────────────────────────────────────────────┤
│  Layer 2: Per-Command ## Completion         │
│  9 planning commands × artifact list        │
│  + terminal constraint + next-step pointer  │
├─────────────────────────────────────────────┤
│  Layer 3: Adapter Reinforcement             │
│  3 adapters × platform-specific guidance    │
│  Names tendency + provides countermeasure   │
└─────────────────────────────────────────────┘
```

## Layer 1: System Instructions Change

### Location

`system-instructions.md` → `## Prime Directive` → `### Hard Constraints`

Currently contains 3 constraints (anti-reversal, anti-confirmation, anti-filler). Add a 4th:

### Proposed Constraint Text

```markdown
- **Never let Plan Mode absorb a command's workflow.** When a command uses
  Plan Mode for discovery, the conversation is a phase — not the deliverable.
  After discovery, resume the command's documented phases and produce its
  documented artifacts. Planning commands create files and stop. They never
  offer to implement, build, or code. If the user wants fast implementation,
  point them to `/prototype`.
```

### Sync Targets

| Source File | Sync Target | Mechanism |
|---|---|---|
| `system-instructions.md` | `cursor/writ.mdc` | Manual parallel edit (separate files with matching content) |
| `cursor/writ.mdc` | `.cursor/rules/writ.mdc` | Automatic (symlink) |

**Verified:** `.cursor/rules/writ.mdc` → symlink to `../../cursor/writ.mdc`. The `cursor/writ.mdc` file is a regular file (not a symlink to `system-instructions.md`), so it requires a parallel edit.

## Layer 2: Per-Command Completion Sections

### Template

```markdown
## Completion

This command succeeds when:

1. **[Primary artifact]** — [specific file(s) exist with required content]
2. **[Secondary artifacts]** — [additional files if applicable]
3. **Summary presented** — the user received a completion summary

**Suggested next step:** `[downstream command]` [brief context]

**Terminal constraint:** This command produces [artifact type]. Do not offer to implement, build, or execute what was planned. For implementation, the user should run `[downstream command]`. For quick prototyping, use `/prototype`.
```

### Per-Command Specifications

#### `/create-spec` (has existing Completion section)

**Action:** Update existing section. Add terminal constraint and next-step pointer. Existing criteria (contract locked, spec package exists, stories actionable, sub-specs generated, package reviewed) are retained.

**Append:**
```markdown
**Suggested next step:** `/implement-spec` to execute the full pipeline, or `/implement-story` for individual stories.

**Terminal constraint:** This command produces specification artifacts. Do not offer to implement, build, or code the spec. For implementation, the user should run `/implement-spec` or `/implement-story`. For quick prototyping, use `/prototype`.
```

#### `/plan-product` (missing Completion section)

**Artifacts:** Product vision doc, roadmap, strategy documents in `.writ/product/`
**Next step:** `/create-spec` to spec individual features from the roadmap

#### `/new-command` (missing Completion section)

**Artifacts:** Command `.md` file in `commands/`
**Next step:** Test the new command by invoking it

#### `/create-issue` (missing Completion section)

**Artifacts:** Issue `.md` file in `.writ/issues/{type}/`
**Next step:** `/create-spec --from-issue` to promote to a specification

#### `/create-adr` (missing Completion section)

**Artifacts:** ADR `.md` file in `.writ/decision-records/`
**Next step:** Reference the ADR from relevant specs or stories

#### `/create-uat-plan` (missing Completion section)

**Artifacts:** UAT plan `.md` file
**Next step:** Execute the UAT plan manually or with test tooling

#### `/research` (missing Completion section)

**Artifacts:** Research `.md` file in `.writ/research/`
**Next step:** `/create-spec` or `/create-adr` informed by the research

#### `/design` (check existing Completion section)

**Artifacts:** Design artifacts (mockups, wireframes, component inventory)
**Next step:** `/create-spec` to formalize into a spec, or `/implement-story` if spec exists

#### `/edit-spec` (check existing Completion section)

**Artifacts:** Updated spec files (spec.md, spec-lite.md, stories)
**Next step:** `/implement-spec` or `/implement-story` to continue implementation

## Layer 3: Adapter Reinforcement

### Section Title

`## Command Workflow Integrity`

### Cursor Adapter (`adapters/cursor.md`)

**Platform tendency:** Cursor's Plan Mode is a distinct interaction mode. When a command switches to Plan Mode for discovery, the mode can become the agent's identity — the agent stays in planning mode and treats the conversation as the final output. Alternatively, it switches back to Agent Mode and immediately offers to "build" the planned artifacts.

**Countermeasure:**
```markdown
## Command Workflow Integrity

When a Writ command uses Plan Mode for discovery (e.g., `/create-spec` Phase 1, `/plan-product` discovery), Plan Mode serves as a phase within the command — not a replacement for it.

**Rule:** After Plan Mode discovery completes, the command must resume its documented phases in Agent Mode and produce its documented artifacts (spec files, stories, ADRs, etc.). The conversation is an intermediate step, not the deliverable.

**Common failure:** The agent stays in Plan Mode and treats the planning conversation as the command's output, or switches to Agent Mode and offers to implement/build. Neither is correct — the command's next phase is artifact creation, not implementation.

**Reference:** System instructions → Prime Directive → Hard Constraints → "Never let Plan Mode absorb a command's workflow."
```

### Claude Code Adapter (`adapters/claude-code.md`)

**Platform tendency:** After a planning conversation completes and artifacts are written, the main session naturally offers to spawn implementation subagents. Claude Code's `permissionMode: plan` prevents writes during discovery, but nothing prevents the session from pivoting to implementation after artifact creation.

**Countermeasure:** Similar structure — reference system instructions, name the tendency, provide the rule.

### OpenClaw Adapter (`adapters/openclaw.md`)

**Platform tendency:** Session continuation bias. After artifact creation, the session continues toward "what's next?" which slides into offering implementation.

**Countermeasure:** Similar structure.

## Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| AI platforms ignore the constraint language | Medium | High | Three-layer reinforcement (system + command + adapter) increases compliance |
| Over-constraining makes Writ feel rigid | Low | Medium | `/prototype` escape valve clearly signposted |
| `cursor/writ.mdc` falls out of sync with `system-instructions.md` | Medium | Medium | Story 1 handles both files; future edits must maintain sync |
| New commands added without Completion sections | Medium | Low | Template established; `/new-command` could enforce this |
