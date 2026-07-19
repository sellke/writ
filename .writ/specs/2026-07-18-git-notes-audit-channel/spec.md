# Spec: Git-Notes Audit Channel

> **Status:** Complete
> **Owner:** @Adam Sellke
> **Created:** 2026-07-18
> **Origin:** Recommendation #1 from [`2026-07-18-writ-vs-conductor-analysis.md`](../../research/2026-07-18-writ-vs-conductor-analysis.md)

## Contract (Locked)

**Deliverable:** A git-native, immutable audit trail for Writ. When a spec lands via `/ship`, Writ composes a condensed **audit digest** from the spec's "What Was Built" (WWB) records and attaches it — under a dedicated `refs/notes/writ` ref — to the commit that actually lands on the base branch. `/release` attaches a version-level rollup note to the release/tag commit. Notes are push/fetch-configured so the audit travels with the repo. Default-on, with a documented opt-out.

**Must include:** The audit note attaches to the **surviving** commit (post-squash/merge), so it is not orphaned by `/ship`'s squash-merge.

**Hardest constraint:** git notes bind to a commit SHA. `/ship` squash-merges (new SHA) and notes are neither pushed nor fetched by default. Both must be handled or the audit trail is orphaned and local-only.

## Why This Exists

Writ already records **"What Was Built"** at each story completion (see `.writ/docs/what-was-built-format.md`). WWB is *forward-looking* context — it feeds downstream agents and lives inside story markdown. It is **not** an immutable, commit-bound audit record:

- It lives in the working tree and can be edited after the fact.
- It is per-story, not bound to the commit that shipped the work.
- It does not travel as an independent, queryable channel.

Conductor (`gemini-cli-extensions/conductor`) demonstrated the complementary idea: attach a durable summary and verification report to commits via `git notes`. The audit then lives in git, travels with the commit, survives file moves, stays out of the diff, and is queryable with `git log --notes`.

This spec adopts that idea in a way that fits Writ's PR-based `/ship` flow (which Conductor never had to solve, because it commits directly on a branch).

## 🎯 Experience Design

### Entry Point

Automatic. Two attach points, both owned by Writ commands:

1. **`/ship`** — after the branch lands on the base branch, attach a **spec-level audit digest** to the landed commit.
2. **`/release`** — after the version is tagged, attach a **version rollup** to the release/tag commit.

### Happy Path

1. Developer completes a spec's stories via `/implement-spec` (WWB records written per story).
2. Developer runs `/ship`.
3. `/ship` merges/squashes the branch onto the base branch → produces the **landed commit SHA**.
4. Writ reads the spec's story WWB verdicts, composes one consolidated digest, and runs `git notes --ref=writ add -F <digest> <landed-sha>`.
5. `/ship` reports: `📝 Audit note attached to <sha> (refs/notes/writ)`.

### Moment of Truth

`git log --notes=writ` on the base branch shows, inline under the landed commit, the exact review verdict, coverage, drift IDs, and files — an immutable record that outlives the working tree and the story files.

### Feedback Model

- `/ship` and `/release` print a one-line confirmation with the note ref and target SHA.
- `/status` surfaces a one-line pointer to the most recent audit note.

### Error Experience (Non-Blocking)

Note composition or attachment failure **never fails the ship or release**. It logs a visible warning and continues. This mirrors the WWB principle: *"The pipeline must NEVER block completion due to incomplete audit data. Partial records are better than no records."*

| Failure | Behavior |
|---|---|
| No WWB records found for spec | Warn, attach a minimal digest (spec ref + landed SHA + `git diff --stat`) |
| `git notes add` fails (e.g., permissions) | Warn `⚠️ audit note not attached — {error}`, continue ship/release |
| Notes ref config missing on a fresh clone | Notes still attach locally; warn that sync refspec is unconfigured, point to opt-out doc |
| Feature disabled via opt-out flag | Silent no-op — no note, no git-config changes |

## 📋 Business Rules

