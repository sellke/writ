# Technical Spec — Phase 4 Production-Grade Substrate

> **Spec:** [`spec.md`](../spec.md)
> **Status:** Not Started
> **Last Updated:** 2026-04-24

This sub-spec captures concrete file layouts, schemas, scripts, and integration points the five Phase 4 stories produce. The contract is in `spec.md`; this document is the implementation reference.

---

## Story 1 — Knowledge Ledger v1

### Directory layout

```
.writ/knowledge/
├── README.md                     # decision tree + schema doc + authoring rules
├── decisions/                    # small "we chose X because Y" — sub-ADR scale
│   └── YYYY-MM-DD-{slug}.md
├── conventions/                  # codebase patterns
│   └── YYYY-MM-DD-{slug}.md
├── glossary/                     # domain terminology
│   └── {term-slug}.md            # filename = term, no date prefix
└── lessons/                      # postmortem-style "we tried X, it failed because Y"
    └── YYYY-MM-DD-{slug}.md
```

`glossary/` deviates from date prefixing because terms are stable identifiers, not events. All other categories use the date-prefixed convention shared with `.writ/issues/` and `.writ/research/`.

### Frontmatter schema (required minimum)

```yaml
---
category: decisions | conventions | glossary | lessons
tags: [tag1, tag2, ...]              # 1+ tags required
created: YYYY-MM-DD
related_artifacts:                   # 0+ items; relative paths
  - .writ/specs/.../spec.md
  - .writ/decision-records/adr-NNN.md
  - .writ/research/.../...md
---
```

Optional fields (extensible without schema migration): `superseded_by`, `replaces`, `author`, `confidence: low|medium|high`.

### `README.md` — "What goes where" decision tree

The README must include this decision flow (text form; the actual README will format it):

```
Is this an architectural choice with serious blast radius
(reverses cost weeks, locks in a substrate, etc.)?
→ YES: .writ/decision-records/ (ADR template)

Is this an investigation that produced specific recommendations
or evaluated multiple options against drivers?
→ YES: .writ/research/ (research template)

Is this a feature contract with stories, gates, and acceptance criteria?
→ YES: .writ/specs/ (spec template)

Otherwise — small, accumulating, cross-cutting:
- A choice we made about how the codebase looks?           → knowledge/decisions/
- A pattern the codebase uses we want documented?          → knowledge/conventions/
- A term whose meaning matters in this project?            → knowledge/glossary/
- A thing we tried that failed (or worked unexpectedly)?   → knowledge/lessons/
```

### `commands/knowledge.md` — authoring command

Modeled on `/create-issue` (terse, single-purpose, <2-minute capture). Behaviors:

| Invocation | Behavior |
|---|---|
| `/knowledge "summary"` | Infer category, prompt for missing tags, write conformant entry |
| `/knowledge --category=lessons "summary"` | Skip category inference |
| `/knowledge --list [category]` | Show entries (filename + first sentence) |
| `/knowledge --read <slug>` | Print a specific entry |

Output template:

```markdown
---
category: {inferred-or-supplied}
tags: [{required}]
created: {YYYY-MM-DD via npx @devobsessed/writ date}
related_artifacts:
  - {if any}
---

# {Title from summary}

## TL;DR

{One-sentence summary}

## Context

{What prompted this — bullet points}

## Detail

{The actual knowledge}

## Related

- [{label}]({path})
```

### Agent context-loading hook

Modify `commands/implement-story.md` Step 2 (Context Loading):

```
2.X — Load Knowledge Context (NEW)
   Extract keywords from:
     - story title
     - story file's "## Context for Agents" block
     - files in scope
   Grep .writ/knowledge/ for matching frontmatter tags or content.
   Assemble matches as `knowledge_context` parameter (max ~2KB; truncate by relevance score if exceeded).
   Pass to coding-agent, architecture-check-agent, review-agent.
```

Modify `agents/coding-agent.md`, `agents/architecture-check-agent.md`, `agents/review-agent.md` input-parameter tables to add `knowledge_context` (string, optional). Each agent's prompt includes a "Loaded knowledge entries" section when populated.

