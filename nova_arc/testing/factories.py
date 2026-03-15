from __future__ import annotations

from pathlib import Path
import tempfile

from nova_arc.backend.client import BackendClient
from nova_arc.backend.service import CommandCenterBackend
from nova_arc.config import AppConfig
from nova_arc.core.mission_profile import ActionPlan, ActionStep, MissionProfile, PerceivedState, ToolExecutionResult, VerificationResult
from nova_arc.tools.factory import build_registry as build_registry_for_runtime


def build_backend_client(db_path: str | None = None) -> BackendClient:
    db_path = db_path or str(Path(tempfile.gettempdir()) / "nova_arc_test.db")
    service = CommandCenterBackend(db_path=db_path)
    service.bootstrap(reset=True)
    return BackendClient(service=service)


def build_registry(
    browser_bridge=None,
    backend_client=None,
    config: AppConfig | None = None,
    pack_id: str = "cold_chain",
    retrieval_bridge=None,
):
    backend_client = backend_client or build_backend_client()
    return build_registry_for_runtime(
        backend_client=backend_client,
        pack_id=pack_id,
        config=config or AppConfig.from_env(),
        browser_bridge=browser_bridge,
        retrieval_bridge=retrieval_bridge,
    )


def build_profile():
    return MissionProfile(
        pack_id="cold_chain",
        name="Pharma Cold Chain Command Center",
        prime_directive="Protect product integrity, patient safety, and compliance.",
        objectives=["Contain temperature excursions", "Prevent compromised inventory release", "Maintain auditability"],
        input_modes=["telemetry", "voice", "image"],
        allowed_tools=["retrieve_evidence", "start_backup_cooling", "quarantine_batch", "hold_shipment", "notify_team"],
        approval_threshold=80,
        mandatory_notify_threshold=85,
        blocked_tool_categories=[],
        success_conditions=["chamber_stabilized", "batch_quarantined", "shipment_held_or_diverted"],
        residual_risk_target=30,
        surface_layout="ops_command_center_v1",
        report_template="compliance_incident_replay",
    )


def build_state():
    return PerceivedState(
        mission="cold_chain",
        context="Pharma DC / Vaccine Vault / KL North",
        situation_summary="Cold room excursion detected.",
        entities=[{"type": "batch", "id": "VX-204", "status": "at-risk"}],
        hazards=["temperature_excursion"],
        signals={"zone_id": "Zone-B", "batch_id": "VX-204", "shipment_id": "SHP-884", "destination": "Hub-2"},
        confidence=0.95,
        risk_score=82,
        recommended_outcome="Protect inventory integrity and compliance",
        evidence=[{"id": "doc1", "score": 0.9, "modality": "document", "source_label": "SOP PDF", "title": "SOP", "snippet": "Contain and quarantine."}],
        incident_id="cold_chain-demo",
        source_transcript="Zone B temperature is above threshold. Batch VX-204 may be affected. Shipment SHP-884 is loading now.",
    )


def build_plan():
    return ActionPlan(
        intent="Protect integrity",
        strategy="Stabilize, quarantine, hold, notify",
        steps=[ActionStep(tool="notify_team", args={"channel": "ops", "message": "test"}, rationale="Tell ops", expected_effect="Awareness")],
        requires_approval=True,
        approval_reason="Risk exceeds threshold",
        fallback="Escalate",
    )


def build_results():
    return [ToolExecutionResult(tool="notify_team", args={"channel": "ops"}, success=True, output="sent", category="notification")]


def build_verification():
    return VerificationResult(success=True, summary="Mission objectives achieved.", achieved_conditions=["batch_quarantined"], missed_conditions=[], residual_risk=22)
