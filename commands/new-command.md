# New Command Creator (new-command)

## Overview

Create new Writ commands through a contract-first approach. No files are created until the developer and AI agree on a command specification through collaborative discovery. This command generates properly structured command files that integrate with the Writ ecosystem.

**When to use** — creating a genuinely new command for the Writ system. Before building, this command challenges whether the proposed command is needed, surfaces overlap with existing commands, and ensures the design fits Writ's patterns.

## Invocation

| Invocation | Behavior |
|---|---|
| `/new-command` | Interactive — describe the command idea |
| `/new-command "audit-deps"` | Start with command concept pre-loaded |

## Command Process

### Phase 1: Command Contract Establishment (No File Creation)

**Mission Statement:**

> Your goal is to turn my rough command idea into a comprehensive command specification. You will deliver the complete command package only after we both agree on the command contract. **Important: Challenge command ideas that don't fit the Writ ecosystem or would create maintenance burden — it's better to surface concerns early than build the wrong command.**

#### Step 1.1: Initial Context Scan

- Scan existing commands in `commands/` to understand patterns and spot potential overlap
- Analyze the Writ ecosystem structure — command categories, execution styles, integration points
- Load successful commands as references (contract-style: `create-spec`; direct: `refactor`; setup: `initialize`)
- Output: context summary (no files created yet)

#### Step 1.2: Switch to Plan Mode for Command Discovery

After the context scan, switch to Plan Mode. Designing a new command is an open-ended conversation — understanding the workflow it serves, how it fits with existing commands, what patterns to follow, where simplification exists. Multiple-choice boxes can't capture this.

> **Design principle (ADR-001):** Use AskQuestion when you know the option space. Use Plan Mode when you need to discover it.

#### Step 1.3: Command Discovery Conversation (Plan Mode)

**Internal Process (not shown to user) — do this before speaking:**

- Silently list every missing detail about the command's purpose and design
- Identify ambiguities in the initial description
- Note potential conflicts with existing commands
- Catalog unknowns: purpose & unique value, target workflow, execution style, inputs/outputs, tool needs, file organization, error handling, integration with existing commands

**Conversation Rules:**

- Ask ONE focused question at a time, targeting the highest-impact unknown
- After each answer, re-scan existing commands for additional context if relevant
- Continue until reaching 95% confidence on the command specification
- **Never declare "final question"** — let the conversation flow naturally
- Let the user signal when they're ready to see a contract
- **Challenge command ideas that create complexity or don't fit** — better to surface concerns early than build problematic commands

**Critical Analysis Responsibility:**

- If command seems to duplicate existing functionality, explain the overlap and suggest alternatives
- If complexity seems too high for the proposed value, recommend simplification
- If the command doesn't fit Writ patterns, point out the inconsistency
- If implementation would create maintenance burden, suggest alternative approaches
- If command scope is unclear or too broad, ask for focus and boundaries

**Pushback Phrasing Examples:**

- "I see potential overlap with [existing command]. How would [your command] be different from [existing]?"
- "The complexity you're describing sounds like it might need 3-4 separate commands. Should we focus on [core piece] first?"
- "I'm concerned that [proposed approach] would break Writ's [established pattern]. Have you considered [alternative]?"
- "This command would need significant ongoing maintenance. Could we achieve the same goal with [simpler approach]?"

**Topic Areas to Explore:**

- What specific developer workflow does this solve that existing commands don't?
- Should this integrate with existing commands, or remain standalone?
- What does success look like — how will developers know the command worked?
- Contract-style (extensive clarification like `create-spec`) or direct execution (immediate action like `refactor`)?
- Where should outputs live — new folder or existing `.writ/` subdirectory?
- What tools will it need?

**Transition to Contract:**

When confidence is high, present the contract (still in Plan Mode). Always leave room for refinement.

#### Step 1.4: Command Contract Proposal

Present a command contract covering: name, purpose, unique value vs. existing commands, execution style, workflow pattern, inputs required, outputs created, tool integration needs, implementation concerns (if any), and recommendations.

Surface any concerns directly in the contract. If the command's value proposition is weak or overlaps significantly with existing commands, say so.

Present in Plan Mode and discuss refinements conversationally.

#### Step 1.4b: Contract Decision (Agent Mode)

When the user returns to Agent Mode after approving the contract direction, confirm with AskQuestion:

