# Agent CLI Contract

> **Status:** Not Started
> **Created:** 2026-10-12
> **Owner:** @AdamSellke
> **Dependencies:** []
> **Amends:** [adr-029-agent-cli-contract](../../decision-records/adr-029-agent-cli-contract.md) rules 1 and 2
> **Origin:** Promoted from issue: `.writ/issues/features/2026-10-12-agent-facing-writ-cli.md`. ADR-029 decided that Writ's agent CLI is the per-workflow scripts it already ships, held to one contract. Discovery found that two output shapes already exist and that commands depend on both, so ADR-029 rule 1 ("JSON by default") is amended to allow both. Usage errors follow pstack's `orch` (help on stderr, non-zero exit). Six dev-only scripts stop shipping.

## Specification Contract

**Deliverable:** Every script Writ ships to installed projects follows one documented, test-enforced agent contract. Dev-only scripts stop shipping.

**Must Include:** A blocking pytest contract test that fails when a shipped script breaks the contract or isn't classified.

**Hardest Constraint:** Changing a script's default output breaks the command files that parse it. Each output fix must update its callers in the same commit.

**🎯 Experience Design:**
- **Entry point:** An agent following a Writ command runs `python3 scripts/<tool>.py <subcommand> …`, or a maintainer adds a new script under `scripts/`.
- **Happy path:** The agent reads one JSON document (data tool) or a verdict line followed by `reason:` lines (check tool) and branches on the exit code. It never parses prose.
- **Moment of truth:** A maintainer adds a script and forgets the contract. `uv run pytest` fails and names the missing classification row or the rule that was broken.
- **Feedback model:** Pytest failure messages name the script, the rule, and the fix. `KNOWN_VIOLATIONS` shows the remaining debt until it is empty.
- **Error experience:** Bad arguments print usage on stderr, nothing on stdout, and exit non-zero. Runtime failures print a structured blocker (data) or `unverifiable` plus a reason (check) on stdout.

**📋 Business Rules:**
- Contract scope is every script `install.sh` ships. After Story 2, that set is exactly the agent-facing scripts.
- Each shipped script has one row in the classification table in `.writ/docs/agent-cli-contract.md`: `data` or `check`, plus any allowances (`network: opt-in`, `bounded-wait`). A shipped script without a row fails the test.
- A data tool prints one JSON document on stdout. On failure it prints a JSON object carrying `blocker` (preferred) or `error` (legacy, accepted) and exits non-zero.
- A check tool prints `pass`, `fail`, or `unverifiable` as the first stdout line, then optional `reason:` and detail lines, then a summary line. It exits 0 when the check ran (`pass` or `unverifiable`), 1 on `fail`, and 2 on a usage error or a check that could not start. *(Amended 2026-10-12, drift-log Story 3 DEV-001: matches the existing check scripts and gates.)*
- Bad arguments: non-zero exit, usage on stderr, and stdout either empty or a JSON blocker. Nothing structured is required.
- A script never starts an agent or model CLI and never waits without a bound. A bounded wait on a process the script started, or on a call it made, is allowed when it has a timeout and is marked `bounded-wait`.
- No network import outside rows marked `network: opt-in`.
- When a default output format changes, every caller in `commands/`, `agents/`, `skills/`, `adapters/`, and `.writ/docs/` is updated in the same commit. An old `--json` flag stays accepted as a no-op.
- Python 3.9 floor and standard library only. No shared helper module, because `_*` files don't ship.

**Success Criteria:** `uv run pytest scripts/tests/test_agent_cli_contract.py` passes with `KNOWN_VIOLATIONS` empty. The full pytest suite, the bash tests, and `bash scripts/eval.sh` are green on Python 3.9 and later. `bash scripts/install.sh --dry-run` lists none of the six dev-only scripts.

**Scope Boundaries:**
- Included: contract doc, ADR-029 amendment, ship-filter change, contract test, conformance fixes and their caller updates.
- Excluded: a `writ` umbrella binary or dispatcher (deferred by ADR-029); moving scripts out of project-root `scripts/` (separate issue); converting check tools to JSON; JSON blockers for argparse errors; upstream-contribution tooling.

