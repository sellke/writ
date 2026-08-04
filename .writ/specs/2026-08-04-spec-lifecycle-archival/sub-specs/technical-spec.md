# Technical Spec: Spec Lifecycle & Archival

> Source: `.writ/specs/2026-08-04-spec-lifecycle-archival/spec.md`

## Detection Logic (Story 1)

### Current (broken)

`commands/status.md`:

```bash
ls -t .writ/specs/*/spec.md | while read f; do
  grep -q "Status: Complete" "$f" || { echo "$f"; break; }
done
```

`commands/create-spec.md` Step 1.3b, prose: "Filter out completed specs — read each `spec.md` header and skip specs with `Status: Complete`."

Both rely on the literal substring `Status: Complete`, which does not appear in `> **Status:** Complete` (bold markdown inserts `**` between the colon and the space).

### Fixed detection contract

A spec's header resolves to **complete-family** if its status line — bold or unbold — matches one of: `Complete`, `Completed ✅`, `Closed — Abandoned`/`Closed — Cancelled` (or `Closed` more generally). *(Amended 2026-08-04: this is now also sufficient for archive-eligibility on its own — see spec.md Technical Concerns → Amendment. Original text: "...even though it is not itself archive-eligible per Business Rule 1's requirement for knowledge evidence.")*

Reference implementation shape (illustrative — commands are markdown-instruction files, so the actual deliverable is updated prose/bash in `status.md` and `create-spec.md`, not a shipped script):

```bash
is_complete_family() {
  local f="$1"
  grep -qE '>\s*(\*\*)?Status:(\*\*)?\s*(Complete|Completed|Closed)' "$f"
}
```

A spec with **no** status header at all does **not** match — `is_complete_family` returns false, so it is treated as active/non-complete. This is the conservative default required by Business Rule 1: undeclared status is never silently treated as done.

Both `commands/status.md`'s active-spec detection and `commands/create-spec.md`'s Step 1.3b overlap check are updated to use equivalent logic, described in each file's own prose/bash style.

### Template canonicalization (forward-only)

`commands/create-spec.md` Phase 2 Step 2.4's spec.md template already writes `> **Status:** Not Started` for new specs. No change needed there for the *initial* value. Add a one-line note in the template section confirming the canonical complete-family spelling for when a spec is later marked done: `> **Status:** Complete` (bold, unadorned — no emoji required, though `Completed ✅` remains a recognized synonym for stories, which use a separate convention already: `Completed ✅` per `commands/create-uat-plan.md` line 53 and `commands/implement-story.md` line 219). This spec does not unify story-level and spec-level status vocabulary — that is a separate, out-of-scope concern.

## Archive Eligibility & Sweep (Story 2)

### Eligibility check

> **Amended 2026-08-04.** Eligibility originally required both conditions below (AND). Condition 2 no longer gates — it is still computed and recorded as ledger enrichment. See spec.md → Technical Concerns → Amendment.

A spec at `.writ/specs/<name>/` is archive-eligible when:

