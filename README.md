# FitDesk Enquiry Assistant

**Time spent:** 3.5 hours

[Repository](https://github.com/TshikhovhokhovhoPhathutshedzo/rahn-assessment-Phathutshedzo-Tshikhovhokhovho)

A Python command-line assistant that helps FitDesk staff prepare replies to customer enquiries. It uses an AI model to classify what the customer asked, but uses the studio's local approved data—not the model—to determine package prices and Saturday availability. Every draft must be reviewed by staff before it is recorded as approved.

> **Important:** This is an assessment/demo application. It does not send email or messages, make bookings, take payments, or refresh live studio availability. “Approved and recorded as sent” means the staff-approved result was written to the local status log.

## What happens when it runs

1. The customer enters an enquiry in the terminal.
2. Gemini receives the FitDesk scope rules in `data/knowledge_base.json` and approved prices/availability in `data/fitdesk_data.json`, then classifies the request as FitDesk-related or off-topic using a validated JSON response.
3. The application checks requested packages and times against `data/fitdesk_data.json`.
4. It builds a reply from approved facts. If a fact is missing or unsupported, it uses: `I'll check with the owner and come back to you.`
5. For an off-topic request, it drafts the fixed FitDesk-only reply from the knowledge base instead of answering the unrelated request. Staff reviews either kind of draft and enters `y` to approve or `n` to reject. This approval is always required.
6. The outcome is recorded in `status_log.json`. Failed requests and rejected drafts are not recorded as sent.

Enquiries are rate limited before any Gemini request: each client can submit up to 10 enquiries in a rolling 60-second window, with a shared application limit of 30 per 60 seconds. This supports three clients at 10 enquiries per minute each and prevents one client from using the whole allowance. A rejected request is logged as `rate_limited` and does not call Gemini. SQLite stores the rolling counters in the ignored `.rate_limit.sqlite3` file so concurrent processes on the same machine share the limit.

By default, the command-line app identifies its caller as `local`. To enforce per-client quotas for three users, configure a distinct `FITDESK_CLIENT_ID` for each user; code can also pass a `client_id` to `process_enquiry`. This is an identifier, not authentication. Processes must use the same local database file to share the total cap; separate machines or hosted instances need a shared service/database.

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
FITDESK_CLIENT_ID=local
```

The default model is `gemini-3.5-flash-lite`, Google's current Flash-Lite option for fast, cost-efficient lightweight tasks. The request also caps output at 256 tokens to keep classification responses compact. Model availability, rates, and free-tier limits can change; see [Google's model documentation](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite) and [pricing](https://ai.google.dev/gemini-api/docs/pricing). Create a key in [Google AI Studio](https://aistudio.google.com/). Keep the real key only in `.env`; `.env.example` contains an empty placeholder and `.env` is ignored by Git.

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

The tests mock Gemini calls, so they do not need an API key, internet access, or a paid AI request. They cover knowledge-base context and off-topic handling, request configuration, response validation, approved-data lookups, draft generation, staff approval, error handling, and status logging.

## Project structure

```text
.
├── data/
│   ├── fitdesk_data.json
│   └── knowledge_base.json
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
│       ├── knowledge_base.py
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
| `knowledge_base.py` | Loads and validates the FitDesk scope rules and combines them with approved studio facts for Gemini context. Invalid or missing knowledge-base data fails closed. |
| `models.py` | Defines the allowed enquiry intents and the Pydantic `EnquiryAnalysis` model. Validation prevents unexpected AI output from flowing into later steps. |
| `rate_limiter.py` | Applies per-client and shared rolling-window request limits before Gemini is called. SQLite transactions make checks atomic across concurrent processes using the same local database file. The CLI client ID is configurable with `FITDESK_CLIENT_ID`; this value identifies a client but does not authenticate it. |
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
| `data/knowledge_base.json` | Defines FitDesk's supported enquiry topics, response rules, and fixed off-topic reply. Gemini receives it with the approved studio data for each classification request. |
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
| `.rate_limit.sqlite3` | Runtime-generated SQLite database that shares request counters across processes on the same machine; it is ignored by Git. |

## Design and safety boundaries

- The AI provider interprets the enquiry; it does not supply the prices or availability used in the reply.
- Gemini receives the local knowledge base and approved studio data on each classification request. Scope classification is model-assisted; the off-topic reply itself is deterministic, and missing or invalid local knowledge data fails closed.
- Requested packages and Saturday times are checked against the customer's message and approved local data.
- Missing or unsupported facts trigger the owner-check phrase instead of a guessed answer.
- AI, data, and log errors fail closed: they do not become successful/sent outcomes.
- Staff approval is always required, even if the model says approval is unnecessary.
- The log is a local audit record. It is not a messaging service or proof that a customer received a reply.

## What doesn't work yet

- The application handles one enquiry per command-line run.
- English enquiries are the supported and tested language.
- Availability is sample/local data and is not refreshed from a live booking system.
- The application does not send replies, make bookings, process payments, or integrate with WhatsApp/email.
- Rate-limit counters are shared only by processes using the same local SQLite file; separate machines or hosted instances do not share the counters.
- Gemini may reject requests because of invalid credentials, account credits, model availability, provider rate limits, or network issues.

## AI use

I used the Copilot coding assistant in VS Code to help implement and debug the Python application, create and run regression tests, and draft the technical requirements and RAPLH log. I used Google's Gemini API in the application to classify a test enquiry; its output was checked against the local approved data and I rejected the draft, so nothing was sent. I also checked Gemini request formatting and model information against Google's documentation. The AI coding assistant did not provide the studio's prices or availability; those are read from `data/fitdesk_data.json`.

## Working style

**Write each answer yourself, without AI, in 80–150 words, as required by the assessment. Replace each prompt below with your own answer before submitting.**

1. It is 22:00, and you have been stuck on the same error for three hours. What do you do next, step by step?

   [Add your own words here; the answer must be at least 80 words.]

2. It is Wednesday. Your teammate has not replied to messages since Monday, and you present together on Friday. What do you do?

   i would first reach out to my teammate via a message or a call to understand why they have not responded since monday, then will clearly communicate the urgency of our friday presentation and ask an update on their progress. While waiting for a response, I would review our shared work, identify any outstanding tasks, and assess what needs to be completed to keep us on schedule. If I still received no response, I would take the initiative to work on the outstanding sections to avoid putting the presentation at risk. I would also inform the relevant team lead if necessary. My priority would be to ensure we deliver a quality presentation on Friday while maintaining professionalism, accountability, and teamwork.

3. Your mentor tells you that the approach you have spent two days on is wrong. How do you react, and what do you do next?

   I would first listen to my mentor and try to understand why they think my approach is wrong. I wouldn't take the feedback personally because I understand that making mistakes is part of learning and improving. I would ask questions to understand where I went wrong and what I should have done differently. Even though I spent two days working on it, I would rather correct my approach than continue with something that won't produce the right results. I would then apply the feedback, make the necessary changes and keep my mentor updated on my progress. I believe being open to feedback is important for personal and professional growth.

4. From January to March 2027, you must attend sessions every Monday, Wednesday and Friday. What in your life could get in the way, and what is your plan for each thing?

   At the moment, my only major commitment is work, and I don't have any other commitments that would interfere with attending the sessions. My plan would be to organise my work schedule around the Monday, Wednesday and Friday sessions and communicate with my employer in advance if any adjustments are needed. I would also make sure I manage my time properly so I can balance my work responsibilities with the programme. I understand the importance of being consistent and showing up for every session. I am committed to making this programme a priority from January to March 2027.
