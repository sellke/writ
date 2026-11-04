---
name: evidence-gated-findings
description: "Back a Critical or Major review finding with evidence a script can run or check, so the finding can block a verdict."
disable-model-invocation: true
status: candidate
status_evidence: "Phase 15 (2026-11-04). Spec 2026-11-04-evidence-gated-review."
---

# Evidence-Gated Findings

## Purpose

A review finding blocks only when it carries executed evidence (ADR-032).
This skill defines that evidence: one `**Evidence:**` field on a Critical or
Major issue, in one of four kinds. A script runs or checks the evidence. A
finding with no evidence, or with evidence that does not confirm, is still
reported, but only as advisory.

This skill owns the evidence grammar and how to write a repro. The consumer
owns when the evidence step runs and what its result does to the verdict.

## When to Use

- You are writing a Critical or Major issue under `### Issues Found`, and the
  issue should block.
- Lower severities never block, and their evidence never runs. Leave them
  without an Evidence field.

## How to Apply

### Which findings can block

The script evaluates an issue only when all three hold:

- Severity is Critical or Major.
- Location names a file in the story's change set.
- The issue cites an AC ID (`AC-N.M`) in its Category, Issue, or Location, or
  its Category is `security` or `architecture`.

Any other issue is advisory, whatever evidence it carries. Issues are keyed F1
to Fn in the order they appear.

### The Evidence field

Write one `**Evidence:**` field after `**Category:**`. Its first word names
the kind. The script ignores a second Evidence field on the same issue.

| Kind | Field form | Confirmed when |
|---|---|---|
| `test` | `test <path>`, then one fenced code block | the project's `Test Runner`, scoped to that file, reports a test failure |
| `recorded` | `recorded <path>::<test name>` | the recorded test run exited non-zero and names that test as failed |
| `check` | ``check `<command and arguments>` `` | the command starts with a static check Gate 2 ran, exits non-zero, and its output names a changed file |
| `security-path` | `security-path source <path:line> sink <path:line>` | Category is `security`, both citations resolve to a real line, and the sink is in the change set |

`recorded` and `security-path` cost no run. `test` and `check` run, at most
five per review, each under a timeout of 120 seconds by default. Put the
findings you most need to block first.

Example:

````markdown
- **Issue:** `parse_limit()` accepts a negative limit and returns every row
- **Location:** `api/limits.py:31`
- **Severity:** Major
- **Category:** criterion [AC-2.3]
- **Evidence:** test `tests/test_limits_repro.py`
  ```python
  from api.limits import parse_limit


  def test_negative_limit_rejected():
      assert parse_limit("-1") is None
  ```
````

### Writing a `test` repro

- Write one file. The fenced block is the whole file, indented or not.
- Use a new path inside the repo. Two findings may not share a path.
- Match the runner's test-file pattern: pytest `test_*.py` or `*_test.py`;
  jest and vitest `*.test.*`, `*.spec.*`, or a file under `__tests__/`; go
  `*_test.go`; cargo `tests/<name>.rs`; rspec `*_spec.rb`.
- Assert the behavior the AC requires. The test fails on the current code and
  passes once the code is fixed.
- Make it fail for the right reason: a failed assertion. An import error at
  the top of the file, a syntax error, or a missing fixture is a broken repro,
  and the finding stays advisory. Put imports at the top: an exception raised
  inside the test body counts as a test failure.
- Change no file but the repro. A repro that writes any other file that git
  sees stops the evidence step and blocks the story.
- Write it to keep. When the finding is fixed, the coder commits the repro
  unchanged as a regression test.

### Writing a `recorded` citation

Cite a test that failed in the recorded run, the way the runner printed it.
For pytest that is `tests/test_x.py::test_fn` or
`tests/test_x.py::Class::test_fn`.

### Writing a `check`

- Start with a command Gate 2 ran, word for word. Add only arguments, such as
  the changed file.
- Never pass a fix flag (`--fix`, `--write`, `-w`). A command that edits a file
  blocks the story.

### Writing a `security-path`

- `source` is where untrusted input enters: a request handler, a file read, an
  environment read.
- `sink` is the line in the change set where that input does harm.
- Cite each as `path:line`, with a line that exists.

### Reading the result

The script prints one line per issue, `finding F<n>: confirmed (...)`,
`finding F<n>: advisory (<reason>)`, or
`finding F<n>: advisory (unverifiable <reason>)`, then a verdict. When the
step cannot run at all (the switch is off, there is no git, or the runner
binary is missing), it prints no finding lines and the agent's verdict stands.
These reasons are stable:

| Reason | Meaning |
|---|---|
| `low_severity <severity>` | Not Critical or Major; never run |
| `location_outside_change_set` | The Location, or a `security-path` sink, is outside the change set |
| `no_claim` | No AC ID, and the Category is not `security` or `architecture` |
| `no_evidence` | No Evidence field |
| `unknown_kind <word>` | The first word of the Evidence field is not one of the four kinds |
| `missing_test_block` | A `test` field has no fenced block after it |
| `repro_passed` | The `test` repro passed |
| `collection_error` | The runner could not collect, load, or build the repro |
| `timeout <seconds>` | The run passed the timeout and was killed |
| `unknown_runner <word>` | The `Test Runner` is not a runner the script classifies |
| `no_test_runner` | The project config has no `Test Runner` |
| `path_exists` | The repro path is on disk, or an earlier finding used it |
| `path_outside_repo` | The repro path is absolute or resolves outside the repo |
| `not_a_test_path` | The repro path does not match the runner's test-file pattern |
| `repro_write_failed` | The repro file could not be written |
| `repro_cap` | Five runs already happened |
| `recorded_passed` | The `recorded` test passed in the recorded run |
| `test_not_in_run` | The `recorded` test is not in the recorded run |
| `no_recorded_run` | There is no recorded run with an `exit code:` line |
| `check_passed` | The `check` exited 0 |
| `no_changed_file_named` | The `check` failed but named no changed file |
| `no_gate2_record` | There is no record of the commands Gate 2 ran |
| `command_not_recorded` | The `check` does not start with a recorded command |
| `command_not_found` | The executable of the `check` is missing |
| `not_security` | A `security-path` on an issue whose Category is not `security` |
| `bad_citation <token>` | A `security-path` citation does not resolve |
| `repro_mutated_tree` | This run changed a file outside the repro; the story is blocked |
| `stopped_after_mutation` | Not run, because an earlier run changed the tree |
