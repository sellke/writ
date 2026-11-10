# Renew a resident parking permit online

> **Status:** Built
> **Agreed:** 2026-10-24 by Tomas Wren
> **Roadmap:** Fewer lapsed permits

## Problem

Residents renew their parking permit by post once a year. About 1 in 5 renewals arrives late, the permit lapses, and the resident is fined.

## Outcome

A resident renews online in a few minutes before the permit lapses.

**Measure:** Lapsed permits fall from 20% to under 8% of renewals due, measured over the first three months.

## Scope

**In:**

- Online renewal of an existing resident permit.

**Out:**

- New permit applications.
- Visitor permits.

## Acceptance criteria

- **A1.** When a resident enters their permit number and postcode and both match a permit due within 30 days, the page shows the permit's vehicle registration, its expiry date, and the renewal fee.
- **A2.** When the number and postcode do not match a permit, or either is empty, the page shows "We couldn't find that permit. Check the number and postcode." and shows no permit details.
- **A3.** When the resident pays the fee by card, the expiry date moves forward by 12 months and they receive a confirmation email with the new expiry date.
- **A4.** An attempt to renew more than 30 days before expiry shows "You can renew from" followed by the date and takes no payment.
- **A5.** When the card payment fails, the expiry date does not change and the page shows "Payment failed. Your permit has not been renewed."
- **A6.** The council's accessibility officer completes a renewal using VoiceOver and reports no blocker.

## Proof

> Verified at `2be9a61` on 2026-11-08 by a verifier that did not write the change.

- **A1. Proved.** Entered permit RP-204417 and postcode LS6 2AB on staging. The page showed "Vehicle: YK19 ABC", "Expires: 28 Nov 2026", and "Renewal fee: £65.00", which match the seeded permit.
- **A2. Needs a person.** A tester should try a wrong postcode and an empty form and read the message that comes back.
- **A3. Proved.** Paid the £65.00 fee with the test card and the page showed "Payment received". Afterwards the permit page still showed "Expires: 28 Nov 2026", and the confirmation email gave the same date.
- **A4. Needs a person.** Someone needs to check by hand that an early renewal is refused and that no money is taken.
- **A5. Proved.** Paid with the test card that is always declined. The page showed "Payment failed. Your permit has not been renewed." and the permit page still showed "Expires: 28 Nov 2026".
- **A6. Needs a person.** Only the accessibility officer can say whether a VoiceOver user hits a blocker. Book a session with her and record the result.

### Try it yourself

1. Open the renewal page on staging and enter RP-204417 and LS6 2AB.

### Not covered

- Permits registered to a business address.
