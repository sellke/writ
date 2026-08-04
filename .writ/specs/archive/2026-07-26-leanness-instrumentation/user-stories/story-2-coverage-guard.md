# Story 2: Coverage Guard — Hard-FAIL on Unmeasured Surface

> **Status:** Completed ✅ (2026-07-26)
> **Priority:** High
> **Dependencies:** Story 1

## User Story

As a **Writ maintainer relying on eval Tier 1 to tell the truth about product weight**, I want **the leanness tripwire to hard-FAIL when any top-level repo entry is neither in the gated product registry nor explicitly declared out of scope**, so that **the next directory someone adds cannot silently fall outside the frame the way `scripts/` did across two audit cycles.**

## Acceptance Criteria

- [x] **Given** this repo with the Story 1 gated registry in place, **when** `python3 scripts/eval-leanness.py` runs after metrics are computed, **then** every top-level entry resolves to either a registry surface or the explicit `out_of_scope` list, and the guard contributes zero structural findings.
- [x] **Given** a temp-dir fixture with a synthetic top-level directory that appears in neither the registry nor `out_of_scope`, **when** the check runs, **then** `structural` contains exactly one finding with `{"subject", "what", "fix"}` shape naming the path and offering both remedies — add a measurement rule or declare it out of scope.
- [x] **Given** a registry entry whose path no longer exists on disk, **when** the check runs, **then** a separate structural finding reports the stale registry entry, naming the missing path and the fix to remove or restore it.
- [x] **Given** declared out-of-scope paths (`.git`, `.writ`, `archive`, `test`, `node_modules`, dotfiles, `README.md`, `CHANGELOG.md`, `LICENSE`, `VERSION`, `package.json`, and similar non-product root files) and every gated registry path, **when** the check runs, **then** none of them produce coverage-guard structural findings.
- [x] **Given** any coverage-guard structural finding, **when** `bash scripts/eval.sh --check=leanness` runs, **then** the Python helper still exits 0, `eval.sh` increments the finding count, and the run FAILs — growth warnings remain warn-only and this story does not promote weight increase to hard-FAIL.

## Implementation Tasks

- [x] 2.1 Extend `scripts/tests/test_eval_leanness.sh` first with failing coverage-guard cases: a temp-dir fixture built on the Story 1 registry that adds a synthetic undeclared top-level directory (expect structural finding), deletes a registry path from disk (expect stale-registry finding), and asserts out-of-scope and dot-prefixed entries stay silent.
- [x] 2.2 Add an explicit `OUT_OF_SCOPE` declaration list beside the Story 1 registry in `scripts/eval-leanness.py` — enumerate non-product top-level paths (`.git`, `.writ`, `archive`, `test`, `node_modules`, dotfiles, `README.md`, `CHANGELOG.md`, `LICENSE`, `VERSION`, `package.json`, and similar) with a comment that growth in the list is itself a leanness signal, mirroring `INFRA_PREFIXES`.
- [x] 2.3 Implement `check_coverage(root)` following the `check_parity()` pattern: after metrics, enumerate top-level entries via `os.scandir`, subtract the union of gated registry paths and `OUT_OF_SCOPE`, and emit one structural finding per unaccounted entry using the `{"subject", "what", "fix"}` dict shape.
- [x] 2.4 Add the stale-registry pass inside `check_coverage()` — every gated registry path must exist on disk; a missing path emits its own structural finding distinguishable from the undeclared-entry case.
- [x] 2.5 Wire `check_coverage()` into `main()` so its findings join the existing `structural` list alongside `check_parity()` and baseline checks, preserving the always-exit-0 JSON envelope contract.
- [x] 2.6 Confirm the real repo resolves every top-level entry with zero coverage findings and that no new hard-FAIL paths were introduced for growth — unjustified weight increase still warns only.
- [x] 2.7 Verify acceptance criteria and the full suite pass: `bash scripts/tests/test_eval_leanness.sh`, `bash scripts/eval.sh --check=leanness` with `Findings: 0` on this repo.

## Notes

- **Anti-recurrence, not a one-time widening.** Story 1 adds `scripts/` to the measured surface and fixes today's 32% blind spot. This story is the reason the spec exists in this shape: it makes the *next* blind spot impossible. The failure mode that persisted across the 2026-07-11 and 2026-07-18 audits was not a broken script — it was an undeclared surface outside the frame.
- **Only unmeasured surface gains teeth.** ADR-015 deliberately rejected hard-FAILING on weight growth (Alternative B). Do not reopen that decision. Coverage findings are the sole new structural source; ratchet warnings belong to Story 4.
- **Enumerate loose root files; do not blanket-exempt them.** A rule like "any top-level regular file is out of scope" would reintroduce the blind spot — a future root-level product markdown file would never be measured. Prefer an explicit list and accept the one-line cost per new root file as the mechanism.
- **Dot-prefix rule covers scratch directories.** Worktree lanes (`.writ-lanes-*`), VCS metadata (`.git`), and platform install dirs (`.cursor`, `.claude`, `.codex`) must match any leading-dot name, not a literal `.writ` string alone.
- **Integration point.** Story 1 owns the gated registry; this story reads it and adds `OUT_OF_SCOPE` beside it. Nested paths inside a measured surface (e.g. `scripts/tests/`) are accounted for by their parent registry entry — the guard operates at repo root only.
- **Risk — local scratch at root.** An untracked top-level directory hard-FAILs a local eval run. That is correct behavior (the finding names the fix); if noise becomes a problem, the narrowest remedy is skipping git-ignored entries, not loosening the declaration requirement.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] `scripts/tests/test_eval_leanness.sh` passes, including the new coverage-guard scenarios
- [x] Real-repo run resolves 100% of top-level entries with `Findings: 0`
- [x] Code reviewed

