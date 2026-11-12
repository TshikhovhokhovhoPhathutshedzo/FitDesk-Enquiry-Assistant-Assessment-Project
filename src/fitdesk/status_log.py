import json
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parents[2] / "status_log.json"


def _ensure_log_file() -> None:
    if not LOG_FILE.exists():
        LOG_FILE.write_text("[]\n", encoding="utf-8")


def read_log() -> list[dict]:
    if not LOG_FILE.exists():
        return []
    try:
        with LOG_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError):
        return []
    return []


def append_status_entry(entry: dict) -> dict:
    _ensure_log_file()
    entries = read_log()
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **entry,
    }
    entries.append(entry)
    temp_path = LOG_FILE.with_suffix(".tmp")
    with temp_path.open("w", encoding="utf-8") as file:
        json.dump(entries, file, indent=2)
        file.write("\n")
    temp_path.replace(LOG_FILE)
    return entry
