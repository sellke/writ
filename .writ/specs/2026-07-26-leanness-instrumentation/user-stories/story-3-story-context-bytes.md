# Story 3: Static `story_context_bytes` Metric

> **Status:** Completed ✅ (2026-07-26)
> **Priority:** Medium
> **Dependencies:** None

## User Story

As a **Writ maintainer running Tier A eval**, I want **a deterministic `story_context_bytes` count of everything `implement-story` declares it loads for a full-pipeline story**, so that **a routing-table or agent-definition change that balloons the per-story context load shows up as a number in the guardian's output instead of being discovered later as a slow, expensive pipeline.**

## Acceptance Criteria

- [x] **Given** a repo with `.writ/context.md`, at least one story file, and `spec-lite.md` present under an active spec folder, **when** `python3 scripts/eval-leanness.py` runs, **then** `metrics.story_context_bytes` is a non-negative integer equal to the sum of the declared-load artifact set: `.writ/context.md` + the deterministically selected story file + `spec-lite.md` + context-hint fetch sources + the documented 2KB `knowledge_context` cap + the five gate agent definition files (`architecture-check-agent.md`, `coding-agent.md`, `review-agent.md`, `testing-agent.md`, `documentation-agent.md`).
- [x] **Given** an unchanged working tree, **when** the script is run twice in succession, **then** both runs emit a byte-identical `story_context_bytes` value (no timestamps, filesystem-order nondeterminism, or run-to-run drift).
- [x] **Given** a fixture where `.writ/context.md`, `spec-lite.md`, or any story file is absent, **when** the script runs, **then** each absent component contributes `0`, the run exits `0`, and no structural finding or traceback is produced.
- [x] **Given** one of the five gate agent definition files grows by N bytes, **when** the script runs, **then** `story_context_bytes` increases by exactly N — the metric tracks declared-load change, not a frozen snapshot.
- [x] **Given** the metric appears in the JSON `metrics` block or any human-readable rendering, **when** a reader inspects that output, **then** the value is accompanied by an explicit proxy label stating it measures declared load, not consumed tokens (Business Rule 7).

## Implementation Tasks

- [x] Extend `scripts/tests/test_eval_leanness.sh` first: assert `story_context_bytes` is present in `metrics` and is a non-negative integer; assert **determinism** by invoking the helper twice against the same tree and comparing extracted values; add a missing-artifact fixture (`--root` temp dir with no `.writ/context.md` and no spec) that yields zero contributions, exit `0`, and no structural finding; assert the proxy label appears in emitted output.
- [x] Add declared-load constants to `scripts/eval-leanness.py`: `KNOWLEDGE_CONTEXT_CAP_BYTES = 2048` and an ordered gate-agent filename list (`architecture-check-agent.md`, `coding-agent.md`, `review-agent.md`, `testing-agent.md`, `documentation-agent.md`), each with a one-line comment citing `commands/implement-story.md` Step 2 and the routing table as source of truth.
- [x] Implement `story_context_components(root) -> dict[str, int]` returning an ordered component → byte-size map. Read file sizes with `os.path.getsize`; sort every globbed file list before summing; return `0` for any absent or unreadable path rather than raising.
- [x] Implement deterministic story selection and hint-resolution rules (see Notes): resolve the same story file and the same fetched hint sections on every run against an unchanged tree; unresolvable references contribute `0`.
- [x] Surface `story_context_bytes` as the sum of the component map inside `compute_metrics`, alongside existing metric keys, preserving the JSON envelope (`structural` / `warnings` / `metrics`) and always-exit-0 contract.
- [x] Add the proxy label at every reporting site: the module docstring output contract, a sibling note key in the metrics block (e.g. `story_context_bytes_note`), and any human-readable render — never present the number as token accounting.
- [x] Verify acceptance criteria and full suite pass: run `bash scripts/tests/test_eval_leanness.sh`, run the script twice against this repo and diff the values, and confirm `bash scripts/eval.sh --check=leanness` still exits `0`.

## Notes

