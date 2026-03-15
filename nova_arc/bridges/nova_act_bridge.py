from __future__ import annotations

from nova_arc.config import AppConfig

from .contracts import BridgeRequest, BridgeResponse, RuntimeBridge


class NovaActBridge(RuntimeBridge):
    backend_name = "nova-act-bridge"

    def __init__(self, backend_client, config: AppConfig):
        self.backend_client = backend_client
        self.config = config

    def health(self) -> dict:
        return {
            "ok": True,
            "backend": self.backend_name,
            "detail": "local admin portal workflow bridge active",
            "portal_url": self.config.admin_portal_base_url,
        }

    def invoke(self, request: BridgeRequest) -> BridgeResponse:
        workflow_id = request.payload.get("workflow_id", "")
        try:
            result = self.backend_client.run_admin_workflow(
                pack_id=request.pack_id,
                workflow_id=workflow_id,
                parameters=request.payload.get("parameters", {}),
            )
            return BridgeResponse(True, self.backend_name, request.operation, result)
        except Exception as exc:
            return BridgeResponse(False, self.backend_name, request.operation, {}, error=f"{type(exc).__name__}: {exc}")
