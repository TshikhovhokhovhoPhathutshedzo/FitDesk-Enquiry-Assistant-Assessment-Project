"""Deterministic responses for FitDesk topics backed by approved local data."""

from difflib import SequenceMatcher
import re

from .lookup import extract_known_facts, load_data


_PRICE_PATTERN = re.compile(r"\b(price|prices|cost|costs|fee|fees|pricing)\b", re.I)
_BOOKING_PATTERN = re.compile(r"\b(book|booking|reserve|reservation|appointment)\b", re.I)
_AVAILABILITY_PATTERN = re.compile(
    r"\b(available|availability|slot|slots|time|times|free|schedule)\b",
    re.I,
)
_UNSUPPORTED_DAY_PATTERN = re.compile(
    r"\b(monday|tuesday|wednesday|thursday|friday|sunday)\b",
    re.I,
)
_FITDESK_CONTEXT_PATTERN = re.compile(
    r"\b(fitdesk|package|session|training|saturday|gym|studio)\b",
    re.I,
)
_CONVERSATIONAL_REFERENCE_PATTERN = re.compile(
    r"\b(it|that|those|them|there|other|another|different|else|book(?:ing)?s?)\b",
    re.I,
)


def _customer_messages(history: list[dict[str, str]]) -> list[str]:
    return [
        item["content"].strip()
        for item in history
        if item.get("role") == "user" and item.get("content", "").strip()
    ]


def _customer_context(message: str, history: list[dict[str, str]]) -> str:
    previous_messages = _customer_messages(history)
    return " ".join([*previous_messages, message.strip()])


def _asks_price(message: str) -> bool:
    if _PRICE_PATTERN.search(message) or re.search(r"\bhow\s+muc(?:h)?\b", message, re.I):
        return True

    return any(
        SequenceMatcher(None, token.casefold(), "much").ratio() >= 0.75
        for token in re.findall(r"[a-z]+", message)
    ) and bool(re.search(r"\bhow\b", message, re.I))


def _asked_for_other_time(message: str) -> bool:
    return bool(re.search(r"\b(other|another|different|else)\b", message, re.I))


def _availability_reply(context: str, other_time: bool) -> str:
    slots = load_data()["saturday_availability"]
    requested_times = _requested_times(context)

    if other_time:
        excluded_times = set(requested_times)
        available = [
            time for time, status in slots.items()
            if status.casefold() == "available" and time not in excluded_times
        ]
        if not available:
            return (
                "I don't see another available Saturday time in the approved schedule. "
                "It isn't live, so please contact FitDesk staff to confirm current availability."
            )
        times = ", ".join(available)
        return (
            f"Other Saturday times listed as available are {times}. "
            "This schedule isn't live; it is sample data. Contact FitDesk staff "
            "to confirm and arrange a booking."
        )

    if requested_times:
        requested = [
            (time, slots.get(time))
            for time in requested_times
        ]
        details = "; ".join(
            (
                f"Saturday {time}: {status.casefold()}"
                if status is not None
                else f"Saturday {time}: not listed in the approved schedule"
            )
            for time, status in requested
        )
        return (
            f"{details}. This schedule isn't live; it is sample data. "
            "Please contact FitDesk staff to confirm and arrange a booking."
        )

    available = [
        time for time, status in slots.items()
        if status.casefold() == "available"
    ]
    full = [
        time for time, status in slots.items()
        if status.casefold() == "full"
    ]
    available_text = ", ".join(available) if available else "none currently listed"
    full_text = ", ".join(full) if full else "none"
    return (
        f"Saturday times listed as available: {available_text}. Full: {full_text}. "
        "This schedule isn't live; it is sample data. Contact FitDesk staff to "
        "confirm current availability and arrange a booking."
    )


def _requested_times(context: str) -> list[str]:
    time_pattern = re.compile(
        r"(?:(?:at|around|by|for|saturday)\s+)?"
        r"(?P<hour>\d{1,2})(?::(?P<minute>[0-5]\d))?"
        r"\s*(?P<meridiem>a\.?m\.?|p\.?m\.?)?\b",
        re.I,
    )
    times = []
    for match in time_pattern.finditer(context):
        hour_text = match.group("hour")
        minute = match.group("minute")
        meridiem = match.group("meridiem")
        if not (minute or meridiem or re.search(r"\b(?:at|around|by|for|saturday)\s*$", context[:match.start()], re.I)):
            continue
        if re.match(r"\s*(?:session|sessions|pack|packs)\b", context[match.end():], re.I):
            continue

        hour = int(hour_text)
        if meridiem:
            if not 1 <= hour <= 12:
                continue
            suffix = meridiem.casefold().replace(".", "")
            if suffix == "pm" and hour != 12:
                hour += 12
            elif suffix == "am" and hour == 12:
                hour = 0
        elif hour > 23:
            continue

        normalized = f"{hour:02d}:{int(minute or '0'):02d}"
        if normalized not in times:
            times.append(normalized)
    return times


def build_local_response(
    message: str,
    history: list[dict[str, str]] | None = None,
) -> dict[str, str | bool] | None:
    """Answer recognizable price and availability questions without model inference."""
    history = history or []
    context = _customer_context(message, history)
    asks_price = _asks_price(message)
    asks_availability = bool(
        _AVAILABILITY_PATTERN.search(message) or _BOOKING_PATTERN.search(message)
    )
    if not asks_price and not asks_availability:
        return None
    previous_context = " ".join(_customer_messages(history))
    has_current_fitdesk_context = bool(_FITDESK_CONTEXT_PATTERN.search(message))
    has_previous_fitdesk_context = bool(
        _FITDESK_CONTEXT_PATTERN.search(previous_context)
    )
    is_contextual_follow_up = bool(_CONVERSATIONAL_REFERENCE_PATTERN.search(message))
    if not has_current_fitdesk_context and not (
        has_previous_fitdesk_context and is_contextual_follow_up
    ):
        return None
    if asks_availability and _UNSUPPORTED_DAY_PATTERN.search(message):
        return None

    facts = extract_known_facts(None, context)
    response_parts = []
    escalation = False
    if asks_price:
        prices = facts["prices"]
        unknown_packages = [
            item for item in facts["unknown"]
            if re.search(r"\b(?:sessions?|packs?)\b", item, re.I)
        ]
        if prices:
            response_parts.extend(
                f"The {package} is {price}."
                for package, price in prices.items()
            )
        if unknown_packages:
            response_parts.append(
                f"I don't have approved pricing for {', '.join(unknown_packages)}. "
                "I'll check with the owner and come back to you."
            )
            escalation = True
        elif not prices:
            packages = load_data()["packages"].values()
            price_list = "; ".join(
                f"{package['name']}: {package['price']}" for package in packages
            )
            response_parts.append(
                f"FitDesk session prices are {price_list}. Which session or package "
                "would you like to know about?"
            )

    if asks_availability:
        response_parts.append(
            _availability_reply(
                context,
                _asked_for_other_time(message),
            )
        )
        if _BOOKING_PATTERN.search(context):
            response_parts.append(
                "I can't place, reserve, or confirm a booking here; contact FitDesk staff "
                "to arrange one."
            )

    return {
        "reply": " ".join(response_parts),
        "intent": "pricing_and_availability" if asks_price and asks_availability else (
            "pricing" if asks_price else "availability"
        ),
        "escalation": escalation,
    }
