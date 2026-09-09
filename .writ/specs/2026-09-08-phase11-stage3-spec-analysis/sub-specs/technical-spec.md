# Technical Spec — Phase 11 Stage 3: Spec Analysis

> Spec: `.writ/specs/2026-09-08-phase11-stage3-spec-analysis/`
> Stories: 1 (CLI), 2 (hooks), 3 (eval + precision)

Shared contract with Stage 2b helpers: Python 3.9 stdlib, argparse subcommands, exit 0 (ran, no blocking helper defect: `pass` or `unverifiable`), 1 (`fail`), 2 (usage). One verdict line, optional `reason:` lines, summary last. `--repo` / `--project` alias.

This script does **not** call an LLM API. Semantic codes arrive only via `--findings`.

## 1. CLI — `scripts/spec-analyze.py` (Story 1)

```
python3 scripts/spec-analyze.py check --spec PATH [--findings FILE] [--repo .]
```

| Flag | Required | Meaning |
|---|---|---|
| `--spec` | yes | Spec folder containing `user-stories/story-*.md` |
| `--findings` | no | JSON file: array of finding objects from the orchestrator LLM pass |
| `--repo` / `--project` | no | Repo root; default `.` |

### Structural codes (script-owned)

| code | When |
|---|---|
| `empty_criterion` | A `- [ ] Given` / `- [x] Given` line has no body after the checkbox |
| `unmeasurable_criterion` | Then-clause is only a vague success phrase (`works correctly`, `as expected`, `looks good`) with no named artifact, path, verdict, or count |
| `under_min_criteria` | Story file has fewer than 3 criterion lines matching `- [ ] Given` / `- [x] Given` |

Prefer under-firing `unmeasurable_criterion`. A clean fixture must not trip it.

### Semantic finding schema (LLM JSON)

`--findings` is a JSON array. Each object:

```json
{"code": "contradiction|gap|ambiguity", "story": "story-1-….md", "summary": "…", "ac_ids": ["AC-1.1"]}
```

- `code`, `story`, `summary` required; `summary` non-empty.
- `story` is a story filename or the literal `spec`.
- `ac_ids` optional; each value must match `AC-\d+\.\d+` when present.
- Unknown `code` or missing required field → `malformed_findings` (script `fail`).
- Empty array `[]` is well-formed.

### Verdict table

| Situation | verdict | exit |
|---|---|---|
| Stories readable; findings (if any) well-formed; no structural code | `pass` | 0 |
| Any structural code or `malformed_findings` | `fail` | 1 |
| Missing/unreadable `--spec`, or no `--findings` and no structural hit | `unverifiable` | 0 |
| Usage (unknown subcommand, bad argv) | (stderr) | 2 |

`pass` / `fail` / `unverifiable` are the only verdict lines. Never print accept / reject / modify-spec.

## 2. Command hooks (Story 2)

**create-spec Step 2.6c** (after 2.6b; still after 2.6a): orchestrator writes findings JSON (or skips and omits `--findings`); runs `check`; Step 2.9 lists reasons as notes; package continues.

**verify-spec:** new advisory check, not 3e/3f. Same CLI. Notes only.

LLM-pass input: story AC text. Output: schema above or `[]`. No API key in the script. No new agent file.

## 3. eval + precision (Story 3)

`CHECKS` includes `spec-analyze`. Missing helper / exit 2 → `add_finding`. Analysis verdicts → `add_note`.

Fixtures: `scripts/tests/fixtures/spec-analyze/` — contradiction, gap, ambiguity, clean. Optional Stage 1 slug names. Gold labels beside fixtures. Precision = TP/FP per class on those labels (schema-check + structural; semantic gold is the labeled JSON).

## 4. Error & Rescue Map

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| `check --spec` | Folder missing / unreadable | `unverifiable`, reason verbatim; commands continue | Fixture: missing path |
| `check --findings` | JSON not an array / bad object | `fail` `malformed_findings`; command notes, continues | Fixture: bad JSON |
| Structural scan | Vague Then-clause | `unmeasurable_criterion` only on the listed phrases; clean fixture must pass | Clean + vague fixtures |
| LLM pass | Orchestrator skips or model writes `[]` | Omit `--findings` or pass `[]`; script `unverifiable` or `pass` on structure | No-findings fixture |
| `eval.sh` live repo | No findings file | `add_note` unverifiable; Findings 0 | eval-wiring bash |
| Helper missing | File not shipped | `add_finding`; eval fails | bash missing-helper case |

## 5. Shadow Paths

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| create-spec 2.6c | Notes in Step 2.9; package completes | No `--spec` (bug) → unverifiable note | No findings, no structural hit → unverifiable note | Malformed JSON → fail note; package completes |
| verify-spec check | Advisory row; report not failed | Missing spec folder → existing verify error | Same as empty | Same as malformed |
| Precision score | TP/FP table in WWB | No gold file → do not invent precision | Empty gold → 0/0 recorded as such | Mis-labeled gold → fix the label, not the command |

## 6. Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| Double invoke in one create-spec run | One Step 2.6c; do not loop |
| Findings JSON from a previous spec | Path is per-run under `.writ/state/`; do not reuse another spec’s file |
| Story file added after 2.6c | Out of scope for that run; next `/verify-spec` picks it up |
| Concurrent verify-spec | Read-only; no lock |

## 7. Tests

- `scripts/tests/test_spec_analyze.py` — pass / fail-structural / fail-malformed / unverifiable-missing-spec / unverifiable-no-findings [AC-1.*]
- `scripts/tests/test_eval_spec_analyze.sh` — registration, note relay, missing helper [AC-2.*, AC-3.*]
- Precision assertions against gold labels [AC-3.*]
