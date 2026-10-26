# Retro Fix Ladder

> **Status:** Not Started
> **Created:** 2026-10-25
> **Owner:** @AdamSellke
> **Dependencies:** []
> **Phase:** 15 — Code-Level Rigor ([roadmap](../../product/roadmap.md), [ADR-030](../../decision-records/adr-030-contract-verifier-boundary-front-door.md))
> **Origin:** Phase 15 decomposition. Roadmap feature "`/retro` fix ladder and rule-to-enforcer table" (Effort S). pstack research F5: the fix ladder and rule table come from pstack's `correct` skill; the two synthesizer criteria come from its `reflect` skill.
> **Mode:** `/create-spec --recommend` (standard). Decisions: [`recommendation-log.md`](recommendation-log.md)

## Specification Contract

**Deliverable:** `/retro` fixes each mistake finding at the highest rung of a five-rung ladder (architecture, types, lint, test, docs), proves every new check fails on a real past mistake, and keeps a rule-to-enforcer table at `.writ/retros/rule-enforcers.md`, all checked by a new shipped `scripts/retro-check.py`. `/refresh-command` counts a finding its guidance already covers as an execution failure, and edits a skill only when the cited transcript used it.

**Must Include:**

1. **Fix ladder in `/retro` Step 5.** A finding whose signal is Silent patch, Stale guidance, Repeated mistake, or User correction (the mistake signals) carries a `**Rung:**` line and a `**Ladder:**` line. The ladder walks architecture, then types, then lint, then test, then docs, and stops at the first rung that works. Each rung it passes over says `no (<reason>)`. Other findings carry `**Rung:** none`.
2. **Proof.** A finding fixed at architecture, types, lint, or test carries a `**Proof:**` line: the past mistake (a commit SHA in this repository, or a transcript the retro read), the check command, and the result. An applied check must fail on the mistake. If it does not, `/retro` restores the edited file and routes the finding `issue`.
3. **Rule-to-enforcer table.** `.writ/retros/rule-enforcers.md` lists each rule a retro finding cited or added, where the rule is written, its enforcer (or `none`), the rung, the proof, and the retro finding it came from. `/retro` reads it before ranking and updates it when a finding is applied or refreshed.
4. **Unenforced rules count as repeats.** A user correction or mistake against a rule whose enforcer is `none` counts as a Repeated mistake on its first occurrence in scope. A mistake against a rule that has an enforcer is marked **enforcer did not hold** and raised one severity level.
5. **`scripts/retro-check.py`**, a shipped check-shape script (ADR-029), validates a retro file and the table: rung vocabulary, ladder order, proof presence and shape, proof refs that resolve (`git cat-file`), applied findings with table rows, and no applied test-rung finding.
6. **Retire the friction-signal remnants in `/retro`.** Remove the `.writ/state/signals.jsonl` evidence sentence, the ADR-025 clause in Error Handling, and the "ADR-025 friction signals" Integration row. Rename the "Writ friction" signal to "Writ command defect". Do not add any signal file, emit line, `Signal:` evidence type, or `--friction` flag.
7. **`/refresh-command` criterion 1.** Before proposing an amendment, check whether the command file, or a skill it reads, already requires the behavior. If it does, the signal is an execution failure: propose no rule text, and log it under `**Rejected:**` with reason `execution failure` and the covering section.
8. **`/refresh-command` criterion 2.** An amendment may target `skills/<name>/SKILL.md` only when the command file references that skill and the cited transcript shows the skill was read in that run. Otherwise reject with reason `skill not used`. Skill amendments pass `bash scripts/lint-skill.sh` in the eval gate.
9. **Seeded table for this repository.** `.writ/retros/rule-enforcers.md` exists in the Writ repo with at least two enforced rows whose proofs were run against real past commits, and at least one row with enforcer `none`.

**Hardest Constraint:** `/retro` never edits source code or tests, yet the types and test rungs are usually code. The ladder still picks the highest rung that works; the route decides who does the work. Config-only fixes (an architecture ruleset, a type-checker setting, a lint rule) route `apply`. Fixes that need source or test edits route `issue`, and the issue draft carries the proof as its done check.

**Success Criteria:**

