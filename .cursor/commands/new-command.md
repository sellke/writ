# New Command Creator (/new-command)

## Overview

A meta command that creates new Writ commands following established patterns and conventions. This command generates properly structured command files, updates documentation, and ensures consistency across the Writ ecosystem.

## Command Process

### Phase 1: Command Contract Establishment (No File Creation)

**Mission Statement:**

> Your goal is to turn my rough command idea into a comprehensive command specification. You will deliver the complete command package only after we both agree on the command contract. **Important: Challenge command ideas that don't fit the Writ ecosystem or would create maintenance burden - it's better to surface concerns early than build the wrong command.**

#### Step 1.1: Initial Context Scan

- Scan existing commands in `commands/` to understand patterns
- Analyze existing Writ ecosystem using `codebase_search`
- Load command patterns from successful commands (`create-spec`, `implement-story`, etc.)
- **Output:** Context summary (no files created yet)

#### Step 1.2: Gap Analysis & Silent Enumeration

**Internal Process (not shown to user):**

- Silently list every missing detail about the command's purpose and implementation
- Identify ambiguities in the initial command description
- Note potential conflicts with existing commands
- Catalog unknowns across these domains:
  - Command purpose & unique value proposition
  - Target workflow & user scenarios
  - Execution complexity & style requirements
  - Input/output specifications
  - Tool integration requirements
  - File organization & output locations
  - Error handling & edge cases
  - Integration with existing commands
  - Documentation & help text needs

#### Step 1.3: Structured Clarification Loop

**Rules:**

- Ask ONE focused question at a time
- After each answer, re-scan existing commands for additional context if relevant
- Continue until reaching 95% confidence on command specification
- Each question should target the highest-impact unknown
- **Never declare "final question"** - let the conversation flow naturally
- Let the user signal when they're ready to lock the contract
- **Challenge command ideas that create complexity or don't fit** - better to surface concerns early than build problematic commands

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

**Question Categories (examples):**

- "What specific developer workflow does this solve that existing commands don't cover?"
- "Should this integrate with [existing command found in scan], or remain separate?"
- "What does 'success' look like - how will developers know the command worked correctly?"
- "Should this be a contract-style command (extensive clarification like create-spec) or direct execution (immediate action like swab)?"
- "Where should outputs be stored - new folder or existing (.writ/[folder])?"
- "What Cursor tools will it need - codebase_search, file_search, edit_file, web_search?"

**Transition to Contract:**

- When confidence is high, present contract without declaring it "final"
- Use phrases like "I think I understand the command you need" or "Based on our discussion, here's the command specification"
- Always leave room for more questions if needed

#### Step 1.4: Echo Check (Command Contract Proposal)

When confident, present a command contract proposal with any concerns surfaced:

**Format:**

```
## Command Contract

**Command Name:** [validated-command-name]

**Purpose:** [One clear sentence describing what this command does]

**Unique Value:** [How this differs from existing commands and why it's needed]

**Execution Style:** [Contract-style with clarification OR Direct execution]

**Workflow Pattern:** [Step-by-step process the command follows]

**Inputs Required:** [Arguments, flags, or interactive inputs needed]

**Outputs Created:** [Files, directories, or modifications made]

**Tool Integration:** [Cursor tools required: codebase_search, file_search, etc.]

**⚠️ Implementation Concerns (if any):**
- [Specific concern about complexity, maintenance, or ecosystem fit]
- [Suggested alternative or mitigation approach]

**💡 Recommendations:**
- [Suggestions for improving the command based on ecosystem analysis]
- [Ways to reduce complexity or improve consistency]

---
Options:
- Type 'yes' to lock this contract and create the command
- Type 'edit: [your changes]' to modify the contract
- Type 'examples' to see similar commands for reference
- Type 'blueprint' to see the planned file structure and documentation
- Ask more questions if anything needs clarification
```

### Phase 2: Command Package Creation (Post-Agreement Only)

