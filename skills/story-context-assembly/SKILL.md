---
name: story-context-assembly
description: "Assemble the targeted context payload each pipeline agent receives — parsed hints, knowledge entries, and role-specific spec-lite sections."
disable-model-invocation: true
status: candidate
---

# Story Context Assembly

## Purpose

Turn a story file and its spec-lite into the **targeted** context each agent
actually needs, instead of handing every agent the whole spec. Three payloads:
`fetched_context` (spec content resolved from the story's context hints),
`knowledge_context` (durable project knowledge matched by keyword), and per-role
`spec_lite_for_*` sections. Every one degrades to something usable rather than
halting when its source is missing. Who receives them, and when, belongs to the
consumer.

## When to Use

- Before dispatching work on a single story to agents that should see spec
  detail relevant to *this* story rather than the whole document.
- When a project keeps durable knowledge entries under `.writ/knowledge/` that
  should reach agents without a human pasting them in.
- When a `spec-lite.md` uses the per-role section format and each role should
  receive only its own section.

## How to Apply

### 1. Fetched context — delegate, never re-derive

> **Authoring reference:** `.writ/docs/context-hint-format.md` — the hint syntax,
> for anyone writing or reviewing a `## Context for Agents` section.

`scripts/story-context.py` is the **sole** implementation that parses a story's
`## Context for Agents` hints and fetches the referenced content. Invoke it;
never restate its parsing algorithm in prose — a second prose copy is how the
two diverge.

```bash
python3 scripts/story-context.py assemble --story <story-file-path> --budget-bytes 21000
```

`21000` is `FETCHED_CONTEXT_BUDGET_BYTES`. **Read the constant's current value
from the script and prefer it over any number written in prose** — the script,
not its callers, owns the derivation.

The script **always exits 0** and prints one JSON object:

```json
{
  "fetched_context": { "error_map_rows": "...", "business_rules": "..." },
  "warnings": ["..."],
  "bytes": { "error_map_rows": 812, "business_rules": 431, "total": 1243 },
  "truncated": false
}
```

Map its keys to output variables:

- `fetched_context` → **`fetched_context`** — pass through unchanged, keyed by
  category.
- `warnings` → **`context_warnings`** — pass through verbatim. This already
  includes the informational "no hints section" log, every parse/fetch warning,
  and — when `truncated` is `true` — the truncation warning naming actual vs.
  budget bytes. **No separate truncation handling is needed**; the script
  embeds it.
- `bytes` → informational byte report for the invocation only; not consumed
  anywhere else beyond logging.

The script handles unresolvable references and unreadable spec files itself.
Guard the **invocation** separately:

| Failure Mode | Detection | Behavior |
|----------|---------------|-----------------|
| Script missing | `scripts/story-context.py` does not exist, or the invocation cannot start | Warn: `⚠️ story-context.py not found — proceeding with spec-lite only`; set `fetched_context` to `{}` and continue |
| Non-zero exit | Process exit code is not `0` | Warn: `⚠️ story-context.py exited non-zero — proceeding with spec-lite only`; set `fetched_context` to `{}` and continue |
| Malformed stdout | stdout is not valid JSON, or lacks the `fetched_context`/`warnings` keys | Warn: `⚠️ story-context.py produced unparseable output — proceeding with spec-lite only`; set `fetched_context` to `{}` and continue |

**A broken assembler degrades context; it never halts the work.** In every row
above, proceed on `spec-lite.md` alone.

### 2. Knowledge context — extract, score, cap

Load matching `.writ/knowledge/` entries so agents inherit durable project
knowledge without anyone prompting for it. Do this **after** fetched context, so
hint-surfaced paths are available as keywords.

**Keyword extraction.** Take candidates from the story title, the story file's
`## Context for Agents` block, and file paths in scope from implementation
tasks, boundary candidates and context hints. Then normalize, in order:

1. Lowercase.
2. Split path segments and hyphenated/slashed terms.
3. Drop common stop words (`the`, `and`, `story`, `file`, `task`, `spec`, etc.).
4. Keep meaningful tokens of **3+ characters**, plus exact path fragments such
   as `commands/implement-story.md`.

**Search and score.**

1. If `.writ/knowledge/` does not exist, skip silently.
2. Grep `.writ/knowledge/` for keyword matches against frontmatter tags, titles,
   TL;DR text and body content.
3. Score each match: **+3** tag match · **+2** title or filename match · **+1**
   body/content match · **+1** related-artifact path matching a file in scope.
4. Prefer categories by consuming role:
   - Architecture review: `decisions/`, `conventions/`, then other matches.
   - Coding: all categories, with `conventions/` and `glossary/` boosted.
   - Code review: `lessons/`, `decisions/`, then other matches.
5. Assemble one shared `knowledge_context` markdown block capped at **~2KB**:

   ```markdown
   ## Loaded Knowledge Entries

   ### .writ/knowledge/conventions/2026-04-24-date-prefixed-slugs.md
   - Category: conventions
   - Tags: filenames, markdown, writ-artifacts
   - TL;DR: Use `YYYY-MM-DD-short-slug.md` for dated Writ artifacts...
   ```

6. If the block exceeds 2KB, **keep higher-scoring entries first and truncate
   lower-scoring details before dropping whole entries.**

**Graceful degradation:**

| Scenario | Behavior |
|----------|----------|
| `.writ/knowledge/` missing | Silent no-op; set `knowledge_context` to empty string |
| No keyword matches | Silent no-op; set `knowledge_context` to empty string |
| Entry has malformed frontmatter | Skip that entry and log `⚠️ Knowledge entry skipped: malformed frontmatter in {path}` |
| Context exceeds 2KB | Truncate by relevance score and log `ℹ️ knowledge_context truncated to 2KB` |

The two silent rows are **deliberate** — an absent knowledge directory is a
normal project shape, not a defect. Do not "improve" either into a warning.

**Output variable:** `knowledge_context` — an optional markdown block of loaded
entries; the **empty string** when no relevant entries were found.

### 3. Role-specific spec-lite sections

Parse `spec-lite.md` into role-specific sections for targeted delivery:

- `spec_lite_for_coding` — content of the `## For Coding Agents` section, from
  its header to the next `---` or `##` heading.
- `spec_lite_for_review` — content of the `## For Review Agents` section.
- `spec_lite_for_testing` — content of the `## For Testing Agents` section.

Which role receives which section, and what supplementary context travels with
it, is the consumer's routing decision.

**Graceful degradation:**

- `spec-lite.md` does not use the agent-specific format (legacy specs without
  `## For {Role} Agents` headers) → use **full** spec-lite content for **all**
  roles.
- A specific section is missing → fall back to full spec-lite content for that
  role and log:
  `⚠️ Spec-lite.md missing "## For {Role} Agents" section — using full content`
- `fetched_context` is empty (no hints parsed, or all references missing) →
  the role receives its spec-lite section only. That is still an improvement
  over the full file for non-legacy specs.
