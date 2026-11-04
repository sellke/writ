---
category: lessons
tags: [phase-close, testing]
created: 2026-10-23
related_artifacts:
  - scripts/tests/test_agent_cli_contract.py
---

# Run pytest alone, never beside eval.sh or the bash tests in the same tree

## TL;DR

Run uv run pytest on its own, never concurrently with bash scripts/eval.sh or the bash test loop in the same checkout: test_agent_cli_contract.py's test_smoke_leaves_repo_unchanged snapshots the repository, and the other runs write to it, so concurrent runs fail it spuriously.

## Context

Recorded at phase close from evidence-bound knowledge writeback.

**Cited evidence:**

- Phase 14 rendering-delegation-rows lane: six test_smoke_leaves_repo_unchanged cases failed once under concurrent runs and passed solo
- scripts/tests/test_agent_cli_contract.py

## Related

- `scripts/tests/test_agent_cli_contract.py`
