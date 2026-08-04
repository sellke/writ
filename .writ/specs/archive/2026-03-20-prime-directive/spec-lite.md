# Prime Directive — Spec Lite

> Compact context for agents. Full spec: `spec.md`

## What

Inline anti-sycophancy prime directive into `system-instructions.md` and `cursor/writ.mdc`. Replace phantom reference to non-existent `.writ/docs/best-practices.md`.

## Key Constraints

- Under 35 lines added (loads every session)
- Content: 3 hard constraints (never reverse without evidence, never confirm without checking, never pad with empty affirmation) + 5 judgment principles (separate facts/assumptions, generate alternatives, name problems early, match confidence to evidence, disagree with evidence not attitude)
- Both files must stay in sync
- Product source change — ships to all Writ installations

## Files in Scope

- `system-instructions.md` — replace line 32 reference with Prime Directive section
- `cursor/writ.mdc` — identical change
- `CHANGELOG.md` — new entry
- `VERSION` — bump to 0.7.0

## Success Criteria

- Phantom reference gone from both files
- Prime directive content present and identical in both
- Under 35 lines added
- No install.sh changes needed