## Context for Agents

- **Business rules:** `spec.md → ## 📋 Business Rules` → [Rule 1 (product surface is an explicit registry, gated), Rule 4 (only unmeasured surface hard-fails — growth stays warn-only; do not reopen ADR-015 Alternative B), Rule 5 (the guardian measures itself; no self-exemption), Rule 6 (dogfooding-only — no `commands/*.md` changes)].
- **Experience:** `spec.md → ## 🎯 Experience Design → ### Error Experience` (structural finding names path and offers "add a rule or declare it out of scope"); `spec.md → ## 🎯 Experience Design → ### Feedback Model` (findings fail the run via `eval.sh`; warnings and metrics never touch the findings counter).
- **Error map rows:** `spec.md → ## 🎯 Experience Design → ### Error Experience` → [Top-level product path with no measurement rule (structural), A measured path exists in the registry but not on disk (structural)]. Do not implement baseline-missing or growth rows here — those are existing or Story 4 scope.
- **Shadow paths:** `spec.md → ## Detailed Requirements → ### Coverage guard` (enumerate top-level entries, subtract registry ∪ `out_of_scope`, anything unaccounted → structural); `spec.md → ## Scope Boundaries → **Excluded, deliberately:**` → [Reopening ADR-015's warn-only decision for growth].
- **Files in scope:** `scripts/eval-leanness.py`, `scripts/tests/test_eval_leanness.sh`.
- **Pattern reference:** `check_parity()` in `scripts/eval-leanness.py` — same `{"subject", "what", "fix"}` finding dict shape and list-return contract.
- **Dependency:** Story 1's gated registry supplies the declared-surface half of the union this guard subtracts from.
- **Not yet available:** `sub-specs/technical-spec.md` does not exist for this spec — index into `spec.md` directly.

> Note: by implementation time, `sub-specs/technical-spec.md` existed (authored
> alongside the spec) and was used as the primary source for the `OUT_OF_SCOPE`
> list and the coverage-guard algorithm; `spec.md` remained the fallback.

---

## What Was Built

**`check_coverage()` — the anti-recurrence hard-FAIL guard.**

- `scripts/eval-leanness.py` — added `OUT_OF_SCOPE` (a `set` of non-product
  top-level names: `archive`, `bin`, `claude-code`, `codex`, `cursor`,
  `node_modules`, `test`, and root files `README.md`, `CHANGELOG.md`,
  `CLAUDE.md`, `AGENTS.md`, `SKILL.md`, `LICENSE`, `VERSION`, `package.json`)
  beside `SURFACE_REGISTRY`, and `check_coverage(root)` following the
  `check_parity()` pattern (list-return, `{"subject","what","fix"}` shape).
  - **Stale-registry pass:** every `SURFACE_REGISTRY` path must exist on disk
    (file for `system_instructions`, directory for the rest); a missing path
    produces a finding distinguishable from the undeclared-entry case (its
    `what` text says "does not exist on disk").
  - **Undeclared-entry pass:** `os.scandir(root)` top-level entries minus
    (gated registry paths ∪ `WRIT_WORKSPACE`'s path ∪ `OUT_OF_SCOPE`); any
    leading-dot name is skipped unconditionally (covers `.git`, `.github`,
    `.claude`, `.codex`, `.cursor`, `.writ`, `.writ-lanes-*`, `.gitignore`,
    `.DS_Store` in one rule rather than enumerating each). One finding per
    unaccounted entry, offering both remedies (add a registry rule, or add to
    `OUT_OF_SCOPE`).
  - Wired into `main()`: `structural = check_parity(root) + check_coverage(root)`.
- `scripts/tests/test_eval_leanness.sh` — 4 new assertions: real-repo zero
  findings, a synthetic undeclared `newthing/` directory (exactly one
  finding, names it, offers the out-of-scope remedy), a deleted `adapters/`
  registry path (distinguishable stale-registry finding), and out-of-scope +
  dot-prefixed entries (`test/`, `archive/`, `.writ-lanes-3/`, `.cursor/`,
  `LICENSE`, `VERSION`) staying silent.
- **Test-harness fix required by this story:** every scenario's JSON output
  file was previously written *inside* the fixture root (`$TMP/out.json`),
  which the new coverage guard then flagged as an undeclared top-level entry
  — a self-inflicted false positive. Fixed by moving every scenario's output
  file to an independent `mktemp` path outside the fixture root.

### Implementation Decisions

1. **Dot-prefix rule instead of enumerating every dot-directory.** Matching
   any leading-dot top-level name in one branch (rather than listing `.git`,
   `.claude`, `.codex`, `.cursor`, `.writ`, `.writ-lanes-*`, `.gitignore`,
   `.DS_Store` individually in `OUT_OF_SCOPE`) means a new worktree lane or
   platform install directory never requires a registry edit — matches the
   story's explicit Notes guidance.
2. **`.writ`'s path is added to the accounted set directly** (via
   `WRIT_WORKSPACE["path"]`), not left to the dot-prefix rule alone, so the
   guard's accounting logic doesn't depend on `.writ` happening to start with
   a dot — a deliberate decoupling for clarity even though the dot-rule would
   also catch it.

### Test Results

**Verification:** `bash scripts/tests/test_eval_leanness.sh` — 24/24
assertions pass (cumulative through Story 2). Real-repo `eval.sh
--check=leanness`: `Findings: 0`.

### Review Outcome

**Result:** PASS (self-reviewed against every acceptance criterion; see
Story 1's note on subagent scoping for this spec).

- **Drift:** None.
- **Security:** Clean.

### Deviations from Spec

None.
