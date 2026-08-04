# Daily Writ Update Check

> **Status:** Completed ✅
> **Created:** 2026-04-28
> **Owner:** Adam Sellke
> **Issue:** `.writ/issues/features/2026-04-28-daily-session-update-check.md`

---

## Specification Contract

**Deliverable:** Add an instruction-level daily Writ update awareness check that runs on first Writ invocation in a session, rate-limited to once per day via `.writ/state/`, and points users to `/update-writ` only when an upstream update appears available.

**Origin:** Promoted from issue: `.writ/issues/features/2026-04-28-daily-session-update-check.md`

**Must Include:**

- A startup protocol in `system-instructions.md` and `cursor/writ.mdc`
- Concise update-available messaging that points to `/update-writ`
- Quiet no-op behavior when Writ is current, recently checked, offline, or not an installed Writ project
- Guidance that startup never applies updates, overwrites files, or changes manifests

**Hardest Constraint:** This must not turn `@sellke/writ` into a general Writ CLI or make every session wait on network work. The check belongs in agent instructions, with a daily cache and short failure path.

### Experience Design

- **Entry point:** Any first Writ invocation in a session, before session auto-orientation or command-specific workflow begins.
- **Happy path:** The agent checks `.writ/state/` for today's cache entry. If no check has run today, it performs one lightweight upstream probe, records the result, and continues with the user's requested workflow.
- **Moment of truth:** If an upstream update appears available, the user sees a terse note such as: "Writ update available. Run `/update-writ` when you are ready."
- **Feedback model:** Update-available results are visible but non-blocking. Current, recently checked, unsupported, and offline states stay silent unless the user explicitly asks about update status.
- **Error experience:** Network or manifest failures do not interrupt startup. The agent records enough state to avoid repeated same-day attempts and proceeds with the original task.
- **First-use state:** If `.writ/state/` does not exist, the agent may create the cache directory only when it is about to record a check result. Missing state should not be treated as an error.

### Business Rules

- **Daily limit:** Run at most one upstream update probe per project per local calendar day.
- **State location:** Store the daily check cache under `.writ/state/`, which is ephemeral and gitignored.
- **No mutation:** Startup update discovery never applies updates, overwrites Writ files, edits manifests, installs packages, or creates commits.
- **Installed project behavior:** For copied Writ installations, compare the installed manifest version/source with the upstream repository state and point to `/update-writ` when newer upstream content appears available.
- **Source repo behavior:** In the Writ source repository, do not recommend `/update-writ`, because that command intentionally aborts in the source repo. Source-repo update awareness may be skipped or expressed as source maintenance guidance only if explicitly requested.
- **Linked installation behavior:** Linked installations should not be prompted to run `/update-writ`; they should follow existing linked-install guidance from lifecycle commands.
- **Runtime boundary:** Do not add `@sellke/writ update-check` or any other runtime update command in this spec. The runtime helper remains scoped to timestamp utilities unless a separate ADR expands it.
- **User control:** The prompt is informational. The user chooses whether and when to run `/update-writ`.

## Current State

- `system-instructions.md` and `cursor/writ.mdc` define a first-session auto-orientation flow for sessions without a specific command.
- Users must explicitly run `/update-writ` to discover and apply upstream Writ updates.
- `/update-writ` already owns update application, manifest classification, customized-file decisions, and source-repo guards.
- The `@sellke/writ` runtime package is scoped to deterministic date and timestamp helpers.

## Expected Outcome

- Writ performs passive update discovery on first invocation in a session without disrupting the requested workflow.
- The update check is rate-limited to once per local day per project.
- Available updates produce a concise pointer to `/update-writ`.
- No-update, offline, unsupported, source-repo, and already-checked states stay quiet.
- The implementation remains markdown-instruction driven and does not expand the runtime helper.

## Success Criteria

1. First Writ invocation checks for updates only when the daily cache permits.
2. Repeated invocations on the same local day skip network work.
3. Available upstream updates produce a concise non-blocking note that points to `/update-writ`.
4. No-update, offline, unsupported, linked-install, and source-repo states do not distract or block the user's task.
5. Startup update discovery never applies updates or mutates installed Writ files.
6. `@sellke/writ` remains unchanged and timestamp-only.
7. `system-instructions.md` and `cursor/writ.mdc` remain behaviorally synchronized for the new startup rule.