```
AskQuestion({
  title: "Command Contract Decision",
  questions: [
    {
      id: "contract_action",
      prompt: "How would you like to proceed with this command contract?",
      options: [
        { id: "yes", label: "Lock contract and create the command" },
        { id: "edit", label: "Edit the contract (I'll specify changes)" },
        { id: "examples", label: "See similar commands for reference" },
        { id: "blueprint", label: "See the planned file structure" },
        { id: "questions", label: "I have more questions before deciding" }
      ]
    }
  ]
})
```

**Handling responses:**
- **yes**: Proceed to Phase 2 (Command File Creation)
- **edit**: Ask free-text follow-up for changes
- **examples**: Show similar command structures, then re-present with AskQuestion
- **blueprint**: Show planned file, then re-present with AskQuestion
- **questions**: Switch back to Plan Mode and return to discovery

---

### Phase 2: Command File Creation (Post-Agreement Only)

Triggered only after user confirms contract with "yes." Track progress with `todo_write`.

#### Step 2.1: Generate the Command File

Create `commands/[command-name].md`. A well-structured command file contains:

| Section | Purpose |
|---|---|
| **Overview** | What the command does and when to use it. 2-4 sentences max. |
| **Invocation** | Table of invocation patterns and behaviors |
| **Command Process** | The workflow — phases, steps, decision points. Contract-style commands get Phase 1 (discovery) and Phase 2 (execution). Direct commands get a linear step sequence. |
| **Core rules or conventions** | Non-obvious constraints, quality bars, patterns to follow |
| **Integration with Writ** | Table mapping relationships to other commands |

**Command categories** inform structure but don't dictate templates:

| Category | Examples | Typical pattern |
|---|---|---|
| Planning/Specification | `create-spec`, `create-adr`, `plan-product` | Contract-first with Plan Mode discovery |
| Implementation | `implement-story`, `refactor` | Direct execution with progress tracking |
| Setup/Analysis | `initialize`, `research`, `explain-code` | Context scan → file generation |
| Quality | `review`, `assess-spec` | Analysis → findings → recommendations |
| Meta | `new-command`, `status` | Ecosystem-aware scaffolding or reporting |

**Quality bars for the generated command file:**

- Every section passes the litmus test: teaches something non-obvious, sets a quality bar, or prevents a likely mistake
- Principles over prescriptions — tell the AI *what matters*, not *how to format*
- No hardcoded line numbers or brittle references to other files
- Language and shell agnostic — use Writ's tools, not platform-specific commands
- Match the voice and density of existing refined commands

#### Step 2.2: Validate Integration

- Verify no naming conflicts with existing commands in `commands/`
- Confirm the command file follows patterns consistent with existing commands
- Check that integration references are accurate (referenced commands actually exist)

Present a summary: file created, command name and usage, key integration points.

---

## Core Rules

1. **Contract before creation** — no files until the specification is agreed upon
2. **Critical over agreeable** — challenge weak command ideas, surface overlap, recommend alternatives
3. **Principles over templates** — generated commands should express quality bars, not fill in blanks
4. **Ecosystem-aware** — every new command must fit the existing command vocabulary and patterns
5. **Language & shell agnostic** — commands work across tech stacks, using Writ's tools

---

## Integration with Writ

| Command | Relationship |
|---------|-------------|
| `/create-spec` | Shares the contract-first interaction model; new commands may reference or integrate with specs |
| `/research` | Run before `/new-command` if the command design requires technical research |
| `/create-adr` | Significant command design decisions (new execution styles, new categories) may warrant an ADR |
| `/assess-spec` | After creating a command, assess whether its specification is complete |

## Completion

This command succeeds when:

1. **Command file created** — a `.md` file exists in `commands/` with the new command's name, containing Overview, Invocation, Command Process, and Integration sections
2. **No naming conflicts** — the command name doesn't collide with existing commands in `commands/`
3. **Integration validated** — references to other commands are accurate and the command fits Writ's patterns
4. **Summary presented** — the user received a completion summary with the file path and usage instructions

**Suggested next step:** Test the new command by invoking it.

**Terminal constraint:** This command produces a command definition (`commands/{name}.md`). Do not offer to implement, build, or execute what was defined. For testing, the user should invoke the new command directly. For quick prototyping, use `/prototype`.
