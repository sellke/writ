I reviewed the change and I think AC-2.3 is not met.

- [ ] Given a declined card, when it is submitted, then the user sees the reason `[AC-2.3]`

- **Issue:** Card number is written to the request log
- **Location:** `app/api/pay.ts:42`
- **Severity:** Critical
- **Category:** security
