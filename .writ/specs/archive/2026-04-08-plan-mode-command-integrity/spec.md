# Plan Mode Command Integrity

> Status: Complete
> Contract Locked: ✅
> Origin: Promoted from issue: `.writ/issues/improvements/2026-04-08-plan-mode-implementation-boundary.md`

## Contract Summary

**Deliverable:** Ensure planning commands retain control of their documented workflow when Plan Mode is used — Plan Mode serves as a discovery phase *within* the command, not a substitute for the command's artifact creation phases. The command's documented markdown deliverables (spec.md, stories, ADRs, etc.) must always be produced.

**Must Include:** A hard constraint in `system-instructions.md` establishing that commands own the workflow and Plan Mode is a tool within commands, not a replacement for them.

**Hardest Constraint:** The AI platform's Plan Mode is a black box we don't control — we can only influence behavior through instruction-level language. The fix has to be strong enough that the platform treats Plan Mode as step 2 of N, not as the entire command.

**Success Criteria:**
- System instructions contain a hard constraint that commands own the workflow and Plan Mode is a phase, not a replacement
- All 9 planning commands have `## Completion` sections naming their required deliverable artifacts
- Commands that use Plan Mode have explicit phase transition language ("after discovery, return to Agent Mode for artifact creation")
- All 3 adapters explain the platform's tendency and countermeasure
- `/prototype` is referenced as the legitimate path for users who want fast implementation without full artifact creation

**Scope Boundaries:**
- Included: System instructions, 9 planning commands, 3 adapters
- Excluded: Implementation commands (`/implement-story`, `/implement-spec`, `/prototype`), agent definitions, ADR-001 (already correct in principle)

---

## 🎯 Experience Design

### The Problem (User Journey Today)

1. Developer invokes `/create-spec "user authentication"`
2. Command switches to Plan Mode for discovery conversation
3. AI platform's Plan Mode takes over — it conducts a planning conversation, potentially offers to "start building," or treats the conversation itself as the deliverable
4. The command's Phase 2 (artifact creation — spec.md, user stories, sub-specs) is partially or fully skipped
5. Developer gets a conversation but not the documented spec package the command promised

### The Fix (User Journey After)

1. Developer invokes `/create-spec "user authentication"`
2. Command uses Plan Mode for discovery conversation (Phase 1)
3. Discovery completes → command explicitly transitions back to Agent Mode
4. Phase 2 executes: spec.md, spec-lite.md, user stories, sub-specs are all created
5. Command presents the complete package and terminates with next-step guidance pointing to `/implement-spec`
6. AI does not offer to implement, build, or code — the command is done

### State Catalog

| State | What the User Sees |
|---|---|
| **Discovery (Plan Mode)** | Conversational back-and-forth shaping the spec/plan/command |
| **Transition** | Explicit signal: "Discovery complete. Creating artifacts..." |
| **Artifact Creation (Agent Mode)** | Files being written, progress tracking, no more open-ended conversation |
| **Completion** | Final summary with file tree, artifact counts, and next-step pointer |
| **Error: Plan Mode absorption** | What we're fixing — conversation treated as the deliverable, artifacts never created |

---

## 📋 Business Rules

### Hard Constraint (for system-instructions.md)

**Commands own the workflow. Plan Mode is a phase, not a replacement.**

- When a command uses Plan Mode for discovery, Plan Mode serves the command — it does not become the command.
- After discovery completes, the command resumes its documented phases and produces its documented artifacts.
- Conversation is not a deliverable. Markdown files are.
- Planning commands terminate with their artifacts and a next-step suggestion. They never offer to implement, build, or code.
- Users who want fast implementation without the full artifact pipeline should use `/prototype`.

### Per-Command Rules

Every planning command must have a `## Completion` section that:
1. Names the specific artifacts the command must produce (file paths or patterns)
2. States that the command terminates after artifact creation
3. Provides a next-step suggestion pointing to the appropriate downstream command
4. Includes a terminal constraint: "Do not offer to implement, build, or code the artifacts produced by this command"

### Affected Commands (9 total)

