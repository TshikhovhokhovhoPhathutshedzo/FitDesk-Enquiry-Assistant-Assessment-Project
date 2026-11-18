# Regression tests

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
| RT-22 | FR-04 | CLI run without an argument | Enter an enquiry interactively and approve | Process the enquiry through the same approval gate | Passed in final `pytest -v` run | Pass |
| RT-23 | FR-06 | Staff interrupts approval | Raise the approval cancellation signal | Log failed_cancelled, never sent | Passed in final `pytest -v` run | Pass |
| RT-24 | FR-05 | Unicode and long customer text | Send a Unicode message with 500 repeated words; reject it | Preserve the trimmed message in the rejected log entry | Passed in final `pytest -v` run | Pass |
| RT-25 | FR-02, FR-03 | Availability value is not Available or Full | Supply status “Maybe” in test data | Fail closed; do not convert it to full or available | Passed in final `pytest -v` run | Pass |
| RT-26 | FR-06 | Approved data contains invalid UTF-8 | Write invalid UTF-8 bytes to the data file | Log failed_data, never sent | Passed in final `pytest -v` run | Pass |
| RT-27 | FR-05, FR-06 | Status log contains invalid UTF-8 | Write invalid UTF-8 bytes to the log | Fail closed and preserve the original file | Passed in final `pytest -v` run | Pass |
| RT-28 | FR-06 | Groq chat-completions provider | Mock Groq JSON-mode response and service errors | Validate the request, parse a valid response, and fail closed on errors | Passed in final `pytest -v` run | Pass |
| RT-29 | FR-08 | AI request success or failure | Mock an approved response and an OpenRouter HTTP 402 | Log the provider and configured model for both outcomes without the API key | Passed in final `pytest -v` run | Pass |
| RT-30 | FR-08 | Provider/model metadata in status log | Run an OpenRouter service failure and an approved Groq enquiry | Record the selected provider and configured model on both outcomes; do not record credentials | Passed in final `pytest -v` run | Pass |

## Real pytest run
Fresh venv command: `.venv-validation\Scripts\python.exe -m pytest -v`
Latest offline run used mocked AI providers and made no network requests:
```
============================= 60 passed in 6.56s =============================
```
Live Groq check: the application received a valid structured classification, looked up the approved price and availability, and displayed a draft. Staff rejected the draft, so it was recorded as not sent.
