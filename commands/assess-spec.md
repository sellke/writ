# Assess Spec Command (assess-spec)

## Overview

Analyze a specification for implementability risks *before* you commit to building it. Flags oversized stories, deep dependency chains, context accumulation hazards, and file-overlap conflicts — then recommends specific decomposition strategies.

This is the "will this actually work?" check. Run it after `/create-spec` or `/edit-spec`, or anytime a spec feels too heavy. `/implement-spec` also runs a lightweight version of this analysis as a pre-flight check before showing the execution plan.

**What this is NOT:** This is not `/verify-spec`. Verification checks whether a *built* spec is correct (tests pass, statuses sync, coverage met). Assessment checks whether an *unbuilt* spec is **shaped well enough to build successfully**.

## Invocation

| Invocation | Behavior |
|---|---|
| `/assess-spec` | Interactive — select spec from `.writ/specs/` |
| `/assess-spec 2026-03-15-feature` | Assess named spec |
| `/assess-spec --brief` | Summary only — skip decomposition recommendations |

## Command Process

### Step 1: Load Spec

**If no argument provided:**

```
AskQuestion({
  title: "Assess Specification",
  questions: [
    {
      id: "spec",
      prompt: "Which specification do you want to assess?",
      options: [
        // Dynamically populated from .writ/specs/
        // Show name, story count, task count, status
        { id: "spec_1", label: "[DATE]-[name] (N stories, M tasks, status)" },
        { id: "all", label: "Assess ALL specifications" }
      ]
    }
  ]
})
```

**Load spec data model:**

```
1. Read spec.md — contract, scope boundaries, deliverables
2. Read spec-lite.md — summary
3. Read user-stories/README.md — progress table, dependency declarations
4. Read ALL user-stories/story-N-*.md files — tasks, acceptance criteria, notes
5. Read sub-specs/technical-spec.md — architecture, file paths, integration points
6. Scan codebase — identify files referenced by stories, check import graphs
```

Build the assessment data structure:

```json
{
  "spec": {
    "name": "feature-name",
    "totalStories": 8,
    "totalTasks": 42,
    "totalAcceptanceCriteria": 28,
    "status": "Planning",
    "completedStories": 2
  },
  "stories": [
    {
      "number": 1,
      "title": "Auth Middleware",
      "tasks": 6,
      "acceptanceCriteria": 4,
      "dependencies": [],
      "status": "Completed ✅",
      "fileAreas": ["src/middleware/", "src/lib/auth.ts"],
      "changeSurface": "cross-component",
      "flags": []
    }
  ],
  "dependencyGraph": {
    "maxDepth": 3,
    "parallelBatches": 4,
    "criticalPath": ["story-1", "story-3", "story-6", "story-8"]
  }
}
```

### Step 2: Run Assessment Checks

Run all checks, collect every flag. Never stop at the first finding — report the full picture.

---

#### Check 1: Spec-Level Sizing

These flags indicate the overall spec may overwhelm the `/implement-spec` orchestrator or represent more work than can be reliably executed in a single pipeline run.

| Signal | Threshold | Severity | Why It Matters |
|---|---|---|---|
| Total stories | > 8 remaining (not complete) | ⚠️ Warn | `/implement-spec` orchestrator accumulates each story's summary in its context window |
| Total tasks | > 50 remaining | ⚠️ Warn | Large overall surface area; high chance of scope drift |
| Total tasks | > 80 remaining | 🛑 Flag | Spec should almost certainly be split into phases |
| Total acceptance criteria | > 40 remaining | ⚠️ Warn | Review agent attention dilution across many criteria |
| No completed stories AND > 6 stories | — | ℹ️ Note | Consider implementing 1-2 stories first to validate assumptions |

**Only count remaining work** — completed stories don't contribute to implementation risk.

---

#### Check 2: Dependency Graph Analysis

Parse each story's dependency declarations and build the DAG (same logic as `/implement-spec` Step 2.1).

| Signal | Threshold | Severity | Why It Matters |
|---|---|---|---|
| Max dependency depth | > 3 levels | ⚠️ Warn | Forces deep serialization — each level must complete before the next starts |
| Max dependency depth | > 5 levels | 🛑 Flag | Pipeline will be almost entirely sequential |
| Zero parallel batches | All stories serial | ⚠️ Warn | No parallelism benefit from `/implement-spec`; might as well run stories individually |
| Single bottleneck story | >3 downstream dependents | ⚠️ Warn | If this story fails or needs rework, everything downstream is blocked |
| Circular dependencies | Any cycle detected | 🛑 Flag | Cannot execute — must be resolved before implementation |

