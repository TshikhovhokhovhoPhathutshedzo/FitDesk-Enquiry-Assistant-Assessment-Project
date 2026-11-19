"""Run the continuous terminal chatbot and retain the assessment approval helper."""

import json
import re
import sys
from uuid import uuid4

from .approval import ApprovalCancelled, get_staff_decision
from .ai_client import analyze_enquiry, get_provider_metadata
from .chat_responses import build_local_response
from .config import RATE_LIMIT_CLIENT_ID
from .drafter import draft_reply
from .gemini_client import AIServiceError, InvalidJSONError
from .lookup import DataFileError, extract_known_facts
from .knowledge_base import load_knowledge_base
from .rate_limiter import RATE_LIMITER, RateLimitExceeded, RateLimiterUnavailable
from .status_log import StatusLogError, append_status_entry
from .ui import (
    show_chat_reply,
    show_customer_message,
    show_draft_reply,
    show_error,
    show_understood_analysis,
)


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
    except DataFileError as exc:
        return _failure_result(message, "failed_data", str(exc), ai_metadata)
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
    if analysis.is_fitdesk_related:
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
    else:
        try:
            draft_text = load_knowledge_base()["off_topic_reply"]
        except DataFileError as exc:
            return _failure_result(message, "failed_data", str(exc), ai_metadata)
        escalation = False

    show_draft_reply(draft_text)

    try:
        decision = staff_decision_func()
    except ApprovalCancelled:
        return _record_result(
            {
                "original_message": message,
                "intent": analysis.intent.value,
                "is_fitdesk_related": analysis.is_fitdesk_related,
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
            "is_fitdesk_related": analysis.is_fitdesk_related,
            "draft_text": draft_text,
            "status": status,
            "escalation": escalation,
            "reason": reason,
        },
        {"status": status, "draft": draft_text, "escalation": escalation},
        ai_metadata,
    )


_EXIT_COMMANDS = {"done", "exit", "quit"}
_GREETING_PATTERN = re.compile(
    r"^(?:hi+|hello+|hey+|good morning|good afternoon|good evening|"
    r"how are you|how's it going|how are you doing|what's up)"
    r"(?:[,\s]+fitdesk(?:\s+assistant)?)?"
    r"(?:[,\s]+(?:how are you(?: doing)?|how's it going|what's up))?[.!? ]*$",
    re.I,
)
_FOLLOW_UP_PATTERN = re.compile(
    r"\b(it|that|those|them|there|then|same|what about|and|how much|"
    r"how many|which one|what time)\b",
    re.I,
)


def _is_greeting(message: str) -> bool:
    normalized = re.sub(r"\s+", " ", message.strip())
    return bool(_GREETING_PATTERN.fullmatch(normalized))


def _lookup_message(message: str, history: list[dict[str, str]]) -> str:
    if len(message.split()) > 10 or not _FOLLOW_UP_PATTERN.search(message):
        return message
    previous_customer_messages = [
        item["content"]
        for item in history
        if item.get("role") == "user" and item.get("content", "").strip()
    ]
    return " ".join([*previous_customer_messages, message]).strip()


def _chat_failure(
    message: str,
    conversation_id: str,
    status: str,
    reason: str,
    ai_metadata: dict,
    ai_used: bool,
) -> dict:
    return _record_result(
        {
            "conversation_id": conversation_id,
            "original_message": message,
            "intent": "unknown",
            "is_fitdesk_related": None,
            "ai_used": ai_used,
            "draft_text": "",
            "status": status,
            "escalation": False,
            "reason": reason,
        },
        {"status": status, "reply": "", "escalation": False},
        ai_metadata if ai_used else None,
    )


