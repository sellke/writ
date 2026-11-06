# Axes plan: data-model-2

Written by the orchestrator before any axes-arm spawn. Caller usage first, then axes, then one combination per draft.

## Caller usage

```text
unenforced_rules()                 # -> rules with no enforcer, or documentation only
enforcers_for(rule_id="no-direct-db-in-handlers")   # -> [(kind, location), ...]; kind: architecture, type, lint, test, docs
add_enforcer(rule_id="no-direct-db-in-handlers", kind="lint", location=".eslintrc rule", proven_by="commit 4e1f0aa")
proof_for(enforcer_id)            # -> the past mistake the check failed on
```

## Persona

a maintainer asking which project rules nothing enforces

## Declared axes (from skills/design-divergence/SKILL.md)

1. Normalized vs embedded: related records live in their own tables, or inside the parent record
2. Mutable rows vs append-only events: updates overwrite a row, or add an event and current state is derived

## Combinations

- Draft 1: normalized tables; mutable rows
- Draft 2: embedded (enforcers inside the rule record); mutable rows
- Draft 3: normalized tables; append-only events
