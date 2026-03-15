from __future__ import annotations

from typing import List

from .mission_profile import MissionProfile, PerceivedState, ToolExecutionResult, VerificationResult


class Verifier:
    def __init__(self, backend_client=None):
        self.backend_client = backend_client

    def verify(
        self,
        profile: MissionProfile,
        state: PerceivedState,
        results: List[ToolExecutionResult],
    ) -> VerificationResult:
        successful_tools = {result.tool for result in results if result.success}
        backend_snapshot = {}
        if self.backend_client and state.incident_id:
            backend_snapshot = self.backend_client.get_dashboard(profile.pack_id, incident_id=state.incident_id)

        achieved = []
        missed = []
        for condition in profile.success_conditions:
            if self._condition_met(condition, successful_tools, backend_snapshot):
                achieved.append(condition)
            else:
                missed.append(condition)

        success = not missed
        residual_risk = max(5, state.risk_score - (len(achieved) * 18))
        if backend_snapshot.get("incident", {}).get("status") == "cooling_started":
            residual_risk = max(5, residual_risk - 4)

        return VerificationResult(
            success=success,
            summary="Mission objectives achieved." if success else "Mission partially achieved. Residual risk remains.",
            achieved_conditions=achieved,
            missed_conditions=missed,
            residual_risk=residual_risk,
            next_step=None if success else "Escalate to human command and continue containment",
            details={"backend_snapshot": backend_snapshot},
        )

    def _condition_met(self, condition: str, successful_tools: set[str], backend_snapshot: dict) -> bool:
        incident_status = backend_snapshot.get("incident", {}).get("status")
        batches = backend_snapshot.get("batches", [])
        shipments = backend_snapshot.get("shipments", [])
        batch_quarantined = any(item.get("status") == "quarantined" for item in batches)
        shipment_held = any(item.get("status") in {"held", "diverted"} for item in shipments)
        mapping = {
            "chamber_stabilized": incident_status == "cooling_started" or "start_backup_cooling" in successful_tools,
            "batch_quarantined": batch_quarantined or "quarantine_batch" in successful_tools,
            "shipment_held_or_diverted": shipment_held or "hold_shipment" in successful_tools,
            "load_shed": "shed_load" in successful_tools,
            "transformer_isolated": "isolate_transformer" in successful_tools,
            "engineer_dispatched": "dispatch_field_engineer" in successful_tools,
        }
        return mapping.get(condition, False)
