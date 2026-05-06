# Technical Specification — Codex CLI Adapter

> Parent: `.writ/specs/2026-05-06-codex-cli-adapter/spec.md`

## Architecture Overview

This spec adds Codex CLI as a third install platform peer to Cursor and Claude Code. The integration is layered:

```
Source code (one repo, three platform variants)
├── agents/*.md                  ← Cursor-native, read directly
├── claude-code/agents/*.md      ← Claude-native, YAML frontmatter
└── codex/agents/*.toml          ← Codex-native, TOML
                                  ↓
Install scripts fan out to platform-native locations
                                  ↓
Active installations (per-project)
├── .cursor/agents/*.md
├── .claude/agents/*.md
└── .codex/agents/*.toml
                                  ↓
Skills install to AgentSkills standard path on Codex
└── .agents/skills/<name>/SKILL.md
                                  ↓
AGENTS.md (Codex's project instructions file) gets a Writ-managed block
└── <!-- writ:start --> ... <!-- writ:end -->
```

**Source-of-truth principle:** Each platform agent file is independently authored from the same role concept. The `--check-parity` lint catches drift; identical content is not enforced (some platforms may have legitimately different optimal phrasings).

**Manifest principle:** Each platform installation owns a manifest (`.codex/.writ-manifest`) tracking the upstream baseline hash for every installed file plus the AGENTS.md Writ block. Three-way overlay (upstream / local / baseline) preserves user modifications.

## TOML Translation Schema

### Field mapping (Markdown agent → TOML)

| Markdown agent | Required TOML field | Source |
|---|---|---|
| `name:` (or filename) | `name` | Filename without `.toml`, lowercase |
| `description:` (frontmatter) | `description` | First sentence of agent file's purpose statement |
| Body content | `developer_instructions` | Multi-line TOML string (`"""..."""`) — full body of `agents/<name>.md` minus frontmatter |
| `readonly: true` | `sandbox_mode = "read-only"` | Boolean → enum |
| `model: "fast"` | `model = "<fast-tier-model-id>"` | Mapped to current Codex fast-tier (verify model IDs at implementation time against `/model` picker) |

### Sandbox mode mapping

| Agent | Cursor `readonly` | Claude `permissionMode` | Codex `sandbox_mode` |
|---|---|---|---|
| architecture-check-agent | `true` | `plan` | `read-only` |
| coding-agent | `false` | `acceptEdits` | `workspace-write` |
| review-agent | `true` | `plan` | `read-only` |
| testing-agent | `false` | `acceptEdits` | `workspace-write` |
| documentation-agent | `false` | `acceptEdits` | `workspace-write` |
| user-story-generator | `false` | `acceptEdits` | `workspace-write` |
| visual-qa-agent | `true` | `plan` | `read-only` |

### TOML file template

```toml
name = "<agent-name>"
description = "<one-sentence purpose, lifted from manifest.yaml>"
sandbox_mode = "<read-only|workspace-write>"
model = "<optional model override>"

developer_instructions = """
<full body of agents/<name>.md, minus frontmatter>
"""

# Optional — for parallel run UI distinction:
# nickname_candidates = ["Atlas", "Delta", "Echo"]
```

## AGENTS.md Merge Algorithm

### Marker convention

```markdown
<!-- writ:start -->
[Writ-owned content here]
<!-- writ:end -->
```

Markers are HTML comments (invisible in rendered Markdown, stable across editors, parseable in shell scripts).

### Merge cases

| Case | Pre-state | Action | Post-state |
|---|---|---|---|
| File absent | No `AGENTS.md` | Create file with `[Writ block]` only | `AGENTS.md` exists with markers + Writ content |
| File present, no markers | User content, no `<!-- writ:start -->` | Append `\n[Writ block]\n` to end | User content preserved verbatim, Writ block appended |
| File present, markers found | Has `<!-- writ:start -->` ... `<!-- writ:end -->` | Replace marker-bounded region atomically | Surrounding user content byte-stable, Writ block updated |
| File present, malformed markers | `<!-- writ:start -->` without matching end (or vice versa) | Halt with error; require manual fix | No changes |
| File present, modified Writ block | Markers present, but Writ block hash ≠ manifest baseline | Preserve with `⚡` warning (overlay rule); `--force` overwrites | Writ block preserved or overwritten per flag |

### Block update detection

The manifest tracks the SHA-256 of the Writ block content (between markers, exclusive). On update:

