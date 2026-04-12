"""In-memory session store. Swap _store for Redis in production."""
import uuid
from typing import Any, Dict

import pandas as pd

_store: Dict[str, Dict[str, Any]] = {}


def create_session() -> str:
    sid = str(uuid.uuid4())
    _store[sid] = {}
    return sid


def exists(session_id: str) -> bool:
    return session_id in _store


def get(session_id: str, key: str, default=None):
    return _store.get(session_id, {}).get(key, default)


def set_value(session_id: str, key: str, value: Any):
    if session_id not in _store:
        _store[session_id] = {}
    _store[session_id][key] = value


def delete_session(session_id: str):
    _store.pop(session_id, None)
