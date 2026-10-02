### REVIEW_RESULT: FAIL

### Summary
Layering issue in the payment route.

### Checklist Results

#### Acceptance Criteria
- [x] Given a payment, when it is submitted, then it is charged once `[AC-2.1]`
- [x] Given a refund, when it is issued, then the ledger balances `[AC-2.2]`
- [x] Given a declined card, when it is submitted, then the user sees the reason `[AC-2.3]`

### Issues Found
- **Issue:** Route calls the processor SDK directly, bypassing the payments service
- **Location:** `app/api/pay.ts:12`
- **Severity:** Major
- **Category:** architecture
- **Suggested Fix:** Go through `services/payments.ts`.

### Drift Analysis

**Overall Drift:** None
