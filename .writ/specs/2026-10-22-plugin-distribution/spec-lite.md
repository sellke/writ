# Plugin Distribution (Lite)

> Source: .writ/specs/2026-10-22-plugin-distribution/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Writ installs as a plugin in Claude Code and Cursor from this repository, built from the generated trees; scripts run from the plugin root; `/initialize` scaffolds `.writ/` via a shipped `scaffold-writ.py`; one smoke test covers both plugins and the three `install.sh` installs; `install.sh` stays; ADR-031 records the script-location decision.

**Implementation Approach:**
- Story 1 verifies before any code: first-party docs plus one live install per platform, recorded in technical-spec.md § Verification Record (status grammar as the rendering-rows spec); picks layout B (`plugins/writ/` generated subdir, the default) or A (repo root is the plugin, `source: "."`, only if validate, a local-path live install, and the root `skills/` scan all behave); picks the Prime Directive carrier (`settings.json` main-thread agent, or forced output style) by probe; fills the relative-path inventory and the token classes (`agent-path`, `skill-path`, `preamble-path`, `instructions-path`). Outcome 2026-10-23: layout B; carrier `plugins/writ/output-styles/writ.md` with `force-for-plugin: true` and `keep-coding-instructions: true` (the P2 quote and P3 persona probes discriminated, P1 did not); token classes add `script-path` (bare `scripts/<name>`) and `command-ref` (`/<cmd>` to `/writ:<cmd>`), body only; `instructions-path` rewrites the Markdown link form only and whole-line HTML comments are never rewritten (DEV-002, DEV-003, DEV-007).
- Claude Code: `.claude-plugin/plugin.json` + `marketplace.json`; a `claude-code-plugin` target in `gen-platform-trees.py` with `script_root: ${CLAUDE_PLUGIN_ROOT}/scripts` and the new tokens; namespaced names (`/writ:<cmd>`, `writ:<agent>`) spelled in generated text; ignored agent frontmatter keys documented.
- Cursor: `.cursor-plugin/plugin.json` (`name`, `description`, `version` from `VERSION`), `rules/writ.mdc`, skills, commands, agents (`commands/` and `agents/` are docs-verified discovery dirs as of 2026-10-23, live load pending UAT, DEV-004; commands keep `python3 scripts/<name>.py`, no plugin-root script form is verified; layout `cursor/plugin/` also ships `system-instructions.md` at its root (DEV-020); agent docs lack the frontmatter Cursor requires (V80, DEV-017, flagged); Story 2's VERSION and full-write test expectations extend in place for the Cursor layout (DEV-019)); local-install protocol; live check is UAT; Story 3 runs after Story 2 (shared `TARGETS` and test file).
- `scripts/scaffold-writ.py scaffold [--project] [--check]`: idempotent eleven-path `.writ/` tree (adds `knowledge/` and `issues/{bugs,features,improvements,goals}`, drops `explanations/`) + `.gitignore` entries, creating the file when absent; `install.sh` and `update.sh` keep a byte-identical bash `init_writ_workspace` with the same list (no Python in the installers) and a test asserts the two lists match; `/initialize` Step 0 runs the script (its tree counts as boilerplate for greenfield detection). Output adds `added .gitignore entry <entry>` detail lines; the `--check` count covers paths and entries; entries append at end of file under the existing comment block; `update.sh` repairs on every non-dry run and leaves the `.gitignore` change for the user to commit (DEV-011 to DEV-016).
- Smoke test `scripts/tests/test_plugin_smoke.sh`, five targets: commands present, `spec-status.py --help` from the resolved root, instructions reachable, scaffold check; `claude plugin validate` when the CLI exists else `unverifiable`.
- README lists a plugin path first only where the smoke test passes.

**Files in Scope:**
- technical-spec.md § Verification Record, § Relative Path Inventory, § Candidate Layouts decision (S1)
- `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `scripts/gen-platform-trees.py` (target + tokens), generated plugin tree, carrier file(s), `adapters/claude-code.md` § Installation; Story 1 record tests and optional manifest fields `repository`, `license`, marketplace `description` (S2, DEV-010)
- `.cursor-plugin/plugin.json`, Cursor layout, `adapters/cursor.md` § Plugin (S3)
- `scripts/scaffold-writ.py`, `scripts/install.sh`, `scripts/update.sh`, `commands/initialize.md`, `.writ/decision-records/adr-031-script-location.md`, script-install-location issue (S4)
- `scripts/tests/test_plugin_smoke.sh`, `README.md`, `adapters/codex.md` one-line note (S5)

**Error Handling:**
- Undocumented behavior → `unverified` row; never a layout decision.
- No `claude` CLI → that check `unverifiable`; other checks run.
- Project without `.writ/` → `/initialize` scaffolds; other commands point at it.
- scaffold-writ.py: a permission error reads `not a directory`, and a `.gitignore` that is a directory crashes; both are known follow-ups (DEV-013).

**Integration Points:**
- Needs `2026-10-22-generated-platform-trees` (TARGETS, token pattern, `--check`).
- Front door under the plugin reads `/writ:writ`; the README example says so.
- ADR-029's script-location consequence is superseded by ADR-031.
- Story 5's live run confirms the prompt-template docs in `plugins/writ/agents/` do not load as agents (DEV-009).

---

## For Review Agents

**Acceptance Criteria:**
1. Verification Record has a dated, sourced, status-marked row per claim; layout, carrier, and tokens are decided from `verified` rows only `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`
2. Claude Code plugin validates, installs from the marketplace file, and a generated command resolves `${CLAUDE_PLUGIN_ROOT}/scripts/…`; namespaced agent spawn recorded `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
3. Cursor layout exists with the documented components and a local-install protocol; live check is a UAT scenario `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`
4. `scaffold-writ.py` is idempotent, mirrored by a bash `init_writ_workspace` in `install.sh` and `update.sh` (drift-tested), and run by `/initialize` Step 0; ADR-031 written; issue resolved `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`
5. Smoke test green on `cursor`, `claude`, `codex`, `claude-plugin`; `cursor-plugin` green or `unverifiable`; README order follows the results `[AC-5.1, AC-5.2, AC-5.3, AC-5.4]`
6. Live Claude Code run recorded: `/writ:initialize` scaffolds, `/writ:writ` routes `[AC-5.5]`

**Business Rules:**
- Every platform claim carries a date and a URL; the README cites only the smoke test.
- The plugin tree is a generator target, never a second generation path.
- Dev-only scripts never enter a plugin (their names may stay in prose that addresses the Writ source repository, DEV-008).

**Experience Design:**
- Entry: two `claude plugin` commands, then `/writ:initialize`.
- Happy path: scaffold, route, script runs from the plugin root.
- Moment of truth: the session carries the Prime Directive without a `scripts/` folder in the project.
- Feedback: smoke test output; README order.
- Error: a missing CLI or docs change is reported as unverifiable, never guessed.

---

## For Testing Agents

**Success Criteria:**
1. `uv run --python 3.9 pytest` passes (scaffold and generator-target tests).
2. Bash loop passes, including `test_plugin_smoke.sh` (temp dirs only).
3. `bash scripts/eval.sh` (outside the sandbox): 0 findings.

**Shadow Paths to Verify:**
- **Happy path:** all five smoke targets pass on a machine with the `claude` CLI.
- **Nil input:** no `claude` CLI → `unverifiable` for that check only.
- **Empty input:** empty temp project → scaffold creates the tree; second run creates nothing.
- **Upstream error:** docs changed → record row updated; decision re-taken.

**Edge Cases:**
- Plugin and `install.sh` install in one project → both command sets exist; documented.
- `.gitignore` already has `.writ/state/` → scaffold adds nothing.

**Test Strategy:**
- pytest for `scaffold-writ.py` and the generator target; bash smoke test from a committed source copy; manual UAT protocols for live sessions.
