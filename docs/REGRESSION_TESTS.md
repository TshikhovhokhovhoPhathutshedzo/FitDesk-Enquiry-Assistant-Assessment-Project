# Regression tests

The staff-approval cases exercise the retained `process_enquiry` assessment helper. The default CLI's continuous chat behavior is covered by the chat-specific cases and no longer prompts staff to approve each reply.

| Test ID | Requirement | Input / precondition | Steps | Expected result | Actual result | Pass / Fail |
|---|---|---|---|---|---|---|
| RT-01 | FR-02, FR-04 | Valid enquiry for known package and Saturday slot | Mock Gemini response; staff says y | Draft contains R1,680 and Saturday availability statuses; log shows sent | Passed in final `pytest -v` run | Pass |
| RT-02 | FR-03 | Unknown package query | Mock Gemini response with a missing package; staff says y | Draft equals exact escalation phrase and escalation flag is true | Passed in final `pytest -v` run | Pass |
| RT-03 | FR-06 | Invalid JSON from AI | Mock Gemini to return broken JSON | Log status is failed_invalid_json and not sent | Passed in final `pytest -v` run | Pass |
| RT-04 | FR-06 | AI service failure or timeout | Mock Gemini service error and transport timeout | Log status is failed_ai_service and not sent | Passed in final `pytest -v` run | Pass |
| RT-05 | FR-04 | Staff says n | Mock valid AI response; staff says n | Log status is rejected_by_staff | Passed in final `pytest -v` run | Pass |
| RT-06 | FR-04 | Staff says y | Mock valid AI response; staff says y | Log status is sent | Passed in final `pytest -v` run | Pass |
| RT-07 | FR-02, FR-03 | Model names an unrequested known package | Ask about 25 sessions; mock model to return 5 sessions | Do not disclose R800; return escalation | Passed in final `pytest -v` run | Pass |
| RT-08 | FR-03, FR-07 | Known package plus unsupported Sunday classes | Mock known package and unsupported detail; staff says y | Include known price plus exact escalation phrase | Passed in final `pytest -v` run | Pass |
| RT-09 | FR-06 | Structured Gemini request | Mock SDK client; inspect request config | Request includes JSON schema and configured timeout | Passed in final `pytest -v` run | Pass |
| RT-10 | FR-03 | Saturday time not listed in approved data | Ask about Saturday 12:00; mock model | Never claim availability; use escalation phrase | Passed in final `pytest -v` run | Pass |
| RT-11 | FR-06 | JSON shape does not match Pydantic model | Mock invalid schema output | Log failed_invalid_json, never sent | Passed in final `pytest -v` run | Pass |
| RT-12 | FR-02 | Number-word package variation | Ask for “twelve sessions” | Return approved R1,680 price | Passed in final `pytest -v` run | Pass |
| RT-13 | FR-06 | Missing or corrupt data file | Remove or corrupt test data | Fail closed with failed_data | Passed in final `pytest -v` run | Pass |
| RT-14 | FR-05, FR-06 | Corrupt status log | Preload invalid JSON log | Do not crash, overwrite, or return sent | Passed in final `pytest -v` run | Pass |
| RT-15 | FR-04 | Model says approval is unnecessary | Return requires_human_approval=false | Still prompt staff; y is required for sent | Passed in final `pytest -v` run | Pass |
| RT-16 | FR-04 | Invalid staff responses | Enter yes, blank, garbage, then Y | Reprompt until exact y/n; only then proceed | Passed in final `pytest -v` run | Pass |
| RT-17 | FR-05 | Concurrent append requests | Run four local writers against one log | Preserve every status entry | Passed in final `pytest -v` run | Pass |
| RT-18 | FR-06 | No API key | Clear key and invoke client | Return a service failure, never sent | Passed in final `pytest -v` run | Pass |
| RT-19 | FR-06 | Empty AI output | Mock empty response | Return invalid-output failure, never sent | Passed in final `pytest -v` run | Pass |
| RT-20 | FR-06 | Gemini API error | Mock API 503 response | Return AI service failure, never sent | Passed in final `pytest -v` run | Pass |
| RT-21 | FR-02, FR-03 | Prompt injection asks for false pricing | Mock a package name absent from the message | Ignore model-suggested fact and escalate | Passed in final `pytest -v` run | Pass |
| RT-22 | FR-01 | CLI run without an argument | Enter a message, receive a reply, then type `done` | Continue the conversation until the exit command | Passed in final `pytest -q` run | Pass |
| RT-23 | FR-06 | Staff interrupts approval | Raise the approval cancellation signal | Log failed_cancelled, never sent | Passed in final `pytest -v` run | Pass |
| RT-24 | FR-05 | Unicode and long customer text | Send a Unicode message with 500 repeated words; reject it | Preserve the trimmed message in the rejected log entry | Passed in final `pytest -v` run | Pass |
| RT-25 | FR-02, FR-03 | Availability value is not Available or Full | Supply status “Maybe” in test data | Fail closed; do not convert it to full or available | Passed in final `pytest -v` run | Pass |
| RT-26 | FR-06 | Approved data contains invalid UTF-8 | Write invalid UTF-8 bytes to the data file | Log failed_data, never sent | Passed in final `pytest -v` run | Pass |
| RT-27 | FR-05, FR-06 | Status log contains invalid UTF-8 | Write invalid UTF-8 bytes to the log | Fail closed and preserve the original file | Passed in final `pytest -v` run | Pass |
| RT-29 | FR-08 | Gemini request success or failure | Mock an approved response and a Gemini service error | Log Gemini and configured model on both outcomes without the API key | Passed in final `pytest -v` run | Pass |
| RT-30 | FR-06 | Gemini output budget | Inspect the mocked Gemini request configuration | Cap model output at 256 tokens | Passed in final `pytest -v` run | Pass |
| RT-31 | FR-09 | Per-client request burst | Exceed one client's configured rolling-window limit | Record `rate_limited` and do not call Gemini | Covered by `tests/test_rate_limiter.py` and CLI integration test | Pass |
| RT-32 | FR-09, NFR-02 | Concurrent shared request burst | Submit concurrent requests from multiple clients | Never admit more than 30 requests in one rolling 60-second window | Covered by thread-pool rate-limiter test | Pass |
| RT-33 | FR-09 | Separate application processes (test shared cap: 20) | Submit requests concurrently from three processes using the same SQLite file | The configured shared cap is enforced across processes | Covered by subprocess rate-limiter test | Pass |
| RT-34 | NFR-02 | Rate-limit database failure | Make the configured SQLite database path unavailable | Fail closed with `failed_rate_limiter`; do not call Gemini | Covered by SQLite and CLI fail-closed tests | Pass |
| RT-35 | FR-10 | Gemini classification context | Inspect the mocked request prompt | Include the knowledge base and approved prices/availability; require scope classification in the structured schema | Passed in final `pytest -q` run | Pass |
| RT-36 | FR-13 | Legacy staff-reviewed enquiry | Mock an unrelated classification and approve the draft | Use the fixed FitDesk-only reply, retain staff approval, and log `is_fitdesk_related: false` | Passed in final `pytest -q` run | Pass |
| RT-37 | FR-10, FR-11 | Missing or corrupt knowledge base | Remove or corrupt the knowledge-base file | Fail closed with `failed_data`; never produce an approved/sent result | Passed in final `pytest -q` run | Pass |
| RT-38 | FR-02 | Greeting / small talk | Enter “how are you?” | Reply warmly without Gemini or staff approval | Passed in final `pytest -q` run | Pass |
| RT-39 | FR-08 | Booking request | Ask to book a listed Saturday time | Show approved schedule, state no booking was made, and direct customer to staff | Passed in final `pytest -q` run | Pass |
| RT-40 | FR-04 | Conversational follow-up | Ask a short follow-up referring to the previous package | Include recent history in Gemini context and use only customer-mentioned facts | Passed in final `pytest -q` run | Pass |
| RT-41 | FR-07, FR-10 | Automatic chatbot reply | Ask an off-topic question in chat mode | Return fixed scope reply directly and log `responded_in_chat` without implying an external send | Passed in final `pytest -q` run | Pass |

