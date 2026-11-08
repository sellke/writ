# Technical Spec: Retro Fix Ladder

> Spec: [`../spec.md`](../spec.md)

## Current State (audit, 2026-10-25)

- `commands/retro.md` (204 lines, 14,135 bytes) reads transcripts, detects nine signals (Step 3), ranks them (Step 4), proposes environment changes with an Evidence block and a Route (Step 5), reviews with the human (Step 6), and writes `.writ/retros/YYYY-MM-DD-<scope>.md` (Step 8). It has no fix order, no proof rule, and no rule table.
- Friction-signal remnants in `commands/retro.md`, retired by ADR-030 on 2026-10-20 and not removed by `2026-10-20-harness-cuts` or `2026-10-20-shipped-command-hygiene`:
  - Step 2, last paragraph: "If `.writ/state/signals.jsonl` exists (ADR-025), read its unreviewed lines in scope as extra evidence; a review with signals and no transcripts is valid but must say it is partial."
  - Error Handling, row "No transcripts found": "... and use ADR-025 signals if present".
  - Integration with Writ, row "ADR-025 friction signals".
  - Step 3, row "Writ friction" (a struggle signal, not the retired design, but the name invites confusion).
- `commands/refresh-command.md` (506 lines, 21,586 bytes) amends one command file. Rejection reasons are `no evidence` and `eval failed`. It never edits a skill. It does not check whether a signal is already covered by the command's guidance.
- `scripts/eval-refresh-evidence.py` line 68: `_REASON_RE = re.compile(r"reason:\s*(no evidence|eval failed)", re.IGNORECASE)`. `scripts/eval.sh` `check_refresh_evidence` runs its scenarios and pins `**Evidence:**`, `**Rejected:**`, `no evidence`, `eval failed`, `verbatim private transcript bodies`, the Tier 2 allowlist sentence, and `structural only — not an LLM-as-judge` in the command, plus four literals in `.writ/docs/refresh-log-format.md`. None of those pins may break.
- `scripts/eval.sh` `check_knowledge_consolidate` pins `read-only` and `mutates no knowledge file` in `commands/retro.md`. Step 7 stays as is.
- `.writ/retros/` holds one legacy `2026-03-15.json`. No markdown retro file and no rule table exist.
- `scripts/install.sh` ships `.writ/docs/*.md` (all but one) and no other `.writ/` folder. `is_shippable_script` ships any `*.py` not on its deny list, so `scripts/retro-check.py` ships, and `plugins/writ/scripts/` gains it on regeneration.
- `.writ/docs/agent-cli-contract.md` § Classification has one row per shipped script; `test_table_complete` enforces it.
- `scripts/arch-lint.py detect --repo .` reports architecture rulesets (dependency-cruiser, import-linter, eslint-plugin-boundaries, ArchUnit); `.writ/docs/architecture-lint.md` documents them.

## `retro-check.py`

### Interface

```
python3 scripts/retro-check.py [--retro PATH] [--table PATH] [--repo DIR]
```

- At least one of `--retro` and `--table`, else usage error (exit 2, usage on stderr, stdout empty).
- `--table` defaults to `rule-enforcers.md` in the retro file's directory when `--retro` is given. The default table is read only when it exists or when a finding needs a row.
- `--repo` defaults to `.`; it is where commit SHAs are resolved with `git -C <repo> cat-file -e <sha>^{commit}`.
- `--help` exits 0.
- Read-only. Writes nothing. No network. Python 3.9, standard library.

### Output (check shape, ADR-029)

```
pass|fail|unverifiable
reason: <code> <detail>
...
retro-check: <verdict> (<f> findings, <r> table rows, <n> reasons)
```

Verdict: `fail` when any fail-class reason exists; else `unverifiable` when any unverifiable-class reason exists; else `pass`. Exit 0 for pass and unverifiable, 1 for fail, 2 for usage. Reasons print in file order: retro findings first, then table rows.

### Retro file grammar

