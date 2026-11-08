# Claude Agent Generator (Lite)

> Source: .writ/specs/2026-10-20-claude-agent-generator/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** `scripts/gen-claude-agents.py` generates `claude-code/agents/writ-*.md` from `agents/*.md` + a frontmatter overlay, with `--check` and an eval check.

**Implementation Approach:**
- Mirror `scripts/gen-codex-agent-tomls.py`: write mode, `--check`, `--agents-dir`, `--out-dir`, check-shape output, exit 0/1/2.
- `OVERLAY` dict keyed by canonical stem: `file`, ordered `frontmatter` pairs, optional `suffix`. Seed from today's seven files verbatim.
- Output: frontmatter → generated-header HTML comment → canonical body (frontmatter + retired `model: "fast"` lines stripped) → suffix.
- Validate every stem has an overlay before the first write.

**Files in Scope:**
- `scripts/gen-claude-agents.py` — new generator
- `scripts/tests/test_gen_claude_agents.py` — new tests
- `claude-code/agents/writ-*.md` — regenerated; `writ-visual-qa.md` added
- `scripts/check-agent-parity.sh` — fold both generators' `--check`; drop visual-qa exemption
- `scripts/eval.sh` — `check_claude_agents` beside `check_codex_tomls`
- `scripts/tests/test_shell_check_shape.sh`, `test_jev_shadow_hooks.sh` — fixture/pin updates
- `adapters/claude-code.md`, `commands/refresh-command.md`, `.writ/docs/agent-cli-contract.md`, `scripts/tests/test_agent_cli_contract.py`

**Error Handling:**
- Unmapped stem → `reason: unmapped <stem>`, write nothing, exit 1
- Stale/missing/orphan → one `reason:` each, sorted by reported name, exit 1; orphan = a `writ-*.md` no current canonical stem generates
- Generator absent beside parity script → skip content check, note it in summary
- Generator `--check` rc ≥ 2 → parity drift reason

**Integration Points:**
- `/refresh-command --check-parity` reads parity line 1; never blocks
- `eval.sh` findings; CI

**Constraints:** Python 3.9 floor. Body passes through verbatim — no section filtering or `Task(...)` rewriting.

---

## For Review Agents

**Acceptance Criteria:**
1. `gen-claude-agents.py --check` passes on the committed tree; one canonical line changed → `fail` + `reason: stale <stem>` `[AC-1.2, AC-2.1]`
2. Unmapped stem in write mode leaves the output dir unchanged `[AC-1.3]`
3. `writ-coder.md` contains `MAX_SELF_FIX_ITERATIONS = 3` and the `boundary_map` rules; frontmatter matches today's values `[AC-2.2, AC-2.3]`
4. `writ-visual-qa.md` exists, read-only; parity script has no visual-qa exemption `[AC-2.1, AC-3.1]`
5. `check-agent-parity.sh` reports content drift as `reason:` lines; shape and exit codes unchanged; the fail summary reports `<m> missing counterpart(s), <c> content drift reason(s)` `[AC-3.2, AC-3.3]`
6. `eval.sh` reports a finding with a regenerate remedy when a Claude agent is stale `[AC-3.4]`

**Business Rules:**
- Generator is the only writer of `claude-code/agents/*.md`
- Body verbatim; overlay owns Claude metadata and suffix
- Agent names/filenames unchanged
- Parity check stays a warning

**Experience Design:**
- Entry: maintainer edits `agents/<stem>.md`
- Happy path: run generator → eval and parity pass
- Moment of truth: forgotten regenerate → eval names `python3 scripts/gen-claude-agents.py`
- Feedback: check-shape verdict / `reason:` / summary
- Error: `reason: unmapped <stem>`, nothing written

---

## For Testing Agents

**Success Criteria:**
1. Generator unit tests cover write, check pass, each reason kind, validate-before-write, usage error
2. Repo-level `--check` passes against real `agents/` and `claude-code/agents/`
3. Full `uv run pytest` (incl. `--python 3.9`), bash tests, and `eval.sh` green

**Shadow Paths to Verify:**
- **Happy path:** regenerate → byte-equal check passes
- **Nil input:** no `agents/` → parity `unverifiable`
- **Empty input:** frontmatter-only canonical → header + suffix only
- **Upstream error:** generator missing → parity skips content, eval finding

**Edge Cases:**
- Canonical `---` horizontal rules after frontmatter → preserved
- Orphan `writ-foo.md` → `reason: orphan writ-foo`

**Coverage Requirements:**
- New code: ≥80%; error paths: 100%

**Test Strategy:**
- pytest with `tmp_path`; bash fixture in `test_shell_check_shape.sh`; agent CLI contract smoke