| RT-42 | FR-01 | Conversation lifecycle | Enter two messages followed by `done` | Keep the conversation open and pass earlier turns as context until exit | Passed in final `pytest -q` run | Pass |
| RT-43 | FR-02 | Greeting addressed to FitDesk | Enter `hi fitdesk` | Give the friendly greeting response without Gemini or owner-check escalation | Passed in final `pytest -q` run | Pass |
| RT-44 | FR-08 | Booking time without minutes | Ask to book for Saturday at 10, 10 am, or 10:00 | Report Saturday 10:00 as full only; don't list unrelated slots or claim a booking | Passed in final `pytest -q` run | Pass |
| RT-45 | FR-05, FR-08 | Combined booking, price, and availability request | Ask to book a single session Saturday at 10 and ask its price | Reply with R180, 10:00 full, and a clear no-booking disclosure | Passed in final `pytest -q` run | Pass |
| RT-46 | FR-08 | Gemini outage during clear booking enquiry | Ask to book a single session Saturday at 14:00 and ask its price; make Gemini unavailable | Use local data to reply R180 and state 14:00 is not listed; no Gemini call is required | Passed in final `pytest -q` run | Pass |
| RT-47 | FR-11, FR-12 | Gemini 503 failure logging | Make the Gemini client raise 503 | Log failed_ai_service with `ai_used: true`, provider, model, and error reason | Passed in final `pytest -q` run | Pass |

## Real pytest run
Fresh venv command: `.venv-validation\Scripts\python.exe -m pytest -q`
Latest offline run used mocked Gemini calls and made no network requests:
```
============================= 60 passed in 27.33s =============================
```
Historical provider experiments are summarized in [PROJECT_REPORT.md](./PROJECT_REPORT.md). The current application is Gemini-only.
