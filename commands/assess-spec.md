# Assess Spec Command (assess-spec)

## Overview

Analyze a specification for implementability risks *before* you commit to building it. Flags oversized stories, deep dependency chains, context accumulation hazards, and file-overlap conflicts — then recommends specific decomposition strategies.

This is the "will this actually work?" check. Run it after `/create-spec` or `/edit-spec`, or anytime a spec feels too heavy. `/implement-spec` also runs a lightweight version of this analysis as a pre-flight check.

**What this is NOT:** `/verify-spec` checks whether a *built* spec is correct. Assessment checks whether an *unbuilt* spec is **shaped well enough to build successfully**.

## Invocation

| Invocation | Behavior |
|---|---|
| `/assess-spec` | Interactive — select spec from `.writ/specs/` |
| `/assess-spec 2026-03-15-feature` | Assess named spec |
| `/assess-spec --brief` | Summary only — skip decomposition recommendations |

## Command Process

### Step 1: Load Spec

If no argument provided, present spec selection from `.writ/specs/` — show name, story count, task count, and status for each. Include an "Assess ALL" option.

**Load the full spec data model:**
1. Read `spec.md`, `spec-lite.md`, `user-stories/README.md`
2. Read ALL story files — tasks, acceptance criteria, dependencies, notes
3. Read `sub-specs/technical-spec.md` — architecture, file paths, integration points
4. Scan codebase — identify files referenced by stories, check import graphs

Build a mental model of: total stories/tasks/AC remaining, per-story sizing, dependency graph shape, file areas each story touches, and change surface per story.

**Only count remaining work** — completed stories don't contribute to implementation risk.

### Step 2: Run Assessment Checks

Run all six checks. Collect every flag — never stop at the first finding. Report the full picture.

---

#### Check 1: Spec-Level Sizing

Flags that the overall spec may overwhelm the `/implement-spec` orchestrator.

| Signal | Threshold | Severity |
|---|---|---|
| Remaining stories | > 8 | ⚠️ Warn |
| Remaining tasks | > 50 | ⚠️ Warn |
| Remaining tasks | > 80 | 🛑 Flag |
| Remaining AC | > 40 | ⚠️ Warn |
| No completed stories AND > 6 stories | — | ℹ️ Note — validate assumptions first |

---

#### Check 2: Dependency Graph

Build the DAG (same logic as `/implement-spec` Step 2.1). Compute: topological batches, critical path, bottleneck stories.

| Signal | Threshold | Severity |
|---|---|---|
| Dependency depth | > 3 | ⚠️ Warn |
| Dependency depth | > 5 | 🛑 Flag |
| All stories serial | Zero parallel batches | ⚠️ Warn |
| Bottleneck story | > 3 downstream dependents | ⚠️ Warn |
| Circular dependencies | Any | 🛑 Flag |

---

#### Check 3: Story-Level Sizing

For each remaining story:

| Signal | Threshold | Severity |
|---|---|---|
| Tasks | > 7 | ⚠️ Warn |
| Tasks | > 10 | 🛑 Flag |
| Acceptance criteria | > 8 | ⚠️ Warn |
| Acceptance criteria | > 12 | 🛑 Flag |

---

#### Check 4: Change Surface Complexity

Classify each story's change surface from its tasks and notes (same categories as `/implement-story` Gate 2.5 but inferred from the *plan*):

- **data layer** — schema, migration, model changes
- **API layer** — routes, endpoints, middleware
- **UI layer** — components, pages, styles
- **shared code** — hooks, utils, lib, context
- **security layer** — auth, permissions
- **test-only** — low risk

| Signal | Threshold | Severity |
|---|---|---|
| Story spans 3+ layers | e.g. data + API + UI | ⚠️ Warn |
| Story spans 4+ layers | — | 🛑 Flag |
| Security + feature bundled | auth changes mixed with features | ⚠️ Warn |
| Infrastructure + user-facing | migrations AND UI in one story | ⚠️ Warn |

---

#### Check 5: File Overlap

Cross-reference file areas each story will touch (from task descriptions, notes, and technical spec).

| Signal | Threshold | Severity |
|---|---|---|
| Two stories share a file area | Any | ℹ️ Note — must sequence |
| Three+ stories share a file area | — | ⚠️ Warn — merge conflict risk |
| Story modifies a file imported by >5 others | — | ⚠️ Warn — ripple effects |

