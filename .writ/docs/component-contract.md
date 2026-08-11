# The Component Contract — Problem, Outcome, Exit Criteria

> **Status:** Shipped (`2026-08-11-component-contract`). All 31 commands and all 7 agents carry the three fields; all 31 commands carry a `## Completion` section.
> **Source of truth for the decision:** [ADR-020](../decision-records/adr-020-component-contract.md)

Every Writ component declares **the problem it addresses, the outcome it produces, and the exit criteria that prove it finished**. ADR-020 captures the *why*; this document captures the *what* and *how*, and is the reference `/new-command` points at when it coaches the fields.

There is no new mechanism. Commands extend the `---` YAML they already carry; agents extend the fenced config block that already carries `model_tier`.

---

## The Three Fields

| Field | Shape | Answers |
|---|---|---|
| `problem:` | One line, one sentence | What goes wrong in the absence of this component |
| `outcome:` | One line, one sentence | The artifact or state that exists once it has run |
| `exit_criteria:` | Block sequence, 2–4 quoted strings | What is observably true afterward that was not true before |

`problem:` and `outcome:` are **one line each** — no line continuation, no YAML block scalars, no lists. A component that cannot state either in one line has a scoping defect the contract should surface rather than accommodate. Soft target: under 200 characters.

---

## Where the Contract Lives

### Commands — the existing `---` frontmatter

```yaml
---
name: implement-story
description: "..."           # already present
problem: "..."               # what goes wrong without this command
outcome: "..."               # the artifact/state that exists after
exit_criteria:
  - "story status is Complete in .writ/specs/<spec>/user-stories/"
  - "all review gates returned PASS"
---
```

Key order is fixed: `name`, `description`, any other existing keys, then `problem`, `outcome`, `exit_criteria`. The three new keys **append after the last existing key** — never before `name` or `description`. Values are double-quoted strings; `exit_criteria` is a block sequence of quoted strings.

`commands/_preamble.md` is excluded. It carries `disable-model-invocation: true`, is never invoked, and has no completion state.

### Agents — the existing fenced config block, two carriers

Six agents use `## Agent Configuration` with an **unlabeled** fence:

````
## Agent Configuration

```
subagent_type: "generalPurpose"
model: default (inherits from parent)
model_tier: orchestration
readonly: false
problem: "..."
outcome: "..."
exit_criteria:
  - "..."
```
````

`agents/visual-qa-agent.md` uses `## Agent Specification` with a ` ```yaml ` fence and a different key set. **Both carriers are written to as they are.** An editor matching `^## Agent Configuration$` alone silently skips the seventh file and reports 6/7 as success — match `^## Agent (Configuration|Specification)$`.

The six unlabeled blocks are not strictly valid YAML (`model: default (inherits from parent)`). That is a documented convention, not a parsed document; appending a block sequence neither improves nor worsens it. Do not normalize either carrier.

---

## Writing `exit_criteria` — the part that is actually hard

A criterion that is present but empty passes every check a lint can build on top of it. Two tests are the only defense, and both are read by a human or a reviewing agent, not by a script.

**The swap test.** Paste any `problem:`, `outcome:`, or `exit_criteria` entry into a *different* component. If it remains plausible there, it is boilerplate and must be rewritten. A criterion that fits `/review` and `/retro` equally well describes neither.

**The restatement test.** If deleting the criterion and re-deriving it from `description:` alone would produce roughly the same sentence, it carries no information. `description:` says what the component is *for*; `exit_criteria` says what is observably *true afterward*.

**Every criterion names something a script could check** — at least one of: a file or directory path, a field value (`Status: Complete`), a count or comparison, a process outcome (`git tag v<VERSION> exists`), or a command-observable state. Write them as present-tense assertions about post-run state, not as instructions or aspirations. Placeholders in angle brackets are expected.

| | Example |
|---|---|
| ✗ Boilerplate | `"the release completes successfully"` — plausible in any command, asserts nothing |
| ✓ Derived | `"VERSION differs from its pre-run value"` · `"a git tag matching v<VERSION> exists"` · `"CHANGELOG.md contains a heading for <VERSION>"` |

Banned constructions: "the command completes successfully", "the report is generated", "the user is informed", "the output is correct", and any criterion whose verb is the component's own name. A criterion that names a path but asserts nothing about it is also not an assertion — `".writ/state/review-<branch>.md"` is a path; `".writ/state/review-<branch>.md exists and contains a Recommendation section"` is a criterion.

**Honest limit.** `exit_criteria` is only *nominally* machine-checkable. A lint can verify the field exists and is non-empty; it cannot verify the assertion is true. ADR-020 records this as a known limit with a 2026-11-11 review trigger. The field earns its lines because it forces the author to name a falsifiable condition — that is the audit value, even when nothing executes it.

---

## `## Completion` and How It Differs

Commands also carry a `## Completion` section, placed immediately before the file's final `## References` (and before any `---` rule that precedes it).

The two are **not redundant, and must not contradict each other**. Frontmatter carries the machine-checkable assertions; the section carries what does not fit a YAML string — outcome-interpretation tables, the statement that a zero result is valid, and the terminal constraint. Every `exit_criteria` entry should be traceable to something the section also asserts. Where a section already exists, derive the criteria *from* it rather than inventing them alongside it.

A section contains, as applicable:

- A one-sentence success condition naming the artifact or state produced.
- Where a zero-result or failure mode exists, one sentence stating it is a valid outcome rather than an error.
- A **Terminal constraint** line stating what the command does *not* do next, wherever it produces something an agent would otherwise volunteer to act on. This is the highest-value line and the least likely to be written unprompted.

---

## Line Budget

The contract is defensible only because it is small. The numbers are ceilings, not targets.

| Surface | Files | Per-file ceiling | Total |
|---|---|---|---|
| Command frontmatter | 31 | 7 lines | 217 |
| Agent config blocks | 7 | 7 lines | 49 |
| New `## Completion` sections | 18 | 14 lines | 252 |
| **Aggregate** | | | **518** |

The 7-line frontmatter ceiling is 1 (`problem`) + 1 (`outcome`) + 1 (the `exit_criteria:` key) + at most 4 entries. Two entries (5 lines) is the floor; three (6 lines) is the expected shape. Needing more than four assertions is a signal about the component, not about the budget.

The 14-line `## Completion` ceiling is derived from the 13 sections that predate the contract, which run 12–18 lines with a median of 15–16. A section written today should be leaner than sections that accreted. A 6-line section that is accurate beats a 14-line one that pads to the ceiling.

---

## References

- **Decision and alternatives:** [ADR-020](../decision-records/adr-020-component-contract.md)
- **Paired token reduction:** [ADR-021](../decision-records/adr-021-progressive-disclosure-token-budget.md) — what makes this contract affordable
- **Boundary this extends:** [ADR-009](../decision-records/adr-009-command-agent-skill-boundary.md)
- **Authoring tool:** [`commands/new-command.md`](../../commands/new-command.md)
- **Companion docs, same shape:** [`.writ/docs/model-tiers.md`](model-tiers.md), [`.writ/docs/skills.md`](skills.md)
