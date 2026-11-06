# Repro stop prompt

Appended to the coding-agent prompt for the `repro-first` arm, at the same tier and model as every other arm. The spawn runs on the story in the story's `parent/` worktree with `arms/repro-first/.writ/config.md` (Repro First `on`, the other three switches `off`). Append the text under `## Prompt`. Read `Kind:` from the reply's `### Repro` section. On `bug`, run the reported command at `parent/`, apply the repro commit's test files to `checkout/`, run the same command there, and record both results with `record --arm repro-first --kind bug --repro-ac … --at-parent … --at-commit …`. Otherwise record `--kind not-a-bug-fix`.

## Prompt

This is a measurement run, not a story implementation. Repro First is on. Do only what this section says, then stop. This section overrides the story's tasks.

This trial uses its own `### Repro` form, below. It differs from the four `### Repro` forms in the coding agent's Output Format: use only the form below, and write no other report section.

### Step 1: decide Kind

`Read skills/tdd-cycle/SKILL.md`. If the worktree has no such file, read it from the Writ repository named in this spawn. Decide Kind by the skill's **Is it a bug?** rule. Check each signal:

- an issue with `**Type:** Bug` that the story or its spec links;
- a file under `.writ/issues/bugs/` that the story or its spec cites;
- the spec's Origin line citing such an issue or file;
- story wording that says existing behavior is wrong: a crash, an error, a wrong result, a regression.

When the signals disagree, use the skill's tie-break question. A missing feature, a refactor, or a speed-up with correct output is not a bug fix.

### Step 2, not a bug fix

Output only this section and stop. Write no code and no tests, and make no commits.

```markdown
### Repro

Kind: not a bug fix: <which signals you checked and why none applies>
```

### Step 2, a bug

Follow steps 1 to 3 of the skill's **Bug fixes: repro first** section, and only those:

1. Reproduce where the bug shows.
2. Watch the test fail for the bug's reason.
3. Commit the repro alone: test files only.

Then stop. Never write the fix and never commit it. Skip the skill's steps 4 to 6. Leave the worktree at the repro commit, make no other commit, and do not push.

Output only this section:

```markdown
### Repro

Kind: bug: <the signal that applied>
Surface: <where the bug shows>; the test enters through <entry point>[; gap: <what the harness could not reach>]
Command: `<the exact command that runs the repro, run from the worktree root>`
Commits: repro <sha>
Targets: AC-N.M (<the acceptance criterion the repro exercises, by its ID in the story>)
Failing output:
    <at most 20 lines of the command's output, indented four spaces>
```

If no repro is possible (nondeterministic, environment-only, or no harness that can run here), make no commit and output only:

```markdown
### Repro

Kind: bug: <the signal that applied>
Repro: none: <reason>
```
