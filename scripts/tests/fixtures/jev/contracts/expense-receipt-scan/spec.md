# Fill in an expense claim from a receipt photo

> **Status:** Draft
> **Agreed:** not yet
> **Roadmap:** Expenses in the same week

## Problem

Field sales reps at a medical-devices distributor type every receipt into the expenses app by hand, usually weeks late. Finance chases about half the team every month, and reps lose receipts before they claim.

## Outcome

A rep photographs a receipt and the claim fills itself in.

**Measure:** Submitting expenses becomes quicker and less painful for reps.

## Scope

**In:**

- Reading the date, merchant, and total from a photographed receipt.

**Out:**

- Mileage claims.
- Receipts in currencies other than euros.
- Changes to the approval steps.

## Acceptance criteria

- **A1.** When a rep photographs a receipt in the app, a new claim opens with the date, merchant, and total filled in from the photo.
- **A2.** The rep can change any filled-in field before submitting.
- **A3.** When the rep taps "Submit", the claim appears in their list as "Submitted" with the photo attached.
- **A4.** Scanning should be accurate enough for normal use.
- **A5.** A claim keeps its photo after submission, and the approver sees the photo beside the claim.
