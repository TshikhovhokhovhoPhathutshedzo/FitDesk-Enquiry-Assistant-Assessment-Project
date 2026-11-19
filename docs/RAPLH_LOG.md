# RAPLH log

### [GENUINE] 2026-11-19 — Restrict AI integration to Gemini and select Flash-Lite
- Task/expectation: Use only the Gemini API key, ensure `.env.example` contains no real key, and select a cost-efficient model with a bounded response.
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
   - The workflow here uses a max 3-attempt rule, human review gate, and explicit test evidence before continuing.
