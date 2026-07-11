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
| `/knowledge --consolidate` | Propose merges, surface contradictions, and flag stale entries across the ledger — dry-run first, write only on explicit approval |

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

If invoked with `--consolidate`:

Consolidation is a **gated write** mode. Its default behavior is read-only (dry-run); only an explicit, approved apply mutates files. The single principle is **merge, never append** — a log grows unbounded, a merged document stays searchable. The deliverable is a reviewable working-tree diff, never a silent mutation.

1. **Dry-run.** Run the reducer in its default non-destructive mode:

   ```bash
   python3 scripts/knowledge-consolidate.py --dry-run
   ```

   Use `--json` when you need the machine-readable proposal to drive presentation. The reducer scans all four categories, reusing the substrate's `_tokens` + Jaccard duplicate detection. Dry-run writes no file.

2. **Present the proposal.** Show each finding with the evidence that triggered it:
   - **Merges** — the canonical (surviving) entry, the entries it would replace, and the duplicate signal (token overlap). Preview the unified diff.
   - **Contradictions** — both entries and their conflicting assertions, presented as a **decision for the human**. The reducer proposes no resolution; never auto-resolve.
   - **Stale flags** — the entry and the observable signal (superseded, all `related_artifacts` missing, or dominated). Never cite age alone.
   - **Skipped** — any malformed entry with its named reason. It is neither rewritten nor dropped.

   If the proposal is empty, report "Nothing to consolidate." and stop. This is a valid no-op that changes no file.

3. **Approval gate.** Use `AskQuestion` to gate every write. Approval may be per-proposal or per-category. If approval is declined, write nothing — the ledger is unchanged. There is no path from `--consolidate` to a write that skips this gate.

4. **Apply approved merges.** On approval, run:

   ```bash
   python3 scripts/knowledge-consolidate.py --apply
   ```

   This writes the canonical entry with `replaces: [...]` and rewrites each merged-away entry into a tombstone carrying `superseded_by: <canonical-slug>` (glossary terms are always tombstoned, never deleted). Report the exact files changed and the lineage recorded. The command does **not** commit; it leaves a reviewable working-tree diff for the human to inspect and PR.

5. Contradiction pairs and stale flags are advisory. Applying merges never resolves a contradiction or retires a stale entry; those remain for an explicit, separate human decision.

Stop after reporting the applied diff (or the declined no-op). Consolidation produces knowledge docs and diffs only.

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

**Date:** Use `npx @sellke/writ date` when available; otherwise use the local system date in `YYYY-MM-DD`.

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

## Phase-Close Writeback

`/implement-phase` closes a phase by proposing candidate lessons drawn from the
phase report and per-spec drift logs. Knowledge writeback then applies the
evidence-bound gates (see [`.writ/docs/phase-execution-state-format.md`](../.writ/docs/phase-execution-state-format.md) → Knowledge Writeback) using the executable evaluator `scripts/phase-state.py knowledge-writeback`:

- A candidate is written to `.writ/knowledge/lessons/` only if it generalizes beyond one spec, cites a supporting artifact or repeated drift, is below ADR blast radius, and is **not a substantive duplicate** of an existing entry.
- **Substantive** deduplication compares *meaning* against every existing knowledge entry — not filenames or exact text — and is conservative: a high overlap with any existing entry is treated as a duplicate to avoid noisy repeated writeback.
- Rejected and no-op outcomes are first-class successes: no qualifying candidate writes nothing and reports the rejected candidates with terse reasons.

## Completion

This command succeeds when:

1. **Entry file created, read/list completed, or consolidation resolved** — write mode creates a markdown file under `.writ/knowledge/{category}/`; read/list modes do not write; `--consolidate` either reports a no-op, leaves a declined ledger unchanged, or applies approved merges as a reviewable working-tree diff.
2. **Frontmatter valid** — category, tags, created, and related_artifacts are present and conformant; consolidation lineage (`replaces` / `superseded_by`) is written bidirectionally.
3. **Confirmation shown** — write mode returns a terse created-path confirmation; `--consolidate` reports the files changed and the lineage recorded.

**Terminal constraint:** This command produces knowledge documentation and diffs only. Do not offer to implement, build, or execute what was captured or consolidated.

---

## References

- Standing instructions: [`commands/_preamble.md`](_preamble.md)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)
