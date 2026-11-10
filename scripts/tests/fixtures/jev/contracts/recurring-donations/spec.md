# Monthly gifts

> **Status:** Draft
> **Agreed:** not yet
> **Roadmap:** Income we can plan on

## Problem

Supporters of the food bank give once and forget. The fundraising team emails a reminder every month, about one in twenty gives again, and the charity cannot plan purchases because income swings by half from month to month.

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
- Gift Aid declarations.

## Acceptance criteria

- **A1.** When a supporter chooses "Monthly", enters an amount of £2 or more and valid card details, and clicks "Donate", the card is charged that amount and the page shows "Thank you. Your next gift is on" followed by the date one month later.
- **A2.** When the amount is empty or under £2, the form shows "Enter an amount of £2 or more" and no charge is made.
- **A3.** When the card is declined, the page shows "Your card was declined. Try another card." and no monthly gift is created.
- **A4.** On the same day of each following month, the card is charged the same amount and the supporter receives a receipt email.
- **A5.** When a monthly charge fails, the supporter receives "We couldn't take your gift this month" with a link to update their card, and the charge is retried once after 3 days.
- **A6.** When the supporter clicks "Cancel monthly gift" in a receipt email and confirms, no further charges are made and they receive "Your monthly gift is cancelled."
