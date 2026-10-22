# `/prototype` Is Silent on an Extra Comparison Page

> **Type:** Improvement
> **Priority:** Low
> **Effort:** XS
> **Created:** 2026-10-22
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

Two agents in the Phase 13 UAT each wrote a fourth HTML page that shows all three drafts side by side:
- Codex (platform-neutral-names Scenario 10) wrote `index.html`.
- Claude Code (Scenario 8) wrote `compare.html`.

`/prototype` Step 2.5 says "a self-contained HTML page per draft" and neither allows nor forbids the extra page. Codex's final reply linked only `index.html`, not each draft, even though `adapters/codex.md` says "give the user each path".

## Expected Outcome

Decide one way and say it in `commands/prototype.md` Step 2.5:

- **Allow:** an optional comparison page that embeds each draft. The reply must still list every draft path.
- **Forbid:** one file per draft, nothing else.

Allowing it looks right, because two platforms chose it on their own. Update the UAT expectation ("one `.html` file per draft") to match the decision.

## Relevant Files

- `commands/prototype.md`: Step 2.5
- `adapters/codex.md`, `adapters/openclaw.md`, `adapters/claude-code.md`: `canvas-preview` rows
- `.writ/specs/2026-10-20-platform-neutral-names/uat-plan.md`: Scenarios 8 and 10 notes