**Compute:**
```
1. Topological sort into parallel batches
2. Count batch count and batch sizes
3. Identify critical path (longest chain through the DAG)
4. Identify bottleneck stories (most downstream dependents)
```

---

#### Check 3: Story-Level Sizing

For each remaining (non-complete) story:

| Signal | Threshold | Severity | Why It Matters |
|---|---|---|---|
| Implementation tasks | > 7 | ⚠️ Warn | Exceeds Writ's own story sizing guideline |
| Implementation tasks | > 10 | 🛑 Flag | Too large for a single coding agent pass |
| Acceptance criteria | > 8 | ⚠️ Warn | Review agent must verify each — attention dilution |
| Acceptance criteria | > 12 | 🛑 Flag | Review quality will degrade |

---

#### Check 4: Change Surface Complexity

For each remaining story, classify its change surface using the same heuristic as Gate 2.5 in `/implement-story`, but from the *plan* rather than actual file changes:

**Infer from story tasks and notes:**
- Tasks mention schema/migration/model changes → **data layer**
- Tasks mention API routes, endpoints, middleware → **API layer**
- Tasks mention components, pages, UI, styles → **UI layer**
- Tasks mention shared hooks, utils, lib, context → **shared code**
- Tasks mention auth, permissions, security → **security layer**
- Tasks mention tests only → **test-only** (low risk)

| Signal | Threshold | Severity | Why It Matters |
|---|---|---|---|
| Story spans 3+ layers | data + API + UI in one story | ⚠️ Warn | Full-stack stories have the highest review iteration rate |
| Story spans 4+ layers | data + API + UI + shared | 🛑 Flag | Almost always should be split |
| Story touches security + another layer | auth changes bundled with features | ⚠️ Warn | Security changes deserve isolated review attention |
| Infrastructure + user-facing in one story | migrations/config AND components/pages | ⚠️ Warn | Different verification needs; split for cleaner gates |

---

#### Check 5: File Overlap Between Stories

Cross-reference the file areas each story will touch (inferred from tasks, notes, and technical spec references).

| Signal | Threshold | Severity | Why It Matters |
|---|---|---|---|
| Two stories modify the same file | Any overlap in planned file areas | ℹ️ Note | Must be sequenced, not parallelized |
| Three+ stories modify the same file | Same file area in 3+ stories | ⚠️ Warn | Merge conflict risk even with sequencing; consider consolidating the shared work |
| Shared utility modification | Story modifies a file imported by >5 other files | ⚠️ Warn | Ripple effects; needs careful integration verification |

**How to detect file areas:**
1. Parse task descriptions for file paths, directory names, and module references
2. Check story `## Notes` sections for file references
3. Cross-reference with `sub-specs/technical-spec.md` file listings
4. If codebase exists, scan import graphs for files mentioned in stories

---

#### Check 6: Context Accumulation Risk

This check estimates whether the spec's shape will cause context degradation during pipeline execution — the concern from Writ's own context engineering research.

**Per-story context cost estimate:**

| Factor | Low | Medium | High |
|---|---|---|---|
| Task count | ≤5 | 6-7 | >7 |
| Acceptance criteria | ≤4 | 5-8 | >8 |
| Change surface | single-component | cross-component | full-stack |
| Likely review iterations | 1 | 2 | 3 (review loop cap) |

Assign each story a context weight: Low = 1, Medium = 2, High = 3.

**Sum across the factor with the highest score to get the story's context cost.**

| Spec-level signal | Threshold | Severity | Why It Matters |
|---|---|---|---|
| Sum of story context costs | > 16 (remaining stories) | ⚠️ Warn | `/implement-spec` orchestrator will carry heavy context by the final stories |
| Sum of story context costs | > 24 (remaining stories) | 🛑 Flag | Strong candidate for splitting into phases |
| Any single story at High on 3+ factors | — | ⚠️ Warn | That story will likely need multiple review iterations; budget for it |
| Critical path stories all High context cost | — | 🛑 Flag | Serialized heavy stories compound context degradation |

---

### Step 3: Generate Decomposition Recommendations

For every ⚠️ Warn and 🛑 Flag, generate a **specific, actionable** recommendation — not a vague "consider splitting."

**Story-level decomposition patterns:**

