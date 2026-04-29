# Technical Spec: Daily Writ Update Check

> **Spec:** `.writ/specs/2026-04-28-daily-writ-update-check/spec.md`
> **Stories:** 1, 2, 3

## Technical Strategy

The update check is a startup instruction, not a runtime command. The agent should perform it as part of first Writ invocation in a session, before session auto-orientation or command-specific work, while preserving the original user request as the main task.

The sequence should be:

1. Detect whether this appears to be a Writ project or Writ installation.
2. Read `.writ/state/writ-update-check.json` if present.
3. If `last_checked_date` equals today's local date, skip the upstream probe.
4. If no same-day cache exists, use existing manifest/source information to perform one lightweight upstream check.
5. Record today's result under `.writ/state/`.
6. If an update appears available for a copied installation, show one concise note pointing to `/update-writ`.
7. Continue the user's original task.

## State File Contract

Preferred path:

```text
.writ/state/writ-update-check.json
```

Recommended fields:

```json
{
  "last_checked_date": "2026-04-28",
  "source": "https://github.com/sellke/writ.git",
  "installed_version": "abc1234",
  "latest_seen_version": "def5678",
  "status": "update_available",
  "checked_by": "startup-update-check"
}
```

Allowed `status` values:

- `current`
- `update_available`
- `skipped_unsupported`
- `skipped_source_repo`
- `skipped_linked_install`
- `upstream_error`

Implementers may simplify the schema if the daily limit and decision rules remain testable.

## Detection Rules

| Condition | Behavior |
|---|---|
| Same local date already recorded | Skip network work and continue silently |
| Copied install with manifest and newer upstream version | Record `update_available`; show concise `/update-writ` note |
| Copied install with manifest and no newer upstream version | Record `current`; continue silently |
| Missing manifest/source metadata | Record or skip `skipped_unsupported`; continue silently |
| Linked installation detected | Record `skipped_linked_install`; do not recommend `/update-writ` |
| Writ source repo detected | Record `skipped_source_repo`; do not recommend `/update-writ` |
| Network or upstream probe failure | Record `upstream_error`; continue silently |
| User explicitly invokes `/update-writ` | Do not duplicate the startup update-available prompt |

## Upstream Probe Guidance

Prefer a short, read-only probe using the manifest's source URL and installed version. Do not clone the full repository during startup. Do not fetch, pull, merge, install, or write outside `.writ/state/`.

The exact probe can be chosen during implementation, but it must satisfy:

- read-only against upstream
- short enough not to make startup feel blocked
- skipped when same-day state exists
- failure-tolerant

## Error & Rescue Map

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| Read daily cache | File missing, malformed JSON, or missing field | Treat as no valid same-day cache; proceed to eligibility checks | Manual fixture with missing and malformed cache |
| Detect installation | No manifest, unknown platform, or incomplete metadata | Skip quietly as unsupported | Fixture without manifest/source |
| Detect source repo | Source repo heuristics are missed | Avoid `/update-writ` recommendation when `SKILL.md`, `commands/`, `agents/`, and `scripts/` indicate source repo | Manual source-repo smoke check |
| Detect linked install | Link metadata unavailable | Prefer quiet skip over unsafe recommendation | Fixture or documented linked-install state |
| Probe upstream | Network unavailable, auth failure, timeout, invalid source | Record `upstream_error` for today and continue original task | Simulate bad source URL/offline condition |
| Compare versions | Upstream version format differs from manifest version | If comparison is uncertain, skip quietly rather than prompt | Manual mismatch fixture |
| Notify user | Prompt appears when no action is useful | Only notify `update_available` in copied installs | Review notification conditions |
| Preserve runtime boundary | Implementer adds runtime update command | Static search confirms no `@sellke/writ update-check` or CLI expansion | Search `bin/`, `package.json`, command docs |

## Shadow Paths

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| First session invocation | Stale cache plus newer upstream shows concise `/update-writ` note, then continues task | No manifest/source skips quietly | Upstream current records `current` and stays quiet | Records `upstream_error`, stays quiet, continues task |
| Same-day repeat invocation | Reads today's cache and skips network work | Missing state behaves like first invocation | Same-day `current` stays quiet | Same-day `upstream_error` avoids retry |
| Source repo dogfood session | Detects source repo and does not recommend `/update-writ` | Detection uncertain skips quietly | No update note | No network retry loop |

## Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| First user message is a Writ command | Run daily check before command workflow, then execute the command |
| User asks only for status/orientation | Run daily check first, then existing three-line orientation |
| User is already invoking `/update-writ` | Do not show a duplicate "run `/update-writ`" note |
| `.writ/state/` directory does not exist | Create it only when recording a result; missing directory is not an error |
| Cache date crosses midnight | Next local calendar day allows one new probe |
| User wants no network work | Same-day cache already prevents repeated work; explicit future opt-out would require separate issue |

## File Impact Matrix

| File | Change |
|---|---|
| `system-instructions.md` | Add daily update check to command execution/startup protocol before session auto-orientation |
| `cursor/writ.mdc` | Mirror the same startup behavior for Cursor installations |
| `commands/update-writ.md` | Optional clarification: startup notification points here; this command still applies updates interactively |
| `.writ/state/writ-update-check.json` | Documented ephemeral cache path, not committed as a product source file |
| Source issue | Update `spec_ref` after spec package creation |

## Verification Plan

1. Static review confirms `system-instructions.md` and `cursor/writ.mdc` contain matching startup update-check rules.
2. Static search confirms `@sellke/writ` runtime files were not expanded for update checking.
3. Manual fixture review covers no cache, same-day cache, stale cache, malformed cache, source repo, unsupported install, and upstream error.
4. `/update-writ` remains the only documented update application path.
5. Source issue contains a `spec_ref` pointing to this spec.