1. **Attach to the surviving commit only.** The digest attaches to the post-squash/merge tip that lands on the base branch — never to a pre-merge story commit (which squash orphans). For a rebase-and-merge that replays N commits, attach the spec rollup to the **tip** landed commit.
2. **Dedicated ref.** All Writ audit notes use `refs/notes/writ`. Never write to `refs/notes/commits` (the git default), to avoid clobbering a user's own notes.
3. **Digest content is audit-only.** Review verdict, coverage %, drift severity + DEV-IDs, review iteration count, files touched, spec/story refs, landed SHA range. **Never** include chain-of-thought, prompts, or transcripts (Prime Directive audit constraint).
4. **Default-on, opt-out clean.** The feature is on by default. A single config flag disables *both* note attachment *and* the git-config refspec setup. Opt-out must leave no git-config side effects.
5. **Sync by configuration.** `install.sh`/setup configures `remote.<remote>.push` and `fetch` refspecs for `refs/notes/writ` so the audit travels on clone/fetch — unless opted out.
6. **Non-blocking always.** Never fail `/ship` or `/release` due to audit-note problems.

## Detailed Requirements

### Digest schema (spec-level, attached at `/ship`)

The digest is composed from the completed spec's story WWB records plus the landed commit range. Full schema in `sub-specs/technical-spec.md` and the new `.writ/docs/git-notes-audit-format.md`. Summary fields:

- **Spec:** folder id + title
- **Landed:** base branch, landed SHA, source commit range
- **Stories:** table of story → review result → drift → coverage
- **Aggregate verdict:** overall review outcome, highest drift severity, total DEV-IDs, aggregate coverage
- **Files:** created/modified counts (+ optional list)
- **Generated by:** Writ version + date

### Version rollup (attached at `/release`)

Composed from the specs included since the previous release tag: version, date, list of shipped specs with their aggregate verdicts, changelog ref.

### Read surface

- Documented canonical command: `git log --notes=writ` (and `git notes --ref=writ show <sha>`).
- `/status` prints a single line: `📝 Last audit note: <sha> — <spec title> (<date>)`.
- No bespoke reader command (excluded from scope).

### Sync configuration

`install.sh` (and platform setup) configures, unless opted out:

```
git config --add remote.<remote>.fetch "+refs/notes/writ:refs/notes/writ"
git config --add remote.<remote>.push  "refs/notes/writ"
```

Guarded: idempotent (no duplicate refspecs), skipped when opted out, and reversible via the opt-out path.

## Implementation Approach

All changes are to Writ **product source** (markdown commands, a docs file, `install.sh`) — this ships to all Writ users. No application runtime code. Verification is via `scripts/eval.sh` static checks + manual dogfooding on this repo (which itself uses `/ship`).

- **`commands/ship.md`** — add a terminal "Audit Note" step after the merge/land step.
- **`commands/release.md`** — add an "Audit Rollup" step after tagging.
- **`commands/status.md`** — add the one-line audit pointer.
- **`scripts/install.sh`** — add guarded notes refspec configuration + opt-out handling.
- **`.writ/docs/git-notes-audit-format.md`** — new digest schema + read/sync/opt-out docs.
- **`.writ/decision-records/adr-017-git-notes-audit-channel.md`** — new ADR recording the decision, the squash-survival rationale, and the WWB-vs-notes boundary.

## Success Criteria

1. After `/ship` of a spec, `git log --notes=writ` on the base branch shows the audit digest on the landed commit.
2. The digest never contains transcripts/prompts/chain-of-thought.
3. A fresh clone with configured fetch refspec sees the notes.
4. The opt-out flag suppresses note attachment **and** leaves git config untouched.
5. `/ship` and `/release` succeed even when audit-note composition fails (non-blocking).
6. `scripts/eval.sh` gains a check asserting `ship.md`/`release.md` reference `refs/notes/writ` and the non-blocking rule.

## Scope Boundaries

**Included:** `/ship` + `/release` note attachment, `.writ/docs/git-notes-audit-format.md`, ADR-017, install/setup refspec config + opt-out, `/status` read line, an eval check.

**Excluded:** Per-story branch-local notes (dropped by squash — deliberately rejected), a bespoke `writ notes` reader command, retroactive backfill of historical commits, GitHub PR-comment mirroring of the digest.

## Dependencies

None (external). Internal story order: Story 1 (format + ADR) is the foundation for Stories 2–4.
