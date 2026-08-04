# Story 6: /update-writ, /reinstall-writ, /uninstall-writ Codex Platform Branches

> **Status:** Code complete — PR review + command-flow evidence pending
> **Priority:** Medium
> **Dependencies:** Story 5

## User Story

**As a** Codex CLI user inside a `codex` session
**I want to** run `/update-writ`, `/reinstall-writ`, or `/uninstall-writ` and have the command recognize my Codex installation, use the correct paths, and surface platform-specific guidance (e.g., "restart Codex to load AGENTS.md changes")
**So that** the in-session lifecycle UX matches what Cursor and Claude Code users get without me dropping to a shell to invoke the install/update/uninstall scripts directly

## Acceptance Criteria

**AC-1: All three lifecycle commands detect `.codex/.writ-manifest` and operate on Codex paths**

- **Given** a project with `.codex/.writ-manifest` present (and no `.cursor/.writ-manifest` or `.claude/.writ-manifest`)
- **When** the user invokes `/update-writ`, `/reinstall-writ`, or `/uninstall-writ`
- **Then** the command's platform-detection step recognizes `codex` as the active platform; subsequent steps use the Codex paths from Stories 4–5 (`.codex/agents/*.toml`, `.codex/config.toml`, AGENTS.md Writ block, `.agents/skills/`); and the underlying script invocation passes `--platform codex` (where applicable) to `update.sh` / `install.sh` / `uninstall.sh`

**AC-2: Codex-specific post-action guidance is surfaced in command output**

- **Given** a user has just completed `/update-writ` or `/reinstall-writ` on a Codex installation
- **When** the command renders its summary
- **Then** the summary includes an explicit "Restart your Codex session to load AGENTS.md changes" line (because Codex reads AGENTS.md at session start, not on every prompt); and `/uninstall-writ` on a Codex installation includes a pre-confirmation warning that AGENTS.md will be modified (Writ block removed) and that `.codex/config.toml` removal will be prompted separately per Story 5's deferred decision; cursor and claude paths render their existing summaries unchanged

**AC-3: Daily update check protocol works unchanged on Codex**

- **Given** the daily-update-awareness cache at `.writ/state/writ-update-check.json` from `.writ/specs/2026-04-28-daily-writ-update-check`
- **When** session startup runs the update awareness check on a Codex installation
- **Then** the cache file location, schema (`last_checked_date`, `status`, `installed_version`, `latest_seen_version`, `source`, `checked_by`), and notification copy ("Writ update available. Run `/update-writ` when you are ready.") are byte-identical to what Cursor and Claude Code emit; no Codex-specific cache fork; the `/update-writ` command path is the same recommendation regardless of platform

**AC-4: Cursor and Claude Code branches are byte-stable**

- **Given** the three command files prior to Story 6's edits
- **When** the diff is computed against the post-Story-6 versions
- **Then** all changes are additive — new Codex branches in platform-detection tables, new Codex platform path rows, new Codex-specific guidance subsections — and the existing Cursor and Claude code paths and prose are unmodified except where a shared table/list grows by one row to include Codex; a reviewer can confirm no Cursor/Claude semantics change by reading only the diff

**AC-5: Cross-command consistency for Codex-specific notes**

- **Given** the same Codex-specific concerns apply to multiple commands (session restart for AGENTS.md, AGENTS.md ownership, `.codex/config.toml` install-once semantics)
- **When** any Codex-specific note appears in more than one command file
- **Then** the wording is consistent (same phrasing, same rationale, same link target — `adapters/codex.md`); a future maintainer reading two commands side-by-side sees identical language for identical behavior, not two paraphrases

## Implementation Tasks

