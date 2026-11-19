# FitDesk Enquiry Assistant SRS

## Business objective
- Provide an interactive terminal chatbot for customers to ask FitDesk questions.
- Answer package-price and Saturday-availability questions from approved local data.
- Keep chat behavior clear about the prototype's lack of booking and messaging integrations.

## Stakeholders
- FitDesk customers
- Studio owner / staff
- Assessment reviewers

## In / out of scope
- In scope: continuous terminal conversation, Gemini-assisted scope/intent classification, recent-turn context, approved data lookup, deterministic replies, off-topic handling, rate limiting, and local audit logging.
- Out of scope: public web or mobile access, WhatsApp/email integration, real bookings, payments, live calendar synchronization, and other weekdays or service details without approved data.

## Functional requirements
- FR-01: The chatbot must remain available for multiple customer messages until the customer types `done`, `exit`, or `quit`, or interrupts with Ctrl+C.
- FR-02: Simple greetings and small talk, including greetings addressed to FitDesk, must receive a friendly FitDesk response without being treated as an off-topic request.
- FR-03: Messages not answered by deterministic greeting, package-price, or Saturday-availability rules must be classified into the constrained intent set and FitDesk scope using Gemini structured output.
- FR-04: When Gemini is used, its prompt must include the knowledge base, approved studio data, and no more than the 10 most recent conversation turns.
- FR-05: Requested package prices and Saturday availability must be verified against `data/fitdesk_data.json`; the model must not be the source of those facts.
- FR-06: Unsupported package prices and other unknown FitDesk facts must use the exact phrase: "I'll check with the owner and come back to you." An unlisted Saturday time must instead be explicitly identified as unlisted, never available or full.
- FR-07: Off-topic messages must receive the fixed FitDesk-only reply from the knowledge base.
- FR-08: The chatbot must not create, reserve, or confirm appointments. Recognized package-price and Saturday-availability requests, including supported follow-ups, must be answerable from local approved data without relying on Gemini. It may show the relevant approved sample Saturday time and status when the customer specifies a numeric time (for example, "at 10"), clearly labeled as not live; an unlisted time must be reported as unlisted, not available or full. Unsupported weekdays must not be answered with Saturday data. Direct customers to FitDesk staff to arrange a booking.
- FR-09: Each client must be limited to 10 requests and the application to 30 requests in a rolling 60-second window; blocked requests must not call Gemini.
- FR-10: Chat replies and failures must be recorded with a conversation ID and status. `responded_in_chat` must mean only that text was displayed in the local terminal, not sent externally.
- FR-11: AI attempts must record the Gemini provider and configured model without recording the API key.
- FR-12: Missing/corrupt knowledge or business data, invalid AI output, AI errors, and rate-limiter failures must fail closed with an explicit error and must never claim a booking was made.
- FR-13: The separate `process_enquiry` assessment helper may retain its staff approval workflow; the main terminal chatbot must not require staff approval for each reply.

## Non-functional requirements
- NFR-01 Security: Keep the Gemini API key only in the Git-ignored `.env`; `.env.example` must not contain a key.
- NFR-02 Reliability: Validation, rate limiting, and local logging must fail closed. SQLite coordinates rate checks only for processes on the same machine using the same file.
- NFR-03 Grounding: Use deterministic templates and local approved facts for customer-facing claims.
- NFR-04 Prototype boundary: The terminal chat is local-only, uses sample availability, and is not a deployed public production service.

## Data inputs / outputs
- Input: customer chat messages, recent conversation turns, knowledge base, approved studio JSON data, Gemini configuration, and client ID.
- Output: a terminal reply, local `status_log.json` record, and explicit error text when processing fails.

## Acceptance criteria
- Given "how are you?" or "hi FitDesk", the chatbot responds warmly and keeps the conversation open without calling Gemini.
- Given successive customer messages, the chatbot continues until an exit command and includes recent turns in non-greeting Gemini requests.
- Given a known package or Saturday slot, the reply uses only the approved local value.
- Given a booking request for Saturday at 10, the chatbot reports the approved 10:00 status only, does not claim to make a booking, and labels the schedule as non-live.
- Given a request to book a single session Saturday at 10 and ask its price, the chatbot reports R180 and the 10:00 status (full), and clearly states no booking was made.
- Given a Gemini service outage and a clear Saturday session booking request, the chatbot still returns the approved package price and slot status without claiming to have contacted a live calendar.
- Given “book for Saturday,” followed by “book for 10:00” and “what other time is available?”, the chatbot lists only other approved available Saturday times, excluding 10:00.
- Given a price follow-up with no known package, the chatbot lists the approved package prices; a supported short typo such as “how muc are bookings?” must still get the menu.
- Given an explicitly unrelated price question, the chatbot must apply FitDesk scope classification instead of showing the package menu.
- Given an unsupported package price, the chatbot must use the exact owner-check escalation phrase and must not invent a price.
- Given an unrelated request, the chatbot returns the fixed FitDesk-only reply.
- Given an invalid model response, service error, corrupt data, or request-limit failure, the chatbot logs a failure and does not claim success.
- Given a successfully displayed response, the log status is `responded_in_chat`; it must not imply an external message was sent.

## Separate assessment workflow
`process_enquiry` retains the staff-reviewed draft flow used by the assessment regression tests. The default `python -m fitdesk` command runs the continuous terminal chatbot instead.
