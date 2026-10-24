---
name: writ
description: "Restate a request in Writ's own words, pick the command whose ceremony fits, confirm once, and run it with its phases on the todo list. The one command a new user needs."
problem: "Writ ships 32 commands and a user has to know which one fits before typing anything, so work starts at the wrong level of ceremony or not at all."
outcome: "The request is restated as goal, problem, and done check, routed to exactly one existing command at the fitting ceremony, and that command runs with its phases mirrored in the todo list; nothing is written beyond what the routed command writes."
entry_level: high
exit_criteria:
  - "the restatement names a goal, a problem, and a done check, or names which of them the request lacks by the prompting guide's part names"
  - "exactly one route from the rule table was proposed, confirmed through one AskQuestion, and the routed command's file was read and followed"
  - "the todo list carries the routed command's phase headings before its first phase runs, and every skipped phase reads skip: <reason>"
  - "no file under .writ/ was created by this command itself"
---

# Writ Command (writ)

## Overview

The front door. Type what you want. `/writ` restates it as a goal, a problem, and a done check, picks the one command whose ceremony fits, asks once, and runs that command with its phases on the todo list.

`/writ` is a router: one rule table, one confirmation, a handoff. It does not plan, specify, or build. The routed command does, and `/writ` adds nothing to that command's workflow. Under a Claude Code plugin the command reads `/writ:writ`.

## Invocation

| Invocation | Behavior |
|---|---|
| `/writ "<request>"` | Restates and routes the inline request |
| `/writ` | Uses conversation context: preceding messages and attached files |
| `/writ @file` | Reads an issue or other file as the request |

## Required Artifacts

None required. Two are optional:

- `.writ/product/roadmap.md`. Absent: the `/implement-phase` route is not offered. When the request names a phase or feature anyway, the restatement says the roadmap is missing and `/plan-product` creates it.
- `.writ/docs/prompting-guide.md`. Absent: a missing part is still named by the guide's part names; the link is dropped.

## Command Process

### Step 1: Restate

Write the request back in Writ's words, not the user's. Name the problem the request implies, not only the change it asks for. Three labeled lines, and a fourth when the request names evidence. Print them as labeled lines first in the reply every time, even when the conversation already holds the request; never fold them into prose:

```
Goal: <what is true afterwards>
Problem: <what is wrong or missing now, as the request implies it>
Done check: <how anyone could tell the work is done>
Proof: <the evidence the result must show: a test, a screenshot, a command's output>
```

The part names are the prompting guide's (**Goal**, **Done check**, **Proof**; see `.writ/docs/prompting-guide.md` § What a request carries). A missing part is reported, not demanded:

```
Goal: (not stated — see prompting-guide.md § What a request carries)
```

- Missing done check or proof: name it on its line and continue to Step 2.
- Missing goal: ask one question in natural language, no menu, and restate from the answer before routing.
- `/writ` with no request and no context: ask one question, "What do you want to do?", and wait for the answer.
- Request is a file: read it. An issue's title and expected outcome are the goal and done check unless the body says otherwise.

### Step 2: Classify

Apply `## Routing Rules` to the restatement. The table is the only classifier. Take the row whose Signal fits; when two rows fit, the rules below decide.

- **Tie-break.** When the cues for `/prototype --no-diverge` and `/create-spec` both fire, `/prototype`'s escalation signals decide: over 5 files, a schema change, a new dependency, core architecture, or low existing coverage → `/create-spec`. None of them → `/prototype --no-diverge`. A signal counts here only when the request states it or the restatement can name it; an unstated file count is not a signal, because `/prototype` counts files when it runs and escalates itself.
- **Empirical fork.** Ask: could a throwaway run answer this faster than asking the user? If yes, the route is `/prototype` with the fork named as the thing to try, and the confirmation says so. Never answer a fork with a question.
- **Roadmap work.** Match the named phase or feature in `.writ/product/roadmap.md` and route `/implement-phase <N>`; the confirmation shows the matched phase. Roadmap absent: the route is not offered (see Required Artifacts).
- **Why or how.** Route `/research`. The confirmation notes that `/why` takes this route when it ships.
- **Flags travel with the route.** `--no-diverge` from the second row; `--from-issue <path>` when the request is an issue file and the route is `/create-spec`; `@file` when the request is a file and the route is `/prototype`.

Hold one route and a one-line reason for it. Run nothing yet.

### Step 3: Confirm

Exactly one AskQuestion. The proposed route carries the `(Recommended)` label per `system-instructions.md` § Recommendation Semantics; every other route in the table is an option; `Not what I meant` is last.

```
AskQuestion({
  title: "Route",
  questions: [{
    id: "route",
    prompt: "<restatement>\n\nProposed: <route> — <one-line reason>",
    options: [
      { id: "proposed", label: "<route> (Recommended)" },
      { id: "alt-1", label: "<other route>" }, …,
      { id: "other", label: "Not what I meant" }
    ]
  }]
})
```

- The proposed route, or another route: continue to Step 4 with that route. The restatement does not change when another route is picked.
- `Not what I meant`: ask one free-text follow-up, then return to Step 1 and restate and route again.

### Step 4: Mirror the Route's Phases

Read the routed command's file, `commands/<name>.md`. Collect its headings matching `^### Phase \d+`; when it has none, collect `^### Step \d+` instead. Put one todo item per heading, in order, carrying the heading text, before the routed command's first phase runs. A phase the chosen flags skip gets ` — skip: <reason>` appended. `--no-diverge` skips `/prototype` Step 2.5 Diverge & Choose; `--quick` skips the gates the routed command's own table names.

Use the `todo_write` capability as the platform adapter maps it. Where the adapter maps `todo_write` to a file write, print the list as a markdown checklist in the reply and write nothing.

### Step 5: Run the Route

Read the routed command's file and follow it top to bottom with the restatement as its request. Add no step and remove none; the routed command owns the conversation from here. `/writ` writes nothing under `.writ/` and keeps no state. Resuming is the routed command's concern.

Routed command file missing (a partial install): name the missing file and `/update-writ`. Do not improvise the workflow.

## Routing Rules

| Signal | Route |
|---|---|
| The request names a goal rather than a change, asks for options, or the direction is unsettled | `/prototype` |
| A bug, or a change with one obvious shape (see tie-break) | `/prototype --no-diverge` |
| A capability users will rely on, or any `/prototype` escalation signal: over 5 files, schema change, new dependency, core architecture, low existing coverage | `/create-spec` |
| Names a phase or feature in `.writ/product/roadmap.md` | `/implement-phase <N>` |
| Asks why something is the way it is, or how something works | `/research` (`/why` takes this route when it ships) |
| A fork that a throwaway run could answer faster than a question | `/prototype`, with the fork named as the thing to try |

## Completion

This command succeeds when:

1. **Restatement shown**: Goal, Problem, Done check, and Proof when evidence was named, with any missing part named by the guide's terms.
2. **One route confirmed**: one AskQuestion, one route taken from the table.
3. **Phases mirrored**: the routed command's headings on the todo list, skipped ones marked `skip: <reason>`.
4. **Routed command ran**: its file read and followed with the restatement as input.

**Terminal constraint:** The routed command owns everything after the handoff. `/writ` creates no artifact and keeps no state.

---

## References

- Standing instructions: [`commands/_preamble.md`](_preamble.md)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)
- Prompting guide: [`.writ/docs/prompting-guide.md`](../.writ/docs/prompting-guide.md) § What a request carries
