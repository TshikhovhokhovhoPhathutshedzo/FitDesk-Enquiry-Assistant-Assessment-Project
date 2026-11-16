import io
import json
from urllib.error import HTTPError

import pytest

from fitdesk import ai_client, openrouter_client
from fitdesk.gemini_client import AIServiceError, InvalidJSONError, SchemaValidationError
from fitdesk.models import Intent


class _FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return self.payload


def _completion(content):
    return {"choices": [{"message": {"content": json.dumps(content)}}]}


def test_openrouter_request_uses_chat_completions_json_mode(monkeypatch):
    calls = {}

    def fake_urlopen(request, timeout):
        calls["request"] = request
        calls["timeout"] = timeout
        return _FakeResponse(
            _completion(
                {
                    "intent": "pricing",
                    "details": "12 sessions",
                    "packages": ["12 sessions"],
                    "saturday_times": [],
                    "requires_human_approval": False,
                }
            )
        )

    monkeypatch.setattr(openrouter_client, "OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(openrouter_client, "OPENROUTER_MODEL", "openai/gpt-4o")
    monkeypatch.setattr(openrouter_client, "REQUEST_TIMEOUT_SECONDS", 19)
    monkeypatch.setattr(openrouter_client, "urlopen", fake_urlopen)

    result = openrouter_client.analyze_enquiry("How much is 12 sessions?")

    request = calls["request"]
    body = json.loads(request.data)
    assert result.intent == Intent.PRICING
    assert request.full_url == "https://openrouter.ai/api/v1/chat/completions"
    assert request.get_method() == "POST"
    assert request.get_header("Authorization") == "Bearer test-key"
    assert request.get_header("Content-type") == "application/json"
    assert calls["timeout"] == 19
    assert body["model"] == "openai/gpt-4o"
    assert body["response_format"] == {"type": "json_object"}
    assert body["messages"][1]["content"] == "How much is 12 sessions?"


def test_openrouter_missing_key_is_a_friendly_service_error(monkeypatch):
    monkeypatch.setattr(openrouter_client, "OPENROUTER_API_KEY", "")
    with pytest.raises(AIServiceError, match="OpenRouter API key is missing"):
        openrouter_client.analyze_enquiry("hello")


def test_openrouter_http_errors_become_service_errors(monkeypatch):
    def fail(*args, **kwargs):
        raise HTTPError(
            "https://openrouter.ai/api/v1/chat/completions",
            429,
            "Too Many Requests",
            {},
            io.BytesIO(b""),
        )

    monkeypatch.setattr(openrouter_client, "OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(openrouter_client, "urlopen", fail)
    with pytest.raises(AIServiceError, match="HTTP 429"):
        openrouter_client.analyze_enquiry("hello")


@pytest.mark.parametrize(
    "response,error_type",
    [
        (b"not json", InvalidJSONError),
        (b"\xff", InvalidJSONError),
        (json.dumps({"choices": []}).encode("utf-8"), InvalidJSONError),
        (
            json.dumps(
                {"choices": [{"message": {"content": '{"intent":"pricing"}'}}]}
            ).encode("utf-8"),
            SchemaValidationError,
        ),
    ],
)
def test_openrouter_invalid_response_fails_closed(monkeypatch, response, error_type):
    class FakeResponse(_FakeResponse):
        def __init__(self):
            self.payload = response

    monkeypatch.setattr(openrouter_client, "OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(openrouter_client, "urlopen", lambda *args, **kwargs: FakeResponse())
    with pytest.raises(error_type):
        openrouter_client.analyze_enquiry("hello")


def test_ai_client_routes_to_openrouter(monkeypatch):
    expected = object()
    monkeypatch.setattr(ai_client, "AI_PROVIDER", "openrouter")
    monkeypatch.setattr(ai_client.openrouter_client, "analyze_enquiry", lambda message: expected)

    assert ai_client.analyze_enquiry("hello") is expected