def process_chat_turn(
    message: str,
    history: list[dict[str, str]] | None = None,
    conversation_id: str | None = None,
    client_id: str = RATE_LIMIT_CLIENT_ID,
) -> dict:
    """Answer one customer turn without the staff-draft approval workflow."""
    message = message.strip()
    if not message:
        return {"status": "ignored_empty_input", "reply": ""}

    history = history or []
    conversation_id = conversation_id or uuid4().hex
    show_customer_message(message)
    ai_metadata = get_provider_metadata()
    ai_used = False

    try:
        RATE_LIMITER.check(client_id)
        if _is_greeting(message):
            reply = load_knowledge_base()["greeting_reply"]
            escalation = False
            related = True
            intent = "other"
            ai_used = False
        elif local_response := build_local_response(message, history):
            reply = str(local_response["reply"])
            escalation = bool(local_response["escalation"])
            related = True
            intent = str(local_response["intent"])
            ai_used = False
        else:
            ai_used = True
            analysis = analyze_enquiry(message, history)
            related = analysis.is_fitdesk_related
            intent = analysis.intent.value
            if not related:
                reply = load_knowledge_base()["off_topic_reply"]
                escalation = False
            else:
                facts = extract_known_facts(analysis, _lookup_message(message, history))
                reply, escalation = draft_reply(analysis, facts)
    except RateLimitExceeded as exc:
        return _chat_failure(
            message, conversation_id, "rate_limited", str(exc), ai_metadata, ai_used
        )
    except RateLimiterUnavailable as exc:
        return _chat_failure(
            message, conversation_id, "failed_rate_limiter", str(exc), ai_metadata, ai_used
        )
    except DataFileError as exc:
        return _chat_failure(
            message, conversation_id, "failed_data", str(exc), ai_metadata, ai_used
        )
    except (OSError, json.JSONDecodeError) as exc:
        return _chat_failure(
            message,
            conversation_id,
            "failed_data",
            f"Could not read approved FitDesk data: {exc}",
            ai_metadata,
            ai_used,
        )
    except InvalidJSONError as exc:
        return _chat_failure(
            message, conversation_id, "failed_invalid_json", str(exc), ai_metadata, ai_used
        )
    except AIServiceError as exc:
        return _chat_failure(
            message, conversation_id, "failed_ai_service", str(exc), ai_metadata, ai_used
        )

    result = {"status": "responded_in_chat", "reply": reply, "escalation": escalation}
    entry = {
        "conversation_id": conversation_id,
        "original_message": message,
        "intent": intent,
        "is_fitdesk_related": related,
        "ai_used": ai_used,
        "draft_text": reply,
        "status": "responded_in_chat",
        "escalation": escalation,
        "reason": "Displayed to the customer in the local terminal chat.",
    }
    recorded = _record_result(entry, result, ai_metadata if ai_used else None)
    if recorded["status"] == "responded_in_chat":
        show_chat_reply(reply)
    return recorded


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    history: list[dict[str, str]] = []
    conversation_id = uuid4().hex
    print("FitDesk chat started. Ask about packages or Saturday availability.")
    print("Type done, exit, or quit when you want to end the conversation.")
    pending_messages = [" ".join(argv)] if argv else []

    try:
        while True:
            message = pending_messages.pop(0) if pending_messages else input("You: ")
            if message.strip().casefold() in _EXIT_COMMANDS:
                print("Chat ended. No booking was made.")
                return 0

            result = process_chat_turn(message, history, conversation_id)
            if result["status"] == "responded_in_chat":
                history.extend(
                    [
                        {"role": "user", "content": message.strip()},
                        {"role": "assistant", "content": result["reply"]},
                    ]
                )
                del history[:-20]
            else:
                messages = {
                    "failed_ai_service": "I couldn't reach the AI service. Check the API key or connection, then try again.",
                    "failed_invalid_json": "I couldn't understand the AI response. Please rephrase and try again.",
                    "failed_data": "FitDesk's approved information couldn't be read. Please try again later.",
                    "failed_status_log": "I couldn't record this response. Please try again.",
                    "rate_limited": "Please wait a moment before sending another message.",
                    "failed_rate_limiter": "I couldn't check the request limit. Please try again later.",
                }
                show_error(
                    messages.get(result["status"], "I couldn't answer that. Please try again.")
                )
    except (EOFError, KeyboardInterrupt):
        print("\nChat ended. No booking was made.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
