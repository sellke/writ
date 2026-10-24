# Drift Log

> Spec: .writ/specs/2026-10-22-plugin-distribution/
> Created: 2026-10-23
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: Verify Both Plugin Formats and Decide the Layout — Drift Report

> Run: 2026-10-23
> Overall Drift: Small

### Deviations

#### [DEV-001] Layout B built and installed although layout A passed validate and install
- **Severity:** Small
- **Spec said:** Task 1.3: "Build layout B (`plugins/writ/`) only if A fails validate or install."
- **Implementation did:** Built a layout B scratch plugin as well, validated it, installed it from a local path, and ran `/writ:stub`, `/writ:scratch-skill`, `/writ:root-skill`, and the `writ:writ-coder` spawn under it, then undid the install (V55, V61 in § Verification Record).
- **Reason:** The decision rule's third condition (the root `skills/` scan) needs a B observation to show that a `skills/` outside `plugins/writ/` stays unloaded; the run changed no product file and its undo is recorded.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** none needed beyond the Story 1 line in spec-lite.md (DEV-002).

#### [DEV-002] Carrier decided by the quote and persona probes, not the assertion probe
- **Severity:** Small
- **Spec said:** Story 1 Notes: ask the session to confirm an unchecked assertion; a carrier counts as observed only when its reply differs from the baseline.
- **Implementation did:** The assertion probe (P1) withheld confirmation in the baseline and under both carriers, so it did not discriminate (V70). The decision rests on P2 (quote the first Hard Constraints bullet and its heading) and P3 (name the persona), which differ from the baseline under both carriers (V67 to V69). Both carriers were observed; verified docs rows broke the tie for the forced output style.
- **Reason:** P1's reply is Claude's default behaviour with no tools, so it cannot show which instructions are present; P2 and P3 can.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → For Coding Agents, the Story 1 line now records the outcome: layout B, carrier `output-styles/writ.md` (`force-for-plugin`, `keep-coding-instructions`), decided by the P2/P3 probes.

#### [DEV-003] Two token classes added to the four the spec named
- **Severity:** Small
- **Spec said:** spec.md Technical Concerns names `agent-path`, `skill-path`, `preamble-path`, `instructions-path` beside `script-root`; Task 1.6 says "Confirm or change the four token classes from the inventory".
- **Implementation did:** The inventory adds `script-path` (73 bare `scripts/<name>` references without an interpreter, plus one `../scripts/` link) and `command-ref` (`/<command>` to `/writ:<command>`, 806 matches), and states that every class rewrites Markdown bodies only.
- **Reason:** AC-2.2 requires every command cross-reference to read `/writ:<command>` and every script call to read `${CLAUDE_PLUGIN_ROOT}/scripts/<name>`; many script calls carry no interpreter. The script-invocation count is 69, not the spec's 132 (recorded in the inventory).
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → For Coding Agents, the Story 1 line lists six token classes.

#### [DEV-004] Cursor `commands/` and `agents/` directories are now documented
- **Severity:** Small
- **Spec said:** spec.md Rule 6 and spec-lite: Cursor agents and commands directories are undocumented, so they ship at the `install.sh` shape labelled `unverified (pending UAT)`.
- **Implementation did:** https://cursor.com/docs/reference/plugins.md (read 2026-10-23) documents `rules/`, `skills/`, `agents/`, `commands/` as default discovery directories (V48). Story 1 records the docs placement as verified; the live load stays `unverified 2026-10-23 (pending UAT)` (V76, V77).
- **Reason:** Upstream docs changed since 2026-10-22 (technical-spec.md → Shadow Paths, Upstream error: record the new URL and re-take the decision).
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → For Coding Agents, the Cursor line says the directories are docs-verified and the live load is pending UAT.

---

## Story 2: Claude Code Plugin — Drift Report

> Run: 2026-10-23
> Overall Drift: Medium

### Deviations

