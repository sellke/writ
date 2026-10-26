---
name: why
description: "Answer why something in this project is the way it is, from Writ's ledger first, then git history, then connected MCP servers, with a confidence tier on every claim and a Preserve / Change / Avoid / Risk list when a change follows."
problem: "Nobody can ask why the code is the way it is and get an answer from the specs, ADRs, drift logs, and audit notes Writ already wrote, so changes undo decisions their authors recorded."
outcome: "An answer whose every claim carries a confidence tier and cites its source, read from the ledger before git history and git history before any MCP server; when a change follows, a saved record ending in a Preserve / Change / Avoid / Risk section that /create-spec reads."
entry_level: high
exit_criteria:
  - "every claim in the answer carries one of Recorded, Stated, Corroborated, Inferred, or Unknown, and the Sources searched list orders ledger, then git, then MCP"
  - "when a change follows, .writ/research/<YYYY-MM-DD>-why-<slug>.md exists and its last ## section is ## Preserve / Change / Avoid / Risk with ### Preserve, ### Change, ### Avoid, ### Risk in that order"
  - "no file outside .writ/research/ was created or modified, and no git ref or note was written"
---

# Why Command (why)

## Overview

`/why` answers why something in this project is the way it is. It reads Writ's ledger first (audit notes, specs, drift logs, What Was Built records, ADRs, knowledge, issues), then git history, then MCP servers already connected in the session. Every claim carries a confidence tier and cites its source.

When a change follows, the answer ends with a `## Preserve / Change / Avoid / Risk` section, saved under `.writ/research/`, and `/create-spec` reads it during discovery.

Use the cheapest evidence that answers the question. Read the ledger before git and git before any MCP server. Stop sweeping once a `Recorded` claim stands and later history does not contradict it. Spawn no subagents; `/why` runs in the session that invoked it.

## Invocation

| Invocation | Behavior |
|---|---|
| `/why "<question>"` | Answers the question |
| `/why <path>[:<line>]` | Asks why the code at that path, or that line, is the way it is |
| `/why` | Uses the question in the conversation context; with none, asks one question: what do you want to know why about? |

A planned change named in the question ("…before I switch it to Redis") makes Step 6 run. No flags.

## Required Artifacts

None required. Optional: `.writ/` (the ledger), a git repository, and connected MCP servers. Each absence is handled in the step that reads it and named in the answer under Sources searched.

## Confidence Tiers

| Tier | Meaning | Typical evidence |
|---|---|---|
| `Recorded` | A ledger entry states the reason | ADR Decision, spec contract or business rule, `DEV-NNN` entry, What Was Built decision, `refs/notes/writ` digest |
| `Stated` | A person wrote the reason at the time, outside the ledger | Commit message, PR or issue text, chat thread, a code comment written in the same commit as the code |
| `Corroborated` | No source states it; two or more independent sources point to it | A commit that adds a test for the case plus an issue describing the bug |
| `Inferred` | One source suggests it | A commit sequence, a renamed file, a reverted change |
| `Unknown` | No source found | The Sources searched list |

- Code is not evidence of its own intent. The shape of the code shows what it does, never why. A claim resting only on the code is `Unknown`.
- A claim never takes a tier above its strongest evidence.
- When sources disagree, show both, name the newer one, and give the claim the lower tier of the two. A newer ledger entry that says it supersedes the older one settles the conflict at its own tier.

## Command Process

### Step 1: Anchor the Question

Restate the question in one line: the subject and, when named, the planned change. With no question and no conversation context, ask one question, what do you want to know why about, and wait.

Search the project for the files, symbols, and terms the question names.

- Not found: say what you searched for, ask one natural-language question about where the subject lives, and stop. No menu, no answer yet. When the subject is outside the project (a library, a standard, a vendor), point to `/research`.
- Found: list the anchor: paths, line ranges, and the commits from `git log --follow <path>`, `git log -L <start>,<end>:<path>`, or `git blame`. With no git repository or no history for the path, the anchor is paths and terms only (see Step 3).

The anchor locates evidence. A commit's existence is not a reason, and the anchor is never cited as one.

### Step 2: Read the Ledger

Read in this order, and stop reading further ledger sources once a `Recorded` claim answers the question:

1. `git notes --ref=writ show <sha>` for each anchor commit. A `refs/notes/writ` digest names the spec folder, its DEV-IDs, and its `spec.md` and `drift-log.md` paths (format: `.writ/docs/git-notes-audit-format.md`). No notes ref, or no note on the anchor commits: record `Ledger: no refs/notes/writ notes on <shas>` and continue.
2. Specs the notes, the commit messages, or a search for the anchor paths name, in `.writ/specs/` and `.writ/specs/archive/`: `spec.md` (contract, Business Rules, Scope Boundaries), `drift-log.md` (`DEV-NNN` entries), and each story's `## What Was Built` (`### Implementation Decisions`, `### Deviations from Spec`).
3. ADRs under `.writ/decision-records/` that name the anchor paths or the subject's terms. Follow `Superseded by` and `Amends` banners to the newest entry.
4. `.writ/knowledge/` and `.writ/issues/` entries that mention the subject, and `.writ/research/` documents those entries cite.