**⚠️ Technical Concerns:**
- `knowledge-consolidate.py`'s markdown output is shown to the user by `/knowledge`. Switching it to JSON moves rendering into the command. What the user sees must stay the same.
- Static checks are heuristics (import and string scans). They catch regressions but don't prove conformance. Per-script tests still own the success-output shape.
- Data tools report failures in two JSON forms: `{"blocker": …}` and `{"schema": …, "error": …}`. Unifying them would break eval checks and commands that read `error`. The contract accepts both and requires `blocker` for new scripts.

**💡 Recommendations:**
- Classify by reading each script's `main()` and its callers, not by name.
- Fix one script per commit, each paired with its caller edits, so every change can be reverted on its own.

## Experience Design

### Who uses it

- **Agents** running Writ commands in an installed project. They need output they can parse without guessing.
- **The maintainer**, adding or changing scripts. They need the test to catch contract breaks before review.

### State Catalog

| State | What the agent or maintainer sees |
|---|---|
| Conforming script, success | Data: one JSON document, exit 0. Check: `pass` first line, summary last, exit 0. |
| Conforming script, runtime failure | Data: JSON with `blocker` or `error`, exit non-zero. Check: `fail` (exit 1) or `unverifiable` with `reason:` (exit 0). |
| Bad arguments | Usage on stderr, empty stdout, exit non-zero. |
| New script, no table row | Contract test fails: `<script> is shipped but has no row in .writ/docs/agent-cli-contract.md`. |
| Script imports a network module without `network: opt-in` | Contract test fails, naming the module and the row to change. |
| Script names an agent CLI (`claude`, `codex`, `cursor-agent`) as a launch target | Contract test fails. |
| Known violation, not yet fixed | Test is xfail with the reason recorded in `KNOWN_VIOLATIONS`. The suite stays green. |
| Known violation fixed but still listed | xfail is strict, so the test fails until the entry is removed. |
| Dev-only script in an installed project after update | `update.sh` / `/update-writ` remove it if unmodified, or flag it as stale if modified. |

### Interaction Patterns

- Contract test failure messages start with the script name and end with the fix ("add a row", "mark `network: opt-in`", "remove from KNOWN_VIOLATIONS").
- The classification table is the one place a reader learns what each script prints.

## Business Rules (Expanded)

1. **Scope follows the ship filter.** The test reads the shipped set by running `is_shippable_script` from `scripts/install.sh` over `scripts/*`. It never keeps its own list, so the filter and the test can't drift.
2. **Classification table format.** It is a markdown table in `.writ/docs/agent-cli-contract.md` with columns `Script | Shape | Allowances | Callers`. `Shape` is `data` or `check`. `Allowances` is empty or a comma list from `network: opt-in`, `bounded-wait`. The test parses it.
3. **Data shape.** stdout holds exactly one JSON value on success. When the tool cannot do its job: a JSON object with a top-level `blocker` (`{code, summary}`) or `error` key, and a non-zero exit. A tool whose result is a verdict may exit non-zero with its normal document (`ac-trace.py`, `exit-criteria.py`). Human-readable output only behind `--pretty`.
4. **Check shape.** stdout line 1 is exactly `pass`, `fail`, or `unverifiable`. The last line is a summary. Exit 0 when the check ran (`pass` or `unverifiable`), 1 on `fail`, 2 on usage or could-not-start. An optional `--json` may print a JSON object instead of the verdict lines, or after the summary as the last line. *(Amended 2026-10-12: was 0/1/2 for pass/fail/unverifiable; `--json` placement amended by Story 5 drift DEV-001.)*
5. **Usage errors.** argparse's default (exit 2, usage on stderr, empty stdout) conforms. A JSON blocker on stdout, as `recommend-state.py` prints, also conforms. Shell scripts: non-zero exit with usage on stderr.
6. **No agent spawning.** No shipped script passes `claude`, `codex`, `cursor-agent`, `gemini`, or `openclaw` as a process to launch.
7. **Bounded waits only.** `time.sleep` or `while True` is allowed only in rows marked `bounded-wait`, and that script must enforce a timeout.
8. **Network opt-in.** `urllib`, `http.client`, `socket`, or `requests` imports are allowed only in rows marked `network: opt-in`, and the opt-in must be documented (ADR-027 double opt-in, or a local readiness probe for `app-verify.py`).
9. **Caller updates travel with the change.** Any default-output change edits its callers in the same commit. A removed flag stays accepted as a no-op.
10. **`KNOWN_VIOLATIONS` is strict debt.** Each entry is `(script, rule, reason)`. xfail is `strict=True`, so a fixed violation fails until it is delisted. The list is empty at spec close.

## Detailed Requirements