## Scope Boundaries

**Included:**

- Startup instruction updates in `system-instructions.md` and `cursor/writ.mdc`
- A project-local daily cache contract under `.writ/state/`
- Lightweight upstream detection rules based on existing manifest/source information
- `/update-writ` cross-reference text for update-available cases
- Manual verification guidance for same-day cache, stale cache, offline, source-repo, and linked-install paths

**Excluded:**

- Applying Writ updates during startup
- Adding update commands to `@sellke/writ`
- Hosted update services, telemetry, or analytics
- CI automation for update discovery
- Broad platform lifecycle expansion for Codex or OpenClaw
- Reworking `/update-writ` beyond clarifying its relationship to startup notification

## Technical Concerns

- **Startup latency:** A network probe during every session would be annoying. The state cache must be checked before any network operation, and failures should be fast and non-blocking.
- **Prompt-instruction reliability:** Because Writ is markdown-first, the behavior depends on the agent following startup instructions. The spec should make the sequence explicit and easy to verify manually.
- **Source repo mismatch:** `/update-writ` is not valid in this repo. The startup note must avoid recommending a command that will intentionally abort.
- **Manifest variance:** Older or incomplete installations may lack manifest metadata. The safe behavior is to skip quietly rather than infer aggressively.
- **Mirror drift:** `system-instructions.md` and `cursor/writ.mdc` duplicate key instruction text. The implementation should update both in the same story and verify the relevant startup sections match.

## Recommendations

- Keep the daily cache format small and human-readable, for example `.writ/state/writ-update-check.json`.
- Cache both successful and failed checks for the current day so an offline network does not cause repeated startup attempts.
- Use a short probe with existing manifest source information instead of cloning the upstream repository during startup.
- Add a precise "do not run in source repo" rule to prevent dogfooding sessions from getting misleading `/update-writ` prompts.

## Cross-Spec Overlap

No active in-progress spec appears to touch this feature area.

Completed specs that constrain this work:

- `2026-04-28-writ-runtime-timestamp-service` limits `@sellke/writ` to timestamp utilities; this spec must not expand the runtime helper.
- `2026-04-24-phase4-production-grade-substrate` reinforces markdown-first behavior, no unnecessary external dependencies, and synchronized instruction surfaces.

## Story Plan

1. **story-1-startup-protocol:** Add the daily update check protocol to Writ startup instructions. Dependencies: None.
2. **story-2-cache-and-detection-contract:** Define the `.writ/state/` cache shape and update detection decision rules. Dependencies: Story 1.
3. **story-3-verification-and-issue-linkage:** Add verification coverage and connect the promoted issue to the completed spec package. Dependencies: Stories 1 and 2.

## Implementation Approach

Implement this as a documentation/instruction change, not runtime code. The implementation should update the duplicated startup guidance in `system-instructions.md` and `cursor/writ.mdc`, and may clarify `/update-writ` only where needed to distinguish update notification from update application.

The likely state contract is a small JSON file under `.writ/state/`, such as:

```json
{
  "last_checked_date": "2026-04-28",
  "source": "https://github.com/sellke/writ.git",
  "installed_version": "abc1234",
  "latest_seen_version": "def5678",
  "status": "update_available"
}
```

The implementation should not require this exact schema if a simpler one satisfies the story acceptance criteria, but it must preserve the daily limit, no-mutation rule, and quiet failure behavior.

## Relevant Files

- `system-instructions.md` - Primary Writ startup behavior and session auto-orientation.
- `cursor/writ.mdc` - Cursor active instruction mirror for Writ startup behavior.
- `commands/update-writ.md` - Existing update application workflow that notification points to.
- `.writ/state/` - Ephemeral cache location for the daily update check.
- `.writ/issues/features/2026-04-28-daily-session-update-check.md` - Source issue to receive `spec_ref`.
