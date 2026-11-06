# Why: /writ confirmation offers at most four options

> **Asked:** 2026-10-25
> **Subject:** `commands/writ.md` § Step 3: Confirm; `/writ` route confirmation; four options
> **Change:** add a fifth option to /writ's confirmation
> **Question:** Why does `/writ`'s confirmation offer at most four options? I want to add a fifth.

## Why: /writ confirmation offers at most four options

**Answer:** Claude Code's question tool takes two to four options per question, and the front-door UAT saw the widget show only four, so the confirmation was cut from up to seven options to the proposed route, two alternatives, and "Not what I meant", with the left-out routes named in the prompt. — Recorded

### Claims

| # | Claim | Tier | Evidence |
|---|---|---|---|
| 1 | The confirmation holds at most four options because Claude Code's question tool takes two to four per question | Recorded | `.writ/specs/2026-10-22-front-door/spec.md` § Business Rules, rule 4 (amended 2026-10-24, DEV-007) |
| 2 | The cap was found in the Phase 14 acceptance pass: front-door S10 saw the widget show four of up to seven options | Recorded | `.writ/specs/2026-10-22-front-door/drift-log.md` → DEV-007 |
| 3 | The platform fact comes from the tool schema observed in Claude Code 2.1.310 | Recorded | `adapters/claude-code.md` § Quick Reference, `AskQuestion()` row; DEV-007 Reason |
| 4 | Routes that do not fit are named in the prompt so the user can ask for one through "Not what I meant" | Recorded | `.writ/specs/2026-10-22-front-door/spec.md` § Business Rules, rule 4; `commands/writ.md` § Step 3 |
| 5 | A test pins the cap, the two alternatives, and the "Other routes" line | Recorded | `.writ/specs/2026-10-22-front-door/drift-log.md` → DEV-007 Resolution; `scripts/tests/test_front_door.py` `test_confirmation_fits_four_options` |

### Sources searched

- Ledger: `.writ/specs/2026-10-22-front-door/spec.md` (Business Rule 4), `.writ/specs/2026-10-22-front-door/drift-log.md` (DEV-007), `adapters/claude-code.md` (`AskQuestion()` row and the question-tool paragraph); no `refs/notes/writ` note on `9d75383` or `00f8261`; nothing in `.writ/decision-records/` or `.writ/knowledge/` on the option cap
- Git: `00f8261` (Step 3 created with every route as an option), `9d75383` (cut to four, 2026-10-24); no commit touched Step 3 after `9d75383`, so no stale-ledger line
- MCP: not read: the ledger answered at Recorded

## Preserve / Change / Avoid / Risk

### Preserve
- At most four options in the one AskQuestion: Claude Code's question tool renders two to four per question — Recorded, `.writ/specs/2026-10-22-front-door/spec.md` Business Rule 4 and DEV-007
- "Not what I meant" stays an option, and the prompt names the routes left out, so every route remains reachable — Recorded, `.writ/specs/2026-10-22-front-door/spec.md` Business Rule 4

### Change
- A fifth choice can enter as a replacement for one of the two alternatives or as a route named in the prompt's "Other routes" line rather than as a fifth option — Inferred, `.writ/specs/2026-10-22-front-door/spec.md` Business Rule 4 and DEV-007 Implementation did

### Avoid
- Offering every route as its own option: the original Step 3 did this (up to seven options) and the widget showed only four — Recorded, `.writ/specs/2026-10-22-front-door/drift-log.md` DEV-007; commit `9d75383`

### Risk
- A fifth option is dropped or truncated by Claude Code's question tool, so the user never sees it — Recorded, `adapters/claude-code.md` `AskQuestion()` row; DEV-007 Reason
- `scripts/tests/test_front_door.py` `test_confirmation_fits_four_options` fails on a fifth option (`alt-3` is forbidden) — Recorded, `.writ/specs/2026-10-22-front-door/drift-log.md` DEV-007 Resolution
