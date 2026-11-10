# Low-stock alerts for parts

> **Status:** Draft
> **Agreed:** not yet
> **Roadmap:** Never out of brake pads

## Problem

Owners of independent bike shops find out a part has run out when a mechanic reaches for it. The repair waits two or three days for the reorder, and the customer often goes elsewhere.

## Outcome

An owner hears that a part is running low while there is still time to reorder it.

**Measure:** Stock-outs recorded in the app fall from an average of 9 per shop per month to 4 or fewer in the two months after launch.

## Scope

**In:**

- A low-stock threshold per part.
- An email to the owner when stock falls to the threshold.

**Out:**

- Automatic purchase orders.
- Supplier integrations.
- Forecasting demand.

## Acceptance criteria

- **A1.** When an owner sets the threshold on a part to a whole number from 0 to 999 and saves, the part page shows "Alert at N".
- **A2.** Owners should be alerted about low stock in a reasonable way that isn't annoying.
- **A3.** When a sale or stock adjustment brings a part's stock to its threshold or below, the owner receives one email naming the part, the stock left, and the threshold.
- **A4.** When the threshold field is left empty or holds anything other than a whole number from 0 to 999, the form shows "Enter a whole number from 0 to 999" and the old threshold stays.
- **A5.** When stock reaches the threshold, the app places a purchase order with the part's supplier automatically.
- **A6.** No second email is sent for the same part until its stock has gone back above the threshold.