#### [DEV-005] Self-locating Writ-source scripts resolve their root to the plugin
- **Severity:** Medium
- **Spec said:** Rule 3: the plugin root holds the shipped script set (`is_shippable_script`), and commands run scripts from the plugin root.
- **Implementation did:** Ships exactly that set. Four of those scripts locate their working root from their own path (`gen-claude-agents.py`, `gen-codex-agent-tomls.py`, `check-agent-parity.sh`, `gen-skill.sh`), so run as `${CLAUDE_PLUGIN_ROOT}/scripts/<name>` from `/writ:refresh-command` or `/writ:new-skill` they read and would write inside the plugin directory instead of the project.
- **Reason:** These are Writ-source maintenance tools that `is_shippable_script` admits today; under `install.sh` their root is the project and the effect is harmless. Reclassifying them (dev-only, or cwd-relative) changes the shipped set for every install path, which is outside this story. Recorded in ADR-031 consequences as a follow-up.
- **Resolution:** Disclosed 2026-10-24 after the acceptance audit found no user-facing warning: `adapters/claude-code.md` → Plugin and the README plugin paragraph now say the two commands write inside the plugin's folder. The scripts are unchanged; reclassifying them stays a follow-up.
- **Spec amendment:** N/A — flagged for post-implementation review

#### [DEV-006] `.writ/docs/` reference docs are absent in a plugin-only project
- **Severity:** Medium
- **Spec said:** spec.md Technical Concerns and the Relative Path Inventory: `.writ/docs/<x>` is a project path, unchanged; Story 2's user story: "I copy nothing into my project".
- **Implementation did:** Leaves the 83 references unchanged, as the inventory decides, and `adapters/claude-code.md` § Plugin says the plugin does not ship them. `install.sh` copies Writ's format docs (e.g. `acceptance-criteria-ids.md`, `spec-lifecycle.md`, `what-was-built-format.md`) into `.writ/docs/`; a plugin-only project has none, and the Story 4 scaffold creates the empty directory only.
- **Reason:** Shipping the docs would add a token class or a scaffold copy step that the contract does not name. Spec-level gap; follow-up for an amendment (candidate: scaffold-writ.py copies shipped docs from the plugin root, or a `writ-doc-path` token).
- **Resolution:** Flagged for review
- **Spec amendment:** N/A — flagged for post-implementation review

#### [DEV-007] Inventory re-take: `instructions-path` rewrites link forms only; comment lines skipped
- **Severity:** Small
- **Spec said:** Story 1 inventory: link and bare `system-instructions.md` forms resolve to `${CLAUDE_PLUGIN_ROOT}/system-instructions.md`.
- **Implementation did:** After review, rewrites only the Markdown link (`` [`system-instructions.md`](../system-instructions.md) `` text and target); bare mentions name installed files and stay. Whole-line HTML comments are not rewritten. The inventory row carries a dated note. Remaining minor prose items: `migrate.md` "Just use /writ:writ commands", `status.md` example log line, `new-command.md` template References now carry `${CLAUDE_PLUGIN_ROOT}/commands/_preamble.md`.
- **Reason:** Bare-mention rewrites changed meaning in install and meta commands (update-writ, reinstall-writ, migrate, plain-prose).
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → For Coding Agents, the Story 1 outcome line notes the link-only rule and skipped comment lines.

#### [DEV-008] Dev-only script calls stay bare in plugin bodies
- **Severity:** Small
- **Spec said:** Rule 3: "A plugin command never references a dev-only script."
- **Implementation did:** Follows the record ("dev-only names unchanged"): `bash scripts/eval.sh` (refresh-command, plain-prose), `scripts/publish-writ-runtime.sh` (release), `scripts/install.sh` / `scripts/update.sh` (update-writ, migrate) stay as written; they address the Writ source repository, not the plugin.
- **Reason:** The record outranks the literal wording for this form; the rule's intent (no dev-only script in the plugin's `scripts/`) holds and is tested.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → For Review Agents, Business Rules: the dev-only rule now says their names may stay in prose that addresses the Writ source repository.

#### [DEV-009] Prompt-template docs excluded from agent loading by the manifest only
- **Severity:** Small
- **Spec said:** Story 1 decision: `plugin.json` `agents` lists the eight generated agents so the prompt-template docs in `agents/` do not load (V03, V23).
- **Implementation did:** Sets the key. `claude plugin validate` still reads the eight prompt docs and warns "No frontmatter block found"; runtime loading is unverified (V72).
- **Reason:** Story 5's live run checks that no `writ:coding-agent`-style agent appears.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → Integration Points: Story 5's live run confirms the prompt-template docs do not load as agents.

