### REVIEW_RESULT: FAIL

### Summary
One acceptance criterion is unmet.

### Checklist Results

#### Acceptance Criteria
- [x] Given a payment, when it is submitted, then it is charged once — verified in `test_pay.py` `[AC-2.1]`
- [x] Given a refund, when it is issued, then the ledger balances — verified in `test_pay.py` `[AC-2.2]`
- [ ] Given a declined card, when it is submitted, then the user sees the reason — the handler returns a generic 500 `[AC-2.3]`

### Security Assessment
**Risk Level:** Clean

### Issues Found (if FAIL)
- **Issue:** Declined cards surface a generic error instead of the decline reason
- **Location:** `app/api/pay.ts:90` — catch block
- **Severity:** Critical
- **Category:** criterion
- **Suggested Fix:** Return the processor's decline code.

### Drift Analysis

**Overall Drift:** None
