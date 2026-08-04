# @sellke/writ

Tiny, dependency-free CLI for deterministic dates and timestamps — used internally by the [Writ](https://github.com/sellke/writ) AI development methodology to name spec folders, state files, and manifest headers consistently across machines and agent runs.

This package is **not** the Writ methodology itself. It is a narrow runtime helper: two commands, no configuration, no state, no network calls beyond `npx` resolving the package.

## Install

No install needed — run directly with `npx`:

```bash
npx @sellke/writ date
npx @sellke/writ timestamp
npx @sellke/writ timestamp --compact
```

Or install it if you want the `writ` binary on your `PATH`:

```bash
npm install --global @sellke/writ
```

## Commands

| Command | Output | Example |
|---|---|---|
| `writ date` | Local calendar date, `YYYY-MM-DD` | `2026-08-04` |
| `writ timestamp` | UTC ISO 8601, no milliseconds | `2026-08-04T17:03:12Z` |
| `writ timestamp --compact` | Filesystem-safe UTC timestamp, sorts lexicographically | `20260804-170312` |
| `writ --help` | Usage | — |

- `date` uses **local** system time — intended for human-facing file/folder names.
- `timestamp` (both forms) uses **UTC** — intended for event identity and cross-machine comparisons.
- Successful commands print exactly one line to stdout; nothing else. Invalid invocations print usage to stderr and exit non-zero.

## Why this exists

Writ command files need a deterministic way to stamp dates and timestamps into generated artifacts (spec folder names, state files, audit ledgers) without relying on an agent's own notion of "today," which can drift or be wrong. This package gives every Writ command a single, testable source of truth for that — nothing more.

## Looking for the Writ methodology?

You're in the right repository, wrong door. See [github.com/sellke/writ](https://github.com/sellke/writ) for the actual AI development framework — commands, agents, and platform adapters for Cursor, Claude Code, Codex CLI, and OpenClaw.

## License

MIT
