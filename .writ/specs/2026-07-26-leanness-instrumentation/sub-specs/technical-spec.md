# Technical Spec: Leanness Instrumentation Rewrite

> Parent: [`spec.md`](../spec.md)
> Created: 2026-07-26

## Scope

A rewrite of `scripts/eval-leanness.py` (currently 314 lines) plus its baseline schema, its shell test harness, the Tier B audit format, and a new ADR. No user-facing surface. No `commands/*.md`.

## Preserved Contracts

These must not change — `scripts/eval.sh` and the Tier B ritual depend on them:

| Contract | Detail |
|---|---|
| CLI | `eval-leanness.py [--root PATH] [--baseline PATH] [--update-baseline]` |
| Output | JSON to stdout: `{"structural": [...], "warnings": [...], "metrics": {...}}` |
| Finding shape | `{"subject", "what", "fix"}` |
| Exit code | Always `0`. `eval.sh` decides FAIL from a non-empty `structural`. |
| Legacy metric keys | `commands`, `agents`, `skills`, `command_lines`, `command_chars` retained |
| Warn rendering | Warnings and metrics flow through `eval.sh`'s `add_note`, never `add_finding` |

## Surface Registry

The central new data structure. Story 1 introduces it; Stories 2 and 4 consume it.

| Surface | Path | Glob | Gated |
|---|---|---|---|
| `commands` | `commands/` | `*.md` | yes |
| `agents` | `agents/` | `*.md` | yes |
| `skills` | `skills/` | `*/SKILL.md` | yes |
| `adapters` | `adapters/` | `*.md` | yes |
| `scripts` | `scripts/` | `*.py`, `*.sh` | yes |
| `system_instructions` | `system-instructions.md` | (file) | yes |
| `writ_workspace` | `.writ/` | `**/*.md` | **no** — reported only |

`out_of_scope` (declared, never measured, never flagged): `.git`, `.github`, `.claude`, `.codex`, `.cursor`, `.writ-lanes-*`, `archive`, `bin`, `claude-code`, `codex`, `cursor`, `node_modules`, `test`, and root files `README.md`, `CHANGELOG.md`, `CLAUDE.md`, `AGENTS.md`, `SKILL.md`, `LICENSE`, `VERSION`, `package.json`, `.gitignore`, `.DS_Store`.

> The `out_of_scope` list is itself a leanness signal. If it grows, someone is adding surface and declaring it away.

## Baseline Schema (new)

```json
{
  "recorded": "2026-07-26",
  "schema": 2,
  "surfaces": {
    "commands":    { "lines": 10726, "chars": 492280, "justification": "" },
    "agents":      { "lines": 1768,  "chars": 0,      "justification": "" },
    "scripts":     { "lines": 18260, "chars": 0,      "justification": "" }
  },
  "total_product_lines": 33651,
  "story_context_bytes": 0,
  "note": "Down is free. Any increase requires a justification string."
}
```

Schema 1 (the current flat form) is detected by the absence of `schema` and produces a structural finding directing the maintainer to `--update-baseline`. This is a one-time migration, not a supported dual mode.

## Error & Rescue Map

The script performs file and directory operations throughout, so failure handling is load-bearing.

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| Read baseline JSON | File absent | Structural finding: "baseline is missing" + `--update-baseline` fix (existing behavior) | Temp dir with no baseline |
| Read baseline JSON | Malformed JSON | Structural finding naming the parse error; exit 0 | Fixture with truncated JSON |
| Read baseline JSON | Schema 1 (no `schema` key) | Structural finding: migrate via `--update-baseline` | Fixture with current committed baseline |
| Walk a registry surface | Directory absent | Structural finding: stale registry entry naming the path | Registry entry pointing at a deleted dir |
| Walk a registry surface | Directory present but empty | 0 lines, 0 chars — **not** an error | Empty temp dir |
| Read a measured file | Permission denied / unreadable | Skip the file, emit a warning naming it, never crash | `chmod 000` fixture |
| Read a measured file | Invalid UTF-8 | Read as bytes and count `\n` (existing approach already does this) | Binary fixture under a measured path |
| Enumerate repo root | New undeclared top-level dir | Structural finding (the coverage guard) | Temp dir with synthetic `newthing/` |
| Compute `story_context_bytes` | Referenced artifact absent | Count 0 for it, note the omission, continue | Repo with no `.writ/context.md` |
| Write baseline (`--update-baseline`) | Parent dir absent | `makedirs` then write (existing behavior) | Temp dir |
| Write baseline (`--update-baseline`) | Disk/permission error | Propagate a clear stderr message, non-zero exit **only** for this write path | Read-only temp dir |

No `[UNPLANNED]` rows remain.

## Shadow Paths

What the maintainer sees, not what the system does.

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| `--check=leanness` on clean repo | Silent pass, metrics note in report | Baseline absent → named structural finding + fix | Measured dir empty → counts 0, still passes | Malformed baseline → structural finding, exit 0 |
| Coverage guard | All top-level paths resolve → silent | New undeclared dir → FAIL naming path + fix | `out_of_scope` entry absent from disk → ignored, no noise | Registry names deleted path → FAIL, stale entry |
| Ratchet | Surface shrank → silent | No baseline entry for a new surface → treated as first record, no warning | Zero-line surface → silent | Unjustified growth → warning with surface, base, current, delta |
| `story_context_bytes` | Deterministic value reported as proxy | No active spec → 0 for spec artifacts, noted | No `knowledge/` → 0 for that slot | Unreadable agent file → skip + warn |

## Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| Two consecutive runs on an unchanged tree | Byte-identical `story_context_bytes` and all metrics. Sort every glob result; never rely on filesystem order. |
| `--update-baseline` run on a repo with findings | Baseline still written — it records reality; findings are reported separately |
| A surface both shrinks and another grows in one run | Evaluated per surface independently; one warning per unjustified surface, not one aggregate |
| `justification` present but empty string | Treated as absent → warning fires |
| `justification` present on a surface that *shrank* | Ignored, no warning; stale justification is not an error |
| Guardian measures itself mid-rewrite | Expected. `eval-leanness.py` grows under `scripts/`; the increase needs a baseline justification like any other |
| Run from a different cwd | `--root` resolution unchanged; all reported paths stay repo-relative via existing `relpath()` |
| `.writ-lanes-*` worktrees present during a phase run | Matched by the `out_of_scope` glob; never measured, never flagged |

## Test Harness

`scripts/tests/test_eval_leanness.sh` is the existing shell harness and the TDD anchor for Stories 1–4. Pattern: build a temp-dir fixture repo, run the script with `--root` and `--baseline` pointed at the fixture, assert on the JSON. Story 4 replaces the current `+10%` tolerance scenario with three ratchet scenarios.

Story 5 is a documentation story; its verification is the full `bash scripts/eval.sh` run reporting `Findings: 0`.

## Story Traceability

| Story | Primary artifacts |
|---|---|
| 1 — Full-surface measurement | registry, `compute_metrics`, baseline schema 2 |
| 2 — Coverage guard | root enumeration, `out_of_scope`, structural findings |
| 3 — `story_context_bytes` | declared-load sum, determinism |
| 4 — Reduction ratchet | `check_baseline` rewrite, `GROWTH_TOLERANCE` removal |
| 5 — ADR-019 + Tier B | decision record, audit format, `eval.sh` render check |
