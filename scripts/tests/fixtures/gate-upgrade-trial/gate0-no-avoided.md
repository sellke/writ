### Summary
Compared the shipped diff with the chosen sketch (A). The sketch avoids none of the defects below.

### Issues Found

- **Issue:** Fee math is split across two modules
- **Location:** `lib/ledger.ts:3`
- **Severity:** Major
- **Category:** architecture
- **Suggested Fix:** Move it into one module.
