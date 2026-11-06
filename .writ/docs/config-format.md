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
- **Eval Command:** make lint
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
| `Eval Command` | ship | Command `/ship --test` and `--watch` run after the Test Runner; its exit code goes into the verification ledger. Absent: the Test Runner alone. |
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
| `Safety Fact` | implement-story (Gate 2.5, Gate 3) | On by default; `off` turns off the blast radius and the safety-fact section; see [Safety Fact](#safety-fact) |
| `Reviewer Filters` | implement-story (Gate 3), review | On by default; `off` turns off the reviewer lead-judgment filters; see [Reviewer Filters](#reviewer-filters) |
| `Evidence Gate` | implement-story (Gate 3), review | On by default; `off` lets the reviewer's verdict block without executed evidence; see [Evidence Gate](#evidence-gate) |
| `Repro First` | tdd-cycle, coding-agent, prototype, implement-story (Gate 1) | `off` turns off the repro-first bug path; absent or `on` keeps it; see [Repro First](#repro-first) |

**Removed keys:** `Review Panel` ([ADR-032](../decision-records/adr-032-evidence-gated-review.md)). A leftover line prints `review-panel: removed (ADR-032)` once per story and does nothing else.

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

## Evidence Gate

```markdown
- **Evidence Gate:** off
```

`- **Evidence Gate:** on|off` turns off evidence gating for a whole story or
`/review` run. With the gate on, a Gate 3 or `/review` finding blocks only when
it carries executed evidence (`skills/evidence-gated-findings/SKILL.md`). With
`off`, the reviewer's verdict blocks as written, and the evidence step runs
nothing. It follows the same rules as `Safety Fact`: no line, an empty value,
or `on` means on; only `off` in any case turns it off; any other value means on
with `reason: malformed_value <value>`. The key must match the case shown.
`python3 scripts/review-override.py switch --name evidence-gate --repo .`
prints the state.

On `/review`, a Critical or High finding without confirmed evidence reads
`Medium (unconfirmed)`, so it cannot make the Recommendation "Do not ship" or
"Ship with caution". `/review` asks before it runs the branch's test code. A
decline, a headless run, or no answer writes
`> Evidence gate: unverifiable (untrusted_branch)` and leaves every severity as
written. With `off`, `/review` asks nothing, downgrades no finding, and writes
`> Evidence gate: off`.

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
