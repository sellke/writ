# Writ Runtime Timestamp Service

> **Status:** Completed ✅
> **Created:** 2026-04-28
> **Owner:** @AdamSellke
> **Package:** `@sellke/writ`

---

## Specification Contract

**Deliverable:** Add a deliberately narrow npm-published Writ runtime helper package, `@sellke/writ`, that provides deterministic date and timestamp commands for Writ command files.

**Origin:** `/create-spec` request after discovering that existing command references to `npx @devobsessed/writ date` point at an unpublished package. The requested replacement package is `@sellke/writ`, verified as currently unpublished on npm.

**Must Include:**

- A root-level npm package definition for `@sellke/writ` with a `bin` entry that can be invoked via `npx @sellke/writ ...`
- Runtime commands:
  - `npx @sellke/writ date` -> local calendar date in `YYYY-MM-DD`
  - `npx @sellke/writ timestamp` -> UTC ISO 8601 timestamp without milliseconds, e.g. `2026-04-28T20:23:53Z`
  - `npx @sellke/writ timestamp --compact` -> filesystem-safe UTC timestamp, e.g. `20260428-202353`
- Command documentation updated to reference `@sellke/writ` instead of `@devobsessed/writ`
- Release and verification guidance that keeps this a tiny helper, not a general-purpose Writ CLI

**Hardest Constraint:** Writ has an accepted product identity as a methodology-first markdown framework, not a CLI tool. This runtime package must solve timestamp determinism without expanding into command orchestration, state management, dashboards, or platform-specific automation.

### Experience Design

- **Entry point:** An agent executing a Writ command needs the current date or timestamp for a file path, state file, manifest header, or metadata field.
- **Happy path:** The agent runs `npx @sellke/writ date` or `npx @sellke/writ timestamp`, receives exactly one line on stdout, and uses it directly.
- **Moment of truth:** `/create-spec`, `/research`, `/create-adr`, and `/knowledge` stop referencing nonexistent packages and produce consistent date strings across machines.
- **Feedback model:** Successful commands print only the requested value. Help and error output appear only for invalid invocations.
- **Error experience:** Unknown commands print concise usage and exit non-zero. The Writ command docs still allow local fallback where appropriate so a transient npm failure never blocks methodology work.
- **First-use state:** `npx @sellke/writ date` works without prior install after the package is published.

### Business Rules

- **Package scope:** Use `@sellke/writ`, aligning npm ownership with the `sellke/writ` source repository.
- **Runtime scope:** Date and timestamp helpers only. Do not implement Writ command execution, spec creation, installer orchestration, or agent workflows in this package.
- **Output stability:** Runtime output must be machine-parseable and newline-terminated, with no banners, emojis, warnings, or extra prose on stdout.
- **Timezone rule:** `date` returns the local system calendar date because Writ file names are human workflow artifacts; `timestamp` returns UTC because timestamps identify events and should compare across machines.
- **Dependency rule:** Prefer zero runtime dependencies. Node's standard library is sufficient.
- **Compatibility rule:** Support the active Node LTS baseline used by npm/npx users. Avoid APIs that require bleeding-edge Node.
- **Fallback rule:** Command markdown may say "use `npx @sellke/writ date` when available; otherwise use local system date in `YYYY-MM-DD`" for non-critical documentation capture.

## Success Criteria

1. `npx @sellke/writ date` produces exactly `YYYY-MM-DD`.
2. `npx @sellke/writ timestamp` produces exactly `YYYY-MM-DDTHH:MM:SSZ`.
3. `npx @sellke/writ timestamp --compact` produces exactly `YYYYMMDD-HHMMSS`.
4. Invalid invocations exit non-zero with concise usage on stderr.
5. All existing command references to `@devobsessed/writ` are replaced with `@sellke/writ` or a documented fallback pattern.
6. The package can be tested locally before publish and published publicly without adding runtime dependencies.
7. The product boundary remains explicit: `@sellke/writ` is a utility helper, not a Writ command runner.

