from __future__ import annotations

from typing import Any, Dict, List
import json

from .mission_profile import utc_now


class ReplayStore:
    def __init__(self):
        self.events: List[Dict[str, Any]] = []

    def log(self, event_type: str, payload: Dict[str, Any]):
        self.events.append({
            "time": utc_now(),
            "type": event_type,
            "payload": payload,
        })

    def all(self) -> List[Dict[str, Any]]:
        return self.events[:]

    def to_json(self) -> str:
        return json.dumps(self.events, indent=2, default=str)
