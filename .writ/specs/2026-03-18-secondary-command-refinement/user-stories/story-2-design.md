# Story 2: design.md Refinement

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer
**I want to** refine design.md to A-grade quality
**So that** the four design modes are clear and focused, with templates replaced by principles that trust the AI's judgment

## Acceptance Criteria

1. **Given** the refined design.md, **when** an AI agent reads Mode A (wireframe), **then** it learns the non-obvious conventions (gray fills for placeholder media, dashed borders for conditional elements, red annotations for interaction notes, "label everything — the coding agent reads these labels") and pipeline integration without needing Excalidraw JSON schema or component primitive lists.

2. **Given** the refined design.md, **when** an AI agent processes mockups in Mode B, **then** it understands what component-inventory and mockups/README should contain and their purpose, but receives principles rather than full markdown templates.

3. **Given** the refined design.md, **when** an AI agent uses Mode C (capture) or Mode D (compare), **then** it has clear, compressed guidance (~10–15 lines each) that references browser MCP for screenshots and preserves the comparison table format for Mode D, without bash/Playwright scaffolding.

4. **Given** the refined design.md, **when** an AI agent extracts a design system from mockups, **then** it knows the concept and categories to extract (colors, typography, spacing, components) without a full markdown template.

5. **Given** the refined design.md, **when** an AI agent reads the full file, **then** the modal structure (wireframe / attach / capture / compare / review) remains the organizing spine, all five modes are clearly distinct, and the Tool Integration table is absent.

## Implementation Tasks

1. **Cut removals** — Remove the Tool Integration table (lines 368–377), Excalidraw JSON schema (lines 71–91), and component primitive list (lines 93–99). Remove bash code examples in Mode C (lines 228–243).

2. **Replace component-inventory template** — Replace the full template (lines 132–150) with principles: what it should contain (components with type, states, notes; design tokens referenced), and its purpose (coding agent reads it at Gate 1 for component structure).

3. **Replace mockups/README template** — Replace the full template (lines 191–207) with principles: catalog purpose (index all visual references), key fields (file, description, screen/component, stories; design notes from analysis).

4. **Replace design system extraction template** — Replace the full template (lines 309–341) with principles: concept (auto-generate when design-system.md doesn't exist), categories to extract (colors, typography, spacing, components with tokens).

5. **Compress Mode C** — Reduce Mode C (lines 219–253) to ~10–15 lines: detect if app is running, use browser MCP to capture screenshots at key viewports, store in mockups/current/ with target/ for mockups. No bash or Playwright code.

6. **Compress Mode D** — Reduce Mode D (lines 256–288) to ~10–15 lines: keep the comparison table format (Aspect | Mockup | Implementation | Match) and recommended fixes structure; cut surrounding scaffolding. Clarify that browser MCP captures current state.

7. **Compress Mode A component states** — Keep the concept of generating multiple wireframes for interactive components (default, loading, empty, error, hover/active). Compress the naming convention to a single line: `{component}-{state}.excalidraw`.

## Notes

**Technical considerations:**
- Pipeline integration (Gate 1 loads mockups, visual-qa-agent for Gate 4.5) must remain explicit — it's non-obvious.
- Wireframe conventions (375×812 mobile, 1440×900 desktop; gray fills, dashed borders, red annotations) are the highest-value content in Mode A.
- The comparison table format in Mode D produces actionable output — preserve its structure.

**Risks:**
- Modes losing clarity when compressed — validate that each mode still has a clear purpose and flow.
- Over-compression of Mode C/D may leave the agent unsure how to capture screenshots — ensure browser MCP is explicitly referenced.

**Watch for:**
- Cross-references to `agents/visual-qa-agent.md` must remain intact.
- Story file `## Visual References` section format (lines 339–342) is used by coding agent — keep the pattern, not necessarily the full example.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Line count within target range (~200 ±10%)
- [ ] No functional capability lost
- [ ] All five modes still clearly distinct