- [x] **6.1** Document the platform-detection extension pattern. In each of the three command files, the platform-paths table currently has rows for `cursor` and `claude`; add a `codex` row with platform dir `.codex`, manifest `.codex/.writ-manifest`, agents src `codex/agents` (TOML, not Markdown), extra files `AGENTS.md` Writ block + `.codex/config.toml`. Confirm the manifest-detection bash snippet adds a `cat .codex/.writ-manifest 2>/dev/null` line in each command's Step 1.
- [x] **6.2** Update `commands/update-writ.md`: extend platform-detection (Step 1), add Codex row to the platform-paths table (Step 1), reference TOML agent overlay in three-way scan prose (Step 3) where it currently says ".md file in upstream `commands/` and the platform's agents source directory" so it acknowledges Codex's TOML format, and add a Codex-specific summary footer (Step 9) recommending session restart for AGENTS.md changes; preserve Cursor/Claude prose verbatim.
- [x] **6.3** Update `commands/reinstall-writ.md`: extend platform-detection (Step 1), add Codex platform option to the no-manifest `AskQuestion` selection, add Codex row to the platform-paths references in Step 3 (file removal list — call out AGENTS.md Writ block removal and `.codex/config.toml` prompt deferred to `uninstall.sh`), add Codex callout in Step 6 summary (session restart + AGENTS.md/config.toml notes), and add Codex `bash` example to the recovery-instructions block in the error-handling section.
- [x] **6.4** Update `commands/uninstall-writ.md`: extend platform-detection (Step 1) including the multi-platform `AskQuestion` to add a `codex` option and a "all three" option (or rename "both" to "all" with explanatory text), add Codex platform-specific files row in Step 3 (AGENTS.md Writ block via `uninstall.sh --platform codex`, `.codex/config.toml` removal prompt per Story 5's decision, `.codex/agents/*.toml`, `.codex/.writ-manifest`), add Codex pre-confirmation warning in Step 2 explaining AGENTS.md modification and config.toml prompt, and add Codex `bash` reinstall example in Step 5 summary.
- [x] **6.5** Verify daily update check protocol works on Codex without changes. Manually inspect `.writ/state/writ-update-check.json` cache contract in `.cursor/rules/writ.mdc` and confirm no platform-specific fields exist; confirm the three command files don't write to the cache file (the awareness check lives in system instructions, not in `/update-writ` body); add a one-line note in `commands/update-writ.md` Step 0 (or a top-of-file callout) reaffirming that the daily cache protocol is platform-agnostic.
- [x] **6.6** Cross-reference command bodies for consistency. Search the three updated command files for Codex-specific prose (session restart, AGENTS.md block, `.codex/config.toml`) and ensure identical wording for identical concepts; link each Codex-specific note to `adapters/codex.md` with a relative path that resolves from the installed location (e.g., `../../adapters/codex.md` if the command lives at `.codex/commands/update-writ.md`).
- [ ] **6.7** Verify all five acceptance criteria. Diff the three command files against the pre-Story-6 versions and confirm only additive Codex-branch changes; manually walk through a Codex `/update-writ` and `/uninstall-writ` flow on a sandbox project (post-Story-5 install) and confirm guidance text appears as drafted; mark story Complete. **Current evidence:** command docs updated, lints clean, Codex-specific prose searched for consistency; live Codex command-flow walkthrough remains for PR/manual smoke.

## Notes

**This story is mostly Markdown editing — the heavy lifting happened in Stories 4–5.** The install/update/uninstall scripts now know how to handle `--platform codex`; Story 6 just teaches the three lifecycle commands to detect Codex installations and route to the right script invocation with the right summary copy. If a reviewer feels themselves wanting to add real logic to a command file, they should stop and ask whether that logic belongs in a script instead.

**AGENTS.md changes don't take effect mid-session.** Codex reads AGENTS.md at session start, not on every prompt. After `/update-writ` modifies the Writ block (or `/reinstall-writ` rewrites it), the user's current `codex` session still sees the old block. The summary footer must say so explicitly — "Restart your Codex session to load AGENTS.md changes" — otherwise users will be confused why a fresh `/create-spec` from the same session still references the old command set.

**`.codex/config.toml` uninstall prompt is Story 5's decision, not this story's.** Story 5 (per the technical spec's Open Implementation Questions #3) decides whether `uninstall.sh --platform codex` removes `.codex/config.toml` silently or prompts. Story 6 honors whatever Story 5 chose by accurately describing that behavior in `commands/uninstall-writ.md`'s pre-confirmation prompt — but Story 6 doesn't get to overrule the decision. If Story 5 lands with a `[user choice]` placeholder, Story 6 fills it in here.

**Multi-platform installations are now genuinely possible.** With three platforms supported, a user could in principle have `.cursor/`, `.claude/`, AND `.codex/` installed in the same project. The `/uninstall-writ` Step 1 multi-platform `AskQuestion` needs to handle three-way selection (cursor/claude/codex/all). The "both" option label from the current command file needs renaming to "all" — flag this in the diff to avoid confusing reviewers who expect "both" to be unchanged.

**Daily-update-check inheritance.** The `.cursor/rules/writ.mdc` Startup Update Awareness section already documents the cache protocol as platform-agnostic; Story 6 doesn't need to change that, just confirm it works on Codex (which it should — the cache file path `.writ/state/writ-update-check.json` lives in the project's Writ workspace, not a platform directory). One sanity check is enough; no test fixture required.

**Expected size.** ~30–50 lines of additive prose per command file (3 platform-row additions, 1–2 Codex-specific subsections, summary-footer extensions). Total Story 6 diff target: ≤200 added lines, near-zero removed lines except the `both` → `all` rename in `uninstall-writ.md`.

## Definition of Done

- [x] Tasks 6.1–6.6 completed
- [ ] Task 6.7 PR/manual command-flow evidence completed
- [ ] All acceptance criteria fully evidenced at PR review time
- [ ] Cursor and Claude command branches byte-stable (verified by diff against pre-Story-6 versions)
- [x] Codex-specific guidance accurate against Stories 4–5 actual script behavior
- [x] Cross-command consistency check passes (identical wording for identical concepts)
- [x] Each Codex-specific note links to `adapters/codex.md`
- [ ] Code reviewed

## Context for Agents

After reading `spec.md` and `sub-specs/technical-spec.md`, the following spec elements apply specifically to this story:

- **Error map rows:** None new. Story 6 inherits the error surfaces from Stories 4–5 (the scripts the commands wrap); Story 6 just makes sure the command-level summaries describe those errors accurately when surfaced via the `/update-writ`, `/reinstall-writ`, `/uninstall-writ` paths. The command-level `Network failure (clone fails)`, `No manifest found`, `Linked installation`, and `No git repo` rows already in the command files apply unchanged on Codex.
- **Shadow paths:** `Update` (Codex happy path: `Writ block updated` summary plus session-restart footer) and `Uninstall` (Codex happy path: `Writ removed; AGENTS.md preserved` or `AGENTS.md deleted (empty after removal)`). The `Install on existing AGENTS.md` shadow path applies to `/reinstall-writ` (it triggers an install after removal).
- **Business rules:** "AGENTS.md ownership" (Writ owns content between markers; uninstall removes block + markers; surrounding content untouched) governs the `/uninstall-writ` warning copy. "`.codex/config.toml` is install-once" governs `/reinstall-writ` (does not overwrite on re-install) and `/uninstall-writ` (prompted removal per Story 5). "Inheritance from skills-foundation/daily-update-check specs" — both prior specs' invariants (manifest schema, overlay logic, daily cache schema) apply unchanged on Codex; this story confirms inheritance, doesn't restate it.
- **Experience:**
  - **Entry points** — lifecycle command invocation from inside an active `codex` session (the user has the chat open and types `/update-writ`).
  - **Feedback model** — post-action summaries with Codex-specific notes (session-restart reminder, AGENTS.md/config.toml callouts, `adapters/codex.md` link), keeping the existing per-file overlay symbols (`✨ / 🔄 / ⚡ / ✓`) and `[N/M]` step format.
- **Files in scope:** `commands/update-writ.md`, `commands/reinstall-writ.md`, `commands/uninstall-writ.md`.
- **Files explicitly out of scope:** `scripts/update.sh`, `scripts/install.sh`, `scripts/uninstall.sh` (all touched in Stories 4–5); `.cursor/rules/writ.mdc` Startup Update Awareness section (platform-agnostic, no edit needed); `adapters/codex.md` (Story 3 — only linked, not edited here); the daily-update-check cache schema or implementation.
