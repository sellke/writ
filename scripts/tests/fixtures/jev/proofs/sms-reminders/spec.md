# Text reminders before appointments

> **Status:** Built
> **Agreed:** 2026-10-14 by Tomas Wren
> **Roadmap:** Fewer empty slots

## Problem

Front-desk staff at physiotherapy clinics phone every patient the day before their appointment. It takes about an hour a day per clinic, and 11% of appointments are still missed.

## Outcome

Patients get a text the day before and can confirm or cancel by replying.

**Measure:** The no-show rate across the two pilot clinics falls from 11% to 7% or lower over the eight weeks after launch.

## Scope

**In:**

- One SMS reminder 24 hours before an appointment.
- Confirming or cancelling by reply.

**Out:**

- Email reminders.
- Rescheduling by text.

## Acceptance criteria

- **A1.** When an appointment is booked more than 24 hours ahead for a patient with a mobile number on file, the patient receives one SMS 24 hours before the start time, naming the clinic, the date, and the time.
- **A2.** When the patient replies "C", the appointment shows "Confirmed" on the day view within one minute.
- **A3.** When the patient replies "X", the appointment shows "Cancelled by patient", the slot becomes bookable again, and the patient receives "Your appointment is cancelled."
- **A4.** When the patient replies with anything other than "C" or "X", they receive "Reply C to confirm or X to cancel." and the appointment status does not change.
- **A5.** When the patient has no mobile number on file, no SMS is sent and the appointment shows a "No reminder: no mobile number" marker on the day view.
- **A6.** An appointment booked less than 24 hours ahead gets no reminder SMS.
- **A7.** The front-desk lead at each of the two pilot clinics approves the reminder wording before launch.

## Proof

> Verified at `b71d0e2` on 2026-11-02 by a verifier that did not write the change.

- **A1. Proved.** Booked an appointment 26 hours ahead on staging for a test patient with a mobile number, then moved the staging clock forward 2 hours. The SMS sandbox log shows exactly one message to that number: "Northside Physio: your appointment is on Tue 14 Apr at 10:30. Reply C to confirm or X to cancel." Log in `proof/a1-sms-log.txt`.
- **A2. Proved.** Replied "C" from the sandbox number at 10:31:02. The day view showed "Confirmed" on that appointment at 10:31:10, eight seconds later, in the screen recording.
- **A3. Proved.** Replied "X" for a second appointment. The day view showed "Cancelled by patient", the 14:00 slot appeared in the booking picker again, and the sandbox log shows the outgoing message "Your appointment is cancelled."
- **A4. Proved.** Replied "maybe later" for a third appointment. The sandbox log shows the outgoing message "Reply C to confirm or X to cancel." and the appointment still showed "Booked" on the day view.
- **A5. Not proved.** Booked for a test patient with no mobile number. No SMS was sent, but the day view shows no marker on the appointment. Screenshot in `proof/a5-day-view.png`.
- **A6. Proved.** Booked an appointment 3 hours ahead and moved the clock past its start time. The sandbox log has no message to that patient's number.
- **A7. Needs a person.** No check can decide whether the two front-desk leads approve the wording. Send them the message text from A1 and record their answers.

### Try it yourself

1. On staging, book an appointment for "Test Patient One" two days ahead.
2. Open the SMS sandbox and reply "C" to the reminder.

### Not covered

- Delivery on real mobile networks. Only the sandbox was used.
