# Initialize Command Workflow

## Overview

### Purpose

Set up technical foundation and development infrastructure by detecting if this is a greenfield (new) or brownfield (existing) project and executing the appropriate technical setup workflow.

### Detection Logic

1. **Scan current directory** for indicators:

   - Presence of package.json, requirements.txt, Cargo.toml, go.mod, etc.
   - Existing source code directories (src/, lib/, app/, etc.)
   - Git repository status
   - Configuration files

2. **Classify as**:
   - **Greenfield**: Empty directory or minimal files
   - **Brownfield**: Existing codebase with established structure

---

## Greenfield Workflow

### Phase 1: Technical Foundation Setup

#### Greenfield Todo Checklist

Use `todo_write` to track progress through technical setup:

```json
{
  "todos": [
    {
      "id": "greenfield-tech-analysis",
      "content": "Determine technology stack and development requirements",
      "status": "in_progress"
    },
    {
      "id": "greenfield-tech-stack",
      "content": "Document technology stack in .writ/docs/tech-stack.md",
      "status": "pending"
    },
    {
      "id": "greenfield-structure",
      "content": "Create project directory structure and config files",
      "status": "pending"
    },
    {
      "id": "greenfield-dev-setup",
      "content": "Set up development configuration and tooling",
      "status": "pending"
    },
    {
      "id": "greenfield-readme",
      "content": "Generate technical README.md with setup instructions",
      "status": "pending"
    }
  ]
}
```

**Ask focused technical questions**:

1. **Project Type**: "What type of application are you building? (web app, API, mobile app, library, CLI tool, etc.)"
2. **Technical Constraints**: "Any required technologies, frameworks, or platforms?"
3. **Development Environment**: "What's your preferred development setup? (local, containerized, cloud-based)"
4. **Scale Requirements**: "Expected technical scale? (prototype, small team, enterprise)"

### Phase 2: Technology Recommendations

Based on technical requirements, recommend:

- **Tech Stack**: Languages, frameworks, databases suitable for the project type
- **Architecture Pattern**: Monolith, microservices, serverless based on scale needs
- **Development Tools**: Testing frameworks, build tools, linting/formatting
- **Project Structure**: Directory layout, naming conventions, configuration

### Phase 3: Technical Foundation Setup

#### Directory Structure (Pre-existing)

The `.writ/` directory structure already exists from installation:

- `.writ/docs/` - For technical documentation
- `.writ/research/` - For research outputs
- `.writ/commands/` - Pre-installed command definitions

#### Configuration Files

- **Package/dependency files** (package.json, requirements.txt, etc.)
- **Git configuration** (.gitignore, .gitattributes)
- **Development configuration** (prettier, eslint, testing config, etc.)
- **Build and deployment configuration** (if applicable)

#### Documentation Creation (Exact File Paths)

1. **`.writ/docs/tech-stack.md`** - Technology stack decisions and rationale
2. **`.writ/docs/code-style.md`** - Coding standards and development patterns
3. **`README.md`** - Technical overview and setup instructions

### Phase 4: Next Steps Guidance

After technical foundation is complete, provide clear next steps:

```
🚀 Technical Foundation Complete!

Your development environment is now set up and documented:
- Technology stack documented and configured
- Development tools and standards established
- Project structure and configuration ready

## Recommended Next Steps:

### For New Products:
/plan-product "your product idea" - Define product vision, strategy, and roadmap

### For Existing Products:
/create-spec "feature description" - Create detailed feature specifications
/implement-story - Implement features with TDD workflow

### For Research:
/research "topic" - Conduct systematic technical research
/create-adr "decision" - Document architectural decisions

Ready to define your product strategy and start building!
```

---

## Brownfield Workflow

### Phase 1: Codebase Analysis

#### Brownfield Todo Checklist

Use `todo_write` to track analysis progress:

```json
{
  "todos": [
    {
      "id": "brownfield-analysis",
      "content": "Analyze existing codebase structure, dependencies, and patterns",
      "status": "in_progress"
    },
    {
      "id": "brownfield-tech-stack",
      "content": "Document current tech stack in .writ/docs/tech-stack.md",
      "status": "pending"
    },
    {
      "id": "brownfield-code-style",
      "content": "Analyze and document code patterns in .writ/docs/code-style.md",
      "status": "pending"
    },
    {
      "id": "brownfield-architecture",
      "content": "Document system architecture and technical decisions",
      "status": "pending"
    }
  ]
}
```

**Scan and analyze**:

- **File structure** and organization patterns
- **Dependencies** and technology stack
- **Code patterns**, conventions, and architecture
- **Configuration files** and build processes
- **Testing setup** and development tools
- **Documentation gaps** and technical debt

### Phase 2: Documentation Generation

#### tech-stack.md

