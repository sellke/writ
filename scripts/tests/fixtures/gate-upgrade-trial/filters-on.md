### REVIEW_RESULT: FAIL

### Summary
The fee-share route lets any signed-in user change another host's split.

### Checklist Results

#### Acceptance Criteria
- [x] Given an event with a fee, when the host publishes it, then the fee shows on the event page `[AC-1.1]`
- [ ] Given a retried payment, when the webhook fires twice, then one fee is recorded `[AC-1.2]`

### Issues Found

- **Issue:** The fee-share route never checks that the caller owns the event
- **Location:** `app/api/events/[id]/fee-share/route.ts:22`
- **Severity:** Major
- **Category:** security
- **Suggested Fix:** Compare `session.user.id` with `event.hostId` before the update.

- **Issue:** The settle job reads every event with no limit
- **Location:** `nightly settle job`
- **Severity:** Major
- **Category:** architecture
- **Suggested Fix:** Page through events 500 at a time.
