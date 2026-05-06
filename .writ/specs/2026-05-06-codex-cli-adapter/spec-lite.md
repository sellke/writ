# Codex CLI Adapter (Lite)

> Source: .writ/specs/2026-05-06-codex-cli-adapter/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Add Codex CLI as a first-class Writ install platform — adapter doc, seven TOML agent translations, AGENTS.md fenced-block integration, full install/update/uninstall pipeline.

**Implementation Approach:**
- AGENTS.md as Codex entry point (no slash-command extension); fenced `<!-- writ:start -->`/`<!-- writ:end -->` markers delimit Writ-owned content
- Native Codex subagents via TOML in `codex/agents/*.toml`; install fans out to `.codex/agents/`
- Skills install at `.agents/skills/` (AgentSkills standard); ADR-009 amended for the corrected path
- `.codex/config.toml` is install-once (user-owned after baseline); manifest tracks baseline hash for `--force` reset
- Self-dogfood symlinks: `.codex/agents/` → `codex/agents/` on Writ repo
- No command renames; direct collisions (`/status`, `/review`) handled via documentation

**Files in Scope:**
- `adapters/codex.md` (new) — adapter doc matching `claude-code.md` depth
- `codex/agents/*.toml` (seven new files) — TOML translations of all Writ agents
- `codex/AGENTS.md.template` (new) — Writ block content
- `codex/config.toml.template` (new) — baseline config
- `scripts/{install,update,unlink,uninstall}.sh` — `--platform codex` branches
- `commands/{update-writ,reinstall-writ,uninstall-writ}.md` — Codex paths
- `commands/refresh-command.md` — `--check-parity` lint extension
- `.writ/decision-records/adr-009-command-agent-skill-boundary.md` — Amendments section
- `README.md` — Platform Support table

**Error Handling:**
- Existing AGENTS.md without Writ block → append, preserve original
- User-modified Writ block on update → preserve with `⚡` warning (overlay semantics)
- AGENTS.md exceeds 32 KiB after install → installer warns, points to `project_doc_max_bytes` config
- `.codex/config.toml` exists on first install → skipped silently (install-once)

**Integration Points:**
- Inherits manifest format and three-way overlay logic from existing platforms
- Inherits `disable-model-invocation: true` skill convention from skills-foundation spec
- Daily update check protocol (`.writ/state/writ-update-check.json`) unchanged

**Line Budget Constraints:**
- AGENTS.md Writ block budget: ≤8 KiB (leaves room for user content under 32 KiB Codex cap)

---

## For Review Agents

**Acceptance Criteria:**
1. `bash scripts/install.sh --dry-run --platform codex` lists seven agents and skills with correct paths
2. AGENTS.md byte-stability outside Writ block verified via hash comparison
3. `/agent` picker in Codex CLI shows installed Writ agents by name
4. `/refresh-command --check-parity` flags missing TOML counterparts (verified by temporarily deleting one)
5. End-to-end `/implement-story` smoke run completes with read-only sandbox on review phase
6. ADR-009 amendment exists with corrected skills path and AgentSkills rationale
7. Source issue's `spec_ref` updated; OpenClaw deferred note added

**Business Rules:**
- AGENTS.md ownership: Writ owns content between `<!-- writ:start -->` / `<!-- writ:end -->` markers only
- Skills path is platform-divergent: Cursor `.cursor/skills/`, Claude `.claude/skills/`, Codex `.agents/skills/`
- `.codex/config.toml` is install-once (user-owned after first install)
- Sandbox mode mapping per agent: architecture-check/review/visual-qa = read-only; coder/tester/documenter/story-gen = workspace-write
- No command renames; AGENTS.md callout documents conflicts with Codex's `/status`, `/review`
- OpenClaw stays out of scope; source issue stays open with deferred note

**Experience Design:**
- Entry: `bash scripts/install.sh --platform codex`; Codex auto-reads AGENTS.md
- Happy path: Install → AGENTS.md updated → `.codex/agents/*.toml` populated → next session recognizes Writ
- Moment of truth: `/implement-story` runs end-to-end with native subagent parallelism + sandbox enforcement
- Feedback: Same `[N/M]` step format Cursor/Claude installs use; AGENTS.md merger has dedicated summary line
- Error: User-modified Writ block preserved with overlay warning; oversize AGENTS.md surfaces config remediation

---

## For Testing Agents

**Success Criteria:**
1. Install summary shows seven agents fanned out to `.codex/agents/*.toml` with correct `sandbox_mode` per agent
2. AGENTS.md hash outside markers identical pre/post install (byte-stable)
3. Manual `/implement-story` run completes all five SDLC phases on Codex
4. `/refresh-command --check-parity` exits 0 with full agent set; warns when one is missing

**Shadow Paths to Verify:**
- **Happy path:** Fresh install on project without AGENTS.md → file created with Writ block; install on project with AGENTS.md → block appended; subsequent update → block replaced atomically
- **Nil input:** No `codex/agents/` source on installer side → warning emitted, commands/skills still install, exit nonzero
- **Empty input:** Empty AGENTS.md exists pre-install → block appended, file no longer empty
- **Upstream error:** Network/git clone failure during `bash <(curl …)` invocation → installer exits with clear error, no partial state written

**Edge Cases:**
- AGENTS.md with Writ block but `</-- writ:end -->` marker malformed → installer detects, warns, refuses to update (user fixes manually)
- User runs `--platform codex` on a project with prior `.cursor/` or `.claude/` install → both installations coexist; manifests are platform-namespaced
- `.codex/config.toml` modified by user, then `--force` install → user prompted before overwrite
- Codex CLI version with different TOML schema than spec assumes → out-of-scope; spec records May 2026 schema

**Coverage Requirements:**
- New script branches: ≥80%
- AGENTS.md merger logic: 100% (critical for byte-stability guarantee)
- Error paths: 100%

**Test Strategy:**
- Bash test fixtures for AGENTS.md merger: empty file, no-marker file, with-marker file, modified-marker file
- Manifest hash comparison test for `.codex/.writ-manifest`
- End-to-end manual smoke on a fresh sandbox project before merge
- `/refresh-command --check-parity` automated regression in `/refresh-command` tests
