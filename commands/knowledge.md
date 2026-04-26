# Knowledge Command (knowledge)

## Overview

Fast-capture for durable project knowledge: small decisions, conventions, glossary terms, and lessons. Speed over ceremony — capture the useful fact in under 2 minutes and get back to work.

Use ADRs for serious architectural choices, research for investigations, and specs for feature contracts. `/knowledge` is for the smaller cross-cutting facts agents and future contributors should not have to rediscover.

## Invocation

| Invocation | Behavior |
|---|---|
| `/knowledge "summary"` | Infer category, ask only for missing required fields, write a conformant entry |
| `/knowledge --category=lessons "summary"` | Use the supplied category and skip category inference |
| `/knowledge --list` | List all knowledge entries by category |
| `/knowledge --list conventions` | List entries in one category |
| `/knowledge --read <slug>` | Read the entry whose filename slug matches `<slug>` |

## Command Process

### Step 1: Project Check

Verify the current project has a `.writ/` directory.

If missing:

```
No `.writ/` directory found.

Run `/initialize` first, then capture this knowledge entry.
```

Stop without creating files.

### Step 2: Route Read-Only Modes

If invoked with `--list [category]`:

1. Validate optional category is one of `decisions`, `conventions`, `glossary`, `lessons`.
2. Scan `.writ/knowledge/{category}/` or all categories.
3. Show filename, title, and first sentence from `## TL;DR`.
4. If no entries exist, say so briefly and stop.

If invoked with `--read <slug>`:

1. Search `.writ/knowledge/{decisions,conventions,glossary,lessons}/` for:
   - Exact filename match: `<slug>.md`
   - Date-prefixed match: `YYYY-MM-DD-<slug>.md`
   - Unique filename containing `<slug>`
2. If zero matches, report `No knowledge entry found for "<slug>".`
3. If multiple matches, list them and ask for the exact slug.
4. Print the selected entry and stop.

### Step 3: Context Capture

For write mode, parse the summary for:

- **Category hints**
  - `lesson`, `failed`, `tried`, `surprised`, `postmortem` -> `lessons`
  - `term`, `means`, `definition`, `glossary` -> `glossary`
  - `convention`, `pattern`, `style`, `always`, `prefer` -> `conventions`
  - `decision`, `chose`, `trade-off`, `because` -> `decisions`
- **ADR warning hints**
  - `architecture`, `substrate`, `irreversible`, `serious blast radius`, `trade-off`
  - If present, warn: `This may belong in an ADR if the blast radius is high. Continue with /knowledge only if this is sub-ADR scale.`
- **File references**
  - Any explicit `.writ/...`, `commands/...`, `agents/...`, `adapters/...`, `scripts/...`, or repo file path
- **Tags**
  - Infer 1-4 lowercase tags from important nouns in the summary and referenced files

If `--category=X` is supplied, validate `X` and use it.

Valid categories:

| Category | Directory | Filename |
|---|---|---|
| `decisions` | `.writ/knowledge/decisions/` | `YYYY-MM-DD-short-slug.md` |
| `conventions` | `.writ/knowledge/conventions/` | `YYYY-MM-DD-short-slug.md` |
| `glossary` | `.writ/knowledge/glossary/` | `term-slug.md` |
| `lessons` | `.writ/knowledge/lessons/` | `YYYY-MM-DD-short-slug.md` |

### Step 4: Light Clarification (Only If Needed)

Ask at most 2 questions in one message. Keep it conversational.

**Question triggers:**

| Signal | Action |
|---|---|
| Category unclear and no `--category` supplied | "Decision, convention, glossary term, or lesson?" |
| Tags missing or too generic | "What 1-3 tags should this carry?" |
| Related artifact implied but not named | "Any file/spec/ADR this should link to?" |

**Skip if obvious:**

- Category can be inferred confidently
- At least one useful tag can be inferred
- No related artifact is needed

### Step 5: Create Entry

Create `.writ/knowledge/` and category subdirectories if they do not exist.

**Date:** Use `npx @devobsessed/writ date` when available; otherwise use the local system date in `YYYY-MM-DD`.

**Slug rules:**

- Lowercase
- Hyphen-separated
- Remove punctuation
- Max 50 characters
- For `glossary`, filename is `{term-slug}.md`
- For other categories, filename is `{YYYY-MM-DD}-{short-slug}.md`

**Template:**

```markdown
---
category: {category}
tags: [{tag1}, {tag2}]
created: {YYYY-MM-DD}
related_artifacts:
  - {repo-relative-path}
---

# {Clear Title}

## TL;DR

{One-sentence summary}

## Context

- {What prompted this}

## Detail

{The actual knowledge. Keep it concise.}

## Related

- [{label}]({path})
```

**Section rules:**

- `related_artifacts` is always present. Use `[]` when empty.
- Omit `## Related` when there are no related artifacts.
- Keep `## Detail` short. If it grows into option analysis, stop and suggest `/research` or `/create-adr`.

### Step 6: Validate Before Writing

Before writing the file, validate the generated entry:

| Field | Rule |
|---|---|
| `category` | Required; one of `decisions`, `conventions`, `glossary`, `lessons`; must match directory |
| `tags` | Required; non-empty array of lowercase slug tags |
| `created` | Required; `YYYY-MM-DD` |
| `related_artifacts` | Required; array, or `[]` |
| filename | Date-prefixed for all categories except `glossary`; glossary has no date prefix |

If validation fails, refuse to write and surface missing fields:

```
Knowledge entry not written.

Missing required field(s): tags, related_artifacts

Add the missing values and run `/knowledge` again.
```

### Step 7: Confirm

```
Created: .writ/knowledge/{category}/{filename}

{Title} ({category}, tags: {tag1}, {tag2})

Back to work!
```

## Example: Fast Capture

```
User: /knowledge --category=conventions "Writ commands should stay adapter-neutral; adapters translate tool mechanics."

Agent:
Created: .writ/knowledge/conventions/2026-04-24-adapter-neutral-commands.md

Writ commands stay adapter-neutral (conventions, tags: adapters, commands)

Back to work!
```

## Completion

This command succeeds when:

1. **Entry file created or read/list operation completed** — write mode creates a markdown file under `.writ/knowledge/{category}/`; read/list modes do not write.
2. **Frontmatter valid** — category, tags, created, and related_artifacts are present and conformant.
3. **Confirmation shown** — write mode returns a terse created-path confirmation.

**Terminal constraint:** This command produces knowledge documentation only. Do not offer to implement, build, or execute what was captured.

---

## References

- Standing instructions: [`commands/_preamble.md`](_preamble.md)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)
