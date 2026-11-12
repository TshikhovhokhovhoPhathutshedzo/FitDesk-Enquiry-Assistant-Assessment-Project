from .lookup import extract_known_facts

ESCALATION_PHRASE = "I'll check with the owner and come back to you."


def draft_reply(analysis, facts: dict | None = None) -> tuple[str, bool]:
    if facts is None:
        facts = extract_known_facts(analysis)

    known_prices = facts.get("prices", {})
    availability = facts.get("availability", {})
    unknown_parts = facts.get("unknown", [])

    if not known_prices and not availability:
        return ESCALATION_PHRASE, True

    sentences = []
    for label, price in known_prices.items():
        sentences.append(f"The {label} is {price}.")

    for slot, status in availability.items():
        status_text = "available" if status.lower() == "available" else "full"
        sentences.append(f"Saturday {slot} is {status_text}.")

    if unknown_parts:
        sentences.append(ESCALATION_PHRASE)
        return " ".join(sentences), True

    return " ".join(sentences), False
