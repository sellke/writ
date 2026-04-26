---
category: glossary
tags: [context-engine, agents, specs]
created: 2026-04-24
related_artifacts:
  - .writ/docs/context-hint-format.md
  - commands/implement-story.md
  - .writ/specs/2026-04-24-phase4-production-grade-substrate/user-stories/story-1-knowledge-ledger.md
---

# Context Hint

## TL;DR

A context hint is an index in a story file that points agents to the precise spec sections they need instead of duplicating the whole spec.

## Context

- The Context Engine introduced `## Context for Agents` blocks in story files.
- `/implement-story` parses those blocks during Step 2.
- Phase 4 knowledge loading reuses the same block as a keyword source.

## Detail

Context hints usually name error map rows, shadow paths, business rules, and experience anchors. The orchestrator resolves them into fetched context and routes relevant pieces to each agent.

Hints should stay short. They are pointers, not a second copy of the contract.

## Related

- [Context hint format](../../docs/context-hint-format.md)
- [Implement Story command](../../../commands/implement-story.md)
