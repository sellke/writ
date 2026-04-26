---
category: decisions
tags: [markdown, source-of-truth, methodology]
created: 2026-04-24
related_artifacts:
  - AGENTS.md
  - system-instructions.md
  - .writ/specs/2026-04-24-phase4-production-grade-substrate/sub-specs/technical-spec.md
---

# Markdown As Instructions, Not Application Code

## TL;DR

Writ's source of truth is reviewed markdown: commands, agents, specs, adapters, ADRs, and knowledge entries.

## Context

- The repo has no app build step, dependency graph, or test suite.
- Product changes ship by changing command and agent markdown.
- Runtime state and derived artifacts must not replace the reviewed markdown contract.

## Detail

When adding substrate, prefer plain files that a maintainer can inspect in a PR. Bash scripts are acceptable for deterministic checks and generation, but the meaning of the workflow should remain in markdown wherever possible.

This keeps Writ portable and lets each adapter execute the same method with its own tool primitives.

## Related

- [AGENTS.md](../../../AGENTS.md)
- [Technical spec](../../specs/2026-04-24-phase4-production-grade-substrate/sub-specs/technical-spec.md)
