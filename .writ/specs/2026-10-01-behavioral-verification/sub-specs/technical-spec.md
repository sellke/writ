# Technical Spec: Behavioral Verification

> Parent: [spec.md](../spec.md)

## Files in Scope

| File | Change | Story |
|---|---|---|
| `.writ/docs/app-verification-format.md` | New: recipe grammar, worked example | 1 |
| `scripts/app-verify.py` | New: `validate` (Story 1), `touched` and `run` (Story 3) | 1, 3 |
| `scripts/tests/test_app_verify.py` | New: pytest for all subcommands | 1, 3 |
| `scripts/tests/fixtures/app-verify/` | New: `app.py`, `check_home.py`, `check_fail.py`, recipe variants | 3 |
| `.writ/decision-records/adr-028-…md` | Amend Decisions 1 and 2; runtime-boundary note | 1 |
| `.writ/product/roadmap.md`, `mission.md`, `mission-lite.md` | Merge Features 1+2; fixture-app success criterion; drop `/initialize` wording | 1 |
| `commands/create-uat-plan.md` | Recipe drafting step; `**Feature:**`/`**Verification:**` lines; run checks for machine scenarios | 2 |
| `commands/implement-story.md` + `commands/implement-story.lean.md` | Gate 4.5 rewrite; `gates:` entry; coding-agent check-authoring line | 4 |
| `agents/coding-agent.md` | One rule: add a check and feature-map row for new user-facing behavior when a recipe exists | 4 |
| `scripts/verdict-provenance.py` | `DEFAULT_MAX_PROSE_ONLY = 1` | 4 |
| `scripts/exit-criteria.py` + `test_exit_criteria.py` | Evidence half of `implement-phase.c2`; `check-uat --spec DIR` subcommand | 5 |
| `.writ/docs/exit-criteria-classification.md` | Record the evidence half | 5 |
| `scripts/eval.sh` + `scripts/tests/test_eval_app_verify.sh` | `app_verify` check: fixture pass/fail/refuse + missing-evidence mutation | 5 |

## Recipe Grammar (`.writ/docs/app-verification.md`)

