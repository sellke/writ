# Technical Spec: Why Command

> Spec: [`../spec.md`](../spec.md) · Research: [`2026-10-19-writ-vs-pstack-research.md`](../../../research/2026-10-19-writ-vs-pstack-research.md) F4 · ADR: [ADR-030](../../../decision-records/adr-030-contract-verifier-boundary-front-door.md)

## Current State (audit, 2026-10-25)

Measured on branch `phase/15-code-level-rigor` at `7f7f991`. Re-measure each number before editing; stop and report a mismatch.

- **Commands.** 34 files in `commands/`: 33 commands plus `_preamble.md`. No command answers "why is this like this?" from the ledger. `/research` is external-first: its exit criteria name `.writ/research/<YYYY-MM-DD>-<topic>-research.md` and source URLs.
- **Ledger locations.**
  - `refs/notes/writ`: audit digests attached by `/ship` and `/release` (format in `.writ/docs/git-notes-audit-format.md`). Each digest names the spec folder id, its DEV-IDs, and the `spec.md` and `drift-log.md` paths. Read with `git notes --ref=writ show <sha>` or `git log --notes=writ`.
  - `.writ/specs/<id>/` and `.writ/specs/archive/<id>/`: `spec.md` (contract, 📋 Business Rules, Scope Boundaries), `drift-log.md` (`DEV-NNN` entries), `user-stories/story-*.md` → `## What Was Built` → `### Implementation Decisions` and `### Deviations from Spec` (format in `.writ/docs/what-was-built-format.md`).
  - `.writ/decision-records/adr-*.md`: Status, Decision, Considered Options, `Superseded by` / `Amends` banners.
  - `.writ/knowledge/{decisions,conventions,lessons,glossary}/`, `.writ/issues/`, `.writ/research/`.
- **Front door.** `commands/writ.md` § Routing Rules, fifth row: `| Asks why something is the way it is, or how something works | `/research` (`/why` takes this route when it ships) |`. § Step 2 bullet: `- **Why or how.** Route `/research`. The confirmation notes that `/why` takes this route when it ships.` `scripts/tests/test_front_door.py` pins `ROUTES[4] == ("/research", None)` and asserts `/why` appears in that cell.
- **Prompting guide.** `.writ/docs/prompting-guide.md` § A why or how question: `Route: `/research` (`/why` replaces it when it ships)`. `scripts/tests/test_prompting_guide.py` checks the recipe's route and asserts `/why` appears in it.
- **`/create-spec`.** Phase 1 runs Step 1.0, Step 1.1 (Initial Context Scan), Step 1.3 (Discovery Conversation). There is no Step 1.2. File size 38,614 bytes; `KNOWN_OVER_BUDGET["commands/create-spec.md"] = 13654` (38,614 − 24,960).
- **Registration surfaces.** `.writ/manifest.yaml` `commands:` (sorted by name; `why` goes between `verify-spec` and `writ`); `SKILL.md` (`bash scripts/gen-skill.sh`); `claude-code/CLAUDE.md`, `codex/AGENTS.md.template`, `cursor/plugin/`, `plugins/writ/` (all `python3 scripts/gen-platform-trees.py`); `README.md` § Commands → Planning & Specification; `adapters/cursor.md` § Directory Structure (count comment `(33)`); `commands/status.md` slash allowlist and § Maintainer Note: Command Allowlist bare list; `.writ/docs/model-tiers.md` `high` row (`(16)`). The repository's own `CLAUDE.md` and `AGENTS.md` list no commands and need no edit.
- **Tests that move.** `scripts/tests/test_front_door.py` (`CURSOR_COUNT = "(33)"`, `ROUTES`), `scripts/tests/test_prompting_guide.py` (`RECIPES`), `scripts/tests/test_platform_neutral_names.py` (`test_cursor_tree` compares the tree to the manifest; passes once both change together), `scripts/tests/test_governor_enforcement.py` (`KNOWN_OVER_BUDGET`).
- **MCP.** No adapter maps an MCP capability. `commands/prototype.md` and `commands/writ-design.md` name MCP servers in plain prose.