| Command | Uses Plan Mode | Required Artifacts | Natural Next Step |
|---|---|---|---|
| `/create-spec` | Yes (Phase 1.2-1.3) | spec.md, spec-lite.md, user stories, sub-specs | `/implement-spec` or `/implement-story` |
| `/plan-product` | Yes | product vision, roadmap, strategy docs | `/create-spec` for individual features |
| `/new-command` | Yes (Step 1.2-1.3) | command .md file in `commands/` | Manual testing of the new command |
| `/create-issue` | No | Issue .md file in `.writ/issues/` | `/create-spec --from-issue` |
| `/create-adr` | Depends | ADR .md file in `.writ/decision-records/` | Reference from specs/stories |
| `/create-uat-plan` | Depends | UAT plan .md file | Manual UAT execution |
| `/research` | Depends | Research .md file in `.writ/research/` | `/create-spec` or `/create-adr` |
| `/design` | Yes | Design artifacts in `.writ/docs/` or spec mockups | `/create-spec` or `/implement-story` |
| `/edit-spec` | Depends | Updated spec files | `/implement-spec` or `/implement-story` |

### Adapter-Specific Tendencies

| Platform | Tendency | Countermeasure |
|---|---|---|
| **Cursor** | Plan Mode becomes the agent's identity — it stays in planning mode and treats the conversation as the output, or switches to Agent Mode and offers to "build it" | Explicit instruction: Plan Mode is a phase within commands. After discovery, return to Agent Mode for artifact creation, not implementation. |
| **Claude Code** | Subagent system treats planning as a complete task. After the planning conversation, the main session offers to spawn implementation agents. | Explicit instruction: Planning commands produce files and stop. Do not spawn implementation subagents after planning commands complete. |
| **OpenClaw** | Session continuation bias — after producing artifacts, the session naturally continues toward "what's next?" which slides into implementation. | Explicit instruction: Planning commands terminate after artifact creation. Suggest next command, do not execute it. |

---

## Implementation Approach

### Layer 1: System Instructions (Root Constraint)

Add a new Hard Constraint to `system-instructions.md` > Prime Directive > Hard Constraints section. This is the root behavioral contract read by every session on every platform.

The constraint should be concise (3-5 lines) and absolute — same tone as the existing anti-sycophancy rules. It establishes the principle; per-command sections and adapters provide the detail.

### Layer 2: Per-Command Completion Sections

For each of the 9 planning commands:
- Commands that already have `## Completion` sections: update to include artifact requirements and terminal constraint
- Commands missing `## Completion` sections: add them with the standard format

The completion section template:

```markdown
## Completion

This command succeeds when:

1. [Artifact 1 exists and contains required content]
2. [Artifact 2 exists and contains required content]
3. [Final summary was presented to the user]

**Next step:** [Downstream command suggestion]

**Terminal constraint:** This command produces [artifact type], not code. Do not offer to implement, build, or execute the [artifacts] produced. Users who want implementation should run [downstream command]. Users who want quick prototyping should use `/prototype`.
```

### Layer 3: Adapter Reinforcement

Add a new section to each adapter (Cursor, Claude Code, OpenClaw) titled "Command Workflow Integrity" that:
1. Names the platform-specific tendency
2. Provides the countermeasure instruction
3. References the system-instructions hard constraint as the authority

### Sync Requirement

`system-instructions.md` is the product source. The Cursor rules file (`cursor/writ.mdc`) mirrors it via the symlink chain (`.cursor/rules/writ.mdc` → `cursor/writ.mdc` → content matches `system-instructions.md`). Verify whether the symlink handles the sync automatically or if `cursor/writ.mdc` needs a parallel edit.

---

## Technical Notes

- This is a documentation-only spec — all deliverables are markdown files. No application code, no tests, no build step.
- The fix is instruction-level, not enforcement-level. We can't programmatically prevent Plan Mode from absorbing a command. We can only make the instructions clear enough that the AI follows them.
- The existing ADR-001 (AskQuestion vs Plan Mode) already establishes the philosophical principle. This spec adds the enforcement language that ADR-001 assumed would be self-evident.
- Risk: over-constraining could make Writ feel rigid when users genuinely want speed. The `/prototype` escape valve must be clearly signposted to prevent this.
