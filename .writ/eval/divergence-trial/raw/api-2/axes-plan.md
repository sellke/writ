# Axes plan: api-2

Written by the orchestrator before any axes-arm spawn. Caller usage first, then axes, then one combination per draft.

## Caller usage

```text
record = why("Why does Gate 0 run before the boundary map?")
for claim in record.claims:
    print(claim.tier, claim.text, claim.source)
print(record.sources_searched)   # ledger, git, MCP servers, in order, empty ones too
if record.change_guidance:
    plan(record.change_guidance.preserve, record.change_guidance.avoid, record.change_guidance.risk)
saved = read_saved_record(path)   # what /create-spec does before it plans
```

## Persona

a developer reading the answer before changing the code it explains

## Declared axes (from skills/design-divergence/SKILL.md)

1. One call vs several: the caller makes one request with options, or composes small requests
2. Errors as exceptions vs result values: failure raises and unwinds, or comes back in the return value

## Combinations

- Draft 1: one call; an unreachable or empty source comes back as a value in the record
- Draft 2: several small calls (claims, sources, guidance); an unreachable or empty source comes back as a value
- Draft 3: one call; an unreachable source raises and unwinds
