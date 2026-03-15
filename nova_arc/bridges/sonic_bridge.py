from __future__ import annotations

from typing import Iterator
import uuid

from nova_arc.config import AppConfig

from .contracts import BridgeRequest, BridgeResponse, RuntimeBridge


class NovaSonicBridge(RuntimeBridge):
    backend_name = "nova-2-sonic"

    def __init__(self, config: AppConfig, enabled: bool = False):
        self.config = config
        self.model_id = config.nova_sonic_model_id
        self.enabled = enabled

    def health(self) -> dict:
        return {
            "ok": True,
            "backend": self.backend_name,
            "detail": "transcript-first Sonic contract active" if not self.enabled else "live Sonic bridge contract active",
            "model_id": self.model_id,
        }

    def invoke(self, request: BridgeRequest) -> BridgeResponse:
        text = request.payload.get("text", "").strip()
        session_id = f"sonic-{uuid.uuid4().hex[:8]}"
        events = list(self.stream(request))
        return BridgeResponse(
            True,
            self.backend_name,
            request.operation,
            {
                "session_id": session_id,
                "text": text or "Operator alert received.",
                "events": events,
                "ingress_label": "Voice Ingress: Nova 2 Sonic",
            },
        )

    def stream(self, request: BridgeRequest) -> Iterator[dict]:
        text = request.payload.get("text", "").strip() or "Operator alert received."
        yield {"event_type": "session_started", "data": {"provider": self.backend_name, "model_id": self.model_id}}
        yield {"event_type": "input_transcript", "data": {"text": text}}
        yield {"event_type": "assistant_text", "data": {"text": "Incident acknowledged. Grounding evidence and planning response."}}
        yield {"event_type": "session_end", "data": {"status": "complete"}}
