# Technical Spec: Repro-First Bug Fixing

> Spec: [`../spec.md`](../spec.md)

## Current State (audit, 2026-10-25)

- `skills/tdd-cycle/SKILL.md` (status `proven`, 120 lines) mentions bugs twice: a "When to Use" bullet ("reproduce it with a failing test first") and a three-line `parseDate('')` example. It says nothing about the surface, commits, or output.
- `agents/coding-agent.md` Implementation Requirement 1 reads the skill; Requirement 3 says "Small commits" and reads `skills/conventional-commits/SKILL.md`. The Output Format has no repro field.
- `commands/implement-story.md` Gate 1 spawns the coding agent "via `Read skills/tdd-cycle/SKILL.md`". The `gates:` frontmatter lists `gate1_coding` as `verification: prose-only`. Step 4 item 6 makes the completion commit and item 7 records its SHA.
- `commands/prototype.md` Step 3 spawns `agents/coding-agent.md` in prototype mode with "Principles to instruct", principle 1 "TDD". Its Step 3 integration pipes a worktree's diff into `git apply`. Step 5 ends "Ready to commit.", so a prototype run does not commit today.
- `commands/writ.md` routes "A bug, or a change with one obvious shape" to `/prototype --no-diverge`.
- `commands/create-issue.md` writes `> **Type:** {Bug|Feature|Improvement}` into `.writ/issues/{bugs,features,improvements}/`. `/create-spec --from-issue` writes `> **Origin:** Promoted from issue: <path>`. Story files carry no type field.
- `skills/subagent-worktree-integration/SKILL.md` steps 2 and 3 diff and copy files. Commits made in the worktree do not reach the checkout. `claude-code/agents/writ-coder.md` has `isolation: worktree`, and `adapters/claude-code.md` says a subagent worktree branches from the remote default branch unless `worktree.baseRef: "head"` is set.
- `scripts/revert-resolve.py` resolves a story's commits by the recorded `> **Commit:**` SHA, then `Ref:` footers naming the spec folder and story file, then `Story N (N.x):` subjects. A repro commit without a footer would be missed by `/revert`.
- No script checks commit order. `story-commit-provenance` is a skill that records one SHA, not a script.
- `.writ/config.md` keys are read by single-line regexes (`scripts/review-panel.py` `config_value`, `scripts/jev-judge.py`). `.writ/docs/config-format.md` lists supported keys.
- `install.sh` ships every `scripts/*.py` not on its dev-only list. A shipped script needs a row in `.writ/docs/agent-cli-contract.md`'s Classification table; `scripts/tests/test_agent_cli_contract.py` fails otherwise.

## Check Script: `scripts/repro-order.py`

### CLI

```
python3 scripts/repro-order.py check --base <rev> [--head <rev>] [--repo <dir>] [--test-glob <pattern>]...
python3 scripts/repro-order.py --help
```

- `--repo` defaults to `.`; `--head` defaults to `HEAD`; `--test-glob` is an `fnmatch` pattern on the repo-relative POSIX path, repeatable, added to the default classification.
- Shape: check (ADR-029 as amended). Line 1 `pass`, `fail`, or `unverifiable`; then `reason:` lines; last line `repro-order: <verdict> (<r> repro, <f> fix commit(s)[, <n> finding(s)])`.
- Exit 0 for `pass` and `unverifiable`, 1 for `fail`, 2 for a usage error or a check that could not start (stdout empty, usage or the cause on stderr).
- Stdlib only, Python 3.9. No network import. No spawn of anything but `git`. Writes nothing.

### Order of work

1. Read `<repo>/.writ/config.md` if it exists. A line matching `^\s*-\s*\*\*Repro First:\*\*\s*(\S+)\s*$` (first match) sets the switch. `off` (case-insensitive) → print `unverifiable`, `reason: repro-first off`, summary, exit 0, without calling git. A value other than `on`/`off` → treat as `on` and remember `reason: repro-first value <v> read as on` for the output.
2. Resolve `--base` and `--head` with `git rev-parse --verify <rev>^{commit}`. Check `git merge-base --is-ancestor <base> <head>`. Any failure → exit 2.
3. `git rev-list --merges <base>..<head>` non-empty → `unverifiable`, `reason: merge_in_range`, exit 0.
4. List commits oldest first: `git rev-list --reverse <base>..<head>`. For each, read the message (`git show -s --format=%B`) and the changes (`git diff-tree --no-commit-id -r -M --name-status -z <sha>`).
5. A **repro commit** has a line `Repro: <non-empty value>` in the message's final paragraph.
6. Classify each changed path: under `.writ/` → ignored; matches the test rule or a `--test-glob` → test; otherwise → source. For a rename, both old and new paths are considered.
7. Apply the rules below and print.

