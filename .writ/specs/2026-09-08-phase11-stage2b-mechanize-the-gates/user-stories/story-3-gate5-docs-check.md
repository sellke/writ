# Story 3: Gate 5 Docs Check — docs-check.py Diffs Documented Symbols Against Changed Exports

> **Status:** Completed ✅
> **Commit:** dda5623edcac6b435be25d005e3f4c4239cc5c17
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer who needs Gate 5's "docs updated" claim re-derived from a symbol-to-export diff so a documentation agent cannot report YES when a new public export has no doc
**I want to** land `scripts/docs-check.py` that diffs public exports in `--changed` (or `git diff --name-only`) against README / CHANGELOG / a detected docs framework / adjacent docstrings, and wire that check into `commands/implement-story.md` Gate 5 after the documentation agent
**So that** missing documentation of a new or newly-public export is a mechanical `fail` (BLOCKED, agent `documentation-agent`), while a markdown-only tree with no public exports — Writ itself — is `unverifiable` rather than a mute-the-check `fail` or a false `pass`

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [x] Given a tiny app fixture whose `--changed` set includes a new or newly-public export that is named in a readable README, CHANGELOG, detected docs-framework page, or adjacent docstring, when `python3 scripts/docs-check.py check --repo <fixture> --changed <file>…` runs, then it prints verdict `pass` (one of `GATE_SCRIPT_VERDICTS`) and exits 0 `[AC-3.1]`
- [x] Given a tiny app fixture whose `--changed` set includes a public export with no matching documented symbol, when `check` runs, then it prints verdict `fail` and a `reason:` line and exits 1 — never treating “could not tell” as `fail` `[AC-3.2]`
- [x] Given a markdown-only fixture with no detected docs framework and no public exports in the changed set (Writ-the-product shape), when `check` runs against that fixture (not this repo as a pass case), then it prints verdict `unverifiable` and exits 0 — not `pass` and not `fail` `[AC-3.3]`
- [x] Given `check --repo .` with `--changed` omitted and git unable to resolve a changed set (`git diff --name-only` against `HEAD^` / the story parent cannot answer), when the script runs, then it prints verdict `unverifiable` with a reason that the set could not be resolved and exits 0 `[AC-3.4]`
- [x] Given this story has landed, when `commands/implement-story.md` is read, then frontmatter `gate5_docs` is `script: scripts/docs-check.py`, Gate 5 runs the script after the documentation agent, script `fail` applies the shared BLOCKED escalation with agent `documentation-agent`, script `unverifiable` continues with the reason verbatim and does not mark the story `DEGRADED`, `eval.sh` registers check `docs-check` (findings via `add_finding`, not count-blocking), and `check_verdict_provenance()` still does not pass `--prose-only-blocking` `[AC-3.5]`

## Implementation Tasks

- [x] 3.1 Write `scripts/tests/test_docs_check.py` (pytest, Python 3.9) using tiny app trees only — never this markdown repo as a `pass` fixture: export-documented → `pass`; export-undocumented → `fail`; empty/markdown tree → `unverifiable`; omitted `--changed` with unresolvable git → `unverifiable`; assert exit 0/1/2 and the shared stdout shape (verdict line, optional `reason:`, summary last) `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`
- [x] 3.2 Implement `scripts/docs-check.py` `check --repo . [--changed FILE …]` (stdlib, argparse, `--repo`): public exports in `--changed` or `git diff --name-only` against `HEAD^` when omitted and git can answer; match against README / CHANGELOG / detected docs framework / adjacent docstrings; verdict table per `sub-specs/technical-spec.md` §3 `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`
- [x] 3.3 Set `commands/implement-story.md` frontmatter `gate5_docs: script: scripts/docs-check.py` and add a “Verify the claim, don't trust it.” block after the documentation agent (Gate 4 pattern): invoke `docs-check.py`; `fail` → BLOCKED with agent `documentation-agent`; `unverifiable` → continue, reason verbatim, no `DEGRADED` `[AC-3.5]`
- [x] 3.4 Register `check_docs_check()` in `scripts/eval.sh` `CHECKS=(...)` as `docs-check` (mirror `check_build_smoke` / `check_verdict_provenance` wiring: `add_finding` / `add_note`, not count-blocking) and add `scripts/tests/test_eval_docs_check.sh` in the `test_eval_verdict_provenance.sh` fixture shape; do not pass `--prose-only-blocking` `[AC-3.5]`
- [x] 3.5 Verify acceptance criteria: Gate 5 body and frontmatter match AC-3.5, fixtures stay tiny app trees, Writ-the-product remains the `unverifiable` case, and the closing commit appends `{date} stage-2b: …` to the decision log `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`
- [x] 3.6 Verify all tests pass: `uv run --python 3.9 pytest scripts/tests/test_docs_check.py` and `bash scripts/eval.sh --check=docs-check` (full `eval.sh` exits 0; `--prose-only-blocking` still off until Story 5) `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`