1. Read current AGENTS.md
2. Extract marker-bounded region
3. Compute SHA-256 of extracted content
4. Compare against `manifest_hash_for("AGENTS.md.writ-block")`
5. If equal → safe to overwrite (no local modifications)
6. If different and `--force` → overwrite with warning
7. If different and not `--force` → preserve with warning

### Uninstall

Remove marker-bounded region plus the markers themselves. If the file becomes empty (no non-whitespace content remains), delete the file. Otherwise leave user content intact.

## Install Script Extension Points

### `install.sh` `--platform codex` branch

Required additions:
- Variable block: `PLATFORM_DIR=".codex"`, `MANIFEST_FILE=".codex/.writ-manifest"`, `AGENTS_SRC="codex/agents"`, `PLATFORM_LABEL="Codex CLI"`, `SKILLS_DIR=".agents/skills"` (note: NOT `${PLATFORM_DIR}/skills`)
- Skills path resolution: introduce a `SKILLS_DIR` variable that platforms set independently — `.cursor/skills` for cursor, `.claude/skills` for claude, `.agents/skills` for codex
- `init_writ_workspace()` unchanged; AGENTS.md handling is separate
- New function: `merge_agents_md()` implementing the algorithm above; called in the same Step where Cursor copies `writ.mdc` and Claude copies `CLAUDE.md`
- New function: `seed_codex_config()` — copies `codex/config.toml.template` to `.codex/config.toml` only if absent
- Manifest writer extended to record AGENTS.md Writ block hash and `.codex/config.toml` baseline hash

### `update.sh`, `unlink.sh`, `uninstall.sh` parity

