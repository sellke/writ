# Story 1 Verification Checklist

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
- [ ] Follow-up dogfood task confirms the hook fires without prompt-side mention after Story 1 ships.

## Adapter Notes

- [x] Cursor adapter documents knowledge loading.
- [x] Claude Code adapter documents knowledge loading.
- [x] OpenClaw adapter documents knowledge loading.