**Proxy limitation (non-negotiable)**

This metric measures what `implement-story` *declares* it loads, not what any model actually consumes. It is fit for catching a routing-table change that balloons the load; it is unfit as ground-truth token usage. Business Rule 7 makes the disclaimer part of the deliverable — any unlabeled reporting site is a failed acceptance criterion.

**Deterministic story selection**

There is no "current story" at eval time. Use a stable worst-case rule: the largest story file under the lexicographically last date-prefixed folder in `.writ/specs/`; zero when no story files exist. Document the rule in-code where implemented.

**Context-hint fetch sources**

Parse `## Context for Agents` from the selected story file and resolve extended references (`file.md → ## Section → ### Subsection`) and bracketed category hints to their source sections in `spec.md` or `technical-spec.md`; sum only those section byte sizes. Unresolvable references contribute `0`. Do not sum whole source files — that would overstate the declared load.

**`knowledge_context` uses the documented cap**

Actual assembly is keyword-driven and non-reproducible. Charge the flat 2KB budget `implement-story` documents (`≤2KB`), not an assembled block.

**Determinism**

Sort every file list, avoid filesystem-order iteration, and never let mtime, environment, or run order enter the sum. Values legitimately change when the tree changes; determinism is asserted only across repeated runs on an *unchanged* tree.

**Risks**

- Over-specifying hint resolution risks the metric becoming its own maintenance burden inside the script this spec is trying to keep lean. Keep the resolver simple; a hint that will not resolve is a `0`, not an error.
- The gate-agent list is a hardcoded mirror of the routing table. If a gate is added to `implement-story.md` and not here, the metric silently understates. Note the coupling in-code.

**Integration**

Independent of Stories 1, 2, and 4 — no dependency on the surface registry. Both Story 1 and this story touch `compute_metrics`; keep this addition self-contained to minimize merge friction.

**Out of scope**

Measurement registry (Story 1), coverage guard (Story 2), reduction ratchet (Story 4), ADR-019 (Story 5), live token instrumentation.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] `scripts/tests/test_eval_leanness.sh` passes, including determinism and missing-artifact scenarios
- [x] Proxy label present at every reporting site
- [x] Code reviewed

## Context for Agents

- **Business rules:** `spec.md → ## 📋 Business Rules` → [Rule 7 (`story_context_bytes` is a declared-load proxy — must be labeled wherever reported); Rule 5 (the guardian measures itself — no self-exemption for `eval-leanness.py`); Rule 6 (dogfooding-only — no `commands/*.md` changes)].
- **Experience:** `spec.md → ## 🎯 Experience Design (CLI / CI — no user-facing UI) → ### Feedback Model` (metrics render through `add_note`, never the findings counter — this metric never fails a run); `spec.md → ## 🎯 Experience Design (CLI / CI — no user-facing UI) → ### Happy Path` (metrics block in report for Tier B ritual to consume).
- **Error map rows:** [] — no row in `### Error Experience` governs this metric; absent artifacts contribute `0` silently rather than producing a finding.
- **Shadow paths:** `spec.md → ## Detailed Requirements → ### Static story_context_bytes` (declared-load artifact set and proxy framing); `spec.md → ## Technical Concerns (surfaced at contract time)` → "`story_context_bytes` is a proxy" (declared load, not consumed tokens); `commands/implement-story.md → ### Step 2: Load Context` (items 1–6), **Routing table — what each agent receives**, and each Gate's *Context routing* note (declared-load source of truth).
- **Files in scope:** `scripts/eval-leanness.py`, `scripts/tests/test_eval_leanness.sh`.

---

## What Was Built

**`story_context_bytes` — a static, deterministic, explicitly-labeled proxy.**