#### [DEV-010] Story 1 record tests added; marketplace and manifest gain optional fields
- **Severity:** Small
- **Spec said:** Story 2 tests cover AC-2.x; AC-2.1 names `name`, `owner.name`, `plugins[]` for the marketplace and `name`, `description`, `author`, `version` for the manifest.
- **Implementation did:** Adds `TestStory1Record` (AC-1.2 to AC-1.4 citations that `review-override.py` requires once Story 1 reads Completed); adds a marketplace `description` and a manifest `repository` and `license` (validate 2.1.309 accepts them, `--strict` included). Owner and author name: Adam Sellke.
- **Reason:** Traceability for a completed story; the optional fields clear validate warnings.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → Files in Scope (S2) names the Story 1 record tests and the optional manifest fields.

---

## Story 4: Scaffold Script, `/initialize` Step 0, and ADR-031 — Drift Report

> Run: 2026-10-23
> Overall Drift: Small

### Deviations

#### [DEV-011] Extra `added .gitignore entry <entry>` output lines
- **Severity:** Small
- **Spec said:** AC-4.1: line 1 `pass`, one `created <path>` line per missing path, last line the summary.
- **Implementation did:** Prints one `added .gitignore entry <entry>` line per appended entry after the `created` lines and before the summary; `/initialize` Step 0 reports them.
- **Reason:** The agent CLI check shape allows detail lines; the `created` lines still follow line 1 and the summary stays last.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → scaffold line: output adds `added .gitignore entry <entry>` detail lines.

#### [DEV-012] `--check` summary counts every reason line
- **Severity:** Small
- **Spec said:** Story Notes: `<n>` and `<m>` count only the listed paths ("ten", stale: the contract has eleven).
- **Implementation did:** `scaffold-writ: fail (<m> missing)` counts missing paths plus missing `.gitignore` entries (plus blocked paths), so a fail caused only by an entry never reads `0 missing`. The pass-path summary counts the eleven paths.
- **Reason:** The summary matches the visible `reason:` lines; AC-4.3 does not define `<m>`.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → scaffold line: the `--check` count covers paths and entries.

#### [DEV-013] `not a directory` fail path; misleading reason on permission errors; `.gitignore` directory crash
- **Severity:** Small
- **Spec said:** No behaviour specified for a file in the way of a path.
- **Implementation did:** A non-directory at a listed path is `fail`, `reason: not a directory <path>`, with a `<k> not a directory` summary suffix; `--project` naming a non-directory exits 2. Review found two edge cases left as follow-ups: a permission error from `mkdir` is reported with the same `not a directory` reason, and a `.gitignore` that is a directory raises `IsADirectoryError` (exit 1, empty stdout, breaking the check-shape line-1 rule).
- **Reason:** Edge cases outside the ACs; logged for a follow-up fix rather than widening this story.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → Error Handling: scaffold-writ.py's permission-error and directory-`.gitignore` paths are known follow-ups.

#### [DEV-014] Missing entries appended at end of file when the Writ comment exists
- **Severity:** Small
- **Spec said:** Notes: append missing entries under the `# Writ ephemeral state` comment, in one write.
- **Implementation did:** When the comment exists, appends the missing entries at end of file without repeating it; otherwise appends a new comment block. The bash function and the script produce the same bytes (9 fixtures).
- **Reason:** Identical result for the block today's installer writes (it sits at end of file); keeps the bash side one `>>` write.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → scaffold line: entries append at end of file under the existing comment block.

#### [DEV-015] `update.sh` repairs before its early exits, skips on `--dry-run`, and leaves `.gitignore` uncommitted
- **Severity:** Small
- **Spec said:** Task 4.3: call the function after `WRIT_SRC` is set so an update repairs a missing tree.
- **Implementation did:** Calls it after `load_baselines`, before the "Already up to date" exits, guarded by `DRY_RUN != true`; the scoped update commit does not stage `.gitignore`, and an up-to-date run prints no repair line. ADR-031 Consequences records it.
- **Reason:** Meets the intent (verified: a real update repaired `.writ/knowledge`, `.writ/issues/goals`, and the lanes entry; dry run wrote nothing).
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → scaffold line: `update.sh` repairs on every non-dry run and leaves the `.gitignore` change for the user to commit.

