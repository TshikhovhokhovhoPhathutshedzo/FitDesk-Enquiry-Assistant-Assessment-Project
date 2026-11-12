from contextlib import contextmanager
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parents[2] / "status_log.json"


class StatusLogError(RuntimeError):
    pass


@contextmanager
def _exclusive_log_lock():
    lock_path = LOG_FILE.with_suffix(LOG_FILE.suffix + ".lock")
    with lock_path.open("a+b") as lock_file:
        if os.name == "nt":
            import msvcrt

            lock_file.seek(0, os.SEEK_END)
            if lock_file.tell() == 0:
                lock_file.write(b"\0")
                lock_file.flush()
            lock_file.seek(0)
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def read_log() -> list[dict]:
    if not LOG_FILE.exists():
        return []
    try:
        with LOG_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
        raise StatusLogError(f"Could not read the status log: {exc}") from exc

    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        raise StatusLogError("The status log must contain a JSON list of entries.")
    return data


def append_status_entry(entry: dict) -> dict:
    with _exclusive_log_lock():
        entries = read_log()
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **entry,
        }
        entries.append(entry)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=LOG_FILE.parent,
                prefix=f".{LOG_FILE.stem}.",
                suffix=".tmp",
                delete=False,
            ) as file:
                temp_path = Path(file.name)
                json.dump(entries, file, indent=2)
                file.write("\n")
                file.flush()
                os.fsync(file.fileno())
            os.replace(temp_path, LOG_FILE)
        except OSError as exc:
            raise StatusLogError(f"Could not atomically update the status log: {exc}") from exc
        finally:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink()
    return entry
