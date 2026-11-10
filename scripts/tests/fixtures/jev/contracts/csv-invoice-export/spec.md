# Export a month of invoices as CSV

> **Status:** Draft
> **Agreed:** not yet
> **Roadmap:** Month-end close without retyping

## Problem

Finance leads at small agencies retype invoice rows from the app into their accounting tool at every month-end. It takes each of them about two hours, and the retyped totals are wrong often enough that three customers raised it in renewal calls.

## Outcome

A finance lead downloads one file for the month and imports it into their accounting tool without editing it.

**Measure:** Support tickets tagged "invoice export" fall from about 14 a month to under 3, checked two months after release.

## Scope

**In:**

- An "Export CSV" button on the invoices list, for one calendar month at a time.

**Out:**

- PDF or Excel export.
- Scheduled or emailed exports.
- Exporting more than one month in a single file.

## Acceptance criteria

- **A1.** When a finance lead selects a month and clicks "Export CSV", the browser downloads a file named `invoices-YYYY-MM.csv` for that month.
- **A2.** The file has a header row and then one row per invoice dated in that month, with the columns invoice number, client name, issue date, due date, net amount, tax amount, total, and status, in that order.
- **A3.** Amounts in the file use a dot as the decimal separator and two decimal places, with no currency symbol or thousands separator.
- **A4.** When the selected month has no invoices, the page shows "No invoices in this month" and no file is downloaded.
- **A5.** A user without the Finance role does not see the "Export CSV" button, and a direct request to the export address returns "403 Forbidden".

## Notes for the builder

The accounting tools our customers named are Xero and QuickBooks. Both import the column order above.
