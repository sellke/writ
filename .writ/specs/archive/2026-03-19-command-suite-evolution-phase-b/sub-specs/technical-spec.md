# Command Suite Evolution Phase B — Technical Spec

> Spec: Command Suite Evolution Phase B
> Created: 2026-03-19
> Stories: 5, 7, 9
> Phase A technical spec: `.writ/specs/2026-03-19-command-suite-evolution/sub-specs/technical-spec.md`

---

## Implementation Approach

All three changes are edits to existing markdown command and agent files. No build step, no CLI, no runtime code.

**Note:** The full format definitions for `.writ/config.md` (Story 1), the BLOCKED output contract (Story 2), and file-level change patterns for stories 1–4, 6, 8 are in the Phase A technical spec. This spec covers only Phase B additions.

---

## New Files and Formats

### `.writ/context.md` (Story 5)

Auto-generated summary file. Written by `/status`, `/implement-story` (at gate transitions), `/implement-spec` (on story completion). Format defined in Phase A technical spec under "New Files and Formats."

**Regeneration rule:** Every write is a full file replace. No incremental patching.

---

## File-Level Changes

### Story 5: `agents/coding-agent.md`, `agents/review-agent.md`, `agents/architecture-check-agent.md`, `commands/implement-story.md`, `commands/implement-spec.md`, `commands/status.md`

Changes as specified in Phase A technical spec (Story 5 section). Apply on top of Phase A Story 4's `status.md` rewrite.

### Story 7: `commands/create-spec.md`, `commands/create-issue.md`, `commands/status.md`

Changes as specified in Phase A technical spec (Story 7 section). Apply on top of Phase B Story 5's `status.md` additions.

### Story 9: `commands/refresh-command.md`, `commands/status.md`

Changes as specified in Phase A technical spec (Story 9 section). Apply on top of Phase B Story 7's `status.md` additions (Needs Triage section).

---

## Status.md Edit Sequence (critical)

`status.md` receives four separate additions across the full spec. The order is non-negotiable:

1. **Phase A Story 1** — add config read (first operation, top of command)
2. **Phase A Story 4** — full rewrite: config read, in-flight jobs, refresh opportunities, phantom removal
3. **Phase B Story 5** — add context.md regeneration step
4. **Phase B Story 7** — add Needs Triage section
5. **Phase B Story 9** — add batch refresh auto-trigger wording and 3+ transcript condition

Each edit extends the file produced by the prior story. Never attempt parallel edits on `status.md`.

---

## Error Mapping

| Operation | What Can Fail | Planned Handling |
|---|---|---|
| Read `.writ/context.md` | File doesn't exist | Skip gracefully, agent continues without it |
| Regenerate context.md | Source files missing | Use empty/default values for missing sections |
| `--from-issue` mode | Issue file not found | Error: "File not found: [path]" |
| Batch transcript analysis | Fewer than N transcripts | Analyze available transcripts, note count |