## Error & Rescue Map

| Operation | Failure | Rescue | User sees |
|---|---|---|---|
| Locate the subject | No file, symbol, or term in the question matches the project | Stop before reading any source | What was searched for, and one natural-language question about where it lives |
| Find anchor commits | Not a git repository, or the path has no history | Continue with the ledger by path and subject terms | `Git: not a git repository` (or `no history for <path>`) under Sources searched |
| Read git notes | `refs/notes/writ` absent, or no note on the anchor commits | Continue with specs, ADRs, and knowledge found by path and term search | `Ledger: no refs/notes/writ notes on <shas>` |
| Read ledger files | `.writ/` absent | Continue with git history | `Ledger: none in this project` |
| Read ledger files | A cited spec, ADR, or record path does not resolve | Skip it and keep the citation out of the claims | The unresolved path listed under Sources searched |
| Read git history | A commit message cites a PR or issue number that git cannot resolve | Treat the number as a lead for Step 4 | The number listed as an unread lead |
| Read MCP server | No server connected, or the call fails or is refused | Continue without it; never prompt to connect or authorize | `MCP: none connected`, or the server name and the failure reason |
| Save why record | The dated path exists | Append `-2`, `-3`, and so on | The final path |
| Save why record | `.writ/research/` absent | Create the directory | The final path |
| Find handoff in create-spec | No section in the conversation, the named file, or a matching record | Skip Step 1.2 silently | Nothing |
| Find handoff in create-spec | The named file lacks the heading | Say so in the context summary and continue | One line naming the file |

## Shadow Paths

| Path | Flow | Outcome |
|---|---|---|
| Happy path | Anchor → ledger → git → answer → handoff when a change follows | A `Recorded` or `Stated` answer; a saved record only when a change follows |
| Nil input | `/why` with no question and no conversation context | One question: what do you want to know why about? |
| Empty input | A question naming nothing the project contains | What was searched for, then one natural-language question |
| Upstream error | An MCP call fails | The failure named under Sources searched; the answer stands on ledger and git |
| No ledger | A project without `.writ/` | Git history and MCP only; the answer says the ledger is absent |
| Stale ledger | The anchor changed after the ledger entry | The claim keeps its tier and carries a line that the entry may describe an earlier shape |
| Conflicting sources | Ledger and later history disagree | Both shown, newer named, claim at the lower tier |
| Change follows | The request names a planned change | The handoff section and the saved record path |

## `commands/why.md` Skeleton

```markdown
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
## Invocation
## Required Artifacts
## Confidence Tiers
## Command Process
### Step 1: Anchor the Question
### Step 2: Read the Ledger
### Step 3: Read Git History
### Step 4: Read MCP Servers When Needed
### Step 5: Answer
### Step 6: Hand Off a Change
## Integration with Writ
## Completion
## References
```

### Invocation

| Invocation | Behavior |
|---|---|
| `/why "<question>"` | Answers the question |
| `/why <path>[:<line>]` | Asks why the code at that path, or that line, is the way it is |
| `/why` | Uses the question in the conversation context; with none, asks one question |

A planned change named in the question ("…before I switch it to Redis") makes Step 6 run. No flags.

### Required Artifacts

None required. Optional: `.writ/` (the ledger), a git repository, connected MCP servers. Each absence degrades per § Error & Rescue Map and is named in the answer.

### Confidence Tiers

| Tier | Meaning | Typical evidence |
|---|---|---|
| `Recorded` | A ledger entry states the reason | ADR Decision, spec contract or business rule, `DEV-NNN` entry, What Was Built decision, `refs/notes/writ` digest |
| `Stated` | A person wrote the reason at the time, outside the ledger | Commit message, PR or issue text, chat thread, a code comment written in the same commit as the code |
| `Corroborated` | No source states it; two or more independent sources point to it | A commit that adds a test for the case plus an issue describing the bug |
| `Inferred` | One source suggests it | A commit sequence, a renamed file, a reverted change |
| `Unknown` | No source found | The Sources searched list |