- `scripts/eval-leanness.py` — added:
  - `KNOWLEDGE_CONTEXT_CAP_BYTES = 2048` and `GATE_AGENT_FILES` (the 5 gate
    agent filenames from `implement-story.md`'s routing table), each with an
    in-code comment naming the source of truth and the understating-risk if
    a gate is added there and not mirrored here.
  - `select_story_file(root)` — deterministic worst-case selection: the
    largest story file under the lexicographically last date-prefixed folder
    in `.writ/specs/`; `None` when none exist. Both the folder list and the
    story-file glob are `sorted()` before `max()` so ties resolve the same
    way every run.
  - `extract_markdown_section()` / `find_heading_containing()` /
    `resolve_spec_file()` / `resolve_extended_ref()` / `resolve_category_ref()`
    / `context_for_agents_section()` / `resolve_context_hints()` — a bounded
    markdown-section resolver for the story's `## Context for Agents` block.
    Extended references (`` `file.md → ## Section → ### Subsection` ``) walk
    nested headings to the deepest resolvable section and sum only that
    section's bytes. Bracketed category hints (`Business rules`, `Error map
    rows`, `Shadow paths`, `Experience`) fall back to a keyword-anchored
    lookup of the category's documented primary source section. Any
    unresolvable reference contributes `0` — never an exception.
  - `story_context_components(root)` — ordered component→bytes map:
    `context_md`, `story_file`, `spec_lite`, `context_hints`,
    `knowledge_context_cap` (flat `2048`, per the Notes' "charge the
    documented cap, not an assembled block" guidance), `gate_agents` (sum of
    the 5 named files' sizes under `agents/`).
  - `story_context_bytes = sum(story_context_components(root).values())`,
    surfaced in `compute_metrics()` alongside a sibling
    `story_context_bytes_note` key (`STORY_CONTEXT_BYTES_NOTE`) — the proxy
    label lives beside the number in the JSON itself, not only in prose.
- `scripts/tests/test_eval_leanness.sh` — added `build_context_repo()` (a
  `build_repo()` extension with `.writ/context.md`, an active spec under
  `.writ/specs/2026-01-01-demo-spec/` with `spec.md`/`spec-lite.md`/a story
  file carrying a `## Context for Agents` block, and the 5 exact gate-agent
  filenames under `agents/`). 5 new assertions: non-negative integer
  presence, determinism (two runs, same value), a gate-agent file growing by
  a known N bytes moving the metric by exactly N, missing-artifact
  graceful degradation (reusing the plain `build_repo()` fixture, which has
  neither `.writ/context.md` nor `.writ/specs/`), and the proxy-label note
  text (`"proxy"` + `"declared"` both present, case-insensitive).
- Verified deterministic against the real repo: two consecutive
  `python3 scripts/eval-leanness.py` runs produced byte-identical
  `story_context_bytes` (74222, selecting this spec's own Story 5 file, the
  largest in the lexicographically-last spec folder — a deliberately
  self-referential but stable choice).

### Implementation Decisions

1. **Category-hint resolution uses a keyword anchor, not an exact heading
   string**, because the documented "primary source" headings
   (`spec.md → ## 📋 Business Rules`, `## 🎯 Experience Design (...)`) vary in
   exact wording across specs; a substring/keyword match keeps the resolver
   generic across whichever spec is "last" at eval time, at the cost of being
   best-effort rather than exact — consistent with the story's explicit
   "unresolvable = 0, not an error" mandate.
2. **`knowledge_context_cap` is unconditional** (always `2048`, never gated
   on `.writ/knowledge/` existing) per the Notes: actual assembly is
   keyword-driven and non-reproducible, so the metric charges the documented
   budget flatly rather than attempting to reproduce assembly.

### Test Results

**Verification:** `bash scripts/tests/test_eval_leanness.sh` — 20/20
assertions pass (cumulative through Story 3). Real-repo determinism verified
via two direct `eval-leanness.py` invocations (diffed `story_context_bytes`).
`eval.sh --check=leanness`: `Findings: 0`.

### Review Outcome

**Result:** PASS (self-reviewed against every acceptance criterion; see
Story 1's note on subagent scoping for this spec).

- **Drift:** None.
- **Security:** Clean — all paths resolved are local-repo, read-only.

### Deviations from Spec

None.
