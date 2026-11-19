# RAPLH log

### [GENUINE] 2026-11-19 — Keep clear booking answers working during Gemini outage
- Task/expectation: Address the logged Gemini HTTP 503 high-demand error for a customer asking the Saturday 14:00 slot status and single-session price.
- Files changed: src/fitdesk/cli.py, src/fitdesk/lookup.py, tests/test_cli.py, README.md, docs/SRS.md, docs/REGRESSION_TESTS.md, docs/PROJECT_REPORT.md.
- What was corrected: Clearly FitDesk-related Saturday booking questions now use the approved local package and availability data without waiting for Gemini. A 14:00 time absent from the sample schedule is reported as unlisted, never available. Gemini failure logs now mark `ai_used: true` when classification raises an error, and retain provider/model metadata.
- Test run and result: `.venv\Scripts\python.exe -m pytest -q` completed with `60 passed in 27.33s`; `git diff --check` succeeded. The exact outage/booking scenario and Gemini 503 log regression passed.
- Approval decision: No live Gemini call was made.

### [GENUINE] 2026-11-19 — Answer combined booking, price, and availability questions
- Task/expectation: Fix the user's example where a request for a single Saturday session at 10 asking both availability and price returned only the booking disclaimer and slot status.
- Files changed: src/fitdesk/cli.py, src/fitdesk/lookup.py, tests/test_cli.py, README.md, docs/SRS.md, docs/REGRESSION_TESTS.md, docs/PROJECT_REPORT.md.
- What was corrected: The booking path now also looks up requested package prices. Customer wording such as "a session" resolves to the approved Single session package (R180); the response includes that price, only the requested Saturday slot (10:00, Full), and a clear statement that no booking is placed and the sample schedule is not live.
- Test run and result: `.venv\Scripts\python.exe -m pytest -q` completed with `58 passed in 33.88s`; `git diff --check` succeeded.
- Approval decision: Added the exact reported combined query as a regression test; targeted and full tests passed. No live Gemini request was made.

### [GENUINE] 2026-11-19 — Fix greeting and booking-time handling
- Task/expectation: Correct two chatbot behaviors shown by the user: "hi fitdesk" should receive a greeting instead of an owner-check fallback, and a booking request for Saturday at 10 should report the requested slot rather than all slots.
- Files changed: src/fitdesk/cli.py, tests/test_cli.py, docs/SRS.md, docs/REGRESSION_TESTS.md, docs/PROJECT_REPORT.md.
- What was corrected: Greeting detection now accepts a FitDesk salutation and small-talk follow-up. Booking time parsing accepts numeric hour, am/pm, and HH:MM forms, normalizes them to the approved schedule, and limits the reply to the requested slot. Unlisted hours are not represented as available.
- Test run and result: `.venv\Scripts\python.exe -m pytest -q` completed with `57 passed in 21.50s`; `git diff --check` succeeded.
- Approval decision: The two reported cases were first added as regression tests and confirmed to fail, then passed after the fixes. No live Gemini request was made.

### [GENUINE] 2026-11-19 — Add continuous terminal customer chat
- Task/expectation: Move the local CLI from a one-enquiry staff approval demo to a continuous customer-chat prototype, remain terminal-only, keep the conversation open until the customer exits, and do not make bookings.
- Prompt summary: “Let customers communicate with the chatbot; continue the conversation until they are done and keep bookings in order.” Clarification: terminal only, local-first, answer availability only; bookings are not to be submitted.
- Files changed: src/fitdesk/cli.py, src/fitdesk/ai_client.py, src/fitdesk/gemini_client.py, src/fitdesk/knowledge_base.py, src/fitdesk/ui.py, data/knowledge_base.json, tests/test_cli.py, README.md, docs/SRS.md, docs/REGRESSION_TESTS.md, docs/PROJECT_REPORT.md.
- What was corrected: Default CLI now provides a multi-turn chat with `done`/`exit`/`quit` commands, retains up to 10 recent turns in Gemini context, responds to simple greetings without a model call, and displays replies without the staff approval prompt. Booking requests show the approved sample Saturday schedule, clearly state that no live booking is made, and refer customers to staff.
- Test run and result: `.venv\Scripts\python.exe -m pytest -q` completed with `53 passed in 21.76s`; `git diff --check` succeeded.
- Scope limitation: This is still a local terminal prototype, not a deployed public production service. Availability is sample data and there is no calendar, messaging, or booking integration. The separate `process_enquiry` approval helper remains for the assessment regression workflow.
- Approval decision: Local implementation and offline tests verified. No live Gemini request was made for this change.

