---
category: conventions
tags: [filenames, markdown, writ-artifacts]
created: 2026-04-24
related_artifacts:
  - .writ/specs/2026-04-24-phase4-production-grade-substrate/spec.md
  - .writ/specs/2026-04-24-phase4-production-grade-substrate/sub-specs/technical-spec.md
---

# Date-Prefixed Slugs For Event-Like Artifacts

## TL;DR

Use `YYYY-MM-DD-short-slug.md` for dated Writ artifacts such as issues, research, decisions, conventions, and lessons.

## Context

- Writ artifacts are meant to be browsed in the filesystem and reviewed in git.
- Date prefixes preserve rough chronology without requiring an index.
- The operator already sees this convention in `.writ/issues/`, `.writ/research/`, and `.writ/decision-records/`.

## Detail

For new knowledge entries, use date-prefixed filenames in `decisions/`, `conventions/`, and `lessons/`. Keep slugs lowercase, hyphenated, and short enough to scan in directory listings.

`glossary/` is the exception: terms use stable slugs without dates because the term is the identifier, not the capture event.

## Related

- [Technical spec](../../specs/2026-04-24-phase4-production-grade-substrate/sub-specs/technical-spec.md)
