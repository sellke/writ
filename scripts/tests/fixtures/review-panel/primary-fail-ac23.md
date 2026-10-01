### EVALUATION_RESULT: FAIL

### Summary
AC-2.3 is not supported: no test shows the decline reason. Overall Drift: None.

### Checklist Results

#### Acceptance Criteria
- [x] Given a payment, when it is submitted, then it is charged once — `test_pay.py::test_once` [AC-2.1]
- [x] Given a refund, when it is issued, then the ledger balances — `test_pay.py::test_refund` [AC-2.2]
- [ ] Given a declined card, when it is submitted, then the user sees the reason — not satisfied: no test asserts the message `[AC-2.3]`

### Issues Found (if FAIL)

- **Issue:** Decline reason is swallowed and never shown
- **Location:** `app/api/pay.ts:88`
- **Severity:** Critical
- **Category:** criterion

### Drift Analysis

**Overall Drift:** None
