# Limit password-reset emails

> **Status:** Draft
> **Agreed:** not yet
> **Roadmap:** Account safety

## Problem

Someone can submit our password-reset form for a customer's address hundreds of times. Last month four customers of the banking app each received more than 200 reset emails in an hour and phoned support believing they had been hacked.

## Outcome

A customer receives at most a few reset emails, however many times the form is submitted for their address.

**Measure:** Customers have a better and safer reset experience.

## Scope

**In:**

- A limit on reset emails per account.

**Out:**

- CAPTCHA.
- Changes to the login form.
- Reset by SMS.

## Acceptance criteria

- **A1.** When a reset is requested for an email address that has an account, a reset email is sent and the page shows "If that address has an account, we've sent a link."
- **A2.** When a reset is requested for an email address with no account, no email is sent and the page shows the same message as in A1.
- **A3.** No more than 3 reset emails are sent to one account in any 60-minute period.
- **A4.** Every reset request for an account sends a new reset email, so the customer always has a fresh link.
- **A5.** When the limit is reached, further requests send no email and the page still shows the same message as in A1.
- **A6.** A reset link stops working 30 minutes after it was sent; opening it later shows "This link has expired. Request a new one."
- **A7.** When the form is submitted with the address field empty, it shows "Enter your email address" and no request is made.
