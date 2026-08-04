# Spec Lifecycle & Archival (Lite)

> Source: .writ/specs/2026-08-04-spec-lifecycle-archival/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Fix broken spec-status detection (`grep -q "Status: Complete"` fails to match `**Status:** Complete` — 27/39 specs misclassified), then build an evidence-gated archive sweep.

**Implementation Approach:**
- Detection fix first (Story 1) — everything else depends on it.
- Archive path: `.writ/specs/archive/<name>/` — one glob level deeper than `.writ/specs/*/spec.md`, so existing commands auto-exclude it. Do not add explicit archive-skip logic elsewhere.
- Eligibility: Complete status AND spec's folder name found in some `.writ/knowledge/**/*.md` `related_artifacts` frontmatter.
- Move = plain `git mv`, no content rewrite, no rewriting of historical cross-references.

**Files in Scope:**
- `commands/status.md` — fix grep, add `--archive` flag
- `commands/create-spec.md` — fix overlap-check grep; add Superseded-by writeback on Amends/Extends
- `commands/edit-spec.md` — manual Superseded-by step
- `commands/verify-spec.md` — confirm `--all` excludes `archive/`
- `scripts/install.sh` — install-once `.cursorindexingignore` seeding
- `.writ/docs/spec-lifecycle.md` — new doc
- `.writ/specs/archive/LEDGER.md` — new, committed audit trail (created on first archive)

**Error Handling:**
- Missing status header → treated as not-Complete (conservative, never auto-archived)
- `git mv` collision at destination → hard stop, name the collision, skip only that spec
- `git mv` failure (dirty tree, etc.) → skip that spec, report, continue sweep

**Integration Points:** `/status --archive` is the only new invocation surface. No changes to `/implement-story` context loading (already verified correct).

---

## For Review Agents

**Acceptance Criteria:**
1. Format-tolerant detection classifies all 39 real specs correctly (bold/unbold `Status:`, `Complete`/`Completed ✅`/`Closed — Abandoned`, absent header → not-Complete).
2. `/status --archive` moves ≥1 real spec in this repo via `git mv`, writes a `LEDGER.md` entry with justifying evidence.
3. `/status`, `create-spec`, `implement-spec`, `verify-spec` (incl. `--all`) all behave correctly with `archive/` present.
4. `install.sh --dry-run --platform cursor` shows `.cursorindexingignore` seeding.
5. ≥1 real spec pair gets a working bidirectional `Superseded by:` / `Amends:` link.

**Business Rules:**
- Eligibility requires BOTH signals (Complete + knowledge evidence) — never time alone.
- Auto-move only within an explicit `/status --archive` invocation — never a side effect of other commands.
- Archive nesting is the sole filtering mechanism — no parallel exclusion lists.
- `.writ/` growth stays ungated (per `2026-07-26-leanness-instrumentation` Rule 2) — this spec is about findability/correctness, not bloat reduction.

**Experience Design:**
- Entry: `/status --archive`
- Happy path: scan → cross-reference knowledge → git mv eligible specs → append ledger line → print summary
- Moment of truth: real sweep against this repo's 39 specs, all references still resolve after
- Feedback: terminal summary (`N archived, M skipped`) + committed ledger entry
- No confirmation prompt: two-signal eligibility bar substitutes for per-item confirmation

---

## For Testing Agents

**Success Criteria:**
1. Detection regex passes against all 5 header-format variants found in this repo's real files (see spec.md audit table).
2. Sweep is idempotent — running twice doesn't re-move or duplicate ledger entries.
3. Archived specs remain fully readable/addressable via normal path lookup post-move.

**Shadow Paths to Verify:**
- **Happy path:** Complete + evidenced spec → archived, ledger entry written.
- **Nil input:** No specs exist yet → sweep no-ops cleanly.
- **Empty input:** No specs are Complete → `0 archived, 0 skipped`.
- **Upstream error:** `git mv` fails mid-sweep → that spec skipped and reported, sweep continues for remaining specs.

**Edge Cases:**
- Spec Complete but zero knowledge references → skipped (correct, not a bug).
- Spec referenced by knowledge but not Complete → skipped (status gate absolute).
- Destination path collision → hard stop for that spec only, named in output.

**Coverage Requirements:**
- New code: ≥80%
- Detection regex: 100% (all 5 real-world variants)
- Error paths (collision, git mv failure): 100%
