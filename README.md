# FitDesk Enquiry Assistant

A Python command-line assistant that helps FitDesk staff prepare replies to customer enquiries. It uses an AI model to classify what the customer asked, but uses the studio's local approved data—not the model—to determine package prices and Saturday availability. Every draft must be reviewed by staff before it is recorded as approved.

> **Important:** This is an assessment/demo application. It does not send email or messages, make bookings, take payments, or refresh live studio availability. “Approved and recorded as sent” means the staff-approved result was written to the local status log.

## What happens when it runs

1. The customer enters an enquiry in the terminal.
2. Gemini classifies the request into the expected fields.
3. The application checks requested packages and times against `data/fitdesk_data.json`.
4. It builds a reply from approved facts. If a fact is missing or unsupported, it uses: `I'll check with the owner and come back to you.`
5. Staff reviews the draft and enters `y` to approve or `n` to reject. This approval is always required.
6. The outcome is recorded in `status_log.json`. Failed requests and rejected drafts are not recorded as sent.

Enquiries are rate limited before any Gemini request: each client can submit up to 10 enquiries in a rolling 60-second window, with a shared application limit of 30 per 60 seconds. This supports three clients at 10 enquiries per minute each and prevents one client from using the whole allowance. A rejected request is logged as `rate_limited` and does not call Gemini.

The current application is a command-line program and identifies its caller as `local`. Code integrating `process_enquiry` can supply a stable authenticated `client_id` to enforce separate client quotas. The limiter is thread-safe within one running process; separate processes or hosted instances do not share counters. A multi-worker web deployment would need a shared backing store such as Redis.

## Requirements

- Python 3.10 or later
- A Gemini API key
- Internet access when running an AI-backed enquiry

## Setup on Windows

Open PowerShell in the repository folder, then run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and add your Gemini API key. The application uses Gemini only:

```dotenv
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-3.5-flash-lite
REQUEST_TIMEOUT_SECONDS=20
```