- `## Transcripts`: list items; each item's first backticked token, or the item text up to the first space, is a transcript path.
- `## Findings`: blocks starting `### F<n> [<Severity>] <Signal>: <title>`, ending at the next `### ` or `## ` heading.
- Per block, field lines start with `**<Field>:**`: `Rung`, `Ladder`, `Proof`, `Disposition` are read; others are ignored.
- Signals: `Silent patch`, `Stale guidance`, `Repeated mistake`, `User correction` (ladder signals); `Dead end`, `Navigation churn`, `Duplicated work`, `Token sink`, `Writ command defect`.
- Rungs: `architecture`, `types`, `lint`, `test`, `docs`, `none`.
- Ladder: `<rung>: no (<reason>); ... ; <rung>: yes`, split on `;`, each entry `<rung>: yes` or `<rung>: no (<non-empty text>)`.
- Proof: `mistake <ref>; check `<command>`; result <fails|passes|pending>`. `<ref>` is `[0-9a-f]{7,40}` or a path ending in `.jsonl`.
- Disposition: `applied`, `refreshed`, `issue`, `dismissed`, `deferred`.

### Table grammar

- The first markdown table in the file. Header cells exactly `Rule`, `Written in`, `Enforcer`, `Rung`, `Proof`, `Since`.
- Rung cell: `architecture`, `types`, `lint`, `test`, or `docs`.
- Enforcer `none` requires Rung `docs` and Proof `—`. Any other Enforcer requires Proof `<ref>: fails`.
- Since cell: `seed`, or `<retro file name> F<n>`.

### Reason codes

| Code | Class | When |
|---|---|---|
| `retro_missing <path>` | unverifiable | `--retro` path does not exist |
| `table_missing <path>` | unverifiable or fail | unverifiable when `--table` was given explicitly and is missing; fail when the default table is missing and an applied or refreshed ladder finding needs a row |
| `no_findings_section` | fail | retro file has no `## Findings` heading |
| `rung_missing F<n>` | fail | finding has no Rung line |
| `rung_invalid F<n> <value>` | fail | Rung value not in the vocabulary |
| `rung_none_on_mistake F<n>` | fail | ladder signal with Rung `none` |
| `ladder_missing F<n>` | fail | Rung is not `none` and there is no Ladder line |
| `ladder_order F<n>` | fail | entries are not a gap-free prefix of architecture, types, lint, test, docs |
| `ladder_no_reason F<n> <rung>` | fail | a `no` entry has no parenthesized reason |
| `ladder_rung_mismatch F<n>` | fail | last entry is not `yes`, a non-last entry is `yes`, or the `yes` rung differs from Rung |
| `proof_missing F<n>` | fail | Rung is architecture, types, lint, or test and there is no Proof line |
| `proof_malformed F<n>` | fail | Proof line does not match the grammar |
| `proof_ref_unknown F<n> <ref>` | fail | SHA does not resolve to a commit, or the transcript path is not in `## Transcripts` |
| `proof_not_failing F<n>` | fail | Disposition `applied` and result is not `fails` |
| `applied_test_rung F<n>` | fail | Rung `test` and Disposition `applied` |
| `disposition_missing F<n>` / `disposition_invalid F<n> <value>` | fail | no Disposition line / value not in the vocabulary |
| `table_row_missing F<n>` | fail | Disposition `applied` or `refreshed`, Rung not `none`, and no table row's Since cell is `<retro file name> F<n>` |
| `table_header` | fail | header cells differ from the six above |
| `table_rung_invalid row <n> <value>` | fail | Rung cell not in architecture..docs |
| `table_unenforced_rung row <n>` | fail | Enforcer `none` with Rung other than `docs`, or Proof other than `—` |
| `table_enforcer_without_proof row <n>` | fail | Enforcer not `none` and Proof not `<ref>: fails` |
| `table_proof_ref_unknown row <n> <ref>` | fail | Proof SHA does not resolve |
| `no_git` | unverifiable | a SHA needs resolving and `--repo` is not a git work tree, or `git` is not on `PATH` |

A retro file with zero findings and a `## Findings` heading passes.

## `commands/retro.md` changes (by section)