Rules under the table: code is not evidence of its own intent; a claim never takes a tier above its strongest evidence; conflicting sources give the lower tier (spec.md → 📋 Business Rules → Conflicts take the lower tier).

### Step contents

- **Step 1: Anchor the Question.** Restate the question in one line: the subject and, when named, the planned change. Search the project for the files, symbols, and terms the question names. Not found → what was searched for and one natural-language question, then stop. Found → list the anchor: paths, line ranges, and the commits from `git log --follow`, `git log -L <start>,<end>:<path>`, or `git blame`. The anchor locates evidence and is never cited as a reason.
- **Step 2: Read the Ledger.** In this order: `git notes --ref=writ show <sha>` for each anchor commit; the specs those notes, the commit messages, or a search for the anchor paths name, in `.writ/specs/` and `.writ/specs/archive/` (`spec.md`, `drift-log.md`, and each story's `## What Was Built`); ADRs under `.writ/decision-records/` that name the anchor paths or the subject's terms, following `Superseded by` banners; `.writ/knowledge/` and `.writ/issues/` entries that mention them; `.writ/research/` documents those entries cite. Stop reading further ledger sources once a `Recorded` claim answers the question. No `.writ/` → say so and go to Step 3.
- **Step 3: Read Git History.** Always run, because it is the stale-ledger check. Read the messages and bodies of the anchor commits and their merge commits; `git log --grep=<term>` for the subject; note every PR or issue number a message cites. When a commit touched the anchor after the date of the `Recorded` entry, add the stale-ledger line.
- **Step 4: Read MCP Servers When Needed.** Only when the strongest claim is below `Stated`. Read PRs and issues the git messages cited, then search for the subject, through MCP servers already connected in the session (code host, issue tracker, chat, docs) or the code host's CLI when it is installed and signed in. Read calls only. Never prompt to connect, install, or authorize anything. Name every server read and every failure under Sources searched.
- **Step 5: Answer.** Print the answer template (§ Output Templates). Every claim gets a tier and evidence: a path with its section heading, a commit SHA, or a server and item id. Name every source searched that held nothing.
- **Step 6: Hand Off a Change.** Runs when a change follows (spec.md → 📋 Business Rules → A change follows). Append the handoff section, save the record (§ Output Templates), print its path, and suggest `/create-spec "<the change>"`. Without a change, print one line: if you plan to change this, name the change and `/why` adds the Preserve / Change / Avoid / Risk list.

### Integration with Writ

| Command | Relationship |
|---|---|
| `/writ` | Routes why-or-how questions about the project here |
| `/research` | Takes questions about something outside the project; `/why` points there when the subject is not in the project |
| `/create-spec` | Step 1.2 reads the handoff section |
| `/create-adr` | Finds saved why records in `.writ/research/` during its research search |
| `/knowledge` | Records a reason the user supplies after an `Unknown` or `Inferred` answer |

### Completion

Succeeds when the answer printed with a tier on every claim and the Sources searched list in source order, and, when a change followed, the saved record exists with the handoff section last. An `Unknown` answer with its sources searched is a valid result. **Terminal constraint:** `/why` explains and hands off. It does not change code, write a spec, record an ADR or knowledge entry, or write git notes. For the change, the user runs `/create-spec` or `/prototype`.

## Output Templates

### Answer (printed every run)

```markdown
## Why: <subject>

**Answer:** <one or two sentences> — <tier>

### Claims

| # | Claim | Tier | Evidence |
|---|---|---|---|
| 1 | <claim> | Recorded | `.writ/decision-records/adr-NNN-<slug>.md` § Decision |
| 2 | <claim> | Stated | commit `<sha>` message |

### Sources searched

- Ledger: <what was read>; nothing in <what held nothing>
- Git: <commits read>; <stale-ledger line when it applies>
- MCP: <servers read>, or "not read: the ledger answered at Recorded", or "none connected"
```

### Saved record (when a change follows)

Path `.writ/research/<YYYY-MM-DD>-why-<slug>.md`. The record is the header, the answer above, and the handoff section, in that order.

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

An empty subsection reads `- none found`.

## `/create-spec` Step 1.2 (Story 4)

Insert between `#### Step 1.1: Initial Context Scan` and `#### Step 1.3: Discovery Conversation (Plan Mode)`, under 700 bytes:

```markdown
#### Step 1.2: Read a `/why` Handoff

Look for a `## Preserve / Change / Avoid / Risk` section in this conversation, in a file the invocation names, and in `.writ/research/*-why-*.md` records whose `Subject` or `Change` line shares a keyword with the feature idea. Carry each one into the contract: Preserve into Business Rules, Change into the Deliverable, Avoid into Scope Boundaries → Excluded, Risk into Technical Concerns. Keep each item's tier and cite the record. Do not re-ask in discovery what the section settles. None found: skip this step.
```

Under `--recommend`, record each carried section in `recommendation-log.md` like any other evidence. No AskQuestion is added.

## `/writ` Route (Story 3)

- § Routing Rules, fifth row:
  `| Asks why something in this project is the way it is, or how it works | `/why` (a question about something outside the project: `/research`) |`
- § Step 2 bullet:
  `- **Why or how.** Route `/why`. A question about something outside the project, such as a library, a standard, or a vendor, routes `/research`.`
- The table keeps six rows. Step 4 mirroring picks up `/why`'s six `### Step N:` headings with no change to `/writ`.
- `.writ/docs/prompting-guide.md` § A why or how question:
  `Route: `/why` (`/research` for a question about something outside the project)`

## Registration Edits (Story 2)

| File | Edit |
|---|---|
| `.writ/manifest.yaml` | `commands:` entry `name: why`, `file: commands/why.md`, `category: planning`, `purpose: "Answer why code is the way it is from the ledger, git history, and MCP servers, with a confidence tier on every claim."`, `tags: [planning, why, history, ledger]`, between `verify-spec` and `writ`. |
| `SKILL.md` | `bash scripts/gen-skill.sh`; `--check` prints `pass`. |
| Generated trees | `python3 scripts/gen-platform-trees.py`; `--check` prints `pass`. Writes `claude-code/CLAUDE.md`, `codex/AGENTS.md.template`, `cursor/plugin/commands/why.md`, `plugins/writ/commands/why.md`, and `plugins/writ/.claude-plugin/plugin.json`. |
| `README.md` | § Commands → Planning & Specification, after the `/research` row: `| `/why` | Answers why code is the way it is from the ledger, git history, and MCP servers, with a confidence tier on every claim; when a change follows, ends with a Preserve / Change / Avoid / Risk list `/create-spec` reads |` |
| `adapters/cursor.md` | § Directory Structure: `why.md  # /why` between `verify-spec.md` and `writ.md`, `#` column aligned; count comment `(33)` → `(34)`. |
| `commands/status.md` | Slash allowlist: `` `/why` `` after `` `/research` ``. § Maintainer Note: Command Allowlist: `` `why` `` after `` `research` ``. |
| `.writ/docs/model-tiers.md` | § Deriving a Command's `entry_level`, `high` row: `why` between `security-audit` and `writ`; count `(16)` → `(17)`. |
| `scripts/eval-command-structure.py` | `ROWS`: `commands/why.md` heading `Confidence Tiers` (`check_command_structure`); `commands/why.md` frontmatter `entry_level` (`check_entry_level`). |
| `scripts/tests/test_front_door.py` | `CURSOR_COUNT = "(34)"`. |

Story 4 adds one more `ROWS` entry: `commands/create-spec.md` heading ``Step 1.2: Read a `/why` Handoff`` (`check_command_structure`).

## Tests (`scripts/tests/test_why_command.py`)

Python 3.9 standard library, the helper style of `scripts/tests/test_front_door.py`.

| Test | Story | Assertion |
|---|---|---|
| `test_command_file` | 1 | `commands/why.md` exists; frontmatter has `name: why`, `entry_level: high`, `problem`, `outcome`, three `exit_criteria`. |
| `test_tiers` | 1 | § Confidence Tiers first table's first column is `Recorded`, `Stated`, `Corroborated`, `Inferred`, `Unknown` in order; the section states that code is not evidence of its own intent. |
| `test_source_order` | 1 | `### Step 2` names `refs/notes/writ`, `drift-log.md`, `What Was Built`, and `.writ/decision-records/`; `### Step 3` names `git log`; `### Step 4` names MCP and `Stated`; Steps 2, 3, 4 appear in that order; Step 1 names one natural-language question for a subject not found, and Steps 2 to 4 each name their absent-source case (`.writ/` absent, not a git repository, none connected). |
| `test_handoff_shape` | 1 | The file contains `## Preserve / Change / Avoid / Risk` followed, in order, by `### Preserve`, `### Change`, `### Avoid`, `### Risk`, and the path pattern `.writ/research/<YYYY-MM-DD>-why-<slug>.md`. |
| `test_budgets` | 1 | Under 200 lines and under 24,960 bytes. |
| `test_step_headings` | 1 | Six `### Step N:` headings, numbered 1 to 6. |
| `test_registration` | 2 | Manifest entry with `category: planning`, sorted; `SKILL.md` and `claude-code/CLAUDE.md` carry a `/why` row; `gen-skill.sh --check` and `gen-platform-trees.py --check` print `pass` first; README, cursor tree `(34)`, both status allowlists, model-tiers `high` row `(17)`. |
| `test_create_spec_reads_handoff` | 4 | `commands/create-spec.md` has `#### Step 1.2: Read a `/why` Handoff` after Step 1.1 and before Step 1.3; that section contains the exact heading literal from `commands/why.md`, the four mappings, and the skip-when-none-found sentence. |

Story 3 changes existing tests instead of adding to this file, so Stories 3 and 4 touch no test file in common:

- `scripts/tests/test_front_door.py`: `ROUTES[4] = ("/why", None)`; the row-5 assertion checks `/research` instead of `/why`; a new `test_why_route` asserts § Step 2 contains ``Route `/why` `` and `commands/writ.md` no longer contains `when it ships`. (Story 2 changes `CURSOR_COUNT` to `"(34)"` in the same file; Story 3 runs after it.)
- `scripts/tests/test_prompting_guide.py`: the why-or-how recipe expects `/why`; the special-case assertion checks `/research`; a new assertion that the guide no longer contains `when it ships`.

## Dogfood Fixture

Run `/why` in this repository. Record each result in the story's What Was Built: the answer line, the top tier, and the ledger source. A mismatch is a fix to `commands/why.md`, not to the fixture.

| # | Question | Expected top tier | Expected ledger source | Story |
|---|---|---|---|---|
| 1 | "Why is the visual design command named `/writ-design` and not `/design`?" | Recorded | `.writ/specs/2026-10-20-platform-neutral-names/spec.md` or `.writ/issues/bugs/2026-10-19-design-command-name-collision.md` | 1 |
| 2 | "Why were friction signals never built?" | Recorded | `.writ/decision-records/adr-030-contract-verifier-boundary-front-door.md` | 1 |
| 3 | "Why does `commands/status.md` list `/writ` first in both allowlists?" | Recorded | `.writ/specs/2026-10-22-front-door/` DEV-003 | 1 |
| 4 | "Why does `/writ`'s confirmation offer at most four options? I want to add a fifth." | Recorded; change follows | `.writ/specs/2026-10-22-front-door/spec.md` Business Rule 4 or DEV-007 | 4 |

For question 4, `/why` saves a record with the handoff section. Then run `/create-spec "add a fifth option to /writ's confirmation"` through Step 1.2 only, in Plan Mode, and confirm the draft contract carries the Preserve item (four options, because Claude Code's question tool takes two to four) into Business Rules and the Risk item into Technical Concerns. Write no spec files. Keep the saved record under `.writ/research/` as evidence.
