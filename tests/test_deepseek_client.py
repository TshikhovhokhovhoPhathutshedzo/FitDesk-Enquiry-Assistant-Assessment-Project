import io
import json
from urllib.error import HTTPError

import pytest

from fitdesk import ai_client, deepseek_client
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


def test_deepseek_request_uses_json_mode_and_validates_response(monkeypatch):
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

    monkeypatch.setattr(deepseek_client, "DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setattr(deepseek_client, "DEEPSEEK_MODEL", "deepseek-test")
    monkeypatch.setattr(deepseek_client, "REQUEST_TIMEOUT_SECONDS", 17)
    monkeypatch.setattr(deepseek_client, "urlopen", fake_urlopen)

    result = deepseek_client.analyze_enquiry("How much is 12 sessions?")

    request = calls["request"]
    body = json.loads(request.data)
    assert result.intent == Intent.PRICING
    assert request.full_url == "https://api.deepseek.com/chat/completions"
    assert request.get_method() == "POST"
    assert request.get_header("Authorization") == "Bearer test-key"
    assert calls["timeout"] == 17
    assert body["model"] == "deepseek-test"
    assert body["response_format"] == {"type": "json_object"}
    assert body["messages"][1]["content"] == "How much is 12 sessions?"
    assert body["thinking"] == {"type": "disabled"}


def test_deepseek_missing_key_is_a_friendly_service_error(monkeypatch):
    monkeypatch.setattr(deepseek_client, "DEEPSEEK_API_KEY", "")
    with pytest.raises(AIServiceError, match="DeepSeek API key is missing"):
        deepseek_client.analyze_enquiry("hello")


def test_deepseek_http_errors_become_service_errors(monkeypatch):
    def fail(*args, **kwargs):
        raise HTTPError(
            "https://api.deepseek.com/chat/completions",
            429,
            "Too Many Requests",
            {},
            io.BytesIO(b""),
        )

    monkeypatch.setattr(deepseek_client, "DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setattr(deepseek_client, "urlopen", fail)
    with pytest.raises(AIServiceError, match="HTTP 429"):
        deepseek_client.analyze_enquiry("hello")


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
def test_deepseek_invalid_response_fails_closed(monkeypatch, response, error_type):
    class FakeResponse(_FakeResponse):
        def __init__(self):
            self.payload = response

    monkeypatch.setattr(deepseek_client, "DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setattr(deepseek_client, "urlopen", lambda *args, **kwargs: FakeResponse())
    with pytest.raises(error_type):
        deepseek_client.analyze_enquiry("hello")


def test_ai_client_routes_to_selected_provider(monkeypatch):
    expected = object()
    monkeypatch.setattr(ai_client, "AI_PROVIDER", "deepseek")
    monkeypatch.setattr(ai_client.deepseek_client, "analyze_enquiry", lambda message: expected)

    assert ai_client.analyze_enquiry("hello") is expected


def test_ai_client_keeps_gemini_as_default_provider(monkeypatch):
    expected = object()
    monkeypatch.setattr(ai_client, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(ai_client.gemini_client, "analyze_enquiry", lambda message: expected)

    assert ai_client.analyze_enquiry("hello") is expected


def test_ai_client_rejects_unknown_provider(monkeypatch):
    monkeypatch.setattr(ai_client, "AI_PROVIDER", "unknown")
    with pytest.raises(AIServiceError, match="Unsupported AI_PROVIDER"):
        ai_client.analyze_enquiry("hello")
