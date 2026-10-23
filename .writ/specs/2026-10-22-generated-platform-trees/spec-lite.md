# Generated Platform Trees (Lite)

> Source: .writ/specs/2026-10-22-generated-platform-trees/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** `scripts/gen-platform-trees.py` (Python 3.9 stdlib, dev-only) generates every per-platform file from source, appends a `## Capability Map` to each root instruction file from the adapter tool tables, fails on an unmapped capability or a vendor tool name in shipped text, and has `--check` and `coverage` modes wired into `eval.sh`.

**Implementation Approach:**
- Parse one tool table per adapter by heading (cursor § Native Tool Availability; claude-code § Tool Mapping → Quick Reference; codex § … → Quick reference — orchestration primitives; openclaw § Quick Reference). Name = leading identifier of column 1; mapping = column 2 (cursor: column 3); notes = last column. Malformed row → `fail`, nothing written; missing heading → `unverifiable`.
- Vocabulary: neutral = union of first-column names; every neutral name needs a row in all four adapters (`unmapped`); vendor-only = backticked identifiers in mapping cells minus neutral minus allowlist {Read, Write, Bash} (a token containing `://` is a URL, not an identifier; DEV-002); a vendor-only token in `commands/`, `agents/`, `skills/` → `vendor`.
- Story 1 repairs tables first: Codex `file_search` row; OpenClaw `readonly: true` folded into `Task`; `Plan Mode` row in all four (agent enters it: Claude Code `EnterPlanMode`; Cursor asks the user, with the command list in its `Used By` column and the mapping plus degradation sentence in `Purpose` (DEV-003); Codex/OpenClaw read-only conversation); one sentence in `create-spec.md`, `plan-product.md`, `new-command.md`.
- Generated: `cursor/writ.mdc` (frontmatter + comment + `system-instructions.md` body + map); `claude-code/CLAUDE.md` via `gen-claude-md.py` with a `{capability_map}` slot; `codex/AGENTS.md.template` from manifest + all skills + built-ins literal + map, no `adapters/` mention, < 16 KiB (the renderer fails closed on an `adapters/` mention or at 16 KiB, writing nothing; DEV-007); driver calls `gen-claude-agents.py` and `gen-codex-agent-tomls.py`.
- Tokens: `TARGETS` with identity `script_root: scripts` for cursor/claude-code/codex (no `commands/` output) and a `fixture` target (`${PLUGIN_ROOT}/scripts`) that writes full `commands/` + `skills/` to `--out-dir`, rewriting only `(python3|bash) scripts/<name>` lines.
- Check shape like `gen-claude-agents.py` (write mode summary `gen-platform-trees: <verdict> (<n> written, <r> reasons)`; `--check` carries the per-kind counts; DEV-004); `check_platform_trees` in eval.sh; `is_shippable_script` denylist entry (landed in Story 1 in `install.sh`, `update.sh`, and `unlink.sh`, byte-identical, because the CLI-contract tests derive the shipped set from it; DEV-001); install evidence bash test.

**Files in Scope:**
- `scripts/gen-platform-trees.py`, `scripts/tests/test_gen_platform_trees.py`, `scripts/tests/fixtures/platform-trees/`, `adapters/*.md` tool tables, `commands/{create-spec,plan-product,new-command}.md` (one sentence each), Plan Mode issue (S1)
- `cursor/writ.mdc`, `scripts/gen-claude-md.py`, `claude-code/CLAUDE.md` (S2)
- `codex/AGENTS.md.template` (S3)
- `scripts/eval.sh`, `scripts/tests/test_eval_platform_trees.sh`, `scripts/install.sh`, `scripts/update.sh` (S4)
- `scripts/tests/test_install_platform_trees.sh`, adapter-mappings issue, adapter install sections (S5)

**Error Handling:**
- Malformed row / empty table → `fail` with line; nothing written.
- Sub-generator exit ≥ 2 → `fail`, `reason: <gen> --check exited <rc>`.
- Hand edit to a generated file → `reason: stale <path>`; remedy names the driver.

**Integration Points:**
- After `2026-10-22-rendering-delegation-rows` (reads its canvas rows and records; adds no second tool table) and `2026-10-22-front-door` (catalogs include `/writ`; the Codex template takeover must preserve its row).
- `2026-10-22-plugin-distribution` adds real non-identity targets.

---

## For Review Agents

**Acceptance Criteria:**
1. All four adapters parse; neutral set equals the golden set; malformed rows and missing sections fail closed `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
2. Parity repairs and `Plan Mode` rows landed; three commands point at the adapter row; Plan Mode issue resolved `[AC-1.5]`
3. `cursor/writ.mdc` and `claude-code/CLAUDE.md` are generated with the map; prime-directive sync passes by construction `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
4. `codex/AGENTS.md.template` is generated, complete, free of `adapters/` mentions, under 16 KiB `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`
5. `--check`, `coverage`, and the fixture target behave per the technical spec; eval gains `check_platform_trees` with a mutation test; driver is dev-only `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`
6. Temp-project installs on cursor, claude, codex carry the map; adapter-mappings issue resolved `[AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5]`

**Business Rules:**
- Regenerate, never hand-edit; every file the driver renders itself names its generator, while `claude-code/CLAUDE.md` keeps `gen-claude-md.py`'s header and no comment (DEV-006).
- Only what differs is committed; identity targets write no command copies.
- Check shape: verdict, reasons, summary; nothing written when any reason exists, except a sub-generator's `stale`/`missing`/`absent`/`extra` output-state reasons, which are what write mode repairs (DEV-005).

**Experience Design:**
- Entry: edit an adapter row or agent, run the driver.
- Happy path: files rewritten, `pass`.
- Moment of truth: forgotten regeneration fails eval with the path and the remedy.
- Feedback: one reason per problem.
- Error: malformed input fails closed.

---

## For Testing Agents

**Success Criteria:**
1. `uv run --python 3.9 pytest` passes, including `test_gen_platform_trees.py`.
2. Bash loop passes, including `test_eval_platform_trees.sh` and `test_install_platform_trees.sh` (temp dirs only; never the Writ repo).
3. `bash scripts/eval.sh` (outside the sandbox): 0 findings.

**Shadow Paths to Verify:**
- **Happy path:** `--check` pass on the committed tree.
- **Nil input:** missing adapter heading → `unverifiable`, exit 0.
- **Empty input:** header-only table → `fail`.
- **Upstream error:** sub-generator exit ≥ 2 → `fail`, nothing written.

**Edge Cases:**
- `Task` variants collapse to one name; `Plan Mode` keeps its space.
- `` `Read` `` in prose is allowlisted; `` `TodoWrite` `` is a vendor hit.
- Prose `scripts/` mentions outside invocation lines are never rewritten.

**Test Strategy:**
- Fixture adapters and commands under `scripts/tests/fixtures/platform-trees/`; golden neutral set; mutation tests for eval; bash install test from a committed source copy.
