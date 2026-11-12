from pathlib import Path

from fitdesk.cli import process_enquiry
from fitdesk.gemini_client import AIServiceError, InvalidJSONError
from fitdesk.models import EnquiryAnalysis, Intent


def _analysis(**kwargs):
    defaults = {
        "intent": Intent.PRICING_AND_AVAILABILITY,
        "details": "How much is the 12-session pack and do you have Saturday slots?",
        "packages": ["12 sessions"],
        "saturday_times": ["09:00", "10:00", "11:00"],
        "requires_human_approval": True,
    }
    defaults.update(kwargs)
    return EnquiryAnalysis(**defaults)


def test_normal_enquiry_is_sent(monkeypatch):
    monkeypatch.setattr("fitdesk.cli.analyze_enquiry", lambda message: _analysis())
    result = process_enquiry("How much is the 12-session pack and do you have Saturday slots?", lambda: "y")
    assert result["status"] == "sent"
    assert "R1,680" in result["draft"]
    assert "Saturday 09:00 is available" in result["draft"]
    assert "Saturday 10:00 is full" in result["draft"]


def test_unknown_item_uses_escalation_phrase(monkeypatch):
    monkeypatch.setattr("fitdesk.cli.analyze_enquiry", lambda message: _analysis(
        details="How much is the 25-session pack?",
        packages=["25 sessions"],
        saturday_times=[],
    ))
    result = process_enquiry("How much is the 25-session pack?", lambda: "y")
    assert result["status"] == "sent"
    assert result["draft"] == "I'll check with the owner and come back to you."
    assert result["escalation"] is True


def test_invalid_json_failure_is_recorded(monkeypatch):
    def fail(_):
        raise InvalidJSONError("bad json")

    monkeypatch.setattr("fitdesk.cli.analyze_enquiry", fail)
    result = process_enquiry("bad question", lambda: "y")
    assert result["status"] == "failed_invalid_json"
    assert result["draft"] == ""


def test_ai_service_failure_is_recorded(monkeypatch):
    def fail(_):
        raise AIServiceError("network timeout")

    monkeypatch.setattr("fitdesk.cli.analyze_enquiry", fail)
    result = process_enquiry("bad question", lambda: "y")
    assert result["status"] == "failed_ai_service"
    assert result["draft"] == ""


def test_staff_rejects_message(monkeypatch):
    monkeypatch.setattr("fitdesk.cli.analyze_enquiry", lambda message: _analysis())
    result = process_enquiry("How much is the 12-session pack and do you have Saturday slots?", lambda: "n")
    assert result["status"] == "rejected_by_staff"
    assert result["draft"]


def test_staff_approves_message(monkeypatch):
    monkeypatch.setattr("fitdesk.cli.analyze_enquiry", lambda message: _analysis())
    result = process_enquiry("How much is the 12-session pack and do you have Saturday slots?", lambda: "y")
    assert result["status"] == "sent"
    assert result["draft"]


def test_status_log_is_written_for_sent_entries(monkeypatch):
    monkeypatch.setattr("fitdesk.cli.analyze_enquiry", lambda message: _analysis())
    result = process_enquiry("How much is the 12-session pack and do you have Saturday slots?", lambda: "y")
    assert result["status"] == "sent"
    log_path = Path(__file__).resolve().parents[1] / "status_log.json"
    assert log_path.exists()
