# Codex CLI Adapter — First-Class Platform Support

> **Status:** Complete
> **Created:** 2026-05-06
> **Owner:** Adam Sellke
> **Origin:** Promoted from `.writ/issues/features/2026-04-02-codex-openclaw-lifecycle-support.md` (Codex half only)
> **Related ADR:** `.writ/decision-records/adr-009-command-agent-skill-boundary.md` (amended by this spec)

---

## Specification Contract

**Deliverable:** Add Codex CLI as a first-class Writ install platform with a complete adapter (`adapters/codex.md`), six native subagent translations (`codex/agents/*.toml`), an AGENTS.md fenced-block integration convention, and full install/update/uninstall fanout via `--platform codex` across `install.sh`, `update.sh`, `unlink.sh`, `uninstall.sh`, and the `/update-writ`, `/reinstall-writ`, `/uninstall-writ` lifecycle commands. Includes a small ADR-009 amendment correcting the skills install path (`.codex/skills/` → `.agents/skills/` per the AgentSkills cross-platform standard).

**Origin:** Promoted from `.writ/issues/features/2026-04-02-codex-openclaw-lifecycle-support.md` — Codex half only. OpenClaw lifecycle support remains open as a follow-up spec; the source issue's `spec_ref` will be updated to point here, but the issue stays open with a note that OpenClaw is unaddressed.

**Must Include:** A working `bash scripts/install.sh --platform codex` that produces a Codex-native installation a user can immediately use — meaning `AGENTS.md` is updated (or created) with a Writ block, `.codex/agents/*.toml` populates with the six translated agents, `.agents/skills/` receives any skills present in the manifest, and `.codex/config.toml` is seeded with sensible defaults. The `/implement-story` pipeline must run end-to-end on Codex with parallel subagent spawning intact.

**Hardest Constraint:** Codex's surface differs from Cursor/Claude in three load-bearing ways — slash commands aren't user-extensible (so AGENTS.md carries invocation), agents are TOML not YAML-frontmatter Markdown (so we maintain a third parallel agent source folder), and skills install at `.agents/skills/` not `.codex/skills/` (so the install fanout breaks the platform-directory pattern that Cursor/Claude follow). Drift between `agents/*.md`, `claude-code/agents/*.md`, and `codex/agents/*.toml` is a real risk over time and the spec must build in a sanity check (lint or `/refresh-command` extension), not just hope contributors remember.

### Experience Design

**Entry points:**
- **User (fresh install):** `bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/install.sh) --platform codex` from project root
- **User (update):** `bash <(curl -s …/update.sh) --platform codex` or `/update-writ`
- **User (uninstall):** `bash <(curl -s …/uninstall.sh) --platform codex` or `/uninstall-writ`
- **Codex session start:** `codex` — Codex auto-reads `AGENTS.md`, sees the `<!-- writ:start -->` block, recognizes Writ commands and agents

**Happy path (install on a project without prior AGENTS.md):**
1. Run installer
2. Output: `⚡ Writ Installer (Codex CLI)` banner
3. Inventory shown: command count, agent count, skills count, version
4. Six steps execute: commands → agents (`.codex/agents/*.toml`) → skills (`.agents/skills/`) → AGENTS.md (created with Writ block) → `.codex/config.toml` (seeded once) → manifest written
5. Summary: `✅ Writ installed for Codex CLI! (version: …)` plus overlay counts
6. Open `codex` → Codex reads AGENTS.md → user types "run /create-spec for X" or "create a spec for X" → assistant follows `.writ/commands/create-spec.md` workflow

**Happy path (install on a project with existing AGENTS.md):**
1. Same install banner and inventory
2. AGENTS.md merger detects existing content, finds no `<!-- writ:start -->` marker, appends Writ block at end of file
3. Summary line: `AGENTS.md: Writ block appended (existing content preserved)`
4. Subsequent updates only modify content between the markers; everything else is byte-stable

**Happy path (`/implement-story` running on Codex):**
1. Orchestrator session reads `.writ/commands/implement-story.md`
2. Spawns `architecture-check` agent via Codex's native subagent system (TOML-defined, `sandbox_mode = "read-only"`)
3. Result returned, orchestrator spawns `coder` agent (`sandbox_mode = "workspace-write"`)
4. Lint/typecheck inline by orchestrator
5. Spawns `reviewer` agent (`sandbox_mode = "read-only"`) — review feedback parsed
6. If FAIL → re-spawns coder with feedback (max 3 iterations)
7. Spawns `tester` agent
8. Spawns `documenter` agent
9. Orchestrator updates story status, commits

