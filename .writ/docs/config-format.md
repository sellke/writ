# Writ Config Format

> Location: `.writ/config.md` (project root)
> Purpose: Shared convention store — eliminates repeated detection across commands

## Why this file exists

`/ship`, `/release`, `/status`, and `/initialize` all need the same project conventions (default branch, test runner, merge strategy, version file, etc.). Without a shared store, each command detects them independently on every run. `.writ/config.md` is the single cache — written once, read everywhere.

## Format

```markdown
# Writ Project Config

> Last Updated: YYYY-MM-DD
> Auto-generated — edit manually if needed

## Conventions

- **Default Branch:** main
- **Test Runner:** jest (detected: package.json scripts.test)
- **Merge Strategy:** squash
- **Version File:** package.json
- **Test Coverage Tool:** jest --coverage

## Paths

- **Changelog:** CHANGELOG.md
- **Writ Specs:** .writ/specs/
- **Writ Issues:** .writ/issues/
```

## Supported Keys

| Key | Used By | Description |
|-----|---------|-------------|
| `Default Branch` | ship, release, status | The primary branch (main, master, develop) |
| `Test Runner` | ship, release | Command to run tests (e.g., `npm test`, `pytest`) |
| `Merge Strategy` | ship | How to integrate the default branch (merge, squash, rebase) |
| `Version File` | release | File containing the version string (e.g., `package.json`) |
| `Test Coverage Tool` | release | Coverage command (e.g., `jest --coverage`) |
| `Changelog` | release | Path to the changelog file |
| `Writ Specs` | status | Path to spec folder (default: `.writ/specs/`) |
| `Writ Issues` | status | Path to issues folder (default: `.writ/issues/`) |

## Read Order (all commands)

1. Check for `.writ/config.md` — if present, parse supported keys
2. For any key not found in config: run existing detection (shell commands, git queries)
3. After detection fills any missing key: offer once — **"Save to .writ/config.md? (y/n)"**
4. On **y**: write or merge into `.writ/config.md` using the format above
5. On **n**: continue for this session without writing

## Rules

- **Never auto-save without offering** — always ask first
- **Never overwrite existing values** without explicit user consent
- **initialize** seeds the file after greenfield setup (no confirmation needed — the user just set these up)
- **ship / release / status** consume the file; they offer to save on first detection
- Keys are case-insensitive on read; write them Title Cased as shown above
