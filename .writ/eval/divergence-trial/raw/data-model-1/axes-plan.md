# Axes plan: data-model-1

Written by the orchestrator before any axes-arm spawn. Caller usage first, then axes, then one combination per draft.

## Caller usage

```text
record_verdict(pr=412, head_sha="9f3c2e1", patch_id="a1b2c3d", verdict="pass", by="/ship")
is_verified(pr=412, head_sha="7d0e4aa")   # -> ("VERIFIED", verdict) when the patch-id matches, else ("NOT VERIFIED", None)
history(pr=412)                              # -> every verdict for the PR, oldest first
```

## Persona

a developer auditing which verdicts a pull request has received

## Declared axes (from skills/design-divergence/SKILL.md)

1. Mutable rows vs append-only events: updates overwrite a row, or add an event and current state is derived
2. Computed on write vs on read: totals are stored when data changes, or calculated when queried

## Combinations

- Draft 1: mutable rows; verified status computed on write
- Draft 2: append-only events; verified status computed on read
- Draft 3: append-only events; verified status computed on write
