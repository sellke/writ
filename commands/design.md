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

Present mode selection via AskQuestion:

| Mode | Description |
|---|---|
| **wireframe** | Generate wireframes from a description or spec |
| **attach** | Attach screenshots/mockups to an existing spec |
| **capture** | Screenshot the current app for reference |
| **compare** | Compare mockup vs current implementation |
| **review** | Review existing mockups for a spec |

#### Step 1.2: Load Context

1. Scan `.writ/specs/` for existing specs
2. Check for `.writ/docs/design-system.md`
3. Detect UI framework (React, Vue, Svelte, HTML) and CSS framework (Tailwind, CSS Modules, styled-components) — influences component suggestions and token references
4. Load existing mockups from `mockups/` in the target spec

---

### Mode A: Generate Wireframes

#### Step A.1: Gather Requirements

If attached to a spec, read `spec.md` and story files to understand the feature. If standalone, clarify: what screen/component, what user actions, what data is displayed, any existing patterns to match.

#### Step A.2: Generate Excalidraw Wireframe

Generate `.excalidraw` JSON files following these conventions:

- **Frame sizes:** 375×812 (mobile), 1440×900 (desktop)
- **Gray fills** (`#e8e8e8`) for placeholder images/media
- **Dashed borders** for optional/conditional elements
- **Red annotations** (`#e03131`) for interaction notes
- **Label everything** — the coding agent reads these labels to map wireframe elements to components

These conventions are non-negotiable. Without them, the coding agent misinterprets wireframes during Gate 1.

#### Step A.3: Generate Component States

For interactive components, generate multiple wireframes covering: default, loading (skeleton), empty (no data), error (validation/API), hover/active where relevant. Name them `{component}-{state}.excalidraw`.

#### Step A.4: Save & Present

Save wireframes to the spec's mockups directory:

```
.writ/specs/{spec-name}/
├── mockups/
│   ├── {screen}-wireframe.excalidraw
│   ├── {screen}-wireframe.png          # Rendered preview if possible
│   ├── {screen}-{state}.excalidraw     # Per-state wireframes
│   └── component-inventory.md
```

**Component inventory** (`component-inventory.md`): Catalog every component from the wireframes. For each component include: name, type (layout/input/display/nav), states generated, and implementation notes (sizing, responsive behavior, constraints). Reference design tokens from `design-system.md` when it exists.

Purpose: the coding agent reads this at Gate 1 to understand component structure before writing code. Make it scannable — use a table, not prose.

---

### Mode B: Attach Mockups

#### Step B.1: Select Target Spec

Present spec selection from `.writ/specs/` via AskQuestion.

#### Step B.2: Accept Visual Inputs

Accept images via file path, paste/upload, URL, or `.excalidraw` JSON files.

#### Step B.3: Catalog & Store

For each image:
1. Copy/save to `mockups/` directory in the spec
2. Analyze with vision — extract: key UI components, layout structure, spacing/sizing, colors/typography, interactive elements

Generate `mockups/README.md` as the visual reference catalog. Key fields: file path, description, screen/component mapped, story references. Include design notes extracted from analysis — spacing patterns, color usage, typography, responsive behavior implied by the mockups.

Purpose: single source of truth for all visual references in a spec. The coding agent and visual-qa-agent both read this.

#### Step B.4: Link to Stories

Update relevant story files with a `## Visual References` section:

```markdown
## Visual References
- **Primary mockup:** `../mockups/dashboard-main.png` — implement the card grid layout shown
- **Component states:** `../mockups/card-states.excalidraw` — all four states required
- **Design notes:** Cards use 8px border-radius, 16px padding, subtle shadow on hover
```

This format is important — the coding agent pattern-matches on `## Visual References` to load visual context.

---

### Mode C: Capture Current UI

Capture the running application's current state for before/after comparison or design reference.

1. **Detect running app** — check if dev server is active; if not, start it using the project's start command
2. **Capture via browser MCP** — use `browser_navigate` and screenshot capabilities at key viewports: desktop (1440×900), tablet (768×1024), mobile (375×812)
3. **Store** in the spec's mockups directory:

```
mockups/
├── current/              # Current state captures
│   ├── desktop-{page}.png
│   ├── tablet-{page}.png
│   └── mobile-{page}.png
└── target/               # Target state (mockups/wireframes)
    └── ...
```

The `current/` vs `target/` split is what enables Mode D comparison.

---

### Mode D: Compare Mockup vs Implementation

Visual comparison of target mockups against the live implementation.

1. **Load target** — mockup from `mockups/target/` or `mockups/*.png`
2. **Capture current** — use browser MCP to screenshot the live app at matching viewport
3. **Compare via vision** — analyze both images and produce a structured comparison

**Comparison table** (this is the key deliverable):

| Aspect | Mockup | Implementation | Match |
|--------|--------|----------------|-------|
| Layout | 3-col grid | 3-col grid | ✅ |
| Card spacing | ~16px gap | 12px gap | ⚠️ Close |
| Card shadow | Subtle on hover | No shadow | ❌ Missing |
| Typography | 14px body, 20px headings | 14px body, 18px headings | ⚠️ Headings smaller |

**Recommended fixes** — list each discrepancy with specific CSS/component changes needed, ordered by visual impact. Include an overall match percentage.

If attached to a spec, create issue entries or update the relevant story with fix tasks.

---

## Design System Extraction

When processing mockups and `.writ/docs/design-system.md` doesn't exist, auto-generate one. Extract from the visual references:

- **Colors** — primary, secondary, background, surface, text (map to framework tokens when applicable)
- **Typography** — font family, size scale with line-height and weight for body/headings/small
- **Spacing** — base unit, component padding, gap sizes, section spacing
- **Components** — border radii, shadow scale, transition defaults

Tag it as auto-extracted so developers know to refine it. Both the coding agent and visual-qa-agent reference this for consistency across stories.

---

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
1. Reads image files via vision model — understands layout, spacing, visual hierarchy
2. Reads Excalidraw JSON for precise layout details — coordinates, groupings, labels
3. References `component-inventory.md` for component structure and states
4. References `design-system.md` for tokens and conventions

### How visual QA validates

See: `agents/visual-qa-agent.md` — optional Gate 4.5 in the implement-story pipeline. Auto-activates when a story has visual references. Uses the same mockup files and comparison table format as Mode D.

## Completion

This command succeeds when the selected mode's output exists and is linked into the spec:

| Mode | Success Condition |
|------|-------------------|
| **wireframe** | Excalidraw files saved to `mockups/`, `component-inventory.md` generated, state wireframes created for interactive components |
| **attach** | Images stored in `mockups/`, `mockups/README.md` catalog generated, relevant stories updated with `## Visual References` section |
| **capture** | Screenshots saved to `mockups/current/` at all relevant viewports |
| **compare** | Comparison table produced with per-aspect match assessment, recommended fixes listed by visual impact |
| **review** | Existing mockups reviewed and any gaps or inconsistencies reported |

If the mode cannot complete (e.g., no running dev server for capture, no mockups exist for compare), report the blocker and suggest how to unblock rather than producing partial output.

**Suggested next step:** `/create-spec` to formalize designs into a spec, or `/implement-story` if a spec already exists.

**Terminal constraint:** This command produces design artifacts (mockups, wireframes, `component-inventory.md` in `.writ/specs/{spec-name}/mockups/`). Do not offer to implement, build, or execute what was designed. For specification, the user should run `/create-spec`. For implementation, use `/implement-story`. For quick prototyping, use `/prototype`.

## Integration with Writ

| Command | Relationship |
|---------|-------------|
| `/create-spec` | Generates specs that `/design` adds visuals to |
| `/implement-story` | Gate 1 loads mockups; Gate 4.5 runs visual QA |
| `/assess-spec` | Visual complexity adds to story sizing signals |

---

## References

- Standing instructions: [`commands/_preamble.md`](_preamble.md)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)
