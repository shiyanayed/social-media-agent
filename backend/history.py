"""
Persist recent posts history as JSON (server-side).
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from backend.config import HISTORY_FILE

logger = logging.getLogger(__name__)
MAX_HISTORY = 50


def _load() -> list[dict[str, Any]]:
    if not HISTORY_FILE.is_file():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(entries: list[dict[str, Any]]) -> None:
    HISTORY_FILE.write_text(
        json.dumps(entries[:MAX_HISTORY], indent=2),
        encoding="utf-8",
    )


def add_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Append a history record."""
    try:
        entries = _load()
        entry["created_at"] = datetime.now(timezone.utc).isoformat()
        entries.insert(0, entry)
        _save(entries)
        return {"status": "ok"}
    except Exception as e:
        logger.error("History save failed: %s", e)
        return {"status": "error", "message": str(e)}


def get_history(limit: int = 20) -> dict[str, Any]:
    """Return recent posts."""
    try:
        entries = _load()[:limit]
        return {"status": "ok", "history": entries}
    except Exception as e:
        return {"status": "error", "message": str(e), "history": []}
