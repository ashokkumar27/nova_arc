from __future__ import annotations

from nova_arc.tools.registry import ToolRegistry
from nova_arc.tools.common_tools import notify_team_tool
from nova_arc.tools.local_tools import start_backup_cooling_tool, shed_load_tool, dispatch_field_engineer_tool
from nova_arc.tools.bridge_tools import quarantine_batch_tool, divert_shipment_tool, isolate_transformer_tool
from nova_arc.core.mission_profile import MissionProfile, PerceivedState, ActionPlan, ActionStep, ToolExecutionResult, VerificationResult
from nova_arc.bridges.nova_act_bridge import NovaActBridge


def build_registry(browser_bridge=None):
    browser_bridge = browser_bridge or NovaActBridge()
    registry = ToolRegistry()
    registry.register(notify_team_tool())
    registry.register(start_backup_cooling_tool())
    registry.register(quarantine_batch_tool(browser_bridge))
    registry.register(divert_shipment_tool(browser_bridge))
    registry.register(shed_load_tool())
    registry.register(isolate_transformer_tool(browser_bridge))
    registry.register(dispatch_field_engineer_tool())
    return registry


def build_profile():
    return MissionProfile(
        pack_id="cold_chain",
        name="Pharma Cold Chain Command Center",
        prime_directive="Protect product integrity, patient safety, and compliance.",
        objectives=["Contain temperature excursions", "Prevent compromised inventory release", "Maintain auditability"],
        input_modes=["telemetry", "voice", "image"],
        allowed_tools=["start_backup_cooling", "quarantine_batch", "divert_shipment", "notify_team"],
        approval_threshold=80,
        mandatory_notify_threshold=85,
        blocked_tool_categories=[],
        success_conditions=["chamber_stabilized", "batch_quarantined", "shipment_diverted"],
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
        evidence=[{"id": "doc1", "score": 0.9, "modality": "document", "title": "SOP", "snippet": "Contain and quarantine."}],
    )


def build_plan():
    return ActionPlan(
        intent="Protect integrity",
        strategy="Stabilize, quarantine, divert, notify",
        steps=[ActionStep(tool="notify_team", args={"channel":"ops","message":"test"}, rationale="Tell ops", expected_effect="Awareness")],
        requires_approval=True,
        approval_reason="Risk exceeds threshold",
        fallback="Escalate",
    )


def build_results():
    return [ToolExecutionResult(tool="notify_team", args={"channel":"ops"}, success=True, output="sent", category="notification")]


def build_verification():
    return VerificationResult(success=True, summary="Mission objectives achieved.", achieved_conditions=["batch_quarantined"], missed_conditions=[], residual_risk=22)