## Scope Boundaries

**Included:**

- Root package metadata and npm bin wiring
- A small Node CLI implementation for date/timestamp output
- Lightweight tests or shell-based verification for the CLI contract
- Updates to Writ command docs that currently reference the nonexistent package
- Release notes/documentation for publishing `@sellke/writ`

**Excluded:**

- General Writ CLI command execution
- Replacing `scripts/install.sh`, `scripts/update.sh`, or existing shell workflow scripts
- Persistent state, telemetry, auth, hosted services, MCP servers, dashboards, or databases
- Backward compatibility with the unpublished `@devobsessed/writ` package name
- Retrofitting old specs unless they are active references that would confuse new work

## Technical Concerns

- **Product identity drift:** Adding `package.json` can make the repo look like a Node application. Mitigation: document the package as a tiny runtime utility and keep existing markdown-first architecture language intact.
- **Publish ownership:** `@sellke/writ` is available on npm, but publishing requires access to the `sellke` npm scope. If the scope is not configured, the implementation should fail at publish time with clear instructions rather than renaming the package casually.
- **npx latency/network dependency:** `npx` may fetch on first run. Writ commands should still allow local date fallback where timestamp precision is not critical.
- **Timezone ambiguity:** `date` local vs. `timestamp` UTC must be called out because both are reasonable defaults in different contexts.

## Recommendations

- Keep the CLI file small enough to read in one screen. If the implementation grows beyond date/timestamp utilities, stop and create an ADR before adding more runtime behavior.
- Add a `npm pack --dry-run` verification step so release confirms the package contains only the expected files.
- Use tests that assert exact stdout/stderr behavior. This is a command contract, not business logic.
- Update command references in one story after the runtime exists so documentation can point to a verified command.

## Cross-Spec Overlap

- **Phase 4 Production-Grade Substrate** touches `commands/create-spec.md`, `commands/knowledge.md`, and `scripts/*` conventions. This spec should preserve its product-boundary guidance and avoid changing unrelated substrate work.
- **Utility Command Refinement** preserved `npx @devobsessed/writ date` as a Writ-specific detail. This spec intentionally supersedes that detail with `@sellke/writ`.
- **Product Decisions Log DEC-001** rejects Writ as a broad CLI tool. This spec is valid only if it remains a narrow timestamp helper.

## Story Plan

1. **story-1-runtime-package:** Create the minimal `@sellke/writ` npm package and CLI behavior. Dependencies: None.
2. **story-2-command-reference-migration:** Replace existing command references from `@devobsessed/writ` to `@sellke/writ` with appropriate fallback wording. Dependencies: Story 1.
3. **story-3-release-and-verification:** Add verification and publish guidance so the package can be tested, packed, and released safely. Dependencies: Stories 1 and 2.

## Implementation Approach

Add the smallest possible Node package at the repository root. The package should coexist with the markdown-first repository structure without implying a build system for command files. A likely implementation is:

- `package.json` with `name: "@sellke/writ"`, `bin: { "writ": "bin/writ.js" }`, `files`, `scripts.test`, and package metadata
- `bin/writ.js` with argument parsing for `date`, `timestamp`, `timestamp --compact`, and help/error output
- tests using Node's built-in test runner or a portable shell script; no third-party dependencies unless a strong need emerges
- command markdown updates after the CLI behavior is verified locally

## Package Review Checklist

- [ ] `package.json` does not introduce unnecessary dependencies
- [ ] `bin/writ.js` has a shebang and executable permissions
- [ ] stdout is value-only for successful commands
- [ ] stderr is usage-only for invalid commands
- [ ] `npm pack --dry-run` includes only expected package files
- [ ] All active Writ command references use `@sellke/writ`
- [ ] Documentation states this is a runtime helper, not a Writ CLI pivot
