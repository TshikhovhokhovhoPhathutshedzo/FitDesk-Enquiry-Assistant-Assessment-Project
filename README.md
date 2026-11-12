**Hours actually spent: [ENTER YOUR REAL NUMBER]**

What this is
This repository contains a small command-line assistant for FitDesk that classifies customer enquiries, reads approved pricing and Saturday availability data, and drafts staff-review replies before anything is logged as sent.

Setup
1. Use Python 3.10+.
2. Create a virtual environment:
   python -m venv .venv
   .\.venv\Scripts\activate
3. Install the project and its dependencies:
   pip install -r requirements.txt
4. Copy .env.example to .env and fill in your free Gemini key.
5. Get a free API key from https://aistudio.google.com/. Keep the key in .env and never commit it.

Run command (provide a message as an argument or omit it for an interactive prompt)
python -m fitdesk "How much is the 12-session pack and do you have Saturday slots?"
python -m fitdesk

Test command
pytest
No API key is needed for pytest because the Gemini layer is mocked in the tests.

Project structure and design principle
The project follows a deterministic pipeline: the LLM only understands the customer message, while code reads approved data and writes the response. That prevents invented prices and fake availability claims.
- `data/fitdesk_data.json` contains the approved sample facts.
- `src/fitdesk/` contains the Gemini client, Pydantic schema, lookup, drafter, approval gate, CLI/UI, and atomic status log.
- `tests/` contains offline mocked regression and failure-path tests; `docs/` contains the SRS and evidence logs.

AI use
- Gemini docs and API examples were checked from Google AI Studio / docs to confirm the official Python SDK and structured-output flow.
- The Copilot AI assistant in this session helped implement the project structure, tests, and validation steps.

What doesn't work yet
- Only English customer enquiries are handled reliably.
- The assistant is designed for a single enquiry per CLI run.
- Availability is read from the local JSON file only; there is no real-time studio availability refresh.
- Model output edge cases are still handled conservatively, and any missing fact triggers the owner-check escalation phrase.

## Working style
<!-- TO BE WRITTEN BY ME, BY HAND, WITHOUT AI: 4 answers, 80–150 words each -->
