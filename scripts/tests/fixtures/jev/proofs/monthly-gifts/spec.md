# Monthly gifts

> **Status:** Built
> **Agreed:** 2026-10-23 by Priya Nair
> **Roadmap:** Income we can plan on

## Problem

Supporters of the food bank give once and forget. The charity cannot plan purchases because income swings by half from month to month.

## Outcome

A supporter sets up a monthly gift once and it repeats until they stop it.

**Measure:** Monthly recurring income reaches £8,000 within three months of launch, from £0 today.

## Scope

**In:**

- Monthly card donations set up on the donate page.
- Cancelling from a receipt email.

**Out:**

- Weekly or annual schedules.
- Direct debit.

## Acceptance criteria

- **A1.** When a supporter chooses "Monthly", enters an amount of £2 or more and valid card details, and clicks "Donate", the card is charged that amount and the page shows "Thank you. Your next gift is on" followed by the date one month later.
- **A2.** When the amount is empty or under £2, the form shows "Enter an amount of £2 or more" and no charge is made.
- **A3.** When the card is declined, the page shows "Your card was declined. Try another card." and no monthly gift is created.
- **A4.** On the same day of each following month, the card is charged the same amount and the supporter receives a receipt email.
- **A5.** When the supporter clicks "Cancel monthly gift" in a receipt email and confirms, no further charges are made and they receive "Your monthly gift is cancelled."
- **A6.** The fundraising manager approves the wording of the thank-you page and the receipt email before launch.

## Proof

> Verified at `a8e2f40` on 2026-11-06 by a verifier that did not write the change.

- **A1. Proved.** On staging with the payment provider in test mode, chose "Monthly", entered £5 and the always-succeeds test card, and clicked "Donate" on 9 November. The provider's event log shows one charge of £5.00, and the page showed "Thank you. Your next gift is on 9 December 2026." Events in `proof/a1-a4-events.txt`.
- **A2. Proved.** Submitted the form with the amount empty and then with £1. Both times the form showed "Enter an amount of £2 or more", and the provider's event log shows no new charge for either attempt.
- **A3. Proved.** Used the test card that is always declined. The page showed "Your card was declined. Try another card." and the admin list of monthly gifts had no new entry.
- **A4. Proved.** Moved the provider's test clock forward one month, twice. A £5.00 charge appeared on 9 December and on 9 January, and the mail catcher received "Your receipt from Eastgate Food Bank" each time. Events in `proof/a1-a4-events.txt`.
- **A5. Proved.** Clicked "Cancel monthly gift" in the December receipt and confirmed. The mail catcher received "Your monthly gift is cancelled." Moving the test clock forward two more months produced no further charge.
- **A6. Needs a person.** Only the fundraising manager can approve the wording. Send her the thank-you page and the receipt email and record her answer.

### Try it yourself

1. Open the donate page on staging, choose "Monthly", and give £5 with the test card.

### Not covered

- Cards that need a bank approval step.
