# Technical Specification: Suite Quality Polish

> Created: 2026-03-22
> Spec: 2026-03-22-suite-quality-polish

## Architecture

No architectural changes. All work is editing existing markdown files or moving files between directories.

## File Map

| File | Stories | Change Type |
|------|---------|-------------|
| `commands/explain-code.md` | 1 | Full rewrite |
| `agents/testing-agent.md` | 2 | Add input parameter + prompt section |
| `agents/documentation-agent.md` | 2 | Add input parameter + prompt section |
| `commands/verify-spec.md` | 3 | Renumber check headings and references |
| `commands/ship.md` | 3 | Update check number cross-references |
| `commands/release.md` | 3 | Update check number cross-references |
| `commands/security-audit.md` | 4 | Replace cron example |
| `commands/prisma-migration.md` | 5 | Move to `contrib/` |
| `commands/test-database.md` | 5 | Move to `contrib/` |
| `commands/status.md` | 5 | Update command allowlist |

## Patterns to Follow

### `/explain-code` Rewrite (Story 1)

Use `/review` (199 lines) as the structural template:
- Overview with clear purpose statement
- Invocation table with modes/flags
- Command Process with numbered steps
- Integration with Writ table at the bottom

### Agent Input Consistency (Story 2)

Match the exact pattern from `agents/coding-agent.md`:

**Input Requirements table row:**
```
| `context_md_content` | **First context item.** Contents of `.writ/context.md` if present — product mission, active spec state, recent drift. Pass empty string if file doesn't exist yet. |
```

**Prompt template injection:**
```
## Project Context

{context_md_content}

---
```

### Check Renumbering (Story 3)

Mapping:
- Checks 1-5: unchanged
- Check 8 → Check 6 (Spec Contract vs Implementation)
- Check 9 → Check 7 (Spec-Lite Integrity)

Cross-reference updates needed:
- `commands/ship.md`: "checks 1–3" — unchanged (those numbers didn't shift)
- `commands/release.md`: "checks 1–5 and 8" → "checks 1–6"
- `commands/verify-spec.md`: all internal references

## Risks

- **Story 3 cross-references:** Other commands may reference verify-spec check numbers in ways not covered by the task list. A full grep for "check 8" and "check 9" across all files is warranted.
- **Story 5 allowlist:** The `/status` command has two separate allowlist locations (Step 9 conditions table and Maintainer Note). Both must be updated.
