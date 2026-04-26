# Writ Spec Format

This document defines the stable metadata fields used by Writ specification files.

## Header Metadata

Every new `spec.md` created by `/create-spec` includes a small metadata header before the specification contract:

```markdown
> **Status:** Not Started
> **Created:** YYYY-MM-DD
> **Owner:** @GitUserName
```

Additional fields such as `Phase`, `Roadmap`, `Anchored ADRs`, or `Source research` may appear when relevant to the spec.

## Owner Field

`Owner` identifies the person who created or owns the spec. It is a lightweight coordination signal, not an auth boundary.

Schema:

```markdown
> **Owner:** @{git-user-name-without-spaces}
```

Creation behavior:

- `/create-spec` resolves the default from `git config user.name`.
- The value is prefixed with `@`.
- Spaces are stripped, so `Adam Sellke` becomes `@AdamSellke`.
- If `git config user.name` is unset or empty, `/create-spec` writes `@unknown` and warns: `Set it with: git config user.name 'Your Name'`.

Verification behavior:

- Specs created on or after `2026-04-24` should include `Owner`.
- `/verify-spec` warns, but does not fail, when a new spec lacks owner metadata.
- Legacy specs created before `2026-04-24` are reported as `legacy — owner not required`.
- Writ does not migrate legacy specs automatically.

Display behavior:

- `/status` shows `Owner` for active specs.
- Specs without owner metadata display `—`.

## Rationale

The owner field is intentionally small. Solo users see their own name on active work, while future small teams get an ownership substrate without introducing accounts, permissions, external services, or retroactive migration.
