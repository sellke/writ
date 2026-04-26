---
category: glossary
tags: [strategy, phase-4, adr-007]
created: 2026-04-24
related_artifacts:
  - .writ/decision-records/adr-007-team-audience-sequencing.md
  - .writ/specs/2026-04-24-phase4-production-grade-substrate/spec.md
---

# Dual-Use Test

## TL;DR

A Phase 4 feature passes the dual-use test when it helps solo Writ usage today and prepares the substrate for small-team collaboration later.

## Context

- Writ is currently optimized for a solo maintainer.
- The roadmap anticipates a future small-team audience but defers explicit team features until there is a concrete signal.
- Phase 4 substrate work must avoid speculative team-only scope.

## Detail

Use the dual-use test as a scope filter. If a proposed feature only helps future teams, defer it. If it only helps the current solo workflow and does not strengthen future collaboration, consider whether it belongs in the current phase.

The test does not require visible team UI. Shared knowledge, eval checks, generated manifests, and stable ownership metadata can all pass because they improve today's workflow while becoming useful collaboration infrastructure later.

## Related

- [ADR-007](../../decision-records/adr-007-team-audience-sequencing.md)