Each follows the same `--platform codex` pattern. Special handling:
- `unlink.sh --platform codex` removes `.codex/agents/` symlinks but leaves `.codex/config.toml` intact (it's install-once, not symlinked)
- `uninstall.sh --platform codex` removes `.codex/`, `.agents/skills/`, manifest, and the AGENTS.md Writ block (preserving surrounding content)

## Error & Rescue Map

This spec touches file operations (install scripts, AGENTS.md mutation) and external integration (Codex CLI surface). Error mapping is required.

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| `install.sh --platform codex` initial run | Git clone fails (network) | Exit nonzero with clear error message; no partial state | Network-disabled smoke test |
| Install AGENTS.md merge (file absent) | Disk full, permission denied | Catch, surface error, leave no partial file | Read-only directory fixture |
| Install AGENTS.md merge (markers malformed) | Mismatched start/end markers in user file | Halt with error message pointing to fix; do not modify | Fixture: AGENTS.md with `<!-- writ:start -->` only |
| Install AGENTS.md merge (combined size > 32 KiB) | Codex's default cap exceeded | Warning surfaced; user steered to `project_doc_max_bytes` config or `AGENTS.override.md` split | Fixture: pre-existing 30 KiB AGENTS.md |
| Install `.codex/config.toml` seeding | File already exists | Skip silently (install-once semantics) | Pre-existing `.codex/config.toml` in test project |
| Install agent TOMLs (`codex/agents/` empty) | Source folder missing or empty | Warning emitted; commands and skills still install; exit nonzero | Removed `codex/agents/` from installer source |
| Install skills to `.agents/skills/` | Existing user-authored skills in `.agents/skills/` | Three-way overlay applies same as commands/agents — user-modified `SKILL.md` files preserved | Modify a skill before update |
| Update detects modified Writ block | User edited content between markers | Preserve with `⚡` warning unless `--force` | Edit AGENTS.md Writ block, run update |
| Uninstall AGENTS.md cleanup | File becomes empty after block removal | Delete the file | Empty AGENTS.md fixture post-removal |
| Uninstall `.codex/config.toml` | User has customized config | `uninstall.sh` removes (config is owned by Writ at install time, but user is warned) — *or* prompt before removing — decision deferred to Story 5 | Customized config fixture |
| `/refresh-command --check-parity` | Missing TOML for an `agents/*.md` agent | Warning, exit code 0 (warning, not failure) | Temporarily delete one TOML |
| End-to-end `/implement-story` on Codex | Codex sandbox refuses workspace-write for coding agent | Surface as `STATUS: BLOCKED` from coding agent; orchestrator escalates | Run with restrictive global sandbox config |
| `[UNPLANNED]` | Codex CLI updates change TOML schema mid-implementation | Treat as schema regression; spec acknowledges in Implementation Notes; defer to follow-up | Cannot pre-test |

## Shadow Paths

Each cell describes what the *user sees*, not what the script does internally.

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| Install on fresh project | "✅ Writ installed for Codex CLI" + agent count | "❌ Source missing" + retry hint | n/a (project always has cwd) | "❌ Failed to clone Writ source" + network suggestion |
| Install on existing AGENTS.md | "AGENTS.md: Writ block appended" | n/a | "AGENTS.md: file was empty, Writ block written" | "⚠️ Malformed markers" + manual fix instructions |
| Update | "Writ block updated" | "Manifest missing — re-run install" | n/a | Network failure surfaces same as install |
| Uninstall | "Writ removed; AGENTS.md preserved" or "AGENTS.md deleted (empty after removal)" | "No Writ installation detected" | n/a | n/a |
| `/implement-story` runs on Codex | All phases complete; `/agent` shows spawned subagents | "STATUS: BLOCKED" from a phase agent | n/a | Sandbox denial → BLOCKED with sandbox error |

## Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| User runs install twice in succession | Second run is a no-op (manifest matches upstream); summary shows zero changes |
| User runs `--platform codex` after `--platform cursor` install | Both installations coexist (different `PLATFORM_DIR`s, different manifests); AGENTS.md gets one Writ block; `.cursor/system-instructions.md` and `.codex/.writ-manifest` are independent |
| User has a Codex `AGENTS.override.md` in a subdir that conflicts with the Writ block | Writ does not touch `AGENTS.override.md` files; Codex's nested override mechanism takes precedence per Codex's own docs; documented in `adapters/codex.md` |
| User modifies a TOML in `.codex/agents/` | Three-way overlay preserves on update with `⚡` warning |
| User adds their own TOML in `.codex/agents/` | Untouched by overlay (no upstream baseline); persists across updates |
| User runs `unlink.sh --platform codex` on a copy-mode install (not symlinked) | No-op for files that aren't symlinks; clear messaging |
| Codex's max_threads cap reached during `/implement-story --all` | Codex queues additional subagents; orchestrator waits; documented as expected behavior in adapter |

## Test Plan

### Bash unit tests (new — first time bash-level testing in this repo)

A lightweight bash test harness in `scripts/tests/` covering:
- `merge_agents_md()` with all five fixtures (file absent / no markers / markers found / malformed / modified block)
- `seed_codex_config()` install-once semantics
- Skills path resolution per platform

The harness can be a single shell script with assertions; doesn't require external test framework. Optional but recommended for AGENTS.md merger correctness (the byte-stability guarantee is too important to verify only manually).

### Manual smoke verification (Story 7)

1. Create sandbox directory: `mkdir /tmp/codex-writ-smoke && cd /tmp/codex-writ-smoke && git init`
2. Run `bash <writ>/scripts/install.sh --platform codex --no-commit`
3. Verify file tree: `.codex/agents/*.toml`, `.codex/config.toml`, `.codex/.writ-manifest`, `AGENTS.md`, `.agents/skills/` (empty if no skills shipped)
4. Open `codex` in sandbox; verify `/agent` lists Writ agents
5. Run `/create-spec "test feature"` workflow end-to-end
6. Verify `/implement-story` runs with sandbox enforcement on review phase
7. Run `bash <writ>/scripts/uninstall.sh --platform codex`; verify clean removal
8. Re-run install; verify `--force` reinstall flow
9. Pre-create `AGENTS.md` with custom content; install; verify byte-stability outside Writ block

### Regression coverage

- Existing Cursor and Claude installs untouched (manual smoke on a non-Codex project)
- `/refresh-command --check-parity` with full agent set: exits 0
- `/refresh-command --check-parity` with one TOML deleted: warns, exits 0
- ADR-009 amendment renders correctly (Markdown formatting)

## Open Implementation Questions

These are deferred to story-level decisions, recorded for traceability:

1. **Model ID mapping for `model: fast` agents.** Cursor's `model: "fast"` is a tier; Codex requires concrete model IDs. Story 2 should resolve via `codex --help` or live `/model` picker introspection at the time of authoring, document the chosen IDs, and add a note to `adapters/codex.md` recommending users override based on their plan.

2. **Whether `/refresh-command --check-parity` should be opt-in or run by default.** Spec says opt-in initially. Reassess after first month of real-world drift signal.

3. **Whether `.codex/config.toml` uninstall should prompt or remove silently.** Spec defers this to Story 5; recommendation is to prompt once with a clear "this is your config, are you sure?" gate.

4. **AgentSkills standard amendment timing.** Whether ADR-009's amendment should be a separate PR before this spec's stories or part of Story 1. Recommendation: part of Story 1 (the spec is the rationale for the amendment).