### Check Rules

| # | Rule | Reason on failure |
|---|---|---|
| 1 | At least one repro commit in `base..head` | `no_repro_commit` |
| 2 | Each repro commit changes at least one test file | `repro_empty <sha>` |
| 3 | Each repro commit changes no source file | `repro_touches_source <sha> <path>` (one line per path) |
| 4 | No commit before the first repro commit changes a source file | `source_before_repro <sha> <path>` |
| 5 | After each repro commit, at least one later commit changes a source file | `no_fix_after_repro <sha>` |
| 6 | No later non-repro commit modifies, renames, or deletes a path the repro commit added or modified | `repro_test_modified <sha> <path>` |

All rules run; every finding prints. A later repro commit may touch an earlier repro's test file (two bugs in one test module). An empty range fails rule 1.

On `pass`, one informational `reason:` line per repro and fix commit:

```
pass
reason: repro 3f2a1c0 test(auth): reproduce login failure for plus-sign emails (1 test file)
reason: fix 9b7d2e1 fix(auth): accept a plus sign in the login email (2 source files)
repro-order: pass (1 repro, 1 fix commit(s))
```

On `fail`:

```
fail
reason: repro_touches_source 3f2a1c0 src/auth/login.ts
reason: no_fix_after_repro 3f2a1c0
repro-order: fail (1 repro, 0 fix commit(s), 2 finding(s))
```

### Test-file rule

A path is a test file when any of these holds:

- a directory segment is `test`, `tests`, `__tests__`, `spec`, `e2e`, or `cypress`;
- the basename matches `test_*`, `*_test.*`, `*.test.*`, `*.spec.*`, `*_spec.*`, `*Test.*`, `*Tests.*`, or is `conftest.py`;
- the path matches a `--test-glob` pattern.

`.writ/` is checked first and ignored, so `.writ/specs/` never reads as a test directory.

## Report Block (`agents/coding-agent.md` Output Format)

One of four forms, always present:

**Bug with a repro**

````markdown
### Repro

- **Kind:** bug: [the recognition signal that applied]
- **Surface:** [where the bug shows]; the test enters through [entry point][; gap: what the harness could not reach]
- **Command:** `[exact command that runs the repro]`
- **Commits:** repro `[sha]` → fix `[sha]`[, `[sha]`]
- **Before the fix (failing):**
  ```text
  [at most 20 lines]
  ```
- **After the fix (passing):**
  ```text
  [at most 10 lines]
  ```
- **Check:** [line 1, any reason: lines, and the summary of repro-order.py check]
````

**Bug without a repro:** `- **Kind:** bug: [signal]`, `- **Repro:** none: [reason]`, `- **Regression test:** [path, or none]`.

**Not a bug fix:** `- **Kind:** not a bug fix: [reason]`.

**Switch off:** `- **Repro:** off`.

Implementation Requirement 3 gains: under `/implement-story`, the repro and fix commits each end with `Ref: .writ/specs/<spec-id>/user-stories/<story-file>.md`.

## Skill Section Draft (`skills/tdd-cycle/SKILL.md`)

Placed after `### Staying honest`. The implementer may tighten wording but keeps every rule.

