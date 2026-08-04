# Pipeline Streamlining (Lite)

## What

Streamline ship, verify-spec, and release so each has one job. Drop the 5-command pre-release ceremony to 2 commands.

## Key Changes

1. **verify-spec** shrinks to pure metadata diagnostic. Remove --pre-deploy, Trello, changelog generation. Default becomes auto-fix.
2. **release** absorbs the release gate (tests + build + spec validation). Conditional test run: skip when HEAD matches last merged PR.
3. **ship** makes tests opt-in (`--test` flag). Adds silent inline spec health check (checks 1-3) in PR body.

## Pipeline After

```
/review (optional) → /ship → /release
```

verify-spec is independent — run when you suspect drift, never a prerequisite.

## Key Constraints

- Trello removed entirely from pipeline
- Changelog generation only in /release
- Release gate build checks (typecheck/lint/format) always run, test suite conditional
- Ship's inline spec check: checks 1-3 only, silent when clean

## Files Changed

- `commands/verify-spec.md` — rewrite
- `commands/release.md` — rewrite
- `commands/ship.md` — refine
- Cross-references in other command files

## Stories

4 stories: verify-spec shrink → release gate → ship tighten → cross-references