### Story 1: Contract doc and ADR amendment
- New `.writ/docs/agent-cli-contract.md` covering the two shapes, usage errors, bounded waits, network opt-in, files as canonical state, single writer, stdlib only, and the classification table for every shipped script, built from reading each `main()` and its callers.
- ADR-029: dated amendment under rules 1 and 2 recording the two shapes, the usage-error rule, the bounded-wait clarification, and the `blocker`/`error` acceptance. Rules text stays; the amendment note follows it (ADR-028 style).
- `/new-skill`'s script guidance gets a one-line pointer to the contract doc only if it already discusses adding scripts; otherwise no command edits.

### Story 2: Stop shipping dev-only scripts
- Exclude `pipeline-baseline.py`, `measure-invocation.py`, `harness-cost.py`, `lean-decision.py`, `prune-ledger.py`, `spawn-cap.py` in `is_shippable_script` in both `scripts/install.sh` and `scripts/update.sh`.
- Update the `/update-writ` exclusion prose (`commands/update-writ.md` § Step 3).
- Check `.writ/docs/*.md`, which ship, for instructions to run these scripts. `skills.md:330` mentions `measure-invocation.py` descriptively; reword it if it implies the script exists in an installed project.
- Extend the install/update shell tests so the six are absent from a fresh install and from the manifest, and an unmodified installed copy is removed as stale on update.

### Story 3: Contract test
- `scripts/tests/test_agent_cli_contract.py`, parametrized per shipped script:
  1. Table completeness (both directions: every shipped script has a row, and every row is a shipped script).
  2. `--help` exits 0 (Python) or prints usage (shell).
  3. A bad flag (`--zz-contract-probe`) exits non-zero with empty stdout.
  4. Static: network imports only under `network: opt-in`; no agent-CLI launch literals; `sleep` / `while True` only under `bounded-wait`.
  5. Shape smoke: for scripts with a no-side-effect invocation in this repo (listed in the test), run it and assert the declared shape.
- `KNOWN_VIOLATIONS` filled from the first red run, each entry with a reason. Runs on Python 3.9.

### Story 4: Data tools and Python check tools conform
- Fix each Python `KNOWN_VIOLATIONS` entry except `app-verify.py`, one script per commit, with callers: `revert-resolve.py` (JSON default, `--pretty`, `--json` kept as no-op; update `/revert`), `knowledge-consolidate.py` (JSON default with `--pretty` for the markdown report; `/knowledge` keeps showing the same report), and the scripts Story 1's audit flagged (change-surface, boundary-map, arch-lint, goal-emit, verdict-provenance, review-panel, gen-codex-agent-tomls, test-integrity).
- `roadmap-sync.py` and `goal-emit.py` write atomically.

### Story 5: Shell scripts and app-verify conform
- *Added 2026-10-12 (drift-log DEV-001, DEV-002): the maintainer kept the check rule strict, every mode included, and split the conformance work.*
- `lint-skill.sh`, `gen-skill.sh`, `check-agent-parity.sh`: verdict line first, summary last, exit 0 when the check ran, 1 on `fail`, 2 on usage; `--help` prints usage and an unknown flag is a usage error. `/refresh-command` keeps treating parity drift as a warning.
- `app-verify.py`: bare verdict on line 1, `feature: <id>` lines from `touched`, summary last; every Gate 4.5 caller and the codex TOML copies move with it.
- The list ends empty. Append `## Resolution` to the origin issue. File `.writ/issues/improvements/2026-10-12-script-install-location.md` (ADR-029 step 6).

## Implementation Approach

- **No new runtime code shared across scripts.** Each fix stays inside its script.
- **Test reads the real ship filter.** It runs a bash one-liner that sources the `is_shippable_script` function out of `install.sh`, the way `test_update_claude_md.sh` stubs helpers, and feeds it each file name. This avoids a second copy of the list.
- **Table parsing is plain markdown.** It parses the first table under `## Classification` in the contract doc, with the same parsing style as existing doc-reading tests (`test_architecture_lint_doc.py`).
- **Ordering:** Stories 1 and 2 are independent. Story 3 needs both (table and final ship set). Story 4 needs 3. Story 5 needs 4.
- **Verification:** `uv run pytest`, `uv run --python 3.9 pytest`, bash tests, `bash scripts/eval.sh` (outside the sandbox), `install.sh --dry-run` and `update.sh --dry-run` into a temp project.