```markdown
### Bug fixes: repro first

Skip this section when `.writ/config.md` has the line `- **Repro First:** off`.
A bug fix then starts from a failing test, as in the three beats.

**Is it a bug?** Yes when the input is an issue with `**Type:** Bug` or a file
under `.writ/issues/bugs/`, when the spec's Origin cites such a file, or when the
request says existing behavior is wrong: a crash, an error, a wrong result, a
regression. When signals disagree, ask whether a test can fail today because the
code does the wrong thing rather than because code is missing. Yes means bug.

1. **Reproduce where the bug shows.** Enter through the surface it was seen on:
   run the CLI, send the request, render the component, call the public
   function. A unit test of the suspected cause is not the repro. When the
   harness cannot reach that surface, use the nearest one it can and note the gap.
2. **Watch it fail for the bug's reason.** The failure shows the wrong value or
   the reported error. Keep the command and its output.
3. **Commit the repro alone.** Test files only, type `test`, with a trailer
   `Repro: <issue path or one-line bug>` in the message's last paragraph.
4. **Fix, then commit the fix separately.** Run the same command and keep the
   passing output. Leave the repro's test files untouched. If the repro was
   wrong, reset to before it and commit a corrected repro first.
5. **Check the order:** `python3 scripts/repro-order.py check --repo . --base <commit before the repro>`.
   Fix every `fail` reason before handing off.
6. **Carry forward** the command, the failing then passing output, both SHAs,
   and the check's output.

No repro possible (nondeterministic, environment-only, no harness): say
`Repro: none` and why, add a regression test where one fits, and write no
`Repro:` trailer.
```

The "When to Use" bug bullet becomes one line pointing at this section. The Examples bug example becomes:

```text
red:    test "POST /login accepts a+b@example.com" → 401 (bug: plus sign rejected)
commit: test(auth): reproduce login failure for plus-sign emails   Repro: login fails for plus-sign emails
green:  stop stripping '+' in normalizeEmail                       → 200
commit: fix(auth): accept a plus sign in the login email
check:  repro-order: pass (1 repro, 1 fix commit(s))
```

## Consumer Lines

**`commands/prototype.md` Step 3, principle 1** (replace the line):

```markdown
1. **TDD** — tests first covering core behavior and obvious edge cases. A bug fix follows the bug path in `skills/tdd-cycle/SKILL.md`: a failing repro committed before the fix.
```

**`commands/prototype.md` Step 3, after the integration paragraph** (new line):

