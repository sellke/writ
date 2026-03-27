# Context Hint Format Specification

> Canonical reference for "## Context for Agents" sections in user story files.
> Any agent generating or parsing context hints MUST follow this format exactly.

## Overview

Context hints are **indexes** that reference specific content in `spec.md` and `technical-spec.md`, not content duplication. They tell the orchestrator which parts of the full specification are relevant to implementing this specific story.

**Core principle:** Story files point to spec content; orchestrator fetches and delivers it. This keeps story files lightweight while giving agents targeted, relevant context.

**When generated:** During `/create-spec` Step 2.6, the `user-story-generator` agent analyzes the full specification and creates context hints for each story.

**When consumed:** During `/implement-story` Step 2 (Load Context), the orchestrator parses hints and fetches referenced content.

## File Location & Lifecycle

**Location:** Each user story file includes a `## Context for Agents` section near the end, after the Definition of Done.

| Event | Action |
|-------|--------|
| Story file created | `user-story-generator` includes context hints section |
| Story implementation begins | `/implement-story` parses hints and fetches content |
| Hint references missing content | Orchestrator logs warning, skips gracefully |
| Manual story creation | Developer can add hints following this format |

## Format Structure

### Required Section Header

```markdown
## Context for Agents
```

### Hint Categories

Context hints are organized into four categories. Each category is optional — only include categories that have relevant content for this story.

#### 1. Error Map Rows

Points to specific rows in the error & rescue map table.

**Format:**
```markdown
- **Error map rows:** [Operation name 1, Operation name 2, Operation name 3]
```

**References:**
- `technical-spec.md` → Error & Rescue Map table → Operation column
- If `technical-spec.md` doesn't exist, can reference `spec.md` → `## 🎯 Experience Design` → `### Error Experience`

**Example:**
```markdown
- **Error map rows:** [Create session, Validate input, Handle Redis failure]
```

**Orchestrator behavior:**
- Parse row names from brackets
- Fetch matching rows from error map table
- Deliver table content to agents

#### 2. Shadow Paths

Points to specific user journey scenarios in shadow path tables.

**Format:**
```markdown
- **Shadow paths:** [Path name 1, Path name 2]
```

**References:**
- `technical-spec.md` → Shadow Paths table → Path name
- If `technical-spec.md` doesn't exist, can reference `spec.md` → `## 🎯 Experience Design` → `### Happy Path Flow`

**Example:**
```markdown
- **Shadow paths:** [User registration flow, Password reset flow]
```

**Orchestrator behavior:**
- Parse path names from brackets
- Fetch matching shadow path rows
- Deliver scenario descriptions to agents

#### 3. Business Rules

Points to specific business rules from the specification contract.

**Format:**
```markdown
- **Business rules:** [Rule summary 1, Rule summary 2]
```

**References:**
- `spec.md` → `## 📋 Business Rules` → Specific rule items

**Example:**
```markdown
- **Business rules:** [Free tier limits (3 projects max), Admin-only workspace deletion, Session expiry (7 days standard, 30 days remember-me)]
```

**Orchestrator behavior:**
- Parse rule summaries
- Fetch full rule text from spec.md
- Deliver to agents with context

#### 4. Experience Elements

Points to specific experience design elements that affect implementation.

**Format:**
```markdown
- **Experience:** [Element name 1 (detail), Element name 2 (detail)]
```

**References:**
- `spec.md` → `## 🎯 Experience Design` → Specific subsections (Entry Point, Happy Path, Moment of Truth, Feedback Model, Error Experience, State Catalog)

**Example:**
```markdown
- **Experience:** [Error feedback model (inline + toast), Empty state (onboarding prompt), Loading behavior (optimistic UI with skeleton)]
```

**Orchestrator behavior:**
- Parse experience element names
- Fetch relevant experience design sections
- Deliver to agents

### Complete Example

```markdown
## Context for Agents

- **Error map rows:** [Create session, Validate input, Handle Redis failure]
- **Shadow paths:** [User registration flow, Password reset flow]
- **Business rules:** [Free tier limits (3 projects max), Admin-only workspace deletion]
- **Experience:** [Error feedback model (inline + toast), Empty state (onboarding prompt)]
```

## Generation Guidelines (for user-story-generator)

When generating context hints for a story:

### Analysis Process

1. **Read story scope** — understand what this story implements
2. **Scan error map** — identify operations this story touches
3. **Scan shadow paths** — identify user journeys this story affects
4. **Scan business rules** — identify rules this story must enforce
5. **Scan experience design** — identify UX elements this story implements

### Selection Criteria

**Include a hint when:**
- Error map row: Story implements or modifies the operation
- Shadow path: Story affects any step in the user journey
- Business rule: Story must enforce or validate the rule
- Experience element: Story implements feedback, loading, error states, or other UX

**Exclude a hint when:**
- Content is not relevant to this story's scope
- Content is general (affects all stories equally)
- Content will be covered by another story (check dependencies)

### Quality Rules

