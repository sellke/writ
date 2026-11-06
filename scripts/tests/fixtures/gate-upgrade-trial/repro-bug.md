### Summary
Followed the bug path to the repro commit and stopped.

### Repro

- **Kind:** bug fix
- **Surface:** api
- **Command:** `npm test -- app/__tests__/pay.test.ts`
- **Repro commit:** 5d1c0de
- **Failing output:**
  FAIL app/__tests__/pay.test.ts
    x records one fee per retried webhook (12 ms)

#### Why it fails

The second webhook call inserts a new fee row.

### Notes
Stopped after the repro commit as instructed; no fix written.
