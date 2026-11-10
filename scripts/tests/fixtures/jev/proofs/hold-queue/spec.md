# Place a hold from the catalogue

> **Status:** Built
> **Agreed:** 2026-10-15 by Tomas Wren
> **Roadmap:** Branch staff off the phone

## Problem

Members of the public library phone their branch to reserve a book that is out on loan. Branches take about 300 of these calls a week.

## Outcome

A member places a hold online and sees their place in the queue.

**Measure:** Phone reservations fall from about 300 a week to under 100 within two months of launch, counted from the branch call log.

## Scope

**In:**

- Placing and cancelling holds on physical books from the online catalogue.

**Out:**

- E-books and audiobooks.
- Fines.

## Acceptance criteria

- **A1.** When a signed-in member clicks "Place hold" on a book with no available copy, the page shows "Hold placed. You are number N in the queue", where N is one more than the number of earlier holds on that book.
- **A2.** When a copy is returned, the first member in the queue receives an email saying the book is ready at their chosen branch and will be kept for 7 days.
- **A3.** When the member does not collect within 7 days, the hold is cancelled, the member receives "Your hold has expired", and the next member in the queue is notified.
- **A4.** When a member with 10 active holds clicks "Place hold", the page shows "You have reached the limit of 10 holds" and no hold is placed.
- **A5.** When a member clicks "Cancel hold" and confirms, the hold is removed and every later member in the queue moves up one place.
- **A6.** A visitor who is not signed in sees "Sign in to place a hold" instead of the "Place hold" button.

## Proof

> Verified at `5f0c7d3` on 2026-11-04 by a verifier that did not write the change.

- **A1. Proved.** Seeded two holds on "The Salt Path", signed in as a third member, and clicked "Place hold". The page showed "Hold placed. You are number 3 in the queue".
- **A2. Proved.** Checked a copy of "The Salt Path" back in at the staging desk. The mail catcher received a message to the first member in the queue: "The Salt Path is ready for you at Central Library. We will keep it for 7 days." Captured in `proof/a2-ready-mail.txt`.
- **A3. Not proved.** Moved the staging clock forward 8 days. The first member's hold was cancelled and they received "Your hold has expired", but the second member received no email.
- **A4. Proved.** Ran `pytest tests/holds/test_limit.py`: 3 passed. One case seeds 10 active holds, posts an eleventh, and asserts the page text "You have reached the limit of 10 holds" and that the member still has 10 holds. Output in `proof/a4-pytest.txt`.
- **A5. Proved.** With three members queued, signed in as the first and clicked "Cancel hold", then confirmed. The hold left their account page. The second member's page then showed "You are number 1 in the queue" and the third member's showed "You are number 2 in the queue".
- **A6. Proved.** Opened the book page in a private window without signing in. The page showed "Sign in to place a hold" and no "Place hold" button.

### Try it yourself

1. Sign in to staging as `member3@example.test` and open "The Salt Path".

### Not covered

- Books with copies at more than one branch.
