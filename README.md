# FitDesk Enquiry Assistant

A Python command-line assistant that helps FitDesk staff prepare replies to customer enquiries. It uses an AI model to classify what the customer asked, but uses the studio's local approved data—not the model—to determine package prices and Saturday availability. Every draft must be reviewed by staff before it is recorded as approved.

> **Important:** This is an assessment/demo application. It does not send email or messages, make bookings, take payments, or refresh live studio availability. “Approved and recorded as sent” means the staff-approved result was written to the local status log.

## What happens when it runs

1. The customer enters an enquiry in the terminal.
2. The selected AI provider classifies the request into the expected fields.
3. The application checks requested packages and times against `data/fitdesk_data.json`.
4. It builds a reply from approved facts. If a fact is missing or unsupported, it uses: `I'll check with the owner and come back to you.`
5. Staff reviews the draft and enters `y` to approve or `n` to reject. This approval is always required.
6. The outcome is recorded in `status_log.json`. Failed requests and rejected drafts are not recorded as sent.

## Requirements

- Python 3.10 or later
- An API key for the provider you select
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

Edit `.env` and set `AI_PROVIDER` to the provider you want to use: `gemini`, `deepseek`, or `openrouter`. Add that provider's key and, if needed, change its model setting. For example, to use OpenRouter:

```dotenv
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=openai/gpt-4o
REQUEST_TIMEOUT_SECONDS=20
```

Other provider settings are:

| Provider | Settings in `.env` | Default model |
|---|---|---|
| Gemini | `GEMINI_API_KEY`, `GEMINI_MODEL` | `gemini-3.8-flash` |
| DeepSeek | `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL` | `deepseek-flash` |
| OpenRouter | `OPENROUTER_API_KEY`, `OPENROUTER_MODEL` | `openai/gpt-4o` |

`AI_PROVIDER` defaults to `gemini` if it is omitted. Only the key for the selected provider is needed. Keep real credentials in `.env`; do not put them in `.env.example`, source files, screenshots, or commits. The `.env` file is ignored by Git.

Get provider keys from [Google AI Studio](https://aistudio.google.com/), [DeepSeek](https://platform.deepseek.com/api_keys), or [OpenRouter](https://openrouter.ai/keys). Check each provider's current pricing and account requirements; API access may require available credits.

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

The tests mock provider calls, so they do not need an API key, internet access, or a paid AI request. They cover provider requests and selection, response validation, approved-data lookups, draft generation, staff approval, error handling, and status logging.

## Project structure

```text
.
├── data/
│   └── fitdesk_data.json
├── docs/
│   ├── RAPLH_LOG.md
│   ├── REGRESSION_TESTS.md
│   └── SRS.md
├── src/
│   └── fitdesk/
│       ├── __init__.py
│       ├── __main__.py
│       ├── ai_client.py
│       ├── approval.py
│       ├── chat_completion.py
│       ├── cli.py
│       ├── config.py
│       ├── deepseek_client.py
│       ├── drafter.py
│       ├── gemini_client.py
│       ├── lookup.py
│       ├── models.py
│       ├── openrouter_client.py
│       ├── status_log.py
│       └── ui.py
├── tests/
│   ├── conftest.py
│   ├── test_cli.py
│   ├── test_deepseek_client.py
│   └── test_openrouter_client.py
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
| `config.py` | Loads `.env` settings, provider keys, model names, provider selection, and request timeout. Keeping configuration here avoids embedding machine-specific values in code. |
| `ai_client.py` | Routes an enquiry to the provider named by `AI_PROVIDER` and reports unsupported provider names. |
| `gemini_client.py` | Sends Gemini requests using its structured JSON response schema, handles service errors, and validates returned analysis. |
| `deepseek_client.py` | Supplies DeepSeek's endpoint and configuration to the shared chat-completion implementation. |
| `openrouter_client.py` | Supplies OpenRouter's endpoint and configuration to the shared chat-completion implementation. |
| `chat_completion.py` | Shares the JSON-mode HTTP request, error handling, and response validation used by DeepSeek and OpenRouter, avoiding duplicated code. |
| `models.py` | Defines the allowed enquiry intents and the Pydantic `EnquiryAnalysis` model. Validation prevents unexpected AI output from flowing into later steps. |
| `lookup.py` | Loads and validates approved studio data, checks what the customer actually requested, and returns matching facts. This is the boundary that prevents the model from inventing or substituting prices and availability. |
| `drafter.py` | Builds the reply from verified facts and adds the standard owner-check phrase when information is unknown. |
| `approval.py` | Keeps the staff approval prompt in a focused module and handles cancellation and invalid responses. |
| `ui.py` | Displays customer input, analysis, draft, and errors in the terminal using Rich panels. |
| `status_log.py` | Appends outcomes to `status_log.json` with locking and atomic file replacement so concurrent writes do not silently overwrite one another. |
| `__init__.py` | Marks `fitdesk` as a Python package and exposes its version. |

### Data, tests, and documentation

| Path | Purpose and importance |
|---|---|
| `data/fitdesk_data.json` | The approved source of package prices and Saturday slot statuses. Change this file when the studio's confirmed facts change; replies should use these facts rather than model-generated claims. |
| `tests/conftest.py` | Adds the `src` directory to the test import path and redirects status logs to a temporary directory, keeping tests isolated from real runtime data. |
| `tests/test_cli.py` | Exercises the application workflow, including approved facts, unsupported requests, approval decisions, and failure cases. |
| `tests/test_deepseek_client.py` | Checks DeepSeek request construction, provider routing, JSON parsing, and service failures using mocked HTTP responses. |
| `tests/test_openrouter_client.py` | Checks the equivalent OpenRouter integration and failure handling without making real API calls. |
| `docs/SRS.md` | Records the software requirements, scope, stakeholders, and acceptance criteria. |
| `docs/REGRESSION_TESTS.md` | Describes the regression-test cases and previously recorded test evidence. |
| `docs/RAPLH_LOG.md` | Keeps the project's work and bug-fix log. |

### Root-level files

| File | Purpose and importance |
|---|---|
| `.env.example` | Safe template showing the available provider settings. It contains empty credential fields; copy it to `.env` and enter secrets only there. |
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

Provider request formats were checked against their API documentation. An AI coding assistant helped with implementation and testing. All package prices and availability used by the application remain in the approved local data file.

## Working style

<!-- TO BE WRITTEN BY ME, BY HAND: 4 answers, 80–150 words each -->
