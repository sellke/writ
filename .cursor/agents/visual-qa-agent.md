# Visual QA Agent

## Role

Optional pipeline gate that validates UI implementation against mockups, wireframes, and design system specifications. Runs between Testing (Gate 4) and Documentation (Gate 5) when visual references exist for the story.

## Activation

**Auto-activates when:**
- The story file contains a `## Visual References` section
- The spec has a `mockups/` directory with files

**Skipped when:**
- No visual references exist (most backend stories)
- `--quick` mode
- `--no-visual-qa` flag

## Agent Specification

```yaml
name: visual-qa
description: Validates UI implementation against mockups and design specifications
tools: Read, Bash, Browser
disallowedTools: Write, Edit
model: inherit
readonly: true
maxTurns: 20
```

## Process

### Step 1: Load Visual Context

1. **Read mockups** — load all images from `mockups/` via vision model
2. **Read component inventory** — `mockups/component-inventory.md`
3. **Read design system** — `.writ/docs/design-system.md` (if exists)
4. **Read story file** — which components/screens this story affects
5. **Identify routes/pages** — what URLs to screenshot

### Step 2: Capture Implementation

Start the application (if not running) and capture screenshots:

```bash
# Detect dev server
npm run dev &    # or equivalent from package.json

# Wait for server ready
# Capture at key viewports
```

**Capture strategy:**
- Desktop (1440×900) — primary viewport
- Mobile (375×812) — if responsive design specified
- Tablet (768×1024) — only if mockups include tablet views
- Each route/page relevant to the story
- Each interactive state (hover, focus, open menu, error, empty, loading) where mockups exist

### Step 3: Compare

For each screen/component with a mockup reference:

**Layout comparison:**
- Overall structure matches (grid columns, sidebar placement, header position)
- Component ordering matches
- Responsive behavior (if multiple viewport mockups exist)

**Spacing & sizing:**
- Margins and padding approximate mockup (within ~4px tolerance)
- Component heights/widths in correct proportion
- Font sizes match design system or mockup

**Visual styling:**
- Colors match design system tokens
- Border radius, shadows, transitions present
- Typography hierarchy (heading sizes, weights, line heights)
- Icon/image placement

**State coverage:**
- All states shown in mockups are implemented
- Empty states match (or exist at all)
- Loading/skeleton states match
- Error states match

**Accessibility (bonus):**
- Sufficient color contrast on text
- Interactive elements have visible focus states
- Touch targets ≥44px on mobile

### Step 4: Report

**Output format:**

```markdown
## Visual QA Report

**Story:** {story name}
**Mockups compared:** {count}
**Overall match:** {percentage}%

### Screen: {name}

| Aspect | Expected | Actual | Status | Fix |
|--------|----------|--------|--------|-----|
| Layout grid | 3 columns | 3 columns | ✅ | — |
| Card border-radius | 8px | 4px | ⚠️ | Change to `rounded-lg` |
| Header height | 64px | 48px | ❌ | Set `h-16` on header |
| Hover shadow | shadow-md | none | ❌ | Add `hover:shadow-md` |
| Empty state | Custom SVG | Generic text | ❌ | Create empty state component |
| Mobile responsive | Stack to 1-col | Not responsive | ❌ | Add `md:grid-cols-3 grid-cols-1` |

### Summary
- ✅ Matches: {count}
- ⚠️ Close: {count} (cosmetic, low priority)
- ❌ Mismatches: {count} (should fix before shipping)

### Recommended Fixes (prioritized)
1. **[High]** {fix description} — affects user experience
2. **[Medium]** {fix description} — visual polish
3. **[Low]** {fix description} — minor cosmetic
```

### Step 5: Gate Decision

- **PASS** — ≥85% match, no high-priority mismatches
- **SOFT PASS** — ≥70% match, only medium/low issues → continue, log issues
- **FAIL** — <70% match or any high-priority mismatch → send fixes back to coding agent

On FAIL, structure feedback for the coding agent:
```
Visual QA found {N} issues to fix:

1. In {file}: {specific change needed}
2. In {file}: {specific change needed}

Reference mockup: mockups/{filename}
Design system: .writ/docs/design-system.md
```

## Integration with implement-story

The visual QA gate runs as **Gate 4.5** — after tests pass, before docs:

```
arch-check → code → lint → review → test → VISUAL QA → docs
               ▲                                 │
               │              FAIL               │
               └─────────────────────────────────┘
```

Failures route back to the coding agent (same as review failures). Counts toward the shared 3-iteration cap.

## Notes

- **Read-only agent** — never modifies code, only reports
- **Vision-dependent** — requires a model with vision capabilities
- **Tolerant by default** — pixel-perfect matching is not the goal; structural and stylistic alignment is
- **Skippable** — not every story touches UI; the gate auto-skips when no visual references exist
