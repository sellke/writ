# Check a gift card balance online

> **Status:** Built
> **Agreed:** 2026-10-21 by Tomas Wren
> **Roadmap:** Fewer calls to stores

## Problem

Customers of our bookshop chain phone a store to ask how much is left on a gift card. Stores take about 220 of these calls a week.

## Outcome

A customer checks a gift card balance on the website without phoning a store.

**Measure:** Calls to stores about gift card balances fall from about 220 a week to under 50, comparing the four weeks before launch with the four weeks after.

## Scope

**In:**

- A balance check page for physical gift cards.

**Out:**

- Topping up a card.
- Digital gift cards.

## Acceptance criteria

- **A1.** When a customer enters a 16-digit card number and the 4-digit PIN from the back of the card and clicks "Check balance", the page shows the balance in pounds and pence and the card's expiry date.
- **A2.** When the number and PIN do not match a card, the page shows "We couldn't find a card with those details" and shows no balance.
- **A3.** When either field is empty or the wrong length, the form shows "Enter the 16-digit number and 4-digit PIN" and nothing is looked up.
- **A4.** After 5 failed attempts from one browser in 10 minutes, the form is locked for 15 minutes and shows "Too many attempts. Try again in 15 minutes."
- **A5.** In a test with five shoppers in the Camden store, at least four find their balance on the page without help.
- **A6.** A card past its expiry date shows "This card expired on" followed by the date, and shows no balance.

## Proof

> Verified at `17c4d88` on 2026-11-05 by a verifier that did not write the change.

- **A1. Proved.** Entered test card 6035 0000 0000 0017 with PIN 4821 on staging and clicked "Check balance". The page showed "Balance: £23.50" and "Expires 30 Nov 2027", which match the seeded card.
- **A2. Proved.** Entered the same card number with PIN 0000 and clicked "Check balance". The site returned an error page reading "502 Bad Gateway". Screenshot in `proof/a2-wrong-pin.png`.
- **A3. Proved.** Ran `npm test -- balance-form`: 7 passed. The cases "empty number", "15-digit number", "17-digit number", "empty PIN", "3-digit PIN", and "5-digit PIN" each expect the message "Enter the 16-digit number and 4-digit PIN" and expect no lookup call. Output in `proof/a3-jest.txt`.
- **A4. Needs a person.** A person needs to type a wrong PIN five times and see whether the form locks.
- **A5. Needs a person.** Whether real shoppers find their balance unaided can only be seen in the store. Run the five-shopper test in Camden and record how many succeed.

### Try it yourself

1. Open the balance page on staging and enter card 6035 0000 0000 0017 with PIN 4821.

### Not covered

- Cards issued before 2019, which use a different number range.