```markdown
# App Verification Recipe

## Launch
- **Command:** `PORT=8765 python3 scripts/tests/fixtures/app-verify/app.py`
- **Ready when:** http://127.0.0.1:8765/
- **Ready timeout:** 30s
- **Reuse running instance:** no

## Safety
- **Safety:** none — fixture app holds no state
<!-- or, for stateful apps: -->
- **Variable:** DATABASE_URL
- **Allowed:** *dev-branch-host*
- **Never:** *prod*
- **Env file:** .env.local

## Login
- **Method:** checks sign in themselves with the seeded user
- **Credentials from:** E2E_USER_EMAIL, E2E_USER_PASSWORD   (names only)

## Feature Map
| ID | Feature | Paths | Check |
|---|---|---|---|
| home | Home page renders | `scripts/tests/fixtures/app-verify/app.py` | `python3 scripts/tests/fixtures/app-verify/check_home.py` |
| oauth | Third-party login | `app/auth/**` | human-only: third-party consent screen |

## Evidence
- **Artifacts:** test-results/

## Cleanup
- **After:** none
```

**Pattern syntax:** `Allowed`/`Never` are shell-style globs (`fnmatch`) matched against the variable's full value. `Paths` are globs matched against repo-relative changed paths, comma-separated.

**Validator findings** (`validate`, exit 1 on any): `missing_section`, `missing_launch_command`, `missing_ready`, `missing_safety` (neither variables nor `Safety: none — reason`), `bad_feature_row`, `duplicate_feature_id`, `bad_feature_id`, `secret_value` (a value containing `://user:pass@`, or any 32+ character token outside backticked commands), `bad_timeout`.

## Run Contract (`app-verify.py run`)

1. Validate the recipe; if invalid → exit 2, `unverifiable (recipe_invalid: <finding>)`.
2. Safety: resolve each variable (environment, then env file); refuse → exit 2.
3. Ready probe before launch: if it answers and reuse is `no` → exit 2 `refused (instance_already_running)`.
4. Launch with `subprocess.Popen(shell=True, start_new_session=True)` so the process group can be stopped; stdout and stderr go to `<evidence>/_launch/`.
5. Poll readiness (an HTTP GET returning any status below 500, or a TCP connect for `port N`) every 0.5 s until the timeout → otherwise fail, `not_ready`.
6. For each selected feature with a check: run it with a 300 s default timeout and env `APP_VERIFY_EVIDENCE_DIR=<feature dir>`; write `result.json` and the logs; copy artifacts.
7. Cleanup always runs (`finally`): SIGTERM the group, wait 10 s, SIGKILL; then run the `After` command.
8. Summary: exit 0 if every check passed, 1 if any failed, 2 if nothing ran.

`result.json` schema `app-verify-result-v1`: `{feature, command, exit_code, verdict, started_at, ended_at, duration_s, recipe_sha256, truncated: {stdout, stderr}, artifacts: [...]}`.

## Error & Rescue Map

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| Read recipe | File missing | `unverifiable (no_recipe)`, exit 2; Gate 4.5 skips with one line | pytest: missing path |
| Validate recipe | Malformed section or row | `unverifiable (recipe_invalid: <finding>)`, exit 2 | pytest: one fixture per finding |
| Resolve safety variable | Unset / unmatched / matches `Never` | `refused (<var> …)`, exit 2, nothing launched | pytest: env override with a non-matching value |
| Read env file | Missing or unreadable | Treated as unset → refused | pytest |
| Pre-launch probe | Instance already answering | `refused (instance_already_running)` unless reuse is `yes` | pytest: start fixture first |
| Launch | Command exits immediately | `fail (launch_exited <code>)`, launch logs kept | pytest: recipe with `false` |
| Readiness | Timeout | `fail (not_ready <N>s)`, cleanup runs | pytest: never-ready recipe |
| Run check | Non-zero exit | `fail`, `result.json` verdict `fail` | pytest: `check_fail.py` |
| Run check | Timeout | Kill the check's group, verdict `fail (timeout)` | pytest: sleep check with a small timeout |
| Copy artifacts | Over 5 MB / missing | Record by path / record `missing`; never fails the run | pytest |
| Cleanup | Process survives SIGTERM | SIGKILL after 10 s; a failed `After` command is a note, not a fail | pytest: check no fixture PID survives |
| Evidence check | Cited file missing / verdict not `pass` | `implement-phase.c2` unmet, naming spec + scenario | mutation test: delete `result.json` |
| `/create-uat-plan` draft | No harness detected | Draft with every feature `human-only: no check yet`; developer may skip | command-hook test |

## Shadow Paths

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| Gate 4.5 | Touched features pass → evidence written → continue | No recipe → skip line | Story touches no mapped path → `no mapped features` line | App never ready → fail → Gate 1 |
| `/create-uat-plan` | Recipe confirmed → scenarios bound → checks pass → scenarios marked passed with evidence | No harness → all human-only draft | Developer skips → today's human plan | Safety refused → scenarios stay human, with reason `refused` |
| Evidence check | All cited files exist and pass → met | No machine scenarios → met (vacuous, noted) | Plan without `**Verification:**` lines (pre-Phase-12) → met, noted `legacy plan` | Unreadable `result.json` → unmet |

## Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| Two runs at once on one port | Pre-launch probe refuses the second |
| Feature ID renamed after evidence written | Evidence check cites paths, not IDs; a stale path is `unmet` |
| Check writes outside the evidence dir | Allowed (project-owned); only named artifacts are copied |
| Windows | Out of scope: process groups use POSIX `start_new_session`; `run` reports `unverifiable (unsupported_platform)` |

## Integration Notes

- `install.sh`/`update.sh` overlay `.writ/docs/*.md`; the project-authored recipe filename is never shipped. Story 1's test asserts that `.writ/docs/app-verification.md` does not exist in the Writ repo.
- `eval.sh` runs a `git init` in a temp dir and must run outside the sandbox; the new check spawns local processes on 127.0.0.1 only.
