import json
import re
from pathlib import Path


DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "fitdesk_data.json"


class DataFileError(RuntimeError):
    pass


def _normalize(text: str) -> str:
    normalized = (text or "").lower()
    for word, digit in (("twelve", "12"), ("five", "5")):
        normalized = re.sub(rf"\b{word}\b", digit, normalized)
    return " ".join(re.findall(r"[a-z0-9]+", normalized))


def _signature(text: str) -> list[str]:
    tokens = _normalize(text).split()
    return [token[:-1] if token.endswith("s") and len(token) > 1 else token for token in tokens]


def load_data() -> dict:
    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DataFileError(f"Could not read approved FitDesk data: {exc}") from exc

    if not isinstance(data, dict):
        raise DataFileError("Approved FitDesk data must be a JSON object.")
    if not isinstance(data.get("packages"), dict) or not isinstance(
        data.get("saturday_availability"), dict
    ):
        raise DataFileError("Approved FitDesk data is missing required sections.")
    if any(
        not isinstance(package, dict)
        or not isinstance(package.get("name"), str)
        or not isinstance(package.get("price"), str)
        for package in data["packages"].values()
    ):
        raise DataFileError("Approved package data must include string names and prices.")
    if any(
        not isinstance(slot, str) or not isinstance(status, str)
        for slot, status in data["saturday_availability"].items()
    ):
        raise DataFileError("Approved Saturday availability must use string slot names and statuses.")
    if any(
        status.casefold() not in {"available", "full"}
        for status in data["saturday_availability"].values()
    ):
        raise DataFileError("Approved Saturday status must be Available or Full.")
    return data


def _requested_package_names(message: str, data: dict) -> list[str]:
    normalized_message = _normalize(message)
    requested = []
    for package in data.get("packages", {}).values():
        name = package.get("name", "")
        normalized_name = _normalize(name)
        if normalized_name and normalized_name in normalized_message:
            requested.append(name)

    requested_counts = re.findall(r"\b(\d+)\s*[- ]?\s*sessions?\b", message.lower())
    number_words = {"five": "5", "twelve": "12"}
    for word, count in number_words.items():
        if re.search(rf"\b{word}\s*[- ]?\s*sessions?\b", message.lower()):
            requested_counts.append(count)

    for count in requested_counts:
        matched_name = next(
            (
                package.get("name", "")
                for package in data.get("packages", {}).values()
                if re.search(rf"\b{re.escape(count)}\s*[- ]?\s*sessions?\b", package.get("name", "").lower())
            ),
            None,
        )
        if matched_name:
            if matched_name not in requested:
                requested.append(matched_name)
        else:
            unknown_name = f"{count} sessions"
            if unknown_name not in requested:
                requested.append(unknown_name)

    if re.search(r"\bsingle\s+session\b", message.lower()):
        single_name = next(
            (
                package.get("name", "")
                for package in data.get("packages", {}).values()
                if _normalize(package.get("name", "")) == "single session"
            ),
            None,
        )
        if single_name and single_name not in requested:
            requested.append(single_name)
    return requested


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


def extract_known_facts(analysis, message: str = "") -> dict:
    data = load_data()
    known = {
        "prices": {},
        "availability": {},
        "unknown": [],
    }

    packages = _requested_package_names(message, data)
    for package_name in packages:
        package = next(
            (
                item
                for item in data.get("packages", {}).values()
                if item.get("name") == package_name
            ),
            None,
        )
        if package is None:
            known["unknown"].append(package_name)
        else:
            known["prices"][package["name"]] = package["price"]

    if not message:
        for package_name in analysis.packages:
            package = find_package(package_name)
            if package is None:
                known["unknown"].append(package_name)
            else:
                known["prices"][package["name"]] = package["price"]

    saturday_times = analysis.saturday_times or []
    if message:
        requested_times = re.findall(r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b", message)
        known_times = data.get("saturday_availability", {})
        if "saturday" not in message.lower():
            saturday_times = []
        elif requested_times:
            saturday_times = [time for time in known_times if time in requested_times]
        elif any(
            word in message.lower()
            for word in ("slot", "availability", "available", "free")
        ):
            saturday_times = list(known_times)
        else:
            saturday_times = []
        for requested_time in requested_times:
            if requested_time not in known_times:
                known["unknown"].append(requested_time)
        unsupported_days = re.findall(
            r"\b(monday|tuesday|wednesday|thursday|friday|sunday)\b",
            message.lower(),
        )
        known["unknown"].extend(day for day in unsupported_days if day not in known["unknown"])
        if re.search(r"\bclasses?\b", message.lower()):
            known["unknown"].append("class information")
        note = _normalize(analysis.details)
        if note and note in _normalize(message) and not any(
            existing in note for existing in (_normalize(name) for name in packages)
        ):
            if note not in (_normalize(item) for item in known["unknown"]):
                known["unknown"].append(analysis.details)
    elif not saturday_times and analysis.details:
        saturday_times = [time for time in data.get("saturday_availability", {}) if time in analysis.details]

    for slot in saturday_times:
        if slot in data.get("saturday_availability", {}):
            known["availability"][slot] = data["saturday_availability"][slot]
        else:
            known["unknown"].append(slot)

    return known
