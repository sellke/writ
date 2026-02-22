# Create Issue Command (create-issue)

## Overview

A fast-capture command for documenting bugs, features, and improvements while mid-development. Designed for speed - get the issue documented in under 2 minutes so you can keep working.

## Usage

```bash
/create-issue "brief description of the issue"
/create-issue
```

## Command Process

### Step 1: Quick Context Capture

**When user provides description:**
- Parse the description for type hints (bug, feature, improvement)
- Identify if current vs expected behavior is clear
- Note any file references mentioned

**Gap Analysis (silent):**
- Is the type obvious? (error/crash = bug, "add X" = feature, "make X better" = improvement)
- Is current vs expected behavior clear?
- Is priority/effort obviously different from defaults?

### Step 2: Light Clarification (Only If Needed)

**Rules:**
- Ask 2-3 questions MAX in a single message
- Skip questions where the answer is obvious from context
- Be conversational, not a checklist
- Respect the user's time - they're mid-flow

**Question triggers:**
- Type unclear → "Is this a bug, feature, or improvement?"
- Behavior unclear → "What's happening now vs what should happen?"
- Seems urgent/trivial → "Priority seems [high/low] - that right?"

**Skip if obvious:**
- Type is clear from description ("crashes when..." = bug)
- Behavior is already described
- Priority/effort seem normal

### Step 3: Context Search (Optional)

**Only search when helpful:**
- Use `Grep` to find relevant files if the issue mentions specific functionality
- Skip search for straightforward issues or if user already mentioned files
- Limit to max 3 most relevant files

**Search triggers:**
- User mentions component/feature name → Search for relevant files
- Bug in specific area → Find related files
- Feature touches existing code → Identify integration points

**Skip search when:**
- Issue is self-contained (typo fix, config change)
- User already specified the files
- It's a new feature with no existing code

### Step 4: Check for Related Issues

**Quick scan of existing issues:**
- Use `Glob` to check `.writ/issues/` for existing issues
- Look for issues in the same area or with similar keywords
- If related issues found, include them in the Related Issues section

**Skip if:**
- No `.writ/issues/` folder exists yet
- No obviously related issues found
- Would slow down capture unnecessarily

### Step 5: Create Issue File

**Determine folder:**
- Bug → `.writ/issues/bugs/`
- Feature → `.writ/issues/features/`
- Improvement → `.writ/issues/improvements/`

**Generate filename:**
- Format: `YYYY-MM-DD-{short-slug}.md`
- Slug: lowercase, hyphens, max 40 chars
- Example: `2026-01-21-null-pointer-config-load.md`

**Create markdown with structure:**

```markdown
# {Clear Title}

> **Type:** {Bug|Feature|Improvement}
> **Priority:** {Low|Normal|High|Critical}
> **Effort:** {Small|Medium|Large}
> **Created:** {YYYY-MM-DD}

## TL;DR

{One-sentence summary of what this is about}

## Current State

{What's happening now / current behavior}

## Expected Outcome

{What should happen / desired behavior}

## Relevant Files

- `{path/to/file1.ext}` - {brief reason}
- `{path/to/file2.ext}` - {brief reason}
- `{path/to/file3.ext}` - {brief reason}

## Related Issues

- [{YYYY-MM-DD-slug}](../type/YYYY-MM-DD-slug.md) - {brief connection}

## Notes

{Any risks, dependencies, or additional context - omit section if none}
```

**Section Rules:**
- **Related Issues**: Omit section entirely if no related issues found
- **Notes**: Omit section entirely if nothing to add
- **Relevant Files**: Include up to 3 files max, omit if none identified

### Step 6: Confirm and Done

**Quick confirmation:**
```
Created: .writ/issues/{type}/YYYY-MM-DD-{slug}.md

{Title} ({type}, {priority} priority, {effort} effort)

Back to work!
```

## Core Rules

1. **Speed over completeness** - Good enough beats perfect. Get it captured, move on.
2. **Conversational, not robotic** - Ask what makes sense, not a checklist.
3. **Defaults are fine** - Normal priority, medium effort unless clearly otherwise.
4. **Max 3 files** - Only the most relevant, don't overwhelm.
5. **Bullet points over paragraphs** - Keep it scannable.
6. **Under 2 minutes** - If it's taking longer, you're overcomplicating it.

## AI Implementation Prompt