- `python3 scripts/retro-check.py` prints `pass` on a conforming retro file and table, and `fail` with a named reason on each malformed fixture (missing rung, out-of-order ladder, missing proof, unresolvable SHA, applied finding without a table row, applied test rung).
- `python3 scripts/retro-check.py --table .writ/retros/rule-enforcers.md` prints `pass` in this repository, and each enforced row's proof was produced by running its enforcer against a real past commit.
- `commands/retro.md` names the five rungs in order, the proof rule, the table path, and `retro-check.py`; it contains no `signals.jsonl`, `signal.py`, `ADR-025`, or `--friction`.
- `commands/refresh-command.md` names both criteria and the reason tokens `execution failure` and `skill not used`; `scripts/eval-refresh-evidence.py` accepts those tokens and still rejects a rejection with no token.
- `uv run --python 3.9 pytest`, the bash test loop, and `bash scripts/eval.sh` report no failures and no findings; `python3 scripts/gen-platform-trees.py --check` prints `pass`.

**Scope Boundaries:**

- Included: `/retro` Steps 3 to 8 and its frontmatter; `/refresh-command` Phases 3 and 4, frontmatter, and Completion; `scripts/retro-check.py` and its tests; `scripts/eval-refresh-evidence.py` scenarios; `.writ/docs/refresh-log-format.md` reason tokens; the seeded table; one row in `.writ/docs/agent-cli-contract.md`; regenerated platform trees.
- Excluded: always-on multi-model panels; cross-vendor routing (ADR-024 stands); formal verification; `reflect`'s three-reviewer panel and its other six synthesizer criteria; `correct`'s "common patterns fail only on additions" and "exceptions carry an expiry"; any friction-signal file, emitter, or nudge; edits to `commands/why.md`, `commands/writ.md`, `commands/prototype.md`, `commands/implement-story.md`, `commands/review.md`, `skills/design-divergence/`, `skills/tdd-cycle/`, or `agents/*`; changes to `scripts/eval.sh`.

## Technical Concerns

- **Byte budget.** `COMMAND_BYTE_BUDGET` in `scripts/eval-leanness.py` is 24,960 bytes (reported, non-blocking). `commands/refresh-command.md` is 21,586 bytes today, leaving about 3,370 bytes for both criteria. `commands/retro.md` is 14,135 bytes. `scripts/tests/test_governor_mutation.py` pads `commands/retro.md` by 12,000 bytes and calls the clean file "comfortably compliant". Both files stay under 24,960 bytes.
- **Referenced paths.** `check_referenced_paths` in `scripts/eval.sh` fails a command that backticks a `*.md` path that does not exist in the repo. `commands/retro.md` will cite `.writ/retros/rule-enforcers.md`, so the seeded table (Story 2) lands before the command change (Story 3). This avoids an allowlist row in `scripts/eval.sh`.
- **New shipped script.** `test_table_complete` in `scripts/tests/test_agent_cli_contract.py` fails unless every shipped script has a row in `.writ/docs/agent-cli-contract.md`. Story 1 adds the row. Other Phase 15 specs may add rows to the same table; a row-level merge conflict is possible and mechanical.
- **Generated trees.** `plugins/writ/commands/`, `cursor/plugin/commands/`, and `plugins/writ/scripts/` are generated. Regenerate with `python3 scripts/gen-platform-trees.py`; never hand-edit.
- **Proof needs history.** The seeded table depends on finding real fix commits whose parent the enforcer fails on. `CLAUDE.md` records one (a Python 3.13-only `pathlib` assumption). If fewer than two qualifying commits are found, Story 2's criterion fails and the spec pauses; it does not fall back to synthetic fixtures.

## Experience Design

### Who uses it

- **A maintainer** running `/retro` after `/implement-spec` or `/implement-phase`, in the Writ repo or in a project using Writ.
- **The agent running `/retro`**, which must choose the rung, run the proof, and keep the table.
- **A maintainer running `/refresh-command`** on a command, often handed a finding from `/retro`.

### Journey

1. Entry: `/retro --spec .writ/specs/<id>` or `/retro --since 7d`.
2. The retro reads `.writ/retros/rule-enforcers.md`, then the transcripts, and detects signals.
3. Each mistake finding shows its ladder: `architecture: no (one package); types: no (no checker configured); lint: yes`, with the lint rule as the change.
4. The human approves `Apply`. The retro edits the lint config, runs the proof against the commit that held the mistake, sees it fail, and adds a table row.
5. Step 8 writes the retro file and runs `python3 scripts/retro-check.py --retro <file>`; it prints `pass`.