| Problem | Recommended Split |
|---|---|
| Full-stack story (data + API + UI) | Split by layer: `{N}a: Schema & Models` → `{N}b: API Routes` → `{N}c: UI Components` |
| Too many tasks (>7) | Group tasks by cohesion: find natural boundaries where a subset delivers testable value |
| Security + feature bundled | Extract security into its own story that runs first: `{N}a: Auth/Permission Layer` → `{N}b: Feature Using Auth` |
| Infrastructure + user-facing | Split: `{N}a: Infrastructure (migrations, config, middleware)` → `{N}b: User-Facing (UI, API endpoints)` |

**Spec-level decomposition patterns:**

| Problem | Recommended Split |
|---|---|
| >8 remaining stories | Split into Phase A (foundation) and Phase B (features that depend on foundation) |
| Deep dependency chain (>3) | Identify the natural "checkpoint" where downstream stories could be a separate spec |
| High total context cost | Put high-context-cost stories in earlier batches when the orchestrator is fresh |
| Bottleneck story with >3 dependents | Implement the bottleneck first as its own spec/prototype to de-risk it |

**Decomposition output format for each recommendation:**

```markdown
### REC-001: Split Story 3 by layer

**Trigger:** Story 3 (User Dashboard) spans 4 layers (data + API + UI + shared), 9 tasks
**Risk:** High review iteration count; coding agent context accumulation in fix loops

**Current:**
  Story 3: User Dashboard (9 tasks, deps: Story 1)

**Proposed:**
  Story 3a: Dashboard Data Layer (3 tasks, deps: Story 1)
    - Schema changes, model definitions, seed data
  Story 3b: Dashboard API (3 tasks, deps: Story 3a)
    - API routes, data fetching, validation
  Story 3c: Dashboard UI (4 tasks, deps: Story 3b)
    - React components, state management, styling

**Impact:**
  - Dependency depth increases by 2 (acceptable — these are tightly coupled)
  - Each sub-story fits within 5-7 task guideline
  - Review agent can focus on one layer per pass
  - Fix loops affect smaller scope
```

**If `--brief` mode:** Skip the full decomposition recommendations. Only show the summary table.

---

### Step 4: Assessment Report

Present the complete assessment:

```
🔍 Spec Assessment: 2026-03-15-user-dashboard

════════════════════════════════════════════════════════
 CHECK                              RESULT    FINDINGS
════════════════════════════════════════════════════════
 1. Spec-level sizing               ⚠️        9 stories, 54 tasks remaining
 2. Dependency graph                ✅        Depth 2, 3 parallel batches
 3. Story-level sizing              🛑        2 stories exceed task limit
 4. Change surface complexity       ⚠️        1 full-stack story
 5. File overlap                    ℹ️        Stories 2,4 share auth module
 6. Context accumulation risk       ⚠️        Score 18/24 (moderate-high)
════════════════════════════════════════════════════════

Overall: ⚠️ Implementable with adjustments (3 recommendations)

── Recommendations ──────────────────────────────────

REC-001: Split Story 3 by layer (🛑 9 tasks, full-stack)
  Story 3 → 3a (Data, 3 tasks) → 3b (API, 3 tasks) → 3c (UI, 4 tasks)

REC-002: Split Story 7 (🛑 11 tasks)
  Story 7 → 7a (Core logic, 5 tasks) → 7b (Integration, 6 tasks)

REC-003: Sequence Stories 2 and 4 (ℹ️ file overlap)
  Both touch src/lib/auth.ts — ensure they're in different batches
  (Already satisfied by dependency graph — no action needed)

── Context Budget Estimate ──────────────────────────

Stories by estimated context cost:
  Story 3: HIGH (9 tasks, full-stack, ~3 review iterations)
  Story 5: HIGH (7 tasks, cross-component, ~2 review iterations)
  Story 7: HIGH (11 tasks, cross-component, ~3 review iterations)
  Story 2: MEDIUM (5 tasks, single-component)
  Story 4: MEDIUM (6 tasks, cross-component)
  Story 6: LOW (4 tasks, test-only)
  Story 8: MEDIUM (5 tasks, API-only)
  Story 9: LOW (3 tasks, docs-only)

If splitting per recommendations, context score drops from 18 → 13.
```

Then prompt:

