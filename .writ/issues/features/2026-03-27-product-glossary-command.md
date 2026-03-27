# Product Glossary Command/Skill

> **Type:** Feature
> **Priority:** Normal
> **Effort:** Medium
> **Created:** 2026-03-27
> **spec_ref:**

## TL;DR

A command or skill that captures, maintains, and surfaces a project-specific glossary of terms and concepts so LLMs have consistent, grounded vocabulary across sessions.

## Current State

- LLMs lose domain context between sessions — they re-infer term meanings from code and docs each time
- Product-specific jargon (e.g., "spec-lite", "contract", "story") is defined implicitly across scattered files, not collected in one place
- Ambiguous terms lead to miscommunication: the LLM interprets "pipeline" differently than the developer means it
- No mechanism exists to teach an LLM "in this project, X means Y" persistently
- Teams onboarding new developers (or new AI tools) have no single reference for domain language

## Expected Outcome

- A glossary file lives in `.writ/docs/glossary.md` (or similar) with structured term definitions
- A command (`/glossary`) or skill allows adding, updating, and querying terms
- Terms include: name, definition, aliases/synonyms, usage context, and optionally related terms
- The glossary is automatically surfaced to LLMs via rules or system context so definitions anchor future conversations
- Adding a term is fast — one-liner capture with optional elaboration later
- The glossary grows organically as the project evolves, not as a one-time documentation effort

## Relevant Files

- `commands/new-command.md` - template for creating new Writ commands
- `.cursor/rules/writ.mdc` - system instructions where glossary context could be auto-injected
- `commands/research.md` - research command already identifies terminology as a discovery output

## Notes

- Key design decision: command vs skill vs both. A command gives interactive CRUD; a skill gives passive always-available context. Likely want both — a command to maintain the glossary and a rule/skill to inject it.
- Consider auto-suggesting new terms when the LLM encounters undefined jargon during spec creation or research.
- The glossary format should be both human-readable (markdown) and machine-parseable (consistent structure per entry) so it can be programmatically injected into context.
- Related prior art: domain-driven design's "ubiquitous language" concept — this is essentially that, made persistent for AI collaborators.