### Backfill candidates (5–10 entries)

| Category | Candidate | Source |
|---|---|---|
| decisions | "Adapter neutrality is non-negotiable" | `agents/*.md` consistent practice; ADR-006 reference |
| decisions | "Markdown-as-instructions, not code" | `AGENTS.md`, mission docs |
| conventions | "Bash script style — install.sh / ralph.sh model" | Inspection of existing scripts |
| conventions | "Filename pattern YYYY-MM-DD-slug.md across `.writ/`" | issues, research, decision-records |
| conventions | "Symlinks for self-dogfooding (.cursor/, .claude/)" | `AGENTS.md` |
| glossary | "spec" — Writ-specific meaning | spec template + `commands/create-spec.md` |
| glossary | "drift log" | `agents/review-agent.md` |
| glossary | "shadow path" | `commands/review.md` |
| glossary | "context hint" | `.writ/docs/context-hint-format.md` |
| glossary | "dual-use test" | ADR-007 |
| lessons | "Story-decomposition overlap (Stories 1+2 of Context Engine)" | drift-log.md DEV-007 |

Story 1's Definition of Done requires ≥5 entries committed across ≥2 categories.

---

## Story 2 — Spec Frontmatter `owner:` Field

### Schema addition

```yaml
---
status: Not Started | In Progress | Complete
created: YYYY-MM-DD
owner: @{git-user-name}    # NEW — defaults to `git config user.name`, with @ prefix
... (existing fields)
---
```

### `commands/create-spec.md` modification

Step 2.4 (Generate Core Documents) — `spec.md` template gains the owner field. Default value:

```bash
OWNER="@$(git config user.name 2>/dev/null | tr -d ' ' || echo 'unknown')"
```

If `git config user.name` is empty, write `owner: @unknown` and emit a warning suggesting `git config user.name 'Your Name'`.

### `commands/verify-spec.md` modification

Add a new check to the existing sequential numbering (per Suite Quality Polish renumbering, current sequence ends at Check 7 — new check is Check 8):

```
Check 8: Spec Owner Field Presence

For each spec in .writ/specs/:
  - If spec was created on/after 2026-04-24 (this spec's ship date):
    REQUIRE: frontmatter contains `owner:` field
    On miss: WARN (do not fail) and offer auto-backfill
  - Else: REPORT as "legacy spec — owner not required"
```

Determination of "post-ship" date:
- Read first commit affecting the spec file: `git log --diff-filter=A --format=%aI -- {spec.md} | tail -1`
- If commit date >= 2026-04-24, owner field required.

### `commands/status.md` modification

In the active-specs section, surface the owner column:

```
Active Specs:
  | Status      | Spec                              | Owner    |
  |-------------|-----------------------------------|----------|
  | In Progress | 2026-04-24-phase4-production...   | @adam    |
```

For legacy specs (no `owner:`), display `—`.

---

## Story 3 — `SKILL.md` Template Generation

### Manifest schema (`.writ/manifest.yaml`)

```yaml
version: 1
metadata:
  name: writ
  version: 0.10.0          # mirrors VERSION file; check enforced in Story 5
  description: "AI-powered development workflow framework — contract-first specs, multi-agent SDLC, automated quality gates."

commands:
  - name: plan-product
    file: commands/plan-product.md
    category: planning
    purpose: "Product planning with contract-first approach"
    tags: [planning, contract-first, plan-mode]

  - name: create-spec
    file: commands/create-spec.md
    category: planning
    purpose: "Contract-first feature specification creation"
    tags: [planning, spec, contract-first]

  # ... one entry per command in commands/

agents:
  - name: architecture-check-agent
    file: agents/architecture-check-agent.md
    purpose: "Pre-coding architectural validation (read-only PROCEED/CAUTION/ABORT)"
    model: medium

  - name: coding-agent
    file: agents/coding-agent.md
    purpose: "TDD implementation with worktree isolation"
    model: smart

  # ... one entry per agent in agents/

categories:
  - id: planning
    label: "Planning & Specification"
  - id: implementation
    label: "Implementation & Quality"
  - id: autonomy
    label: "Autonomous Execution"
  - id: release
    label: "Release & Delivery"
  - id: security
    label: "Security"
  - id: setup
    label: "Setup & Maintenance"
  - id: migration
    label: "Migration"
```

