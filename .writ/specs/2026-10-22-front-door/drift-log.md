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
