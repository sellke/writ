---
name: new-skill
description: "Scaffold a reusable Writ skill (SKILL.md) that commands and agents can read to acquire a focused competence. Enforces the command/agent/skill boundary."
problem: "Reusable know-how stays inlined in agent and command bodies, and hand-written skill files drift into role or workflow shape that nobody catches until a consumer loads them."
outcome: "A lint-clean SKILL.md scaffold exists at the path scripts/skill-target.py printed: skills/<name>/ in the Writ source repository, registered in .writ/manifest.yaml and the root SKILL.md catalog; the platform's skills folder in an installed project, with no manifest created."
entry_level: standard
exit_criteria:
  - "the target: path scripts/skill-target.py printed exists carrying disable-model-invocation: true and status: candidate in its frontmatter"
  - "scripts/lint-skill.sh printed pass on line 1 for the captured description before any file was written"
  - "when scripts/skill-target.py printed manifest: .writ/manifest.yaml, the manifest gained one alphabetically placed skills: entry for <name> and bash scripts/gen-skill.sh --check printed pass on line 1 or the project has no scripts/gen-skill.sh; when it printed manifest: none, no .writ/manifest.yaml exists"
---

# New Skill Creator (new-skill)

## Overview

Scaffold a new Writ skill — a capability file (SKILL.md) that an agent or command can `Read` to acquire a focused competence. Skills are the third Writ primitive: **commands are verbs**, **agents are nouns**, **skills are tools**. This command captures the skill's intent, runs a boundary lint at authoring time, and writes the SKILL.md — refusing to scaffold anything that drifts into role or workflow shape. In the Writ source repository the skill goes to `skills/<name>/SKILL.md` and gets a `.writ/manifest.yaml` entry. A project that installed Writ with `install.sh` or a plugin has no manifest, so the skill goes to the platform's skills folder and no manifest is created.

**When to use** — you have an agent or command that keeps inlining the same chunk of "how to do X well," or you've identified a reusable capability that multiple consumers will need. Before scaffolding, this command enforces the boundary between commands, agents, and skills.

## Invocation

| Invocation | Behavior |
|---|---|
| `/new-skill <name>` | Scaffold a skill named `<name>` (kebab-case) |
| `/new-skill` | Interactive — prompt for name |

`<name>` must be kebab-case, unique across commands, agents, and existing skills.

---

## Command Process

This is a **direct command** (not contract-first like `/new-command`). Skills are smaller-scope artifacts; the boundary lint is the contract.

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
- **Uniqueness and target:** Run the check, with `<platform>` the platform you are running on: `claude` (Claude Code), `cursor`, or `codex`.

  ```bash
  python3 scripts/skill-target.py check <name> --platform <platform>
  ```

  With `.writ/manifest.yaml` (the Writ source repository), the script checks the manifest's `commands:`, `agents:`, and `skills:` entries. Without it (an `install.sh` or plugin project), it checks the installed commands, agents, and skills. Read line 1:

  - `pass` → keep the `target:` and `manifest:` lines. Step 3.1 writes the `target:` path, and Step 3.2 runs only when `manifest:` is `.writ/manifest.yaml`.
  - `fail` → each `reason:` line names a format problem or the command, agent, or skill that has the name. For a taken name, reject:

    > ❌ Name "{name}" conflicts with existing {kind}. Skills must have unique names across commands, agents, and skills.

    Then re-prompt or exit. **Do not write any files.**
  - `unverifiable` → no installed commands were found for that platform. Check `--platform` and re-run; never proceed on `unverifiable`.

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

The description is what a future agent reads to decide whether to load the skill. Treat it as the primary lint target.

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

Run `bash scripts/lint-skill.sh` against a *temporary* SKILL.md in `/tmp` containing the captured frontmatter and an empty body. The lint enforces ADR-009's role convention and is shared with `/refresh-command`, so authoring and review cannot diverge.

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

**Read line 1 of stdout:**

- `pass` (exit 0) → description passes the role convention. Proceed to Phase 3.
- `fail` (exit 1) → one or more violations. The `reason:` lines give the offending phrase and category, each followed by a `Remediation:` line. **Re-prompt for the description** (preserving name and tags) and re-lint. Loop until clean or the user aborts.
- `unverifiable` (exit 0) → the temp file was not found. Rewrite it and re-lint; never proceed on `unverifiable`.
- Exit `2` → usage error. Surface the script's stderr verbatim and abort.

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

#### Step 3.1: Write the Skill File

