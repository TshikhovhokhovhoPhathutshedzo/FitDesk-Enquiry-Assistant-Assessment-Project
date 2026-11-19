"""Run the enquiry pipeline: classify, verify facts, draft, approve, and log."""

import json
import sys

from .approval import ApprovalCancelled, get_staff_decision
from .ai_client import analyze_enquiry, get_provider_metadata
from .config import RATE_LIMIT_CLIENT_ID
from .drafter import draft_reply
from .gemini_client import AIServiceError, InvalidJSONError
from .lookup import DataFileError, extract_known_facts
from .rate_limiter import RATE_LIMITER, RateLimitExceeded, RateLimiterUnavailable
from .status_log import StatusLogError, append_status_entry
from .ui import show_customer_message, show_draft_reply, show_error, show_understood_analysis


def _record_result(entry: dict, result: dict, ai_metadata: dict | None = None) -> dict:
    try:
        append_status_entry({**(ai_metadata or {}), **entry})
    except (OSError, StatusLogError) as exc:
        print(f"Could not record enquiry status: {exc}")
        return {
            "status": "failed_status_log",
            "draft": result.get("draft", ""),
            "escalation": result.get("escalation", False),
        }
    return result


def _failure_result(
    message: str,
    status: str,
    reason: str,
    ai_metadata: dict | None = None,
) -> dict:
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
        ai_metadata,
    )


def process_enquiry(
    message: str,
    staff_decision_func=get_staff_decision,
    client_id: str = RATE_LIMIT_CLIENT_ID,
):
    message = message.strip()
    if not message:
        return _failure_result("", "failed_empty_input", "Customer message was empty.")

    show_customer_message(message)
    ai_metadata = get_provider_metadata()

    try:
        RATE_LIMITER.check(client_id)
        analysis = analyze_enquiry(message)
    except RateLimitExceeded as exc:
        return _failure_result(message, "rate_limited", str(exc), ai_metadata)
    except RateLimiterUnavailable as exc:
        return _failure_result(message, "failed_rate_limiter", str(exc), ai_metadata)
    except KeyboardInterrupt:
        return _failure_result(
            message,
            "failed_cancelled",
            "Enquiry processing was cancelled.",
            ai_metadata,
        )
    except InvalidJSONError as exc:
        return _failure_result(message, "failed_invalid_json", str(exc), ai_metadata)
    except AIServiceError as exc:
        return _failure_result(message, "failed_ai_service", str(exc), ai_metadata)

    show_understood_analysis(analysis)
    try:
        facts = extract_known_facts(analysis, message)
    except DataFileError as exc:
        return _failure_result(message, "failed_data", str(exc), ai_metadata)
    except (OSError, json.JSONDecodeError) as exc:
        return _failure_result(
            message,
            "failed_data",
            f"Could not read approved FitDesk data: {exc}",
            ai_metadata,
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
            ai_metadata,
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
        ai_metadata,
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
            "rate_limited": "Too many enquiries. Please wait before trying again.",
            "failed_rate_limiter": "The request limit could not be checked. Nothing was sent.",
        }
        show_error(messages.get(result["status"], "The enquiry was not sent."))
        return 1
    print("Approved and recorded as sent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
