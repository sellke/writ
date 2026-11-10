# Renew a resident parking permit online

> **Status:** Draft
> **Agreed:** not yet
> **Roadmap:** Fewer lapsed permits

## Problem

Residents renew their parking permit by post once a year. About 1 in 5 renewals arrives late, the permit lapses, and the resident is fined for parking outside their own home.

## Outcome

A resident renews online in a few minutes before the permit lapses.

**Measure:** Lapsed permits fall from 20% to under 8% of renewals due, measured over the first three months.

## Scope

**In:**

- Online renewal of an existing resident permit.

**Out:**

- New permit applications.
- Visitor permits.
- Changing the vehicle on a permit.

## Acceptance criteria

- **A1.** When a resident enters their permit number and postcode and both match a permit due within 30 days, the page shows the permit's vehicle registration, its expiry date, and the renewal fee.
- **A2.** When the number and postcode do not match a permit, or either is empty, the page shows "We couldn't find that permit. Check the number and postcode." and shows no permit details.
- **A3.** When the resident pays the fee by card, the expiry date moves forward by 12 months and they receive a confirmation email with the new expiry date.
- **A4.** During renewal the resident can change the vehicle registration on the permit.
- **A5.** A permit can be renewed only in the 30 days before it expires; an earlier attempt shows "You can renew from" followed by the date and takes no payment.
- **A6.** A resident can renew at any time of year, including more than 30 days before expiry, and the new 12 months are added on.
- **A7.** When the card payment fails, the expiry date does not change and the page shows "Payment failed. Your permit has not been renewed."
