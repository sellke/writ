# Consolidate Conventional Commits guidance into the new skill

> **Type:** Improvement
> **Priority:** Normal
> **Effort:** Small
> **Created:** 2026-05-04
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

Wire `commands/ship.md` and `commands/release.md` to reference the new `skills/conventional-commits/SKILL.md` instead of inlining their own commit-format guidance, so the duplication identified in ADR-009 actually collapses.

## Current State

- `skills/conventional-commits/SKILL.md` exists, lint-clean, registered in the manifest, and rendered into the root `SKILL.md` catalog.
- `commands/ship.md` lines 206–223 inline the full commit-format spec — header grammar, type/scope/summary/body/ref source-of-truth table, and the "match the project's existing convention" recommendation.
- `commands/release.md` inlines the type-parsing rules at lines 70–76 and the description-source priority list at lines 238–242 — both implicitly depend on the same Conventional Commits vocabulary the skill now owns.
- No consumer (command or agent) currently `Read`s the skill, so the consolidation that justified extracting it is theoretical until one of these files points at it.
- `agents/coding-agent.md` does not currently inline commit guidance at all — different problem (inconsistency rather than duplication), but worth solving on the same pass.

## Expected Outcome

- `commands/ship.md` Step 4 trims its inline format block down to the *splitting heuristic* (which belongs to the command — choosing what each commit contains) and adds a `Read skills/conventional-commits/SKILL.md` instruction at the point where the message is authored.
- `commands/release.md` references the skill where it parses commits for changelog generation; keeps the version-bump rules (those are release-specific, not commit-format).
- `agents/coding-agent.md` references the skill at the point of TDD commit creation, so coding-agent commits match `/ship` commits stylistically.
- Net token reduction in the two command files; single source of truth for commit format guidance; coding-agent gains a consistency it didn't previously have.
- Decision recorded: inline `Read skills/conventional-commits/SKILL.md` references vs. `required_skills:` frontmatter (currently reserve-only per `system-instructions.md`, review trigger 2026-08-03 — using inline references now matches the documented pattern).

## Relevant Files

- `commands/ship.md` — lines 206–223 inline the full format spec; primary consolidation target.
- `commands/release.md` — lines 70–76 (type parsing) and 238–242 (description source priority) implicitly depend on the same vocabulary.
- `skills/conventional-commits/SKILL.md` — the consolidation target; already complete and lint-clean.

## Notes

- This is the realization step for ADR-009's pilot-skill scope. The decision record explicitly names `conventional-commits` as a pilot extraction; this issue closes the loop by making at least one consumer actually consume it.
- Do **not** strip ship.md's "match the project's existing convention" recommendation as a separate point — it now lives inside the skill, but the meta-decision (when ship.md should invoke the skill at all) still belongs to the command.
- Keep ship.md's commit-splitting heuristic and message-source table (Type/Scope/Summary/Body/Ref columns) — those describe *which* changes go into a commit and *where* the data comes from, which is orchestration, not format. The skill only owns *how the message is phrased*.
- Consider whether `commands/refactor.md` and `commands/retro.md` should also reference the skill. `retro.md` parses commits with implicit Conventional Commits assumptions; `refactor.md` has no current inline guidance. Lower priority than ship/release.
- After consolidation, run `bash scripts/lint-skill.sh skills/conventional-commits/SKILL.md` once more to confirm no consumer added a circular `Read commands/...` instruction back into the skill body.