**Triggered only after user confirms contract with 'yes'**

#### Step 2.1: Initialize Tracking

```bash
# Use todo_write to track creation process
1. Generate command documentation with proper structure
2. Update ecosystem documentation and references
3. Validate command integration and consistency
4. Present completed command for user review
```

#### Step 2.2: Generate Command File Structure

**Generate Standard Command File Structure:**

```markdown
# [Command Name] Command ([command-name])

## Overview

[Generated from description and clarifying questions]

## Command Process

### Step 1: [Phase Name]

[Generated workflow steps based on contract]

### Step 2: [Phase Name]

[Generated workflow steps based on contract]

## Core Rules

[Generated based on command type and execution style from contract]

## Tool Integration

[Generated tool usage based on contract requirements]

## Integration Notes

[Generated integration details with existing commands]
```

**Template Sections Based on Command Type and Execution Style:**

**Contract Style Commands** (like `create-spec`, `create-adr`):

- Phase 1: Contract Establishment (No File Creation)
- Interactive clarification rounds with structured questions
- Critical analysis and assumption challenging
- Echo check/contract proposal phase
- Explicit user agreement before proceeding

**Direct Execution Commands** (like `refactor`, `implement-story`):

- Immediate action workflows
- Minimal clarification if needed
- Clear step-by-step execution
- Progress feedback and completion confirmation

**Setup/Analysis Commands:**

- Context scanning steps
- File generation workflows
- Progress tracking with `todo_write`

**Implementation Commands:**

- TDD workflows if applicable
- Code modification steps
- Verification procedures

**Integration Commands:**

- Platform-specific API interactions
- Sync and conflict resolution
- Error handling patterns

### Step 3: Validation and Integration

**Verify Command Integration:**

- Check command file syntax and structure
- Ensure no conflicts with existing commands
- Validate command follows established patterns
- Test command can be discovered by Cursor

**Present Summary:**

```
✅ New command created successfully!

📁 Files Created:
  - commands/[command-name].md

🚀 Command Ready:
  Usage: /[command-name] [args]
  Documentation: commands/[command-name].md
```

## Core Rules

1. **Consistent Structure** - All generated commands follow established patterns
2. **Clear Documentation** - Each section has purpose and implementation details
3. **Automatic Integration** - Updates all necessary documentation files
4. **Validation Required** - Check for conflicts and proper structure
5. **Template Flexibility** - Adapt template based on command type and requirements
6. **Language & Shell Agnostic** - Commands should work across different programming languages and shell environments, using Writ's existing tools rather than making assumptions about tech stack

## AI Implementation Prompt

```
You are creating a new Writ command following established patterns.

MISSION: Generate a complete, well-structured command file and update documentation.

COMMAND SPECIFICATION:
- Name: {command_name}
- Description: {description}
- Category: {category}
- Execution Style: {contract_style_or_direct_execution}
- Usage Pattern: {usage_pattern}
- AI Coordination: {needs_ai_prompts}
- Output Location: {output_location}
- Tool Integration: {cursor_tools}
- Workflow Steps: {workflow_phases}

TEMPLATE STRUCTURE:
1. Title: # [Command Name] Command ([command-name])
2. Overview: Purpose and capabilities
3. Usage: Command syntax with examples
4. Command Process: Detailed step-by-step workflow
5. Core Rules: Implementation guidelines
6. AI Implementation Prompt: (if AI coordination needed)
7. Integration Notes: Cursor tool coordination

TEMPLATE ADAPTATION RULES:
- Contract Style commands: Include clarification phases, contract establishment, critical analysis, user agreement checkpoints
- Direct Execution commands: Include immediate action workflows, minimal interaction, clear progress feedback
- Setup/Analysis commands: Include context scanning, file generation, todo tracking
- Implementation commands: Include TDD workflows, code modification, verification
- Integration commands: Include API interactions, sync, error handling
- All commands: Include clear examples, tool coordination, progress tracking
- CRITICAL: Be language and shell agnostic - use codebase_search, list_dir, file_search instead of language-specific find commands or hardcoded file extensions

DOCUMENTATION UPDATES:
Commands are automatically discovered by Cursor from `commands/` - no manual documentation updates needed.

OUTPUT REQUIREMENTS:
1. Generate complete command file following the template
2. Ensure consistency with existing command patterns
3. Validate no conflicts with existing commands
4. Create command in `commands/[command-name].md`

QUALITY CHECKS:
- Command name follows naming conventions (lowercase, hyphens)
- Usage examples are clear and practical
- Workflow steps are actionable and specific
- Integration points are clearly documented
- All sections serve a clear purpose
- No hardcoded language assumptions or shell-specific commands
- Uses Writ's existing tools (codebase_search, list_dir, file_search) rather than system-specific commands
```