```markdown
# Technology Stack

## Languages

- [Primary language with version]
- [Secondary languages if any]

## Frameworks & Libraries

- [Main framework with version and purpose]
- [Key dependencies with purposes]

## Infrastructure

- [Database technology]
- [Deployment platform]
- [CI/CD tools]

## Development Tools

- [Package manager]
- [Testing framework]
- [Linting/formatting tools]

## Architecture Pattern

[Monolith/Microservices/Serverless/etc. with reasoning]
```

#### code-style.md

```markdown
# Code Style Guide

## File Organization

[Directory structure patterns observed]

## Naming Conventions

- [Variable naming patterns]
- [Function naming patterns]
- [File naming patterns]

## Code Patterns

[Common patterns observed in codebase]

## Testing Patterns

[How tests are structured and named]

## Documentation Style

[Comment and documentation patterns]
```

### Phase 3: Gap Analysis & Recommendations

Identify and document:

- **Missing technical documentation**
- **Inconsistent code patterns**
- **Technical debt and improvement opportunities**
- **Testing coverage gaps**
- **Development workflow improvements**
- **Architecture optimization opportunities**

### Phase 4: Next Steps Guidance

After brownfield analysis is complete, provide clear next steps:

```
🔍 Technical Foundation Analysis Complete!

Your existing project has been analyzed and documented:
- Current technology stack and architecture documented
- Code patterns and conventions identified
- Technical gaps and improvement opportunities noted

## Recommended Next Steps:

### For Product Strategy (Recommended First):
/plan-product "enhanced product vision" - Define product strategy and roadmap

### For Feature Development:
/create-spec "feature description" - Create detailed feature specifications
/implement-story - Implement features following established patterns

### For Technical Improvements:
/research "technical topic" - Research solutions for identified gaps
/create-adr "technical decision" - Document architectural improvements

Ready to define your product strategy and enhance your codebase!
```

---

---

## CRITICAL: Final Message Requirements

**MANDATORY**: The initialize command MUST end with a message that prominently recommends `plan-product` as the next logical step for both greenfield and brownfield projects. This is required because:

1. Initialize handles ONLY technical foundation
2. plan-product handles product strategy and vision
3. Users need both for complete project setup
4. plan-product should be the next step before feature development

**Required message format**:

```
🚀 Technical Foundation Complete! / 🔍 Technical Foundation Analysis Complete!

## Recommended Next Steps:

### For Product Strategy (Recommended First):
/plan-product "your product idea/vision" - Define product strategy and roadmap

### For Feature Development:
/create-spec "feature description" - Create detailed feature specifications
/implement-story - Implement features

### For Technical Improvements:
/research "topic" - Research solutions for gaps
/create-adr "decision" - Document architectural decisions
```

---

## Implementation Notes

### Tool Integration

- Use `codebase_search` for semantic understanding
- Use `file_search` for pattern discovery
- Use `todo_write` for progress tracking throughout both workflows
- Use `edit_file` to create documentation files

### Output Locations & File Structure

#### Directory Structure (Created by Install Script)

```
.writ/
├── commands/                 # CC command definitions (pre-installed)
└── docs/
    ├── best-practices.md     # Development best practices (pre-installed)
    ├── code-style.md         # Code conventions and patterns
    ├── tech-stack.md         # Technology decisions and rationale
    └── architecture.md       # System architecture (if complex)
```

#### Specific File Locations

**Docs Directory** (`.writ/docs/`):

- `best-practices.md` - Development best practices (pre-installed)
- `code-style.md` - Coding standards, naming conventions, patterns
- `tech-stack.md` - Technology choices with justifications
- `architecture.md` - System architecture and technical decisions (if complex)

**Research Directory** (`.writ/research/`):

- Research outputs, technical analysis, and investigation results

**Commands Directory** (`.writ/commands/`):

- Pre-installed CC command definitions (managed by system)

**Root Directory**:

- `README.md` - Project overview and quick start (only for new projects)

### Todo Integration

Each phase should update todos to show progress, enabling Cursor's todo tracking:

#### Example Todo Updates

```javascript
// Mark analysis complete and start documentation phase
todo_write({
  merge: true,
  todos: [
    { id: "greenfield-tech-analysis", status: "completed" },
    { id: "greenfield-tech-stack", status: "in_progress" },
  ],
});

// Update when creating documentation files
todo_write({
  merge: true,
  todos: [
    { id: "greenfield-tech-stack", status: "completed" },
    { id: "greenfield-dev-setup", status: "completed" },
    { id: "greenfield-readme", status: "in_progress" },
  ],
});
```

#### Todo Best Practices

- **Always include file paths** in todo content for clarity
- **Use descriptive IDs** that indicate workflow type (greenfield/brownfield)
- **Update todos immediately** after completing each task
- **Mark todos as completed** only after files are actually created
- **Use `merge: true`** to update existing todos without replacing the entire list

#### File Creation Verification

Before marking documentation todos as complete, ensure:

1. **Directory exists**: `.writ/docs/`
2. **File is created**: Use `write` tool to create the actual file
3. **Content is complete**: File contains all required sections
4. **Path is correct**: Double-check exact file path matches todo description