```
AskQuestion({
  title: "Assessment Actions",
  questions: [
    {
      id: "action",
      prompt: "How would you like to proceed?",
      options: [
        { id: "apply_all", label: "Apply all decomposition recommendations" },
        { id: "apply_some", label: "Choose which recommendations to apply" },
        { id: "proceed", label: "Proceed to implementation as-is (accept risks)" },
        { id: "save", label: "Save report only — I'll handle it manually" }
      ]
    }
  ]
})
```

**Handling responses:**

- **apply_all**: Run `/edit-spec` with each recommendation as a pre-formed modification contract. Apply sequentially — each split may affect subsequent recommendations.
- **apply_some**: Present each recommendation as a yes/no AskQuestion. Apply selected ones via `/edit-spec`.
- **proceed**: Done. User accepts the risks. No changes.
- **save**: Write report to `.writ/specs/[spec-folder]/assessment-YYYY-MM-DD.md` and exit.

---

### Step 5: Apply Decomposition (if requested)

For each accepted recommendation, the assessment command orchestrates the decomposition directly rather than spawning a full `/edit-spec` flow. The changes are mechanical (split a story file into N files, update README, adjust dependencies) — they don't need discovery conversation.

**Per story split:**

1. Read the source story file
2. Partition tasks into sub-story groups per the recommendation
3. Create new story files with correct numbering, dependencies, and acceptance criteria partitioned to match
4. Remove or archive the original oversized story
5. Update `user-stories/README.md` — new rows, updated dependency graph, recalculated totals
6. Update `spec-lite.md` if story titles/counts changed

**Per spec split (Phase A / Phase B):**

1. Create a new spec folder for Phase B: `.writ/specs/[DATE]-[name]-phase-b/`
2. Move downstream stories to Phase B
3. Add cross-spec dependency note to Phase B's `spec.md`
4. Update Phase A's README to reflect reduced scope
5. Generate Phase B's README, spec.md, and spec-lite.md

**After all splits applied:**

```
✅ Decomposition complete

Applied: REC-001 (Story 3 → 3a, 3b, 3c), REC-002 (Story 7 → 7a, 7b)
Stories: 9 → 12
Tasks: 54 → 54 (unchanged — same work, better shaped)
Max story size: 11 → 6 ✅
Context score: 18 → 13 ✅

Re-running quick assessment...

════════════════════════════════════════════════════════
 CHECK                              RESULT
════════════════════════════════════════════════════════
 1. Spec-level sizing               ⚠️  12 stories (borderline)
 2. Dependency graph                ✅  Depth 3, 4 parallel batches
 3. Story-level sizing              ✅  All stories ≤7 tasks
 4. Change surface complexity       ✅  No full-stack stories
 5. File overlap                    ✅  Overlap resolved by sequencing
 6. Context accumulation risk       ✅  Score 13 (moderate)
════════════════════════════════════════════════════════

Ready for /implement-spec.
```

---

## Assessment Severity Definitions

| Severity | Meaning | Action |
|---|---|---|
| 🛑 **Flag** | Likely to cause pipeline problems (review loops, context degradation, merge conflicts) | Strongly recommend addressing before implementation |
| ⚠️ **Warn** | Elevated risk but may succeed — depends on codebase complexity and story specifics | Consider addressing; at minimum, be aware during implementation |
| ℹ️ **Note** | Informational — something to be aware of, no action required | Noted in report for visibility |
| ✅ **Pass** | Within healthy thresholds | No concern |

## Overall Assessment Ratings

| Rating | Criteria |
|---|---|
| ✅ **Ready to implement** | No 🛑 Flags, ≤2 ⚠️ Warns |
| ⚠️ **Implementable with adjustments** | No 🛑 Flags but >2 ⚠️ Warns, OR 1 🛑 Flag with clear mitigation |
| 🛑 **Needs restructuring** | ≥2 🛑 Flags, or 1 🛑 Flag without clear mitigation |

---

## Integration with Writ

| Command | Relationship |
|---------|-------------|
| `/create-spec` | Run `/assess-spec` after creating a spec to validate its shape |
| `/edit-spec` | Run after major edits to re-validate; `/assess-spec` can invoke `/edit-spec` for splits |
| `/implement-spec` | Runs a **lightweight pre-flight assessment** (Checks 1-3 + context score) before showing the execution plan |
| `/verify-spec` | Complementary — assess-spec checks shape *before* building; verify-spec checks correctness *after* building |

**Recommended flow:**
```
/create-spec       # Shape the feature
/assess-spec       # Validate it's well-shaped for implementation
/implement-spec    # Build it (runs pre-flight assessment automatically)
/verify-spec       # Verify the built result
```
