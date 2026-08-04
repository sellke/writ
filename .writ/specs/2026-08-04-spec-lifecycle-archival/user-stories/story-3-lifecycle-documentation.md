# Story 3: Lifecycle Documentation

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** future Writ contributor or AI agent working in this codebase
**I want to** a durable `.writ/docs/spec-lifecycle.md` that records the canonical status vocabulary, archive path convention, two-signal eligibility rule, and the single-level-glob exclusion invariant — plus confirmation that `verify-spec --all` and existing backup artifacts behave correctly under that convention
**So that** I can implement or extend spec-lifecycle features without re-deriving the design from scattered command prose, and so no one accidentally adds redundant `archive/` exclusion checks (or breaks archive exclusion by switching to recursive globs)

## Acceptance Criteria

- [ ] Given the locked spec contract in `spec.md` → `## Detailed Requirements` → `### Lifecycle documentation` and Business Rules 5–6, when `.writ/docs/spec-lifecycle.md` is created, then it includes all required sections: **canonical status vocabulary** (which values count as complete-family for detection), **archive convention** (`.writ/specs/archive/<name>/`) with an explanation of *why* one extra path segment is sufficient for every existing single-level glob to ignore archived specs automatically, the **two-signal eligibility rule** (Complete status AND knowledge evidence), and a **prominent author note** stating: *"Do not add a second, separate exclusion check for `archive/` anywhere — the one-level-deeper glob already handles it; only add explicit handling if a command deliberately needs to INCLUDE archived specs (e.g. a future `--include-archived` flag)."*
- [ ] Given `commands/verify-spec.md` Step 1.1's `--all` enumeration (`.writ/specs/*/` folders containing `spec.md`), when audited against a fixture layout that includes both active specs and `.writ/specs/archive/<name>/spec.md`, then archived specs are **excluded by default** without any explicit `archive/` filter — and if any check within `verify-spec.md` uses a recursive `**` glob under `.writ/specs/` that would *include* archive contents, this story adds the **minimal explicit exclusion** needed so `--all` skips `archive/` by default (a future `--include-archived` flag is explicitly out of scope).
- [ ] Given the three existing `spec-lite.md` files under `backups/` subfolders (`.writ/specs/2026-07-10-model-tier-delegation/backups/…`, `.writ/specs/2026-02-27-phase1-foundation/backups/…`, `.writ/specs/2026-04-24-phase4-production-grade-substrate/backups/…` — artifacts of `/edit-spec`'s backup mechanism), when the doc records the **backups/ invariant**, then it states — with evidence, not assertion — that single-level globs (`.writ/specs/*/spec.md`, `.writ/specs/*/spec-lite.md`) do **not** match nested `backups/<timestamp>/spec-lite.md` paths, and no code change is required for that behavior.
- [ ] Given the new doc ships as a Writ product convention (not dogfood-only), when cross-links are added, then at minimum `spec.md` → `## Detailed Requirements` → `### Lifecycle documentation` references `.writ/docs/spec-lifecycle.md`, and `commands/verify-spec.md` Step 1.1 `--all` prose links to the doc's archive-exclusion section — so future command authors encounter the guidance at the point of editing scanning logic.
- [ ] Given an automated guard is feasible without building new product surface, when verification runs, then either an `eval.sh` static assertion or a small pytest fixture confirms that `verify-spec.md`'s `--all` folder enumeration uses a single-segment glob (`.writ/specs/*/`) and does not recurse into `.writ/specs/archive/**` — preventing silent regression if someone "fixes" what looks like a missing exclusion.

## Implementation Tasks

- [ ] 3.1 Read existing convention docs (`.writ/docs/self-dogfooding.md`, `.writ/docs/context-hint-format.md`, `.writ/docs/leanness-audit-format.md`) and mirror their tone: purpose blurb at top, structured sections, tables where helpful, cross-links to ADRs/specs where relevant.
- [ ] 3.2 Draft `.writ/docs/spec-lifecycle.md` covering: (a) complete-family status vocabulary and format-tolerant detection intent (reference Story 1 without duplicating its implementation), (b) archive path layout and the glob mechanics table showing why `.writ/specs/*/spec.md` excludes both `archive/<name>/` and `<name>/backups/<timestamp>/`, (c) two-signal archive eligibility (Complete + knowledge `related_artifacts` citation), (d) the prominent "do not add redundant archive/ exclusion" author note, (e) confirmed invariants for `backups/` spec-lite artifacts.
- [ ] 3.3 Audit `commands/verify-spec.md` end-to-end for every `.writ/specs/` enumeration — Step 1.1 `--all` (line ~35), Check 8 owner scan (line ~347), Check P4 evidence table (line ~556), and any other folder-walking prose. Record findings: single-level `*` globs naturally exclude archive; flag any `**` or unqualified recursive walk that would pull in `.writ/specs/archive/<name>/`.
- [ ] 3.4 Write a failing-then-passing verification fixture: create a disposable temp layout with `.writ/specs/active-spec/spec.md` and `.writ/specs/archive/archived-spec/spec.md`, then assert the `--all` enumeration contract (single-level glob + "contains spec.md" filter) yields only the active spec. If audit finds a recursive walk, apply the minimal fix to `verify-spec.md` (e.g. explicit `archive/` skip or tighten glob) and update the fixture expectations accordingly.
- [ ] 3.5 Document the `backups/` invariant with concrete evidence: list the three real paths, show that `.writ/specs/*/spec-lite.md` does not match them (one-level `*` stops at the spec folder name), and note this is unchanged by archival — no `/edit-spec` or backup mechanism changes in scope.
- [ ] 3.6 Add cross-links: from this spec's `spec.md` lifecycle section → the new doc; from `commands/verify-spec.md` `--all` prose → the doc's archive-exclusion subsection; optionally a one-line pointer in `AGENTS.md` under Repository Structure or Key Design Decisions so Codex/Claude agents discover it.
- [ ] 3.7 Run verification: read the finished doc against all acceptance criteria, execute the fixture/eval guard, and confirm no unintended changes to `/edit-spec` backup behavior or other commands beyond any minimal `verify-spec.md` fix identified in 3.3–3.4.

## Notes

**Independent of Stories 1 and 2.** This story documents a convention already locked in the spec contract. It does not require the detection fix or archive sweep to ship first, but the doc must describe the *real* mechanism accurately (format-tolerant complete-family detection, knowledge cross-reference, `git mv` to `.writ/specs/archive/<name>/`). If Story 1's canonical vocabulary differs slightly from today's drift, the doc should describe the target state per Business Rule 8, not today's broken grep.

**Parallel with Story 2.** Documentation can proceed while the sweep mechanism is built; coordinate only on path names (`archive/`, `LEDGER.md`) so the doc matches Story 2's implementation.

**verify-spec --all is the one risky call site.** Most commands already use `.writ/specs/*/spec.md` (e.g. `status.md` lines 78/334, `create-spec.md` overlap check). Step 1.1 `--all` uses the same single-segment shape (`.writ/specs/*/`). Check 8's prose ("For each `spec.md` under `.writ/specs/`") is ambiguous — verify whether it runs per selected spec folder or walks recursively; if recursive, that is the fix target for this story.

**Risks:**

- Future contributors may not read `.writ/docs/` — cross-links at edit points (`verify-spec.md`, `create-spec.md` for new commands) matter more than doc completeness alone.
- Someone may "helpfully" add explicit `grep -v archive` filters everywhere, creating dual maintenance and hiding the real invariant (glob depth). The prominent author note exists specifically to prevent this.
- A well-intentioned switch from `*` to `**` in any command would silently break archive exclusion — the eval/fixture guard in task 3.4 mitigates this for `verify-spec`.

**Out of scope:** `--include-archived` flag, changes to `/edit-spec` backup behavior, `.cursorindexingignore` (Story 4), supersession banners (Story 5), running the actual archive sweep (Story 6).

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** []
- **Business rules:** [Nesting is the filtering mechanism (.writ/specs/archive/<name>/ breaks single-level globs), verify-spec --all excludes archive/ by default]
- **Experience:** []

Reference: `.writ/docs/context-hint-format.md` — read `spec.md` directly for full contract text at `## 📋 Business Rules` (items 5–6), `## Detailed Requirements` → `### Lifecycle documentation`, and `## Technical Concerns` (backup spec-lite note).
