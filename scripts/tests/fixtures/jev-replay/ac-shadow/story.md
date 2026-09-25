# Story 9: Greeting Endpoint (synthetic ac-shadow fixture)

> **Status:** In Progress

## User Story

**As a** visitor
**I want to** get a greeting by name
**So that** the page feels personal

## Acceptance Criteria

> **AC IDs assigned through:** AC-9.3

- [ ] Given a name `Ada`, when `greet("Ada")` runs, then it returns `Hello, Ada!` `[AC-9.1]`
- [ ] Given an empty name, when `greet("")` runs, then it returns `Hello, stranger!` `[AC-9.2]`
- [ ] Given a name longer than 64 characters, when `greet` runs, then it raises `ValueError` `[AC-9.3]`

## Implementation Tasks

- [ ] 9.1 Implement `greet` `[AC-9.1, AC-9.2, AC-9.3]`
