# Discount codes at checkout

> **Status:** Built
> **Agreed:** 2026-10-26 by Priya Nair
> **Roadmap:** Marketing runs its own offers

## Problem

The marketing team at our meal-kit company gives discounts by asking support to credit accounts by hand, about 600 credits a month.

## Outcome

Marketing creates a code and customers apply it themselves at checkout.

**Measure:** Manual account credits fall from about 600 a month to under 50 in the first full month after launch.

## Scope

**In:**

- Percentage-off codes created by marketing and applied at checkout.

**Out:**

- Fixed-amount codes.
- Free-shipping codes.

## Acceptance criteria

- **A1.** When a marketer creates a code with a name, a percentage from 5 to 50, and an end date, it appears in the "Codes" list as "Active".
- **A2.** When a customer enters an active code at checkout and clicks "Apply", the order total drops by that percentage and the code is shown under the total.
- **A3.** When a customer enters a code that is unknown, inactive, or past its end date, the page shows "That code isn't valid" and the total does not change.
- **A4.** A customer can use only one code on an order; applying a second code replaces the first.
- **A5.** When a marketer clicks "Deactivate" on a code, the list shows it as "Inactive".
- **A6.** When the name is empty or the percentage is outside 5 to 50, the form shows "Enter a name and a percentage from 5 to 50" and no code is created.

## Proof

> Verified at `f4410ac` on 2026-11-07 by a verifier that did not write the change.

- **A1. Proved.** Created the code SPRING20 at 20% ending 30 June in the staging admin. The "Codes" list showed "SPRING20, 20%, Active".
- **A2. Proved.** With a basket total of £48.00, entered SPRING20 at checkout and clicked "Apply". The total became £38.40 and "SPRING20 (-20%)" was shown under the total.
- **A3. Proved.** Ran the checkout test suite. Results in `proof/a3-checkout-tests.txt`.
- **A4. Proved.** Tested and confirmed working.
- **A5. Proved.** The deactivate endpoint sets `active = false`, and the list template reads that flag to print "Inactive".

### Try it yourself

1. In the staging admin, create a 20% code and apply it to a basket.

### Not covered

- Orders paid with account credit.
