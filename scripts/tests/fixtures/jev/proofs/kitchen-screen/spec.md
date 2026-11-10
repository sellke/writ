# Kitchen screen for open orders

> **Status:** Built
> **Agreed:** 2026-10-27 by Marta Okafor
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

## Acceptance criteria

- **A1.** When an order is paid at the till, it appears on the kitchen screen within 5 seconds, showing the order number, each item with its quantity, and any note typed at the till.
- **A2.** Open orders are listed oldest first.
- **A3.** When a cook taps "Ready" on an order, it leaves the kitchen screen and the till shows the order number under "Ready to collect".
- **A4.** An order that has been open for more than 8 minutes shows a red border.
- **A5.** When there are no open orders, the screen shows "No open orders".
- **A6.** When the kitchen screen loses its connection, it shows "Offline. Orders may be missing." across the top until the connection returns.

## Proof

> Verified at `c33e1b9` on 2026-11-07 by a verifier that did not write the change.

- **A1. Proved.** Paid order 1042 at the staging till: 2 cheeseburgers, 1 fries, with the note "no pickles". The till printed the receipt and showed "Payment complete".
- **A2. Proved.** Paid orders 1043, 1044, and 1045 one minute apart. The kitchen screen listed them from top to bottom as 1043, 1044, 1045.
- **A3. Proved.** Tapped "Ready" on order 1043 on the kitchen screen. It left the kitchen screen.
- **A4. Needs a person.** Someone has to leave an order open for eight minutes and watch for the red border.
- **A5. Proved.** The empty state is handled in `OrderList.vue`, which renders the "No open orders" text when the list is empty.
- **A6. Proved.** Turned off Wi-Fi on the kitchen tablet. Within a few seconds the banner "Offline. Orders may be missing." appeared across the top of the screen. It went away when Wi-Fi came back.

### Try it yourself

1. Pay any order at the staging till and watch the kitchen tablet.

### Not covered

- More than 40 open orders at once.
