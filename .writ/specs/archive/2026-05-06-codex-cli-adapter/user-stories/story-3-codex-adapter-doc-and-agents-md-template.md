# Story 3: Codex Adapter Doc & AGENTS.md Block Template

> **Status:** Complete ✅
> **Priority:** High
> **Dependencies:** Story 2

## User Story

**As a** Codex CLI user discovering Writ for the first time, and as a Writ contributor about to wire `--platform codex` into the install scripts
**I want to** read a complete adapter doc that explains exactly how Writ maps onto Codex's surface, and find a concrete `codex/AGENTS.md.template` plus `codex/config.toml.template` checked into the repo
**So that** users can decide whether the platform integration fits their workflow before installing, and Story 4's install-script work has a stable contract to inject — not a moving target

## Acceptance Criteria

**AC-1: `adapters/codex.md` exists with parity to `adapters/claude-code.md`**

- **Given** `adapters/cursor.md`, `adapters/claude-code.md`, and `adapters/openclaw.md` exist and define the depth bar for an adapter doc
- **When** Story 3 ships
- **Then** `adapters/codex.md` exists with at minimum these sections in order: `Overview`, `Installation` (with both `Automated` and `Manual` subsections), `Key Features Used`, `Tool Mapping` (table), `Skills`, `Workflow Patterns`, `CLI Usage`, `Command Workflow Integrity`, `Built-in Codex Commands vs Writ Commands` (the naming-conflict callout), and `Gotchas`; total length is comparable to `adapters/claude-code.md` (no shorter than 80% of its line count, no longer than 150% — clarity beats completeness)

**AC-2: Tool Mapping table is complete and accurate**

