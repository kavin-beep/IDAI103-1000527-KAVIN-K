"""Append-only JSONL log of every generation, used for tuning and validation evidence."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from coachbot import config


def prompt_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:10]


def log_event(record: dict, path: Path = config.LOG_FILE) -> None:
    """Never log API keys or the athlete's name; prompts are stored as a hash."""
    path.parent.mkdir(parents=True, exist_ok=True)
    safe = {k: v for k, v in record.items() if k not in {"api_key", "name"}}
    safe["ts"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(safe, ensure_ascii=False) + "\n")


def read_logs(path: Path = config.LOG_FILE) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows
