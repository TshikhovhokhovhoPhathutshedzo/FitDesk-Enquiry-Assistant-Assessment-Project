# Regression tests

| Test ID | Requirement | Input / precondition | Steps | Expected result | Actual result | Pass / Fail |
|---|---|---|---|---|---|---|
| RT-01 | FR-02, FR-04 | Valid enquiry for known package and Saturday slot | Mock Gemini response to pricing_and_availability; staff says y | A draft contains R1,680 and Saturday availability statuses; log shows sent | Real pytest run produced 7 passed; the fixture-based scenario passed | Pass |
| RT-02 | FR-03 | Unknown package query | Mock Gemini response with a missing package; staff says y | Draft equals exact escalation phrase and escalation flag is true | Real pytest run included the unknown-item scenario and it passed | Pass |
| RT-03 | FR-06 | Invalid JSON from AI | Mock Gemini to raise invalid JSON path | Log status is failed_invalid_json and not sent | Real pytest run included this scenario and it passed | Pass |
| RT-04 | FR-06 | AI service failure | Mock Gemini to raise AIServiceError | Log status is failed_ai_service and not sent | Real pytest run included this scenario and it passed | Pass |
| RT-05 | FR-04 | Staff says n | Mock valid AI response; staff says n | Log status is rejected_by_staff | Real pytest run included this scenario and it passed | Pass |
| RT-06 | FR-04 | Staff says y | Mock valid AI response; staff says y | Log status is sent | Real pytest run included this scenario and it passed | Pass |

## Real pytest run
```
C:/Users/Phathutshedzo/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pytest -q
.......                                                                  [100%]
7 passed, 1 warning in 2.59s
```