The default model is `gemini-3.5-flash-lite`, Google's cost-efficient Flash-Lite option. The request also caps output at 256 tokens to keep classification responses compact. Model availability, rates, and free-tier limits can change; see [Google's model documentation](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite) and [pricing](https://ai.google.dev/gemini-api/docs/pricing). Create a key in [Google AI Studio](https://aistudio.google.com/). Keep the real key only in `.env`; `.env.example` contains an empty placeholder and `.env` is ignored by Git.

## Run the application

With the virtual environment activated, run either:

```powershell
python -m fitdesk
```

The program prompts for a customer enquiry. To pass one directly as a command-line argument:

```powershell
python -m fitdesk "How much is the 12-session pack and do you have Saturday slots?"
```

The application displays its interpretation and a draft, then prompts `Send? (y/n)`. Enter `y` to approve and record it, or `n` to reject it. No external message is sent.

If you do not activate the virtual environment, use its Python executable directly:

```powershell
.\.venv\Scripts\python.exe -m fitdesk
```

## Run the tests

Install dependencies as described above, then run:

```powershell
python -m pytest
```

The tests mock Gemini calls, so they do not need an API key, internet access, or a paid AI request. They cover request configuration, response validation, approved-data lookups, draft generation, staff approval, error handling, and status logging.

## Project structure

```text
.
├── data/
│   └── fitdesk_data.json
├── docs/
│   ├── RAPLH_LOG.md
│   ├── PROJECT_REPORT.md
│   ├── REGRESSION_TESTS.md
│   └── SRS.md
├── src/
│   └── fitdesk/
│       ├── __init__.py
│       ├── __main__.py
│       ├── ai_client.py
│       ├── approval.py
│       ├── cli.py
│       ├── config.py
│       ├── drafter.py
│       ├── gemini_client.py
│       ├── rate_limiter.py
│       ├── lookup.py
│       ├── models.py
│       ├── status_log.py
│       └── ui.py
├── tests/
│   ├── conftest.py
│   ├── test_cli.py
│   └── test_rate_limiter.py
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
└── README.md
```

## What each part does and why it matters

### Application code: `src/fitdesk/`

| File | Purpose and importance |
|---|---|
| `__main__.py` | Makes `python -m fitdesk` start the command-line application. |
| `cli.py` | Coordinates the full workflow: input, AI classification, fact lookup, reply drafting, staff approval, and status recording. It is the main place to follow an enquiry through the program. |
| `config.py` | Loads the Gemini key, selected model, and request timeout from `.env`. Keeping configuration here avoids embedding machine-specific values in code. |
| `ai_client.py` | Provides the single Gemini analysis entry point and reports the non-secret provider/model values written to the status log. |
| `gemini_client.py` | Sends Gemini requests using its structured JSON response schema and compact output limit, handles service errors, and validates returned analysis. |
| `models.py` | Defines the allowed enquiry intents and the Pydantic `EnquiryAnalysis` model. Validation prevents unexpected AI output from flowing into later steps. |
| `rate_limiter.py` | Applies thread-safe per-client and shared rolling-window request limits before Gemini is called. The current CLI uses one `local` client identity; hosted integrations should pass an authenticated client ID and use shared storage across multiple application processes. |
| `lookup.py` | Loads and validates approved studio data, checks what the customer actually requested, and returns matching facts. This is the boundary that prevents the model from inventing or substituting prices and availability. |
| `drafter.py` | Builds the reply from verified facts and adds the standard owner-check phrase when information is unknown. |
| `approval.py` | Keeps the staff approval prompt in a focused module and handles cancellation and invalid responses. |
| `ui.py` | Displays customer input, analysis, draft, and errors in the terminal using Rich panels. |
| `status_log.py` | Appends outcomes to `status_log.json` with locking and atomic file replacement so concurrent writes do not silently overwrite one another. Enquiry entries include the selected `ai_provider` and `ai_model` (not the secret key). |
| `__init__.py` | Marks `fitdesk` as a Python package and exposes its version. |

### Data, tests, and documentation

| Path | Purpose and importance |
|---|---|
| `data/fitdesk_data.json` | The approved source of package prices and Saturday slot statuses. Change this file when the studio's confirmed facts change; replies should use these facts rather than model-generated claims. |
| `tests/conftest.py` | Adds the `src` directory to the test import path and redirects status logs to a temporary directory, keeping tests isolated from real runtime data. |
| `tests/test_cli.py` | Exercises the application workflow and Gemini request setup using mocked AI responses; tests do not make real API calls. |
| `tests/test_rate_limiter.py` | Verifies per-client and shared rolling limits, expiry, and thread safety under concurrent requests. |
| `docs/SRS.md` | Records the software requirements, scope, stakeholders, and acceptance criteria. |
| `docs/REGRESSION_TESTS.md` | Describes the regression-test cases and previously recorded test evidence. |
| `docs/RAPLH_LOG.md` | Keeps the project's work and bug-fix log. |
| `docs/PROJECT_REPORT.md` | Gives new readers an end-to-end project, test, historical provider, and status-log report, including known failures and fixes. |

### Root-level files

| File | Purpose and importance |
|---|---|
| `.env.example` | Safe Gemini-only configuration template. The `GEMINI_API_KEY` value is empty; copy it to `.env` and enter the real key only there. |
| `.gitignore` | Prevents local secrets, virtual environments, caches, and runtime status logs from being added to Git. |
| `pyproject.toml` | Defines project metadata, Python compatibility, dependencies, and the `src` package layout used by installation tools. |
| `requirements.txt` | Lists the packages installed by `pip install -r requirements.txt`, including the project itself and test dependency. |
| `README.md` | This guide: setup, configuration, commands, workflow, and code map. |
| `.env` | Local-only provider configuration created during setup. It is intentionally not tracked or documented with its contents. |
| `status_log.json` | Runtime-generated record of enquiry outcomes. It is ignored by Git and appears after the application records an outcome. |
| `status_log.json.lock` | Runtime lock file used while updating the status log; it is also ignored by Git. |

## Design and safety boundaries

- The AI provider interprets the enquiry; it does not supply the prices or availability used in the reply.
- Requested packages and Saturday times are checked against the customer's message and approved local data.
- Missing or unsupported facts trigger the owner-check phrase instead of a guessed answer.
- AI, data, and log errors fail closed: they do not become successful/sent outcomes.
- Staff approval is always required, even if the model says approval is unnecessary.
- The log is a local audit record. It is not a messaging service or proof that a customer received a reply.

## Current limitations

- The application handles one enquiry per command-line run.
- English enquiries are the supported and tested language.
- Availability is sample/local data and is not refreshed from a live booking system.
- The application does not send replies, make bookings, process payments, or integrate with WhatsApp/email.
- A selected provider may reject requests because of invalid credentials, account credits, model availability, rate limits, or network issues.

## AI assistance

Gemini request formatting and the selected Flash-Lite model were checked against Google's API documentation. An AI coding assistant helped with implementation and testing. All package prices and availability used by the application remain in the approved local data file.

## Working style

<!-- TO BE WRITTEN BY ME, BY HAND: 4 answers, 80–150 words each -->
