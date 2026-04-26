---
category: decisions
tags: [adapters, portability, commands]
created: 2026-04-24
related_artifacts:
  - .writ/specs/2026-04-24-phase4-production-grade-substrate/spec.md
  - .writ/decision-records/adr-006-non-degrading-destination.md
  - adapters/cursor.md
  - adapters/claude-code.md
  - adapters/openclaw.md
---

# Adapter Neutrality Is Non-Negotiable

## TL;DR

Writ commands describe workflows in platform-neutral terms; adapters translate mechanics for Cursor, Claude Code, and OpenClaw.

## Context

- Writ is distributed as markdown methodology, not a single runtime.
- Platform-specific execution APIs differ, but the workflow contract should not.
- Phase 4 depends on substrate features working identically across adapters.

## Detail

Command and agent files should name generic responsibilities first: read files, ask bounded questions, spawn agents, run shell checks, and update Writ artifacts. Adapter docs explain how each platform maps those responsibilities to concrete tools.

Do not add a feature that only works because one platform has a private runtime hook. If a platform can optimize the workflow, document that as an adapter detail while preserving the same command-level behavior elsewhere.

## Related

- [Phase 4 spec](../../specs/2026-04-24-phase4-production-grade-substrate/spec.md)
- [Cursor adapter](../../../adapters/cursor.md)