Write the `target:` path from Step 1.1: `skills/<name>/SKILL.md` in the Writ source repository; `.claude/skills/<name>/SKILL.md`, `.cursor/skills/<name>/SKILL.md`, or `.agents/skills/<name>/SKILL.md` in an installed project. Create its folder if needed. `Read skills/plain-prose/SKILL.md` before filling the body sections below; a skill is read inline by every consumer, so its prose carries the same rules as a command's. Then write the file:

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

Skip this step and Step 3.3 when Step 1.1 printed `manifest: none`. An installed project has no `.writ/manifest.yaml`; do not create one. Report `Manifest: none (installed project)` and `Catalog: not regenerated (no scripts/gen-skill.sh)` in Step 3.4.

Otherwise append a new entry under `skills:`, in **alphabetical order by `name`** to keep diffs clean:

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

`scripts/gen-skill.sh` renders the root `SKILL.md` catalog of the Writ source repository, and installs do not ship it. If the project has no `scripts/gen-skill.sh`, skip this step and report `Catalog: not regenerated (no scripts/gen-skill.sh)` in Step 3.4.

Otherwise run `bash scripts/gen-skill.sh --check` to confirm the manifest is well-formed and the new skill renders into the root `SKILL.md` table. Read line 1: `pass` means the catalog is current. `fail` with a `reason: SKILL.md drifts` line means run `bash scripts/gen-skill.sh` to refresh the catalog. `fail` with a `reason: YAML error` line means fix the manifest entry and re-run.

#### Step 3.4: Final Output

`<target>` is the `target:` path from Step 1.1.

```
✅ Skill scaffolded: <target>

Description: "<description>"
Manifest:    .writ/manifest.yaml (entry appended)
Catalog:     SKILL.md (regenerated)

Next steps:
  - Open <target> and write the body
  - Reference it from the consumer (agent or command) via:
      Read <target>
  - Or declare it under `required_skills:` in the consumer's frontmatter
    (see system-instructions.md → Skills section)
```

---

## Core Rules

1. **Boundary lint gates every write.** Description-shape and body-shape rejections are the contract. On lint failure, revise or abort; do not write a half-shaped skill.
2. **Lint logic lives in `scripts/lint-skill.sh`.** Both `/new-skill` and `/refresh-command` invoke the same script. No regex grammar duplicated inline in command files.
3. **Verb-phrase descriptions only.** "Write", "Validate", "Generate", "Audit", "Convert", "Detect" — not "Acts as", "Run the full", "The X agent". The description is the field agents read most.
4. **`disable-model-invocation: true` is mandatory** for Writ-authored skills. Explicit invocation is the only invocation mode.
5. **Names are unique across primitives.** A skill cannot share a name with a command or agent: in the Writ source repository, any manifest entry; in an installed project, any installed command, agent, or skill. `scripts/skill-target.py` runs before the lint to fail fast.
6. **Manifest in alphabetical order.** Within `skills:`, entries are sorted by `name:` to keep diffs reviewable. Only the Writ source repository has a manifest; `/new-skill` never creates one.
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

1. **Skill file created** — the `target:` path from Step 1.1 exists with valid frontmatter (`name`, `description`, `disable-model-invocation: true`, `status: candidate`) and scaffolded sections (Purpose, When to Use, How to Apply, Examples)
2. **Lint passed** — `scripts/lint-skill.sh` printed `pass` on line 1 against the captured frontmatter (including the lifecycle check: a born `candidate` needs no evidence)
3. **Manifest updated** — `.writ/manifest.yaml` contains a new `skills:` entry, alphabetically placed, or, when Step 1.1 printed `manifest: none`, no `.writ/manifest.yaml` exists
4. **Catalog regenerated** — root `SKILL.md` reflects the new skill (`bash scripts/gen-skill.sh --check` prints `pass`), or Step 3.3 was skipped because the project has no `scripts/gen-skill.sh`
5. **No name collisions** — `scripts/skill-target.py` printed `pass`: the name is unique across commands, agents, and existing skills
6. **Summary presented** — the user received the file path, manifest confirmation, and next-step guidance

**Suggested next step:** Open the `target:` path and write the body. When ready to use the skill, declare it in the consumer's `required_skills:` frontmatter (see [`system-instructions.md`](../system-instructions.md) → Skills) or invoke it inline with a `Read` of that path.

**Terminal constraint:** This command produces a skill scaffold. Do not offer to implement, build, or execute the skill body; the user writes it. For quick prototyping of skill content, the user can edit the file directly.

---

## References

- Standing instructions: [`commands/_preamble.md`](_preamble.md)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)
- User-facing explainer: [`.writ/docs/skills.md`](../.writ/docs/skills.md)
- Lint grammar source: [`scripts/lint-skill.sh`](../scripts/lint-skill.sh)
- Name check and target path: [`scripts/skill-target.py`](../scripts/skill-target.py)
