# FitDesk Enquiry Assistant SRS

## Business objective
- Help a Hermanus fitness studio respond to customer enquiries using approved pricing and Saturday slot data only.
- Keep staff in control of every outbound message and reject invented facts.

## Stakeholders
- Studio owner / staff
- Customer service team
- Assessment reviewers

## In / out of scope
- In scope: enquiry classification, data lookup, draft reply generation, staff approval, safe status logging, failure handling.
- Out of scope: automated bookings, payments, WhatsApp integration, real-time availability refresh.

## Functional requirements
- FR-01: The system must classify each customer message into a constrained intent: pricing, availability, pricing_and_availability, or other.
- FR-02: The system must read approved data from data/fitdesk_data.json and never invent missing values.
- FR-03: When no fact is available, the system must return the exact escalation phrase: "I'll check with the owner and come back to you."
- FR-04: Staff approval is always required before a message is logged as sent.
- FR-05: The status log must record sent, rejected_by_staff, failed_invalid_json, failed_ai_service, and similar states without losing prior entries.
- FR-06: The clerk must never record a sent status when the AI service fails, JSON is invalid, or the answer is unapproved.
- FR-07: Partial answers must combine known facts with the escalation phrase when a fact is missing, and the record must be flagged as escalation.
- FR-08: Each enquiry that attempts an AI request must log the selected provider and configured model name, without logging the API key.

## Non-functional requirements
- NFR-01 Security: .env holds the selected AI provider's API key, and secret scanning checks stop accidental commit leaks.
- NFR-02 Reliability: failed AI calls, malformed output, and timeouts fail closed and leave a non-sent log entry.
- NFR-03 Cost and simplicity: the project keeps a single data source and deterministic templates to reduce model cost and keep behaviour explainable.

## Data inputs / outputs
- Input: customer message, data/fitdesk_data.json, .env configuration, staff approval response.
- Output: deterministic draft message, status_log.json entry, CLI display of the draft and approval prompt.

## Approval and failure rules
- If staff says n, status is rejected_by_staff and no sent log is written.
- If facts are missing and staff approves the escalation message, the log may record sent with escalation: true.
- If the AI response is malformed or the AI service fails, the system logs a failed state and never marks the message as sent.

## Acceptance criteria
- Given a question about a known package, when the data exists, then the system replies with the approved price and no invented value.
- Given a question about a package not in the data file, when the package is unknown, then the system uses the exact escalation phrase instead of inventing a price.
- Given a question about Saturday availability, when the time slot is present, then the result reflects the approved status.
- Given an invalid response from any configured AI provider, when JSON validation fails, then the status is not sent.
- Given staff input n, when approval is refused, then the status is rejected_by_staff.
- Given a valid draft and staff input y, when approval is accepted, then the status is sent.

## Ambiguities and assumptions
- What is unclear: whether enquiries about other weekdays or class schedules should be answered. What I'd ask the owner: “Should the assistant handle class schedules beyond Saturday availability?” [ASSUMPTION] Until data is added, those questions escalate to the owner.
- What is unclear: whether package names have customer-facing aliases. What I'd ask the owner: “Are there approved alternative names for single, 5-session, and 12-session packages?” [ASSUMPTION] Only names and values in the data file are treated as approved.
- What is unclear: what to say when a request mixes supported and unsupported facts. What I'd ask the owner: “Should we include the known part and escalate the unknown part?” [ASSUMPTION] The assistant includes known facts and adds the exact escalation phrase for missing facts.
