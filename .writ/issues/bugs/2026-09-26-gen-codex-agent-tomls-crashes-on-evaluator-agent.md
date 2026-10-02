# gen-codex-agent-tomls.py crashes on evaluator-agent

> **Type:** Bug
> **Priority:** Normal
> **Effort:** Small
> **Created:** 2026-09-26
> **spec_ref:** .writ/specs/archive/2026-09-26-arch-lint-and-follow-ups/spec.md

## TL;DR

`python3 scripts/gen-codex-agent-tomls.py` exits with `SystemExit` on `evaluator-agent`, because its `PURPOSES` and `SANDBOX` tables have no entry for it. It has already rewritten three unrelated TOMLs by the time it fails.

## Current State

- `2026-09-26-drift-arch-guards` Story 3 regenerated `codex/agents/{evaluator,review}-agent.toml` by calling the generator's functions in-process (drift DEV-010).
- Before that, every TOML in `codex/agents/` was out of sync with its `agents/*.md` source; `evaluator-agent.toml` was a hand-shortened 1.9 KB body.
- `adapters/codex.md` and task text still document the CLI as the regeneration path.

## Expected Outcome

- `evaluator-agent` has `PURPOSES` and `SANDBOX` (`read-only`) entries.
- The CLI regenerates every TOML without error, and the rest are brought back in sync with their sources.
- A test runs the CLI end to end on a temp copy.

## Relevant Files

- `scripts/gen-codex-agent-tomls.py`
- `scripts/tests/test_gen_codex_agent_tomls.py`
- `codex/agents/*.toml`

## Resolution

2026-09-26, commit 60f10a9 (spec `2026-09-26-arch-lint-and-follow-ups`, Story 1). `evaluator-agent` is mapped, every stem is validated before any write, all 8 TOMLs were regenerated, and `gen-codex-agent-tomls.py --check` runs in `eval.sh` as `codex-tomls`.
