### REVIEW_RESULT: PASS

### Summary
Both criteria hold. The story says: As a guest, I want to see the event fee before I pay.

### Checklist Results

#### Acceptance Criteria
- [x] Given an event with a fee, when a guest opens it, then the fee is shown — verified in `components/__tests__/ui.test.tsx` `[AC-1.1]`
- [x] Given a free event, when a guest opens it, then no fee line renders — verified in `components/__tests__/ui.test.tsx` `[AC-1.2]`

### Security Assessment
**Risk Level:** Clean
No new input paths.

### Boundary Compliance

**Not applicable** (no boundary map)
