# Kitchen screen for open orders

> **Status:** Draft
> **Agreed:** not yet
> **Roadmap:** Right order, first time

## Problem

Cooks in our burger restaurants work from paper tickets. In a rush, tickets get lost or read out of order, and about 1 order in 30 has to be remade.

## Outcome

Cooks see every open order on one screen, in the order it arrived.

**Measure:** Remade orders fall from 1 in 30 to 1 in 100 or fewer across the three pilot kitchens in the first month.

## Scope

**In:**

- A kitchen screen that lists open orders.
- Marking an order ready.

**Out:**

- Printing tickets.
- Orders from delivery apps.
- Recipe or allergen information.

## Acceptance criteria

- **A1.** When an order is paid at the till, it appears on the kitchen screen within 5 seconds, showing the order number, each item with its quantity, and any note typed at the till.
- **A2.** Open orders are listed oldest first.
- **A3.** When a cook taps "Ready" on an order, it leaves the kitchen screen and the till shows the order number under "Ready to collect".
- **A4.** An order that has been open for more than 8 minutes shows a red border.
- **A5.** When there are no open orders, the screen shows "No open orders".
- **A6.** When the kitchen screen loses its connection, it shows "Offline. Orders may be missing." across the top until the connection returns.