- **Be specific** — "Session creation error handling" not "Error handling"
- **Be concise** — Include only what's relevant, not everything
- **Be accurate** — Reference content that actually exists in spec files
- **Use existing terminology** — Match operation names, path names, rule summaries from the spec exactly

### Graceful Degradation

If the spec doesn't have certain content, adjust references:
- No `technical-spec.md` → reference `spec.md` sections instead
- No error map → reference `spec.md` → `## 🎯 Experience Design` → `### Error Experience`
- No shadow paths → reference `spec.md` → `## 🎯 Experience Design` → `### Happy Path Flow`

## Parsing Guide (for Orchestrators)

When reading context hints to fetch content:

### Parsing Algorithm

1. **Locate section** — find `## Context for Agents` header
2. **Extract categories** — identify which hint categories are present
3. **Parse each category:**
   - Split on category prefix (`**Error map rows:**`, `**Shadow paths:**`, etc.)
   - Extract bracketed content `[item 1, item 2, item 3]`
   - Split on commas to get individual references
   - Trim whitespace from each reference

4. **Fetch referenced content:**
   - Error map rows → read `technical-spec.md`, find matching table rows
   - Shadow paths → read `technical-spec.md`, find matching path scenarios
   - Business rules → read `spec.md`, find matching rule items
   - Experience → read `spec.md`, find matching experience subsections

5. **Handle missing references:**
   - Log warning: `⚠️ Context hint references missing content: [reference]`
   - Skip that hint
   - Continue processing remaining hints
   - Never block the pipeline on missing hints

### Error Handling

| Scenario | Behavior |
|----------|----------|
| `## Context for Agents` section missing | Proceed without hints (legacy story files) |
| Hint category malformed | Skip that category, log warning |
| Referenced content not found | Skip that reference, log warning |
| Empty brackets `[]` | Skip that category (valid: no relevant content) |
| File read failure (`spec.md` or `technical-spec.md`) | Log error, fall back to spec-lite.md |

### Validation Checklist

Before consuming hints, verify:
- [ ] Section header is exactly `## Context for Agents`
- [ ] Each category uses standard prefix format
- [ ] Bracketed content is parseable
- [ ] At least one hint category present (or section intentionally empty)

## Examples

### Minimal Example (Single Category)

```markdown
## Context for Agents

- **Business rules:** [Admin-only workspace deletion, Workspace member limit (5 for free tier)]
```

### Rich Example (All Categories)

```markdown
## Context for Agents

- **Error map rows:** [Create workspace, Invite member, Delete workspace]
- **Shadow paths:** [Workspace creation flow, Member invitation flow]
- **Business rules:** [Admin-only workspace deletion, Workspace member limit (5 for free tier), Workspace name validation (3-50 chars)]
- **Experience:** [Error feedback model (toast notifications), Empty state (workspace creation CTA), Confirmation prompts (delete workspace)]
```

### Example with Spec Content References

When `technical-spec.md` doesn't exist:

```markdown
## Context for Agents

- **Error map rows:** `spec.md` → `## 🎯 Experience Design` → `### Error Experience` (orchestrator warning/skip behavior for bad hints)
- **Shadow paths:** `spec.md` → `## 🎯 Experience Design` → `### Happy Path Flow` (steps 1–3)
- **Business rules:** `spec.md` → `## 📋 Business Rules` → `### Validation Rules`
- **Experience:** `spec.md` → `## 🎯 Experience Design` → `### Entry Point`, `### Moment of Truth`
```

This extended format allows direct file → section references when content isn't in structured tables.

### Example with Empty Hints (Valid)

```markdown
## Context for Agents

- **Error map rows:** []
- **Business rules:** [Session expiry (7 days standard)]
```

Empty brackets are valid — they signal "this category was considered but has no relevant content for this story."

## Validation Rules

Agents generating context hints MUST verify before writing:

| Rule | Check |
|------|-------|
| **Section header present** | Exactly `## Context for Agents` |
| **At least one category** | Include at least one hint category (or explicitly note "No context hints needed for this story") |
| **Bracketed format** | Each category uses `[item 1, item 2, ...]` format |
| **Accurate references** | Referenced content exists in spec files |
| **No content duplication** | Hints reference content, never duplicate it |
| **Concise summaries** | Rule summaries and experience elements are brief (1-2 sentences max each) |

## Integration with Pipeline

### During `/create-spec`

**Step 2.6: Generate User Stories in Parallel**

The `user-story-generator` agent:
1. Receives full `spec.md` and `technical-spec.md` content as parameters
2. Analyzes which spec content is relevant to this story
3. Generates context hints section following this format
4. Includes section at end of story file (after Definition of Done)