## Implementation Details

### Command Name Validation

**Validation Rules:**

- Lowercase letters, numbers, hyphens only
- No spaces or special characters
- Maximum 20 characters
- Cannot start with number or hyphen
- Must not conflict with existing commands

**Validation Process:**

```bash
# Check format
echo "command-name" | grep -E '^[a-z][a-z0-9-]*[a-z0-9]$'

# Check conflicts
ls .writ/commands/ | grep "^command-name.md$"
```

### Template Selection Logic

**Command Categories and Templates:**

1. **Setup/Analysis** (`initialize`, `research`, `explain-code`)

   - Context scanning workflows
   - Documentation generation
   - Progress tracking emphasis

2. **Planning/Specification** (`create-spec`, `create-adr`, `plan-product`)

   - Interactive clarification phases
   - Structured output formats
   - Contract-based workflows

3. **Implementation** (`implement-story`, `refactor`)

   - Code modification workflows
   - TDD patterns
   - Verification steps

4. **Quality** (`status`, `refactor`)
5. **Meta** (`new-command`, `explain-code`)
   - Command scaffolding and template generation
   - Documentation updates across the ecosystem
   - Validation and consistency checks

### Documentation Update Locations

**cc.md Update Points:**

- Line ~15-50: Available Commands sections
- Line ~95-110: Command documentation list
- Line ~150-190: Usage examples

**cc.mdc Update Points:**

- Line ~25-35: Core Commands list
- Line ~35-45: Enhanced workflows (if integration)

**README.md Update Points:**

- Line ~120-140: Feature sections
- Line ~400-415: Command reference table
- Line ~250-270: Source structure

### Error Handling

**Common Issues:**

- **Duplicate command name**: Check existing commands, suggest alternatives
- **Invalid command name format**: Provide format guidance and examples
- **Documentation update conflicts**: Use safe merge strategies, manual review if needed
- **Template generation errors**: Validate inputs, provide clear error messages

**Error Messages:**

```
❌ Command creation failed: [specific reason]

Suggestions:
- Check command name format (lowercase, hyphens only)
- Ensure name doesn't conflict with existing commands
- Verify all required inputs are provided

Try: /new-command "valid-name" "clear description"
```

## Integration Notes

This command integrates with Writ by:

1. **Following Established Patterns** - Uses same structure as existing commands
2. **Maintaining Consistency** - Ensures all new commands match style and format
3. **Automatic Documentation** - Updates all necessary files without manual intervention
4. **Extensibility** - Makes it easy to add new capabilities to Writ
5. **Quality Assurance** - Validates structure and prevents conflicts

## Future Enhancements

Potential improvements (not in initial version):

- **Template Library**: Multiple command templates for different use cases
- **Interactive Wizard**: Step-by-step command creation with guidance
- **Integration Testing**: Automated testing of generated commands
- **Version Control**: Track command changes and updates
- **Command Dependencies**: Handle commands that depend on other commands

But for now: Focus on core functionality - create well-structured commands that integrate seamlessly with the existing Writ ecosystem.
