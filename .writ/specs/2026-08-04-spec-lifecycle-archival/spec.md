# Spec: Spec Lifecycle & Archival

> **Status:** Complete
> **Owner:** @Adam Sellke
> **Created:** 2026-08-04
> **Dependencies:** []
> **Origin:** Ask-mode discussion on whether the growing `.writ/` corpus risks confusing agents; escalated to `/create-spec` after discovery surfaced a live detection bug, not just a hypothetical growth concern.

## Contract (Locked)

**Deliverable:** Fix the broken spec-status detection that undermines `/status` and `create-spec`'s overlap check, then build an evidence-gated archive lifecycle for completed specs — shipped as a Writ product feature so every project using Writ gets it, not just this repo.

**Must include:** The detection fix. Everything else — archiving, indexing exclusion, supersession — depends on correctly knowing which specs are actually Complete, and today that check silently fails for 27 of 39 specs in this repo alone.

**Hardest constraint:** Making archival "free" for the rest of the command suite. Rather than teaching `/status`, `create-spec`, and `implement-spec` to explicitly skip an archive folder, nest it at `.writ/specs/archive/<name>/` — one extra path segment breaks every existing `.writ/specs/*/spec.md` single-level glob for free. Zero changes needed to the commands that already rely on that glob shape.

## Why This Exists

An ask-mode review of whether Writ's ever-growing `.writ/` corpus risks confusing agents found that runtime context loading is already disciplined (`/implement-story` caps fetched context at 21KB, uses role-sliced `spec-lite.md`, never loads the full corpus). But verifying that claim required testing the actual filtering logic commands use to find "the active spec" — and that logic is broken.

