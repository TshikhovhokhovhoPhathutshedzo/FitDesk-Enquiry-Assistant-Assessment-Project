import json
import re
from pathlib import Path


DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "fitdesk_data.json"


def _normalize(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", (text or "").lower()))


def _signature(text: str) -> list[str]:
    tokens = _normalize(text).split()
    return [token[:-1] if token.endswith("s") and len(token) > 1 else token for token in tokens]


def load_data() -> dict:
    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def find_package(text: str):
    message_tokens = set(_signature(text))
    data = load_data()
    packages = data.get("packages", {})
    for package_key, package_data in packages.items():
        aliases = {package_key, package_data.get("name", "")}
        for alias in list(aliases):
            alias_tokens = _signature(alias)
            if not alias_tokens:
                continue
            if all(token in message_tokens for token in alias_tokens):
                return package_data
    return None


def find_saturday_slot(text: str):
    cleaned = _normalize(text)
    data = load_data()
    slots = data.get("saturday_availability", {})
    for slot in slots:
        slot_norm = _normalize(slot)
        if slot_norm in cleaned or cleaned in slot_norm:
            return slot, slots[slot]
    return None, None


def extract_known_facts(analysis) -> dict:
    data = load_data()
    known = {
        "prices": {},
        "availability": {},
        "unknown": [],
    }

    packages = analysis.packages or []
    if not packages and analysis.details:
        packages = [analysis.details]

    for package_name in packages:
        package = find_package(package_name)
        if package is None:
            known["unknown"].append(package_name)
        else:
            known["prices"][package["name"]] = package["price"]

    saturday_times = analysis.saturday_times or []
    if not saturday_times and analysis.details:
        saturday_times = [time for time in data.get("saturday_availability", {}) if time in analysis.details]

    for slot in saturday_times:
        if slot in data.get("saturday_availability", {}):
            known["availability"][slot] = data["saturday_availability"][slot]
        else:
            known["unknown"].append(slot)

    return known