### `scripts/gen-skill.sh` — generator

```
Usage: scripts/gen-skill.sh [--dry-run] [--check]

Default:    Read .writ/manifest.yaml, regenerate SKILL.md body, write to disk
--dry-run:  Read manifest, build expected SKILL.md body in memory, print to stdout
--check:    Read manifest, build expected, diff against committed SKILL.md, exit 1 on diff

Behavior:
  - Preserves SKILL.md frontmatter (lines 1-4: --- name: writ description: ... ---)
  - Replaces body content from line 5 onward
  - Body structure:
      # Writ
      {static intro paragraph from manifest.metadata.description}
      ## System Instructions
      {static reference to system-instructions.md}
      ## Available Commands
      {generated tables grouped by category}
      ## Available Agents
      {generated table from agents:}
      ## Removed (Migration Notes)
      {static section preserved from current SKILL.md}

Dependencies:
  - yq (preferred) — `command -v yq && yq ...`
  - Fallback: pure-bash YAML reader for the limited subset used (no anchors, no flow style)
  - Reports clearly which mode is active

Exit codes:
  0 = success (or --check passed clean)
  1 = --check found drift, OR malformed manifest
  2 = manifest file missing
  3 = SKILL.md file missing or unreadable
```

### CI gate

`.github/workflows/eval.yml` (or extension of existing CI):

```yaml
- name: Verify SKILL.md is up to date with manifest
  run: bash scripts/gen-skill.sh --check
```

### Header comment in `SKILL.md`

After the frontmatter block, before the title:

```html
<!--
  This file is generated from .writ/manifest.yaml by scripts/gen-skill.sh.
  Do not edit by hand. Edit the manifest and regenerate.
  CI will fail if SKILL.md drifts from the manifest.
-->
```

---

## Story 4 — Preamble Enforcement for Commands

### `commands/_preamble.md` — content

Target ≤80 lines (eval check). Sections:

```markdown
# Writ Command Preamble

> Every command in `commands/` references this file. Standing instructions that
> apply across the surface area live here, not duplicated per command.

## Plan Mode Integrity (per Prime Directive)

When a command uses Plan Mode for discovery, the conversation is a phase — not the
deliverable. After discovery, resume the command's documented phases and produce
its documented artifacts. Planning commands create files and stop. They never
offer to implement, build, or code.

## File Organization

All work is organized into `.writ/`:

- `specs/` — feature contracts and stories
- `product/` — roadmap, mission, strategy
- `research/` — investigation outputs
- `decision-records/` — ADRs
- `knowledge/` — accumulating cross-cutting facts (decisions/conventions/glossary/lessons)
- `issues/` — fast-capture bugs/features
- `state/` — ephemeral runtime state (gitignored)

## Tool Selection

- **AskQuestion** — bounded decisions with enumerable options
- **Plan Mode** — open-ended discovery and shaping
- **todo_write** — multi-step task tracking (3+ steps)
- **Parallel tool calls** — when independent

## Knowledge Context

Before starting work, the orchestrator may load relevant entries from
`.writ/knowledge/`. Treat them as first-class context, not optional reading.

## Adapter Neutrality

Commands must work identically on Cursor, Claude Code, OpenClaw via the
generic tool-name vocabulary. No platform-specific runtime hooks.
```

### Per-command "References" section

Every file in `commands/` ends with:

```markdown
---

## References

- Standing instructions: [`commands/_preamble.md`](_preamble.md)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)
- {any other command-specific references}
```

If the command file already has a "## References" section (some do), augment rather than duplicate.

### Agent files

