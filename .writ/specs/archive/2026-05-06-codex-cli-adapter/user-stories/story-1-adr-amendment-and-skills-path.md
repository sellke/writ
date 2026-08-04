# Story 1: ADR-009 Amendment & Skills Path Correction

> **Status:** Complete ✅
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ contributor implementing the Codex platform support
**I want to** lock the correct skills install path (`.agents/skills/`) and the install-script variable indirection that supports it
**So that** downstream stories can wire `--platform codex` against a correct, documented foundation rather than discovering the path mismatch mid-implementation

## Acceptance Criteria

**AC-1: ADR-009 amendment exists with corrected path and rationale**

- **Given** ADR-009 currently states `.codex/skills/` as the planned Codex skills install path
- **When** Story 1 ships
- **Then** ADR-009 has a new `## Amendments` section dated 2026-05-06 that records the corrected path (`.agents/skills/`), explains the rationale (alignment with the AgentSkills cross-platform standard), explicitly notes that Cursor and Claude keep their platform-namespaced paths (no migration), and links to both the AgentSkills standard and `.writ/specs/2026-05-06-codex-cli-adapter/spec.md` as the originating spec

**AC-2: `install.sh` introduces `SKILLS_DIR` variable with no behavior change for cursor/claude**

- **Given** `scripts/install.sh` currently hardcodes `$PLATFORM_DIR/skills` in `overlay_scan_skills()` and other skills-related code paths
- **When** the refactor lands
- **Then** every skills path reference reads from a single `SKILLS_DIR` variable set in the per-platform variable block (alongside `PLATFORM_DIR`, `MANIFEST_FILE`, `AGENTS_SRC`, `PLATFORM_LABEL`); for cursor `SKILLS_DIR=".cursor/skills"` and for claude `SKILLS_DIR=".claude/skills"`; `overlay_scan_skills()` and all related code paths consume `$SKILLS_DIR` exclusively (no remaining `$PLATFORM_DIR/skills` literals)

**AC-3: Cursor and Claude install regression unaffected**

- **Given** a project with no prior Writ install
- **When** `bash scripts/install.sh --platform cursor --dry-run` and `bash scripts/install.sh --platform claude --dry-run` run pre-refactor and post-refactor
- **Then** the post-refactor outputs are byte-identical to pre-refactor for both platforms (or any difference is purely cosmetic, e.g. variable expansion order in echo lines, and is documented in the PR description)

**AC-4: AgentSkills standard cited in the amendment**

- **Given** the ADR amendment
- **When** a fresh reader opens ADR-009
- **Then** the amendment cites the AgentSkills cross-platform standard by name with a working URL or reference, and the rationale clearly states *why* Codex uses `.agents/skills/` (cross-platform readability) while Cursor and Claude keep platform-namespaced paths (no in-flight ecosystem to disrupt)

**AC-5: `update.sh`, `unlink.sh`, `uninstall.sh` mirrored where they reference skills**

