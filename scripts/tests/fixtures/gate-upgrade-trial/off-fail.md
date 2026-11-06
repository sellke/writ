### REVIEW_RESULT: FAIL

### Summary
The host fee is charged twice when a payment retries. The story says: As a host, I want to collect one fee per event so that my guests are never overcharged.

### Checklist Results

#### Acceptance Criteria
- [x] Given an event with a fee, when the host publishes it, then the fee shows on the event page — verified in `app/__tests__/api.test.ts` `[AC-1.1]`
- [ ] Given a retried payment, when the webhook fires twice, then one fee is recorded — the insert has no idempotency check `[AC-1.2]`

### Security Assessment
**Risk Level:** High
The pay route trusts the amount the client sends.

### Issues Found

- **Issue:** The pay route trusts the amount the client sends
- **Location:** `app/api/pay/route.ts:12`
- **Severity:** Critical
- **Category:** security
- **Suggested Fix:** Read the amount from the event record:
  ```diff
  --- a/app/api/pay/route.ts
  +++ b/app/api/pay/route.ts
  @@ -10,3 +10,3 @@
  -  const amount = body.amount;
  +  const amount = event.fee;
  ```

- **Issue:** Retried webhooks record a second fee row
- **Location:** `app/api/pay/webhook.ts:40`
- **Severity:** Major
- **Category:** criterion
- **Suggested Fix:** Key the insert on the payment intent id.

### Boundary Compliance

**Not applicable** (no boundary map)
