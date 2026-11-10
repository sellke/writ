# Export a month of invoices as CSV

> **Status:** Built
> **Agreed:** 2026-10-20 by Priya Nair
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

## Acceptance criteria

- **A1.** When a finance lead selects a month and clicks "Export CSV", the browser downloads a file named `invoices-YYYY-MM.csv` for that month.
- **A2.** The file has a header row and then one row per invoice dated in that month, with the columns invoice number, client name, issue date, due date, net amount, tax amount, total, and status, in that order.
- **A3.** Amounts in the file use a dot as the decimal separator and two decimal places, with no currency symbol or thousands separator.
- **A4.** When the selected month has no invoices, the page shows "No invoices in this month" and no file is downloaded.
- **A5.** A user without the Finance role does not see the "Export CSV" button, and a direct request to the export address returns "403 Forbidden".
- **A6.** In a hallway test, at least four of five finance leads find the "Export CSV" button without being told where it is.

## Decisions

## Proof

> Verified at `4c1e9ab` on 2026-11-03 by a verifier that did not write the change.

- **A1. Proved.** Signed in as a Finance user on the preview build, selected March 2026, and clicked "Export CSV". The browser downloaded a file named `invoices-2026-03.csv`. Screenshot of the download bar in `proof/a1-download.png`.
- **A2. Proved.** Opened the downloaded file. The first row is `invoice_number,client_name,issue_date,due_date,net_amount,tax_amount,total,status`, followed by 6 rows. The seeded March data has 6 invoices and the invoice numbers match. File saved as `proof/a2-invoices-2026-03.csv`.
- **A3. Proved.** Ran `pytest tests/export/test_amount_format.py`: 6 passed. The cases cover 1234.5 written as `1234.50`, 0 as `0.00`, and 1000000 as `1000000.00`, and check that no row holds a currency symbol or a comma inside an amount. Output in `proof/a3-pytest.txt`.
- **A4. Proved.** Selected February 2031, which has no seeded invoices, and clicked "Export CSV". The page showed "No invoices in this month". The browser's network log shows no request to `/invoices/export` and nothing was downloaded.
- **A5. Proved.** Signed in as a user with the Sales role: the invoices list has no "Export CSV" button. A request to `/invoices/export?month=2026-03` with that user's session returned `403 Forbidden`. Transcript in `proof/a5-curl.txt`.
- **A6. Needs a person.** Whether finance leads find the button unaided can only be seen by watching them. Run the hallway test with five finance leads and record how many find it.

### Try it yourself

1. Sign in to the preview build as `finance@example.test`.
2. Open Invoices, pick March 2026, and click "Export CSV".

### Not covered

- Import into Xero and QuickBooks was not tried.
