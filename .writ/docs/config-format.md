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
- **Delivery Provider:** github
- **Delivery Remote:** origin
- **Preview Provider:** vercel
- **Preview Project:** prj_example
- **Preview Evidence Source:** deployment-status
- **Preview URL Pattern:** https://*.example.dev
- **Required Checks:** eval, integration
- **CI Wait Timeout:** 30m
- **Preview Wait Timeout:** 20m
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
| `Default Branch` | ship, release, status, ralph | The primary branch (main, master, develop) |
| `Test Runner` | ship, release, ralph | Command to run tests (e.g., `npm test`, `pytest`) |
| `Merge Strategy` | ship | How to integrate the default branch (merge, squash, rebase) |
| `Delivery Provider` | implement-spec, ship | PR/check provider mapping (for example `github`) |
| `Delivery Remote` | implement-spec, ship | Source remote used for branch identity and push |
| `Preview Provider` | implement-spec | Existing preview metadata provider; never provisions infrastructure |
| `Preview Project` | implement-spec | Stable existing provider project ID used for preview evidence; normalized as `previewProjectId` |
| `Preview Evidence Source` | implement-spec | Supported deployment/status/check/project convention that binds preview to SHA |
| `Preview URL Pattern` | implement-spec | Optional safety pattern that narrows discovered shareable preview URLs |
| `Required Checks` | implement-spec | Additive project-required check names; never removes provider requirements |
| `CI Wait Timeout` | implement-spec | Per-session required-check wait before resumable `waiting_ci` |
| `Preview Wait Timeout` | implement-spec | Per-session preview wait before resumable `discovering_preview` |
| `Version File` | release | File containing the version string (e.g., `package.json`) |
| `Test Coverage Tool` | release | Coverage command (e.g., `jest --coverage`) |
| `Changelog` | release | Path to the changelog file |
| `Writ Specs` | status | Path to spec folder (default: `.writ/specs/`) |
| `Writ Issues` | status | Path to issues folder (default: `.writ/issues/`) |
| `Ralph Max Iterations` | ralph.sh | Default max outer-loop iterations (`0` = unlimited) |
| `Ralph CLI Agent` | ralph.sh | CLI agent executable name or path (default: `claude`) |
| `Ralph CLI Model` | ralph.sh | Model flag value for primary agent (default: `opus`) |
| `Ralph CLI Flags` | ralph.sh | Additional CLI flags (space-separated) |
| `Ralph Stop on Failure` | ralph.sh | If `true`, stop loop on first story failure (default: `false`) |

### Ralph Configuration

Ralph keys are optional — all have sensible defaults. Add them when you need to customize CLI loop behavior.

```markdown
## Ralph

- **Ralph Max Iterations:** 0
- **Ralph CLI Agent:** claude
- **Ralph CLI Model:** opus
- **Ralph CLI Flags:** --dangerously-skip-permissions --verbose
- **Ralph Stop on Failure:** false
```

| Key | Default | Notes |
|-----|---------|-------|
| `Ralph Max Iterations` | `0` (unlimited) | Set to `20` for a bounded run; `0` runs until all stories complete or all are blocked |
| `Ralph CLI Agent` | `claude` | The CLI binary to invoke; could be `claude-code`, `codex`, or a custom wrapper |
| `Ralph CLI Model` | `opus` | Passed as `--model` flag to the CLI agent |
| `Ralph CLI Flags` | `--dangerously-skip-permissions --verbose` | Appended to the agent invocation; adjust for your security posture |
| `Ralph Stop on Failure` | `false` | `true` = halt the loop on the first failed story; `false` = skip and continue |

## Read Order (all commands)

1. Check for `.writ/config.md` — if present, parse supported keys
2. For any key not found in config: run existing detection (shell commands, git queries)
3. After detection fills any missing key: offer once — **"Save to .writ/config.md? (y/n)"**
4. On **y**: write or merge into `.writ/config.md` using the format above
5. On **n**: continue for this session without writing

### Delivery and Preview Detection

- `Delivery Provider`: derive only from one canonical remote provider; multiple
  or unrecognized remotes are ambiguous and block.
- `Delivery Remote`: use `origin` only when it exists and is unambiguous;
  otherwise require an explicit bounded choice.
- `Preview Provider`, `Preview Project`, and `Preview Evidence Source`: detect
  only from existing checked-in provider/project metadata or a documented
  project convention. `Preview Project` maps exactly to normalized
  `config.previewProjectId` in the immutable capability/config snapshot.
  Detection failure or multiple project matches blocks with setup guidance;
  an account/team name, URL pattern, deployment URL, or inferred slug is not a
  project ID. Detection never creates accounts, projects, deployments,
  environments, or secrets, and detected values are never silently written
  back to `.writ/config.md`.
- Preview project privacy: persist only the minimum stable provider project ID
  and integration provenance needed for same-project verification. Never
  persist access tokens, credentials, private environment values, bypass URLs,
  or raw provider responses in config or the capability snapshot.
- `Preview URL Pattern`: is never inferred from a discovered URL and never
  fabricates a locator. A discovered URL must already be safe to share.
- `Required Checks`: supplements the provider-required set. Failure to discover
  provider requirements is unavailable, not an empty set. Explicit provider
  evidence of zero requirements is valid. Provider discovery records provider/
  repository/query-time/head plus stable required IDs/names/set digest; config
  entries are separately classified and cannot substitute for that evidence.
- Wait timeouts accept a positive integer plus `s`, `m`, or `h`. Timeout is not
  success: preserve the exact waiting state and resume target.
- Authentication, authorization, unsupported evidence source, stale SHA, unsafe
  URL, or ambiguous identity blocks with setup/resume guidance.

Detected values may be used and recorded in the current execution capability
snapshot, but are never silently saved to `.writ/config.md`.

## Rules

- **Never auto-save without offering** — always ask first
- **Never overwrite existing values** without explicit user consent
- **initialize** seeds the file after greenfield setup (no confirmation needed — the user just set these up)
- **ship / release / status** consume the file; they offer to save on first detection
- Keys are case-insensitive on read; write them Title Cased as shown above