**Moment of truth:** A user who has used Writ on Cursor or Claude Code installs it on a fresh Codex project, runs `/create-spec` and `/implement-spec`, and gets the same artifacts and same multi-agent quality gates with no functionality regression. Codex's `/agent` thread switching shows the spawned subagents. Read-only review is enforced by Codex's sandbox, not just by prompt convention.

**Feedback model:**
- Install/update progress: same `[N/M]` step format Cursor/Claude installs use
- AGENTS.md merger: dedicated summary line (`AGENTS.md: Writ block appended` / `Writ block updated` / `Writ block preserved (local modifications)`)
- Per-file overlay status: `✨ New / 🔄 Update / ⚡ Preserved / ✓ Unchanged` symbols carried over from existing platforms
- ADR-009 amendment: visible in repo diff at PR time

**Error experience:**

| Failure mode | What user sees | Recovery path |
|---|---|---|
| Existing AGENTS.md without Writ block on first install | Block appended; original content preserved verbatim | None needed — happy path |
| Existing AGENTS.md with Writ block on update | Block replaced atomically; surrounding content untouched | None needed — happy path |
| User-modified Writ block detected on update | `⚡ Preserved: AGENTS.md (local modifications in writ block)` warning | Run `--force` to overwrite; or merge manually and re-run |
| Combined AGENTS.md exceeds Codex 32 KiB cap after install | Installer warns: `⚠️ AGENTS.md is N KiB, exceeds default Codex cap (32 KiB). Configure project_doc_max_bytes or split via AGENTS.override.md.` | User edits config or splits content |
| `.codex/config.toml` already exists on first install | Skipped silently; existing config preserved | None — install-once semantics |
| `codex/agents/*.toml` source missing on installer | Warning: `⚠️ codex/agents/ source missing — agent install skipped`; commands and skills still install | Re-run from a complete Writ source |
| Drift detected by `/refresh-command --check-parity` | Output: `⚠️ Agent X.md has no counterpart in codex/agents/` | Author the missing TOML file or document the platform-specific exclusion |

**Empty / first-use states:**
- Install on a project with no `.git` directory: works; Codex's `project_root_markers` config controls discovery, installer documents the limitation
- Install with `--dry-run` on a fresh project: shows what would be created without writing anything
- Codex session opened before install completes (race condition): AGENTS.md may be partially written; subsequent `codex` restart picks up the complete state

**Responsive / discoverability behavior:**
- AGENTS.md Writ block includes a `## Built-in Codex Commands vs Writ Commands` callout with the naming-conflict table (Codex `/status` vs Writ status, Codex `/review` vs Writ review)
- AGENTS.md Writ block lists all available Writ commands with one-line purposes — same source-of-truth as `claude-code/CLAUDE.md` and `cursor/writ.mdc` Commands sections, kept in sync via a shared template

### Business Rules

**AGENTS.md ownership:**
- Writ owns content between `<!-- writ:start -->` and `<!-- writ:end -->` markers exclusively
- Everything outside the markers is user-owned and never touched by install/update/uninstall
- Markers are HTML comments (Codex parses Markdown without expanding them; they don't render in the user's view but are visible in diffs)
- Uninstall removes the block and the surrounding markers; if AGENTS.md becomes empty after removal, the file is also removed

**Skills install path is platform-divergent:**
- Cursor → `.cursor/skills/<name>/SKILL.md`
- Claude Code → `.claude/skills/<name>/SKILL.md`
- Codex → `.agents/skills/<name>/SKILL.md` (cross-platform AgentSkills standard)
- ADR-009 amended to record this divergence; the amendment notes that the AgentSkills standard's `.agents/` namespace is the cross-platform-readable path Codex chose to support, while Cursor and Claude Code use platform-namespaced paths