- **Given** the sibling lifecycle scripts may also reference skills paths
- **When** Story 1 ships
- **Then** any skills path references in `update.sh`, `unlink.sh`, and `uninstall.sh` are likewise parameterized via `SKILLS_DIR` (or an audit confirms they don't currently reference skills paths and a one-line note is added to the PR description); cursor and claude lifecycle dry-runs remain regression-clean

## Implementation Tasks

- [x] **1.1** Capture pre-refactor baseline: run `bash scripts/install.sh --platform cursor --dry-run` and `bash scripts/install.sh --platform claude --dry-run` from a clean throwaway dir, save outputs to `/tmp/writ-skills-refactor-baseline-{cursor,claude}.txt` for diff comparison in Task 1.5
- [x] **1.2** Amend `.writ/decision-records/adr-009-command-agent-skill-boundary.md` with a new `## Amendments` section dated 2026-05-06: corrected Codex skills path (`.agents/skills/`), AgentSkills standard rationale, explicit no-migration note for Cursor/Claude, and a link back to this spec
- [x] **1.3** Refactor `scripts/install.sh`: introduce `SKILLS_DIR` in the per-platform variable block (lines ~66–76), replace all `$PLATFORM_DIR/skills` literals with `$SKILLS_DIR` in `overlay_scan_skills()` (line ~323) and the four other call sites Grep'd at lines ~150, ~336, ~400, ~430, ~470, ~524
- [x] **1.4** Audit `scripts/update.sh`, `scripts/unlink.sh`, `scripts/uninstall.sh` for skills path references; mirror the `SKILLS_DIR` indirection wherever found (or document in the PR that none exist)
- [x] **1.5** Run post-refactor `--dry-run` for cursor and claude, diff against the Task 1.1 baselines, confirm semantic equivalence (or zero diff); attach the diff to the PR description
- [x] **1.6** Add a one-line note to `adapters/cursor.md` and `adapters/claude-code.md` Skills sections acknowledging that the install path is platform-namespaced (`.cursor/skills/` / `.claude/skills/`) and that Codex uses the AgentSkills standard `.agents/skills/` path — link to the ADR-009 Amendments section
- [x] **1.7** Verify all five acceptance criteria; mark story Complete

## Notes

**Why this story is sequenced first.** Stories 2–7 all assume the corrected skills path is locked in code and in the ADR. If we wait, the path correction would land partway through the install-script work in Story 4 and force re-touching files multiple times. The amendment is small (a few paragraphs) and the install.sh refactor is small (variable introduction + ~6 substitutions); together this is the smallest possible foundation story that unblocks the rest.

**Risk: refactoring `install.sh` breaks cursor/claude flows.** Mitigated by the Task 1.1 / Task 1.5 baseline-and-diff regression check. The change is purely indirection — the *values* `SKILLS_DIR` resolves to for cursor and claude are identical to the current hardcoded `$PLATFORM_DIR/skills` expansions. If the diff is non-empty for reasons other than cosmetic ordering, halt and investigate before proceeding.

**No `--platform codex` wiring in this story.** The codex branch in the variable block (and the `SKILLS_DIR=".agents/skills"` line for it) lands in Story 4. Story 1 only prepares the variable indirection so Story 4's diff stays small and reviewable.

**Amendment style.** ADR-009 currently has no `## Amendments` section. This is the first amendment to it. Use a level-2 heading at the bottom of the file. Future amendments append under the same section as new dated entries.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Cursor and Claude install regression unaffected (diff evidence in PR)
- [x] ADR-009 amendment reads cleanly to a fresh reader (no insider context required)
- [x] Code reviewed
- [x] Documentation updated (`adapters/cursor.md`, `adapters/claude-code.md` Skills section notes)

## Context for Agents

After reading `spec.md` and `sub-specs/technical-spec.md`, the following spec elements apply specifically to this story:

- **Error map rows:** None directly — this story is preparatory and doesn't introduce new error surfaces. Existing skills overlay error handling is preserved unchanged.
- **Shadow paths:** `Update` (skills overlay path resolution must continue to work for cursor/claude) and `Install on fresh project` (cursor/claude regression check via `--dry-run`).
- **Business rules:** "Skills install path is platform-divergent" from `spec.md` — this story is the codification of that rule in both ADR-009 and the install script.
- **Experience:** Feedback model — install summary format is unchanged (per-file overlay symbols `✨ / 🔄 / ⚡ / ✓` and `[N/M]` step format remain identical for cursor/claude).
- **Files in scope:** `.writ/decision-records/adr-009-command-agent-skill-boundary.md`, `scripts/install.sh`, `scripts/update.sh`, `scripts/unlink.sh`, `scripts/uninstall.sh`, `adapters/cursor.md`, `adapters/claude-code.md`.
- **Files explicitly out of scope:** `adapters/codex.md` (Story 3), `codex/agents/*.toml` (Story 2), any `--platform codex` branch wiring (Story 4).
