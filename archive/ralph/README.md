# Ralph (retired)

Ralph was Writ's autonomous, opaque, unbounded CLI loop for multi-spec execution:
plan in Cursor (`/ralph plan`), hand off to a bash loop (`ralph.sh`) that piped a
single-iteration prompt (`PROMPT_build.md`) to a headless CLI agent, and review in
Cursor (`/ralph status`). It is **retired as of Phase 6** and preserved here for
historical comprehension only. Nothing in this folder is loaded by command
discovery, generated catalogs (`SKILL.md`), adapters, or config.

## What replaced it

Supervised multi-spec execution now runs through **`/implement-phase`**, which
absorbed Ralph's durable inventions with stronger guarantees:

| Ralph capability | Supervised replacement in `/implement-phase` |
|---|---|
| Fresh context per iteration | Fresh isolated per-spec execution lanes (branch + worktree) |
| Loose state file across iterations | `phase-execution-v2` state with atomic writes and read-only resume reconciliation |
| Skip-and-continue on failure | Bounded transient retry, then terminal-failure quarantine with dependent blocking |
| End-of-run summary | Categorical production health and honest, evidence-bound completion reporting |

Bounded single-spec autonomy is a **separate, explicitly supported** path:
`/implement-spec --recommend <one-spec>` (and `/create-spec --recommend`), which is
session-started, bound to one locked spec, finite, and gated by one SHA-bound
production approval. Multi-spec `/implement-phase --recommend` remains **excluded**
(see [ADR-013](../../.writ/decision-records/adr-013-recommended-autonomous-delivery.md)).

## Why it was retired

Opaque unbounded execution could not offer the isolation, resumability, and honest
evidence Writ now requires. See
[ADR-012 — Ralph deprecation](../../.writ/decision-records/adr-012-ralph-deprecation.md).

## Migration

There is **no compatibility reader and no state migration**. Existing `ralph-*.json`
run state is not read by any active command. **Finish or abandon any in-flight
`ralph-*.json` run before upgrading**, then drive remaining multi-spec work with
`/implement-phase`.

## Contents

- `ralph.md` — the retired `/ralph` command
- `ralph.sh` — the outer loop script
- `PROMPT_build.md` — the single-iteration prompt template
- `ralph-cli-pipeline.md` — gate mapping, back pressure, state protocol
- `ralph-state-format.md` — the `ralph-*.json` JSON schema
