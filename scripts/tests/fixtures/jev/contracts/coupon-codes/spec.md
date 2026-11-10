# Discount codes at checkout

> **Status:** Draft
> **Agreed:** not yet
> **Roadmap:** Marketing runs its own offers

## Problem

The marketing team at our meal-kit company gives discounts by asking support to credit accounts by hand, about 600 credits a month. Offers go live days late and some customers are credited twice.

## Outcome

Marketing creates a code and customers apply it themselves at checkout.

**Measure:** Manual account credits fall from about 600 a month to under 50 in the first full month after launch.

## Scope

**In:**

- Percentage-off codes created by marketing and applied at checkout.

**Out:**

- Fixed-amount codes.
- Free-shipping codes.
- Codes limited to particular products.

## Acceptance criteria

- **A1.** When a marketer creates a code with a name, a percentage from 5 to 50, and an end date, it appears in the "Codes" list as "Active".
- **A2.** When a customer enters an active code at checkout and clicks "Apply", the order total drops by that percentage and the code is shown under the total.
- **A3.** A customer can use only one code on an order; applying a second code replaces the first.
- **A4.** Codes can be combined, so a customer who applies two codes gets both discounts on the same order.
- **A5.** When a marketer clicks "Deactivate" on a code, the list shows it as "Inactive".
