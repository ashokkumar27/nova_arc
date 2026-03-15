from __future__ import annotations

from typing import Iterator

from .contracts import BridgeRequest, BridgeResponse, RuntimeBridge


class NovaSonicBridge(RuntimeBridge):
    backend_name = "sonic"

    def invoke(self, request: BridgeRequest) -> BridgeResponse:
        return BridgeResponse(True, self.backend_name, request.operation, {"text": "Voice session acknowledged."})

    def stream(self, request: BridgeRequest) -> Iterator[dict]:
        yield {"event_type": "input_transcript", "data": {"text": request.payload.get("text", "Operator alert received")}}
        yield {"event_type": "assistant_text", "data": {"text": "Incident acknowledged. Starting containment assessment."}}
        yield {"event_type": "session_end", "data": {"status": "complete"}}
