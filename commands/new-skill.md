# New Skill Creator (new-skill)

## Overview

Scaffold a new Writ skill — a capability file (SKILL.md) that an agent or command can `Read` to acquire a focused competence. Skills are the third Writ primitive: **commands are verbs**, **agents are nouns**, **skills are tools**. This command captures the skill's intent, runs a boundary lint at authoring time, writes `skills/<name>/SKILL.md`, and appends an entry to `.writ/manifest.yaml` — refusing to scaffold anything that drifts into role or workflow shape.

**When to use** — you have an agent or command that keeps inlining the same chunk of "how to do X well," or you've identified a reusable capability that multiple consumers will need. Before scaffolding, this command enforces the boundary [ADR-009](../.writ/decision-records/adr-009-command-agent-skill-boundary.md) draws between commands, agents, and skills.

## Invocation

| Invocation | Behavior |
|---|---|
| `/new-skill <name>` | Scaffold a skill named `<name>` (kebab-case) |
| `/new-skill` | Interactive — prompt for name |

`<name>` must be kebab-case, unique across commands, agents, and existing skills.

---

## Command Process

This is a **direct command** (not contract-first like `/new-command`). Skills are smaller-scope artifacts; the boundary lint *is* the contract.

### Phase 1: Capture

#### Step 1.1: Resolve the Name

If a name was passed as an argument, validate it. Otherwise prompt:

```
AskQuestion({
  title: "Skill Name",
  questions: [{
    id: "name",
    prompt: "What's the skill name? (kebab-case, e.g. 'tdd-cycle', 'conventional-commits')",
    options: []  // Free-text input; AskQuestion permits this when no options listed.
  }]
})
```

Validate the name:

- **Format:** Matches `^[a-z][a-z0-9-]*$` (kebab-case, starts with letter)
- **Uniqueness:** Read `.writ/manifest.yaml` and verify no `name:` entry under `commands:`, `agents:`, or `skills:` matches. If a collision exists, reject:

  > ❌ Name "{name}" conflicts with existing {kind}. Skills must have unique names across commands, agents, and skills.

  Then re-prompt or exit. **Do not write any files.**

#### Step 1.2: Verb-Phrase Coaching, Then Capture Description

**Before** asking for the description, show this hint verbatim:

> Skills describe a capability — they are tools, not roles or workflows.
> Start with a verb (Write, Validate, Audit, Generate, Convert, Detect, ...).
> Avoid: "Acts as", "Is responsible for", "The X agent", "Run the full", "Execute the entire".

Then capture the description with a free-text prompt:

```
AskQuestion({
  title: "Skill Description",
  questions: [{
    id: "description",
    prompt: "One-line capability description (verb-phrase). This appears in the manifest and the SKILL.md frontmatter.",
    options: []
  }]
})
```

The description is the **highest-leverage signal** — it's what a future agent reads to decide whether to load the skill. Treat it as the primary lint target.

#### Step 1.3: Optional Tags

Skills can carry optional discovery tags. Prompt only if the user wants them:

```
AskQuestion({
  title: "Tags (optional)",
  questions: [{
    id: "tags",
    prompt: "Comma-separated tags for discovery (e.g. 'testing,tdd,ruby'). Leave blank to skip.",
    options: []
  }]
})
```

Parse comma-separated input into an array; treat blank as empty.

---

### Phase 2: Lint

Run `bash scripts/lint-skill.sh` against a *temporary* SKILL.md in `/tmp` containing the captured frontmatter and an empty body. The lint enforces ADR-009's role convention — **shared with `/refresh-command`** so there is no divergence between authoring and review.

#### Step 2.1: Build the Lint Candidate

Write a temp file (e.g. `/tmp/new-skill-lint-$$.md`) with this content:

```markdown
---
name: <name>
description: "<description>"
disable-model-invocation: true
status: candidate
---

# <Title-Cased Name>

## Purpose

(scaffolded body — lint candidate)
```

`status: candidate` is the born lifecycle state (ADR-014): a new skill has
earned no evidence yet, and `candidate` requires none — so the scaffold passes
the lifecycle lint unchanged.

#### Step 2.2: Run the Lint

```bash
bash scripts/lint-skill.sh /tmp/new-skill-lint-$$.md
```

**Exit codes:**

- `0` → description passes the role convention. Proceed to Phase 3.
- `1` → one or more violations. The script prints the offending phrase, category, and remediation. **Re-prompt for the description** (preserving name and tags) and re-lint. Loop until clean or the user aborts.
- `2` → usage error. Surface the script's stderr verbatim and abort.

Always remove the temp file after the run (`rm -f /tmp/new-skill-lint-$$.md`).

#### Step 2.3: Surface Lint Output

When lint fails, present the failure conversationally — not as raw script output:

> ❌ The description "{description}" starts with "{pattern}", which signals a {category} (skills are tools, not roles or workflows).
>
> **Suggested rewrite:** {remediation}
>
> Want to revise the description, or abort?

Use `AskQuestion` with options `revise` / `abort`.

---

### Phase 3: Write

Triggered only after lint passes. Track with `todo_write` if more than three writes are involved (in this case: SKILL.md, manifest entry, optional gen-skill check — borderline; use judgment).

#### Step 3.1: Generate `skills/<name>/SKILL.md`

Create the directory `skills/<name>/` if needed, then write `skills/<name>/SKILL.md`:

