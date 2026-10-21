# Play back the goal and the problem before starting

> **Type:** Feature
> **Priority:** Normal
> **Effort:** Small
> **Created:** 2026-10-13
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

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