---

#### Check 6: Context Accumulation Risk

Estimate whether the spec's shape will cause context degradation during pipeline execution.

Rate each remaining story across four factors (Low/Medium/High): task count (≤5 / 6-7 / >7), AC count (≤4 / 5-8 / >8), change surface (single-component / cross-component / full-stack), likely review iterations (1 / 2 / 3). A story's context cost = its highest factor score (Low=1, Medium=2, High=3).

| Signal | Threshold | Severity |
|---|---|---|
| Sum of context costs | > 16 | ⚠️ Warn |
| Sum of context costs | > 24 | 🛑 Flag — split into phases |
| Single story High on 3+ factors | — | ⚠️ Warn |
| Critical path stories all High | — | 🛑 Flag — compounds degradation |

---

### Step 3: Decomposition Recommendations

For every ⚠️ Warn and 🛑 Flag, generate a **specific, actionable** recommendation — not "consider splitting."

**Story-level split patterns:**

| Problem | Split Strategy |
|---|---|
| Full-stack story (3+ layers) | By layer: `{N}a: Data` → `{N}b: API` → `{N}c: UI` |
| Too many tasks (>7) | By cohesion: find boundaries where a subset delivers testable value |
| Security + feature | `{N}a: Auth/Permission Layer` → `{N}b: Feature Using Auth` |
| Infrastructure + user-facing | `{N}a: Infrastructure` → `{N}b: User-Facing` |

**Spec-level split patterns:**

| Problem | Split Strategy |
|---|---|
| >8 remaining stories | Phase A (foundation) → Phase B (dependent features) |
| Deep dependency chain | Split at the natural checkpoint |
| High context cost | Front-load high-cost stories while orchestrator is fresh |
| Bottleneck with >3 dependents | Implement bottleneck first as its own spec to de-risk |

Each recommendation should include: the trigger (what flag it addresses), the current shape, the proposed shape, and the impact on dependency depth and context cost.

**If `--brief` mode:** Skip recommendations, only show the summary table.

---

### Step 4: Assessment Report

Present a summary table of all 6 checks with results and findings, an overall rating, recommendations with before/after shapes, and a context budget showing each story's estimated cost.

**Overall ratings:**

| Rating | Criteria |
|---|---|
| ✅ Ready to implement | No 🛑 Flags, ≤2 ⚠️ Warns |
| ⚠️ Implementable with adjustments | No 🛑 Flags but >2 ⚠️ Warns, OR 1 🛑 Flag with clear mitigation |
| 🛑 Needs restructuring | ≥2 🛑 Flags, or 1 🛑 Flag without mitigation |

Then offer: apply all recommendations, choose which to apply, proceed as-is (accept risks), or save report only.

---

### Step 5: Apply Decomposition (if requested)

When the user chooses to apply recommendations, execute the splits directly — these are mechanical changes that don't need discovery conversation.

**Per story split:** Partition tasks into sub-story files, set dependencies correctly, partition AC to match tasks, update README and spec-lite. Archive the original oversized story.

**Per spec split:** Create a Phase B spec folder, move downstream stories there, add cross-spec dependency notes, update both phases' README and spec files.

**After all splits:** Re-run a quick assessment to confirm the new shape passes. Show before/after comparison: story count, max story size, context score.

---

## Severity Definitions

| Severity | Meaning |
|---|---|
| 🛑 **Flag** | Likely pipeline problems — strongly recommend fixing first |
| ⚠️ **Warn** | Elevated risk — consider fixing or at minimum track during implementation |
| ℹ️ **Note** | Informational — no action required |
| ✅ **Pass** | Within healthy thresholds |

---

## Integration with Writ

| Command | Relationship |
|---------|-------------|
| `/create-spec` | Run `/assess-spec` after creating a spec to validate its shape |
| `/edit-spec` | Run after major edits to re-validate; `/assess-spec` can invoke `/edit-spec` for splits |
| `/implement-spec` | Runs a **lightweight pre-flight assessment** (Checks 1-3 + context score) before execution |
| `/verify-spec` | Complementary — assess checks shape *before* building; verify checks correctness *after* |

---

## References

- Standing instructions: [`commands/_preamble.md`](_preamble.md)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)