### [GENUINE] 2026-11-19 — Share rate limits across concurrent CLI processes
- Task/expectation: During the assignment compliance review, make the three-client rate limit effective across separate application processes instead of only within one process.
- Prompt summary: “Review the project against the assessment brief, close the gaps, then commit everything and push to the renamed repository.”
- Files changed: src/fitdesk/rate_limiter.py, src/fitdesk/config.py, src/fitdesk/cli.py, .env.example, .gitignore, tests/conftest.py, tests/test_rate_limiter.py, README.md, docs/SRS.md, docs/PROJECT_REPORT.md, docs/REGRESSION_TESTS.md.
- What was corrected: Replaced the process-local counter with a transaction-serialized SQLite store; added configurable per-client IDs and explicit fail-closed handling if the store cannot be checked.
- Test run and result: `.venv-validation\Scripts\python.exe -m pytest -q` completed with `45 passed in 14.41s`; `compileall` and `git diff --check` succeeded.
- Approval decision: Reviewed the tests and project diff; ready for commit and push. The author supplied 3.5 hours and answers to questions 2–4, which were copied verbatim. Question 1 was counted at 74 words; the author was asked to extend it to the required 80–150 words, but no additional text was supplied, so its placeholder remains rather than inventing a personal answer.

### [GENUINE] 2026-11-19 — Add thread-safe enquiry rate limiting
- Task/expectation: Add a separate, practical rate limiter for a small three-client workload and commit and push the verified changes.
- Prompt summary: “Place a proper rate limiter for the chatbot on a different file, set a realistic limit for three simultaneous users, then commit and push.”
- Files changed: src/fitdesk/rate_limiter.py, src/fitdesk/cli.py, tests/conftest.py, tests/test_cli.py, tests/test_rate_limiter.py, README.md, docs/REGRESSION_TESTS.md.
- Rate policy: 10 enquiries per client per rolling 60 seconds, and 30 total enquiries per rolling 60 seconds. Requests over either limit are logged as `rate_limited` without invoking Gemini.
- Scope limitation: The limiter is thread-safe and in-memory within one Python process. The CLI currently uses the shared `local` client identity; an integration can pass an authenticated client ID to `process_enquiry`. Separate processes/hosts need shared storage for coordinated limits.
- Test run and result: `.venv-validation\Scripts\python.exe -m pytest -q` completed with `42 passed in 5.35s`; `compileall` and targeted `git diff --check` succeeded.
- Approval decision: Reviewed the diff and test evidence before committing and pushing; preserved an unrelated environment-template edit rather than including it in that change.

### [GENUINE] 2026-11-19 — Restrict AI integration to Gemini and select Flash-Lite
- Task/expectation: Use only the Gemini API key, ensure `.env.example` contains no real key, and select a cost-efficient model with a bounded response.
- Prompt summary: “Use only the Gemini key, select the model that does not consume too many tokens, then commit and push.”
- Files changed: .env.example, README.md, docs/PROJECT_REPORT.md, docs/REGRESSION_TESTS.md, docs/SRS.md, src/fitdesk/ai_client.py, src/fitdesk/config.py, src/fitdesk/gemini_client.py, tests/test_cli.py; removed DeepSeek/OpenRouter/Groq clients and tests.
- Test run and result: `.venv-validation\Scripts\python.exe -m pytest -q` completed with `37 passed in 4.90s`; `compileall` and `git diff --check` succeeded.
- What was corrected: Removed non-Gemini routing/configuration, changed the default model to `gemini-3.5-flash-lite`, capped generated output at 256 tokens, and kept `GEMINI_API_KEY` blank in `.env.example`. The local `.env` model setting was updated without displaying or changing the Gemini credential.
- Approval decision: One live request was made using the user's local Gemini key; the classification and draft succeeded, then the draft was rejected (`n`). The local status log records `rejected_by_staff`, provider `gemini`, and model `gemini-3.5-flash-lite`; no message was sent. Existing historic status-log entries remain unchanged and are documented as previous provider experiments.

