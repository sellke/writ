# Agent CLI Contract (Lite)

> Source: .writ/specs/2026-10-12-agent-cli-contract/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Every script Writ ships follows one documented, test-enforced agent contract; six dev-only scripts stop shipping.

**Implementation Approach:**
- Two output shapes. Data tools: one JSON document; failure is JSON with `blocker` (or legacy `error`) and a non-zero exit. Check tools: first line `pass`/`fail`/`unverifiable`, `reason:` lines, summary last, exit 0/1/2.
- Usage errors: argparse default (exit 2, usage on stderr, empty stdout). A JSON blocker on stdout also passes.
- The contract test reads the shipped set by sourcing `is_shippable_script` from `scripts/install.sh`. Never keep a second list.
- Classification table in `.writ/docs/agent-cli-contract.md`: `Script | Shape | Allowances | Callers`.
- Fixes: JSON default + `--pretty`, old `--json` kept as a hidden no-op, callers updated in the same commit.
- Python 3.9 standard library only. No shared `_*` helper (those don't ship).

**Files in Scope:**
- `.writ/docs/agent-cli-contract.md` — new contract doc and table (S1)
- `.writ/decision-records/adr-029-agent-cli-contract.md` — dated amendment (S1)
- `scripts/install.sh`, `scripts/update.sh` — six-name exclusion arm, kept identical (S2)
- `commands/update-writ.md`, `.writ/docs/skills.md` — prose (S2)
- `scripts/tests/test_agent_cli_contract.py` — new (S3)
- `scripts/revert-resolve.py`, `scripts/knowledge-consolidate.py`, `commands/revert.md`, `commands/knowledge.md`, other flagged Python scripts + callers — conformance (S4)
- `scripts/lint-skill.sh`, `gen-skill.sh`, `check-agent-parity.sh`, `app-verify.py` + callers, codex TOMLs — conformance (S5)

**Error Handling:**
- Ship filter can't be sourced → test setup error naming `is_shippable_script`.
- No table → one setup error naming the doc.
- Modified dev-only script in an installed project → kept, stale warning (existing update behavior).

**Integration Points:**
- `/revert` and `/knowledge` read the changed defaults. `/retro` calls `knowledge-consolidate.py --json` (keeps working).
- `eval.sh` still runs the six dev-only scripts from the source tree.

See spec.md → ## Implementation Approach and sub-specs/technical-spec.md.

---

## For Review Agents

**Acceptance Criteria:**
1. The contract doc has all sections, and its table classifies every shipped script exactly once `[AC-1.1, AC-1.2, AC-1.3]`
2. ADR-029 carries the dated amendment, and rules 1–7 are unchanged `[AC-1.4]`
3. Neither install nor update ships the six. Update removes unmodified copies and warns on modified ones `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`
4. No shipped doc or command points at the six by path `[AC-2.5]`
5. The contract test fails with script + rule + fix for each violation type, and strict xfail tracks known debt `[AC-3.1, AC-3.2, AC-3.3]`
6. `KNOWN_VIOLATIONS` shrinks to Story 5's entries, then to empty; the suite is green on 3.9 and later `[AC-3.4, AC-4.3, AC-5.5]`
7. `revert-resolve` and `knowledge-consolidate` default to JSON. `--pretty` reproduces the old output byte for byte, and callers are updated `[AC-4.1, AC-4.2, AC-4.4]`
8. Python check tools print the verdict first in every mode; shell scripts and app-verify follow; atomic writes; callers updated `[AC-4.5, AC-5.1, AC-5.2, AC-5.3, AC-5.4]`
9. The origin issue is resolved, and the script-location issue is filed `[AC-5.5]`

**Business Rules:**
- Scope = what `install.sh` ships. Each script has exactly one table row (data or check).
- No agent-CLI launches. Waits only in `bounded-wait` rows, with a timeout.
- Network imports only in `network: opt-in` rows (jev-judge, app-verify).
- A default-output change carries its caller edits in the same commit.
- `KNOWN_VIOLATIONS` is strict debt and empty at close.

**Experience Design:**
- Entry: an agent runs `python3 scripts/<tool>.py …`, or a maintainer adds a script.
- Happy path: parse JSON or the verdict line and branch on the exit code.
- Moment of truth: forgetting the contract fails pytest with a named fix.
- Feedback: failure messages give script, rule, and fix.
- Error: usage on stderr; structured blocker or `unverifiable` on stdout.

---

## For Testing Agents

**Success Criteria:**
1. `uv run pytest scripts/tests/test_agent_cli_contract.py` passes with `KNOWN_VIOLATIONS == {}`.
2. Full pytest (3.9 and default), the bash tests, and `bash scripts/eval.sh` are green.
3. `install.sh --dry-run` into a temp project lists none of the six.

**Shadow Paths to Verify:**
- **Happy path:** conforming script passes all checks.
- **Nil input:** shipped script without a table row → completeness failure.
- **Empty input:** no table → single setup error.
- **Upstream error:** `is_shippable_script` can't be sourced → setup error.

**Edge Cases:**
- `"socket hang up"` string literal in build-smoke.py → not a network import.
- recommend-state.py JSON blocker on bad flag → conforming.
- Fixed script still listed in `KNOWN_VIOLATIONS` → strict XPASS failure.
- Modified dev-only copy on update → kept with stale warning.

**Test Strategy:**
- Rule checks proven with fixture scripts in `tmp_path`, never by breaking real scripts.
- Shape smoke runs read-only invocations from a temp cwd; `git status` unchanged.
- Shell tests use temp projects for install/update.
