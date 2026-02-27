# Documentation Agent

## Purpose

Specialized agent for creating and maintaining comprehensive developer documentation using VitePress. Generates structured documentation in `docs/` that can be built into a searchable documentation site with Mermaid diagrams.

## Agent Configuration

```
subagent_type: "generalPurpose"
readonly: false  # CRITICAL: Must be false - agent creates documentation files!
```

**IMPORTANT:** Do NOT set `readonly: true` when launching this agent.

## Documentation Structure (VitePress)

The agent maintains documentation in `docs/` at the project root:

```
docs/
├── .vitepress/
│   └── config.ts              # VitePress configuration (sidebar, nav)
├── index.md                   # Home page
├── guide/
│   ├── index.md              # Getting started
│   ├── quick-start.md        # Quick start guide
│   └── development.md        # Development workflow
├── architecture/
│   ├── index.md              # Architecture overview
│   ├── data-flow.md          # Data flow diagrams
│   └── technology-choices.md # Tech rationale
├── features/
│   ├── index.md              # Features index
│   └── {feature-name}.md     # Individual feature docs
├── components/
│   ├── index.md              # Components index
│   ├── ui.md                 # shadcn/ui components
│   └── {component-name}.md   # Individual component docs
└── reference/
    ├── api.md                # Server actions
    ├── types.md              # TypeScript types
    └── hooks.md              # Custom hooks
```

## Responsibilities

1. **Document features** - Create `docs/features/{feature-name}.md` with Mermaid diagrams
2. **Document components** - Create `docs/components/{component-name}.md`
3. **Update architecture** - Add to `docs/architecture/index.md` when major changes
4. **Update sidebar** - Add new pages to `docs/.vitepress/config.ts`
5. **Add inline docs** - Add JSDoc comments to source files

## Input Requirements

| Parameter | Description |
|-----------|-------------|
| `story_file_path` | Full path to the story file |
| `full_story_content` | Complete story markdown content |
| `spec_context` | Relevant specification context |
| `files_changed` | List of files created/modified |
| `functionality_summary` | Summary of new functionality |

## Prompt Template

```
Task({
  subagent_type: "generalPurpose",
  description: "Update VitePress documentation",
  readonly: false,
  prompt: `You are the Documentation Agent for the Weather App VitePress documentation.

## Your Mission

Create or update developer documentation for the implemented story. The documentation lives in \`docs/\` and uses VitePress with Mermaid diagrams.

## Story Implemented

**Story file path:** {story_file_path}
**Story content:**
{full_story_content}

## Specification Context

{spec_context}

## Implementation Summary

**Files created/modified:**
{files_changed}

**New functionality:**
{functionality_summary}

## Documentation Tasks

### 1. Feature Documentation

Create \`docs/features/{feature-name}.md\` with this structure:

\`\`\`markdown
# Feature Name

Brief description of the feature.

## Overview

What this feature does and why it exists.

## Architecture

\`\`\`mermaid
graph TB
    A[Component] --> B[Hook]
    B --> C[Service]
\`\`\`

## Components

| Component | Purpose | Location |
|-----------|---------|----------|
| ComponentName | What it does | \`src/path/file.tsx\` |

## State Management

How state is handled (context, local state, etc.)

## Usage Examples

\`\`\`tsx
// Code example showing how to use this feature
\`\`\`

## Related Files

- \`src/path/file.ts\` - Description
- \`src/path/other.ts\` - Description
\`\`\`

### 2. Component Documentation

For new reusable components, create \`docs/components/{component-name}.md\`:

\`\`\`markdown
# ComponentName

Brief description.

## Usage

\`\`\`tsx
import { ComponentName } from '@/components/path'

<ComponentName prop="value" />
\`\`\`

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| prop | string | - | Description |

## Examples

[Code examples for different use cases]
\`\`\`

### 3. Architecture Updates

If the story adds major components or changes data flow, update \`docs/architecture/index.md\`:

- Add to the component architecture diagram
- Update data flow if patterns changed
- Document new subsystems

### 4. Update VitePress Sidebar

Add new pages to \`docs/.vitepress/config.ts\` in the appropriate sidebar section:

\`\`\`typescript
// In the sidebar config for features:
{
  text: 'Features',
  items: [
    { text: 'Overview', link: '/features/' },
    { text: 'New Feature', link: '/features/new-feature' },  // Add this
  ]
}
\`\`\`

### 5. Update Feature Index

Add the new feature to the table in \`docs/features/index.md\`:

\`\`\`markdown
| Feature | Status | Description |
|---------|--------|-------------|
| [New Feature](/features/new-feature) | ✅ Complete | Description |
\`\`\`

### 6. Inline Documentation

Add JSDoc comments to source files:

\`\`\`typescript
/**
 * Brief description of the function/component.
 * 
 * @param paramName - Description
 * @returns Description of return value
 * 
 * @example
 * \`\`\`ts
 * const result = functionName(arg)
 * \`\`\`
 */
\`\`\`

## Mermaid Diagram Types

Use these for visual documentation:

**Component relationships:**
\`\`\`mermaid
graph TB
    A[Parent] --> B[Child]
    A --> C[Child]
\`\`\`

**Data flow:**
\`\`\`mermaid
sequenceDiagram
    User->>Component: Action
    Component->>Service: Request
    Service-->>Component: Response
\`\`\`

**State machines:**
\`\`\`mermaid
stateDiagram-v2
    [*] --> Loading
    Loading --> Success
    Loading --> Error
\`\`\`

## Output Format

### DOCS_UPDATED: [YES/NO]

### Documentation Changes

#### Files Created
- **File:** \`docs/features/feature-name.md\`
- **Purpose:** Feature documentation with architecture diagram

#### Files Updated
- **File:** \`docs/.vitepress/config.ts\`
- **Change:** Added feature to sidebar

#### Diagrams Added
- Component architecture diagram in feature doc
- Data flow sequence diagram

#### Inline Documentation
- **File:** \`src/components/Feature.tsx\`
- **Added:** JSDoc for component and props

### Summary
Brief summary of documentation changes.
`
})
```

## Output Format

### When Documentation Created

```markdown
### DOCS_UPDATED: YES

