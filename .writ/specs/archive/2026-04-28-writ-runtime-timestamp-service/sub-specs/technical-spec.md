# Technical Spec - Writ Runtime Timestamp Service

> **Spec:** [`spec.md`](../spec.md)
> **Status:** Not Started
> **Last Updated:** 2026-04-28

This sub-spec defines the concrete runtime package contract for `@sellke/writ`. The intent is a tiny utility package that fixes timestamp references without changing Writ's markdown-first architecture.

## Package Shape

```
.
├── package.json
├── bin/
│   └── writ.js
└── test or scripts/
    └── cli verification
```

Recommended `package.json` properties:

| Field | Value / Rule |
|---|---|
| `name` | `@sellke/writ` |
| `version` | Current repo release version, or first publish version selected during release |
| `bin` | `{ "writ": "bin/writ.js" }` |
| `files` | Include only runtime package files and required docs |
| `type` | Use the simplest module format for the chosen Node baseline |
| `dependencies` | Prefer none |

## CLI Contract

| Invocation | stdout | stderr | Exit |
|---|---|---|---|
| `writ date` | `YYYY-MM-DD\n` | empty | 0 |
| `writ timestamp` | `YYYY-MM-DDTHH:MM:SSZ\n` | empty | 0 |
| `writ timestamp --compact` | `YYYYMMDD-HHMMSS\n` | empty | 0 |
| `writ --help` | usage or empty | usage allowed | 0 |
| `writ` | empty | usage | 1 |
| `writ unknown` | empty | usage | 1 |
| `writ timestamp --unknown` | empty | usage | 1 |

Successful stdout is intentionally parseable. Do not print banners, emojis, warnings, or explanatory prose on stdout for successful commands.

## Formatting Rules

### `date`

- Uses local system time.
- Format: `YYYY-MM-DD`.
- Pads month and day to two digits.
- Intended for human workflow artifacts: spec folders, research files, ADR metadata, knowledge entries.

### `timestamp`

- Uses UTC.
- Format: `YYYY-MM-DDTHH:MM:SSZ`.
- Omits milliseconds.
- Intended for event identity, manifests, state files, and cross-machine comparisons.

### `timestamp --compact`

- Uses UTC.
- Format: `YYYYMMDD-HHMMSS`.
- Must sort lexicographically by time.
- Intended for filesystem-safe state files such as `.writ/state/execution-{timestamp}.json` or `.writ/state/ralph-{timestamp}.json`.

## Command Reference Migration

Replace active command references:

| Current | Replacement |
|---|---|
| `npx @devobsessed/writ date` | `npx @sellke/writ date` |
| `YYYY-MM-DD via npx @devobsessed/writ date` | `YYYY-MM-DD via npx @sellke/writ date` |

For commands where date generation should not block execution, use fallback wording:

> Use `npx @sellke/writ date` when available; otherwise use the local system date in `YYYY-MM-DD`.

Do not update historical validation reports or completed story text unless they are actively misleading current command execution.

## Error & Rescue Map

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| Run `date` | Local Date formatting bug | Exact regex and range/padding assertion | CLI output test |
| Run `timestamp` | Milliseconds or local timezone leak into output | Assert UTC `Z` suffix and no decimal seconds | CLI output test |
| Run compact timestamp | Non-sortable or unsafe format | Assert `YYYYMMDD-HHMMSS` and no colon characters | CLI output test |
| Run invalid command | CLI exits 0 or writes usage to stdout | Exit 1; usage on stderr | Invalid invocation test |
| Publish package | npm scope unavailable or package contents wrong | Document npm scope requirement; run `npm pack --dry-run` first | Release checklist |
| Execute Writ command before publish | `npx` cannot resolve package | Command docs permit local date fallback for non-critical uses | Documentation review |

## Shadow Paths

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| CLI invocation | Value-only stdout, exit 0 | Usage on stderr, exit 1 | Usage on stderr, exit 1 | npx package resolution failure; command docs explain fallback |
| Command docs | Active commands reference `@sellke/writ` | No timestamp needed | Fallback date allowed where safe | Local date fallback prevents methodology block |
| Release | Pack contents reviewed and publish succeeds | Missing npm auth stops release | Missing package metadata stops pack/publish | Scope ownership issue surfaced explicitly |

## Verification Commands

Expected local checks after implementation:

```bash
npm test
npm pack --dry-run
node bin/writ.js date
node bin/writ.js timestamp
node bin/writ.js timestamp --compact
rg "@devobsessed/writ|@sellke/writ" commands .writ/specs/2026-04-28-writ-runtime-timestamp-service
```

If a project does not adopt a formal test runner, replace `npm test` with a shell verification script invoked by the package script.

## Release Notes

- Publishing must happen under the `@sellke` npm scope.
- First publish should be public (`npm publish --access public`) if using a scoped package.
- The package should be packed and inspected before publish.
- The changelog entry should call this a runtime helper, not "Writ CLI v1".
