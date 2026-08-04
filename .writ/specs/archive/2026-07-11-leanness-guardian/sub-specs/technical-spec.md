# Technical Spec: Leanness Guardian

> Source: .writ/specs/2026-07-11-leanness-guardian/spec.md

## Architecture

Two independent tiers, both in the dogfooding layer:

```
Tier A (mechanical, per-PR, CI)          Tier B (judgment, cadence)
─────────────────────────────           ──────────────────────────
scripts/eval.sh                          .writ/docs/leanness-audit-format.md
  CHECKS=( ... leanness )       ──feeds──▶  (template)
  check_leanness()                            │ produces
    └─ scripts/eval-leanness.py               ▼
         reads:                          .writ/docs/leanness-audit-YYYY-MM-DD.md
           commands/*.md                   findings → decisions → ADR/roadmap
           README (command table)
           commands/status.md (allowlist)
           .writ/leanness-baseline.json
```

## Tier A — `scripts/eval.sh` integration

The runner maps a check name to a bash function via
`func="check_${check//-/_}"` (eval.sh:2323). To add the check:

1. Append `leanness` to the `CHECKS=()` array (eval.sh:19–43), after
   `memory-interop`.
2. Define `check_leanness()` following the established shape: set
   `CURRENT_*` counters via the harness, invoke the Python helper, parse its
   JSON output, and call `add_finding "<subject>" "<what>" "<how to fix>"` per
   finding. Structural findings increment `CURRENT_FINDINGS` (→ FAIL); warnings
   are reported in the check body but **must not** call `add_finding` (so they
   stay non-blocking / exit 0).

> **Note on warn-only mechanics:** `add_finding` increments `TOTAL_FINDINGS`,
> which fails the run. Warnings therefore print to the check's report section
> **without** `add_finding`. If the harness has no warn primitive, emit warning
> lines directly into `$CHECK_TMP`/report and keep `CURRENT_FINDINGS` at 0 for
> warn-only outcomes.

## `scripts/eval-leanness.py`

Pure-Python, stdlib only (matches sibling `eval-*.py`). Contract:

```
usage: eval-leanness.py [--root PATH] [--baseline PATH]
output: JSON to stdout:
  {
    "structural": [ {"subject": "...", "what": "...", "fix": "..."} ],
    "warnings":   [ {"subject": "...", "what": "...", "fix": "..."} ],
    "metrics":    {"commands": N, "agents": N, "skills": N,
                   "command_lines": N, "command_chars": N}
  }
exit code: 0 always (the bash check decides FAIL from `structural`)
```

### Registry parity (structural — the novel contribution)

Three registries, cross-checked **directionally** (see DEV-001 in `drift-log.md`).
**Manifest parity is intentionally excluded** (owned by `check_manifest`).

| Registry | Source of truth | Parse method | Direction |
|---|---|---|---|
| Files | `commands/*.md` minus infra (`_preamble.md`) | glob | — |
| README table | root `README.md` command table rows | regex on table rows naming `/command` | **bidirectional** with files |
| `/status` allowlist | `commands/status.md` "Maintainer Note: Command Allowlist" backtick list | regex on the backtick command list | **one-way** (phantom-only) |

The README table is the authoritative full registry. The `/status` allowlist is a
curated *suggestion* subset (it governs which commands `/status` may proactively
suggest), so it is intentionally incomplete and is never used to flag orphans.

Findings:
- **Orphan:** a command file present but absent from the **README table** →
  structural. (The allowlist never produces orphans.)
- **Phantom:** a name in the README table **or** the `/status` allowlist with no
  backing file → structural.

Infra exclusion list is explicit and small (`_preamble`); if it grows, that is
itself a leanness signal worth a warning.

### Count ceilings (warn)

`commands > 35`, `agents > 10`, `skills > 12`. Chosen with headroom over current
31/7/6 so the tripwire is silent today and only speaks on genuine growth.

### Aggregate weight (warn)

Compare `command_lines`/`command_chars` against `.writ/leanness-baseline.json`.
Warn when growth exceeds **+10%** vs baseline. The warning text names the
baseline file and the deliberate-bump path (re-run with `--update-baseline`, or a
documented manual edit) so a legitimate large feature does not create nagging.

## `.writ/leanness-baseline.json`

Committed (not under `.writ/state/`, so it is version-controlled). Seed:

```json
{
  "recorded": "2026-07-11",
  "commands": 31,
  "agents": 7,
  "skills": 6,
  "command_lines": 10659,
  "command_chars": 484616,
  "note": "Bump deliberately when growth is legitimate; the delta is the signal."
}
```

> **Alternative considered:** derive the trend from git (`git show <last-tag>:`).
> Rejected for v1 — needs tag access in CI and is less deterministic than a
> committed baseline. The retro `trends.json` precedent favors an explicit file.

## Fixture test (`scripts/tests/`)

Existing tests are shell scripts (`test_*.sh`). Add `test_eval_leanness.sh`:
1. Build a temp repo skeleton with a minimal `commands/`, `README.md`,
   `commands/status.md`, and baseline.
2. Assert `eval-leanness.py --root <tmp>` reports empty `structural` (PASS).
3. Inject an orphan (add `commands/ghost.md` absent from README + allowlist);
   assert `structural` is non-empty (FAIL).
4. Inject a phantom (name a command in the allowlist with no file); assert FAIL.

## Tier B — `.writ/docs/leanness-audit-format.md`

Template sections:
- **When to run:** per-phase-close or quarterly (not per-release).
- **Inputs:** paste latest `--check=leanness` metrics; list manifest + adapters.
- **Judgment checklist:** (a) native displacement per Principle #4; (b) command
  overlap; (c) existence justification; (d) prune candidates.
- **Output contract:** dated `leanness-audit-YYYY-MM-DD.md` — a table of
  findings, each with a decision (keep / prune / merge / defer) and a follow-up
  (ADR number, roadmap edit, or issue).

`self-dogfooding.md` gains a short "Leanness cadence" subsection pointing to the
template and stating the trigger.

## Governance — ADR-015

Records the durable stance: *Writ polices its own leanness via a CI tripwire plus
a cadence-bound ritual, never via distributable surface.* Follows the ADR format
(Date/Status/Category, Decision, Context, Considered Alternatives, Consequences).
Extends the spirit of Design Principles #1 and #4; references ADR-009/014 for the
surface it measures.

## Verification

- `bash scripts/eval.sh --check=leanness` → PASS on current repo.
- `bash scripts/tests/test_eval_leanness.sh` → all assertions pass.
- `git status` shows no changes under `commands/` and no `/status` allowlist diff.
