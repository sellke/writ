# Play back the goal and the problem before starting

> **Type:** Feature
> **Priority:** Normal
> **Effort:** Small
> **Created:** 2026-10-13
> **spec_ref:** .writ/specs/2026-10-22-front-door/

## TL;DR

Add an explicit, user-invoked restatement of the goal and the problem — modeled on pstack's `/in-your-own-words` — that ends the turn before any work starts.

## Current State

- Writ has no step that plays a request back as a goal and a problem before work begins.
- pstack's [`in-your-own-words`](https://github.com/cursor/plugins/blob/main/pstack/skills/in-your-own-words/SKILL.md) skill is one instruction: restate, in your own words, the user's goals and the problem they are trying to solve. It runs only when the user types `/in-your-own-words` (`disable-model-invocation: true`).
- Commands start their workflow as soon as they are invoked. Skills are capabilities a command or agent loads; they do not initiate work.

## Expected Outcome

- The user can invoke a restatement and get back, in the agent's own words, the goal and the problem being solved.
- That restatement is the whole turn. It does not start the task, run a checklist, or offer to implement.
- It runs only when invoked. Other commands do not load it.
- The primitive is chosen against ADR-009 before any file is written.

## Relevant Files

- `.writ/decision-records/adr-009-command-agent-skill-boundary.md` - user-invoked start/middle/end is a command; a skill does not initiate work
- `.writ/docs/skills.md` - skill shape, `disable-model-invocation`, and the boundary lint
- `commands/new-command.md` - authoring path if this is a command

## Notes

- Source body is a single sentence under MIT. Port the behavior into Writ's command or skill shape.
- `/new-skill` refuses a workflow-shaped description. A user-typed entry point with a beginning and an end fits `/new-command`. A restatement method that several commands `Read` fits a skill, and then it is not its own slash entry.

## Resolution

2026-10-22, lane `writ/phase/14/2026-10-22-front-door` (spec `2026-10-22-front-door`; Story 1, commit 00f8261a2ff71fca1806817c6835f947bbbf8f8f, wrote `commands/writ.md`; Story 3 closes this issue). The restatement is absorbed as `/writ` Step 1 Restate. `/writ "<request>"` writes the request back in Writ's own words on three labeled lines, Goal, Problem, and Done check, plus Proof when the request names evidence. A part the request lacks is named on its line by the prompting guide's terms, `(not stated — see prompting-guide.md § What a request carries)`, not demanded; only a missing goal gets a question.

The restatement does not end the turn. The issue expected it to be the whole turn, but ADR-030's front door replaces that expectation: `/writ` routes. Steps 2 through 5 classify the restatement with the `## Routing Rules` table, confirm the route once (one AskQuestion, "Not what I meant" last), mirror the routed command's phases onto the todo list, and run the routed command with the restatement as its request.

Primitive, chosen against ADR-009 before any file was written: a user-invoked command with a start, a middle, and an end (the `/new-command` shape), not a skill. It runs only when invoked; other commands do not load it. `scripts/tests/test_front_door.py::test_issue_resolution` pins this resolution.

Not done: no standalone restate-only invocation exists. A user who wants only the restatement stops at the confirmation; "Not what I meant" asks a follow-up and restates again rather than exiting.
