### REVIEW_RESULT: FAIL

### Summary
The retried webhook still records a second fee, and fee math now lives in two places.

### Checklist Results

#### Acceptance Criteria
- [x] Given an event with a fee, when the host publishes it, then the fee shows on the event page `[AC-1.1]`
- [ ] Given a retried payment, when the webhook fires twice, then one fee is recorded — no idempotency check `[AC-1.2]`

### Security Assessment
**Risk Level:** Medium
The fee calculation is duplicated, so a rounding fix can land in one copy only.

### Safety Fact

- **Changed:** `lib/fees.ts`
- **Reached by:** `app/api/pay/route.ts`, `app/api/cron/settle.ts`
- **Rung:** traced

### Issues Found

- **Issue:** Fee math is duplicated between the route handler and the settle job; AC-1.2 depends on both agreeing
- **Location:** `lib/fees.ts:8`
- **Severity:** Major
- **Category:** architecture
- **Suggested Fix:** Export one `computeFee(event)` and call it from both.
  ```diff
  @@ -1,4 +1,6 @@
  +export function computeFee(event) {
  +  return Math.round(event.price * 0.05);
  +}
  ```

- **Issue:** Variable naming is inconsistent
- **Location:** `lib/fees.ts:20`
- **Severity:** Minor
- **Category:** taste
- **Suggested Fix:** Rename `amt` to `amount`.