### Documentation Changes

#### Files Created

1. **File:** `docs/features/weather-backgrounds.md`
   - Complete feature documentation with Mermaid diagrams
   - Component table, state management, usage examples

#### Files Updated

1. **File:** `docs/.vitepress/config.ts`
   - Added weather-backgrounds to features sidebar

2. **File:** `docs/features/index.md`
   - Added weather-backgrounds to feature index table

3. **File:** `docs/architecture/index.md`
   - Added Weather Backgrounds subsystem to component architecture diagram

#### Diagrams Added

1. Component hierarchy diagram showing:
   - WeatherThemeProvider → GradientBackground
   - WeatherThemeProvider → ParticleSystem

2. Data flow sequence diagram showing theme updates

#### Inline Documentation

- `src/components/background/GradientBackground.tsx` - JSDoc for component and props
- `src/components/background/hooks/useReducedMotion.ts` - JSDoc for hook

### Summary
Created comprehensive feature documentation for Weather Backgrounds with architecture diagrams, updated VitePress sidebar, and added inline documentation to source files.
```

### When No Updates Needed

```markdown
### DOCS_UPDATED: NO

### Assessment
The story implemented internal refactoring only. No new features, components, or API changes that would require documentation updates.

### Recommendations
- Consider documenting in future if this utility becomes public API
```

## VitePress Commands

To preview documentation locally:

```bash
# Install VitePress (one-time)
pnpm add -D vitepress

# Start dev server
pnpm docs:dev

# Build for production
pnpm docs:build
```

## Documentation Guidelines

### When to Create New Docs

| Change Type | Documentation Action |
|-------------|---------------------|
| New feature | Create `docs/features/{name}.md` |
| New component | Create `docs/components/{name}.md` |
| Architecture change | Update `docs/architecture/index.md` |
| New API/hook | Update `docs/reference/` |
| Config change | Update relevant guide |

### Mermaid Best Practices

- Keep diagrams focused (max 10-15 nodes)
- Use subgraphs for grouping related items
- Add labels to connections when helpful
- Use consistent styling across docs

### JSDoc Standards

```typescript
/**
 * Brief description (one line).
 * 
 * @description Longer description if needed.
 * 
 * @param param - Parameter description
 * @returns Return value description
 * 
 * @example
 * ```ts
 * const result = func(arg)
 * // result: expected output
 * ```
 */
```
