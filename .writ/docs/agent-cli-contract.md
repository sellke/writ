# Agent CLI Contract

> Decision: [ADR-029](../decision-records/adr-029-agent-cli-contract.md), amended 2026-10-12
> Applies to: every script Writ installs into a project's `scripts/` folder

Writ commands, agents, and skills tell agents to run scripts such as `python3 scripts/spec-status.py scan`. This doc states what every one of those scripts promises, so an agent can parse the output and branch on the exit code without reading prose. The table at the end says which shape each script prints.

## Scope

The contract covers every shipped script. A shipped script is a `*.py` or `*.sh` file in Writ's `scripts/` folder that `is_shippable_script` in `scripts/install.sh` accepts. `scripts/update.sh` uses the same filter.

- The filter also ships `jev-thresholds.json`. It is a data file that `jev-judge.py` reads, not a script, so it has no row.
- Lifecycle scripts (`install.sh`, `update.sh`, and the like), `eval*` checks, `sweep-*` tools, and `_*` helper modules never ship, so the contract does not cover them.
- Dev-only scripts for measuring and evaluating Writ itself stay in the Writ source repo. They do not ship and have no row. The note under the Classification table names them.

## Data shape

A data tool answers a question with structured data.

- On success it prints exactly one JSON document on stdout and exits 0.
- When the tool cannot do its job, it prints one JSON object on stdout and exits non-zero. The object has a top-level `blocker` key holding `{"code": …, "summary": …}`. Older tools put the failure under a top-level `error` key instead. The contract accepts both. New scripts use `blocker`.
- A tool whose result is itself a verdict may exit non-zero with its normal JSON document, for example `ac-trace.py` exits 1 when it reports findings. Read the document, not just the exit code.
- Human-readable output appears only behind `--pretty`. JSON is never behind a flag.
- A tool that used to need `--json` still accepts it as a no-op, so old command files keep working.

## Check shape

A check tool answers "does this pass?".

- Line 1 of stdout is exactly `pass`, `fail`, or `unverifiable`, with nothing else on the line.
- `reason: …` lines and other detail lines may follow.
- The last line is a one-line summary, usually `<tool>: <verdict> (…)`.
- The exit code says whether the check ran: 0 when it ran (line 1 says `pass` or `unverifiable`), 1 for `fail`, 2 for a usage error or a check that could not start. Branch on line 1, not on exit 0 alone.
- A check tool may offer `--json` to print one JSON object instead of the verdict lines. The exit code rule still applies.
- Every subcommand and mode of a check tool prints in this shape, including modes that write files.

## Usage errors

Bad arguments (an unknown flag, a missing required option) are a usage error.

- Exit non-zero. Print usage on stderr. Leave stdout empty.
- argparse's default behavior (exit 2, usage on stderr) already conforms.
- A script may print a single JSON blocker object on stdout instead of leaving it empty. `recommend-state.py` does this.
- Shell scripts: exit non-zero and print usage on stderr.

This matches pstack's `orch`, which prints help on stderr and exits non-zero. A usage error never needs a structured payload.

## Never spawn or wait unbounded

A script handles one invocation and exits. This applies ADR-028's runtime boundary (no daemon, no state kept between runs) to every shipped script, and follows pstack's `orch` rule that the CLI never spawns, waits, or wakes anything.

- A script never starts an agent or model CLI: `claude`, `codex`, `cursor-agent`, `gemini`, `openclaw`. Spawning agents is the harness's job. Repeating work on a schedule is the harness's loop or schedule feature.
- A script may run the commands its workflow needs, such as `git` or a build command a project recipe names.
- A script may wait only on a process it started or a call it made, and only with a timeout or an attempt cap. Its row must carry `bounded-wait`.
- The contract test treats any `time.sleep` call or `while True` loop as a wait. Write other loops with the bound in the loop itself (`for`, or `while <condition>`), not `while True`.

## Network

A default run makes no network call.

- The contract test scans imports for these modules: `urllib.request`, `urllib.error`, `http.client`, `socket`, `requests`. A script may import one only if its row carries `network: opt-in`.
- `urllib.parse` is exempt. It splits URLs and opens no connection.
- The opt-in must be documented. `jev-judge.py` uses ADR-027's double opt-in (a `Judgment Provider` line in `.writ/config.md` and that backend's API key in the environment). `app-verify.py` probes a local port on the app it launched to see whether the app is ready.

## State

- Plain files under `.writ/` are the system of record: markdown, JSON, or TSV. A person or agent can read and repair them without the script.
- Each state file has one writer. Write atomically: write a temp file, then rename it over the target.
- Scripts keep nothing in memory between runs and run no daemon.

## Runtime

- Python scripts use only the standard library and run on Python 3.9 or later.
- Shell scripts use POSIX shell features. The shipped shell scripts run under `bash`.
- Each script stands alone. There is no shared helper module, because `_*` files do not ship.

## Adding a script

These steps apply in the Writ source repo.

1. Decide whether it ships. A script ships only when a command, agent, or skill tells an agent to run it by path. A dev-only tool needs a case arm in `is_shippable_script` in both `scripts/install.sh` and `scripts/update.sh`.
2. Pick the shape, data or check, and follow that section.
3. Add a row to the Classification table. Add `network: opt-in` or `bounded-wait` only if the script needs it.
4. Document every subcommand in `--help` and add tests under `scripts/tests/`.
5. Run `uv run pytest scripts/tests/test_agent_cli_contract.py`. It fails when a shipped script has no row or breaks a rule, and names the script, the rule, and the fix.

