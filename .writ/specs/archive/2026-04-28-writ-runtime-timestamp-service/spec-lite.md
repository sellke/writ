# Writ Runtime Timestamp Service (Lite)

> Source: `.writ/specs/2026-04-28-writ-runtime-timestamp-service/spec.md`
> Purpose: Efficient AI context for implementation
> Status: Completed ✅

## For Coding Agents

**Deliverable:** Minimal npm package `@sellke/writ` with `date`, `timestamp`, and `timestamp --compact` runtime helpers.

**Implementation Approach:**
- Add root `package.json` for npm publish; do not turn Writ into an app project
- Add `bin/writ.js` with zero-dependency Node CLI behavior
- Successful stdout is value-only; errors/help go to stderr
- Keep runtime scope to timestamp utilities unless an ADR expands it

**Files in Scope:**
- `package.json` - npm metadata, bin entry, test/pack scripts
- `bin/writ.js` - CLI implementation
- CLI tests or verification script - exact output contract
- `commands/{create-spec,research,create-adr,knowledge}.md` - package reference migration

**Error Handling:**
- Unknown command -> usage on stderr + exit 1
- Unsupported flag -> usage on stderr + exit 1
- `--help` -> usage + exit 0

**Integration Points:**
- Writ command docs use `npx @sellke/writ date`
- Manifest/update scripts remain shell-first; runtime helper does not replace them

---

## For Review Agents

**Acceptance Criteria:**
1. `date` outputs exactly `YYYY-MM-DD`
2. `timestamp` outputs exactly `YYYY-MM-DDTHH:MM:SSZ`
3. `timestamp --compact` outputs exactly `YYYYMMDD-HHMMSS`
4. All active `@devobsessed/writ` references are removed or explicitly superseded
5. Package scope remains timestamp-only

**Business Rules:**
- Package name is `@sellke/writ`
- `date` is local calendar date; timestamps are UTC
- Zero runtime dependencies preferred
- No command runner, state manager, dashboard, MCP server, or installer replacement
- Markdown-first Writ identity remains intact

**Experience Design:**
- Entry: command needs date/timestamp for filename or metadata
- Happy path: `npx @sellke/writ date` returns one line
- Moment of truth: no command references a nonexistent package
- Feedback: quiet success; concise usage on invalid input
- Error: docs allow local fallback where npm availability should not block work

---

## For Testing Agents

**Success Criteria:**
1. CLI exact-output tests pass locally
2. Invalid invocation tests verify non-zero exit and stderr usage
3. `npm pack --dry-run` package contents are reviewed
4. Command-reference search shows no active stale package references

**Shadow Paths to Verify:**
- **Happy path:** `date`/`timestamp`/compact each print expected format
- **Nil input:** no args -> usage + exit 1
- **Empty input:** blank/unknown arg -> usage + exit 1
- **Upstream error:** package not published yet -> docs still explain local fallback for non-critical uses

**Edge Cases:**
- Month/day/hour/minute/second padding is always two digits
- Timestamp omits milliseconds
- Compact timestamp sorts lexicographically
- Help output never pollutes stdout in success cases

**Coverage Requirements:**
- Critical CLI paths: 100%
- Command reference migration: static search evidence

**Test Strategy:**
- Prefer Node built-in tests or portable shell assertions
- Include `npm pack --dry-run` in release verification