Agents in `agents/` get an analogous reference where applicable, pointing at `_preamble.md` and any agent-shared rules. Story 4 adds these alongside the command updates.

### Adapter doc updates

Each of `adapters/cursor.md`, `adapters/claude-code.md`, `adapters/openclaw.md` gains a short note explaining the preamble convention and how their platform loads it (e.g., "Cursor loads `_preamble.md` as part of the command file lookup; no special handling required").

---

## Story 5 — Eval Tier 1 (Static Checks)

### `scripts/eval.sh` — runner

```
Usage: scripts/eval.sh [--check=NAME] [--report=PATH] [--fix]

Default:        Run all checks, write report to .writ/state/eval-{date}.md, exit non-zero on any failure
--check=NAME:   Run only a named check (required-sections | anti-sycophancy | broken-refs | length | manifest | preamble | owner | prime-directive-sync)
--report=PATH:  Write report to PATH instead of default
--fix:          For checks that support auto-fix (e.g., add missing preamble reference), apply fixes; otherwise report

Exit codes:
  0 = all checks passed
  1 = at least one check found violations
  2 = a check failed to run (e.g., missing dependency)
```

### Check details

| Check ID | What it verifies | Failure output | Auto-fix? |
|---|---|---|---|
| `required-sections` | Every `commands/*.md` has `## Overview`, `## Invocation` (or note exempt), `## Command Process` (or equivalent like `## Phases`) | `commands/X.md: missing section "## Overview"` | No |
| `anti-sycophancy` | No banned phrases in `commands/*.md`, `agents/*.md`, `system-instructions.md`, `cursor/writ.mdc`. Banned phrases come from a list (extensible): "Great question!", "Excellent point!", "Absolutely!", "Perfect question", "What a wonderful idea" | `commands/X.md:42: banned phrase 'Great question!'` | No |
| `prime-directive-sync` | `system-instructions.md` and `cursor/writ.mdc` Prime Directive sections are byte-identical (between `## Prime Directive` and the next `##` heading) | `cursor/writ.mdc Prime Directive section drift detected; diff:\n...` | No |
| `broken-refs` | Markdown links of the form `(./...)`, `(../...)`, `(commands/...)` in `commands/`, `agents/`, `adapters/`, `system-instructions.md`, `SKILL.md` resolve to existing files; agent names referenced as `agents/X-agent.md` exist | `commands/X.md:15: broken ref to agents/missing-agent.md` | No |
| `length` | `spec-lite.md` ≤100 lines; `commands/_preamble.md` ≤80 lines; `commands/*.md` ≤2000 lines (catch-runaway threshold) | `commands/X.md: 2147 lines (limit 2000)` | No |
| `manifest` | `.writ/manifest.yaml` parses; every command/agent in manifest exists; no orphan files in `commands/` or `agents/` not in manifest (excluding `_preamble.md` and `_*.md` infra files) | `manifest: command 'X' references commands/X.md (does not exist)` or `commands/Y.md exists but not in manifest` | No |
| `preamble` | Every `commands/*.md` (excluding `_*.md`) contains a reference to `commands/_preamble.md` | `commands/X.md: missing reference to commands/_preamble.md` | Yes (`--fix` appends a References section) |
| `owner` | Every spec.md created on/after 2026-04-24 has `owner:` in frontmatter | `.writ/specs/X/spec.md: missing owner field` (legacy specs ignored) | No |

### CI gate

`.github/workflows/eval.yml`:

```yaml
name: Eval Tier 1
on: [pull_request, push]
jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0          # required for `owner` check (date determination via git log)
      - name: Install yq
        run: sudo snap install yq
      - name: Run eval
        run: bash scripts/eval.sh --report=eval-report.md
      - name: Upload report
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: eval-report
          path: eval-report.md
```

### Triage of pre-existing violations

Story 5's first task is a `bash scripts/eval.sh` run against the post-Story-1–4 surface. Each finding is either:
- Fixed in Story 5's PR (broken refs, missing sections), or
- Grandfathered with a comment in the file (`<!-- eval-exempt: reason -->`), with a follow-up issue in `.writ/issues/`

