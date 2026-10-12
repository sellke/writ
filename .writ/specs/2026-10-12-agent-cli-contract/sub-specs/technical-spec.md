# Technical Spec: Agent CLI Contract

> Spec: [`../spec.md`](../spec.md) · ADR: [ADR-029](../../../decision-records/adr-029-agent-cli-contract.md)

## Current State (audit, 2026-10-12)

The ship filter is `is_shippable_script` in `scripts/install.sh:922` and `scripts/update.sh:569`. It ships `*.py` and `*.sh`, except lifecycle scripts, `eval*`, `_*`, `sweep-*`, and publish artifacts, plus `jev-thresholds.json`.

- **Python:** 37 shipped scripts. All exit 0 on `--help`. All exit 2 on an unknown flag with argparse usage on stderr. `recommend-state.py` prints a JSON blocker on stdout instead; under the usage rule, a non-empty stdout is allowed only if it is that JSON blocker (see Contract Test → bad-flag probe).
- **Shell:** `lint-skill.sh`, `gen-skill.sh`, `check-agent-parity.sh`.

Preliminary shapes (Story 1 confirms each by reading `main()` and its callers):

| Group | Scripts |
|---|---|
| Data, JSON default | ac-trace, archive-sweep, build-smoke, exit-criteria, phase-state, quality-config-audit, recommend-state, resolve-spec-reference, roadmap-sync, spec-deps, spec-status, story-context, story-deps, supersession-writeback, test-integrity |
| Check, verdict line | arch-check, docs-check, drift-format, goal-emit, review-override, review-panel (`--json` optional), spec-analyze, verdict-provenance, jev-judge |
| Needs a ruling | app-verify (summary line, then JSON with `--json`), boundary-map (`compute` JSON, `crossings` text lines), change-surface (prints one class word), arch-lint (`detect` prints lines), gen-codex-agent-tomls (`wrote …` lines in write mode, verdict in `--check`), revert-resolve (text by default, `--json` opt-in), knowledge-consolidate (markdown by default, `--json` opt-in), the three shell scripts |
| Dev-only, stop shipping (Story 2) | pipeline-baseline (launches agent CLIs), measure-invocation (network), harness-cost, lean-decision, prune-ledger, spawn-cap |

Allowances observed:

- `network: opt-in`: `jev-judge.py` (ADR-027 double opt-in), `app-verify.py` (`socket` readiness probe on a local port it started).
- `bounded-wait`: `app-verify.py` (readiness poll, `READY_POLL_S`), `jev-judge.py` (retry backoff), `test-integrity.py` (`while True` at line 320; Story 1 confirms whether this is a bounded parse loop or a wait).
- `build-smoke.py` and `recommend-state.py` matched the network scan only through string literals (`"socket hang up"`) or non-import text. The import-based static check must not flag them.

## Contract Doc (Story 1)

Path: `.writ/docs/agent-cli-contract.md` (ships to installed projects with the other `.writ/docs`).

Sections:

1. **Scope** — what counts as a shipped script; dev-only scripts never ship.
2. **Data shape** — Business Rule 3 of spec.md.
3. **Check shape** — Business Rule 4.
4. **Usage errors** — Business Rule 5.
5. **Never spawn, never wait unbounded** — Business Rules 6–7, citing ADR-028's runtime boundary and pstack `orch`.
6. **Network** — Business Rule 8.
7. **State** — files under `.writ/` are canonical, one writer per file, atomic writes, readable without the tool.
8. **Runtime** — Python 3.9 standard library or POSIX shell. No shared `_*` helper is shipped.
9. **Adding a script** — add the row, run `uv run pytest scripts/tests/test_agent_cli_contract.py`.
10. **Classification** — the table.

Table columns: `Script | Shape | Allowances | Callers`. `Callers` lists the command, agent, or skill files that invoke it (for example `commands/revert.md`). It is informational, and the test checks only that it is non-empty.

## ADR-029 Amendment (Story 1)

Add a dated block after rule 7 of "The agent CLI contract": `*Amended 2026-10-12 by [2026-10-12-agent-cli-contract](../specs/2026-10-12-agent-cli-contract/spec.md):*` followed by:

- Rule 1 now allows two shapes, data (JSON) and check (verdict line), and accepts `error` beside `blocker` for existing data tools.
- Usage errors: non-zero exit, usage on stderr, empty stdout. Matches pstack `orch`.
- Rule 2: a bounded wait on a process the script started or a call it made is allowed with a timeout. Starting agent or model CLIs never is.
- Dev-only scripts stop shipping. The contract covers only shipped scripts.

Use targeted edits. Don't rewrite the original rule text.

## Ship Filter (Story 2)

In both `install.sh` and `update.sh`, add a case arm before the `*.py|*.sh` acceptance:

```bash
    pipeline-baseline.py|measure-invocation.py|harness-cost.py|lean-decision.py|prune-ledger.py|spawn-cap.py)
      # Dev-only tooling (eval.sh, measurement); not agent-facing. ADR-029.
      return 1 ;;
```

Keep the two functions byte-identical in that region; a test compares them. Update `commands/update-writ.md` Step 3 prose to list "dev-only measurement and eval helpers (…)". The stale-file logic (manifest entry present, upstream absent, local hash == baseline → remove) already covers removal from installed projects. Story 2 adds a test proving it for one of the six.

## Contract Test (Story 3)

