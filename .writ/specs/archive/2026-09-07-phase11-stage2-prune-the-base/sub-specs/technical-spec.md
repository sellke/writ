# Technical Spec — Phase 11 Stage 2a: Prune the Base

> Source: [`../spec.md`](../spec.md) · Stories: [`../user-stories/`](../user-stories/)

## 1. `scripts/prune-ledger.py` (Story 1)

```
prune-ledger.py check   --repo . [--base-commit cf84742] [--cap 10000] [--cap-blocking]
prune-ledger.py measure --repo .          # bytes per ## / ### section, both base files
```

**Inputs.** `BASE_FILES = ("system-instructions.md", "commands/_preamble.md")`; `LEDGER = ".writ/decision-records/pruned-instructions-ledger.md"`.

**Removed lines.** `git diff --no-color -U0 <base-commit> -- <file>` from `--repo`; every hunk line starting with `-` (not `---`) is a removed line, text taken verbatim after the marker. No whitespace normalization. Lines removed *and* re-added identically elsewhere in the file (a pure move within the file) are not removals: compute as multiset difference of removed vs added texts per file.

**Ledger rows.** Regex over each line: `^\| (\d{4}-\d{2}-\d{2}) \| ([^|]+) \| (moved|behavior-request|duplicate) \| ([^|]*) \| (.*) \|$`. The text column escapes `|` as `\|`; the parser unescapes. Header and separator rows are skipped. Any other row starting with `|` is a `malformed_row` finding.

**Findings (one line each, `<code>: <detail>`):**

| Code | Condition |
|---|---|
| `removed_not_in_ledger` | a removed line's text has no ledger row with identical text and file |
| `ledger_text_reappeared` | a ledger row's text is present as a whole line in the same base file at HEAD |
| `over_cap` | sum of byte sizes > `--cap`; a finding only with `--cap-blocking`, otherwise a note line prefixed `note:` |
| `malformed_row` | ledger row fails the regex |
| `ledger_missing` | note, not a finding, until the first removal exists |

**Summary line (always last):** `base: <bytes> bytes (cap <cap>), ledger: <rows> rows, removed: <n>, re-added: <n>`.

