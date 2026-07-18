# Model-Tier Delegation — User Stories

> **Spec:** `.writ/specs/2026-07-10-model-tier-delegation/spec.md`
> **ADR:** `.writ/decision-records/adr-014-model-tier-delegation.md` (created in Story 1)
> **Status:** Not Started
> **Total Stories:** 4

## Overview

A portable `model_tier` convention where **agents** carry an enforceable tier (`orchestration` → anchor/`inherit`, `capability` → floor/`fast`), resolved per-platform via native relative primitives, while **skills and commands** carry advisory-only tier metadata. No maintained model ranking (native abstractions only); relative semantics; graceful degradation. Corrects the originating issue's skill-carrier framing — the tier lives at the agent spawn boundary, the only place Writ passes a `model` parameter.

## Stories Summary

| # | Story | Status | Tasks | Priority | Dependencies |
|---|---|---|---|---|---|
| 1 | [Tier Contract + ADR-014](story-1-tier-contract-adr.md) | Not Started | 0/6 | High | None |
| 2 | [Agent Adoption](story-2-agent-adoption.md) | Not Started | 0/6 | High | Story 1 |
| 3 | [Adapter Resolution (2-Band Native)](story-3-adapter-resolution.md) | Not Started | 0/6 | High | Story 1 |
| 4 | [Authoring & Lint Integration + Docs](story-4-authoring-lint-docs.md) | Not Started | 0/6 | Medium | Stories 1, 2, 3 |

**Progress:** 0/24 tasks complete.

## Dependency Graph

```
Story 1 (contract + ADR) ──┬─→ Story 2 (agent adoption) ──┐
                           │                               │
                           └─→ Story 3 (adapter resolution)┤
                                                           ▼
                                              Story 4 (authoring + lint + docs)
```

**Parallel batches:**

- **Batch A:** Story 1 — foundation, must land first.
- **Batch B (deps on Story 1):** Stories 2 and 3 — can run concurrently; must agree on the tier→concrete-model resolution (2 asserts intent, 3 documents platform resolution).
- **Batch C (synthesis):** Story 4 — gates on 1, 2, 3.

## Story Descriptions

### Story 1 — Tier Contract + ADR-014
Define the `model_tier` frontmatter convention (two named tiers + reserved ordinal-offset form), document it in `system-instructions.md` and its byte-identical `cursor/writ.mdc` mirror, and record ADR-014 (agent-as-carrier, relative-not-absolute, staged resolver + rejected alternatives). No behavior change; contract and docs only.

### Story 2 — Agent Adoption
Add `model_tier` to all 7 agents (frontmatter + `manifest.yaml`), mapped from today's `model:` settings: `architecture-check-agent` + `user-story-generator` → `capability`; the other five → `orchestration`. A rename-to-portable with **zero behavioral regression** — every agent resolves to the same concrete model it uses today.

### Story 3 — Adapter Resolution (2-Band Native)
Document tier → native-resolution tables in `adapters/cursor.md` (`inherit`/`fast`), `adapters/codex.md` (mini ID / inherit), and `adapters/openclaw.md` (`model` param / omit), each with the warn-and-fall-back graceful-degradation rule. No maintained ranking; relative primitives only; reserved offsets clamp to floor.

### Story 4 — Authoring & Lint Integration + Docs
`/new-command` and `/new-skill` scaffold an advisory `model_tier:` field; the shared frontmatter lint validates tier values. Create `.writ/docs/model-tiers.md` (canonical explainer) and reference the convention from `README.md` and `AGENTS.md`.

## What's Out of Scope

Explicitly *not* in this spec — reserved for follow-up:

- **Refreshable per-platform model-family ranking + N-step (>2-band) resolution** — reserved by the contract, built only on evidence that band-collapse costs quality
- **Runtime anchor-model detection** beyond native `inherit`
- **Quality-regression eval harness** for capability-tier output (shipping on the `convention_only` posture)
- **Auto-downgrading** existing agents beyond preserving today's settings
- **Enforcing tier on commands/skills** — structurally impossible; advisory only

## How to Run This Spec

```bash
/implement-spec .writ/specs/2026-07-10-model-tier-delegation/
```

`/implement-spec` runs Story 1 first, then batches Stories 2 and 3, then Story 4 as synthesis.

## Quick Links

- [Spec (full)](../spec.md)
- [Spec (lite)](../spec-lite.md)
- [Technical sub-spec](../sub-specs/technical-spec.md)
- [Source issue](../../../issues/features/2026-07-10-model-tier-delegation.md)
- [ADR-009 (verb/noun/tool boundary)](../../decision-records/adr-009-command-agent-skill-boundary.md)
