# Design Command (design)

## Overview

Visual design companion for writ specs. Generates wireframes, accepts screenshots/mockups as design inputs, and stores visual references that the coding agent uses during implementation.

Works standalone or integrated into the `/create-spec` → `/implement-story` pipeline.

## Invocation

| Invocation | Behavior |
|---|---|
| `/design` | Interactive — select a spec or start fresh |
| `/design 2026-03-01-dashboard` | Add visuals to existing spec |
| `/design --wireframe "login page"` | Generate Excalidraw wireframe from description |
| `/design --screenshot` | Capture current UI state for reference |
| `/design --compare` | Side-by-side mockup vs implementation |

## Command Process

### Phase 1: Context & Mode Selection

#### Step 1.1: Determine Mode

```
AskQuestion({
  title: "Design Mode",
  questions: [
    {
      id: "mode",
      prompt: "What would you like to do?",
      options: [
        { id: "wireframe", label: "Generate wireframes from a description or spec" },
        { id: "attach", label: "Attach screenshots/mockups to an existing spec" },
        { id: "capture", label: "Screenshot the current app for reference" },
        { id: "compare", label: "Compare mockup vs current implementation" },
        { id: "review", label: "Review existing mockups for a spec" }
      ]
    }
  ]
})
```

#### Step 1.2: Load Context

1. **Scan `.writ/specs/`** for existing specs
2. **Check for design system docs** in `.writ/docs/design-system.md`
3. **Detect UI framework** — React, Vue, Svelte, HTML (influences component suggestions)
4. **Detect CSS framework** — Tailwind, CSS Modules, styled-components (influences spacing/token references)
5. **Load existing mockups** from `mockups/` in the target spec

---

### Mode A: Generate Wireframes

#### Step A.1: Gather Requirements

If attached to a spec, read `spec.md` and story files to understand the feature.

If standalone, ask:
- What screen/component are we designing?
- What user actions should be possible?
- What data is displayed?
- Any existing patterns to match? (show screenshots of current app if available)

#### Step A.2: Generate Excalidraw Wireframe

Generate an Excalidraw JSON file representing the wireframe.

**Excalidraw JSON structure:**
```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "writ",
  "elements": [
    {
      "type": "rectangle",
      "x": 0, "y": 0,
      "width": 375, "height": 812,
      "strokeColor": "#1e1e1e",
      "backgroundColor": "transparent",
      "label": { "text": "Mobile Frame" }
    }
  ],
  "appState": {
    "viewBackgroundColor": "#ffffff",
    "gridSize": 20
  }
}
```

**Component primitives to use:**
- **Rectangle** — containers, cards, buttons, inputs
- **Text** — labels, headings, body text, placeholder content
- **Line/Arrow** — flows, connections, dividers
- **Ellipse** — avatars, icons (placeholder)
- **Diamond** — decision points (for flow diagrams)
- **Groups** — logically group related elements

**Wireframe conventions:**
- Use 375×812 frame for mobile, 1440×900 for desktop
- Gray fills (`#e8e8e8`) for placeholder images/media
- Dashed borders for optional/conditional elements
- Annotations in red (`#e03131`) for interaction notes
- Label everything — the coding agent reads these labels

#### Step A.3: Generate Component States

For interactive components, generate multiple wireframes:
- **Default state**
- **Loading state** (skeleton screens)
- **Empty state** (no data)
- **Error state** (validation, API failure)
- **Hover/active states** (if relevant)

Name them: `{component}-default.excalidraw`, `{component}-empty.excalidraw`, etc.

#### Step A.4: Save & Present

Save wireframes to spec's mockups directory:

```
.writ/specs/{spec-name}/
├── mockups/
│   ├── {screen}-wireframe.excalidraw
│   ├── {screen}-wireframe.png          # Rendered preview (if possible)
│   ├── {screen}-empty-state.excalidraw
│   └── component-inventory.md          # List of components with descriptions
```

Generate `component-inventory.md`:
```markdown
# Component Inventory

## {Screen Name}

| Component | Type | States | Notes |
|-----------|------|--------|-------|
| Header | Layout | default | Fixed, 64px height |
| SearchBar | Input | default, focused, loading | Debounced, 300ms |
| CardGrid | List | default, empty, loading | 3-col desktop, 1-col mobile |
| Card | Display | default, hover, selected | Links to detail view |

## Design Tokens Referenced
- Spacing: 4px grid (Tailwind: space-1 = 4px)
- Border radius: 8px (rounded-lg)
- Shadow: sm for cards, lg for modals
- Colors: [reference design-system.md if exists]
```

---

### Mode B: Attach Mockups

#### Step B.1: Select Target Spec

```
AskQuestion({
  title: "Attach Mockups",
  questions: [
    {
      id: "spec",
      prompt: "Which spec should these mockups attach to?",
      options: [list of specs from .writ/specs/]
    }
  ]
})
```

#### Step B.2: Accept Visual Inputs

Accept images via:
- **File path** — local image files
- **Paste/upload** — platform-dependent (Cursor paste, Claude Code file reference)
- **URL** — external image links
- **Excalidraw files** — `.excalidraw` JSON files

#### Step B.3: Catalog & Store

For each image:
1. Copy/save to `mockups/` directory in the spec
2. Analyze the image with vision — extract:
   - Key UI components visible
   - Layout structure (grid, flex, sidebar+main, etc.)
   - Approximate spacing and sizing
   - Colors and typography observed
   - Interactive elements (buttons, inputs, links)
