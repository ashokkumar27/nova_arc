from __future__ import annotations

from .contracts import BridgeRequest, BridgeResponse, RuntimeBridge


class MultimodalEmbeddingBridge(RuntimeBridge):
    backend_name = "mme"

    def health(self) -> dict:
        return {"ok": True, "backend": self.backend_name, "detail": "demo grounding active"}

    def invoke(self, request: BridgeRequest) -> BridgeResponse:
        query = request.payload.get("query", {})
        pack_id = request.pack_id
        content = query.get('content', '')
        matches = [
            {
                "id": f"{pack_id}-sop-001",
                "score": 0.93,
                "modality": "document",
                "title": f"{pack_id} SOP",
                "snippet": f"Reference guidance for {query.get('type', 'text')} incident containment.",
            },
            {
                "id": f"{pack_id}-incident-014",
                "score": 0.88,
                "modality": "text",
                "title": "Prior incident replay",
                "snippet": f"Historical incident related to: {content[:80] or 'operational anomaly'}.",
            },
        ]
        return BridgeResponse(True, self.backend_name, request.operation, {"matches": matches})
