from __future__ import annotations

from .contracts import BridgeRequest, BridgeResponse, RuntimeBridge


class NovaActBridge(RuntimeBridge):
    backend_name = "nova_act"

    def invoke(self, request: BridgeRequest) -> BridgeResponse:
        workflow_id = request.payload.get("workflow_id", "workflow")
        params = request.payload.get("parameters", {})
        summary = f"Workflow {workflow_id} completed with parameters {params}"
        return BridgeResponse(
            True,
            self.backend_name,
            request.operation,
            {
                "run_id": f"act-{workflow_id}-001",
                "status": "completed",
                "summary": summary,
                "artifacts": {"screenshots": [], "logs": []},
            },
        )
