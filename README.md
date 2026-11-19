# FitDesk Enquiry Assistant

**Time spent:** 3.5 hours

[Repository](https://github.com/TshikhovhokhovhoPhathutshedzo/rahn-assessment-Phathutshedzo-Tshikhovhokhovho)

A Python terminal chatbot prototype that lets a customer have a continuous conversation with FitDesk. A deterministic local response layer handles supported package-price and Saturday-availability questions, including follow-ups using earlier customer messages. Gemini classifies other messages; prices and availability always come from approved local information.

> **Important:** This is a local terminal prototype, not a deployed production service. It does not send messages externally, make or confirm bookings, take payments, or refresh live availability. Booking-related messages receive the listed Saturday schedule and a clear instruction to contact FitDesk staff; the displayed sample schedule is not a live calendar.

## What happens when it runs

1. The chatbot opens a terminal conversation and stays available until the customer types `done`, `exit`, or `quit` (or presses Ctrl+C).
2. Simple greetings and recognized package-price or Saturday-availability questions receive deterministic replies without using Gemini. Follow-ups such as “what other time is available?” and “how much is it?” use earlier customer messages. Other messages are sent to Gemini with the FitDesk knowledge base, approved studio data, and up to the 10 most recent conversation turns.
3. The application checks requested prices and Saturday times against `data/fitdesk_data.json`; it does not rely on model-generated prices or availability.
4. Unsupported package prices and other unknown facts use: `I'll check with the owner and come back to you.` An unlisted Saturday time is explicitly labeled as unlisted; off-topic messages get a fixed FitDesk-only reply.
5. Booking requests are not submitted. The chatbot answers requested package prices and Saturday times from approved data (including stating when a time is not listed), then tells the customer to contact FitDesk staff to confirm current availability and arrange a booking.
6. Each response or failure is recorded in `status_log.json` with a conversation ID. A `responded_in_chat` status means only that the reply was shown in the local terminal; no external message was sent.

Every chat turn is rate limited: each client can submit up to 10 messages in a rolling 60-second window, with a shared application limit of 30 per 60 seconds. Greetings do not call Gemini. SQLite stores the rolling counters in the ignored `.rate_limit.sqlite3` file so concurrent processes on the same machine share the limit.

By default, the command-line app identifies its caller as `local`. To enforce per-client quotas for three users, configure a distinct `FITDESK_CLIENT_ID` for each user. This is an identifier, not authentication. Processes must use the same local database file to share the total cap; separate machines or hosted instances need a shared service/database.

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

The chatbot prompts for messages continuously. Say `done`, `exit`, or `quit` when you want to end the conversation. To start the chat with an opening message:

```powershell
python -m fitdesk "Hi, how much is the 12-session pack?"
```

The application replies directly in the terminal; there is no staff approval prompt in chatbot mode. This is still a local simulation—customers cannot connect over the internet.

If you do not activate the virtual environment, use its Python executable directly:

```powershell
.\.venv\Scripts\python.exe -m fitdesk
```

## Run the tests

Install dependencies as described above, then run:

```powershell
python -m pytest
```

The tests mock Gemini calls, so they do not need an API key, internet access, or a paid AI request. They cover continuous chat, greetings, follow-up context, booking safety, knowledge-base context, approved-data lookups, error handling, rate limiting, and status logging. The staff-reviewed `process_enquiry` path is retained for assessment tests but is not used by the chatbot command.

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
| `cli.py` | Runs the continuous terminal chat, handles exit commands and conversation context, classifies messages, grounds replies, and logs each turn. It also retains `process_enquiry` for the separate staff-reviewed assessment workflow. |
| `chat_responses.py` | Answers recognized package-price and Saturday-availability requests and follow-ups from approved data, without relying on Gemini. |
| `config.py` | Loads the Gemini key, selected model, and request timeout from `.env`. Keeping configuration here avoids embedding machine-specific values in code. |
| `ai_client.py` | Provides the single Gemini analysis entry point and reports the non-secret provider/model values written to the status log. |
| `gemini_client.py` | Sends Gemini requests using its structured JSON response schema and compact output limit, handles service errors, and validates returned analysis. |
| `knowledge_base.py` | Loads and validates the FitDesk scope rules and combines them with approved studio facts for Gemini context. Invalid or missing knowledge-base data fails closed. |
| `models.py` | Defines the allowed enquiry intents and the Pydantic `EnquiryAnalysis` model. Validation prevents unexpected AI output from flowing into later steps. |
| `rate_limiter.py` | Applies per-client and shared rolling-window request limits before Gemini is called. SQLite transactions make checks atomic across concurrent processes using the same local database file. The CLI client ID is configurable with `FITDESK_CLIENT_ID`; this value identifies a client but does not authenticate it. |
| `lookup.py` | Loads and validates approved studio data, checks what the customer actually requested, and returns matching facts. This is the boundary that prevents the model from inventing or substituting prices and availability. |
| `drafter.py` | Builds the reply from verified facts and adds the standard owner-check phrase when information is unknown. |
| `approval.py` | Keeps the staff approval prompt for the assessment's separate staff-reviewed workflow; chatbot mode does not request approval per customer message. |
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
- The retained `process_enquiry` assessment helper requires staff approval; continuous chatbot replies are displayed directly and do not require approval.
- The log is a local audit record. It is not a messaging service or proof that a customer received a reply.

## What doesn't work yet

- One local terminal conversation runs at a time; each new run starts a new conversation.
- English enquiries are the supported and tested language.
- **Known response issue:** booking intent is not recognized or acknowledged consistently for every wording. Some replies may not clearly respond to the customer's request to book, even though package-price and Saturday-availability answers generally work. The chatbot cannot create or confirm bookings; customers must contact FitDesk staff.
- Availability is sample/local data and is not refreshed from a live booking system.
- The terminal chatbot is local only; it is not deployed for public customers and does not send replies externally.
- The application does not make bookings, process payments, or integrate with WhatsApp/email.
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
