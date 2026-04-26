# Writ Knowledge Ledger

The knowledge ledger stores small, cross-cutting project facts that should survive chats, agent sessions, and future contributors. It is plain markdown in git; there is no database or generated source of truth.

## What Goes Where

Use this decision tree before creating an entry:

```text
Is this an architectural choice with serious blast radius
(reversal costs weeks, locks in a substrate, changes the system shape)?
-> YES: .writ/decision-records/ (ADR template)

Is this an investigation that produced specific recommendations
or evaluated multiple options against drivers?
-> YES: .writ/research/ (research template)

Is this a feature contract with stories, gates, and acceptance criteria?
-> YES: .writ/specs/ (spec template)

Otherwise — small, accumulating, cross-cutting:
- A choice we made about how the codebase looks?         -> knowledge/decisions/
- A pattern the codebase uses we want documented?        -> knowledge/conventions/
- A term whose meaning matters in this project?          -> knowledge/glossary/
- A thing we tried that failed or surprised us?          -> knowledge/lessons/
```

When in doubt, prefer the smallest durable home. Promote to an ADR or research note only when the entry needs heavier analysis, trade-off history, or formal approval.

## Categories

| Directory | Use For | Filename |
|---|---|---|
| `decisions/` | Small choices below ADR scale | `YYYY-MM-DD-short-slug.md` |
| `conventions/` | Reusable codebase or workflow patterns | `YYYY-MM-DD-short-slug.md` |
| `glossary/` | Writ-specific terms and meanings | `term-slug.md` |
| `lessons/` | Things tried, learned, or corrected | `YYYY-MM-DD-short-slug.md` |

## Required Frontmatter

Every entry must start with this schema:

```yaml
---
category: decisions | conventions | glossary | lessons
tags: [tag1, tag2]
created: YYYY-MM-DD
related_artifacts:
  - .writ/specs/example/spec.md
---
```

Rules:
- `category` must match the containing directory.
- `tags` must contain at least one lowercase slug.
- `created` uses `YYYY-MM-DD`.
- `related_artifacts` is always present. Use `[]` when there are no related files.
- Optional fields are allowed: `superseded_by`, `replaces`, `author`, `confidence`.

## Authoring Rules

Use `/knowledge "summary"` for fast capture. The command infers a category, prompts only for missing required fields, validates frontmatter before writing, and confirms with the created path.

Use `/knowledge --category=lessons "summary"` when inference would be ambiguous.

Use `/knowledge --list [category]` to scan entries and `/knowledge --read <slug>` to load one entry by filename slug.

Keep entries short. If the explanation needs a long comparison, write research. If it changes architecture, write an ADR.
