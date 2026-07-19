# ADR-017: Git-Notes Audit Channel — Immutable, Commit-Bound Audit Trail

> **Date:** 2026-07-18
> **Status:** Accepted
> **Category:** Framework Architecture
> **Origin:** Recommendation #1 from [`2026-07-18-writ-vs-conductor-analysis.md`](../research/2026-07-18-writ-vs-conductor-analysis.md)

## Decision

Writ attaches an **immutable, commit-bound audit digest** to shipped work using
`git notes` under a **dedicated `refs/notes/writ` ref**. `/ship` composes a
spec-level digest from the spec's per-story "What Was Built" (WWB) records and
attaches it to the commit that **actually lands on the base branch** (post
squash/merge). `/release` attaches a version rollup to the release/tag commit. The
notes are push/fetch sync-configured by `install.sh` so the audit travels with the
repo. The feature is **default-on with a clean git-config opt-out**
(`writ.auditNotes`), and audit-note failure is **always non-blocking**.

The full schema, read/sync/opt-out mechanics, and the WWB boundary live in
[`.writ/docs/git-notes-audit-format.md`](../docs/git-notes-audit-format.md).

## Context

Writ already records **"What Was Built"** at each story completion (see
[`what-was-built-format.md`](../docs/what-was-built-format.md)). WWB is
*forward-looking* context — it feeds downstream agents and lives inside story
markdown. It is **not** an immutable, commit-bound audit record:

- It lives in the working tree and can be edited after the fact.
- It is per-story, not bound to the commit that shipped the work.
- It does not travel as an independent, queryable channel.

Conductor (`gemini-cli-extensions/conductor`) demonstrated the complementary idea:
attach a durable summary and verification report to commits via `git notes`. The
audit then lives in git, travels with the commit, survives file moves, stays out of
the diff, and is queryable with `git log --notes`.

Two mechanics make a naive adoption fail for Writ:

1. **`git notes` bind to a commit SHA.** Writ's `/ship` squash-merges — the work
   lands as a **new** commit, and any note attached to a pre-merge story commit is
   orphaned.
2. **Notes are neither pushed nor fetched by default.** Without refspec
   configuration, the audit trail is local-only and never shared.

Both must be handled explicitly or the audit trail is worthless (orphaned and
stranded on one machine). Conductor never had to solve #1 because it commits
directly on a branch; Writ's PR-based flow forces the issue.

## Decision Detail

### Attach to the surviving (landed) commit — squash-survival

The digest attaches to the **post-squash/merge tip that lands on the base branch** —
never to a pre-merge story commit. Land strategies resolve as:

- **Squash-merge** → the single squash commit (`git rev-parse <base>` after merge).
- **Merge commit** → the merge commit SHA.
- **Rebase-and-merge** (replays N commits) → the **tip** of the replayed commits.

This is the load-bearing decision: because a note cannot survive the SHA change of a
squash, the only durable attach point is the commit that actually exists on the base
branch after landing. `notes.rewriteRef` is offered as *local* hardening (copies
notes forward on `rebase`/`amend`) but explicitly does **not** rescue squash-merge,
which is why post-land attachment is primary rather than per-story-plus-copy.

### Dedicated `refs/notes/writ` ref

All Writ audit notes use `refs/notes/writ`, never `refs/notes/commits` (the git
default). A dedicated ref avoids clobbering a user's own notes and lets sync
refspecs target exactly Writ's channel.

### Audit-only content (no transcripts / CoT)

The digest carries only audit fields: review verdict, coverage %, drift severity +
DEV-IDs, review iteration count, files touched, spec/story refs, landed SHA range.
It **never** includes chain-of-thought, prompts, or transcripts. This is the same
durable-audit constraint [ADR-013](adr-013-recommended-autonomous-delivery.md)
established for recommended-delivery summaries — audit records are observable
evidence, not private reasoning.

### Default-on, clean opt-out; always non-blocking

A single per-repo git-config key `writ.auditNotes` (default `true`) gates *both*
note attachment *and* the sync-refspec setup. Disabling it makes `/ship` and
`/release` silent no-ops and makes `install.sh` remove any Writ-added refspecs,
leaving no residue. Composition or attachment failure never fails a ship or release —
it warns and continues, mirroring WWB's "partial records beat no records" principle.

## Considered Alternatives

**A. Per-story branch-local notes (attach at each story commit).** Rejected. Writ's
`/ship` squash-merges, so per-story notes are attached to commits that the squash
orphans — the audit would vanish from the base branch. Even `notes.rewriteRef` does
not help, because a squash produces a *new* commit rather than *rewriting* an
existing one. Attaching the consolidated digest to the surviving landed commit is the
only squash-durable option.

**B. Use the default `refs/notes/commits` ref.** Rejected. It is the ref `git notes`
writes to by default and the one users are most likely to use themselves. Writing
Writ digests there risks clobbering user notes and makes it impossible to sync only
Writ's channel. A dedicated `refs/notes/writ` isolates the audit cleanly.

**C. Store the full WWB record in the note.** Rejected. WWB narratives can include
"Implementation Decisions" prose that risks transcript-like content, violating the
audit-only constraint; they are also per-story and verbose. The note aggregates WWB
into a bounded, audit-only digest and *references* the spec/drift-log for depth,
rather than duplicating the working-tree record into git.

**D. Mirror the digest as a GitHub PR comment instead of git notes.** Rejected (out
of scope). PR comments are platform-specific, mutable, and do not travel with the
repo on clone. Git notes are git-native and platform-agnostic — the whole point of
the channel.

## Consequences

**Positive:**

- An immutable, commit-bound, queryable audit trail (`git log --notes=writ`) that
  survives squash-merge, file moves, and working-tree edits.
- Complements WWB without duplicating it — the two occupy distinct positions on the
  mutability/granularity/audience axes (see the format doc's boundary table).
- Default-on sync means the audit is actually shared; the clean opt-out respects
  repos that don't want it, with no config residue.
- Non-blocking design means the audit channel can never break shipping or releasing.

**Negative:**

- The digest is only as good as the WWB records it aggregates; a spec with no WWB
  gets a minimal (git-diff-stat) digest. Mitigation: the documented minimal-digest
  fallback + warning.
- Notes require sync configuration to travel; a fresh clone without the fetch refspec
  sees no notes. Mitigation: `install.sh` configures the refspecs by default and the
  format doc documents the manual `git config` for existing clones.
- A second audit surface (notes) alongside WWB risks reader confusion about which is
  authoritative for what. Mitigation: the explicit WWB ↔ notes boundary table in the
  format doc and this ADR.

## References

- Owning spec — [`2026-07-18-git-notes-audit-channel`](../specs/2026-07-18-git-notes-audit-channel/spec.md)
- Technical spec — [`sub-specs/technical-spec.md`](../specs/2026-07-18-git-notes-audit-channel/sub-specs/technical-spec.md)
- Format doc — [`git-notes-audit-format.md`](../docs/git-notes-audit-format.md)
- WWB format (the boundary counterpart) — [`what-was-built-format.md`](../docs/what-was-built-format.md)
- Audit-only content precedent — [ADR-013](adr-013-recommended-autonomous-delivery.md)
- Origin analysis — [`2026-07-18-writ-vs-conductor-analysis.md`](../research/2026-07-18-writ-vs-conductor-analysis.md)