`commands/status.md` (and the equivalent prose in `create-spec.md`'s overlap check) filters specs with:

```bash
grep -q "Status: Complete" "$f"
```

Tested against all 39 real spec files in this repo:

| Header format | Count | Matches the grep? |
|---|---:|---|
| `> **Status:** Complete` (bold, modern) | 19 | **No** — `**` sits between `:` and the space, so the literal substring `Status: Complete` never appears |
| `> **Status:** Completed ✅` (bold) | 8 | **No**, same reason |
| `> Status: Complete` (unbold, older) | 8 | Yes |
| `> Status: Closed — Abandoned...` (unbold) | 1 | Partial — matches on "Closed" text depending on exact grep, not reliably |
| No status header at all | 3 | N/A — these are actually Complete per their content but were never given a header |

27 of 39 specs — the majority, and every spec created since the bold-header convention took over around 2026-03-20 — are invisible to this filter. `/status`'s "find the most recently modified non-Complete spec" logic and `create-spec`'s "skip specs with `Status: Complete`" overlap check both only work correctly today by accident, because mtime-sorting usually surfaces genuinely active work first regardless of the broken filter underneath.

This reframes the original question. The risk isn't "the corpus is big and agents get lost in it" — the corpus is small in the parts that matter and runtime loading is already thin. The risk is that the *mechanism meant to distinguish active from historical* silently fails, which would corrupt any archival or retrieval system built on top of it. Fixing detection has to come first.

Separately, `2026-07-26-leanness-instrumentation` already settled that `.writ/` growth is "ceremony cost, not product... reported for trend visibility, never gated." This spec does not reopen that decision. It is about findability and correctness — a spec whose status a machine can trust, and a place for genuinely-done work to live so it stops competing for attention (human or agent) with what's actually in flight — not about reducing bloat to satisfy a leanness gate.

## 🎯 Experience Design (CLI / dogfooding — no user-facing UI)

### Entry Point

`/status --archive` — a new, explicit flag. Running the sweep is a deliberate act, never a side effect of routine `/status`, `/knowledge`, or `create-spec` invocations.

### Happy Path

1. Maintainer runs `/status --archive`.
2. The command re-scans every `.writ/specs/*/spec.md` header using the fixed, format-tolerant detection.
3. For each spec resolving to Complete, it checks whether any `.writ/knowledge/**/*.md` entry's `related_artifacts` frontmatter references that spec's path.
4. Every spec with both signals (Complete + knowledge evidence) is `git mv`'d to `.writ/specs/archive/<original-folder-name>/`, unchanged internally.
5. Each move appends one line to a committed audit ledger: spec name, the knowledge entry/entries that supplied evidence, and a timestamp.
6. Terminal summary: `N specs archived, M Complete specs skipped (no knowledge evidence yet)`.

### Moment of Truth

Running the sweep against this repo's own 39 specs and watching genuinely-done work move out of the active list, with git history, `spec_ref` links from issues, and `Amends:` pointers from ADRs all still resolving correctly afterward.

### Feedback Model

Terminal summary line plus the durable ledger entry. No confirmation prompt per spec — the two-signal eligibility bar (Complete + cited by knowledge) stands in for a human "are you sure," per Business Rule 2 below.

### Error / Edge Experience

| Situation | Behavior |
|---|---|
| Spec is Complete but has no knowledge evidence | Skipped, named in the "skipped" count — never archived, this is not a failure |
| Spec has knowledge evidence but is not Complete | Skipped — status gate is absolute |
| `.writ/specs/archive/` doesn't exist yet | Created on first archive, not at install time |
| A spec folder somehow already exists at the destination path | Hard stop, named collision, no overwrite |
| `git mv` fails (dirty working tree conflict, etc.) | That spec's move is skipped and reported; the sweep continues with the rest rather than aborting entirely |

## 📋 Business Rules

1. **Eligibility = Complete status AND cited by knowledge evidence.** A spec is archive-eligible only if (a) its status resolves to Complete under the fixed, format-tolerant detection, and (b) at least one `.writ/knowledge/` entry's `related_artifacts` list references it. Time in Complete status, alone, is never sufficient — this mirrors the existing "signal-based, not age" principle already established for knowledge-ledger staleness.
2. **Auto-move, not auto-invoke.** "No per-spec confirmation" means the sweep doesn't prompt once it's explicitly run — it does not mean specs get archived as a side effect of unrelated commands. The sweep only ever runs when `/status --archive` is invoked.
3. **Every move is a plain, reversible `git mv`.** No content rewrite, no path-reference rewriting elsewhere. A committed audit ledger (not `.writ/state/`, which is gitignored/ephemeral) records every move with its justifying evidence — satisfying the standing project expectation that automatic actions carry an observable, durable audit trail.
4. **Archived specs stay fully addressable.** Existing inbound references (an issue's `spec_ref`, an ADR's `Amends:` pointer) are not rewritten. Git tracks the rename; the reference still resolves via normal path lookup or `git log --follow`. Rewriting historical pointers project-wide is out of scope.
5. **Nesting is the filtering mechanism.** `.writ/specs/archive/<name>/` is one path segment deeper than `.writ/specs/<name>/`, so every existing single-level glob (`.writ/specs/*/spec.md`) used by `/status`, `create-spec`, `implement-spec` excludes it automatically. No changes to those commands' scanning logic are needed or in scope.
6. **`verify-spec --all` excludes `archive/` by default.** Archived specs were already verified before archiving; a future `--include-archived` flag is explicitly deferred, not built here.
7. **`.cursorindexingignore` ships via `install.sh`**, install-once (same pattern as `.codex/config.toml`), so every Writ project — not just this repo — gets `.writ/specs/archive/` excluded from Cursor semantic search by default.
8. **Status vocabulary detection becomes format-tolerant, not rewritten.** Existing files keep their current spelling (`Complete`, `Completed ✅`, bold or unbold); only the detection regex changes to recognize all current variants. `create-spec.md`'s template canonicalizes spelling for specs created from now on, so drift doesn't reaccumulate.
9. **Supersession gets a real reverse pointer.** The existing ad hoc `Amends:` / `Extends:` header field (already used inconsistently — e.g. `2026-07-26-leanness-instrumentation`) becomes a documented convention, and superseding a spec now also writes `> **Superseded by:** [new-spec]` back onto the superseded spec's header. Today that reverse pointer doesn't reliably exist in either direction.

## Detailed Requirements

### Detection fix

Replace the literal `grep -q "Status: Complete"` in `commands/status.md` with a format-tolerant check that recognizes: bold or unbold `Status:` label, any of `Complete` / `Completed ✅` / `Closed — Abandoned` as complete-family values, and treats a fully absent status header as "not complete" (conservative default — never silently archive something whose status was never declared). Apply the equivalent fix to `create-spec.md`'s Step 1.3b overlap-check prose.

### Knowledge cross-reference check

A spec is "cited by knowledge evidence" if its `spec.md` (or `spec-lite.md`) path — matched by the spec's folder name, since knowledge entries reference paths that may drift in exact form — appears in the `related_artifacts` frontmatter list of at least one file under `.writ/knowledge/{decisions,conventions,glossary,lessons}/`. This reuses existing, already-populated frontmatter; no new fields are introduced anywhere in the knowledge ledger.

### Archive sweep mechanism

New `--archive` flag on `/status`. For each eligible spec: `git mv .writ/specs/<name> .writ/specs/archive/<name>`, then append an entry to `.writ/specs/archive/LEDGER.md` (created on first use) recording the spec name, the knowledge entry filename(s) that supplied evidence, and an ISO timestamp. The ledger is committed to git, not treated as ephemeral state.

### Lifecycle documentation

A new `.writ/docs/spec-lifecycle.md` recording: the canonical status vocabulary, the archive convention and why nesting one level deep is sufficient for existing commands to ignore it, the eligibility rule, and an explicit note for future command authors: **do not add a second, separate exclusion check for `archive/` — the one-level glob already handles it; only add explicit handling if you need to deliberately include archived specs.**

### `.cursorindexingignore` scaffolding

`install.sh`'s `init_writ_workspace` (or an adjacent install-once helper, mirroring `seed_codex_config`'s pattern) creates `.cursorindexingignore` with `.writ/specs/archive/**` if the file doesn't already exist. Never overwrites an existing file — install-once, like `.codex/config.toml`. Applied for the Cursor platform; a no-op (or harmless stray file) for Claude/Codex installs since the file has no effect outside Cursor.

