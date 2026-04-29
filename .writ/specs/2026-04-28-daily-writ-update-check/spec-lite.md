# Daily Writ Update Check (Lite)

> Source: `.writ/specs/2026-04-28-daily-writ-update-check/spec.md`
> Purpose: Efficient AI context for implementation
> Status: Completed ✅

## For Coding Agents

**Deliverable:** Instruction-level daily update awareness on first Writ invocation, cached under `.writ/state/`, pointing to `/update-writ` only when appropriate.

**Implementation Approach:**
- Update `system-instructions.md` and `cursor/writ.mdc` startup guidance together
- Check daily cache before any network probe; at most one probe per local day
- Use existing manifest/source info; never clone/apply/update during startup
- Do not add `@sellke/writ update-check`; runtime remains timestamp-only

**Files in Scope:**
- `system-instructions.md` - primary startup protocol
- `cursor/writ.mdc` - Cursor mirror of startup protocol
- `commands/update-writ.md` - optional relationship clarification only
- `.writ/state/writ-update-check.json` - planned ephemeral cache shape

**Error Handling:**
- Missing/old manifest -> skip quietly
- Network failure -> record same-day failure and continue
- Source repo or linked install -> no `/update-writ` prompt
- Existing same-day cache -> skip network work

**Integration Points:**
- Session Auto-Orientation runs after this check
- `/update-writ` remains the only update application workflow
- Mirrors must stay behaviorally synchronized

---

## For Review Agents

**Acceptance Criteria:**
1. Startup instructions define first-in-session daily update check
2. Same-day repeat invocations skip network work
3. Update-available message is concise and non-blocking
4. No-update/offline/unsupported/source-repo paths stay quiet
5. Startup never mutates Writ files, manifests, or git history
6. `@sellke/writ` has no new update-check command

**Business Rules:**
- One upstream probe per project per local calendar day
- State is ephemeral under `.writ/state/`
- Startup discovers only; `/update-writ` applies updates
- Source repo must not recommend `/update-writ`
- User controls whether/when to update

**Experience Design:**
- Entry: first Writ invocation in a session
- Happy path: cache check -> optional lightweight probe -> original task continues
- Moment of truth: "Writ update available. Run `/update-writ` when ready."
- Feedback: visible only when action is useful
- Error: offline or unsupported checks do not interrupt work

---

## For Testing Agents

**Success Criteria:**
1. Manual verification covers fresh cache, same-day cache, stale cache
2. Offline/upstream failure proceeds without repeated prompts
3. Source repo and linked install do not suggest `/update-writ`
4. Instruction mirrors are checked for startup-rule parity

**Shadow Paths to Verify:**
- **Happy path:** stale/no cache + newer upstream -> note points to `/update-writ`
- **Nil input:** missing manifest/source -> skip quietly
- **Empty input:** current upstream -> no notification
- **Upstream error:** network failure -> cache failure for today and continue

**Edge Cases:**
- Cache file missing parent directory -> create only when recording result
- Local date changes at midnight -> next check allowed
- Manifest source unavailable -> no speculative fallback
- User is already running `/update-writ` -> do not duplicate prompt

**Coverage Requirements:**
- Critical behavior verified manually via documented shell/state scenarios
- Mirror parity checked by static diff/search

**Test Strategy:**
- Use temporary `.writ/state/` fixtures or documented manual setup
- Search confirms no runtime helper expansion
- Review `/update-writ` relationship text for source-repo accuracy
