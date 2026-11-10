# Refunds without waiting for an agent

> **Status:** Draft
> **Agreed:** not yet
> **Roadmap:** Support load under control

## Problem

Support agents at our online furniture store approve every refund by hand. Customers wait about three days for an answer, and refund requests are a third of all support contacts.

## Outcome

A customer requests a refund from their order page, and an eligible order is refunded without an agent touching it.

**Measure:** The share of refund requests handled without an agent rises from 0% to at least 60% in the first six weeks.

## Scope

**In:**

- A refund request button on the order page for delivered orders.
- Automatic approval for eligible orders.

**Out:**

- Exchanges.
- Refunds for custom-made items.
- Partial refunds.

## Acceptance criteria

- **A1.** When a customer opens a delivered order, the page shows a "Request refund" button.
- **A2.** When the customer requests a refund within 30 days of delivery, the refund is approved automatically and the order shows "Refund approved".
- **A3.** Refund requests that look suspicious are handled appropriately.
- **A4.** When the refund is approved, the customer receives an email stating the amount and that it reaches their card in 5 to 7 working days.
- **A5.** When the customer requests a refund more than 14 days after delivery, the request is declined and the order shows "Refund window closed".
- **A6.** An order that has not been delivered shows no "Request refund" button.