### Supersession banner convention

When `create-spec.md`'s locked contract declares an `Amends:` or `Extends:` relationship to a prior spec (already an existing header convention, used inconsistently), Phase 2 spec generation now also writes `> **Superseded by:** [new-spec-path]` onto the referenced prior spec's header as part of package creation. `edit-spec.md` gets the equivalent manual step documented for cases where supersession is declared after the fact.

## Implementation Approach

Sequenced by dependency, not by story-file order:

1. **Detection fix first** (Story 1) — every other story either depends on correct Complete/non-Complete classification or is independently shippable, but testing the sweep mechanism is meaningless against broken detection.
2. **Knowledge cross-reference + sweep mechanism** (Story 2) build directly on the fix.
3. **Documentation** (Story 3), **`.cursorindexingignore`** (Story 4), and **supersession banners** (Story 5) are independent of each other and of the sweep mechanism's internals — they can proceed in parallel once Story 1 lands.
4. **Dogfood run** (Story 6) depends on Story 2 being complete and is the spec's own validation: run the real sweep against this repo's real 39 specs, not a fixture.

## Success Criteria

1. Format-tolerant detection correctly classifies all 39 current specs in this repo as Complete or not — verified against the audit table in "Why This Exists," not just asserted.
2. Running `/status --archive` against this repo actually archives at least one real spec, proving the mechanism against production data.
3. No regression: `/status`, `create-spec`, `implement-spec`, and `verify-spec` (default, non-`--all`... and `--all` too) all behave correctly with `.writ/specs/archive/` present and populated.
4. `install.sh --dry-run --platform cursor` shows the new `.cursorindexingignore` seeding step.
5. At least one existing spec pair gets a real `Superseded by:` / `Amends:` bidirectional link where one didn't reliably exist before.

## Technical Concerns (surfaced at contract time)

- **Conservative default on missing headers.** The 3 specs with no status header at all are content-complete but will not be auto-archived by this mechanism (they fail the "resolves to Complete" gate by design, per Business Rule 1's conservative bias). They can be backfilled with a status header manually later; that backfill is not required by this spec.
- **`related_artifacts` path matching is approximate.** Knowledge entries may reference a spec by full path, by `spec.md` or `spec-lite.md`, or with slight path drift. The check matches on the spec's folder-name component rather than requiring exact path equality, to avoid false negatives — documented as a known heuristic, not exact-match verification.
- **This is dogfooding-only.** No new command-suite surface beyond one flag on `/status`; no change to `/implement-story`'s context-loading behavior (already verified correct); does not reopen `adr-015`'s or `adr-019`'s warn-only, `.writ`-is-ungated decisions.

## Scope Boundaries

**Included:** status-detection fix (both call sites), archive-sweep mechanism (`/status --archive`) with committed audit ledger, knowledge cross-reference eligibility check, `.writ/docs/spec-lifecycle.md`, `.cursorindexingignore` product-wide scaffolding via `install.sh`, supersession banner convention (`create-spec.md` + `edit-spec.md`), one real dogfooding run against this repo's own specs.

**Excluded, deliberately:**

- **Mass-rewriting existing status text** to one canonical spelling. Detection becomes tolerant instead; only new specs get the canonical form.
- **A new leanness/growth metric.** Already owned by `2026-07-26-leanness-instrumentation` (Business Rule 2: `.writ/` is reported, never gated). Reopening that is out of scope.
- **Rewriting historical cross-references** (issue `spec_ref`, ADR `Amends:` pointers) to point at new archive paths. Git rename tracking is deemed sufficient.
- **Archiving `research/` or `decision-records/`.** Both are small (8 and 19 files respectively), dated, and load-bearing precedent — not the growth problem this spec addresses.
- **`verify-spec --include-archived` flag.** Deferred; `--all` simply excludes `archive/` for now.
- **Live token-usage instrumentation of the archive sweep itself.** Out of scope; this is a file-organization feature, not a context-measurement one.