- **Given** Codex exposes a documented set of tools and primitives (`Read`, `Write`, `Edit`, `Bash`, `Grep`, `Glob`, `/agent`, `/skills`, `$skill-name`, `/fork`, `/side`, `AGENTS.md` hierarchy, `.codex/config.toml`)
- **When** a reader opens the Tool Mapping section of `adapters/codex.md`
- **Then** the table maps every Writ-relevant Codex primitive to its Writ usage with one-line notes; all seven Writ agents are listed with their `sandbox_mode` (sourced from Story 2's TOMLs); and the table is verifiable line-by-line against Codex's official docs

**AC-3: `codex/AGENTS.md.template` exists, is ≤8 KiB, and contains the required block content**

- **Given** the spec mandates an 8 KiB block budget and a specific content list (project overview, command table with one-line purposes, agent list with TOML locations, invocation guidance, naming-conflict callout)
- **When** the template ships
- **Then** `codex/AGENTS.md.template` exists; `wc -c codex/AGENTS.md.template` reports ≤8192 bytes; the file contains every required content element; and it begins with text that makes the file's purpose obvious to a contributor reading it cold (e.g., a leading `<!-- This is the Writ-managed block content injected into AGENTS.md between writ:start/writ:end markers. Edit here, not in user installations. -->`)

**AC-4: `codex/config.toml.template` exists with the documented baseline**

- **Given** the spec specifies the install-once baseline as `[agents] max_threads = 6, max_depth = 1`, `[features] codex_hooks = false`, and a commented-out MCP placeholder block
- **When** the template ships
- **Then** `codex/config.toml.template` exists at the product root, parses as valid TOML, contains exactly those baseline values (no surprise additions), the MCP block is commented but discoverable (the user can uncomment to enable), and a leading comment explains that this file is install-once and Writ never modifies it after first install

**AC-5: Naming-conflict callout matches Codex's actual built-in slash commands**

- **Given** Codex CLI ships built-in commands including `/plan`, `/review`, `/init`, `/status`, `/agent`, `/fork`, `/side` (and possibly more — verified at implementation time)
- **When** a reader opens the `Built-in Codex Commands vs Writ Commands` section of `adapters/codex.md` and the corresponding callout in `codex/AGENTS.md.template`
- **Then** every documented direct collision (Writ has a same-named command) is listed with the resolution model — Codex's built-in works as Codex defines it; Writ's same-named command is reached by phrasing intent ("run writ status", "writ review") or by routing context; the callout is explicit that Writ does *not* rename its commands to dodge the conflict (consistent with the spec's "No command renames" business rule)

## Implementation Tasks

- [x] **3.1** Author a documentation review checklist as a working document (jot in `/tmp/codex-adapter-review-checklist.md` or a scratch file) covering: (a) every section heading in `adapters/claude-code.md`, (b) every Codex primitive that needs mapping, (c) every official Codex doc URL to cross-check against, (d) the `wc -c` budget for the AGENTS.md template, (e) the live `/` slash popup contents to verify naming conflicts against
- [x] **3.2** Author `adapters/codex.md` matching `adapters/claude-code.md` depth: write all required sections in order (Overview → Installation → Key Features Used → Tool Mapping → Skills → Workflow Patterns → CLI Usage → Command Workflow Integrity → Built-in Codex Commands vs Writ Commands → Gotchas); pull TOML inventory from Story 2's `codex/agents/*.toml` files for the Tool Mapping agent rows
- [x] **3.3** Author `codex/AGENTS.md.template` with the Writ-managed block content (project overview, command table, agent list with TOML locations, invocation guidance, naming-conflict callout); after each draft pass, run `wc -c codex/AGENTS.md.template` and confirm ≤8192 bytes — if over, cut nice-to-haves first (verbose phrasing, redundant examples), prioritize the command table and naming-conflict callout
- [x] **3.4** Author `codex/config.toml.template` with the baseline `[agents]` (`max_threads = 6`, `max_depth = 1`), `[features] codex_hooks = false`, commented-out MCP placeholder block, and a leading comment explaining install-once semantics; verify it parses by running `python3 -c "import tomllib; tomllib.loads(open('codex/config.toml.template').read())"` (or equivalent Bash/Node TOML parser)
- [x] **3.5** Cross-reference `adapters/codex.md` against Codex's official docs (AGENTS.md guide, slash commands page, skills page, custom subagents/TOML schema) for every claim made — if a claim cannot be verified against an official source, either remove it or mark it as "behavior observed in Codex CLI vN.N.N" with a date
- [x] **3.6** Verify the naming-conflict table matches the live Codex `/` slash popup (open `codex` in a sandbox, type `/`, screenshot or transcribe the full list, cross-check against the callout) — if Codex has built-ins beyond `/plan`, `/review`, `/init`, `/status`, `/agent`, `/fork`, `/side` that collide with Writ commands, add them to the callout
- [x] **3.7** Verify all five acceptance criteria: `adapters/codex.md` parity (line count and section coverage), Tool Mapping completeness, AGENTS.md template size budget (`wc -c`), config.toml.template baseline contents, naming-conflict callout accuracy; mark story Complete

## Notes

**Why this story sits between TOML translations (Story 2) and install scripts (Story 4).** Story 2 produces the agent inventory; Story 3 documents and packages it. Story 4 wires the scripts. If we authored the scripts before the docs, the install summary lines, the AGENTS.md merge logic, and the user-facing inventory could drift from each other. By locking the documentation contract first, Story 4 has a fixed target.

**The adapter doc is one of the user's first touchpoints.** Clarity beats completeness. Over-explaining hurts more than under-explaining; users will follow up with `/help` or read the spec if they want depth. Aim for the same prose density as `adapters/claude-code.md` — confident, tight, no hedging.

**The 8 KiB AGENTS.md block budget is a hard ceiling, not a target.** Codex's default `project_doc_max_bytes` is 32 KiB and the user's own AGENTS.md content shares the budget. Every byte in the Writ block is a byte the user can't use for their project context. If the draft exceeds 8 KiB, cut — don't ship over budget and document the workaround.

**The config.toml template is install-once.** Once it's at the user's `.codex/config.toml`, Writ never updates it (matches Claude Code's `settings.local.json` pattern). Defaults must therefore be conservative: users opt *into* hooks, not opt out. The MCP block is commented because we don't know which MCP servers a user wants — the placeholder shows the structure without enabling anything.

**Naming conflicts: coexistence model, not deprecation.** The callout should make clear that Codex's bare `/status` and `/review` continue to work as Codex defines them. Writ's same-named commands are reached by phrasing intent ("run writ status") or by the assistant routing on context. Neither side is renamed or deprecated — both coexist. This matches the spec's "No command renames" business rule and the AGENTS.md ownership rule (Writ owns content, not behavior).

**Drift risk between the AGENTS.md template and the same content in `claude-code/CLAUDE.md` / `cursor/writ.mdc`.** All three are platform-native packagings of the same conceptual content (Writ identity, command list, agent list, invocation guidance). They will drift over time. Story 3 doesn't try to solve this — the parity lint extension in Story 7 (`/refresh-command --check-parity` for adapter content) is where it's caught. For now, hand-author each file in its native idiom; don't try to share content programmatically across them.

**TOML enumeration in the adapter doc.** Story 2 produces seven TOMLs (`architecture-check-agent`, `coding-agent`, `review-agent`, `testing-agent`, `documentation-agent`, `user-story-generator`, `visual-qa-agent`). All seven appear in both `adapters/codex.md`'s Tool Mapping section *and* the AGENTS.md template's agent list with their TOML paths. If Story 2's outputs differ from this list (e.g., an agent is renamed), Story 3's content must follow.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] `adapters/codex.md` reviewed against `adapters/claude-code.md` depth (line count within 80–150%)
- [x] `codex/AGENTS.md.template` confirmed ≤8 KiB via `wc -c`
- [x] `codex/config.toml.template` parses as valid TOML
- [x] Naming-conflict callout verified against the live Codex `/` slash popup
- [x] Code/docs reviewed

## Context for Agents

After reading `spec.md` and `sub-specs/technical-spec.md`, the following spec elements apply specifically to this story:

- **Error map rows:** None directly — Story 3 produces documentation and templates, not runtime code that can fail. Error handling for AGENTS.md merge cases (missing markers, oversize, etc.) is owned by Story 4's install-script work; Story 3 only documents the *shape* of the block that Story 4 will inject.
- **Shadow paths:** `Install on existing AGENTS.md` (the AGENTS.md template content must read cleanly when *appended* to existing user content — no assumptions of being at the top of the file) and `Update` (the block content must be safe to replace atomically without surrounding context — no Markdown link references that resolve only relative to the user's content).
- **Business rules:** `AGENTS.md ownership` (the template content lives between the markers, never outside), `AGENTS.md size pressure` (≤8 KiB budget — see `spec.md` → `## Technical Concerns`), `No command renames` (the naming-conflict callout describes coexistence, not deprecation; see `spec.md` → `## Business Rules` → `No command renames`), `Naming-conflict resolution via callout` (documentation-only, no logic).
- **Experience:** Entry points (the user's first touchpoint after install is `codex` reading the new AGENTS.md block — the template content shapes that first impression; see `spec.md` → `## Experience Design` → `Entry points`), Happy path on existing AGENTS.md (the template must work as appended content; see `spec.md` → `## Experience Design` → `Happy path (install on a project with existing AGENTS.md)`), Responsive/discoverability behavior (the naming-conflict callout *is* the discoverability mechanism — when a user types `/status` and Codex's built-in runs, the callout in their AGENTS.md is what tells them how to reach Writ's status; see `spec.md` → `## Experience Design` → `Responsive / discoverability behavior`).
- **Files in scope:** `adapters/codex.md` (new), `codex/AGENTS.md.template` (new), `codex/config.toml.template` (new).
- **Files explicitly out of scope:** `scripts/install.sh` and the `--platform codex` branch wiring (Story 4), `codex/agents/*.toml` (Story 2 — Story 3 *reads* them for the adapter doc Tool Mapping but does not author or modify them), the parity lint in `/refresh-command` (Story 7), README updates (Story 7).
- **Reference files for depth/style:** `adapters/claude-code.md` (depth target, section order), `adapters/cursor.md` (alternate model, similar ground), `adapters/openclaw.md` (Tool Mapping table reference), `claude-code/CLAUDE.md` (shape reference for the AGENTS.md template), `cursor/writ.mdc` (Cursor's project rules — same identity content, different idiom), `commands/_preamble.md` (the AGENTS.md template should point at it for shared command preamble).
