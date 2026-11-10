# Check a gift card balance online

> **Status:** Draft
> **Agreed:** not yet
> **Roadmap:** Fewer calls to stores

## Problem

Customers of our bookshop chain phone a store to ask how much is left on a gift card. Stores take about 220 of these calls a week, and each one pulls a bookseller off the shop floor for a few minutes.

## Outcome

A customer checks a gift card balance on the website without phoning a store.

**Measure:** Calls to stores about gift card balances fall from about 220 a week to under 50, comparing the four weeks before launch with the four weeks after.

## Scope

**In:**

- A balance check page for physical gift cards.

**Out:**

- Topping up a card.
- Digital gift cards.
- Moving a balance between cards.

## Acceptance criteria

- **A1.** When a customer enters a 16-digit card number and the 4-digit PIN from the back of the card and clicks "Check balance", the page shows the balance in pounds and pence and the card's expiry date.
- **A2.** When the number and PIN do not match a card, the page shows "We couldn't find a card with those details" and shows no balance.
- **A3.** When either field is empty or the wrong length, the form shows "Enter the 16-digit number and 4-digit PIN" and nothing is looked up.
- **A4.** After 5 failed attempts from one browser in 10 minutes, the form is locked for 15 minutes and shows "Too many attempts. Try again in 15 minutes."
- **A5.** The balance check never asks for a PIN, so a customer with only the card number can see the balance.
- **A6.** A customer can add £10, £20, or £50 to the card from the balance page.