### Local dev workflow

```bash
# Run before pushing
bash scripts/eval.sh

# Auto-fix what can be auto-fixed
bash scripts/eval.sh --fix

# Run a single check
bash scripts/eval.sh --check=preamble
```

---

## Cross-Story Files Touched

Tracking surface area for boundary-computation purposes (per `2026-03-20-file-ownership-boundaries`):

| File / Path | Stories That Touch | Note |
|---|---|---|
| `.writ/knowledge/**` | 1 | Story 1 owns |
| `.writ/manifest.yaml` | 3, 5 | Story 3 creates; Story 5 reads |
| `commands/knowledge.md` | 1 | Story 1 owns |
| `commands/_preamble.md` | 4 | Story 4 owns |
| `commands/create-spec.md` | 2, 4 | Story 2 adds owner field; Story 4 adds preamble ref |
| `commands/implement-story.md` | 1, 4 | Story 1 adds knowledge hook; Story 4 adds preamble ref |
| `commands/verify-spec.md` | 2, 4, 5 | Story 2 adds Check 8; Story 4 adds preamble ref; Story 5 may amend |
| `commands/status.md` | 2, 4 | Story 2 adds owner display; Story 4 adds preamble ref |
| Other `commands/*.md` | 4 | Story 4 adds preamble references everywhere |
| `agents/coding-agent.md` | 1, 4 | Story 1 adds knowledge_context; Story 4 adds preamble ref |
| Other `agents/*.md` | 1, 4 | Story 1 may add knowledge_context to arch-check & review; Story 4 adds preamble refs |
| `SKILL.md` | 3 | Story 3 makes it a generator output |
| `scripts/gen-skill.sh` | 3 | Story 3 owns |
| `scripts/eval.sh` | 5 | Story 5 owns |
| `.github/workflows/eval.yml` | 3, 5 | Story 3 wires `gen-skill.sh --check`; Story 5 wires `eval.sh` |
| `adapters/cursor.md` | 1, 4 | Story 1 notes knowledge hook; Story 4 notes preamble convention |
| `adapters/claude-code.md` | 1, 4 | Same as above |
| `adapters/openclaw.md` | 1, 4 | Same as above |

The orchestrator (`/implement-story`) computes file boundaries per story from this table.

---

## Verification Strategy

This is a methodology framework — markdown + bash, no application code. "Tests" are:

| Story | Verification |
|---|---|
| 1 | `/knowledge "test entry"` produces conformant file; agent loads a backfilled entry on a follow-up task without prompt-side mention; README decision tree review |
| 2 | New spec via `/create-spec` has `owner:` field; `/verify-spec` reports legacy specs without warning; `/status` displays owners |
| 3 | `bash scripts/gen-skill.sh --dry-run` produces expected output; `--check` exits 0 against committed SKILL.md after regeneration; manifest schema rejects malformed entries |
| 4 | All command files reference `_preamble.md`; preamble loads correctly under each adapter (manual smoke test); `_preamble.md` ≤80 lines |
| 5 | `bash scripts/eval.sh` exits 0 against full post-Story-1–4 surface; CI gate fires on a deliberate violation in a test branch; auto-fix applies preamble references correctly |

---

## References

- Spec: [`../spec.md`](../spec.md)
- ADRs: [005](../../../decision-records/adr-005-knowledge-substrate-markdown-over-database.md), [006](../../../decision-records/adr-006-non-degrading-destination.md), [007](../../../decision-records/adr-007-team-audience-sequencing.md), [008](../../../decision-records/adr-008-spec-as-team-contract-moat.md)
- Research: [`2026-04-24-writ-vs-gstack-rigor-comparison.md`](../../../research/2026-04-24-writ-vs-gstack-rigor-comparison.md)
- Roadmap: [Phase 4](../../../product/roadmap.md#phase-4-production-grade-substrate-6-8-weeks)
