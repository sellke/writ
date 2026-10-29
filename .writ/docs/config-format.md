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
| `Default Branch` | ship, release, status | The primary branch (main, master, develop) |
| `Test Runner` | ship, release | Command to run tests (e.g., `npm test`, `pytest`) |
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
| `Review Panel` | implement-story (Gate 3) | Opt-in cross-vendor reviewer slugs; see [Review Panel](#review-panel) |
| `Gate 0 Divergence` | implement-story (Gate 0) | On by default; `off` disables the boundary-crossing-route sketches; see [Gate 0 Divergence](#gate-0-divergence) |
| `Safety Fact` | implement-story (Gate 2.5, Gate 3) | On by default; `off` turns off the blast radius and the safety-fact section; see [Safety Fact](#safety-fact) |
| `Reviewer Filters` | implement-story (Gate 3), review | On by default; `off` turns off the reviewer lead-judgment filters; see [Reviewer Filters](#reviewer-filters) |
| `Repro First` | tdd-cycle, coding-agent, prototype, implement-story (Gate 1) | `off` turns off the repro-first bug path; absent or `on` keeps it; see [Repro First](#repro-first) |

> The former autonomous CLI-loop configuration keys are retired along with the loop
> itself; supervised multi-spec execution runs through `/implement-phase` and needs
> no dedicated loop configuration. See `archive/`.

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

## Review Panel

```markdown
- **Review Panel:** gpt-5.6-sol-medium, cursor-grok-4.6-medium-fast
```

`- **Review Panel:** <slug>[, <slug>…]` names Cursor model slugs from vendors
other than the session's. It is never detected or offered for saving: the
line is also the consent to send story content to those vendors, so only the
developer writes it. The first matching line wins; `none`
(case-insensitive), or no line, means the panel is off and Gate 3 runs
exactly as before. Slugs keep their order; a repeated slug is dropped
(`duplicate_slug`), and slugs after the third kept reviewer are dropped
(`over_cap`). Slugs from the session's vendor (`same_vendor`) or with a prefix
the vendor table does not know (`unknown_vendor`) are dropped too.
`python3 scripts/review-panel.py status --repo . --origin "<session model>"`
prints which reviewers are active, which were dropped, and why. See
[ADR-028](../decision-records/adr-028-behavioral-verification-and-cross-family-panels.md)
Decision 3.

## Gate 0 Divergence

```markdown
- **Gate 0 Divergence:** off
```

`- **Gate 0 Divergence:** on|off` under `## Conventions` turns off the
design sketches `/implement-story` Gate 0 runs on the boundary-crossing route.
It is never detected or offered for saving. No line, or `on`, means on. Any
other value also means on, and Gate 0 prints
`gate0-divergence: on (malformed: <value>)`, so a typo never disables the
sketches. Only Gate 0 reads the line; `/prototype` is unaffected.

## Safety Fact

```markdown
- **Safety Fact:** off
```

`- **Safety Fact:** on|off` turns off the `/implement-story` Gate 2.5 blast
radius and the Gate 3 safety-fact section and verifier. It is never detected
or offered for saving. No line, an empty value, or `on` means on. Only `off`
in any case turns it off; surrounding whitespace is ignored. Any other value
also means on and resolves with `reason: malformed_value <value>`. The first
matching line wins. The key must match the case shown.
`python3 scripts/review-override.py switch --name safety-fact --repo .`
prints the state.

## Reviewer Filters

```markdown
- **Reviewer Filters:** off
```

`- **Reviewer Filters:** on|off` turns off the lead-judgment filters that the
Gate 3 reviewers and `/review` apply. It follows the same rules as
`Safety Fact`: no line, an empty value, or `on` means on; only `off` in any
case turns it off; any other value means on with
`reason: malformed_value <value>`. The key must match the case shown.
`python3 scripts/review-override.py switch --name reviewer-filters --repo .`
prints the state.

## Repro First

```markdown
- **Repro First:** off
```

`- **Repro First:** on|off` under `## Conventions` turns off the repro-first
bug path. It is never detected or offered for saving. No line, an empty value,
or `on` means on. Only `off` in any case turns it off. Any other value also
means on, and `python3 scripts/repro-order.py check --base <rev>` prints
`reason: repro-first value <value> read as on`. The first matching line wins.
The key must match the case shown. With `off`, the bug path in
`skills/tdd-cycle/SKILL.md` is skipped and the ordinary cycle runs, so a bug
fix still starts from a failing test. The coding agent's `### Repro` block
reads `Repro: off`. Neither `/prototype` nor `/implement-story` runs the check,
and the ordered-commits cherry-pick rule does not apply. Run by hand,
`python3 scripts/repro-order.py check --base <rev>` prints `unverifiable` and
`reason: repro-first off` and exits 0 before reading git.

## Rules

- **Never auto-save without offering** — always ask first
- **Never overwrite existing values** without explicit user consent
- **initialize** seeds the file after greenfield setup (no confirmation needed — the user just set these up)
- **ship / release / status** consume the file; they offer to save on first detection
- Keys are case-insensitive on read; write them Title Cased as shown above
