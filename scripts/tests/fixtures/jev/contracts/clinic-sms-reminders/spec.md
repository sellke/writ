# Text reminders before appointments

> **Status:** Draft
> **Agreed:** not yet
> **Roadmap:** Fewer empty slots

## Problem

Front-desk staff at physiotherapy clinics phone every patient the day before their appointment. It takes about an hour a day per clinic, and 11% of appointments are still missed because many patients do not pick up.

## Outcome

Patients get a text the day before and can confirm or cancel by replying. Front-desk staff stop making reminder calls.

**Measure:** The no-show rate across the two pilot clinics falls from 11% to 7% or lower over the eight weeks after launch.

## Scope

**In:**

- One SMS reminder 24 hours before an appointment.
- Confirming or cancelling by reply.

**Out:**

- Email reminders.
- Reminders for group classes.
- Rescheduling by text.

## Acceptance criteria

- **A1.** When an appointment is booked more than 24 hours ahead for a patient with a mobile number on file, the patient receives one SMS 24 hours before the start time, naming the clinic, the date, and the time.
- **A2.** When the patient replies "C", the appointment shows "Confirmed" on the day view within one minute.
- **A3.** When the patient replies "X", the appointment shows "Cancelled by patient", the slot becomes bookable again, and the patient receives "Your appointment is cancelled."
- **A4.** When the patient replies with anything other than "C" or "X", they receive "Reply C to confirm or X to cancel." and the appointment status does not change.
- **A5.** When the patient has no mobile number on file, no SMS is sent and the appointment shows a "No reminder: no mobile number" marker on the day view.
- **A6.** An appointment booked less than 24 hours ahead gets no reminder SMS.