- **Frontmatter.** `description` unchanged. `outcome` gains: each mistake finding fixed at the highest working rung, and a rule table the next run reads. `exit_criteria` gains two lines: (1) "every mistake finding names its rung and the higher rungs it passed over, and every finding fixed at architecture, types, lint, or test cites a proof run against a real past mistake"; (2) "`python3 scripts/retro-check.py --retro <retro file>` printed pass, or its reason lines are in the run's final report". Keep the existing three.
- **Overview → Principles.** Add: "Fix at the highest rung that works. Architecture, then types, then a lint, then a test, then docs."
- **Step 2.** Delete the `signals.jsonl` sentence. Keep "If no transcripts are found, print where you looked and offer `--session <path>`."
- **Step 3.** Rename "Writ friction" to "Writ command defect". Add after the counting rule: "A user correction against a rule whose enforcer is `none` in the rule table counts on its own, as a Repeated mistake."
- **Step 4.** Before ranking, read `.writ/retros/rule-enforcers.md` if it exists. Add the **enforcer did not hold** rule beside **fix did not hold**.
- **Step 5.** Replace the example with one that carries Rule, Rung, Ladder, Target, Change, Proof, Route. Add a `### Fix ladder` table (rung, what it is in `/retro`, route) and the Ladder and Proof grammar in one short paragraph each. Routes table: note that a source or test edit routes `issue` with the proof as the issue's done check. Keep "Never target source code or tests."
- **Step 6.** For Apply on architecture, types, or lint: run the proof after the edit (Business Rule 8). If the check does not fail on the mistake, restore the file to its pre-edit content, set `result passes`, and record `issue`. If the check cannot run, set `result pending` and record `issue`.
- **Step 8.** The retro file uses headings `## Transcripts` and `## Findings`, and each finding carries `**Disposition:**`. Add `## Rule table changes`. Update `.writ/retros/rule-enforcers.md` for each applied or refreshed ladder finding (create it with the heading and header row if absent). Then run `python3 scripts/retro-check.py --retro <file>`. On `fail`, fix the record and re-run once; a second `fail` goes into the final report with its reason lines.
- **Error Handling.** Drop "and use ADR-025 signals if present". Add rows: proof does not fail; proof cannot run; table malformed.
- **Integration with Writ.** Delete the ADR-025 row. `/refresh-command` row: an `execution failure` it logs is a candidate for the ladder on the next retro.
- **Byte ceiling.** The file stays under 24,960 bytes.

## `commands/refresh-command.md` changes (by section)

- **Frontmatter.** `exit_criteria` line 3 names all four reason tokens. Line 1 says "every amendment written to commands/<name>.md or to a skill it read". `description` unchanged.
- **Phase 3.** Before the five required fields, add "**Covered already?**": search the command file and every `skills/<name>/SKILL.md` it names for text that requires the behavior. A covered signal is an execution failure: no proposal; record it for the log with reason `execution failure` and the covering section. Add "**Skill targets**": the rule in Business Rule 14, rejected as `skill not used`.
- **Evidence block.** "Affected section" may read `skills/<name>/SKILL.md → "<section>"`.
- **Step 4.1a.** A skill amendment also runs `bash scripts/lint-skill.sh skills/<name>/SKILL.md`; line 1 `fail` rejects with `eval failed`.
- **Step 4.2.** Rejected examples show all four tokens. "Target file" lists the command and any skill edited.
- **Completion and terminal constraint.** "improves one command file, and the skills that run read, from evidence."
- **Byte ceiling.** The file stays under 24,960 bytes; the additions total under about 2,500 bytes.

## `scripts/eval-refresh-evidence.py` and `.writ/docs/refresh-log-format.md`

- `_REASON_RE` becomes `reason:\s*(no evidence|eval failed|execution failure|skill not used)`. The missing-token message lists the four tokens.
- New scenarios, emitted as PASS/FAIL TSV like the others: `rejected-execution-failure-is-valid-record`, `rejected-skill-not-used-is-valid-record`, `rejected-unknown-token-fails`.
- `refresh-log-format.md` § Rejection reasons gains two rows; the field reference's Rejected and Target file rows name them. The four literals `check_refresh_evidence` pins stay.

## Seeded table (`.writ/retros/rule-enforcers.md`)

Candidate rules, to be confirmed against history by Story 2 (each needs a fix commit whose parent the enforcer fails on):

| Rule | Candidate enforcer | Where to look |
|---|---|---|
| The suite runs on Python 3.9 | `uv run --python 3.9 pytest <test>` | the commit that removed the 3.13-only `pathlib` assumption `CLAUDE.md` mentions |
| Generated trees are never hand-edited or stale | `python3 scripts/gen-platform-trees.py --check` | fix commits touching `plugins/writ/` or `cursor/plugin/` |
| Shipped commands link no Writ-internal history | `python3 scripts/eval-shipped-refs.py` | `2026-10-20-shipped-command-hygiene` Story 1 fixes |
| Instruction files use plain prose | `none` (docs: `skills/plain-prose/SKILL.md`) | — |