### [GENUINE] 2026-11-18 — Record provider/model in enquiry status and document project evidence
- Task/expectation: Make AI failures attributable to a provider/model and produce a reader-friendly report from code, tests, and available local status-log evidence.
- Files changed: src/fitdesk/ai_client.py, src/fitdesk/cli.py, tests/test_cli.py, README.md, docs/SRS.md, docs/REGRESSION_TESTS.md, docs/PROJECT_REPORT.md.
- Test run and result: `.venv-validation\Scripts\python.exe -m pytest -q` completed with `60 passed in 6.56s`; `compileall` succeeded.
- What was corrected: New status entries include non-secret `ai_provider` and `ai_model` fields. Existing log entries were not rewritten because their model identity cannot be recovered reliably. Added a project report documenting historical counts, provider errors, verified Groq outcome, test coverage, limitations, and fixes.
- Approval decision: No live requests were made for this documentation and logging update. API keys remain local and are not logged.

### [GENUINE] 2026-11-12 — Project scaffold and remote setup
- Task/expectation: Initialize the repo, create the required bootstrap files, and confirm the remote repo before code changes.
- Summary of prompt/instruction: “Set up the project with .gitignore, .env.example, requirements.txt, then push the initial scaffold.”
- Files changed: .gitignore, .env.example, requirements.txt
- Test run and result: No code tests yet; the initial local commit succeeded, then the first push failed because the remote repo URL was incorrect.
- What was corrected: The remote URL was updated to the confirmed GitHub repository before the successful push.
- Approval decision: Proceeded after remote confirmation.

### [GENUINE] 2026-11-12 — Fix pytest import path and validate the suite
- Task/expectation: Get pytest to run in the src-layout project and verify the implementation against the required scenarios.
- Summary of prompt/instruction: “Run the tests and fix the root cause of any import or logic failure before continuing.”
- Files changed: tests/conftest.py, src/fitdesk/lookup.py, tests/test_cli.py
- Test run and result: `C:/Users/Phathutshedzo/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest -q` → `7 passed, 1 warning in 2.59s`
- What was corrected: Added the src path to sys.path for pytest, tightened package matching to avoid false positives like “25 sessions” matching “5 sessions”, and fixed the log-writing test to stub the Gemini result properly.
- Approval decision: Proceeded because the suite passed.

### [GENUINE] 2026-11-12 — Finalize failure handling and verify clean installation
- Task/expectation: Audit and finish the project, cover failure paths, verify a fresh requirements-only install, and prepare the final changes for review.
- Summary of prompt/instruction: The finalisation brief required structured Gemini output, deterministic facts, explicit failures, offline tests, a repository audit, and a final push.
- Files changed: .gitignore, README.md, docs/SRS.md, docs/REGRESSION_TESTS.md, docs/RAPLH_LOG.md, pyproject.toml, requirements.txt, src/fitdesk/approval.py, src/fitdesk/cli.py, src/fitdesk/gemini_client.py, src/fitdesk/lookup.py, src/fitdesk/models.py, src/fitdesk/status_log.py, src/fitdesk/ui.py, tests/test_cli.py
- Test run and result: Fresh environment created and installed from requirements.txt. With GEMINI_API_KEY unset, `.venv-validation\Scripts\python.exe -m pytest -v` completed with `36 passed in 6.85s`. A no-key CLI smoke run returned exit 1, displayed a friendly error, and recorded failed_ai_service. A later live request was attempted; see the genuine live-integration entry below.
- What was corrected: Added schema-constrained Gemini output and actual HTTP timeout configuration; tightened customer-text-bound lookup, unknown day/time handling, and number-word matching; made data/log failures non-sent; added cross-process log locking and CLI cancellation/empty-input handling.
- Approval decision: Human review is pending. No email was sent and the repository rename is pending GitHub CLI access.

