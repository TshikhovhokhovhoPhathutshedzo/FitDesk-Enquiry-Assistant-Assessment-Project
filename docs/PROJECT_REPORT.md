# FitDesk Enquiry Assistant — Project and Test Report

**Report date:** 19 November 2026

**Project type:** Python command-line assessment/demo

**Repository:** [FitDesk Enquiry Assistant](https://github.com/TshikhovhokhovhoPhathutshedzo/FitDesk-Enquiry-Assistant-Assessment-Project)

## 1. Executive summary

FitDesk Enquiry Assistant accepts one customer enquiry, uses a selected AI provider to classify it, verifies requested prices and Saturday times against local approved data, drafts a response, asks staff to approve or reject it, and records the outcome.

The AI is used to understand the message, not as the source of prices or availability. Code resolves facts from `data/fitdesk_data.json`; unsupported questions use the owner-check escalation phrase. Every draft remains behind a staff approval gate.

The current application uses Gemini only. Its default model is `gemini-3.5-flash-lite`, Google's cost-efficient Flash-Lite option, and generated output is capped at 256 tokens. Earlier project iterations experimented with DeepSeek, OpenRouter, and Groq; those integrations have been removed. The historical status-log report below preserves those past experiments and should not be read as current provider support.

## 2. Scope and boundaries

### Included

- Command-line input, either interactively or as a command argument.
- Gemini request and JSON classification.
- Validated JSON classification of intent, requested packages, requested Saturday times, and other details.
- Approved price and Saturday availability lookup from a local JSON file.
- Deterministic reply drafting and a fixed escalation phrase for unsupported facts.
- Staff approval (`y`) or rejection (`n`) before a result can be recorded as sent.
- Local status history with atomic updates and process locking.
- Mocked offline regression tests for provider integrations and the application flow.

### Not included

- Sending email, text, WhatsApp, or other customer messages.
- Making bookings, taking payments, or connecting to a live scheduling system.
- Automatically refreshing the sample availability data.
- Guaranteeing provider uptime, free usage, account credits, or model availability.

“Approved and recorded as sent” is a local status value; it does not mean a message was transmitted to a customer.

## 3. How a request moves through the application

1. `src/fitdesk/__main__.py` starts the command-line interface.
2. `src/fitdesk/cli.py` accepts the enquiry and coordinates the workflow.
3. `src/fitdesk/ai_client.py` calls the Gemini integration.
4. Gemini returns a classification which is validated against `src/fitdesk/models.py`.
5. `src/fitdesk/lookup.py` checks the customer's actual request against `data/fitdesk_data.json`; model-suggested facts alone are not trusted.
6. `src/fitdesk/drafter.py` builds the reply from approved facts and escalates unknown information.
7. `src/fitdesk/approval.py` requires staff to approve or reject the draft.
8. `src/fitdesk/status_log.py` records the outcome in the local, Git-ignored `status_log.json`.

`src/fitdesk/gemini_client.py` uses Gemini's SDK-specific structured-output integration. The app does not load or call other AI providers.

## 4. Provider and model configuration

The app reads the Gemini key and optional model from `.env`:

| Provider | Environment variables | Default model in project configuration |
|---|---|---|
| Gemini | `GEMINI_API_KEY`, `GEMINI_MODEL` | `gemini-3.5-flash-lite` |

Google describes Gemini 3.5 Flash-Lite as optimized for cost-efficient, high-throughput execution. The request caps output at 256 tokens. These measures limit response size and use a cost-efficient model; they do not guarantee a particular bill or free-tier allowance. The key is intentionally never written to the status log or committed to the repository.

## 5. Status-log findings

The local `status_log.json` was inspected on 18 November 2026. It contained **21 entries** covering 16–18 November. The log file is ignored by Git and is local to the working copy; these counts describe that historical snapshot and may differ on another machine.

### Overall statuses

| Logged status | Count | Interpretation |
|---|---:|---|
| `failed_ai_service` | 19 | The application did not receive a usable classification from the provider. No reply was approved or sent. |
| `rejected_by_staff` | 2 | A draft was rejected during staff review; it was not recorded as sent. |
| `failed_ai_service` with provider/model metadata | 1 of the 19 failures | A newer OpenRouter request explicitly recorded `openrouter` and `openai/gpt-4o`; it returned HTTP 402. |

The last row is a detail within the `failed_ai_service` total, not an additional status.

### Provider/error breakdown from the inspected log

For legacy entries, a provider below is attributed only when its name appeared in the recorded error reason. Its model was not recorded, so the model is marked unknown.

| Provider attribution | Model recorded at the time? | Outcome in local log | Count | What the evidence establishes |
|---|---|---|---:|---|
| Gemini (inferred from error text) | No | HTTP 400 `INVALID_ARGUMENT` | 6 | Gemini rejected the submitted schema. The schema was subsequently changed to the supported JSON-schema form. |
| Gemini (inferred from error text) | No | HTTP 403 `PERMISSION_DENIED` | 1 | The provider rejected the credential and reported it as leaked. That credential was cleared; it should not be reused. |
| Gemini (inferred from error text) | No | HTTP 504 `DEADLINE_EXCEEDED` | 3 | Requests timed out before returning an answer. These records alone do not establish a quota limit. |
| DeepSeek (inferred from error text) | No | HTTP 402 | 1 | The request was rejected for insufficient balance, consistent with the provider's error-code documentation. |
| OpenRouter (inferred from error text) | No | HTTP 402 | 5 | The requests were rejected for an account/key credit or spending-limit condition. Legacy entries do not contain provider metadata or model names. |
| OpenRouter (explicit metadata) | `openai/gpt-4o` | HTTP 402 | 1 | This newer entry explicitly identifies the configured provider and model. |
| Groq (inferred from error text) | No | HTTP 403 | 1 | A request was blocked with Cloudflare error code 1010. Retrying with a descriptive `User-Agent` subsequently allowed a Groq response. |
| Provider not identifiable | No | Missing Gemini key message | 1 | The reason says a Gemini key was missing, but no provider metadata was captured. |
| Provider not recorded | No | `rejected_by_staff` | 2 | The log confirms rejection, but pre-metadata entries cannot identify the model used. |

### What historical records cannot tell us

- Most entries were written before `ai_provider` and `ai_model` fields were added. Their model cannot be reliably reconstructed from the log.
- A provider name in an error message is useful evidence of which client made the request, but is not a recorded model ID.
- The Groq live success was observed in the test session, but its local rejection record predates model metadata; that historical row cannot independently prove which model produced it.
- New AI attempts record `ai_provider` and configured `ai_model`. This makes future errors, successful classifications, and staff decisions easier to attribute. Existing log entries are left unchanged rather than rewritten with guesses.

## 6. Live-provider observations

These are observations from individual test requests, not guarantees about provider availability:

| Provider/model | Observation | Result |
|---|---|---|
| Gemini / model used in earlier test (`gemini-3.8-flash`) | Schema incompatibility was observed first; after the request schema was corrected, later calls returned a credential rejection or deadline timeout. | Those earlier attempts did not produce a verified draft. The current default, `gemini-3.5-flash-lite`, was subsequently live-verified: it returned a valid classification and draft, which staff rejected before sending. |
| DeepSeek / model not recorded | HTTP 402 was returned. | Historical experiment only; integration removed. |
| OpenRouter / one new record has `openai/gpt-4o`; other model IDs not recorded | HTTP 402 returned. | Historical experiment only; integration removed. |
| Groq / model not recorded in the historical log | Initial request returned HTTP 403 with Cloudflare error 1010. Adding a descriptive `User-Agent` allowed a later request to return a valid classification. | Historical experiment only; integration removed. |

The HTTP codes above describe those individual requests. They do not prove that a provider is always unavailable or that another account/model will produce the same result.

## 7. Problems encountered and fixes

| Problem | Effect | Fix or current handling |
|---|---|---|
| Gemini SDK schema included a field Gemini rejected | Gemini returned HTTP 400 before producing JSON. | Send a compact Gemini-compatible JSON schema and validate the result locally with Pydantic. |
| Gemini credential was rejected as leaked | Live Gemini calls failed with HTTP 403. | Stop retrying with that credential and clear it locally. Credentials should be rotated privately and stored only in `.env`. |
| Gemini requests exceeded the provider deadline | Calls returned HTTP 504, including a retry with a longer client timeout. | Record the service error and fail closed; the app does not mark the enquiry as sent. |
| DeepSeek returned HTTP 402 | No model response was available. | Report the provider error; the provider documentation describes 402 as insufficient balance. |
| OpenRouter returned HTTP 402 | No model response was available. | Record provider/model in new entries and direct the operator to check the OpenRouter account/key credits or limits. |
| Groq request was blocked with HTTP 403 / Cloudflare 1010 | The first live request was denied before a classification was returned. | Add a descriptive application User-Agent; a later Groq call returned valid JSON and the FitDesk draft flow completed. |
| A status-log error did not say which model was used | Older errors were difficult to attribute. | Add non-secret `ai_provider` and `ai_model` fields to each new enquiry status entry. Do not invent these fields for historical entries. |
| A model could suggest unrequested package facts | Could have produced an incorrect price reply. | Resolve requested packages from customer text and approved data in deterministic code. |
| Unknown weekday/time or missing data might be answered confidently | Could have made an unsupported availability claim. | Validate available data and use the exact escalation phrase for unknown facts. |
| Concurrent or corrupt log writes could lose or damage records | Audit history might be overwritten or the CLI might claim success. | Use a process lock, atomic replacement, validation, and fail-closed error handling. |
| Staff approval might be skipped or misread | An unreviewed message could be recorded as sent. | Always prompt for explicit `y` or `n`; cancellation and invalid input are non-sent outcomes. |

## 8. Regression-test report

Run the offline suite from the repository root:

```powershell
python -m pytest -v
```

The latest verified Gemini-only automated run was **37 passed in 4.90 seconds**. Separately, a live request using `gemini-3.5-flash-lite` successfully classified an enquiry and generated a draft. The staff rejection path was selected, and the status log recorded `rejected_by_staff`, provider `gemini`, and model `gemini-3.5-flash-lite`; nothing was sent. The automated suite uses mocked Gemini calls, so it does not need API credentials or make network calls. It covers:

- Gemini structured schema, compact 256-token output budget, timeout settings, and malformed/service responses.
- Gemini model metadata on successful and failed enquiry records.
- Pricing and availability lookups against approved data, including unsupported requests and prompt-injection-style substitutions.
- Staff approval, rejection, cancellation, and invalid responses.
- Missing/corrupt data, malformed AI responses, invalid UTF-8, concurrent status-log updates, and fail-closed behavior.

The test result is evidence for the tested code paths, not a claim that external services are always available. See [REGRESSION_TESTS.md](./REGRESSION_TESTS.md) for the test matrix and [SRS.md](./SRS.md) for requirements.

## 9. Running and troubleshooting

1. Create and activate a virtual environment, install `requirements.txt`, and copy `.env.example` to `.env`. See the [README setup instructions](../README.md#setup-on-windows).
2. Put the Gemini key only in `.env`; set `GEMINI_MODEL` only if you want to override the Flash-Lite default.
3. Run `python -m fitdesk` and inspect the draft. Enter `n` for a test run so it is recorded as rejected rather than approved.
4. If the CLI shows a generic service error, inspect the newest object at the end of local `status_log.json`. New records include `ai_provider`, `ai_model`, `status`, and `reason`; never share or commit `.env`.
5. For a service failure, inspect the logged HTTP status and check the Gemini credential, model availability, network, or current Gemini API limits before retrying. Historical entries in the report include errors from other providers, but the current app calls Gemini only.

## 10. Related project documentation

- [README](../README.md): install, configure, run, test, and navigate the source tree.
- [Software Requirements Specification](./SRS.md): requirements and scope.
- [Regression Tests](./REGRESSION_TESTS.md): test-case matrix and validation evidence.
- [RAPLH Log](./RAPLH_LOG.md): chronological development and bug-fix notes.
