# Drift Log

> Spec: .writ/specs/2026-10-22-front-door/
> Created: 2026-10-22
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: The `/writ` Command File — Drift Report

> Run: 2026-10-22
> Overall Drift: Small

### Deviations

#### [DEV-001] Overview states the Claude Code plugin name `/writ:writ`
- **Severity:** Small
- **Spec said:** spec.md → Technical Concerns accepts the `/writ:writ` plugin name and assigns its documentation to `2026-10-22-plugin-distribution`; the story Notes say "No change here."
- **Implementation did:** `commands/writ.md` → Overview carries one sentence: "Under a Claude Code plugin the command reads `/writ:writ`."
- **Reason:** A reader of the installed command has no other place to learn the namespaced name. The sentence duplicates a fact the plugin spec owns and can go stale if that spec changes the namespace.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** None needed. spec-lite.md → Integration Points already states the plugin name.

#### [DEV-002] Step 1 adds an issue-file restatement heuristic
- **Severity:** Small
- **Spec said:** The Invocation row `/writ @file` reads an issue or other file as the request; Interaction Patterns say `--from-issue <path>` travels with the route. No rule derives the restatement from an issue's fields.
- **Implementation did:** `commands/writ.md` → Step 1, last bullet: "An issue's title and expected outcome are the goal and done check unless the body says otherwise."
- **Reason:** Restatement guidance for the file case, not classification logic; Business Rule 1 (the table is the only classifier) is untouched.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** None needed. spec-lite.md does not describe the file case beyond the invocation.

---

## Story 2: Registration and Catalogs — Drift Report

> Run: 2026-10-22
> Overall Drift: Small

### Deviations

#### [DEV-003] `commands/status.md` Maintainer Note bare list also gains `writ`
- **Severity:** Small
- **Spec said:** Contract item 5 names "`commands/status.md` command list"; technical-spec.md → Registration Edits names the slash allowlist only ("add `/writ` first").
- **Implementation did:** `/writ` first in the slash allowlist and `writ` first in the bare list under `## Maintainer Note: Command Allowlist`.
- **Reason:** The Maintainer Note's own rule says "If a new command is added to the suite, add it here," and `test_status_allowlists` checks both lists together; updating one would leave them disagreeing.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → Implementation Approach, Registration line now reads "`status.md` lists (the slash allowlist and the Maintainer Note bare list both add `writ` first)".

#### [DEV-004] README install follow-up lines and closing sentence point at `/writ`
- **Severity:** Small
- **Spec said:** Business Rule 10 specifies the opening of § Quick Start; contract item 5 says § Quick Start is rewritten so `/writ` is the first thing a reader sees. The per-platform install subsections are not named.
- **Implementation did:** Inside § Quick Start, the Cursor, Claude Code, and Codex "Then in …" lines read `/writ "my feature"` (Codex: "follow `.codex/commands/writ.md`"), and the closing sentence ends "; `/writ` picks the route for you." The "Writ ships 32 commands" count is dropped per the story Notes.
- **Reason:** The install subsections are H3s under `## Quick Start`; leaving them at `/create-spec "my feature"` would contradict the front door the section now opens with.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → Registration line now says the per-platform install follow-up lines name `/writ "my feature"`.

#### [DEV-005] Maintenance edits to two pre-existing test files outside the S2 file list
- **Severity:** Small
- **Spec said:** spec-lite.md → Files in Scope (S2) lists `scripts/tests/test_front_door.py` as the only test file; task 2.1 names `test_platform_neutral_names.py` as a style reference.
- **Implementation did:** `scripts/tests/test_gen_claude_md.py` `EXPECTED_FIXTURE` gains the "Start with" line; `scripts/tests/test_platform_neutral_names.py` `test_status_allowlists` anchors on the `create-spec` token instead of the line start (both lists), and `test_cursor_tree` sorts the expected tree entries by command name.
- **Reason:** Each is forced by a contracted edit (the TEMPLATE line; `writ` first in the lists; `writ.md` before `writ-design.md` in the tree) and the suite is red without it. Each test's intent is unchanged.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → Files in Scope (S2) line names the two maintenance edits.

---
