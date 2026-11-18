import io
import json
from urllib.error import HTTPError

import pytest

from fitdesk import ai_client, chat_completion, groq_client
from fitdesk.gemini_client import AIServiceError, InvalidJSONError
from fitdesk.models import Intent


def test_groq_request_uses_chat_completions(monkeypatch):
    calls = {}
    analysis = {
        "intent": "pricing",
        "details": "12 sessions",
        "packages": ["12 sessions"],
        "saturday_times": [],
        "requires_human_approval": False,
    }

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps(
                {"choices": [{"message": {"content": json.dumps(analysis)}}]}
            ).encode()

    def fake_urlopen(request, timeout):
        calls["request"] = request
        calls["timeout"] = timeout
        return Response()

    monkeypatch.setattr(groq_client, "GROQ_API_KEY", "test-key")
    monkeypatch.setattr(chat_completion, "urlopen", fake_urlopen)
    result = groq_client.analyze_enquiry("How much is 12 sessions?")

    request = calls["request"]
    body = json.loads(request.data)
    assert result.intent == Intent.PRICING
    assert request.full_url == "https://api.groq.com/openai/v1/chat/completions"
    assert request.get_method() == "POST"
    assert request.get_header("Authorization") == "Bearer test-key"
    assert request.get_header("User-agent") == "FitDesk-Enquiry-Assistant/0.1.0"
    assert body["model"] == "openai/gpt-oss-20b"
    assert body["response_format"] == {"type": "json_object"}
    assert calls["timeout"] == 20


def test_groq_missing_key_is_a_friendly_error(monkeypatch):
    monkeypatch.setattr(groq_client, "GROQ_API_KEY", "")
    with pytest.raises(AIServiceError, match="Groq API key is missing"):
        groq_client.analyze_enquiry("hello")


def test_groq_http_errors_become_service_errors(monkeypatch):
    def fail(*args, **kwargs):
        raise HTTPError(
            "https://api.groq.com/openai/v1/chat/completions",
            429,
            "Too Many Requests",
            {},
            io.BytesIO(b""),
        )

    monkeypatch.setattr(groq_client, "GROQ_API_KEY", "test-key")
    monkeypatch.setattr(chat_completion, "urlopen", fail)
    with pytest.raises(AIServiceError, match="HTTP 429"):
        groq_client.analyze_enquiry("hello")


def test_groq_invalid_response_fails_closed(monkeypatch):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b"not-json"

    monkeypatch.setattr(groq_client, "GROQ_API_KEY", "test-key")
    monkeypatch.setattr(chat_completion, "urlopen", lambda *args, **kwargs: Response())
    with pytest.raises(InvalidJSONError):
        groq_client.analyze_enquiry("hello")


def test_ai_client_routes_to_groq(monkeypatch):
    expected = object()
    monkeypatch.setattr(ai_client, "AI_PROVIDER", "groq")
    monkeypatch.setattr(ai_client.groq_client, "analyze_enquiry", lambda message: expected)

    assert ai_client.analyze_enquiry("hello") is expected