#### [DEV-016] `/initialize` Greenfield wording counts the Step 0 tree as boilerplate
- **Severity:** Small
- **Spec said:** Task 4.4 names Step 0 and one replaced sentence.
- **Implementation did:** Also edits the Greenfield bullet so the `.writ/` tree Step 0 created does not tip detection toward brownfield.
- **Reason:** Without it Step 0 would change the detection result it runs before.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → scaffold line: Step 0's tree counts as boilerplate for greenfield detection.

---

## Story 3: Cursor Plugin — Drift Report

> Run: 2026-10-23
> Overall Drift: Medium

### Deviations

#### [DEV-017] Cursor `agents/` ships frontmatter-less prompt docs where Cursor requires agent frontmatter
- **Severity:** Medium
- **Spec said:** Contract item 3: "commands, agents, skills as the docs place them"; Rule 6 keeps install.sh's component set.
- **Implementation did:** Ships the 8 `agents/*.md` prompt-template docs (install.sh `AGENTS_SRC="agents"`) at the documented `agents/` directory. https://cursor.com/docs/reference/plugins.md (read 2026-10-23) says agents require YAML frontmatter (`name`, `description`) and the submission checklist requires valid frontmatter for every component (V80); none of the 8 files has it.
- **Reason:** Parity with install.sh's `.cursor/agents/`; the live load is pending UAT. Cursor may skip or list them as broken agents, and they may fail the marketplace review. Decide before the maintainer submits: generate Cursor frontmatter, move them out of a discovery directory, or let the UAT outcome decide.
- **Resolution:** Fixed 2026-10-24 after UAT: `render_cursor_plugin` adds `name` and `description` frontmatter (from the manifest purpose) to each layout agent whose source has none; `test_agents_carry_cursor_frontmatter` pins it. install.sh's `.cursor/agents/` copies are unchanged; whether Cursor needs frontmatter there too is part of the pending Cursor UAT.
- **Spec amendment:** N/A — flagged for post-implementation review

#### [DEV-018] Cursor agent-frontmatter claim added to the Verification Record
- **Severity:** Small
- **Spec said:** Rule 1: every platform claim is in the Verification Record first.
- **Implementation did:** `adapters/cursor.md` § Plugin states that Cursor agent files need YAML frontmatter; the claim was read from https://cursor.com/docs/reference/plugins.md on 2026-10-23 and is recorded as V80 (verified 2026-10-23), which the adapter row cites.
- **Reason:** Story 3 read the claim while writing the adapter; the record row keeps Rule 1.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** technical-spec.md § Verification Record gains V80; spec-lite.md Cursor line notes it.

#### [DEV-019] Story 2 and prior-spec test expectations extended for the Cursor layout
- **Severity:** Small
- **Spec said:** Story 3 Notes: "Add a class to it. Do not rewrite Story 2's tests."
- **Implementation did:** Extends Story 2's VERSION check case to expect both stale manifests and adds one `--target cursor-plugin` step to its write-repair test; updates four exact expectations in `test_gen_platform_trees.py` and one in `test_eval_platform_trees.sh` for the new tree. No assertion loosened.
- **Reason:** VERSION feeds both manifests, and every full write and `--check` now covers the Cursor layout.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md Cursor line: Story 2's VERSION and full-write expectations extend in place for the Cursor layout.

#### [DEV-020] The Cursor layout ships `system-instructions.md` at its root
- **Severity:** Small
- **Spec said:** Rule 6 lists `.cursor-plugin/plugin.json`, `rules/writ.mdc`, `skills/`, `commands/`, `agents/`.
- **Implementation did:** After review, also renders `system-instructions.md` at the layout root so the 42 `](../system-instructions.md)` links in commands, agents, and skills resolve, as they do in install.sh's `.cursor/` shape and in the Claude plugin; a link-resolution test guards it. The root file sits outside every discovery directory (V48), so it adds no component.
- **Reason:** Without it the layout is the only Writ shape where those links dangle; the rule file already carries the same text.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md Cursor line lists `system-instructions.md` at the layout root.