## Classification

| Script | Shape | Allowances | Callers |
|---|---|---|---|
| `ac-trace.py` | data |  | commands/create-spec.md, commands/edit-spec.md, commands/verify-spec.md |
| `app-verify.py` | check | network: opt-in, bounded-wait | commands/implement-story.md, commands/create-uat-plan.md, agents/coding-agent.md, agents/visual-qa-agent.md, adapters/codex.md |
| `arch-check.py` | check |  | commands/implement-story.md |
| `arch-lint.py` | check |  | commands/implement-story.md, .writ/docs/architecture-lint.md |
| `archive-sweep.py` | data |  | commands/release.md, commands/status.md |
| `boundary-map.py` | data |  | commands/implement-story.md |
| `build-smoke.py` | data |  | commands/implement-story.md, commands/status.md |
| `change-surface.py` | data |  | commands/implement-story.md |
| `check-agent-parity.sh` | check |  | commands/refresh-command.md, adapters/codex.md |
| `docs-check.py` | check |  | commands/implement-story.md |
| `drift-format.py` | check |  | commands/implement-story.md, commands/implement-spec.md |
| `exit-criteria.py` | data |  | commands/implement-phase.md, commands/implement-spec.md, adapters/claude-code.md |
| `gen-codex-agent-tomls.py` | check |  | commands/refresh-command.md, adapters/codex.md |
| `gen-skill.sh` | check |  | commands/new-skill.md, commands/update-writ.md |
| `goal-emit.py` | check |  | commands/create-goal.md, commands/implement-phase.md, adapters/claude-code.md |
| `jev-judge.py` | check | network: opt-in, bounded-wait | commands/create-spec.md, commands/implement-story.md, commands/verify-spec.md |
| `knowledge-consolidate.py` | data |  | commands/knowledge.md, commands/retro.md |
| `lint-skill.sh` | check |  | commands/new-skill.md, commands/refresh-command.md, commands/update-writ.md |
| `phase-state.py` | data |  | commands/implement-phase.md, commands/implement-spec.md, commands/status.md, commands/revert.md, commands/knowledge.md, adapters/claude-code.md |
| `quality-config-audit.py` | data |  | commands/initialize.md, commands/status.md |
| `recommend-state.py` | data |  | skills/drift-triage/SKILL.md |
| `resolve-spec-reference.py` | data |  | commands/release.md, commands/ship.md |
| `revert-resolve.py` | data |  | commands/revert.md, commands/implement-story.md |
| `review-override.py` | check |  | commands/implement-story.md |
| `review-panel.py` | check |  | commands/implement-story.md, adapters/claude-code.md, adapters/codex.md, adapters/cursor.md |
| `roadmap-sync.py` | data |  | commands/release.md |
| `spec-analyze.py` | check |  | commands/create-spec.md, commands/verify-spec.md |
| `spec-deps.py` | data |  | commands/implement-phase.md, commands/implement-spec.md, commands/verify-spec.md |
| `spec-status.py` | data |  | commands/create-spec.md, commands/status.md |
| `story-context.py` | data |  | commands/implement-story.md, skills/story-context-assembly/SKILL.md |
| `story-deps.py` | data |  | commands/implement-spec.md |
| `supersession-writeback.py` | data |  | commands/create-spec.md, commands/edit-spec.md |
| `test-integrity.py` | data |  | commands/implement-story.md, agents/testing-agent.md, commands/status.md |
| `verdict-provenance.py` | check |  | commands/implement-story.md |

**Not in the table.** `jev-thresholds.json` ships, but it is a data file that `jev-judge.py` reads, not a script. Six dev-only scripts stay in the Writ source repo for measuring and evaluating Writ: `pipeline-baseline.py`, `measure-invocation.py`, `harness-cost.py`, `lean-decision.py`, `prune-ledger.py`, and `spawn-cap.py`. Writ no longer ships them, and `/update-writ` removes unmodified copies left by an older install.

### Notes

The Shape column records the shape each script prints. Every shipped script conforms, and `scripts/tests/test_agent_cli_contract.py` enforces it; its `KNOWN_VIOLATIONS` list names any temporary exception. The notes below record script-specific details an agent needs to parse the output.

The Callers column names the main callers and is not complete. Before you change a script's output, grep `commands/`, `agents/`, `skills/`, `adapters/`, and `.writ/docs/` for its name, including `*.lean.md` files.

- `app-verify.py` — check. `touched` prints one `feature: <id>` line per matched feature between the verdict and the summary. A refused run prints `unverifiable` on line 1 and keeps `refused` in its summary and JSON. With `--json`, the verdict lines print as usual and one JSON object follows the summary as the last line. The network import is a readiness probe on the app it launched. The wait polls readiness until the recipe's ready timeout and stops its process group within the cleanup grace period.
- `jev-judge.py` — check. The network path needs ADR-027's double opt-in. Retries on rate limits stop after `MAX_ATTEMPTS`. Calibration detail goes to stderr.
- `review-panel.py` — check. A panel word that is not a verdict is the first `reason:` line: `tally` prints `fail` then `reason: block` on a consensus finding (exit 1), and `trial-report` prints `pass` then `reason: keep` or `reason: remove`. With `--json`, the object's `verdict` holds the panel word.
- `recommend-state.py` — data. Its `urllib.parse` import splits URLs and is not a network call. On a bad flag it prints a JSON blocker on stdout, which the usage-error rule allows.
