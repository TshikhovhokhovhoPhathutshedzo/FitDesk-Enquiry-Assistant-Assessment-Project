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
4. Copy .env.example to .env.
5. Set `AI_PROVIDER` to `gemini`, `deepseek`, or `openrouter`, then add the matching API key:
   - Gemini: set `GEMINI_API_KEY` and get a key from https://aistudio.google.com/.
   - DeepSeek: set `DEEPSEEK_API_KEY` from your DeepSeek account.
   - OpenRouter: set `OPENROUTER_API_KEY` from https://openrouter.ai/keys.
   Keep credentials only in `.env`; never commit them. Gemini is the default provider.

Run command (provide a message as an argument or omit it for an interactive prompt)
python -m fitdesk "How much is the 12-session pack and do you have Saturday slots?"
python -m fitdesk

Test command
pytest
No API key is needed for pytest because both provider layers are mocked in tests.

Project structure and design principle
The project follows a deterministic pipeline: the LLM only understands the customer message, while code reads approved data and writes the response. That prevents invented prices and fake availability claims.
- `data/fitdesk_data.json` contains the approved sample facts.
- `src/fitdesk/cli.py` runs the workflow: classify the enquiry, look up approved facts, draft a reply, ask staff to approve it, and record the result.
- `src/fitdesk/ai_client.py` selects Gemini, DeepSeek, or OpenRouter from `AI_PROVIDER`. `gemini_client.py` handles Gemini; DeepSeek and OpenRouter use the shared `chat_completion.py` request and validation code.
- `src/fitdesk/lookup.py` checks model-extracted requests against the approved JSON data; `drafter.py` builds replies only from those facts.
- `src/fitdesk/approval.py`, `ui.py`, and `status_log.py` handle staff confirmation, terminal display, and safe status logging.
- `src/fitdesk/models.py` defines the validated analysis structure.
- `tests/` contains offline mocked regression and failure-path tests; `docs/` contains the SRS and evidence logs.

AI use
- Gemini, DeepSeek, and OpenRouter API documentation were checked to confirm each provider's JSON response mode and request format.
- The Copilot AI assistant in this session helped implement the project structure, tests, and validation steps.

What doesn't work yet
- Only English customer enquiries are handled reliably.
- The assistant is designed for a single enquiry per CLI run.
- Availability is read from the local JSON file only; there is no real-time studio availability refresh.
- Model output edge cases are still handled conservatively, and any missing fact triggers the owner-check escalation phrase.

## Working style
<!-- TO BE WRITTEN BY ME, BY HAND, WITHOUT AI: 4 answers, 80–150 words each -->
