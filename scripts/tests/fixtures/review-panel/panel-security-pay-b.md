### REVIEW_RESULT: FAIL

### Summary
PAN leak in logs.

### Checklist Results

#### Acceptance Criteria
- [x] Given a payment, when it is submitted, then it is charged once `[AC-2.1]`
- [x] Given a refund, when it is issued, then the ledger balances `[AC-2.2]`
- [x] Given a declined card, when it is submitted, then the user sees the reason `[AC-2.3]`

### Issues Found
- **Issue:** Raw card data reaches the logger
- **Location:** app/api/pay.ts:44
- **Severity:** Major
- **Category:** Security
- **Suggested Fix:** Mask before logging.

### Drift Analysis

**Overall Drift:** None