**Required parameters for generator:**
- `spec_content` — full text of `spec.md`
- `technical_spec_content` — full text of `technical-spec.md` (or empty string if file doesn't exist)

### During `/implement-story`

**Step 2: Load Context**

The orchestrator:
1. Reads the story file
2. Parses `## Context for Agents` section
3. Fetches referenced content from spec files
4. Delivers targeted content to agents based on role:
   - Coding agents: error map rows, implementation approach
   - Review agents: business rules, experience design
   - Testing agents: shadow paths, edge cases

**Orchestrator outputs:**
- `context_hints_parsed` — structured data with categories and references
- `context_content_fetched` — actual spec content referenced by hints
- `context_warnings` — list of missing or malformed references

### Graceful Degradation

If context hints are incomplete or missing:
1. Orchestrator logs warnings but proceeds
2. Falls back to spec-lite.md for baseline context
3. Pipeline continues normally (degraded context, not broken pipeline)

## Manual Usage

Developers can manually add or edit context hints when:
- Creating stories outside `/create-spec` workflow
- Refining hints after spec updates
- Correcting inaccurate hints

**Process:**
1. Open story file
2. Locate or create `## Context for Agents` section
3. Follow format guidelines above
4. Reference actual content from `spec.md` or `technical-spec.md`
5. Test by running `/implement-story` and checking for warnings

## Validation Strategy

Since Writ is a markdown-based workflow system with no automated test suite, validation follows a documentation + golden file approach:

### Generation Validation (Task 1.4)

**Goal:** Verify user-story-generator produces valid context hints

**Method: Golden File Comparison**

1. **Setup:** Create a test spec with known error maps, shadow paths, and business rules
2. **Generate:** Run `/create-spec` on test spec, let user-story-generator create stories
3. **Inspect:** Manually read generated story files' `## Context for Agents` sections
4. **Validate:**
   - [ ] Section header is exactly `## Context for Agents`
   - [ ] Hints use bracketed format `[item 1, item 2, ...]`
   - [ ] Referenced content exists in spec files
   - [ ] Error map row names match table exactly
   - [ ] Shadow path names match table exactly
   - [ ] Business rules are concise summaries, not full duplication
   - [ ] Experience elements reference specific subsections
5. **Document:** Record results in story implementation summary

**Dogfood validation:** Run on this spec itself (Context Engine spec) — stories should include context hints.

### Parsing Validation (Task 1.5)

**Goal:** Verify orchestrator can parse hints and handle edge cases

**Method: Manual Verification + Edge Case Documentation**

Since Story 1 establishes format only (Story 4 implements orchestrator), document parsing rules and edge cases here:

**Parsing Rules (for Story 4 implementation):**
1. Locate `## Context for Agents` section (search for exact header)
2. Extract lines starting with `- **Error map rows:**`, `- **Shadow paths:**`, etc.
3. Parse bracketed content using regex: `\[(.*?)\]`
4. Split on commas, trim whitespace from each item
5. Use item names to fetch content from spec files

**Edge Cases to Handle:**

| Scenario | Expected Behavior | Test Method |
|----------|-------------------|-------------|
| Section missing entirely | Proceed without hints (legacy story) | Run on story file without section |
| Empty brackets `[]` | Skip category (valid: no content) | Include `- **Error map rows:** []` in test story |
| Malformed brackets `[item 1, item 2` | Skip category, log warning | Create malformed test story, verify warning |
| Referenced content not found | Skip reference, log warning | Reference nonexistent error map row, verify warning |
| File read failure | Fall back to spec-lite.md | Rename spec.md temporarily, verify fallback |
| Category prefix typo | Skip that line, log warning | Use `- **Eror map rows:**`, verify warning |

**Validation Steps:**
1. Create test story files with each edge case
2. Document expected orchestrator behavior for each
3. Story 4 implementer will verify these behaviors
4. Golden file: keep edge case examples in `.writ/docs/context-hint-format.md` (this file)

**Success Criteria:**
- [ ] All edge cases documented with expected behavior
- [ ] Parsing algorithm specified clearly for Story 4 implementer
- [ ] Validation checklist complete (see "Validation Rules" section above)

### Dogfooding Validation (Task 1.6)

**Goal:** Verify context hints are present in this spec's story files

**Method: Manual Inspection**

1. Read `.writ/specs/2026-03-27-context-engine/user-stories/story-1-per-story-context-hints.md`
2. Verify `## Context for Agents` section exists
3. Verify hints reference actual content from `spec.md` and `technical-spec.md`
4. Repeat for stories 2-5

**Expected Results:**
- Story 1: Has context hints section (already present — it's the format example!)
- Stories 2-5: Should have hints when generated via `/create-spec` with updated user-story-generator

**Validation Timing:**
- Story 1: Already present (manually added as format example)
- Stories 2-5: Verify after this story completes and spec is regenerated (if needed)

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-03-27 | Initial format specification |
| 1.1 | 2026-03-27 | Added validation strategy section (Tasks 1.4-1.5) |

## See Also

- `.writ/docs/drift-report-format.md` — Similar structured markdown format
- `.writ/docs/what-was-built-format.md` — Complementary context format for cross-story continuity
- `agents/user-story-generator.md` — Agent that generates these hints
- `commands/create-spec.md` — Command that orchestrates hint generation
- `commands/implement-story.md` — Command that consumes these hints
