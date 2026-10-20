# Knowledge Consolidation Proposal (dry-run)

Scanned 6 entries across decisions, conventions, glossary, lessons.

## Proposed merges (merge, never append)

- **lessons** / canonical `2026-01-01-retry-quarantine-b` — Retries And Quarantine For Recoverable Failures
  - replaces: 2026-01-01-retry-quarantine-a
  - duplicate signal: token overlap 0.947 (>= 0.50)

## Contradictions — surfaced for human review, never auto-resolved

- **conventions**: `2026-01-01-indent-spaces` vs `2026-01-01-indent-tabs` (subject overlap 0.600)
  - signal: high subject overlap with a negation-asymmetric assertion
  - `2026-01-01-indent-spaces`: Never use tabs for indentation in this codebase; use spaces.
  - `2026-01-01-indent-tabs`: Always use tabs for indentation in this codebase.

## Stale flags — observable signal only, awaiting explicit retirement

- **decisions** `2026-01-01-dangling`
  - all related_artifacts missing on disk: gone/removed-one.md, gone/removed-two.md

## Skipped (malformed — never rewritten or dropped)
- `{TMP}/.writ/knowledge/glossary/broken.md`: missing frontmatter

## Preview diff (no files written)

```diff
--- a/.writ/knowledge/lessons/2026-01-01-retry-quarantine-b.md
+++ b/.writ/knowledge/lessons/2026-01-01-retry-quarantine-b.md
@@ -3,6 +3,8 @@
 tags: [retries, quarantine, phase]
 created: 2026-01-01
 related_artifacts: []
+replaces:
+  - 2026-01-01-retry-quarantine-a
 ---
 
 # Retries And Quarantine For Recoverable Failures
--- a/.writ/knowledge/lessons/2026-01-01-retry-quarantine-a.md
+++ b/.writ/knowledge/lessons/2026-01-01-retry-quarantine-a.md
@@ -1,20 +1,9 @@
 ---
 category: lessons
-tags: [retries, quarantine, phase]
 created: 2026-01-01
-related_artifacts: []
+superseded_by: 2026-01-01-retry-quarantine-b
 ---
 
-# Bounded Retries Keep Failures Recoverable
+# Superseded
 
-## TL;DR
-
-Bounded retries plus quarantine keep partial failures recoverable without contaminating the shared phase branch.
-
-## Context
-
-- Captured for testing.
-
-## Detail
-
-Bounded retries plus quarantine keep partial failures recoverable without contaminating the shared phase branch during phase execution.
+Merged into [Retries And Quarantine For Recoverable Failures](../lessons/2026-01-01-retry-quarantine-b.md).
```

