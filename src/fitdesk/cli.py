import json
import sys

from .approval import ApprovalCancelled, get_staff_decision
from .drafter import draft_reply
from .gemini_client import AIServiceError, InvalidJSONError, analyze_enquiry
from .lookup import DataFileError, extract_known_facts
from .status_log import StatusLogError, append_status_entry
from .ui import show_customer_message, show_draft_reply, show_error, show_understood_analysis


def _record_result(entry: dict, result: dict) -> dict:
    try:
        append_status_entry(entry)
    except (OSError, StatusLogError) as exc:
        print(f"Could not record enquiry status: {exc}")
        return {
            "status": "failed_status_log",
            "draft": result.get("draft", ""),
            "escalation": result.get("escalation", False),
        }
    return result


def _failure_result(message: str, status: str, reason: str) -> dict:
    return _record_result(
        {
            "original_message": message,
            "intent": "unknown",
            "draft_text": "",
            "status": status,
            "escalation": False,
            "reason": reason,
        },
        {"status": status, "draft": "", "escalation": False},
    )


def process_enquiry(message: str, staff_decision_func=get_staff_decision):
    message = message.strip()
    if not message:
        return _failure_result("", "failed_empty_input", "Customer message was empty.")

    show_customer_message(message)

    try:
        analysis = analyze_enquiry(message)
    except KeyboardInterrupt:
        return _failure_result(message, "failed_cancelled", "Enquiry processing was cancelled.")
    except InvalidJSONError as exc:
        return _failure_result(message, "failed_invalid_json", str(exc))
    except AIServiceError as exc:
        return _failure_result(message, "failed_ai_service", str(exc))

    show_understood_analysis(analysis)
    try:
        facts = extract_known_facts(analysis, message)
    except DataFileError as exc:
        return _failure_result(message, "failed_data", str(exc))
    except (OSError, json.JSONDecodeError) as exc:
        return _failure_result(
            message,
            "failed_data",
            f"Could not read approved FitDesk data: {exc}",
        )

    draft_text, escalation = draft_reply(analysis, facts)
    show_draft_reply(draft_text)

    try:
        decision = staff_decision_func()
    except ApprovalCancelled:
        return _record_result(
            {
                "original_message": message,
                "intent": analysis.intent.value,
                "draft_text": draft_text,
                "status": "failed_cancelled",
                "escalation": escalation,
                "reason": "Staff approval was cancelled.",
            },
            {"status": "failed_cancelled", "draft": draft_text, "escalation": escalation},
        )

    if decision == "n":
        status = "rejected_by_staff"
        reason = "Staff answered n."
    elif decision == "y":
        status = "sent"
        reason = "Staff approved the draft."
    else:
        status = "failed_approval"
        reason = "Staff approval response was not y or n."

    return _record_result(
        {
            "original_message": message,
            "intent": analysis.intent.value,
            "draft_text": draft_text,
            "status": status,
            "escalation": escalation,
            "reason": reason,
        },
        {"status": status, "draft": draft_text, "escalation": escalation},
    )


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv:
        message = " ".join(argv)
    else:
        try:
            message = input("Customer message: ")
        except (EOFError, KeyboardInterrupt):
            _failure_result("", "failed_cancelled", "Customer input was cancelled.")
            show_error("Enquiry input was cancelled. Nothing was sent.")
            return 1

    if not message.strip():
        result = process_enquiry("")
        show_error("Please enter a customer enquiry. Nothing was sent.")
        return 1

    try:
        result = process_enquiry(message)
    except KeyboardInterrupt:
        _failure_result(message, "failed_cancelled", "Enquiry processing was cancelled.")
        show_error("Enquiry processing was cancelled. Nothing was sent.")
        return 1

    if result["status"] != "sent":
        messages = {
            "failed_ai_service": "AI service unavailable. Check the API key or connection; nothing was sent.",
            "failed_invalid_json": "The AI response was invalid. Nothing was sent.",
            "failed_data": "Approved studio data could not be read. Nothing was sent.",
            "failed_status_log": "The result could not be recorded. Nothing was sent.",
            "failed_cancelled": "Enquiry processing was cancelled. Nothing was sent.",
            "failed_approval": "Staff approval was not confirmed. Nothing was sent.",
            "rejected_by_staff": "Staff rejected the draft. Nothing was sent.",
        }
        show_error(messages.get(result["status"], "The enquiry was not sent."))
        return 1
    print("Approved and recorded as sent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