### [GENUINE] 2026-11-16 — Live Gemini request and schema compatibility fix
- Task/expectation: Run the application with the user-confirmed replacement key and verify an end-to-end Gemini enquiry without displaying the credential.
- Summary of prompt/instruction: “Let's run it and test”; the user confirmed the `.env` value had been replaced after revoking the value exposed in chat.
- Files changed: src/fitdesk/gemini_client.py, tests/test_cli.py, .env (the rejected value was cleared after the provider response).
- Test run and result: Six live enquiries initially returned HTTP 400 because Gemini rejected `additional_properties` emitted from the Pydantic schema. After replacing it with an explicit supported JSON schema, the offline suite passed 36 tests. A follow-up live request reached Gemini but returned HTTP 403 `PERMISSION_DENIED`, with the provider reporting the key as leaked. No live draft was generated.
- What was corrected: Replaced direct Pydantic schema submission with a compact JSON schema compatible with Gemini's accepted fields, retaining Pydantic validation locally. Cleared the rejected local key and stopped further live calls.
- Approval decision: User authorized live testing and confirmed the local key was rotated. The provider rejected it; a newly generated key must be added locally before any retry.

## Bug-hunt table

| ID | Description | Root cause | Fix | Regression evidence |
|---|---|---|---|---|
| B-01 | A model could return a known package the customer did not request | Lookup trusted model package names | Resolve requested packages from customer text before using approved data | `test_model_cannot_substitute_a_known_package_not_requested` |
| B-02 | Sunday 09:00 could be described as Saturday 09:00 | Time lookup did not require a Saturday context | Only use Saturday availability when Saturday is asked about; escalate unsupported days/times | `test_sunday_time_does_not_claim_saturday_availability` |
| B-03 | Missing/corrupt price data could crash the CLI | File/JSON errors escaped lookup | Validate data structure and return failed_data | `test_missing_data_file_fails_without_sending`, `test_corrupt_data_file_fails_without_sending` |
| B-04 | Corrupt status log could be silently overwritten | Invalid JSON was treated as an empty log | Fail closed and preserve the original corrupt file | `test_corrupt_status_log_never_records_sent_or_crashes` |
| B-05 | Concurrent writers could overwrite one another | Read/modify/write had no process lock | Lock around read and atomic replace | `test_concurrent_status_log_appends_are_not_lost` |
| B-06 | Empty CLI invocation did not offer interactive input or log rejection | CLI returned early before the normal pipeline | Add interactive input and failed_empty_input handling | `test_empty_interactive_input_is_rejected` |
| B-07 | SDK call had no actual structured schema or effective timeout | Timeout was passed in the wrong request field and JSON mode was absent | Use Pydantic response_schema and HttpOptions timeout in milliseconds | `test_gemini_request_uses_structured_schema_and_timeout` |
| B-08 | Unexpected availability values could be described as “full”; invalid UTF-8 could crash file reads | Lookup accepted arbitrary status strings and omitted UnicodeDecodeError handling | Validate statuses against Available/Full and fail closed on invalid encoding | `test_undocumented_availability_status_fails_without_sending`, `test_non_utf8_data_file_fails_without_sending`, `test_non_utf8_status_log_never_records_sent_or_crashes` |
| B-09 | Gemini rejected the SDK-generated Pydantic schema | `additionalProperties` was serialized in a field the Gemini endpoint does not accept | Send a compact supported JSON schema and retain Pydantic validation after response | Live request changed from HTTP 400 schema error to HTTP 403 credential rejection; offline schema assertion passes |

### Closing answers
1. How would you stop an AI coding agent from changing unrelated files or exposing an API key?
   - Keep the repo scoped to the project folder and use .gitignore to block .env, .venv, __pycache__, pytest cache, and runtime log data.
   - Only stage specific files using git add on the intended paths instead of a blind git add . and scan staged diffs for secrets before commit.

2. How would you stop the loop if the agent keeps repeating the same failed fix?
   - Stop after the third attempt on the same root cause, document the output and hypothesis, and ask for human guidance.
   - Do not repeat the same change without new evidence. Compare the latest failure with earlier attempts, keep the relevant error and test output, and revise the diagnosis or choose a simpler approach. If progress still depends on an assumption, pause for human review rather than making more speculative edits.