**Moment of truth:** a finding that reads "lint: yes" with "Proof: mistake 3f2c1ab; check `ruff check src/`; result fails". The maintainer sees the rule is now a check that would have caught the original mistake.

### State Catalog

| State | What the user sees |
|---|---|
| No table yet | The retro says no rules are tabled yet and creates `.writ/retros/rule-enforcers.md` on the first applied or refreshed ladder finding. |
| Mistake against an unenforced rule | The finding says the rule is in the table with enforcer `none`, is ranked as a Repeated mistake, and the ladder proposes an enforcer. |
| Mistake against an enforced rule | The finding is marked **enforcer did not hold**, one level higher, naming the table row. |
| Proof fails to fail | The retro restores the edited file, says the check passed on the past mistake, and records the finding as `issue` with `result passes`. |
| Proof cannot run (tool not installed) | The finding routes `issue` with `result pending`; the issue draft carries the proof command as its done check. |
| Docs rung chosen | The Ladder line explains why each higher rung does not work; no proof is required; the table row has enforcer `none`. |
| `retro-check.py` prints `fail` | The retro fixes its own record and re-runs once. A second `fail` is reported with its reason lines; the environment edits stay. |
| `/refresh-command` signal already covered | The proposal list shows it under Rejected with `execution failure` and the covering section, and suggests `/retro` if it recurs. |
| `/refresh-command` skill target not used | Rejected with `skill not used`, naming the skill and the transcript. |

## Business Rules (Expanded)

1. **Rung vocabulary.** `architecture`, `types`, `lint`, `test`, `docs`, in that order, and `none` for findings outside the ladder. Spelled exactly so in the command, the retro file, the table, and the script.
2. **Ladder signals.** Silent patch, Stale guidance, Repeated mistake, User correction. Dead end, Navigation churn, Duplicated work, Token sink, and Writ command defect carry `**Rung:** none` by default. The retro may ladder one of them when a check would prevent it; any finding with a rung other than `none` carries a valid Ladder line and follows the proof rules.
3. **Ladder line.** `**Ladder:** <rung>: no (<reason>); ...; <rung>: yes`. It starts at `architecture`, lists rungs in order without gaps, gives every `no` a reason in parentheses, ends with the one `yes`, and that rung equals the Rung line.
4. **Rung meaning in `/retro`.** architecture: a ruleset `python3 scripts/arch-lint.py detect` finds (see `.writ/docs/architecture-lint.md`), or a boundary or layout rule. types: a type-checker setting. lint: a lint rule whose message names the fix. test: a test that fails on the mistake. docs: a steering file, doc, skill, command, or `/knowledge` entry.
5. **Route by edit type.** Config-only architecture, types, and lint fixes route `apply`. Any fix that needs a source or test edit routes `issue`. A test-rung finding never has disposition `applied`. Docs-rung fixes keep the current routes (`apply`, `refresh`, `knowledge`).
6. **Proof line.** `**Proof:** mistake <ref>; check `<command>`; result <fails|passes|pending>`. `<ref>` is a 7 to 40 character hex commit SHA that resolves in the repository, or a transcript path listed in the retro file's `## Transcripts` section. A synthetic fixture written for the occasion is not a past mistake.
7. **Proof outcomes.** `applied` requires `result fails`. `issue` allows `pending` or `passes`. `dismissed` and `deferred` allow any result. A proof is required for architecture, types, lint, and test rungs, and not for docs.
8. **Running a proof.** Materialize the mistake without touching the working tree: `git show <sha>:<path>` into a temp directory, or `git worktree add --detach <tmp> <sha>` for checks that need the whole tree, removed afterwards. For a transcript ref, reconstruct the snippet the transcript quotes into a temp file. Run the check with the new config against it.
9. **Table format.** `.writ/retros/rule-enforcers.md`, heading `# Rule-to-Enforcer Table`, one table with columns `| Rule | Written in | Enforcer | Rung | Proof | Since |`. Enforcer is a command or config path in backticks, or `none`. `none` implies rung `docs` and Proof `—`. Any other enforcer has a Proof cell `<ref>: fails`. Since is `<retro file name> F<n>` or `seed`.
10. **Table location.** `.writ/retros/` is project history, committed with the retro file, and not shipped by `install.sh`. The table is not placed in `.writ/docs/`, which ships to every installed project.
11. **Unenforced and failed enforcers.** Rule 4 of the contract above. A match is by rule and target, read from the table.
12. **Retro file headings** that `retro-check.py` reads: `## Transcripts` (one list item per path) and `## Findings` (one `### F<n> [<Severity>] <Signal>: <title>` block per finding, each with `**Rung:**` and `**Disposition:**` lines).
13. **Refresh execution failure.** Covered means the command file or a skill it reads already states the behavior the signal shows was skipped. Moving, repeating, or rewording that guidance is not proposed. The log entry names the covering section.
14. **Refresh skill targets.** Allowed only when the command file contains the skill's `skills/<name>/SKILL.md` path and the cited transcript is readable here and contains a read of that path or an invocation of that skill by name. An unreadable transcript cannot show use.
15. **Reason tokens.** `/refresh-command` rejects with `no evidence`, `eval failed`, `execution failure`, or `skill not used`, and no other token.
16. **Plain prose.** All added command text follows `skills/plain-prose/SKILL.md`. No links to `.writ/research/`, `.writ/decision-records/`, or archived specs from shipped commands (`check_shipped_refs`).
17. **Python 3.9 floor, standard library only** for `scripts/retro-check.py` and its tests. Subprocess calls use an argument list, never `shell=True`.

