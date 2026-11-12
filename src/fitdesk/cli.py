import sys
from pathlib import Path

from .approval import get_staff_decision
from .drafter import draft_reply
from .gemini_client import AIServiceError, InvalidJSONError, SchemaValidationError, analyze_enquiry
from .lookup import extract_known_facts
from .status_log import append_status_entry
from .ui import show_customer_message, show_draft_reply, show_understood_analysis


def process_enquiry(message: str, staff_decision_func=get_staff_decision):
    show_customer_message(message)

    try:
        analysis = analyze_enquiry(message)
    except InvalidJSONError:
        entry = {
            "original_message": message,
            "intent": "unknown",
            "draft_text": "",
            "status": "failed_invalid_json",
            "escalation": False,
            "reason": "AI returned invalid JSON.",
        }
        append_status_entry(entry)
        return {"status": "failed_invalid_json", "draft": "", "escalation": False}
    except (AIServiceError, SchemaValidationError) as exc:
        entry = {
            "original_message": message,
            "intent": "unknown",
            "draft_text": "",
            "status": "failed_ai_service",
            "escalation": False,
            "reason": str(exc),
        }
        append_status_entry(entry)
        return {"status": "failed_ai_service", "draft": "", "escalation": False}

    show_understood_analysis(analysis)
    facts = extract_known_facts(analysis)
    draft_text, escalation = draft_reply(analysis, facts)
    show_draft_reply(draft_text)

    decision = staff_decision_func()
    if decision == "n":
        entry = {
            "original_message": message,
            "intent": analysis.intent.value,
            "draft_text": draft_text,
            "status": "rejected_by_staff",
            "escalation": escalation,
            "reason": "Staff answered n.",
        }
        append_status_entry(entry)
        return {"status": "rejected_by_staff", "draft": draft_text, "escalation": escalation}

    if escalation and not analysis.requires_human_approval:
        # staff approval is always required, but escalation should still be logged as sent if approved.
        pass

    entry = {
        "original_message": message,
        "intent": analysis.intent.value,
        "draft_text": draft_text,
        "status": "sent",
        "escalation": escalation,
        "reason": "Staff approved the draft.",
    }
    append_status_entry(entry)
    return {"status": "sent", "draft": draft_text, "escalation": escalation}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("Usage: python -m fitdesk \"customer message\"")
        return 1

    message = " ".join(argv)
    result = process_enquiry(message)
    if result["status"] != "sent":
        print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