1. `is_complete_family(.writ/specs/<name>/spec.md)` is true (Story 1's fixed detection). This is the sole eligibility condition.

Separately (enrichment, not eligibility): at least one file under `.writ/knowledge/{decisions,conventions,glossary,lessons}/*.md` may have a `related_artifacts` frontmatter entry containing the substring `<name>` (the spec's folder-name component — e.g. `2026-07-10-knowledge-consolidation`). This is a folder-name substring match, not exact path equality, to tolerate `related_artifacts` entries written as `.writ/specs/<name>/spec.md`, `.writ/specs/<name>/`, or similar variants. When found, it's recorded on the ledger line; when absent, the ledger line reads `no knowledge evidence yet`.

Reference shape for the cross-reference scan:

```bash
spec_has_knowledge_evidence() {
  local spec_name="$1"  # e.g. 2026-07-10-knowledge-consolidation
  grep -rlE "related_artifacts:" .writ/knowledge/*/*.md 2>/dev/null | \
    xargs -I{} sh -c "awk '/^related_artifacts:/,/^[a-z_]+:/' {} | grep -q \"$spec_name\"" \
    && return 0
  return 1
}
```

(Exact awk/grep incantation is an implementation detail for the coding agent; the contract is: scan `related_artifacts` YAML lists across all four knowledge categories for the spec's folder name.)

### Move mechanism

```bash
mkdir -p .writ/specs/archive
git mv ".writ/specs/${name}" ".writ/specs/archive/${name}"
```

If the destination already exists: hard stop for that spec only, print the collision, continue the sweep for remaining specs. If `git mv` fails for any other reason (dirty tree, permissions): skip that spec, report the failure reason, continue the sweep.

### Audit ledger

`.writ/specs/archive/LEDGER.md`, created on first archive if absent, committed to git (not `.writ/state/`). One line appended per archived spec:

```markdown
- 2026-08-04T15:32:00Z — `2026-07-10-knowledge-consolidation` archived (evidence: `.writ/knowledge/lessons/2026-07-19-...md`)
```

### Idempotency

Since the sweep re-scans `.writ/specs/*/spec.md` (single-level glob) each run, a spec already moved to `.writ/specs/archive/<name>/` no longer appears in that glob's results at all — the second run simply never considers it. No separate "already archived" tracking is needed; the move itself is the idempotency mechanism.

### Why nesting makes this free elsewhere

Every existing scan in the command suite uses a single-level glob: `.writ/specs/*/spec.md`. A path like `.writ/specs/archive/<name>/spec.md` has **two** segments after `specs/`, so it never matches `*/spec.md` (which expects exactly one). This is true for:

- `commands/status.md`'s `ls -t .writ/specs/*/spec.md`
- `commands/create-spec.md`'s Step 1.3b overlap scan
- `commands/implement-spec.md`'s spec-selection listing

No code changes are needed in any of these three files for archive exclusion — verify this holds (Story 3) rather than re-implementing it.

## `verify-spec --all` (Story 3)

`commands/verify-spec.md`'s `--all` flag must be checked against its actual folder-enumeration logic. If it uses a single-level glob like the others, it already excludes `archive/` for free — document this. If it recurses more broadly (e.g. `find .writ/specs -name spec.md`, which *would* descend into `archive/`), add the minimal explicit exclusion (`-path '*/archive/*' -prune -o ...` or equivalent) so `--all` skips `archive/` by default. A future `--include-archived` flag to opt back in is out of scope — do not build it.

## `.cursorindexingignore` (Story 4)

New install-once helper in `scripts/install.sh`, mirroring `seed_codex_config()`:

```bash
seed_cursorindexingignore() {
  local op="${1:-apply}"
  local dest=".cursorindexingignore"
  if [ -f "$dest" ]; then
    [ "$op" = "preview" ] && echo "    Would preserve: .cursorindexingignore (already exists; install-once)"
    [ "$op" = "apply" ] && echo "    ⚡ Preserved: .cursorindexingignore (install-once)"
    return 0
  fi
  [ "$op" = "preview" ] && { echo "    Would seed: .cursorindexingignore (first install)"; return 0; }
  printf '%s\n' '.writ/specs/archive/**' > "$dest"
  echo "    ✨ Seeded: .cursorindexingignore"
}
```

Wired into the existing `--dry-run` preview pass and the apply pass, for the Cursor platform at minimum (implementer's call on whether to also seed for Claude/Codex platforms, since the file is inert there — document the decision either way).

This repo's own root `.cursorindexingignore` (currently absent) is created as a direct, manual step in this story — this repo does not run `install.sh` on itself (symlinked dev install per `.writ/docs/self-dogfooding.md`).

## Supersession Banners (Story 5)

When `create-spec.md`'s locked contract declares `Amends:` or `Extends:` pointing at an existing spec, Phase 2 (after the new spec's `spec.md` is written) also writes back to the **referenced** spec's header:

```
> **Superseded by:** [`<new-spec-name>`](../<new-spec-folder>/spec.md)
```

inserted as a new line in the existing header metadata block (alongside `Status`, `Owner`, `Created`, etc.), never replacing the `Status:` line itself — a superseded spec's status field still records its own terminal state (`Complete`, `Closed — Abandoned`, etc.) independently of the fact that something else now supersedes it.

`commands/edit-spec.md` gets the equivalent manual instruction: when an edit declares that the edited spec now supersedes another, write the same `Superseded by:` line onto the older spec.

## Dogfood Run (Story 6)

Executed against this repo's real 39 specs, not a fixture, after Story 2 lands:

1. Run `/status --archive` (or the direct equivalent bash) against this repo.
2. Confirm at least one real spec moves.
3. Spot-check: does the moved spec's folder still resolve via `git log --follow`? Does any issue's `spec_ref` or ADR `Amends:` pointer referencing it still make sense (even though the path text itself isn't rewritten)?
4. Confirm `/status`, `create-spec`'s overlap check, and `implement-spec`'s spec listing all still behave correctly with `.writ/specs/archive/` populated.
5. Record results in the story's own "What Was Built" section — this is the spec's own acceptance evidence for Success Criterion 2.

## Testing Strategy

- **Story 1:** Fixture spec.md files covering all 5 real-world header variants (bold Complete, bold Completed ✅, unbold Complete, Closed — Abandoned, no header) — assert correct classification for each.
- **Story 2:** Fixture `.writ/knowledge/` entries with and without matching `related_artifacts`; fixture specs Complete/not-Complete crossed with evidence/no-evidence (2×2); collision and git-mv-failure simulation.
- **Story 3:** Fixture `.writ/specs/archive/<name>/spec.md` present — assert `verify-spec --all` does not visit it (or does, if intentionally testing `--include-archived` were in scope, which it is not).
- **Story 4:** `install.sh --dry-run` output assertion (first run vs. re-run with file already present).
- **Story 5:** Round-trip test — declare Amends in a fixture contract, assert the referenced spec's header gains the `Superseded by:` line.
- **Story 6:** Not unit-testable in the traditional sense — its "test" is the real dogfooding run itself, captured as evidence in the story file.

## Non-Goals (restated from spec.md Scope Boundaries)

No mass rewrite of existing status text. No new leanness metric. No rewriting of historical cross-references. No archiving of `research/` or `decision-records/`. No `verify-spec --include-archived` flag. No token-usage instrumentation of the sweep itself.