## Detailed Requirements

### Story 1: `retro-check.py`

- New `scripts/retro-check.py`, check shape: line 1 `pass`, `fail`, or `unverifiable`; `reason:` lines; summary `retro-check: <verdict> (<f> findings, <r> table rows, <n> reasons)`. Exit 0 for pass or unverifiable, 1 for fail, 2 for usage.
- Interface and reason codes: `sub-specs/technical-spec.md` → ## `retro-check.py`.
- New `scripts/tests/test_retro_check.py`, tests first, with fixtures built in `tmp_path` and a throwaway git repository for SHA resolution.
- Row `| retro-check.py | check |  | commands/retro.md |` in `.writ/docs/agent-cli-contract.md`. Regenerate trees.

### Story 2: Seed this repository's table

- Find at least two fix commits in this repository's history where an existing enforcer (a pytest test, an eval check, `gen-platform-trees.py --check`, or similar) fails on the fix commit's parent and passes on the fix. Run each and record the result.
- Write `.writ/retros/rule-enforcers.md` with those rows (Since `seed`) and at least one row with enforcer `none` for a rule only prose states.
- Test that `retro-check.py --table` passes on the seeded file.

### Story 3: `/retro` ladder, proof, table, and retirement

- Edit `commands/retro.md` per Must Include 1 to 6 and Business Rules 1 to 12. Update `outcome` and `exit_criteria` in the frontmatter; leave `description` unchanged.
- New `scripts/tests/test_retro_fix_ladder.py` pins the command text.
- Regenerate trees.

### Story 4: `/refresh-command` criteria

- Edit `commands/refresh-command.md` per Must Include 7 and 8 and Business Rules 13 to 15: Phase 3 classification, the Evidence block's affected section for skills, Step 4.1a's lint for skill targets, the Step 4.2 log, the exit criteria, Completion, and the terminal constraint.
- Extend `scripts/eval-refresh-evidence.py` (`_REASON_RE`, two valid-record scenarios) and `.writ/docs/refresh-log-format.md` (Rejection reasons table, Target file field).
- New `scripts/tests/test_refresh_command_criteria.py` pins the command text. Regenerate trees.

## Implementation Approach

- **Order.** Story 1, then Story 2, then Story 3. Story 4 is independent and can run beside any of them.
- **Edit by section heading**, never by line number.
- **Tests read markdown as text**, in the style of `scripts/tests/test_prompting_guide.py`. Test docstrings name the AC IDs they cover.
- **No `scripts/eval.sh` change.** The new reason tokens run through the existing `check_refresh_evidence` scenario loop; the command pins live in pytest.
- **Verification after each story:** `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, `python3 scripts/gen-platform-trees.py --check`, and `bash scripts/eval.sh` outside any sandbox.
