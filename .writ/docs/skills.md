# Skills — The Third Writ Primitive

> **Status:** Foundation shipped (`2026-05-03-skills-foundation`); lifecycle added (`2026-07-10-skill-lifecycle`). Four production skills have been extracted from high-traffic commands (`2026-07-10-skill-extraction`) — `code-explanation`, `error-rescue-mapping`, `safe-refactor-loop`, and `tdd-cycle` — each born `status: candidate` (promotion to `proven` accrues later with evidence), alongside the shipped `conventional-commits` pilot. See [Extraction Patterns](#extraction-patterns) below.
> **Source of truth for the boundary:** [ADR-009](../decision-records/adr-009-command-agent-skill-boundary.md)
> **Cross-platform format:** [AgentSkills standard](https://agentskills.io)

This document is the user-facing explainer for skills. ADR-009 captures the *why* (decision and rationale); this document captures the *what* and *how*.

---

## Verb / Noun / Tool

Writ has three first-class primitives. Each plays a distinct role.

| Primitive | Grammar | What it is | Example |
|---|---|---|---|
| **Command** | Verb | A user-invoked workflow with phases, lifecycle, and durable artifacts. The user types `/command-name`. | `/create-spec`, `/implement-spec`, `/release` |
| **Agent** | Noun | A role with inherent behavior. Spawned by a command to occupy a specific function for the duration of a phase. Not user-invoked directly. | `coding-agent`, `review-agent`, `architecture-check-agent` |
| **Skill** | Tool | A reusable capability. Not a workflow, not a role — *how to do a specific thing well*. Wielded by commands and agents when relevant. | (proposed) `tdd-cycle`, `conventional-commits`, `adr-writing` |

### The boundary in one sentence

> Workflow → command. Role → agent. Capability → skill.

If two answers feel right for a piece of work, the work probably needs to be split.

### Composition is acyclic

```
Commands  →  spawn  →  Agents
Commands  →  use    →  Skills
Agents    →  use    →  Skills
```

**Skills do not call commands. Skills do not spawn agents. Skills do not chain other skills.** This keeps the dependency tree clean and prevents skills from quietly becoming workflows. The boundary lint (`scripts/lint-skill.sh`) enforces this at authoring time and during `/refresh-command --lint-skills`.

---

## File Format

Skills are markdown files conforming to the [AgentSkills open standard](https://agentskills.io) — the same format used by Cursor, Claude Code, Codex CLI, and OpenClaw. This buys cross-platform reach for free.

### Layout

```
skills/
├── <name>/
│   ├── SKILL.md                 # required — the skill definition
│   └── (optional sidecar files) # data, prompts, examples — install-once
```

A skill is a folder. The folder contains `SKILL.md` (the definition) and optional sidecar files (e.g. data files, prompt fragments, worked examples) that the skill body references.

### Required frontmatter

Every Writ-authored `SKILL.md` opens with YAML frontmatter:

```yaml
---
name: <kebab-case-name>
description: "<one-line verb-phrase>"
disable-model-invocation: true
---
```

| Field | Required | Notes |
|---|---|---|
| `name` | yes | Kebab-case. Unique across `commands:`, `agents:`, and `skills:` in the manifest. |
| `description` | yes | One-line verb-phrase ("Write commit messages…", "Validate diffs against…"). The boundary lint rejects role-shape and workflow-shape descriptions. |
| `disable-model-invocation` | yes (Writ-authored) | `true`. Opts out of platform auto-discovery so every skill load is explicit. See *Invocation* below. |

### Body conventions

Body sections, in order:

```markdown
# <Title-Cased Name>

## Purpose
<One paragraph: what this capability does and why an agent would load it.>

## When to Use
<2–4 bullets: concrete trigger conditions an agent should recognize.>

## How to Apply
<Step-by-step or principles.>

## Examples
<Optional: 1–2 worked examples showing input → output.>
```

The body must not invoke commands (`Read commands/foo.md`), call other skills (`Read skills/foo/SKILL.md`), spawn subagents (`Task(...)`), or invoke slash commands (`/foo` at start of a line). Code blocks are exempt from the lint — examples can show whatever they need to.

---

## Invocation

There are two invocation modes. Writ standardizes on one of them for its own skills.

### Explicit invocation (Writ-authored skills)

Writ-authored skills set `disable-model-invocation: true` so platforms with skill auto-discovery (Cursor's `<agent_skills>` block, Claude Code's skill loader, etc.) do not ambient-load them. The consuming command or agent reads the skill explicitly when the relevant phase begins:

```
Read skills/<name>/SKILL.md
```

Trade-off: more verbose (the consumer names what it needs), but every skill load is **deterministic, debuggable, and traceable** in transcripts. This matches Writ's contract-first ethos.

### Auto-invocation (community-installed skills)

Skills installed via community catalogs (e.g. `clawhub`, `agentskills.io`) typically use ambient invocation by description match — that's outside Writ's control and follows whatever the installer configured. Writ does not fight platform conventions for skills it didn't author.

### `required_skills:` frontmatter convention

Commands and agents may declare skills they need in their frontmatter:

```yaml
---
name: example-agent
required_skills:
  - tdd-cycle
  - conventional-commits
---
```

The harness pre-loads each named skill before the consumer's first phase begins.

**Schema:**
- Optional array of strings.
- Values match `name:` entries under `skills:` in `.writ/manifest.yaml`.
- Order is preserved (downstream tooling may use it for load priority).
- Duplicates are silently deduplicated.
- Unknown skill names produce a **warning**, not a hard failure.

**Status: reserve-only.** Defined in this foundation spec, but no agent or command currently uses it. Pilot skill specs will adopt it organically. Defining the schema now prevents pilots from inventing competing conventions.

> **Review trigger: 2026-08-03** (90 days post-ship). If no consumer has adopted `required_skills:` by then, deprecate or revisit.

---

## Skill Lifecycle

Every Writ-authored skill carries a required `status:` frontmatter field that
records how mature it is. Maturity is **earned from evidence**, not asserted:
the lint (`scripts/lint-skill.sh`) proves the declared state from the evidence
present in the same frontmatter — one file, no git history, no network. This is
the orthogonal lifecycle axis added on top of ADR-009's classification; see
[ADR-014](../decision-records/adr-014-skill-lifecycle.md) for the full rationale.

### The three states

| State | Evidence bar | Meaning |
|---|---|---|
| `candidate` | 0+ evidence entries (none required) | Provisional; the born state from `/new-skill` |
| `proven` | ≥3 well-formed evidence entries | In real use across consumers |
| `promoted` | `proven` bar **and** ≥1 entry with `type: promotion` | A consumer structurally depends on it (declared in `required_skills:`) |

The ladder is **monotone** — each state's evidence bar is a strict superset of
the one below — so a valid higher state statically implies the lower bars were
met. `candidate → promoted` skipping is unrepresentable. The three-entry
threshold ports GStack's "active after three successes" model. Demotion
(`proven → candidate`) is a manual maintainer edit the lint does not police; the
lint only ever proves the *current* declared state is earned.

### Evidence schema

Non-`candidate` states carry an `evidence:` block — a YAML list where each entry
has all four fields:

| Field | Format | Meaning |
|---|---|---|
| `date` | `YYYY-MM-DD` | When the evidence was recorded |
| `type` | `usage \| transcript \| eval \| promotion` | Class of evidence |
| `ref` | repo-relative path or transcript UUID | Pointer to the evidence |
| `note` | one line | Human-readable justification |

`type` semantics: `usage` = a consumer command or agent wields the skill;
`transcript` = a recorded agent-transcript UUID shows a successful application;
`eval` = a passing eval check exercises the skill; `type: promotion` = a
consumer declares the skill in its `required_skills:` frontmatter. The lint
validates *shape and thresholds only* — it never verifies that a cited path or
UUID is genuine.

### Worked example

`conventional-commits` ships at `status: proven` — used by `/ship`, `/release`,
and `coding-agent`:

```yaml
---
name: conventional-commits
description: "Write Conventional Commits messages ..."
disable-model-invocation: true
status: proven
evidence:
  - date: 2026-05-06
    type: usage
    ref: commands/ship.md
    note: "Cited as the commit-message authority in /ship's commit phase."
  - date: 2026-05-12
    type: usage
    ref: commands/release.md
    note: "Release changelog grouping consumes the type vocabulary."
  - date: 2026-06-01
    type: usage
    ref: agents/coding-agent.md
    note: "coding-agent authors story commits through this skill."
---
```

Were a consumer to add `conventional-commits` to its `required_skills:`, the
author would record a fourth entry with `type: promotion` and edit
`status: promoted`. The lint would confirm the promotion record exists.

### Where status lives

`status:` is duplicated in two places, exactly like `description:`:

- **`skills/<name>/SKILL.md` frontmatter** — authoritative; the lint validates it.
- **`.writ/manifest.yaml` skills entry** — a render mirror for the catalog's
  `Status` column. A missing manifest `status:` renders as `candidate`.

The lifecycle findings surface through the same `scripts/lint-skill.sh` that
`/new-skill` runs at authoring time and `/refresh-command --lint-skills` runs at
review time — one validator, identical rules everywhere.

---

## Authoring a Skill

Use `/new-skill <name>` to scaffold a new skill. The command:

1. Validates the name (kebab-case, unique across all primitives).
2. Coaches you toward verb-phrase descriptions (showing examples of role-shape and workflow-shape phrasings to avoid).
3. Runs `scripts/lint-skill.sh` against the captured frontmatter — re-prompts on rejection, never writes a half-shaped skill.
4. Generates `skills/<name>/SKILL.md` with `disable-model-invocation: true`, `status: candidate` (the born lifecycle state), and the standard sections.
5. Appends a `skills:` entry to `.writ/manifest.yaml` (alphabetical).
6. Regenerates the root `SKILL.md` catalog via `scripts/gen-skill.sh`.

The boundary lint is the contract — same script, same grammar, same exit codes whether the lint runs at authoring time (`/new-skill`) or at review time (`/refresh-command --lint-skills`). No divergence.

---

## Extraction Patterns

Some skills are not authored fresh — they are **extracted** from a high-traffic
command or agent that already contained a reusable capability tangled up with its
orchestration. Extraction pays off when the same *how* is (or will be) wielded by
more than one consumer, or when lifting it measurably shrinks a heavy command
toward pure orchestration.

### The transform

```text
identify the durable capability prose  (the reusable "how", not the "when/with what data")
        │
        ▼
author skills/<name>/SKILL.md  (status: candidate, verb-phrase description)
        │
        ▼
lint-skill.sh  ──► clean? ──no──► rewrite orchestration prose into capability prose
        │ yes
        ▼
wire the consumer:  Read skills/<name>/SKILL.md   (the "when/with what data" stays here)
        │
        ▼
shrink the source section to a one-paragraph orchestration note
        │
        ▼
register in .writ/manifest.yaml (alphabetical) → regenerate the catalog
```

Two rules keep extraction honest. First, the **capability moves, the
orchestration stays**: the skill owns *how to do the thing well*; the consumer
retains *when to invoke it and with what data*. Orchestration language —
"then run the reviewer", "`Read commands/…`", a line that starts with a slash
command — must be rewritten into capability prose or the boundary lint blocks it.
Second, **every extracted skill needs a live consumer**: because Writ skills are
`disable-model-invocation: true`, a skill nothing `Read`s is dead weight.

### Shrink note shape

Each shrunk section becomes a short orchestration note naming the skill and the
*how/when* split, mirroring `commands/ship.md`'s commit-authoring note:

> **`<Capability>`:** `Read skills/<name>/SKILL.md` for *how to do X*. This command owns *when to invoke it and what data to pass*.

### Shipped extractions (`2026-07-10-skill-extraction`)

| Skill | Source | Wired consumer(s) | Reuse justification |
|---|---|---|---|
| `code-explanation` | retired `/explain-code` command | `commands/research.md` | A general, depth-scaled explanation capability any agent can wield; the weak command retired into it |
| `tdd-cycle` | `/implement-story` coding phase | `implement-story` (Gate 1), `coding-agent`, `testing-agent` | Strongest reuse — three live consumers share the red → green → refactor discipline (ADR-009 names it) |
| `error-rescue-mapping` | `/create-spec` Step 2.8 | `create-spec` now; a review pass later | Error & Rescue / Shadow Path / edge-case tables share their shape with a reviewer's output by design |
| `safe-refactor-loop` | `/refactor` Phase 3 | `refactor` now; prototype work later | Thinnest current reuse — justified by the durable behavior-preserving-change discipline plus a real command shrink |

The set is committed at **four**, not padded to the roadmap's "3–5" ceiling.
`/ship` was named as a candidate but its high-traffic capability was already
extracted as `conventional-commits`; its non-extraction is documented in
`commands/ship.md`, not treated as a gap. All four extracted skills are born
`status: candidate` — "in real use" is satisfied here by wiring live consumers;
promotion to `proven` requires evidence and is owned by the lifecycle spec.

---

## Boundary Examples

Concrete cases to make the line unambiguous (mirrors ADR-009's table):

| Concern | Classification | Why |
|---|---|---|
| "Run the spec implementation pipeline through dependency-aware story batches" | **Command** (`/implement-spec`) | User-invoked workflow with phases and durable artifacts |
| "Act as a code reviewer who verifies acceptance criteria, code quality, tests, and drift" | **Agent** (`review-agent`) | Persistent role with its own context and quality bar |
| "Write a commit message in Conventional Commits format given a diff" | **Skill** (`conventional-commits`) | Reusable capability used by multiple consumers; no workflow, no role |
| "Run a TDD red/green/refactor cycle on a unit of work" | **Skill** (`tdd-cycle`) | Capability used by `coding-agent` and `/prototype`; describes *how*, not orchestration |
| "Run an OWASP Top 10 + STRIDE threat audit and produce a report" | **Command** (`/security-audit`) — *not* a skill | User-invoked, multi-phase, durable artifacts. The OWASP *patterns* could be a skill (`owasp-review-patterns`). |
| "Be the documentation engineer who detects the framework and updates docs" | **Agent** (`documentation-agent`) — *not* a skill | A role with persistent identity, not a one-shot capability |

---

## Per-Platform Behavior

Each adapter documents the platform-specific install path, loading mechanism, and invocation pattern:

| Platform | Install path | Adapter doc |
|---|---|---|
| Cursor | `.cursor/skills/<name>/SKILL.md` | [`adapters/cursor.md`](../../adapters/cursor.md) → Skills |
| Claude Code | `.claude/skills/<name>/SKILL.md` | [`adapters/claude-code.md`](../../adapters/claude-code.md) → Skills |
| OpenClaw | `.openclaw/skills/<name>/SKILL.md` | [`adapters/openclaw.md`](../../adapters/openclaw.md) → Skills |

`scripts/install.sh` and `scripts/update.sh` fan skills out alongside commands and agents using the same three-way overlay logic — local modifications to platform-native `SKILL.md` files are preserved across updates. Sidecar files inside a skill folder are install-once: copied on first install, never overwritten on update.

---

## Empty-State Behavior

If `.writ/manifest.yaml` has `skills: []`, the catalog generator (`scripts/gen-skill.sh`) **silently skips** the `## Available Skills` section in the root `SKILL.md`. This keeps empty manifests producing clean catalogs and matches the contract from Story 1 of the foundation spec.

---

## What Skills Are *Not*

To prevent drift, name what skills aren't:

- **Skills are not commands.** A workflow with phases, lifecycle, and durable artifacts is a command. If a proposed skill needs to invoke `/something` or read other commands, it's mis-classified.
- **Skills are not agents.** A role with persistent identity that a workflow steps into is an agent. If a proposed skill describes "acting as" something, it's mis-classified.
- **Skills are not docs.** `.writ/docs/` already houses reference documentation. Skills are *invocable capabilities* that an agent can wield to do something well — not passive reading material.
- **Skills are not chained.** Skills do not call other skills. If two skills naturally compose, combine them into the consumer (agent or command) that uses both.

---

## References

- **Boundary rationale:** [ADR-009](../decision-records/adr-009-command-agent-skill-boundary.md)
- **Cross-platform format:** [AgentSkills standard](https://agentskills.io)
- **Authoring tool:** [`commands/new-skill.md`](../../commands/new-skill.md)
- **Review tool:** [`commands/refresh-command.md`](../../commands/refresh-command.md) → Phase 5 (Skills Boundary Lint)
- **Lint grammar:** [`scripts/lint-skill.sh`](../../scripts/lint-skill.sh)
- **Catalog generator:** [`scripts/gen-skill.sh`](../../scripts/gen-skill.sh)
- **Required-skills convention source:** [`system-instructions.md`](../../system-instructions.md) → Skills section
- **Self-dogfooding pattern:** [`.writ/docs/self-dogfooding.md`](./self-dogfooding.md) → Skills section
