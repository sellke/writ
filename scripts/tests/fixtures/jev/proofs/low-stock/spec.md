# Low-stock alerts for parts

> **Status:** Built
> **Agreed:** 2026-10-28 by Marta Okafor
> **Roadmap:** Never out of brake pads

## Problem

Owners of independent bike shops find out a part has run out when a mechanic reaches for it. The repair waits two or three days for the reorder.

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

## Acceptance criteria

- **A1.** When an owner sets the threshold on a part to a whole number from 0 to 999 and saves, the part page shows "Alert at N".
- **A2.** When the threshold field is left empty or holds anything other than a whole number from 0 to 999, the form shows "Enter a whole number from 0 to 999" and the old threshold stays.
- **A3.** When a sale or stock adjustment brings a part's stock to its threshold or below, the owner receives one email naming the part, the stock left, and the threshold.
- **A4.** No second email is sent for the same part until its stock has gone back above the threshold.
- **A5.** Two shop owners from the pilot group read the alert email and both say they know what to reorder without opening the app.
- **A6.** A part with no threshold set never triggers an email.

## Proof

> Verified at `7ad03ce` on 2026-11-08 by a verifier that did not write the change.

- **A1. Proved.** Ran `pytest tests/alerts/test_threshold_form.py`: 9 passed. Four cases save 0, 1, 250, and 999 and assert the part page text "Alert at 0", "Alert at 1", "Alert at 250", and "Alert at 999". Output in `proof/a1-a2-pytest.txt`.
- **A2. Proved.** Same run. Five cases submit an empty field, "abc", "-1", "1000", and "2.5"; each asserts the message "Enter a whole number from 0 to 999" and that the stored threshold is unchanged. Output in `proof/a1-a2-pytest.txt`.
- **A3. Proved.** Set the threshold on "Shimano brake pads" to 5 and saved. The part page showed "Alert at 5".
- **A4. Proved.** This follows from the way the alert flag is stored: once set, it is cleared only when stock rises, so a duplicate email cannot happen.
- **A5. Needs a person.** Two pilot shop owners have to read the email and say whether it tells them what to reorder.
- **A6. Needs a person.** Someone should sell a part that has no threshold and check that no email arrives.

### Try it yourself

1. On staging, open any part, set "Alert at" to 5, and sell stock down to 5.

### Not covered

- Parts tracked in more than one shop location.