A cited path that does not resolve is skipped, kept out of the claims, and listed under Sources searched. No `.writ/` in the project: record `Ledger: none in this project` and go to Step 3.

### Step 3: Read Git History

Always run this step: it is the stale-ledger check.

- Read the messages and bodies of the anchor commits and their merge commits.
- Run `git log --grep=<term>` for the subject's terms.
- Note every PR or issue number a message cites. A number git cannot resolve is a lead for Step 4.
- When a commit touched the anchor after the date of the `Recorded` entry, the claim keeps its tier and carries a line that the entry may describe an earlier shape.

When the project is not a git repository, or the path has no history, record `Git: not a git repository` (or `no history for <path>`) under Sources searched and read the ledger by path and subject terms only.

### Step 4: Read MCP Servers When Needed

Run this step only when the strongest claim after Steps 2 and 3 is below `Stated`. Otherwise record `not read: the ledger answered at Recorded` (or `git answered at Stated`) and go to Step 5.

Read the PRs and issues the git messages cited, then search for the subject, through MCP servers already connected in the session (code host, issue tracker, chat, docs) or the code host's CLI when it is installed and signed in. Make read calls only. Never prompt to connect, install, or authorize a server.

No server connected: record `MCP: none connected`. A call that fails or is refused: name the server and the reason under Sources searched and continue without it.

### Step 5: Answer

Print the answer template below. The `**Answer:**` line ends with the strongest tier reached. Every claim gets a tier and evidence: a path with its section heading, a commit SHA, or a server and item id. Name every source searched that held nothing. An `Unknown` answer names what was searched.

```markdown
## Why: <subject>

**Answer:** <one or two sentences> — <tier>

### Claims

| # | Claim | Tier | Evidence |
|---|---|---|---|
| 1 | <claim> | Recorded | `.writ/decision-records/adr-<NNN>-<slug>.md` § Decision |
| 2 | <claim> | Stated | commit `<sha>` message |

### Sources searched

- Ledger: <what was read>; nothing in <what held nothing>
- Git: <commits read>; <stale-ledger line when it applies>
- MCP: <servers read>, or "not read: the ledger answered at Recorded", or "none connected"
```

### Step 6: Hand Off a Change

Run this step only when a change follows: the request names a planned change, or the user names one after the answer. Without one, print one line and write nothing: if you plan to change this, name the change and `/why` adds the Preserve / Change / Avoid / Risk list.

When a change follows, save the record to `.writ/research/<YYYY-MM-DD>-why-<slug>.md`. The slug is kebab-case from the subject, at most six words. Create `.writ/research/` if it is absent. If the path exists, append `-2`, `-3`, and so on; never overwrite a record. The record is the header, the answer from Step 5, and the handoff section, in that order. The handoff is the record's last `##` section:

```markdown
# Why: <subject>

> **Asked:** <YYYY-MM-DD>
> **Subject:** <anchor paths and terms>
> **Change:** <the planned change>
> **Question:** <the question as asked>

<the answer, from ## Why: through ### Sources searched>

## Preserve / Change / Avoid / Risk

### Preserve
- <what the change must keep, and why> — <tier>, <source>

### Change
- <what the change alters> — <tier>, <source>

### Avoid
- <an approach the history shows failed or was rejected> — <tier>, <source>

### Risk
- <what could break> — <tier>, <source>
```

Keep the heading and the four subsections exactly as shown, in that order. An empty subsection reads `- none found`. Print the saved path and the next step: `/create-spec "<the change>"`, whose Step 1.2 reads the section.

## Integration with Writ

| Command | Relationship |
|---|---|
| `/writ` | Routes why-or-how questions about the project here |
| `/research` | Takes questions about something outside the project (a library, a standard, a vendor); `/why` points there when the subject is not in the project |
| `/create-spec` | Step 1.2 reads the handoff section |
| `/create-adr` | Finds saved why records in `.writ/research/` during its research search |
| `/knowledge` | Records a reason the user supplies after an `Unknown` or `Inferred` answer |

## Completion

This command succeeds when the answer printed with a tier on every claim and the Sources searched list in source order (ledger, git, MCP), and, when a change followed, the saved record exists with the handoff section last. An `Unknown` answer with its sources searched is a valid result.

`/why` is read-only apart from the saved record: it writes no git ref, note, or commit, edits no ledger entry, and makes only read calls to MCP servers.

**Terminal constraint:** `/why` explains and hands off. It does not change code, write a spec, record an ADR or knowledge entry, or write git notes. For the change, the user runs `/create-spec` or `/prototype`.

## References

- Standing instructions: [`commands/_preamble.md`](_preamble.md)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)
- Audit note format: [`.writ/docs/git-notes-audit-format.md`](../.writ/docs/git-notes-audit-format.md)
- What Was Built format: [`.writ/docs/what-was-built-format.md`](../.writ/docs/what-was-built-format.md)