```markdown
---
name: <name>
description: "<description>"
disable-model-invocation: true
status: candidate
---

# <Title-Cased Name>

## Purpose

<One paragraph: what this capability does and why an agent would load it.>

## When to Use

<2–4 bullet points: concrete trigger conditions an agent should recognize.>

## How to Apply

<Step-by-step or principles. This is the body the lint scans against the
body-shape grammar — keep paragraphs concise; avoid `Read commands/`,
`Read skills/`, `Task(`, or slash-command invocations. Code blocks are
exempt from the lint.>

## Examples

<Optional: 1–2 worked examples showing input → output.>
```

The frontmatter MUST include `disable-model-invocation: true` so platforms with skill auto-discovery (e.g. Cursor, Claude Code's `<agent_skills>` block) do not ambient-load the skill. Every skill load is explicit and traceable. See [`adapters/cursor.md`](../adapters/cursor.md), [`adapters/claude-code.md`](../adapters/claude-code.md), [`adapters/openclaw.md`](../adapters/openclaw.md) for per-platform details.

#### Step 3.2: Append to `.writ/manifest.yaml`

Append a new entry under `skills:`, in **alphabetical order by `name`** to keep diffs clean:

```yaml
  - name: <name>
    file: skills/<name>/SKILL.md
    description: "<description>"
    status: candidate
    tags: [<tag1>, <tag2>]   # omit if empty
```

The manifest `status:` is the catalog render mirror (ADR-014); the SKILL.md
frontmatter is authoritative. Both are born `candidate`.

If the manifest currently has `skills: []`, replace the inline empty list with a block-style list before inserting. Use `awk` or `sed` for the in-place edit (the manifest is a hand-edited YAML file — avoid full-file rewrites).

#### Step 3.3: Verify with `gen-skill.sh`

Run `bash scripts/gen-skill.sh --check` to confirm the manifest is well-formed and the new skill renders into the root `SKILL.md` table. If `--check` reports a regeneration delta, run `bash scripts/gen-skill.sh` to refresh the catalog.

#### Step 3.4: Final Output

```
✅ Skill scaffolded: skills/<name>/SKILL.md

Description: "<description>"
Manifest:    .writ/manifest.yaml (entry appended)
Catalog:     SKILL.md (regenerated)

Next steps:
  - Open skills/<name>/SKILL.md and write the body
  - Reference it from the consumer (agent or command) via:
      Read skills/<name>/SKILL.md
  - Or declare it under `required_skills:` in the consumer's frontmatter
    (see system-instructions.md → Skills section)
```

---

## Core Rules

1. **Boundary lint is non-negotiable.** Description-shape and body-shape rejections (per [ADR-009](../.writ/decision-records/adr-009-command-agent-skill-boundary.md)) are the contract. Lint failure means revise or abort — never write a half-shaped skill.
2. **Lint logic lives in `scripts/lint-skill.sh`.** Both `/new-skill` and `/refresh-command` invoke the same script. No regex grammar duplicated inline in command files.
3. **Verb-phrase descriptions only.** "Write", "Validate", "Generate", "Audit", "Convert", "Detect" — not "Acts as", "Run the full", "The X agent". The description is the most-read signal; protect it.
4. **`disable-model-invocation: true` is mandatory** for Writ-authored skills. Explicit invocation is the only invocation mode.
5. **Names are unique across primitives.** A skill cannot share a name with a command or agent. The validation runs before the lint to fail fast.
6. **Manifest in alphabetical order.** Within `skills:`, entries are sorted by `name:` to keep diffs reviewable.
7. **Born `candidate`.** Every new skill scaffolds at `status: candidate` (ADR-014) — the provisional lifecycle state that requires no evidence. A skill earns `proven` (≥3 recorded evidence entries) and then `promoted` (a consumer's `required_skills:` declaration) later, by hand, as it sees real use. `/new-skill` never scaffolds a non-`candidate` state.

---

## Integration with Writ

| Command | Relationship |
|---|---|
| `/refresh-command` | Runs the same boundary lint against existing `skills/*/SKILL.md` files; shares `scripts/lint-skill.sh` |
| `/new-command` | Sibling scaffolding command for the verb primitive |
| `/create-adr` | Significant skill-extraction decisions may warrant an ADR (precedent: ADR-009) |

---

## Completion

This command succeeds when:

1. **Skill file created** — `skills/<name>/SKILL.md` exists with valid frontmatter (`name`, `description`, `disable-model-invocation: true`, `status: candidate`) and scaffolded sections (Purpose, When to Use, How to Apply, Examples)
2. **Lint passed** — `scripts/lint-skill.sh` returned exit `0` against the captured frontmatter (including the lifecycle check: a born `candidate` needs no evidence)
3. **Manifest updated** — `.writ/manifest.yaml` contains a new `skills:` entry, alphabetically placed
4. **Catalog regenerated** — root `SKILL.md` reflects the new skill (verified via `bash scripts/gen-skill.sh --check`)
5. **No name collisions** — the skill name is unique across commands, agents, and existing skills
6. **Summary presented** — the user received the file path, manifest confirmation, and next-step guidance

**Suggested next step:** Open `skills/<name>/SKILL.md` and write the body. When ready to use the skill, declare it in the consumer's `required_skills:` frontmatter (see [`system-instructions.md`](../system-instructions.md) → Skills) or invoke it inline with `Read skills/<name>/SKILL.md`.

**Terminal constraint:** This command produces a skill scaffold. Do not offer to implement, build, or execute the skill body — that's the user's craft work. For quick prototyping of skill content, the user can edit the file directly.

---

## References

- Standing instructions: [`commands/_preamble.md`](_preamble.md)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)
- Boundary rationale: [ADR-009](../.writ/decision-records/adr-009-command-agent-skill-boundary.md)
- Lifecycle rationale: [ADR-014](../.writ/decision-records/adr-014-skill-lifecycle.md)
- User-facing explainer: [`.writ/docs/skills.md`](../.writ/docs/skills.md)
- Lint grammar source: [`scripts/lint-skill.sh`](../scripts/lint-skill.sh)