**Exit codes.** 0 no findings; 1 findings; 2 usage or git failure (stderr carries git's message; nothing fabricated).

**eval.sh.** `check_pruned_base()` next to `check_pipeline_baseline()`, registered as `pruned-base`. Cap blocking is decided by the presence of `.writ/decision-records/pruned-instructions-ledger.md` containing the marker line `<!-- cap: blocking -->`, which Story 3 appends when it reaches the cap. Notes relayed via `add_note`, findings via `add_finding`.

## 2. Ledger format (Story 1)

```markdown
# Pruned Instructions Ledger

> Append-only. One row per line removed from system-instructions.md or commands/_preamble.md
> since cf84742 (Phase 11 Stage 1 closeout). Checked by scripts/prune-ledger.py.

| Date | File | Class | Reason | Text |
|---|---|---|---|---|
| 2026-09-08 | system-instructions.md | moved | .writ/docs/model-tiers.md | ## Model Tiers |
```

Class vocabulary: `moved` (reason = destination path), `behavior-request` (reason = why the model does it unprompted, ≤ 120 chars), `duplicate` (reason = where the surviving copy lives).

## 3. Move targets (Story 2)

| Base section | Bytes | Target | Note |
|---|---|---|---|
| `## Model Tiers` + `### entry_level` | 4,519 | `.writ/docs/model-tiers.md` | ADR-024 already documents the policy; the doc holds the tables |
| `### required_skills: frontmatter convention` | 2,809 | `.writ/docs/skills-convention.md` | check for an existing skills doc first |
| `### Skill authoring` | 458 | same file | |
| `## Startup Update Awareness` | 3,784 | `.writ/docs/startup-update-awareness.md` | `update.sh` may reference; keep the one-line trigger in base |
| `### Recommendation Semantics` (tutorial part) | ~1,875 | `.writ/docs/recommendation-semantics.md` | the rule sentence stays in base |

Expected after Story 2: ~15,000 bytes. Each section leaves one line: `See .writ/docs/<file> for <topic>.` `check_referenced_paths` must resolve every link.

## 4. Cut candidates (Story 3)

Classification table (in the story's What Was Built) has columns: file, section, line count, class, action. Candidate sections and current bytes: Identity & Approach 663, Command Execution Protocol 827, Judgment Principles 816, Prose 418, Interaction Tool Selection 1,241, Session Auto-Orientation 559, Skills 397, File Organization 728 (duplicate of preamble's 320), preamble Tool Selection 244, Knowledge Context 122, Adapter Neutrality 181. Kept verbatim: Hard Constraints 1,064, Plan Mode Integrity 270 + 635, User Challenge 1,189, Autonomy Gate Classes 1,773, Artifact Integrity 575, the Recommended Delivery Exception rule. Needed cut from 15,000 to 10,000: ~5,000 bytes; candidates total ~6,200.

The Fable 5.1 batching line: one line appended to each of `adapters/claude-code.md`, `adapters/cursor.md`, `adapters/codex.md`, `adapters/openclaw.md` under a `## Model-specific` heading; `prune-ledger.py` does not check adapters — the Goal Card's "one line per model" QUALITY rule is verified by `grep -c` in Story 3's verification task and recorded.

## 5. `scripts/verdict-provenance.py` (Story 4)

```
verdict-provenance.py check --command commands/implement-story.md [--max-prose-only 2] [--prose-only-blocking]
```

Parses YAML frontmatter with a minimal line parser (no PyYAML; stdlib only, matching `exit-criteria.py`'s approach) for a `gates:` list of `{id, script?, verification?}`. Parses `#### Gate N` headings from the body and maps them to ids by a fixed table: `Gate 0` → `gate0_arch`, `0.5` → `gate0_5_boundary`, `1` → `gate1_coding`, `2` → `gate2_build`, `2.5` → `gate2_5_surface`, `3` → `gate3_review`, `3.5` → `gate3_5_drift`, `4` → `gate4_tests`, `4.5` → `gate4_5_visual`, `5` → `gate5_docs`. Names for 0, 2, 3, 4, 5 match `pipeline-baseline.py`'s `GATE_NAMES` so a later join is free.

Findings: `heading_without_entry`, `entry_without_heading`, `entry_without_source` (neither key), `entry_both_sources`, `script_missing` (path not on disk relative to repo), `unknown_verification_value` (anything but `prose-only`). Note: `prose_only_count: <n> (cap <max>)`; a finding instead when `--prose-only-blocking`. Exit codes as §1.

`eval.sh` check `verdict-provenance` registered next to `pruned-base`; not blocking on count until the mechanization spec passes `--prose-only-blocking`.

## 6. Re-run file and compare (Story 5)

New file `.writ/eval/baselines/<date>-claude-fable-5-1.json`: copy Stage 1's `schema`, `model`, `yuss_head`, `criteria`, `selection`, `excluded`, `rejection_tally`; set `generated_at` to now, `runs_per_story: null`, `runs: []`. `pipeline-baseline.py validate` must pass once eight records exist. Run command and monitoring follow Stage 1 Story 5's What Was Built (nohup, `--keep`, scratch `--tmp-root`). `compare <stage1> <new>` decides keep-or-revert on the `exit_criteria` column only; token and wall-clock deltas are recorded, not judged.

Revert path: `/revert` on the Story 2 and Story 3 completion commits (Stage 1's `revert-resolve.py` resolves them); the ledger file is restored to its post-Story-1 state by the same revert since its rows landed in those commits; ADR-026, Story 4's markers, and the re-run JSON stay.

## 7. Tests

- `scripts/tests/test_prune_ledger.py` — temp git repo fixture with a fake base commit; one test per finding code; move-within-file not a removal; pipe escaping round-trip; exit 2 on bad base commit.
- `scripts/tests/test_verdict_provenance.py` — fixture command files: complete block; missing entry; extra entry; both keys; missing script; count over cap as note vs finding.
- `scripts/tests/test_eval_pruned_base.sh`, `test_eval_verdict_provenance.sh` — following `test_eval_pipeline_baseline.sh`'s shape.
- Story 5 has no new unit tests; its verification is the compare table and `validate`.