---

## Story 5: Smoke Test Across Five Targets, README Install Order, and Live-Run Evidence — Drift Report

> Run: 2026-10-23
> Overall Drift: Medium

### Deviations

#### [DEV-021] `cursor-plugin` script-run reads `unverifiable (no cursor session)`, not `pass (requires project scripts/)`
- **Severity:** Small
- **Spec said:** Rule 9 and technical-spec.md § Smoke Test (`cursor-plugin` row): with the identity `scripts/` form, check in a temp project holding install.sh's script copy and report `pass (requires project scripts/)`.
- **Implementation did:** Follows AC-5.3 and the contract's Success Criteria ("green or `unverifiable (no cursor session)` on Cursor"): the line reads `unverifiable (no cursor session)` when the layout has no `scripts/`, so the target's summary is `unverifiable`.
- **Reason:** The contract outranks Rule 9, and `pass (...)` would break AC-5.1's line grammar. While the layout ships no `scripts/`, `cursor-plugin` cannot read `pass`, so AC-5.4's "Cursor plugin first" branch needs a layout change as well as the UAT.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → Smoke test line: the cursor-plugin script-run line reads `unverifiable (no cursor session)` until the layout ships a plugin-root `scripts/`.

#### [DEV-022] `### Cursor (plugin)` stays in the README when `cursor-plugin` fails
- **Severity:** Medium
- **Spec said:** Rule 10: "when the target fails, the subsection is omitted."
- **Implementation did:** Follows AC-5.4 and the story Notes: `test_readme_install_order` keeps `### Cursor (plugin)` after the Cursor install.sh section, with "local install; marketplace listing pending", for any result short of `pass` plus `cursor-uat run`. Today's fixture reads `cursor-plugin unverifiable`, so today's README is the same under either rule.
- **Reason:** The story Notes chose this branch and asked to amend Rule 10 if the maintainer wants a failing Cursor plugin removed. A failing Cursor plugin path would stay documented with a green test.
- **Resolution:** Fixed 2026-10-24 after UAT: `test_readme_install_order` follows spec Rule 10, so a `cursor-plugin fail` result requires the `### Cursor (plugin)` subsection to be omitted; a mutation run confirms the test fails when it is present.
- **Spec amendment:** N/A — flagged for post-implementation review (options: amend Rule 10 to match AC-5.4, or keep Rule 10 and assert the heading is absent on `cursor-plugin fail`)

#### [DEV-023] Smoke test adds checks and flags beyond the AC
- **Severity:** Small
- **Spec said:** AC-5.1 to AC-5.3 and technical-spec.md § Smoke Test list four checks per target plus `validate`; the story Notes say the maintainer copies the summary lines into the fixture.
- **Implementation did:** Adds an `install` line for the install.sh targets (rc 0 and the local-source line, so install.sh never clones), `validate-marketplace` for `claude-plugin`, `--targets`, `--no-self-test`, `--verbose`, usage errors exiting 2, and `--record`, which writes the fixture (carrying a `cursor-uat run` line forward).
- **Reason:** Sharper diagnosis; no network.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → Smoke test line names the `install` and `validate-marketplace` lines and `--record`.

#### [DEV-024] test-integrity authenticity has no shell analysis
- **Severity:** Small
- **Spec said:** implement-story Gate 4: `test_imports_no_source` is blocking.
- **Implementation did:** `scripts/test-integrity.py` applies its script-invocation pass to `.py` tests only (about line 768), so `scripts/tests/test_plugin_smoke.sh`, like every existing `scripts/tests/*.sh`, reads `test_imports_no_source`. The story's Python test passes; the smoke test's hold on the source is shown by mutation runs (a broken `spec-status.py`, a dropped scaffold path, a removed carrier heading, a changed Writ-block import each made it exit 1).
- **Reason:** Checker blind spot, not a test defect; follow-up: extend authenticity to shell tests that call `bash|python3 "<x>/scripts/<name>"`.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → For Testing Agents, Test Strategy: the bash smoke test is checked by mutation runs; test-integrity authenticity reads `.py` tests only.

---
