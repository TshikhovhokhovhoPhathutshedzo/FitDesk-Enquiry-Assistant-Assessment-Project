"""Load FitDesk scope rules and combine them with approved studio facts."""

import json
from pathlib import Path

from .lookup import DataFileError, load_data

KNOWLEDGE_BASE_FILE = Path(__file__).resolve().parents[2] / "data" / "knowledge_base.json"


def load_knowledge_base() -> dict:
    try:
        with KNOWLEDGE_BASE_FILE.open("r", encoding="utf-8") as file:
            knowledge_base = json.load(file)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DataFileError(f"Could not read the FitDesk knowledge base: {exc}") from exc

    required = (
        "company",
        "scope_definition",
        "supported_topics",
        "response_rules",
        "greeting_reply",
        "off_topic_reply",
    )
    if not isinstance(knowledge_base, dict) or any(
        key not in knowledge_base for key in required
    ):
        raise DataFileError("The FitDesk knowledge base is missing required fields.")
    if not all(
        isinstance(knowledge_base[key], str)
        for key in ("company", "scope_definition", "greeting_reply", "off_topic_reply")
    ) or not all(
        isinstance(knowledge_base[key], list)
        and all(isinstance(item, str) for item in knowledge_base[key])
        for key in ("supported_topics", "response_rules")
    ):
        raise DataFileError("The FitDesk knowledge base has invalid field types.")
    if any(
        not knowledge_base[key].strip()
        for key in ("company", "scope_definition", "greeting_reply", "off_topic_reply")
    ):
        raise DataFileError("The FitDesk knowledge base has an empty required value.")
    return knowledge_base


def load_knowledge_context() -> str:
    """Return scope rules and approved prices/availability for Gemini grounding."""
    return json.dumps(
        {
            "knowledge_base": load_knowledge_base(),
            "approved_studio_data": load_data(),
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
