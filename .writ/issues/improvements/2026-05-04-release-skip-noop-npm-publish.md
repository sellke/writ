# Decouple `@sellke/writ` runtime helper from `/release`

> **Type:** Improvement
> **Priority:** Normal
> **Effort:** Small
> **Created:** 2026-05-04
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

The `@sellke/writ` npm package is a tiny runtime helper for deterministic Writ dates/timestamps. It is not the methodology in npm form, and `bin/writ.js` is essentially frozen — yet `/release` was bumping its version and trying to publish it on every methodology release. Decouple it: remove npm preflight + publish from `/release` entirely, leave `package.json#version` untouched by `/release`, and document a one-shot manual publish path for the rare case where `bin/` actually changes.

## Current State

- `commands/release.md` Step 1.3d ran `npm test` + `node bin/writ.js` smoke checks + `npm pack --dry-run` whenever root `package.json#name == "@sellke/writ"`.
- `commands/release.md` Step 4.4 ran `npm publish --access public` + `npx` smoke verification under the same condition.
- `commands/release.md` Step 3.1 unconditionally bumped `package.json#version` to match `VERSION` for any project with a `package.json`.
- `bin/writ.js` has been touched in **exactly one** commit in repo history: `fdb72e4 feat(runtime): add Writ timestamp helper` (v0.15.0). Untouched since.
- npm registry has only `0.14.0` and `0.15.0` published. v0.16.0 and v0.17.0 were both methodology-only releases that hit the `npm whoami` E401 gate and were deferred — but the deferral was theatre: the tarball contents would have been byte-for-byte identical to v0.15.0 modulo the `version` field. There was nothing real to publish.
- Result: every methodology release pretended to ship a new npm version that was functionally a no-op, and the release summary reported phantom "publish deferred" follow-ups that were never actionable.

## Expected Outcome

- `/release` does **not** run npm preflight, does **not** run `npm publish`, does **not** bump `package.json#version`, and does **not** include an "npm Package" line in the release summary.
- The methodology version (`VERSION`, `CHANGELOG.md`, git tags) is the single source of truth for what `/release` ships, and it advances independently of the npm helper version.
- `package.json#version` reflects the last actually-published npm version (`0.15.0`) and stays put until someone manually bumps it.
- `commands/release.md` carries a brief, clearly-Writ-self-only "Runtime Helper Publish (manual)" section documenting the manual workflow for the rare case where `bin/writ.js` does change: `npm version <bump> && npm publish --access public`. Three lines, no orchestration.
- `--dry-run` preview reflects the new shape (no npm commands listed for `@sellke/writ`).

## Relevant Files

- `commands/release.md` — primary edit target (Step 1.3d removed; Step 3.1 conditional skip for `@sellke/writ`; Step 4.4 removed; Phase 5 npm summary line removed; Dry Run npm block trimmed; new "Runtime Helper Publish (manual)" section added).
- `package.json` — `version` reset from drifted `0.17.0` back to actual-published `0.15.0`.
- `.writ/specs/2026-04-28-writ-runtime-timestamp-service/spec.md` — original rationale for the runtime helper. Nothing here challenges its existence; only the publish cadence and the `/release` coupling.

## Notes

- **Original framing (gate on package-surface diff) was wrong.** The first prototype added a clever `git diff` + `jq 'del(.version)'` gate to skip npm publish only when no surface changed. That managed complexity instead of eliminating it. User pushback ("It probably will never change. Let's just keep it simple.") reframed the problem: the right answer is to decouple, not to gate. Smaller diff, fewer concepts, accurate to design intent.
- **Why not delete the npm package entirely?** Because the helper does serve a real purpose — `npx @sellke/writ date` and `npx @sellke/writ timestamp` give Writ commands a portable, dependency-free way to produce deterministic timestamps regardless of which platform is running. The package should exist; it just should not be coupled to methodology release cadence.
- **Honest accounting of releases v0.16.0 and v0.17.0.** Both shipped "npm publish deferred" notes that were misleading — there was no real pending publish work, just a version-string bump that would have produced a byte-equivalent tarball. Future release notes will not include phantom npm follow-ups.
- **Possible follow-up (low priority):** drop `README.md` from `package.json#files` and add a tiny `bin/README.md` so the helper tarball doesn't ship the methodology README. Not blocking — just a hygiene improvement if/when someone next touches `bin/`.
- **Status:** Prototyped on `main` working tree (uncommitted) — see edits to `commands/release.md` and `package.json` reset. Ready to ship as a `chore: decouple @sellke/writ from /release` commit alongside the next methodology release, or earlier as a standalone PR.
