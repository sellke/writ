### REVIEW_RESULT: FAIL

### Summary
Criteria met; one security issue, located by quoting the code.

### Checklist Results

#### Acceptance Criteria
- [x] Given a payment, when it is submitted, then it is charged once `[AC-2.1]`

### Issues Found (if FAIL)

1. **Issue:** Admin check returns the session token to any caller
   - **Location:** `if (user.isAdmin) return token`
   - **Severity:** Critical
   - **Category:** security
   - **Suggested Fix:** Return a boolean, never the token.

### Drift Analysis

**Overall Drift:** None