3. Generate a `mockups/README.md` cataloging all visual references

**mockups/README.md:**
```markdown
# Visual References

## Mockups

| File | Description | Screen/Component | Stories |
|------|-------------|-------------------|---------|
| dashboard-main.png | Main dashboard layout | Desktop, logged in | Story 1, 2 |
| mobile-nav.png | Mobile navigation drawer | Mobile, all states | Story 3 |
| card-states.excalidraw | Card component states | Component | Story 2 |

## Design Notes
- [Observations extracted from mockup analysis]
- [Spacing patterns, color usage, typography]
- [Responsive behavior implied by mockups]
```

#### Step B.4: Link to Stories

Update relevant story files to reference their mockups:

```markdown
## Visual References
- **Primary mockup:** `../mockups/dashboard-main.png` — implement the card grid layout shown
- **Component states:** `../mockups/card-states.excalidraw` — all four states required
- **Design notes:** Cards use 8px border-radius, 16px padding, subtle shadow on hover
```

---

### Mode C: Capture Current UI

#### Step C.1: Start Application

Check if the app is running. If not:
```bash
# Detect start command from package.json
npm run dev  # or equivalent
```

Wait for the app to be ready.

#### Step C.2: Capture Screenshots

Using Playwright or browser tooling:

```bash
# Capture key viewports
# Desktop (1440×900)
# Tablet (768×1024)
# Mobile (375×812)
```

Capture the current state of specified pages/routes.

#### Step C.3: Store as Reference

Save to spec or project-level reference:

```
.writ/specs/{spec-name}/
├── mockups/
│   ├── current/                    # Current state captures
│   │   ├── desktop-{page}.png
│   │   ├── tablet-{page}.png
│   │   └── mobile-{page}.png
│   └── target/                     # Target state (mockups/wireframes)
│       ├── desktop-{page}.png
│       └── {page}-wireframe.excalidraw
```

---

### Mode D: Compare Mockup vs Implementation

#### Step D.1: Load References

1. Load target mockup from `mockups/target/` or `mockups/*.png`
2. Capture current implementation state via browser screenshot

#### Step D.2: Visual Comparison

Use vision model to compare:

**Comparison report:**
```markdown
## Visual Comparison: {screen}

### Mockup vs Implementation

| Aspect | Mockup | Implementation | Match |
|--------|--------|----------------|-------|
| Layout | 3-col grid | 3-col grid | ✅ |
| Header height | ~64px | 64px | ✅ |
| Card spacing | ~16px gap | 12px gap | ⚠️ Close but off |
| Card shadow | Subtle on hover | No shadow | ❌ Missing |
| Empty state | Custom illustration | Generic "no data" | ❌ Differs |
| Color scheme | Blue primary (#3b82f6) | Blue primary (#3b82f6) | ✅ |
| Typography | 14px body, 20px headings | 14px body, 18px headings | ⚠️ Headings smaller |

### Recommended Fixes
1. Add `gap-4` (16px) to card grid container
2. Add `shadow-sm hover:shadow-md transition-shadow` to cards
3. Update heading size from `text-lg` to `text-xl`
4. Create custom empty state component matching mockup illustration

### Overall: 70% match — 3 issues to address
```

#### Step D.3: Generate Fix Tasks

If attached to a spec, create issue entries or update the relevant story with fix tasks.

---

## Design System Extraction

When processing mockups, if `.writ/docs/design-system.md` doesn't exist, auto-generate one:

```markdown
# Design System

> Auto-extracted from mockups. Update as needed.

## Colors
- Primary: #3b82f6 (blue-500)
- Secondary: #6366f1 (indigo-500)
- Background: #ffffff
- Surface: #f9fafb (gray-50)
- Text primary: #111827 (gray-900)
- Text secondary: #6b7280 (gray-500)

## Typography
- Font: Inter (or system-ui fallback)
- Body: 14px / 1.5 line-height
- Heading 1: 24px / 1.2 / semibold
- Heading 2: 20px / 1.3 / semibold
- Small: 12px / 1.4

## Spacing
- Base unit: 4px
- Component padding: 16px
- Card gap: 16px
- Section gap: 32px

## Components
- Border radius: 8px (cards), 6px (buttons), 4px (inputs)
- Shadows: sm (cards), md (dropdowns), lg (modals)
- Transitions: 150ms ease-in-out
```

## Integration with Pipeline

### How specs reference mockups

Story files include a `## Visual References` section (added by `/design` or `/create-spec`):

```markdown
## Visual References
- **Layout:** `../mockups/dashboard-wireframe.excalidraw`
- **Screenshot (current):** `../mockups/current/desktop-dashboard.png`
- **Component states:** `../mockups/card-states.excalidraw`
```

### How the coding agent uses them

The coding agent (Gate 1) loads visual references when present:
1. Reads image files via vision model
2. Reads Excalidraw JSON for precise layout details
3. References `component-inventory.md` for component structure
4. References `design-system.md` for tokens and conventions

### How visual QA validates

See: `agents/visual-qa-agent.md` — optional Gate 4.5 in the implement-story pipeline.

## Tool Integration

| Tool | Purpose |
|------|---------|
| `write` | Create Excalidraw JSON files |
| `read_file` + vision | Analyze uploaded mockups/screenshots |
| Browser/Playwright | Capture current UI state |
| Vision model | Compare mockup vs implementation |
| `codebase_search` | Find existing components to reference |
