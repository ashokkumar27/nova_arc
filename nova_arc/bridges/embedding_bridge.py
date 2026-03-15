from __future__ import annotations

from .contracts import BridgeRequest, BridgeResponse, RuntimeBridge


class MultimodalEmbeddingBridge(RuntimeBridge):
    backend_name = "mme"

    def invoke(self, request: BridgeRequest) -> BridgeResponse:
        query = request.payload.get("query", {})
        pack_id = request.pack_id
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
                "snippet": "Similar historical incident with verified resolution.",
            },
        ]
        return BridgeResponse(True, self.backend_name, request.operation, {"matches": matches})
