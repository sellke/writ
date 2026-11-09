# Technical Spec: Review-Route Rigor

> Parent: [`spec.md`](../spec.md) · Stories: [`user-stories/`](../user-stories/README.md)

## Current State (audit, 2026-10-25)

- **Gate 2.5** (`commands/implement-story.md`) runs `change-surface.py classify`, then `boundary-map.py crossings`, whose `route` becomes `gate3_route`. `crossings` routes `review-agent` on any out-of-scope or readable crossing, on `full_stack_surface`, or on `map_unreadable`. An `unverifiable` helper also routes `review-agent`.
- **Gate 3** spawns `evaluator-agent` by default and swaps in `review-agent` when `gate3_route` names it. After the agent returns, `review-override.py check` re-derives a FAIL-only verdict from `ac-trace.py` and `test-integrity.py`. The story report prints `gate3-route:`.
- **`review-agent`** (`agents/review-agent.md`) has no input for recorded test results, no blast radius, and no safety-fact section. Its review principles include "Security is never Minor."
- **`evaluator-agent`** gets `recorded_test_results` (the orchestrator's own run) and scans residual architecture, security, and taste.
- **`/review`** (`commands/review.md`) builds a Failure Modes Registry with Critical/High/Medium/Low severities and saves `.writ/state/review-<branch>.md`.
- **Claude Code native agents.** `scripts/gen-claude-agents.py` writes `claude-code/agents/writ-reviewer.md` and `writ-evaluator.md` from the canonical bodies verbatim, plus an overlay. `scripts/gen-platform-trees.py` runs it with every other generator. Hand edits to generated files are stale on the next `--check`.
- **Config-line switches already exist:** `- **Review Panel:**` (`review-panel.py status`) and `- **Judgment Provider:**` (`jev-judge.py status`). This spec follows that pattern.
- **Agents already read skills:** `coding-agent` reads `skills/tdd-cycle/SKILL.md`; `testing-agent` reads it too. A reviewer reading a skill is not new.
- **Sizes:** `commands/implement-story.md` 36,226 bytes; `agents/review-agent.md` 20,231; `agents/evaluator-agent.md` 9,480; `commands/review.md` 10,300.

## Switches

| Switch | Config line (`.writ/config.md`) | Controls |
|---|---|---|
| `safety-fact` | `- **Safety Fact:** off` | Gate 2.5 blast radius, the `review-agent` safety-fact section, the `safety-fact` verifier, `skills/blast-radius/SKILL.md` |
| `reviewer-filters` | `- **Reviewer Filters:** off` | Whether `review-agent`, `evaluator-agent`, and `/review` read `skills/review-judgment-filters/SKILL.md` |

Default on. A trial's off arm adds one line; its on arm removes the line or writes `on`.

### Resolver

```bash
python3 scripts/review-override.py switch --name safety-fact|reviewer-filters [--repo .]
```

Check shape (`.writ/docs/agent-cli-contract.md`):

```
off
reason: config_off
review-override switch: safety-fact off (.writ/config.md)
```

| Input | Line 1 | `reason:` | Exit |
|---|---|---|---|
| no `.writ/config.md`, or unreadable | `on` | `no_config` | 0 |
| file present, no line for this switch | `on` | `no_config_line` | 0 |
| value `off` (any case, surrounding whitespace ignored) | `off` | `config_off` | 0 |
| value `on` or empty | `on` | `config_on` | 0 |
| any other value | `on` | `malformed_value <value>` | 0 |
| unknown `--name`, or no `--name` | stdout empty, usage on stderr | — | 2 |

Pattern: `^- \*\*Safety Fact:\*\*[ \t]*(.*)$` and `^- \*\*Reviewer Filters:\*\*[ \t]*(.*)$`, multiline, first match wins. The `check` subcommand is unchanged.

## Blast Radius

```bash
python3 scripts/change-surface.py blast-radius --changed FILE … [--repo .] [--limit 20] [--pretty]
```

For each changed file that is not a test file:

1. **Search tokens.** The repo-relative path with and without its extension (`scripts/review-override.py`, `scripts/review-override`). Also the file stem (`review-override`), unless the stem is shorter than 4 characters or is generic: `index`, `main`, `mod`, `__init__`, `utils`, `util`, `types`, `type`, `constants`, `config`, `helpers`, `readme`, `setup`, `app` (case-insensitive). A token matches only when the characters on both sides are not `[A-Za-z0-9_-]`.
2. **Candidates.** `git ls-files` run in `--repo`. If git fails, walk the repo, skipping `.git/`, `node_modules/`, and dot-directories. Always skip `.writ/` (specs and state reference files but do not call them), every changed file, and any file over 1 MB or not valid UTF-8.
3. **Split.** A matching candidate goes to `tests` when it looks like a test (`.test.`, `.spec.`, `__tests__/`, `test_*.py`, `*_test.py`, `*_test.go`, or a `test/` or `tests/` path segment) and to `consumers` otherwise. This test check is a new helper; `is_test`, which `classify` uses, does not change.
4. **Cap.** At most `--limit` entries per changed file per list, sorted by path. A capped file is listed under `truncated`.

JSON (default; `--json` is a no-op, as for `classify`):

```json
{"verdict": "pass",
 "consumers": {"agents/review-agent.md": ["commands/implement-story.md"]},
 "tests": {"agents/review-agent.md": ["scripts/tests/test_review_override.py"]},
 "truncated": [],
 "reasons": []}
```

- `verdict` is `pass`, or `unverifiable` with `reasons: ["repo_unreadable"]` when `--repo` is not a readable directory. A git failure adds the informational reason `no_git_walked` and keeps `pass`.
- `--pretty` prints the verdict line, one `<changed>: <n> consumer(s), <m> test(s)` line per changed file, `reason:` lines, and the summary `change-surface blast-radius: <verdict> (<n> changed, <k> consumers)`.
- Exit 0 for `pass` or `unverifiable`, 2 for an empty `--changed` or other usage. `classify` output and exit codes do not change.

## Evidence Ladder

The ladder is ordered weakest to strongest. A rung's evidence stands on its own. The ladder is not cumulative: a fact can reach `tested` without a `read` line.

| # | Rung | Meaning | Evidence line | The verifier accepts it when |
|---|---|---|---|---|
| 1 | `claimed` | Someone said so: the coding agent's report, a commit message, a comment, the spec. | none | `**Fact:**` is non-empty |
| 2 | `read` | The reviewer read the code that makes the fact true. | `- read: path:line` | `path` exists inside `--repo` and `line` (or the start of `line-line`) is no greater than the file's line count |
| 3 | `traced` | The reviewer followed the changed code to its callers, and each cited caller is consistent with the fact. | `- traced: path:line — <what this caller passes or expects>`, or `- traced: none — <search run>` | Every cited `path:line` is valid as for `read`, and at least one is. When the blast-radius file is readable, its verdict is `pass`, and its `consumers` are non-empty, at least one cited path is in the union of `consumers`. `none` is accepted only when the blast-radius file is readable, its verdict is `pass`, and the union of `consumers` is empty. |
| 4 | `tested` | A test exercises the fact and passed in the orchestrator's recorded run. | `- tested: path::test_name` | `path` exists, `test_name` occurs in its text, the tests-output file has a line `exit code: 0`, and `path` occurs in the tests-output text |
| 5 | `reproduced` | The fact was observed in the running app. | `- reproduced: path/to/evidence/<label>/<feature>/result.json` | the file exists, parses as JSON, `schema` is `app-verify-result-v1`, and `verdict` is `pass` |

**Measured rung:** the highest rung whose evidence the verifier accepts. **Floor on the review-agent route:** `traced` (3).

`reproduced` is out of reach on a first Gate 3 pass because Gate 4.5 runs after Gate 3. It is reachable on a recode iteration where `app-verify.py run` already wrote a passing `result.json` for this story. Evidence from an earlier iteration may predate the current code; the skill tells the reviewer to cite it only when the feature's checked paths were not changed since.

## Safety Fact Section

`review-agent` writes this section after `### Security Assessment` when `safety_fact` is `on`:

```markdown
### Safety Fact
**Fact:** <one sentence: the single fact this change is safe because of>
**Holds:** yes | no
**Rung:** claimed | read | traced | tested | reproduced
**Evidence:**
- read: `scripts/review-override.py:142`
- traced: `commands/implement-story.md:292` — passes --story and --spec, never --route
- tested: `scripts/tests/test_review_override.py::test_switch_off`
```

Rules the skill states:

- One fact. If the change is safe only because of two facts, name the weaker one.
- Name a fact about the code, not about the process ("no caller passes an empty list", not "the tests pass").
- Push the fact up the ladder as far as the evidence allows. Trace before writing `traced`; cite the test before writing `tested`.
- If tracing finds a caller that breaks the fact, write `**Holds:** no`, cite that caller, and FAIL with an issue at that location (category `architecture`, or `security` when it is one).
- Start from `blast_radius`. When it is `(none)` or unverifiable, search for callers yourself and cite them.

## Verifier

```bash
python3 scripts/review-override.py safety-fact --review-output FILE [--repo .] \
  [--blast-radius FILE] [--tests-output FILE]
```

**Parsing.**
- The section starts at a heading line matching `^#{2,6}\s*Safety Fact\s*$` and ends at the next heading.
- Fields are `**Fact:**`, `**Holds:**`, `**Rung:**`, and `**Evidence:**`. Matching is case-insensitive, and the bold markers are optional.
- Evidence lines are `- <rung>: <value>`. Backticks around a value are stripped.
- The review verdict comes from the first `REVIEW_RESULT:` or `EVALUATION_RESULT:` heading, with the same pattern `review-panel.py` uses.
- Cited paths are resolved against `--repo`. A path that resolves outside `--repo` is rejected.

**Output** (check shape):

```
fail
rung: claimed=tested measured=read
fact: no caller passes --route to review-override.py check
reason: safety_fact_below_floor read
review-override safety-fact: fail (measured read, floor traced)
```

| Condition | Line 1 | `reason:` | Exit |
|---|---|---|---|
| section present, measured ≥ `traced`, and (`Holds: yes`, or `Holds: no` with verdict FAIL or PAUSE) | `pass` | none | 0 |
| no section, empty `Fact`, `Rung` not one of the five, or `Holds` not `yes`/`no` | `fail` | `safety_fact_missing <what>` | 1 |
| measured < `traced` | `fail` | `safety_fact_below_floor <measured>` | 1 |
| `Holds: no` with verdict PASS | `fail` | `safety_fact_contradicts_verdict` | 1 |
| `--review-output` missing or unreadable | `unverifiable` | `review_output_unreadable` | 0 |
| `--review-output` not given | stdout empty, usage on stderr | — | 2 |

When more than one fail reason applies, all are printed in the table's order. A claimed rung above the measured rung is not a reason on its own; the `rung:` line shows both. An unreadable `--blast-radius` or `--tests-output` is not unverifiable: the rungs that need it cannot be accepted, and the measured rung falls.

## Gate 2.5 Change (draft, `commands/implement-story.md`)

Append after the existing `unverifiable` sentence:

> **Blast radius.** When `gate3_route` names `review-agent`, run `python3 scripts/review-override.py switch --name safety-fact`. On `on`, run `python3 scripts/change-surface.py blast-radius --changed <files> --repo . > .writ/state/blast-radius-<story-stem>.json` and pass the file to Gate 3 as `blast_radius`. Otherwise `blast_radius` is `(none)`.

## Gate 3 Change (draft, `commands/implement-story.md`)

Inputs paragraph (risk route): add `recorded_test_results`, `safety_fact` (`on` when Gate 2.5 wrote a blast radius, else `off`), and `blast_radius`. Every Gate 3 spawn gets `reviewer_filters`, from `python3 scripts/review-override.py switch --name reviewer-filters`. Panel reviewers receive the same inputs, as they already do.

New paragraph after the `review-override.py check` bullets:

> **Safety fact (risk route, `safety_fact` on).** Save the agent output to `.writ/state/gate3-review-<story-stem>.md` and `recorded_test_results` to `.writ/state/gate3-tests-<story-stem>.txt` (lines `command: …`, `exit code: N`, then the output tail). Run `python3 scripts/review-override.py safety-fact --review-output <that file> --repo . --blast-radius <Gate 2.5 file> --tests-output <that file>`.
> - `safety_fact_missing` or `safety_fact_below_floor` → re-spawn `review-agent` once with the `reason:` lines appended, then re-run the verifier. The two spawns count as one Gate 3 attempt.
> - Still `safety_fact_missing` → BLOCKED escalation, agent `review-agent`, restart Gate 3.
> - Still `safety_fact_below_floor`, or `safety_fact_contradicts_verdict` → Gate 3 FAIL on the review-loop recode path. Pass the fact and the measured rung to the coder, and ask for a test that exercises the fact. An agent FAIL in the same pass is still one increment. On PAUSE, list the lines with the drift options; accept still recodes.
> - `unverifiable` → continue, print the reason, not `⚠️ DEGRADED`.
>
> The story report prints `reviewer-filters: <on|off>` and `safety-fact: <measured> (claimed <claimed>) — <fact>`. When the safety fact does not apply, it prints `safety-fact: off` or `safety-fact: not on route`.

**Byte budget:** Gate 2.5 and Gate 3 grow by at most 1,800 bytes net, measured with `wc -c commands/implement-story.md` before and after. The ladder, the section format, and the filters stay in the skills.

## Agent and Command Changes

| File | Change |
|---|---|
| `agents/review-agent.md` | Input rows: `recorded_test_results`, `reviewer_filters` (`on`/`off`), `safety_fact` (`on`/`off`), `blast_radius` (JSON or `(none)`). Prompt: two conditional lines — "When `{reviewer_filters}` is `on`, `Read skills/review-judgment-filters/SKILL.md` and apply it before you set REVIEW_RESULT." and "When `{safety_fact}` is `on`, `Read skills/blast-radius/SKILL.md` and write its `### Safety Fact` section, starting from `{blast_radius}`." Output format: one slot line, `### Safety Fact (only when safety_fact is on; format in the skill)`. |
| `agents/evaluator-agent.md` | Input row `reviewer_filters`; the same filters line before EVALUATION_RESULT. No safety fact: the evaluator never runs on the risk route. |
| `commands/review.md` | Step 3 opens with: run `python3 scripts/review-override.py switch --name reviewer-filters`; on `on`, `Read skills/review-judgment-filters/SKILL.md` and apply it before Technique 4 assigns severities and before the Recommendation. Step 4's report header gains `> Reviewer filters: on|off`. |
| `.writ/manifest.yaml` | Two `skills:` entries, `status: candidate`. |
| `README.md`, root `SKILL.md` | A `## Skills` table row per new skill and the live-skill count; root `SKILL.md` regenerated with `bash scripts/gen-skill.sh` (Stories 2 and 4). |
| `.writ/docs/config-format.md` | A key-table row and a short section for `Safety Fact` and `Reviewer Filters`: line format, default on, malformed rule (Story 1). |
| generated trees | `python3 scripts/gen-platform-trees.py` after each story that edits `agents/`, `commands/`, or `skills/`. |

## Filters Skill (draft body)

`skills/review-judgment-filters/SKILL.md`, frontmatter `disable-model-invocation: true`, `status: candidate`, `status_evidence: "Phase 15 (2026-10-25). 3 consumers: agents/review-agent.md, agents/evaluator-agent.md, commands/review.md."`. Description (passes `lint-skill.sh`): "Separate findings that change a verdict from nits and untraced hypotheticals, without dismissing security findings."

Body sections: Purpose; When to Use (any reviewer about to set a verdict or a ship recommendation); How to Apply with the three filters from `spec.md` § Filters, in that order, each with one example. Filter order matters: apply 3 before 2, so a security finding is never dropped by the hypothetical rule. For `/review`, "nit" maps to Low and "Major or above" maps to High or above.

## Blast-Radius Skill (outline)

`skills/blast-radius/SKILL.md`, `status: candidate`, `status_evidence: "Phase 15 (2026-10-25). 1 consumer: agents/review-agent.md; kept as a skill so the safety-fact switch can remove it cleanly."`. Description: "Name the one fact a change is safe because of and push its evidence up a five-rung ladder."

Sections: Purpose; When to Use; the Evidence Ladder table (rungs 1–5, meaning, evidence line); the Safety Fact section format and rules (§ Safety Fact Section); reading `blast_radius` JSON; when `Holds: no`.

## Clean Removal

**Remove `safety-fact`:**
1. Delete `skills/blast-radius/`, its `.writ/manifest.yaml` entry, its README row, and its `.writ/docs/config-format.md` row and section; rerun `bash scripts/gen-skill.sh`.
2. Delete the `safety-fact` subcommand and the `safety-fact` name from `switch` in `scripts/review-override.py`, and their tests.
3. Delete the `blast-radius` subcommand from `scripts/change-surface.py`, and its tests.
4. Delete the Gate 2.5 "Blast radius" paragraph, the Gate 3 "Safety fact" paragraph, and the `safety_fact`/`blast_radius` inputs in Gate 3.
5. Delete the `review-agent` input rows `safety_fact`, `blast_radius`, and `recorded_test_results`, the safety-fact conditional line, and the output slot line. Delete the Gate 3 save of `gate3-tests-<story-stem>.txt`.
6. Regenerate trees.

**Remove `reviewer-filters`:**
1. Delete `skills/review-judgment-filters/`, its manifest entry, its README row, and its `.writ/docs/config-format.md` row and section; rerun `bash scripts/gen-skill.sh`.
2. Delete the `reviewer-filters` name from `switch` and its tests.
3. Delete the input row and conditional line in both agents, the Step 3 lines and header line in `commands/review.md`, and the `reviewer_filters` input and report line in Gate 3.
4. Regenerate trees.

If both are removed, delete the `switch` subcommand.

## Tests

| File | Covers |
|---|---|
| `scripts/tests/test_review_override.py` (extend) | `switch`: every row of the resolver table, both names. `safety-fact`: each rung accepted and rejected, the floor, each fail reason, multi-reason order, overclaim line, path escaping `--repo`, unreadable review output, missing `--review-output`. `check`: existing tests stay green. |
| `scripts/tests/test_change_surface.py` (extend) | `blast-radius`: stem match, path match, generic-stem path-only match, token boundaries, `.writ/` and changed-file exclusion, test split, cap and `truncated`, no-git walk, non-UTF-8 and >1 MB skip, empty `--changed` exit 2, `--pretty` shape. `classify`: existing tests stay green. |
| `scripts/tests/test_review_route_rigor.py` (new) | Each skill exists and passes `bash scripts/lint-skill.sh`. Distinctive filter sentences and ladder rung definitions occur in their skill and in none of `agents/*.md`, `commands/*.md`, or `claude-code/agents/*.md`. The conditional `Read` lines and input rows are present in `review-agent.md`, `evaluator-agent.md`, and `review.md`. Both manifest entries exist. |

All tests run under `uv run --python 3.9 pytest`. Fixtures are built in `TemporaryDirectory`, as the existing review-override tests do.

## Shadow Paths

| Flow | Happy | Nil | Empty | Upstream error |
|---|---|---|---|---|
| Switch resolution | line `off` → `off` | no config file → `on`, `no_config` | `- **Safety Fact:**` with no value → `on`, `config_on` | unreadable file → `on`, `no_config` |
| Blast radius | consumers listed per changed file | `--changed` omitted → exit 2 | every changed file is a test → empty maps, `pass` | no git → walk, `no_git_walked`; bad `--repo` → `unverifiable` |
| Safety-fact verify | measured ≥ `traced` → `pass` | no `--review-output` → exit 2 | section present, no evidence lines → measured `claimed` → `below_floor` | review file unreadable → `unverifiable` |
| Gate 3 routing | `pass` → continue | — | — | verifier crashes (non-0/1/2 exit) → treat as `unverifiable`, print the exit code |

## Error & Rescue Map

| Operation | What fails | Rescued? | Test? | What the user sees |
|---|---|---|---|---|
| `switch` reads `.writ/config.md` | file absent or unreadable | Yes: default on | Yes | `on` with `reason: no_config` in the story report |
| `switch` parses value | typo (`of`) | Yes: default on | Yes | `reason: malformed_value of`; the trial operator sees the arm did not switch |
| `blast-radius` lists candidates | `git ls-files` fails | Yes: filesystem walk | Yes | `reason: no_git_walked` |
| `blast-radius` reads a candidate | binary, non-UTF-8, or >1 MB | Yes: skipped | Yes | nothing; file absent from lists |
| `blast-radius` on a huge repo | slow scan | Partial: one pass, one compiled pattern per changed file | No | Gate 2.5 takes longer; no failure |
| `safety-fact` reads review output | file missing | Yes: `unverifiable` | Yes | `safety-fact: unverifiable (review_output_unreadable)`; Gate 3 continues |
| `safety-fact` resolves a cited path | path escapes `--repo` (`../../etc/passwd:1`) | Yes: evidence rejected | Yes | measured rung falls; possibly `below_floor` |
| `safety-fact` reads blast radius | file missing or malformed | Yes: `traced` needs an existing caller cite, `none` rejected | Yes | measured rung may fall |
| `safety-fact` reads tests output | file missing, or no `exit code: 0` | Yes: `tested` not accepted | Yes | measured rung falls to the next accepted rung |
| Reviewer omits the section twice | — | Yes: BLOCKED escalation | No (prose) | the BLOCKED AskQuestion for `review-agent` |
| Reviewer cannot reach `traced` twice | — | Yes: recode with "add a test that exercises the fact" | No (prose) | a Gate 3 FAIL line naming the fact and its measured rung |
