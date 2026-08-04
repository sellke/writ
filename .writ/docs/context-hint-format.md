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

## Parsing Contract (Executable, Not Restated Here)

> **This section changed in Story 4 of `2026-08-03-deterministic-story-substrate`.** Parsing and fetching used to be a prose algorithm restated here for orchestrators to interpret by judgment. That restatement is retired — `scripts/story-context.py` is now the single, tested implementation, and this document is no longer the place to look for parsing behavior.

**Executable contract:** `scripts/story-context.py assemble --story <path> [--budget-bytes N]`

Consumers (currently `/implement-story` Step 2 and `eval-leanness.py`'s `story_context_bytes` measurement) invoke this script rather than parsing `## Context for Agents` by hand. It always exits 0 and prints one JSON object:

```json
{
  "fetched_context": { "error_map_rows": "...", "business_rules": "..." },
  "warnings": ["Context hint references missing content: \"...\" in ..."],
  "bytes": { "error_map_rows": 812, "business_rules": 431, "total": 1243 },
  "truncated": false
}
```

- `fetched_context` — resolved content per category, keyed by the JSON names in the table above (`error_map_rows`, `shadow_paths`, `business_rules`, `experience`)
- `warnings` — every degradation the script hit: missing hints section, malformed category, unresolved reference, absent source file, or budget truncation — never an exception, always a warning
- `bytes` / `truncated` — the byte report and whether the payload was truncated against `--budget-bytes` (relevance-ordered: earlier categories in the table above survive truncation first)

**For the parsing algorithm, category-resolution rules, malformed-input handling, or budget-enforcement logic:** read `scripts/story-context.py` directly — its module docstring and function docstrings are the authoritative, current description, not a paraphrase that can drift out of sync with the code.

**For validating that behavior:** run `python3 -m pytest scripts/tests/test_story_context.py` (unit coverage) or `bash scripts/eval.sh --check=story-context` (scenario + static checks). Both are real, automated, and re-run on every change — this format doc's job is authoring guidance for humans and generators, not a second copy of the parser's behavior for someone to keep in sync by hand.

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
2. Invokes `scripts/story-context.py assemble --story <path> --budget-bytes <N>` (Story 4 — see "Parsing Contract" above; the orchestrator no longer parses `## Context for Agents` itself)
3. Receives resolved content already fetched from spec files in the script's JSON output
4. Delivers targeted content to agents based on role, per the routing table in `commands/implement-story.md` (Architecture Check, Coding, Review, Testing, and Documentation agents each receive a different category subset)

**Orchestrator outputs** (mapped from the script's JSON keys — see `commands/implement-story.md` for the exact mapping):
- `fetched_context` — resolved spec content per category, from the script's `fetched_context` key
- `context_warnings` — missing references, malformed categories, absent sections, and budget truncation, from the script's `warnings` key

> **Fixed in this rewrite:** earlier revisions of this section named `context_hints_parsed` and `context_content_fetched` as the orchestrator's outputs. Neither name ever matched `commands/implement-story.md`'s actual variables (`context_hints` pre-Story-4, `fetched_context`/`context_warnings` throughout) — a documentation drift predating this story, corrected here rather than carried forward.

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

Generation (authoring hints for a new story) and parsing (resolving hints against spec content) sit on opposite sides of the Story 4 boundary now: generation quality is still verified by documentation and golden-file review below, because a generated hint's *relevance* is a judgment call no test suite can make. Parsing is a different claim — `scripts/story-context.py` is real, tested Python, and its correctness is verified by `python3 -m pytest scripts/tests/test_story_context.py` and `bash scripts/eval.sh --check=story-context`, not by golden-file review. See "Parsing Contract" above.

### Generation Validation (Task 1.4)

**Goal:** Verify user-story-generator produces valid context hints

**Method: Golden File Comparison**

1. **Setup:** Create a test spec with known error maps, shadow paths, and business rules
2. **Generate:** Run `/create-spec` on test spec, let user-story-generator create stories
3. **Inspect:** Manually read generated story files' `## Context for Agents` sections
4. **Validate:**
   - [ ] Section header is exactly `## Context for Agents`
   - [ ] Hints use bracketed lists `[item 1, item 2, ...]` and/or extended `spec.md →` / `technical-spec.md` references per this document; bracketed items should match table Operation / path names when using bracket form
   - [ ] Referenced content exists in spec files
   - [ ] Error map row names match table exactly (when using bracketed format)
   - [ ] Shadow path names match table exactly (when using bracketed format)
   - [ ] Business rules are concise summaries, not full duplication
   - [ ] Experience elements reference specific subsections
5. **Document:** Record results in story implementation summary

**Dogfood validation:** Run on this spec itself (Context Engine spec) — stories should include context hints.

> **Retired: "Parsing Validation (Task 1.5)."** This subsection originally documented parsing rules and edge cases for a Story 4 implementer to build against by hand. Story 4 shipped `scripts/story-context.py` instead, with its own unit tests (`scripts/tests/test_story_context.py`, 65 tests) and scenario checks (`bash scripts/eval.sh --check=story-context`) covering every edge case this subsection used to describe in prose — section-missing, empty brackets, malformed brackets, unresolved references, source-file-read failure, and category-prefix typos all have real fixtures now. Read the script and its tests for current parsing behavior; this document no longer restates it.

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
| 2.0 | 2026-08-03 | Story 4 of `2026-08-03-deterministic-story-substrate`: retired the "Parsing Guide" algorithm restatement and "Parsing Validation (Task 1.5)" subsection now that `scripts/story-context.py` is the single tested implementation; fixed stale `context_hints_parsed`/`context_content_fetched` output names in "Integration with Pipeline" to match the command file's actual `fetched_context`/`context_warnings`; removed the stale "no automated test suite" premise from "Validation Strategy." Authoring guidance (Generation Guidelines, Format Structure, Examples, Validation Rules, Manual Usage) is unchanged — this doc's role narrows to authoring; the script now owns parsing. |

## See Also

- `scripts/story-context.py` — the executable parsing/fetching contract (see "Parsing Contract" above)
- `scripts/tests/test_story_context.py` — unit tests for the parsing contract
- `.writ/docs/drift-report-format.md` — Similar structured markdown format
- `.writ/docs/what-was-built-format.md` — Complementary context format for cross-story continuity
- `agents/user-story-generator.md` — Agent that generates these hints
- `commands/create-spec.md` — Command that orchestrates hint generation
- `commands/implement-story.md` — Command that invokes the parsing contract and routes results to agents
