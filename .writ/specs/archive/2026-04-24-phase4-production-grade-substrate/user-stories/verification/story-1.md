# Story 1 Verification Checklist

> **Story:** [Knowledge Ledger v1](../story-1-knowledge-ledger.md)
> **Date:** 2026-04-24

Manual verification for Knowledge Ledger v1.

## Schema And Decision Tree

- [x] `.writ/knowledge/README.md` includes the what-goes-where decision tree for ADRs, research, specs, and knowledge.
- [x] README documents the required frontmatter fields: `category`, `tags`, `created`, `related_artifacts`.
- [x] README documents category directories and filename conventions, including glossary files without date prefixes.
- [x] Backfilled entries use conformant frontmatter and category-matching directories.

## Command Behavior

- [x] `commands/knowledge.md` documents `/knowledge "summary"`.
- [x] `commands/knowledge.md` documents `--category=X`.
- [x] `commands/knowledge.md` documents `--list [category]`.
- [x] `commands/knowledge.md` documents `--read <slug>`.
- [x] `commands/knowledge.md` refuses malformed entries before writing and names missing fields.
- [x] Confirmation matches the terse `/create-issue` style.

## Agent Loading

- [x] `commands/implement-story.md` Step 2 defines keyword extraction from story title, `## Context for Agents`, and files in scope.
- [x] `commands/implement-story.md` defines grep-based `.writ/knowledge/` matching and a ~2KB `knowledge_context` cap.
- [x] Architecture, coding, and review agents accept optional `knowledge_context`.
- [x] Implementation-side validation: keyword extraction, grep selection, ≤2KB cap, and per-agent routing reviewed and confirmed wired. Organic confirmation tracked at [`2026-04-26-story-1-knowledge-loading-organic-validation`](../../../../issues/improvements/2026-04-26-story-1-knowledge-loading-organic-validation.md) (next Phase 5 feature; 90-day ADR-005 review as formal recheck).

## Adapter Notes

- [x] Cursor adapter documents knowledge loading.
- [x] Claude Code adapter documents knowledge loading.
- [x] OpenClaw adapter documents knowledge loading.
