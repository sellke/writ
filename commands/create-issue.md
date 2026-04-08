# Create Issue Command (create-issue)

## Overview

Fast-capture for bugs, features, and improvements mid-development. Speed over completeness — get it documented in under 2 minutes and get back to coding. Good enough beats perfect.

## Invocation

| Invocation | Behavior |
|---|---|
| `/create-issue "description"` | Create issue from description |
| `/create-issue` | Interactive — prompt for description |

## Command Process

### Step 1: Context Capture

Parse the description for:
- **Type hints** — error/crash = bug, "add X" = feature, "make X better" = improvement
- **Current vs expected behavior** — clear or ambiguous?
- **File references** — any mentioned explicitly?

### Step 2: Light Clarification (Only If Needed)

Ask 2-3 questions MAX in a single message. Be conversational, not a checklist — respect that the user is mid-flow. Default to normal priority, medium effort unless clearly otherwise.

**Question triggers:**

| Signal | Action |
|---|---|
| Type unclear | "Is this a bug, feature, or improvement?" |
| Behavior unclear | "What's happening now vs what should happen?" |
| Seems urgent/trivial | "Priority seems [high/low] — that right?" |

**Skip if obvious:**
- Type clear from description ("crashes when..." = bug)
- Behavior already described
- Priority/effort seem normal

### Step 3: Context Search (Only When Helpful)

Use `Grep` to find relevant files when the issue mentions specific components or functionality.

**Search when:**
- User mentions a component/feature name
- Bug in a specific area → find related files
- Feature touches existing code → identify integration points

**Skip when:**
- Self-contained issue (typo fix, config change)
- User already specified files
- New feature with no existing code

Max 3 files in the final issue.

### Step 4: Related Issues Check

Quick scan of `.writ/issues/` with `Glob` for existing issues in the same area or with similar keywords. Include genuinely related ones in the Related Issues section.

**Skip if:**
- No `.writ/issues/` folder exists yet
- No obviously related issues found
- Would slow down capture unnecessarily

### Step 5: Create Issue File

**Folder:** Bug → `.writ/issues/bugs/` | Feature → `.writ/issues/features/` | Improvement → `.writ/issues/improvements/`

**Filename:** `YYYY-MM-DD-{short-slug}.md` — lowercase, hyphens, max 40 chars.

**Template:**

```markdown
# {Clear Title}

> **Type:** {Bug|Feature|Improvement}
> **Priority:** {Low|Normal|High|Critical}
> **Effort:** {Small|Medium|Large}
> **Created:** {YYYY-MM-DD}
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

{One-sentence summary}

## Current State

{What's happening now — bullet points, not paragraphs}

## Expected Outcome

{What should happen — bullet points, not paragraphs}

## Relevant Files

- `{path/to/file.ext}` - {brief reason}

## Related Issues

- [{YYYY-MM-DD-slug}](../type/YYYY-MM-DD-slug.md) - {brief connection}

## Notes

{Risks, dependencies, or additional context}
```

**Section rules:**
- **Related Issues** — omit entirely if none found
- **Notes** — omit entirely if nothing to add
- **Relevant Files** — max 3 files, omit if none identified
- **spec_ref** — always include in the frontmatter block, empty by default; set to the spec path (e.g. `.writ/specs/2026-03-20-fix-login/spec.md`) when the issue is promoted via `/create-spec --from-issue`

### Step 6: Confirm

```
Created: .writ/issues/{type}/YYYY-MM-DD-{slug}.md

{Title} ({type}, {priority} priority, {effort} effort)

Back to work!
```

## Example: Clarification Needed

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

## Completion

This command succeeds when:

1. **Issue file created** — a `.md` file exists in `.writ/issues/{bugs,features,improvements}/` with the `YYYY-MM-DD-{slug}.md` naming convention
2. **Issue content complete** — the file contains Type, Priority, Effort metadata, TL;DR, Current State, and Expected Outcome sections
3. **Confirmation shown** — the user received a brief confirmation with the file path, title, type, priority, and effort

**Suggested next step:** `/create-spec --from-issue` to promote the issue to a full specification.

**Terminal constraint:** This command produces issue documentation (`.writ/issues/{type}/`). Do not offer to implement, build, or execute what was captured. For specification, the user should run `/create-spec --from-issue`. For quick prototyping, use `/prototype`.
