from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

from nova_arc.config import AppConfig

from .service import CommandCenterBackend


def create_app(db_path: str | None = None) -> FastAPI:
    config = AppConfig.from_env()
    service = CommandCenterBackend(db_path or config.backend_db_path)
    service.bootstrap(reset=False)

    app = FastAPI(title="Nova A.R.C. ColdChain Live Backend", version="1.0.0")
    app.state.service = service

    @app.get("/health")
    def health() -> dict:
        return service.health()

    @app.post("/bootstrap")
    def bootstrap(payload: dict) -> dict:
        return service.bootstrap(reset=payload.get("reset", False), pack_id=payload.get("pack_id"))

    @app.post("/incidents/ingest")
    def ingest_incident(payload: dict) -> dict:
        return service.ingest_incident(
            pack_id=payload["pack_id"],
            scenario=payload["scenario"],
            context=payload.get("context", ""),
            transcript=payload.get("transcript", ""),
        )

    @app.get("/dashboard/{pack_id}")
    def get_dashboard(pack_id: str, incident_id: str | None = Query(default=None)) -> dict:
        return service.get_dashboard(pack_id=pack_id, incident_id=incident_id)

    @app.post("/actions/start-backup-cooling")
    def start_backup_cooling(payload: dict) -> dict:
        return service.start_backup_cooling(
            pack_id=payload["pack_id"],
            zone_id=payload["zone_id"],
            incident_id=payload.get("incident_id"),
        )

    @app.post("/actions/quarantine-batch")
    def quarantine_batch(payload: dict) -> dict:
        return service.quarantine_batch(
            pack_id=payload["pack_id"],
            batch_id=payload["batch_id"],
            reason=payload.get("reason", ""),
            incident_id=payload.get("incident_id"),
            via=payload.get("via", "api"),
        )

    @app.post("/actions/hold-shipment")
    def hold_shipment(payload: dict) -> dict:
        return service.hold_shipment(
            pack_id=payload["pack_id"],
            shipment_id=payload["shipment_id"],
            reason=payload.get("reason", ""),
            incident_id=payload.get("incident_id"),
            via=payload.get("via", "api"),
            disposition=payload.get("disposition", "held"),
        )

    @app.post("/actions/notify-team")
    def notify_team(payload: dict) -> dict:
        return service.record_notification(
            pack_id=payload["pack_id"],
            channel=payload["channel"],
            provider=payload.get("provider", "slack"),
            message=payload["message"],
            incident_id=payload.get("incident_id"),
            external_status=payload.get("external_status", "queued"),
        )

    @app.post("/evidence/search")
    def search_evidence(payload: dict) -> dict:
        return service.search_evidence(
            pack_id=payload["pack_id"],
            query_text=payload.get("query_text", ""),
            top_k=int(payload.get("top_k", 4)),
        )

    @app.post("/admin/workflows/quarantine-batch")
    def run_quarantine_workflow(payload: dict) -> dict:
        try:
            return service.run_admin_workflow(
                pack_id=payload["pack_id"],
                workflow_id="quarantine_batch_v1",
                parameters=payload.get("parameters", {}),
            )
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/admin/workflows/hold-shipment")
    def run_hold_workflow(payload: dict) -> dict:
        try:
            return service.run_admin_workflow(
                pack_id=payload["pack_id"],
                workflow_id="hold_shipment_v1",
                parameters=payload.get("parameters", {}),
            )
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/admin", response_class=HTMLResponse)
    def admin(pack_id: str = Query(default="cold_chain")) -> str:
        return service.render_admin_portal_html(pack_id=pack_id)

    return app


app = create_app()
