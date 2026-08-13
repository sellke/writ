# Technical Spec — Recalibrate the implement-spec / implement-story Loop

> Parent: [`spec.md`](../spec.md)

## File Map

| File | Story | Change |
|---|---|---|
| `commands/implement-spec.md` | 1 | Step 3.2 spawn-mechanism note; Step 3.3 execution-state write reinforcement; completion-step spec.md-header sync |
| `skills/subagent-result-completeness/SKILL.md` | 2 | new |
| `commands/implement-story.md` | 2 | one blockquote note under "### Step 3: Run Pipeline" intro |
| `skills/subagent-worktree-integration/SKILL.md` | 3 | new |
| `commands/implement-story.md` | 3 | one more blockquote note, alongside Story 2's |

## Insertion Points (as of spec creation — reconfirm on implementation, see § Risk below)

### `commands/implement-spec.md`

- **Step 3.2 ("Execute Batches")** — after the "If parallel batch" bullet
  list (`Spawn ... concurrently` / `Wait for all to complete` /
  `If any story fails, decide...`), before "If sequential batch". Add:

  > **Platform note:** on a harness where invoking `/implement-story` loads
  > its instructions into the *current* context rather than running it as a
  > backgrounded subagent, "spawn ... concurrently" means the orchestrator
  > issues one parallel tool-call per story (each running that story's own
  > Gate 0/1/3/4/5 sequence) — not a nested command call the harness
  > auto-parallelizes. Confirm which behavior your platform's invocation
  > gives before assuming concurrency is free.

- **Step 3.3 ("Update State After Each Story")** — strengthen the first
  bullet ("Update execution state file with result") into a load-bearing
  requirement, e.g.:

  > **Update execution state file with result** — this is a required disk
  > write, not a mental note: update the story's `stories.{id}` entry in
  > `.writ/state/execution-{timestamp}.json` immediately, before dispatching
  > the next story. It is the only artifact `--resume` reads; tracking
  > progress solely in conversation state does not substitute for it and will
  > not survive a restart.

- **Completion step** — after the checker-verdict-governs paragraph
  (currently ending "...rather than presenting `✅ Specification Complete`."),
  before the `---` that opens `## Phase-Orchestrated Lane Mode`. Add:

  > **Spec header sync.** When the checker verdict is `met` and every story
  > is `Completed ✅`, update `spec.md`'s own `> **Status:**` line to
  > `Complete (<date>)` — the same completion status story files and
  > `README.md` already receive at Step 3.3 / Step 4 of `implement-story.md`.
  > This header is easy to leave stale, since nothing else in this file
  > writes it; `/verify-spec` Check 5b is otherwise the first thing to notice.

### `commands/implement-story.md`

- **"### Step 3: Run Pipeline" intro** already carries two blockquote notes
  (`> **Context refresh:** ...` and `> **File creation discipline:** ...`)
  before the `---` that opens Gate 0. Add two more, matching the exact same
  one-paragraph blockquote shape — one per skill, added by their respective
  stories:

  > **Sub-agent completeness:** `Read skills/subagent-result-completeness/SKILL.md`
  > for *how* to tell a spawned gate agent's complete verdict from a mid-task
  > stop, and what to do about the latter. Applies to every gate below that
  > spawns a sub-agent (Gate 0, 1, 3, 4, 4.5).

  > **Sub-agent worktree integration:** `Read skills/subagent-worktree-integration/SKILL.md`
  > for *how* to reconcile a spawned agent's isolated worktree with the
  > orchestrator's own checkout. Applies to every gate below that spawns a
  > sub-agent (Gate 0, 1, 3, 4, 4.5).

  This is a **deliberate deviation from the originally-drafted per-gate
  reference** (repeating a "Read skills/..." line inside Gate 0, 1, 3, 4, and
  4.5 individually) in favor of the file's own established cross-cutting
  pattern — matching how `Context refresh` and `File creation discipline`
  already apply to the whole pipeline from one place rather than being
  repeated five times. Story 2/3's acceptance criteria are written against
  this single-location form.

## Reuse

| Need | Existing code/pattern | Do not |
|---|---|---|
| Skill file format | `skills/story-commit-provenance/SKILL.md` (frontmatter: `name`/`description`/`disable-model-invocation: true`/`status: candidate`; body: Purpose / When to Use / How to Apply) | invent a new skill-file shape |
| Boundary lint | `scripts/lint-skill.sh` — verb-phrase description, no `Read commands/`, no `Read skills/` (skill-to-skill chaining), no `Task(`, no bare slash-command invocation in the body | skip linting before considering a skill done |
| Cross-cutting command note pattern | `commands/implement-story.md`'s existing `Context refresh` / `File creation discipline` blockquotes under "### Step 3: Run Pipeline" | repeat a near-identical line once per gate |
| Shared-template pattern | `commands/implement-story.md`'s "### BLOCKED Agent Escalation" (one template referenced by both Gate 1 and Gate 4) | duplicate escalation prose per gate |

## Error & Rescue Map

This is a documentation/process spec — no runtime error paths. The table
below covers authoring-time failure modes only.

| Operation | What Can Fail | Planned Handling |
|---|---|---|
| Author a new `SKILL.md` | Description reads as a role or workflow (ADR-009 violation) | `scripts/lint-skill.sh` FAILs naming the category (`Role-shape` / `Workflow-shape`) and remediation; rephrase as a verb-phrase capability |
| Author a new `SKILL.md` | Body references `Read commands/`, `Read skills/`, `Task(`, or a bare slash command | `scripts/lint-skill.sh` FAILs naming the category; inline the steps or move the reference to the consuming command instead |
| Edit `commands/implement-story.md` | Frontmatter or `## Completion` heading accidentally touched | `bash scripts/eval.sh`'s structural/governor checks FAIL; revert the accidental edit, keep only the Step 3 intro additions |
| Edit `commands/implement-spec.md` | Same as above, for its own frontmatter/`## Completion` | Same — `bash scripts/eval.sh` catches it |
| Story 3 runs before Story 2 lands | The Step 3 intro blockquote note Story 3 expects to sit "alongside Story 2's" doesn't exist yet | Story 3 task 3.1 requires reading the current file state first; if Story 2 isn't present, this is a dependency-ordering violation the orchestrator should catch via `/implement-spec`'s own dependency validation, not something Story 3 papers over |

No `[UNPLANNED]` cells remain.

## Verification

```bash
bash scripts/lint-skill.sh skills/subagent-result-completeness/SKILL.md
bash scripts/lint-skill.sh skills/subagent-worktree-integration/SKILL.md
bash scripts/eval.sh
```

Manual read-through: confirm both new blockquote notes in
`commands/implement-story.md` match the exact phrasing shape of `Context
refresh` / `File creation discipline`, and confirm `git diff --stat` on both
edited command files shows no change outside their prose bodies (frontmatter
and `## Completion` byte-identical).

## Risk

`commands/implement-story.md` was refactored to a much shorter "thin
contract" form by a concurrent peer session during the run that produced this
spec's evidence (commit `c4a5bf4`, "reduce the command to a thin contract").
The insertion points documented above reflect the file as it stood at spec
creation time. Story 2/3 must re-read the file's actual current content
before editing — do not assume the line numbers or exact surrounding prose
are unchanged; the *shape* of the convention (two blockquote notes under Step
3's intro) is what must be preserved and extended, not literal text offsets.
