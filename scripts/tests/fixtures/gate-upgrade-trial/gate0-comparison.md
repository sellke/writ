### Summary
Compared the shipped diff with the chosen sketch (B). One defect in the diff is one the sketch avoids.

### Checklist Results
- [ ] Given a retried payment, when the webhook fires twice, then one fee is recorded `[AC-1.2]`

### Issues Found

- **Issue:** The webhook handler inserts a fee row before it checks the payment intent, so a retry double-charges
- **Location:** `app/api/pay/webhook.ts:40`
- **Severity:** Critical
- **Category:** security
- **Avoided by:** sketch B line 14 — upsert keyed on payment_intent_id
- **Suggested Fix:** Use the sketch's upsert.

- **Issue:** Fee math is split across two modules
- **Location:** `lib/ledger.ts:3`
- **Severity:** Major
- **Category:** architecture
- **Suggested Fix:** Move it into one module.

### Recommendations

- **Issue:** A shared fee helper would read better
- **Location:** `lib/helpers.ts:1`
- **Severity:** Critical
- **Category:** security
- **Avoided by:** sketch A line 3
