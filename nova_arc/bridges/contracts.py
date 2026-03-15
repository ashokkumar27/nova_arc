from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, Optional
import uuid


@dataclass
class BridgeRequest:
    operation: str
    payload: Dict[str, Any]
    mode: str = "demo"
    mission_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pack_id: str = "default"
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BridgeResponse:
    ok: bool
    backend: str
    operation: str
    result: Dict[str, Any]
    usage: Dict[str, Any] = field(default_factory=dict)
    latency_ms: int = 0
    error: Optional[str] = None


class RuntimeBridge:
    backend_name = "base"

    def health(self) -> dict:
        return {"ok": True, "backend": self.backend_name}

    def invoke(self, request: BridgeRequest) -> BridgeResponse:
        raise NotImplementedError

    def stream(self, request: BridgeRequest) -> Iterator[dict]:
        raise NotImplementedError