File: `scripts/tests/test_agent_cli_contract.py`.

```python
SHIPPED = shipped_scripts()          # bash: source the is_shippable_script function from install.sh
TABLE = parse_classification()       # first table under "## Classification"
KNOWN_VIOLATIONS = {                 # (script, rule) -> reason; must be {} at spec close
}
```

Tests, each parametrized over `SHIPPED`:

| Test | Rule | Assertion |
|---|---|---|
| `test_table_complete` | scope | `set(SHIPPED) == set(TABLE)`; message names the missing or extra script |
| `test_help` | 9 | `python3 <s> --help` → exit 0 / `bash <s> --help` → exit 0 or usage on stdout or stderr |
| `test_bad_flag` | 5 | `--zz-contract-probe` → exit ≠ 0. stdout must be empty, or a single JSON object with a `blocker` key |
| `test_no_unmarked_network` | 8 | `ast` import scan for `urllib`, `http.client`, `socket`, `requests`; allowed only if the row has `network: opt-in` |
| `test_no_agent_launch` | 6 | `ast` scan: no `subprocess.*`/`os.exec*`/`Popen` call whose first argument list literal starts with an agent CLI name |
| `test_bounded_wait_marked` | 7 | `time.sleep` call or `while True` only if the row has `bounded-wait` |
| `test_shape_smoke` | 3–4 | For scripts in `SMOKE_INVOCATIONS` (read-only invocations against this repo, e.g. `spec-status.py scan --specs-dir .writ/specs`), run and assert the declared shape |

Shell scripts get table, help, and bad-flag tests only. The `ast` checks are Python-only.

xfail: `pytest.param(..., marks=pytest.mark.xfail(strict=True, reason=…))` for any `(script, rule)` in `KNOWN_VIOLATIONS`.

Use `subprocess.run([sys.executable, …])` so `uv run --python 3.9 pytest` exercises the floor. Run from a temp cwd for invocations that could write state.

## Conformance Fixes (Story 4)

Pattern for a data tool that defaults to text:

1. Make JSON the default and add `--pretty` for the old human rendering.
2. Keep `--json` as an accepted no-op flag (`help=argparse.SUPPRESS`).
3. Update callers. Grep `commands/ agents/ skills/ adapters/ .writ/docs/` for the script name.
4. Update the script's own tests for the new default.
5. Remove its `KNOWN_VIOLATIONS` entries.

Known callers:

- `revert-resolve.py` → `commands/revert.md:52` (passes `--json`; drop it).
- `knowledge-consolidate.py` → `commands/knowledge.md:74,92` (`--dry-run`, `--apply`). The command currently shows the markdown report. Either switch the command to `--pretty` to keep the identical report, or render from JSON. Prefer `--pretty`: one-line caller change, same user experience.

For check tools that need a ruling (app-verify, change-surface, arch-lint, boundary-map `crossings`), Story 1's table decides the shape and Story 4 fixes only what the test flags.

## Error & Rescue Map

| Operation | Failure | Detection | Rescue | What the maintainer or agent sees |
|---|---|---|---|---|
| Read ship filter from `install.sh` | Function renamed or moved | Test setup fails to source it | Test errors with a message naming `is_shippable_script` | `cannot load is_shippable_script from scripts/install.sh` |
| Parse classification table | Table missing or malformed | Parser finds no table under `## Classification` | Fail every parametrized test with one clear setup error | `no classification table in .writ/docs/agent-cli-contract.md` |
| Run a script's `--help` | Script crashes on import (e.g. 3.10-only syntax) | Non-zero exit with traceback | Test fails with stderr excerpt | Traceback tail plus script name |
| Shape smoke | Invocation writes state | Run in temp cwd; repo `git status` unchanged | Remove the invocation from `SMOKE_INVOCATIONS` | N/A — prevented by design |
| Update removes dev-only script | User modified it | Local hash ≠ baseline | Existing behavior: flag as stale, keep the file | `/update-writ` stale warning |
| Default output change | Caller still parses old text | Grep for callers during the fix | Same-commit caller edit; `--json` kept as no-op | No change for installed command files that still pass `--json` |

## Files in Scope

| File | Story | Change |
|---|---|---|
| `.writ/docs/agent-cli-contract.md` | 1 | New |
| `.writ/decision-records/adr-029-agent-cli-contract.md` | 1 | Dated amendment |
| `scripts/install.sh`, `scripts/update.sh` | 2 | Six-name exclusion arm |
| `commands/update-writ.md` | 2 | Exclusion prose |
| `.writ/docs/skills.md` | 2 | Reword line 330 if needed |
| `scripts/tests/test_install_update_*.sh` (new or extended) | 2 | Absent on install; stale removal on update |
| `scripts/tests/test_agent_cli_contract.py` | 3 | New |
| `scripts/revert-resolve.py`, `commands/revert.md`, `scripts/tests/test_revert_resolve*.py` | 4 | JSON default |
| `scripts/knowledge-consolidate.py`, `commands/knowledge.md`, its tests | 4 | JSON default, `--pretty` |
| Other `KNOWN_VIOLATIONS` scripts and callers | 4 | As flagged |
| `.writ/issues/features/2026-10-12-agent-facing-writ-cli.md` | 4 | `## Resolution` |
| `.writ/issues/improvements/2026-10-12-script-install-location.md` | 4 | New issue |