**`.codex/config.toml` is install-once:**
- Installer writes baseline on first install: `[agents] max_threads = 6, max_depth = 1`, `[features] codex_hooks = false`, MCP placeholder block (commented out)
- Subsequent updates never overwrite — file is treated as user-owned config after first install (matches Claude Code's `settings.local.json` pattern)
- Manifest tracks initial baseline hash so `--force` install can offer to reset, but default behavior preserves user customization

**Codex agent source-of-truth:**
- Six TOML files live in `codex/agents/<name>.toml` at product source root (parallel to `agents/*.md` and `claude-code/agents/*.md`)
- Required TOML fields: `name`, `description`, `developer_instructions` (the latter sourced from the body of `agents/<name>.md`)
- Sandbox-mode mapping table:
  - `architecture-check-agent` → `read-only`
  - `coding-agent` → `workspace-write`
  - `review-agent` → `read-only`
  - `testing-agent` → `workspace-write` (may install dependencies)
  - `documentation-agent` → `workspace-write`
  - `user-story-generator` → `workspace-write`
  - `visual-qa-agent` → `read-only`
- Optional TOML fields when valuable: `model` (preserve `model: fast` cases as `model = "gpt-5.4-mini"` or equivalent fast tier), `nickname_candidates` for UI distinction in parallel runs

**Self-dogfooding:**
- `.codex/agents/` symlinks to `codex/agents/` on the Writ repo (matches `.cursor/` and `.claude/` patterns)
- AGENTS.md stays a real file (already the case)
- `.codex/config.toml` is gitignored on the Writ repo (per-developer)
- `unlink.sh --platform codex` understands the symlink-vs-copy distinction same as the existing platforms

**No command renames:**
- Direct collisions (`/status`, `/review`) handled via documentation only
- AGENTS.md Writ block includes a callout explaining: Codex's bare `/status` and `/review` continue to work as Codex defines them; Writ's are reached by phrasing intent ("run writ status", "writ review", or letting the assistant route based on context)

**Drift sanity check:**
- `/refresh-command` extended with a `--check-parity` mode (or always-on for adapters)
- Lints: every agent file in `agents/*.md` should have a counterpart in `claude-code/agents/<name>.md` AND `codex/agents/<name>.toml`
- Output: warnings only (not hard fails) — some agents may legitimately be platform-specific in the future
- `--check-parity` exits non-zero only if a documented exclusion list is missing

**OpenClaw out of scope:**
- 2026-04-02 source issue covers both platforms; this spec ships Codex only
- OpenClaw lifecycle/install deferred to a follow-up spec (referenced in the issue's status note)
- The issue stays open after this spec ships, with the OpenClaw half flagged

### Detailed Requirements

**Files created in product source:**
- `adapters/codex.md` — full adapter doc, depth matching `claude-code.md`
- `codex/agents/architecture-check-agent.toml`
- `codex/agents/coding-agent.toml`
- `codex/agents/review-agent.toml`
- `codex/agents/testing-agent.toml`
- `codex/agents/documentation-agent.toml`
- `codex/agents/user-story-generator.toml`
- `codex/agents/visual-qa-agent.toml`
- `codex/AGENTS.md.template` — the Writ block content that gets injected (kept separate from the install logic for easier review)
- `codex/config.toml.template` — the baseline `.codex/config.toml` content for fresh installs

**Files modified in product source:**
- `scripts/install.sh` — `--platform codex` branch, AGENTS.md merger logic, skills path resolution, `.codex/config.toml` seeding
- `scripts/update.sh` — same platform branch with three-way overlay
- `scripts/unlink.sh` — symlink/copy detection for `.codex/`
- `scripts/uninstall.sh` — Codex paths, AGENTS.md block removal
- `commands/update-writ.md` — Codex platform detection and overlay messaging
- `commands/reinstall-writ.md` — Codex platform paths
- `commands/uninstall-writ.md` — Codex platform paths and AGENTS.md cleanup
- `commands/refresh-command.md` — `--check-parity` lint extension
- `.writ/decision-records/adr-009-command-agent-skill-boundary.md` — Amendments section
- `README.md` — Platform Support table updated to include Codex
- `AGENTS.md` (this repo) — updated reference to point at the now-existing `adapters/codex.md`
- `.cursor/system-instructions.md` and `claude-code/CLAUDE.md` — if they enumerate platforms, update to include Codex

**Files self-dogfood-symlinked on the Writ repo:**
- `.codex/agents/` → `codex/agents/`
- `.agents/skills/` → `skills/` (matches the Cursor/Claude pattern of platform-installation symlinks)

**Manifest extension:**
- `.codex/.writ-manifest` follows the same format as `.cursor/.writ-manifest` and `.claude/.writ-manifest`
- Tracks: commands hashes, agent TOML hashes, skill SKILL.md hashes, AGENTS.md Writ block hash, `.codex/config.toml` baseline hash
- Manifest format keeps `# platform: codex` line for installer self-identification

### Implementation Approach

**Story sequencing rationale:**
- Story 1 (ADR amendment + skills path) is foundational and small — locks the correct path before downstream stories use it
- Story 2 (TOML translations + parity lint) builds the agent inventory before scripts need to fan it out
- Story 3 (adapter doc + AGENTS.md template) defines the contract the install scripts implement
- Stories 4–6 are the install/update/uninstall pipeline, sequenced by file dependency
- Story 7 wraps up: README, smoke verification, issue writeback

**Drift mitigation strategy:**
- Parity lint added in Story 2 catches missing TOMLs immediately
- Smoke verification in Story 7 runs end-to-end on a sandbox project — catches integration drift between TOML semantics and orchestrator expectations
- AGENTS.md template lives in `codex/AGENTS.md.template` rather than inline in `install.sh` — easier to review, lint, and update without touching shell logic

**Test strategy (manual smoke + lightweight automation):**
- Bash unit-test sketch for install.sh AGENTS.md merger (`--dry-run` plus content fixtures)
- Manual smoke: run `install.sh --platform codex` on a sandbox project; open Codex; run `/create-spec` and `/implement-story` end-to-end
- Diff-based verification of AGENTS.md byte-stability outside the Writ block

**Risk mitigation for `/refresh-command` extension:**
- Add `--check-parity` as a new flag on the existing command, not a replacement for any current behavior
- Existing `/refresh-command` flow unchanged when the flag is absent
- Lint is opt-in for a few cycles before being baked into default behavior (pending real-world drift signal)

## Current State

- `adapters/cursor.md`, `adapters/claude-code.md`, `adapters/openclaw.md` exist; `adapters/codex.md` does not, despite being referenced in `AGENTS.md`
- `install.sh`, `update.sh`, `unlink.sh`, `uninstall.sh` support `--platform cursor|claude` only
- `/update-writ`, `/reinstall-writ`, `/uninstall-writ` know about Cursor and Claude Code paths only
- ADR-009 declares `.codex/skills/` as the planned Codex skills install path; the AgentSkills standard and Codex docs use `.agents/skills/`
- No `codex/agents/` source folder exists; no TOML translations of any Writ agent
- Repo root `AGENTS.md` exists as a real file, manually maintained, but its content is a project-overview document — not the user-installation Writ block this spec introduces
- Pre-existing issue `.writ/issues/features/2026-04-02-codex-openclaw-lifecycle-support.md` documents this gap and adds OpenClaw to the same scope; that issue's `spec_ref` is unset

## Expected Outcome

- A Codex CLI user runs `bash scripts/install.sh --platform codex` and gets a working Writ installation with full multi-agent SDLC pipeline support
- `/create-spec`, `/implement-spec`, `/implement-story`, and the rest of the Writ command set work on Codex with the same artifacts and quality gates as Cursor/Claude Code
- Read-only review is enforced via Codex's native sandbox, not just prompt convention
- Skills install at the AgentSkills standard path (`.agents/skills/`) and ADR-009 reflects this
- Drift between platform agent variants is observable via `/refresh-command --check-parity`
- The 2026-04-02 issue's `spec_ref` points to this spec; the OpenClaw half is explicitly deferred and visible
- Writ's README accurately reflects three-platform support (Cursor, Claude Code, Codex CLI)

## Success Criteria

1. **Adapter doc parity:** `adapters/codex.md` exists with sections matching `adapters/claude-code.md` (Installation, Tool Mapping, Skills, Workflow Patterns, Gotchas). Reviewed for accuracy against Codex's official docs.
2. **Native subagent install:** `bash scripts/install.sh --dry-run --platform codex` lists six agents under `.codex/agents/*.toml` with correct `sandbox_mode` values; actual install creates them; running `/agent` in Codex CLI shows them in the picker.
3. **AGENTS.md block lifecycle:** Install on a project without AGENTS.md creates it with a Writ block; install on a project with existing user content appends only the block and preserves everything else byte-for-byte (verified by hash comparison); update modifies only the block content; uninstall removes only the block.
4. **Lifecycle command parity:** `/update-writ`, `/reinstall-writ`, `/uninstall-writ` recognize a Codex installation via `.codex/.writ-manifest` and operate on the correct paths.
5. **End-to-end pipeline smoke:** A manual run of `/implement-story` on a sample Codex installation completes architecture-check → coding → review → testing → documentation with read-only sandbox enforcement on the review phase.
6. **ADR-009 amendment lands:** A new "Amendments" section records the corrected skills path with rationale and links to the AgentSkills standard.
7. **Drift sanity check active:** `/refresh-command --check-parity` flags any agent in `agents/*.md` lacking a counterpart in `codex/agents/`. Verified by deleting one TOML temporarily and observing the warning.
8. **Source issue updated:** `.writ/issues/features/2026-04-02-codex-openclaw-lifecycle-support.md` `spec_ref` set to `.writ/specs/2026-05-06-codex-cli-adapter/spec.md`; a "Codex shipped, OpenClaw deferred" note added in the issue's Notes section.
9. **README updated:** Platform Support table includes Codex CLI with install command and feature parity status.

## Scope Boundaries

**Included:**
- `adapters/codex.md` (full adapter doc)
- `codex/agents/*.toml` (seven TOML translations covering all current agents)
- `codex/AGENTS.md.template` (Writ block content)
- `codex/config.toml.template` (`.codex/config.toml` baseline)
- AGENTS.md fenced-block convention, marker logic, and merge behavior
- `install.sh`, `update.sh`, `unlink.sh`, `uninstall.sh` `--platform codex` support
- Manifest tracking and three-way overlay for Codex
- `.codex/config.toml` install-once seeding
- `/update-writ`, `/reinstall-writ`, `/uninstall-writ` Codex platform branches
- ADR-009 amendment (corrected skills path)
- `/refresh-command --check-parity` lint
- README and product documentation updates
- Smoke verification of end-to-end install + `/implement-story` pipeline on Codex

**Excluded:**
- OpenClaw install/lifecycle support — deferred to follow-up spec
- Codex hooks (`hooks.json`, `[hooks]` in TOML) integration — additive future work
- Plugin packaging (Codex's `plugins` distribution mechanism) — future amplification
- Renaming any Writ commands to dodge built-in Codex slash commands
- Migrating Writ commands to Codex skills (preserves ADR-009 boundary)
- Codex-specific spec or agent *content* variants — same `commands/` and `agents/` markdown sources serve all platforms; only the platform-native packaging differs
- Migrating existing Cursor/Claude installations to also use `.agents/skills/` — those stay on platform-namespaced paths

## Technical Concerns

- **AGENTS.md size pressure.** Codex's default 32 KiB cap is the hard ceiling. The Writ block is an *index* (table of available commands/agents + invocation guidance), not a full restatement of `system-instructions.md`. Block budget: ≤8 KiB to leave room for project-specific content above and below.
- **Drift between three agent formats.** `agents/*.md`, `claude-code/agents/*.md`, `codex/agents/*.toml`. The parity lint mitigates but doesn't eliminate. Acceptance: this is the cost of supporting platforms with genuinely different native formats.
- **Sandbox-mode mapping.** Codex's `sandbox_mode` (`read-only` / `workspace-write` / `danger-full-access`) is coarser than Cursor's `readonly: true` and Claude's `permissionMode`. Mapping decisions are explicit per agent (see Business Rules table) and documented in `adapters/codex.md`.
- **`/refresh-command` extension scope.** Adding a parity check to a high-traffic command requires care. Story-level acceptance criteria mandate that existing command behavior is unchanged when `--check-parity` is absent.
- **Codex docs may evolve.** The TOML schema for custom agents is described as "may evolve as authoring and sharing mature" in OpenAI's docs. Spec records the current schema (May 2026); future maintenance may need to track schema changes via the parity lint or a fresh adapter audit.

## Cross-Spec Overlap

- **`.writ/issues/features/2026-04-02-codex-openclaw-lifecycle-support.md`** (open issue) — this spec consumes the Codex half. Source issue stays open with OpenClaw half explicitly deferred. `spec_ref` set to this spec on creation.
- **`.writ/specs/2026-05-03-skills-foundation/`** (Complete) — established the `.cursor/skills/` and `.claude/skills/` install patterns. This spec extends with `.agents/skills/` for Codex and amends ADR-009. Treats the foundation spec's invariants (manifest schema, overlay logic, `disable-model-invocation: true`) as inputs.
- **`.writ/specs/2026-04-28-daily-writ-update-check/`** (Complete) — established the daily update check protocol that `/update-writ` already implements. Codex platform branches in lifecycle commands inherit this protocol unchanged.

## Implementation Notes

- This spec assumes Codex CLI behaves as documented in OpenAI's published guides as of May 2026. If material schema or capability changes ship from upstream during implementation, story-level adjustments may be needed.
- The TOML-to-Markdown drift problem is structurally similar to the Markdown-with-YAML-frontmatter drift that already exists between `agents/*.md` and `claude-code/agents/*.md`. The `--check-parity` lint applies to all three.
- AGENTS.md merge logic intentionally uses HTML-comment markers rather than YAML frontmatter or TOML — markers must be invisible in rendered Markdown and stable across editors. HTML comments meet both requirements.
