from __future__ import annotations

from typing import Any, Dict
import json
from urllib import request as urllib_request

from .service import CommandCenterBackend


class BackendClient:
    def __init__(self, backend_url: str | None = None, service: CommandCenterBackend | None = None):
        self.backend_url = (backend_url or "").rstrip("/")
        self.service = service

    def bootstrap(self, reset: bool = False, pack_id: str | None = None) -> Dict[str, Any]:
        if self.service:
            return self.service.bootstrap(reset=reset, pack_id=pack_id)
        return self._request("POST", "/bootstrap", {"reset": reset, "pack_id": pack_id})

    def health(self) -> Dict[str, Any]:
        if self.service:
            return self.service.health()
        return self._request("GET", "/health")

    def ingest_incident(self, pack_id: str, scenario: str, context: str, transcript: str) -> Dict[str, Any]:
        payload = {"pack_id": pack_id, "scenario": scenario, "context": context, "transcript": transcript}
        if self.service:
            return self.service.ingest_incident(**payload)
        return self._request("POST", "/incidents/ingest", payload)

    def get_dashboard(self, pack_id: str, incident_id: str | None = None) -> Dict[str, Any]:
        if self.service:
            return self.service.get_dashboard(pack_id=pack_id, incident_id=incident_id)
        path = f"/dashboard/{pack_id}"
        if incident_id:
            path = f"{path}?incident_id={incident_id}"
        return self._request("GET", path)

    def start_backup_cooling(self, pack_id: str, zone_id: str, incident_id: str | None = None) -> Dict[str, Any]:
        payload = {"pack_id": pack_id, "zone_id": zone_id, "incident_id": incident_id}
        if self.service:
            return self.service.start_backup_cooling(**payload)
        return self._request("POST", "/actions/start-backup-cooling", payload)

    def quarantine_batch(self, pack_id: str, batch_id: str, reason: str, incident_id: str | None = None, via: str = "api") -> Dict[str, Any]:
        payload = {"pack_id": pack_id, "batch_id": batch_id, "reason": reason, "incident_id": incident_id, "via": via}
        if self.service:
            return self.service.quarantine_batch(**payload)
        return self._request("POST", "/actions/quarantine-batch", payload)

    def hold_shipment(
        self,
        pack_id: str,
        shipment_id: str,
        reason: str,
        incident_id: str | None = None,
        via: str = "api",
        disposition: str = "held",
    ) -> Dict[str, Any]:
        payload = {
            "pack_id": pack_id,
            "shipment_id": shipment_id,
            "reason": reason,
            "incident_id": incident_id,
            "via": via,
            "disposition": disposition,
        }
        if self.service:
            return self.service.hold_shipment(**payload)
        return self._request("POST", "/actions/hold-shipment", payload)

    def record_notification(
        self,
        pack_id: str,
        channel: str,
        provider: str,
        message: str,
        incident_id: str | None = None,
        external_status: str = "queued",
    ) -> Dict[str, Any]:
        payload = {
            "pack_id": pack_id,
            "channel": channel,
            "provider": provider,
            "message": message,
            "incident_id": incident_id,
            "external_status": external_status,
        }
        if self.service:
            return self.service.record_notification(**payload)
        return self._request("POST", "/actions/notify-team", payload)

    def search_evidence(self, pack_id: str, query_text: str, top_k: int = 4) -> Dict[str, Any]:
        payload = {"pack_id": pack_id, "query_text": query_text, "top_k": top_k}
        if self.service:
            return self.service.search_evidence(**payload)
        return self._request("POST", "/evidence/search", payload)

    def run_admin_workflow(self, pack_id: str, workflow_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        payload = {"pack_id": pack_id, "parameters": parameters}
        if self.service:
            return self.service.run_admin_workflow(pack_id=pack_id, workflow_id=workflow_id, parameters=parameters)
        path = "/admin/workflows/quarantine-batch" if workflow_id == "quarantine_batch_v1" else "/admin/workflows/hold-shipment"
        return self._request("POST", path, payload)

    def render_admin_portal_html(self, pack_id: str = "cold_chain") -> str:
        if self.service:
            return self.service.render_admin_portal_html(pack_id=pack_id)
        with urllib_request.urlopen(f"{self.backend_url}/admin?pack_id={pack_id}") as response:
            return response.read().decode("utf-8")

    def _request(self, method: str, path: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
        url = f"{self.backend_url}{path}"
        data = None
        headers = {}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib_request.Request(url=url, data=data, headers=headers, method=method)
        with urllib_request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
