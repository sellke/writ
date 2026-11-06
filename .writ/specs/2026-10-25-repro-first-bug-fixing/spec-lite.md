# Repro-First Bug Fixing (Lite)

> Source: .writ/specs/2026-10-25-repro-first-bug-fixing/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** A bug path in `skills/tdd-cycle/SKILL.md`: failing repro on the bug's surface, committed alone with a `Repro:` trailer before the fix; `scripts/repro-order.py check` re-derives the order; a `### Repro` report block; reached by `/prototype` and `/implement-story`; switched off by `- **Repro First:** off` in `.writ/config.md`.

**Implementation Approach:**
- Order: Story 1 script, Story 2 skill, Story 3 coding agent, Story 4 consumers and integration.
- Script: stdlib Python 3.9, check shape (line 1 verdict, `reason:` lines, summary last; exit 0/1/2). Rules and reason codes: technical-spec.md § Check Rules.
- Switch read first; `off` → `unverifiable`, `reason: repro-first off`, before any git call.
- Consumers get one bug-path line each; the integration skill cherry-picks ordered commits.
- Regenerate trees with `python3 scripts/gen-platform-trees.py`; never hand-edit them.

**Files in Scope:**
- `scripts/repro-order.py`, `scripts/tests/test_repro_order.py` (new)
- `scripts/tests/test_repro_first_wiring.py` (new)
- `skills/tdd-cycle/SKILL.md` — `### Bug fixes: repro first`
- `agents/coding-agent.md` — Requirements 1 and 3, `### Repro` block
- `commands/prototype.md` Step 3; `commands/implement-story.md` Gate 1 (bug-path lines only)
- `skills/subagent-worktree-integration/SKILL.md` — ordered-commits paragraph
- `.writ/docs/agent-cli-contract.md`, `.writ/docs/config-format.md`, `scripts/tests/test_agent_cli_contract.py` (one row each)

**Error Handling:**
- Unreadable config, bad rev, base not ancestor, no git → exit 2, stdout empty
- Merge in range → `unverifiable`, `merge_in_range`
- Cherry-pick conflict → abort, copy files, say the order was lost

**Integration Points:**
- Front door routes bugs to `/prototype --no-diverge`; `/revert` finds repro/fix commits by `Ref:` footer.
- `2026-10-25-gate-upgrade-removal-measurement` flips `Repro First` and uses § Removal Inventory.

**Do not touch:** `/prototype` Step 2.5, Gate 0, Gate 2.5, Gate 3, `commands/why.md`, `commands/writ.md`, reviewer and evaluator agents.

---

## For Review Agents

**Acceptance Criteria:**
1. `repro-order.py check` passes a correct repro-then-fix history and fails each broken one with its reason code `[AC-1.1, AC-1.2]`
2. Switch `off` makes the check print `unverifiable` / `reason: repro-first off` and exit 0 `[AC-1.3]`
3. The skill's bug path states recognition, surface, valid red, commit order, and the no-repro escape, and passes `lint-skill.sh` `[AC-2.1, AC-2.2, AC-2.5]`
4. Every coding agent report has a `### Repro` block in one of four forms `[AC-3.2, AC-3.3]`
5. Both consumers re-run the check after integration; `/implement-story` maps `fail` to `⚠️ DEGRADED` `[AC-4.1, AC-4.2]`
6. Integration carries ordered commits by cherry-pick; every Removal Inventory row is pinned by a test `[AC-4.3, AC-4.4]`

**Business Rules:**
- Bug: issue `**Type:** Bug` / `.writ/issues/bugs/`, Origin citing one, or wording that existing behavior is wrong
- Repro commit: test files only, `Repro:` trailer; fix commits never touch repro files
- Story runs: repro and fix commits carry `Ref:` to the story file
- Runs on every bug fix; adds no spawn, no loop, no loop increment

**Experience Design:**
- Entry: `/prototype --no-diverge`, a bug issue, or a story from a bug spec
- Happy path: repro fails → commit → fix passes → commit → check `pass`
- Moment of truth: same command failing then passing, two SHAs in order
- Feedback: `### Repro` block; `repro-order:` line in the summary
- Error: `fail` with `reason:` lines; `Repro: none: <reason>` when unreproducible

---

## For Testing Agents

**Success Criteria:**
1. `uv run --python 3.9 pytest scripts/tests/test_repro_order.py scripts/tests/test_repro_first_wiring.py` green
2. `bash scripts/lint-skill.sh` passes on both touched skills
3. `python3 scripts/gen-platform-trees.py --check` passes; `bash scripts/eval.sh` 0 findings

**Shadow Paths to Verify:**
- **Happy path:** repro → fix → `pass`
- **Nil input:** no `--base` → exit 2, stdout empty
- **Empty input:** `base == head` → `fail`, `no_repro_commit`
- **Upstream error:** no git / not a repo → exit 2

**Edge Cases:**
- Two repro commits → each needs a later source commit
- Repro test renamed later → `repro_test_modified`
- `.writ/`-only commits → ignored
- Tests outside known patterns → `--test-glob`

**Coverage Requirements:**
- Every rule and reason code has a fixture test
- Every Removal Inventory row has a wiring assertion

**Test Strategy:**
- Fixture git repos in temp dirs (stdlib), text checks on markdown
