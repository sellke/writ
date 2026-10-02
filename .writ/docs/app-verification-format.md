# App Verification Recipe Format

> Location: `.writ/docs/app-verification.md` (project-authored; Writ never ships this file)
> Purpose: Tell Writ how to start your app, which checks prove each feature works, and which targets are safe to run against
> Read by: `scripts/app-verify.py` (`validate`, `touched`, `run`), `/create-uat-plan`, `/implement-story` Gate 4.5

## Why this file exists

Writ can only claim a feature works if a machine decided it. The recipe names your project's own commands: how to launch the app, how to tell it is ready, and which test or script checks each feature. Writ starts those commands, records the result, and stops what it started. It never brings its own browser, test runner, or server.

`/create-uat-plan` drafts the recipe the first time it runs on a project and asks you to confirm it. After that, you own it: edit it like any other project file.

The recipe lives under `.writ/docs/`, which Writ's installer overlays from its own `.writ/docs/*.md`. Writ therefore never ships a file named `app-verification.md`, so your recipe can never be overwritten. A test in the Writ repo enforces that.

## Sections

A recipe is Markdown with six `##` sections, in any order:

| Section | Holds |
|---|---|
| `## Launch` | `Command` (required), `Ready when` (required), `Ready timeout`, `Reuse running instance` |
| `## Safety` | Either `Safety: none — <reason>`, or one or more `Variable` entries with `Allowed` and optional `Never` patterns, plus an optional `Env file` |
| `## Login` | How checks sign in — names of credential variables, never their values. Free-form; Writ does not read it |
| `## Feature Map` | The `ID \| Feature \| Paths \| Check` table |
| `## Evidence` | `Artifacts` — paths your checks write (screenshots, traces) to copy into the evidence folder, or `none` |
| `## Cleanup` | `After` — an optional command to run after the app is stopped, or `none` |

## Settings

Settings are `- **Key:** value` lines, the same format `.writ/config.md` uses. A command may be wrapped in backticks; the backticks are stripped.

| Key | Section | Value |
|---|---|---|
| `Command` | Launch | Shell command that starts the app in the foreground |
| `Ready when` | Launch | An `http://` or `https://` URL (ready when a GET returns any status below 500), or `port N` (ready when a TCP connect to 127.0.0.1:N succeeds) |
| `Ready timeout` | Launch | Seconds, as `30s` or `30`. Default `120s` |
| `Reuse running instance` | Launch | `yes` or `no` (default). With `no`, a run refuses when the app already answers before launch, because a running server's environment cannot be checked |
| `Safety` | Safety | `none — <reason>` for apps that hold no state. The reason is required |
| `Variable` | Safety | An environment variable that names the target (for example `DATABASE_URL`). Starts a new entry |
| `Allowed` | Safety | Comma-separated patterns the variable's value must match (at least one per `Variable`) |
| `Never` | Safety | Comma-separated patterns the value must not match |
| `Env file` | Safety | A `KEY=VALUE` file read when the variable is not in the process environment. Read only, never written |
| `Artifacts` | Evidence | Comma-separated paths, or `none` |
| `After` | Cleanup | Shell command, or `none` |

## Feature Map

```markdown
| ID | Feature | Paths | Check |
|---|---|---|---|
| home | Home page renders | `src/app/page.tsx`, `src/components/hero/**` | `npx playwright test e2e/home.spec.ts` |
| oauth | Third-party login | `src/auth/**` | human-only: third-party consent screen |
```

- **ID** — kebab-case (`event-create`), unique in the table. UAT scenarios cite it as `**Feature:** <id>`.
- **Feature** — one line a tester would recognise.
- **Paths** — comma-separated globs over repo-relative paths. Gate 4.5 runs every feature whose paths match a file the story changed. Required for a row with a check.
- **Check** — a backticked command whose exit code is the verdict (0 passes, anything else fails), or `human-only: <reason>` when no machine can decide it. A pipe inside the backticks is part of the command.

## Patterns

`Allowed`, `Never`, and `Paths` are shell-style globs, matched with Python's `fnmatch` against the whole value: `*` matches any run of characters (including `/`), `?` one character, `[abc]` a set. `Allowed: *dev-branch-host*` matches any value containing `dev-branch-host`.

## Safety

Safety refuses by default. Before anything launches, `app-verify.py run` resolves each `Variable` from the process environment, then from the `Env file`. It refuses, and launches nothing, when the value is unset, matches no `Allowed` pattern, or matches a `Never` pattern. A missing or unreadable env file counts as unset. Writ never edits your environment files, migrations, or data.

**Names only.** The recipe stores variable names and patterns, never secret values. The validator rejects a URL with embedded credentials (`scheme://user:password@host`, anywhere, including inside backticks) and any 32+ character token outside a backticked command. Upper-case environment variable names (`NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID`) are names, not tokens, and pass.

## Validator Findings

`python3 scripts/app-verify.py validate --recipe .writ/docs/app-verification.md` exits 0 when the recipe is valid, 1 with findings, and 2 when the file is missing or not UTF-8. Every finding has one code:

| Code | Meaning |
|---|---|
| `missing_section` | One of the six sections is absent |
| `missing_launch_command` | `## Launch` has no `Command` |
| `missing_ready` | `Ready when` is absent, or neither a URL nor `port N` |
| `missing_safety` | No `Variable` and no `Safety: none — <reason>`, or a `Variable` with no `Allowed` pattern |
| `bad_feature_row` | Wrong cell count or header, a `Check` that is neither a backticked command nor `human-only: <reason>`, or a check row with no `Paths` |
| `duplicate_feature_id` | An ID appears twice |
| `bad_feature_id` | An ID is not kebab-case |
| `secret_value` | A credential-bearing URL, or a long token outside backticks |
| `bad_timeout` | `Ready timeout` is not a positive number of seconds |

## Worked Example

A web app backed by a branch database, with Playwright checks:

```markdown
# App Verification Recipe

## Launch
- **Command:** `pnpm dev --port 3100`
- **Ready when:** http://127.0.0.1:3100/api/health
- **Ready timeout:** 90s
- **Reuse running instance:** no

## Safety
- **Variable:** DATABASE_URL
- **Allowed:** *ep-dev-*.neon.tech*, *localhost*
- **Never:** *prod*
- **Env file:** .env.local

## Login
- **Method:** checks sign in themselves with the seeded test user
- **Credentials from:** E2E_USER_EMAIL, E2E_USER_PASSWORD

## Feature Map
| ID | Feature | Paths | Check |
|---|---|---|---|
| event-create | Create an event from the dashboard | `src/app/events/**`, `src/lib/events.ts` | `pnpm exec playwright test e2e/event-create.spec.ts` |
| invite-accept | Accept an invite link | `src/app/invite/**` | `pnpm exec playwright test e2e/invite.spec.ts` |
| google-oauth | Sign in with Google | `src/auth/**` | human-only: third-party consent screen |

## Evidence
- **Artifacts:** test-results/, playwright-report/

## Cleanup
- **After:** none
```

A second, runnable example is the stateless fixture recipe Writ's own tests drive: `scripts/tests/fixtures/app-verify/recipe-pass.md`.

## Evidence Layout

Each feature run writes `{spec}/evidence/<run>/<feature-id>/result.json` (schema `app-verify-result-v1`) plus `stdout.log` and `stderr.log`, each truncated to 256 KB. `<run>` is `story-N` for Gate 4.5 and `uat` for `/create-uat-plan`. Launch output lands in `{spec}/evidence/<run>/_launch/`. `Artifacts` are copied up to 5 MB per feature; larger ones are recorded by path only, and absent ones are recorded as `missing`.