```
You are executing the create-issue command to quickly capture a bug/feature/improvement.

MISSION: Document the issue fast so the developer can keep working. Under 2 minutes total.

BEHAVIOR:
- Be conversational and brief
- Ask only what's missing (2-3 questions max, in one message)
- Skip obvious things - don't ask type if "crashes when..." clearly means bug
- Default to normal priority, medium effort unless clearly different
- Search codebase only when it adds value, not by default

QUESTION DECISION TREE:
- Type unclear? → Ask
- Type obvious from description? → Don't ask
- Current/expected behavior missing? → Ask  
- Already described? → Don't ask
- Seems urgent (security, data loss)? → Confirm high priority
- Seems trivial (typo)? → Confirm low effort
- Normal complexity? → Use defaults, don't ask

FILE SEARCH RULES:
- User mentions component/feature → Search for relevant files
- Generic issue → Skip search
- User specified files → Use those, skip search
- Max 3 files in final issue

RELATED ISSUES RULES:
- Check .writ/issues/ for existing issues in same area
- Include if genuinely related (same component, similar bug, dependent feature)
- Omit section entirely if no related issues
- Don't slow down capture to do exhaustive search

OUTPUT STRUCTURE:
- Title: Clear, actionable
- TL;DR: One sentence max
- Current State: What's broken/missing (bullets)
- Expected Outcome: What should happen (bullets)
- Relevant Files: Max 3, with brief reason each
- Related Issues: Only if found, omit section otherwise
- Notes: Only if there are risks/dependencies, otherwise omit

FOLDER STRUCTURE:
- .writ/issues/bugs/ - for bugs
- .writ/issues/features/ - for features  
- .writ/issues/improvements/ - for improvements

FILENAME: YYYY-MM-DD-{short-slug}.md (slug: lowercase, hyphens, max 40 chars)

COMPLETION:
- Show filepath created
- One-line summary
- "Back to work!" - keep it light
```

## Examples

### Example 1: Clear Bug

```
User: /create-issue "App crashes when config file is missing"

Agent: Got it - null pointer when config is missing.

Created: .writ/issues/bugs/2026-01-21-crash-missing-config.md

Crash on missing config file (bug, normal priority, medium effort)

Back to work!
```

### Example 2: Needs Clarification

```
User: /create-issue "the login thing is weird"

Agent: Quick clarification:
- Bug (something's broken) or improvement (works but could be better)?
- What's happening vs what you expect?

User: Bug - password field doesn't show dots, shows plain text

Agent: Security bug - password visible in plain text. Checking auth files...

Created: .writ/issues/bugs/2026-01-21-password-field-plain-text.md

Password field shows plain text instead of masked (bug, high priority, small effort)

Back to work!
```

### Example 3: Feature Request

```
User: /create-issue "add dark mode"

Agent: Feature: dark mode toggle. Should this live in settings, or be a quick toggle in the header?

User: Settings page

Agent: Created: .writ/issues/features/2026-01-21-dark-mode-settings.md

Dark mode toggle in settings (feature, normal priority, medium effort)

Back to work!
```

### Example 4: Related Issue Found

```
User: /create-issue "login button doesn't work on mobile"

Agent: Found a related issue about login from last week. Adding cross-reference.

Created: .writ/issues/bugs/2026-01-21-login-button-mobile.md

Login button unresponsive on mobile (bug, normal priority, medium effort)
Related to: 2026-01-15-login-timeout-slow-networks

Back to work!
```

## Integration Notes

This command integrates with Writ by:

1. **File Organization** - Uses `.writ/issues/` with type subfolders
2. **Minimal Tool Usage** - Only `Grep` when helpful, `Glob` for related issues, `Write` for creation
3. **Speed Focus** - No heavy processing, no external integration, just markdown
4. **Complements Other Commands** - Issues captured here can later be expanded into specs (`create-spec`) or inform architectural decisions (`create-adr`)
5. **Cross-Referencing** - Related Issues section connects clustered problems for better context

## Folder Structure

```
.writ/issues/
├── bugs/
│   ├── 2026-01-21-crash-missing-config.md
│   └── 2026-01-21-password-field-plain-text.md
├── features/
│   ├── 2026-01-21-dark-mode-settings.md
│   └── 2026-01-20-export-to-pdf.md
└── improvements/
    ├── 2026-01-21-cache-api-responses.md
    └── 2026-01-19-simplify-nav-menu.md
```

## Future Enhancements

Potential improvements (not in initial version):

- **Issue lifecycle**: Mark issues as resolved, link to PRs
- **Search/filter**: `/issues list --type=bug --priority=high`
- **Upgrade path**: `/issue-to-spec` to expand an issue into a full specification
- **Statistics**: Track issue creation/resolution velocity

But for now: Keep it fast. Capture the issue, get back to coding.
