# Axes plan: api-1

Written by the orchestrator before any axes-arm spawn. Caller usage first, then axes, then one combination per draft.

## Caller usage

```text
result = run(["python3", "scripts/pr-ready.py", "--pr", "412"])
if result.exit_code == READY: merge(412)
elif result.exit_code == CONFLICTS: rebase(412)
elif result.exit_code == FAILING_CHECKS: fix_checks(412)
else: hand_back_to_human(result.stdout)   # threads, gates, or several blockers
print(result.stdout.splitlines()[-1])     # the summary line
```

## Persona

the developer who maintains the /ship --watch loop and calls this script after every change it makes

## Declared axes (from skills/design-divergence/SKILL.md)

1. One call vs several: the caller makes one request with options, or composes small requests
2. Errors as exceptions vs result values: failure raises and unwinds, or comes back in the return value

## Combinations

- Draft 1: one call; blockers come back as result values
- Draft 2: several small calls; blockers come back as result values
- Draft 3: one call; blockers raise (fail the invocation) and unwind
