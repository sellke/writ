# Spec Lifecycle & Archival

> This document records the canonical status vocabulary, the archive path convention, the two-signal archive eligibility rule, and the glob-depth invariant that makes archival "free" for the rest of the command suite. See [`2026-08-04-spec-lifecycle-archival`](../specs/2026-08-04-spec-lifecycle-archival/spec.md) for the full contract this doc implements, and [Supersession Banners](#supersession-banners) below for the `Amends:` / `Extends:` / `Superseded by:` convention.

## Canonical Status Vocabulary

Every spec's header declares a status line — bold or unbold — inside its leading `>`-blockquote metadata block:

```markdown
> **Status:** Not Started
> **Status:** In Progress
> **Status:** Complete
```

**Complete-family values** (any of these resolve as "done" for scanning purposes):

| Value | Notes |
|---|---|
| `Complete` | Canonical spelling for **new** specs going forward (Business Rule 8) |
| `Completed ✅` | Legacy synonym, still recognized — matches the story-level convention used by `create-uat-plan.md` and `implement-story.md` |
| `Closed — Abandoned` | Terminal-but-never-shipped state; complete-family for *scanning* purposes (excluded from "active"), but archiving still requires knowledge evidence like any other complete-family spec (see [Two-Signal Eligibility](#two-signal-archive-eligibility) below) |

**Detection is format-tolerant, not rewritten.** [`scripts/spec-status.py`](../../scripts/spec-status.py) is the single executable source of truth: it recognizes bold (`> **Status:** ...`) and unbold (`> Status: ...`) labels and matches any value starting with `Complete` or `Closed` (trailing parenthetical text, dates, or emoji are ignored). Existing spec files are **never mass-rewritten** to a single spelling — only the detector became tolerant. New specs created by `/create-spec` canonicalize to the bold, unadorned `> **Status:** Complete` form when later marked done, so spelling drift does not reaccumulate (Business Rule 8).

**A missing status header conservatively resolves not-complete.** If a spec's leading metadata block has no status line at all, it is *never* silently treated as done — undeclared status must never be inferred from body content. This is intentional and by design (spec.md → Technical Concerns): a headerless spec is content-complete but stays out of the complete-family class until a human adds a status header.

**Why this mattered:** the literal substring check `grep -q "Status: Complete"` never matches `> **Status:** Complete` — bold markdown inserts `**` between the colon and the space. This silently misclassified 27 of 39 real specs in this repo before the fix (`2026-08-04-spec-lifecycle-archival` Story 1). Consult that spec's audit table if you need historical detail; this doc only records the corrected target state.

## Archive Convention

Archived specs live at:

```
.writ/specs/archive/<original-folder-name>/
```

— **one path segment deeper** than an active spec (`.writ/specs/<name>/`). Nothing about the spec's internal content changes on archival; it is a plain `git mv`, fully reversible, with git rename tracking preserved (`git log --follow` resolves history at the new path).

### Why one extra path segment is sufficient

Every existing spec-enumeration call site in the command suite uses a **single-level glob**: `.writ/specs/*/spec.md`. A single-level glob matches exactly one path segment between `specs/` and `spec.md`. An archived spec's path — `.writ/specs/archive/<name>/spec.md` — has **two** segments there, so it can never match `*/spec.md`.

| Call site | Glob shape | Matches `archive/<name>/spec.md`? |
|---|---|---|
| `commands/status.md` — active-spec detection (`ls -t .writ/specs/*/spec.md`) | single-level | No |
| `commands/create-spec.md` — Step 1.3b overlap-check spec listing | single-level | No |
| `commands/implement-spec.md` — spec-selection listing | single-level | No |
| `commands/verify-spec.md` — `--all` folder enumeration (`.writ/specs/*/`) | single-level | No |
| `scripts/spec-status.py` — `scan --specs-dir` (`specs_dir.glob("*/spec.md")`) | single-level | No |
| `scripts/archive-sweep.py` — eligibility scan (delegates to `spec-status.py`) | single-level | No |

**This is deliberate, not incidental.** The glob depth *is* the exclusion mechanism. No command in the list above contains a separate, explicit `archive/` skip check — none is needed.

> **⚠️ Do not add a second, separate exclusion check for `archive/` anywhere.** The one-level-deeper glob already handles it for every present and future single-level-glob call site. Only add explicit handling if a command deliberately needs to **include** archived specs (e.g. a hypothetical future `--include-archived` flag on `/verify-spec` — deferred, not built, per Business Rule 6). If you find yourself writing `grep -v archive` or `-path '*/archive/*' -prune`, stop: either the call site already uses a single-level glob (no fix needed) or it uses a recursive glob and the *narrowest* fix is to tighten it back to single-level, not bolt on a parallel filter.

### The `backups/` invariant (a second, pre-existing case of the same mechanism)

`/edit-spec`'s backup mechanism writes snapshots to `.writ/specs/<name>/backups/<timestamp>/spec-lite.md` (and similar). This repo has three real examples:

```
.writ/specs/2026-07-10-model-tier-delegation/backups/20260718-105002/spec-lite.md
.writ/specs/2026-02-27-phase1-foundation/backups/2026-03-14T00-00-00/spec-lite.md
.writ/specs/2026-04-24-phase4-production-grade-substrate/backups/2026-04-26-edit-spec/spec-lite.md
```

A single-level glob `.writ/specs/*/spec-lite.md` stops at the spec folder name and does **not** descend into `backups/<timestamp>/spec-lite.md` — the same depth-based exclusion that keeps `archive/` invisible to routine scans keeps `backups/` invisible too. No code change was required for this; it was already true before this spec existed. `/edit-spec`'s backup behavior is unchanged by archival.

## Two-Signal Archive Eligibility

A spec is **archive-eligible** only when **both** signals hold:

1. **Status resolves to complete-family** under the format-tolerant detector above.
2. **At least one `.writ/knowledge/{decisions,conventions,glossary,lessons}/*.md` entry's `related_artifacts` frontmatter references the spec's folder name** (substring match on the folder-name component, e.g. `2026-07-10-knowledge-consolidation` — tolerant of `related_artifacts` entries written as a full path, `spec.md`, `spec-lite.md`, or a bare folder reference; documented as a known heuristic, not exact-path verification).

**Time in Complete status, alone, is never sufficient.** This mirrors the existing "signal-based, not age-based" principle already established for knowledge-ledger staleness (see `2026-07-10-knowledge-consolidation`). A spec can sit in `Complete` status indefinitely without being archived if nothing in the knowledge ledger cites it yet — that is correct behavior, not a bug, and is reported as a "skipped (no knowledge evidence yet)" count rather than a failure.

**The status gate is absolute.** A spec cited by knowledge evidence but not yet Complete is never archived regardless of citation count.

The mechanism (`scripts/archive-sweep.py`, invoked via `/status --archive`) is a plain, reversible `git mv` per eligible spec, with one line appended to the committed `.writ/specs/archive/LEDGER.md` per move (spec name, citing knowledge filename(s), ISO 8601 timestamp). See `commands/status.md` → `### Archive Sweep (--archive)` for the full invocation contract.

## `verify-spec --all` and Archive Exclusion

`commands/verify-spec.md` Step 1.1's `--all` enumeration builds its spec list from `.writ/specs/*/` — a single-level glob, identical in shape to every other call site in the table above. **No code change was required in `verify-spec.md` for this spec** — the exclusion was already correct by construction; this section exists to document and guard that fact, not to introduce new behavior.

Audited call sites within `verify-spec.md`:

| Location | Shape | Archive-safe? |
|---|---|---|
| Step 1.1 `--all` folder resolution (`.writ/specs/*/`) | single-level | Yes — by construction |
| Check 8 (owner field presence, "for each `spec.md` under `.writ/specs/`") | operates on the already-resolved Step 1.1/1.2 list, not an independent recursive walk | Yes — inherits Step 1.1's exclusion |
| Check P4 evidence table (`.writ/specs/*/`) | single-level | Yes — by construction |

A future `--include-archived` flag to deliberately opt back in is explicitly **deferred** (Business Rule 6) — `--all` simply excludes `archive/` by default today, and that is the complete scope of this concern.

## Supersession Banners

When one spec's locked contract declares that it **replaces** or **builds on** an existing spec, that relationship gets a header field on the *new* spec, and — as of this spec — a matching reverse pointer written back onto the *older* spec.

### Forward pointers (declared by the new spec's author)

| Field | Semantics |
|---|---|
| `> **Amends:** [older-spec](../older-spec/spec.md)` | The new spec **supersedes/replaces** the older spec's work. The older spec becomes historical; readers should treat the new spec as canonical going forward. |
| `> **Extends:** [older-spec](../older-spec/spec.md)` | The new spec **builds on** the older spec without fully replacing it. Both remain independently relevant — consistent with existing ADR usage of `Extends:` (see ADR-014, ADR-015, ADR-019). |

Both fields may also point at an ADR rather than a spec (e.g. `2026-07-26-leanness-instrumentation`'s `> **Amends:** [...] / [ADR-015]`). Reverse-pointer write-back applies only to resolvable `.writ/specs/<folder>/spec.md` targets — ADR references are forward-only, with no reverse write-back into the ADR.

### Reverse pointer (written back onto the older spec)

When `/create-spec` (Phase 2, after the new spec's `spec.md` is written) or `/edit-spec` (when a modification adds/changes an `Amends:`/`Extends:` relationship) detects a resolvable `Amends:` or `Extends:` reference, it writes:

```markdown
> **Superseded by:** [new-spec-name](../new-spec-folder/spec.md)
```

onto the **referenced (older)** spec's header — inserted as a new line in the existing metadata block, alongside `Status`, `Owner`, `Created`, etc. **The older spec's own `Status:` line is never replaced or rewritten** — a superseded spec keeps recording its own terminal state (`Complete`, `Closed — Abandoned`, etc.) independently of the fact that something else now supersedes it. Both fields legitimately coexist:

```markdown
> **Status:** Complete
> **Superseded by:** [2026-07-26-leanness-instrumentation](../2026-07-26-leanness-instrumentation/spec.md)
```

**Malformed or unresolvable references fail gracefully.** A broken relative path, a missing spec folder, or an absent header block on the referenced file logs a clear warning and skips the write-back — it never corrupts the referenced spec's header or body, and never blocks the new spec's own package creation.

**Why this matters:** before this convention, the ad hoc `Amends:`/`Extends:` field existed but was used inconsistently, and the reverse pointer didn't reliably exist in either direction — a reader landing on a superseded spec had no signal that something newer had replaced it. See `2026-07-11-leanness-guardian` → `2026-07-26-leanness-instrumentation` for the retroactive proof pair.

## Quick Reference for Future Command Authors

- **Enumerating specs?** Use `.writ/specs/*/spec.md` (or `.writ/specs/*/`) — single segment, never `**`. You get archive exclusion for free.
- **Classifying a spec's status?** Call `scripts/spec-status.py is-complete --file <path>` (or `scan --specs-dir <dir>`) — don't hand-roll a substring grep.
- **Checking archive eligibility?** Call `scripts/archive-sweep.py scan --specs-dir <dir> --knowledge-dir <dir>` — don't reimplement the two-signal check.
- **Tempted to add `grep -v archive` or a `-prune` clause?** Stop and re-read [Why one extra path segment is sufficient](#why-one-extra-path-segment-is-sufficient) above. You almost certainly don't need it.