```markdown
**Bug path:** record `git rev-parse HEAD` before spawning. When the agent's `### Repro` block names commits, run `python3 scripts/repro-order.py check --repo . --base <that SHA>` after integration and put its output and the failing-then-passing output in the Step 5 summary; `fail` makes the summary "Prototype Complete (with issues)".
```

**`commands/implement-story.md` Gate 1, after `**Report:**`** (new line):

```markdown
**Bug path:** record `git rev-parse HEAD` before the spawn. When the report's `### Repro` block names commits, run `python3 scripts/repro-order.py check --repo . --base <that SHA>` after integration and print its first line as `repro-order:` in the Step 4 report. `fail` marks the story `⚠️ DEGRADED` with its `reason:` lines; `unverifiable` prints and continues.
```

`gate1_coding` stays `verification: prose-only`: the script covers only the bug path, and `scripts/verdict-provenance.py` reports `entry_both_sources` if a gate names both.

**`skills/subagent-worktree-integration/SKILL.md`, end of step 3** (new paragraph):

```markdown
**Ordered commits.** When the agent's result names commits whose order is
evidence, such as a repro commit before its fix, carry those commits with
`git cherry-pick <sha>...`, oldest first, instead of copying their files, so
the order and message trailers survive. On a conflict, run
`git cherry-pick --abort`, copy the files as above, and say that the order was
lost.
```

Worktrees share the repository's object store, so the orchestrator can cherry-pick commits made in an agent's worktree without fetching. Cherry-pick applies each commit's own diff, which also avoids copying a stale worktree's unrelated files.

## Config Row (`.writ/docs/config-format.md`)

Supported Keys table:

```markdown
| `Repro First` | tdd-cycle, coding-agent, prototype, implement-story (Gate 1) | `off` turns off the repro-first bug path; absent or `on` keeps it; see [Repro First](#repro-first) |
```

Section: format line, values, default, "never detected or offered for saving", and what `off` changes (Business Rule 9).

## Error & Rescue Map

| Operation | Failure | Detection | Rescue | User sees |
|---|---|---|---|---|
| Read `.writ/config.md` | Unreadable or not UTF-8 | `OSError`, `UnicodeDecodeError` | Exit 2, cause on stderr | `repro-order: cannot read .writ/config.md (...)` |
| Read `.writ/config.md` | Absent | `exists()` false | Switch reads `on` | Nothing extra |
| Resolve `--base` / `--head` | Unknown rev, shallow history | `git rev-parse` non-zero | Exit 2 | `repro-order: cannot resolve <rev>` |
| Ancestry | Base not an ancestor of head | `merge-base --is-ancestor` exit 1 | Exit 2 | `repro-order: <base> is not an ancestor of <head>` |
| Run git | `git` not on PATH, not a repository | `FileNotFoundError`, `rev-parse --git-dir` non-zero | Exit 2 | `repro-order: not a git repository` / `git not found` |
| Range shape | Merge commit in range | `rev-list --merges` non-empty | `unverifiable`, exit 0 | `reason: merge_in_range` |
| Integration | Cherry-pick conflict | `git cherry-pick` non-zero | Abort, copy files, say the order was lost | Re-run check: `fail`, `reason: no_repro_commit` |
| Agent self-check | `fail` before handoff | Exit 1 | Fix history within `MAX_SELF_FIX_ITERATIONS = 3`; at the cap, `STATUS: BLOCKED` | BLOCKED escalation, as today |

## Shadow Paths

- **Happy path:** repro commit (tests only, trailer), fix commit (source), check `pass`; orchestrator re-run `pass`.
- **Nil input:** `--base` missing → argparse usage on stderr, exit 2, stdout empty.
- **Empty input:** `base == head` → `fail`, `reason: no_repro_commit`.
- **Upstream error:** `git` missing or the repository unreadable → exit 2 with the cause.

## Interaction Edge Cases

| Case | Behavior |
|---|---|
| Two bugs, two repro commits | Each repro needs a later source commit; rule 4 applies before the first repro only |
| Repro un-skips an existing test | A test-file change; valid repro |
| Fix commit also adds new tests | Allowed; only the repro's own files are frozen |
| Repro test renamed after the fix | `repro_test_modified` |
| Completion commit touches only `.writ/` | Ignored by classification |
| Project tests outside known patterns | Caller passes `--test-glob`; without it the repro reads `repro_touches_source` |
| Paths with spaces or non-ASCII | `-z` output parsing |
| Switch value `yes` | Read as `on`, with an informational reason line |

## Tests

### `scripts/tests/test_repro_order.py` (Story 1)

Fixture helper: `make_repo(tmp)` runs `git init`, sets local `user.name`/`user.email`, makes a base commit with `src/app.py` and `tests/test_app.py`; `commit(repo, files, message)` writes files and commits.

| Test | History | Expect |
|---|---|---|
| `test_pass_repro_then_fix` | repro (tests, trailer) → fix (src) | `pass`, exit 0, repro and fix reason lines |
| `test_fail_no_repro` | fix only | `fail`, `no_repro_commit` |
| `test_fail_repro_touches_source` | repro changes src and tests | `repro_touches_source` |
| `test_fail_repro_empty` | repro changes only `.writ/` | `repro_empty` |
| `test_fail_source_before_repro` | fix → repro | `source_before_repro` |
| `test_fail_no_fix_after_repro` | repro only | `no_fix_after_repro` |
| `test_fail_repro_test_modified` | repro → fix that edits the repro test | `repro_test_modified` |
| `test_unverifiable_merge` | a merge in range | `unverifiable`, exit 0 |
| `test_switch_off` | config `- **Repro First:** off` | `unverifiable`, `repro-first off`, exit 0, no git call needed (non-repo dir works) |
| `test_switch_unknown_value` | config `yes` | runs; extra reason line |
| `test_test_glob` | repro in `qa/login_check.py` with `--test-glob 'qa/*'` | `pass` |
| `test_usage_errors` | no `--base`; bad rev; base not ancestor | exit 2, stdout empty |

### `scripts/tests/test_repro_first_wiring.py` (Stories 2–4)

Text checks, one per Removal Inventory row: the skill heading `### Bug fixes: repro first` and its `Repro First` skip line; `scripts/repro-order.py check` named in the skill; `### Repro` in the coding agent's Output Format with all four forms; the `Ref:` footer sentence; `skills/tdd-cycle/SKILL.md` named in `commands/prototype.md` Step 3; a `**Bug path:**` line naming `repro-order.py` in `commands/prototype.md` Step 3 and in `commands/implement-story.md` Gate 1; `git cherry-pick` in the integration skill; the `Repro First` row in `.writ/docs/config-format.md`. Plus: `bash scripts/lint-skill.sh` passes on both touched skills.
