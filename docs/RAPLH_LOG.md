# RAPLH log

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

### Closing answers
1. How would you stop an AI coding agent from changing unrelated files or exposing an API key?
   - Keep the repo scoped to the project folder and use .gitignore to block .env, .venv, __pycache__, pytest cache, and runtime log data.
   - Only stage specific files using git add on the intended paths instead of a blind git add . and scan staged diffs for secrets before commit.

2. How would you stop the loop if the agent keeps repeating the same failed fix?
   - Stop after the third attempt on the same root cause, document the output and hypothesis, and ask for human guidance.
   - The workflow here uses a max 3-attempt rule, human review gate, and explicit test evidence before continuing.
