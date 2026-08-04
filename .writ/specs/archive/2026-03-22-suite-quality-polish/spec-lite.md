# Suite Quality Polish (Lite)

> Source: .writ/specs/2026-03-22-suite-quality-polish/spec.md
> Purpose: Efficient AI context for implementation

## What We're Building

Five targeted quality fixes to bring the Writ command/agent suite from A- to A+. All changes are markdown file edits — no application code.

## Key Changes

1. **Rewrite `/explain-code`** — Fix broken markdown, remove non-existent feature references, follow established command patterns
2. **Agent input consistency** — Add `context_md_content` to Testing Agent and Documentation Agent
3. **Renumber `/verify-spec` checks** — 1-5,8,9 → sequential 1-7, update all cross-references
4. **Platform-agnostic `/security-audit`** — Replace OpenClaw cron example with generic scheduling note
5. **Move project-specific commands** — `prisma-migration.md` and `test-database.md` to `contrib/`

## Success Criteria

- All commands follow established patterns (Overview, Invocation, Phases, Integration table)
- No broken markdown, no references to non-existent features
- Consistent agent input contracts across all 5 pipeline agents
- Check numbering is sequential with no gaps
- No platform-specific examples in core commands

## Files in Scope

- `commands/explain-code.md` (rewrite)
- `agents/testing-agent.md` (add input)
- `agents/documentation-agent.md` (add input)
- `commands/verify-spec.md` (renumber)
- `commands/ship.md` (update check references)
- `commands/release.md` (update check references)
- `commands/security-audit.md` (replace cron example)
- `commands/prisma-migration.md` (move to contrib/)
- `commands/test-database.md` (move to contrib/)
- `commands/status.md` (update command allowlist)
