# Technical spec — flagged harness cuts

> Parent: `.writ/specs/2026-09-24-flagged-harness-cuts/spec.md`

## Flag

`WRIT_HARNESS_LEAN` is set to `1` or unset. Any other value is treated as unset and warned once. The loader in `scripts/measure-invocation.py` and `scripts/story-context.py` read it from the environment. Commands do not grow a second copy of their body.

| Flag | Files loaded | Over-budget context |
|---|---|---|
| Unset | `commands/_preamble.md` and `commands/<name>.md` | Truncate and warn, current behavior |
| `1` | The `.lean.md` sibling when it exists, else the default file plus a warning that names the missing sibling | Write the full text under `.writ/state/` and return path, size, and a short tail |

Lean siblings this spec creates:

- `commands/_preamble.lean.md`
- `commands/create-spec.lean.md`
- `commands/verify-spec.lean.md`
- `commands/implement-phase.lean.md`
- `commands/implement-story.lean.md`

`measure-invocation.py` excludes `*.lean.md` from the default floor. A test hashes or counts bytes of the unset invocation and fails if a lean file’s bytes are included.

## Spill

When the flag is `1` and story-context bytes exceed the budget, `story-context.py` writes the pre-truncation payload to `.writ/state/story-context-spill-<story-id>.md` and sets:

- `truncated` remains the signal that the inline payload is not the full text
- `spill.path`, `spill.bytes`, and a tail of at most 500 bytes inside `fetched_context` for the category that was cut

Flag unset does not write a spill file and does not add `spill`. Existing `enforce_budget` tests pass without the variable set.

The “What Was Built” 1,000-line rule is prose in `skills/dependency-context-loading/SKILL.md`. The default skill text stays truncate-by-priority. The lean implement-story body points at a spill file instead. This spec does not change the default skill’s truncate wording.

## Keep or revert

The model is the current default frontier for the family under test. Claude Opus 5.5 is that default for much of this work. GPT-6 Astra is the OpenAI counterpart. Fable 5.1, the model in `.writ/eval/baselines/2026-09-07-claude-fable-5-1.json`, is an older measured run and sits below both. Story 5 does not treat that file as the cost opponent.

Story 5 runs the same four stories × 2 twice on one model: flag on, and flag off. `pipeline-baseline.py compare` is between those two runs. Relative prowess is the scope of a keep: the lean default may apply to that model and to models at least as capable. It does not apply downward to a weaker model.

| Outcome | Condition | What the maintainer is left with |
|---|---|---|
| Keep | Every exit-criteria row is 2/2 and flag-on `cost_usd` is lower than the same-model flag-off control | Default load path becomes the lean siblings for models of that prowess or higher. Decision log names the model and includes the numbers. |
| Null | Exit criteria hold and same-model `cost_usd` does not drop | Default load path unchanged. Decision log says null, names the model, and includes the numbers. |
| Quality miss | Any exit-criteria row under 2/2 | Default load path unchanged (revert the flip if it was applied). The compare table is recorded. |

`cost_usd` is the price. `scripts/harness-cost.py` prints the formula beside it and does not decide.

## Error & Rescue Map

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| Read the flag | Value other than `1` or unset | Treat as unset. One warning names the value. | Unit test with `WRIT_HARNESS_LEAN=yes` |
| Load a lean sibling | Sibling missing while flag is `1` | Load the default file. Warning names the missing path. | Unit test with the flag set and no sibling |
| Spill over-budget context | `.writ/state/` not writable | Warning names the error. Inline payload is the current truncated form, and the warning says the spill was not written. | Unit test with a read-only state dir |
| Keep-or-revert | Compare selection mismatch | Do not flip the default. Record the compare error. | Fixture baseline with a mismatched story id |

## Shadow Paths

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| Flag off assemble | Same truncate warning as today | No spill file, floor unchanged | Empty category stays empty, no false spill | Budget script error leaves the payload’s existing warning list |
| Flag on assemble | Lean text selected; over budget writes a spill file and returns path, size, tail | Variable unset is the nil path: default files | Under budget: no spill file | State dir not writable: warning plus truncated inline text |
| Baseline decision | Keep line, lean files become the default | No new baseline file: do not flip, say the file is missing | Empty `runs` array: do not flip | An exit-criteria row under 2/2: revert flip, record the table |

## Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| Flag set in the unit-test process by accident | Tests that assert the default path clear the variable first |
| Lean preamble grows past 95 lines | Story 2 fails. Do not raise the `check_length` cap. The default preamble is the file the cap measures, and it must stay ≤95. |
| Default command edited to contain both bodies | Floor byte test fails |
| Story 5 run twice | Second run reconciles against the repo. A prior keep is not inferred from the decision-log line alone. |