Story 2 records the exact command, the parent SHA, and the exit code. A row whose proof cannot be produced is not written with an enforcer.

## Tests

| File | Covers |
|---|---|
| `scripts/tests/test_retro_check.py` | Every reason code in the table above, one fixture each; a conforming retro file and table pass; `--help` exits 0; no arguments exits 2 with empty stdout; read-only (fixture directory unchanged); SHA resolution against a `git init` repo in `tmp_path`; `no_git` outside a repo. |
| `scripts/tests/test_retro_fix_ladder.py` | `commands/retro.md`: the five rungs in order in the Fix ladder table; the Ladder and Proof grammar strings; `.writ/retros/rule-enforcers.md`; `retro-check.py`; "Writ command defect"; absence of `signals.jsonl`, `signal.py`, `ADR-025`, `--friction`, `Writ friction`; byte size under 24,960. The seeded table passes `retro-check.py --table`. |
| `scripts/tests/test_refresh_command_criteria.py` | `commands/refresh-command.md`: "Covered already?", "Skill targets", the four tokens, `lint-skill.sh` in Step 4.1a for skill targets; byte size under 24,960; `scripts/eval-refresh-evidence.py` emits the three new scenario names as PASS. |

## Error & Rescue Map

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| `retro-check.py` reads the retro file | Path missing | `unverifiable`, `reason: retro_missing <path>`, exit 0 | Fixture with a nonexistent path |
| `retro-check.py` reads the table | Explicit path missing | `unverifiable`, `table_missing`; needed default missing → `fail` | Two fixtures |
| `retro-check.py` resolves a SHA | Not a git work tree, or no `git` | `unverifiable`, `reason: no_git` | Run in a non-repo `tmp_path` |
| `retro-check.py` resolves a SHA | SHA unknown | `fail`, `proof_ref_unknown` / `table_proof_ref_unknown` | `git init` fixture with a fabricated SHA |
| `retro-check.py` args | Unknown flag, no input | Exit 2, usage on stderr, empty stdout | `test_agent_cli_contract.py` bad-flag test plus a no-args test |
| `/retro` Step 6 proof run | Check passes on the past mistake | Restore the edited file, `result passes`, disposition `issue` | Read-through in Story 3; `proof_not_failing` fixture guards the record |
| `/retro` Step 6 proof run | Check tool not installed, or the mistake cannot be materialized | `result pending`, disposition `issue`, issue draft carries the proof command | Read-through in Story 3 |
| `/retro` Step 8 table update | Table missing | Create it with heading and header row | `table_row_missing` fixture |
| `/retro` Step 8 retro-check | `fail` twice | Report reason lines in the final report; environment edits stay | Read-through in Story 3 |
| `/refresh-command` skill target | Transcript not readable here | Reject `skill not used` | Pinned text; scenario in `eval-refresh-evidence.py` |
| `/refresh-command` skill target | `lint-skill.sh` line 1 `fail` | Reject `eval failed` | Pinned text |
| Story 2 seeding | Fewer than two qualifying fix commits | Stop the story and report; no synthetic proofs | Story 2 criterion |

## Shadow Paths

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| `retro-check.py --retro` | `pass` | No `--retro` and no `--table` → exit 2 | `## Findings` with no blocks → `pass` | `git` missing → `unverifiable` `no_git` |
| `/retro` ladder finding | Lint rung, proof fails on the past commit, row added | No rule table → created on first applied ladder finding | No mistake findings → no ladder lines, table untouched | Proof check passes on the mistake → restored, `issue` |
| `/refresh-command` signal | Missing rule → evidenced amendment applied | No transcript ID → `no evidence` | Signal already covered → `execution failure`, nothing applied | Skill target with unreadable transcript → `skill not used` |

## Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| Two findings name the same rule | One table row; Since names the first finding; the second is recorded in the retro file only. |
| A finding's past mistake is in an uncommitted transcript snippet | Ref is the transcript path; the snippet is reconstructed into a temp file for the proof. |
| `--report-only` run | All dispositions `deferred`; no table change; `retro-check.py` still runs on the file. |
| Legacy retro file without Rung lines | Not checked; `retro-check.py` runs only on the file the current run wrote. |
| Project with no `.writ/retros/` yet | No table is read; Step 8 creates the folder, and creates the table only when an applied or refreshed ladder finding needs a row. |
| Rule table edited by hand | Next run's `retro-check.py --retro` reads it as is; malformed rows fail the check and are reported. |