## Notes

**Technical considerations.** Same CLI family as `build-smoke.py` / `test-integrity.py` / `verdict-provenance.py`: Python 3.9 stdlib, subcommands, exit 0/1/2, `--repo`. Verdict vocabulary is `pipeline-baseline.py` `GATE_SCRIPT_VERDICTS`: `pass` / `fail` / `unverifiable`. Detected frameworks stay the Gate 5 list already in `implement-story.md` (VitePress, Docusaurus, Nextra, MkDocs, Storybook, or plain README). `install.sh` already copies `scripts/*.py` — no install work.

**Hardest constraint.** A FAIL that means “could not tell” gets muted. No docs framework **and** no public exports is `unverifiable`, not `fail`. This repo is that case. Fixtures that would “pass” on Writ’s README would lie.

**Risks.** Export discovery must stay conservative: inventing public symbols from markdown, or treating every identifier as an export, turns `unverifiable` trees into false `fail`. Prefer a small, explicit public-export heuristic on the tiny app fixtures (e.g. `__all__`, `export` / `exports`, documented API files) over scanning this repository.

**Integration.** No story dependencies. Story 5 owns the frontmatter flip of the remaining prose-only gates and turning `--prose-only-blocking` on; this story sets `gate5_docs` to `script:` so provenance is truthful the moment the file exists. Replay against Stage 1/2a baselines is Story 5.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** `spec.md → ## 🎯 Experience Design`
- **Business rules:** [Checker wins, `unverifiable` is not a failed gate, No new gate numbers, Python 3.9 stdlib, ADR-013 holds, Decision log]
- **Experience:** `spec.md → ## 🎯 Experience Design`

---

## What Was Built

**Implementation Date:** 2026-09-08

### Files Created

1. **`scripts/docs-check.py`** (428 lines) — `check --repo [--changed]`. Conservative exports (`__all__`, JS/TS `export` / `exports` only). Markdown never invents exports. Writ / no public exports → `unverifiable`.
2. **`scripts/tests/test_docs_check.py`** (259 lines) — tiny app fixtures only. [AC-3.1–AC-3.5]
3. **`scripts/tests/test_eval_docs_check.sh`** (226 lines)

### Files Modified

- **`commands/implement-story.md`** — `gate5_docs: script: scripts/docs-check.py`; Gate 5 verify block; fail → BLOCKED with `documentation-agent`.
- **`scripts/eval.sh`** — `docs-check` / `check_docs_check()` pins live `--changed` to README.md so this repo stays unverifiable.

### Implementation Decisions

1. **Bare `def`/`class` are not public exports.** `__all__` / `export` only.
2. **This repo is never a pass fixture.**

### Test Results

Story-module pytest + bash harness green. Full suite 1135 passed, 1 skipped. `eval.sh` Findings 0. Coverage unverifiable.

### Review Outcome

**Result:** PASS — 1 iteration. Drift: Medium (DEV-001).
