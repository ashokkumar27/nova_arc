from __future__ import annotations

from typing import List

from .mission_profile import MissionProfile, PerceivedState, ToolExecutionResult, VerificationResult


class Verifier:
    def verify(
        self,
        profile: MissionProfile,
        state: PerceivedState,
        results: List[ToolExecutionResult],
    ) -> VerificationResult:
        successful_tools = {r.tool for r in results if r.success}
        achieved = []
        missed = []
        for condition in profile.success_conditions:
            if self._condition_met(condition, successful_tools):
                achieved.append(condition)
            else:
                missed.append(condition)
        success = not missed
        residual_risk = max(5, state.risk_score - (len(achieved) * 20))
        return VerificationResult(
            success=success,
            summary="Mission objectives achieved." if success else "Mission partially achieved. Residual operational risk remains.",
            achieved_conditions=achieved,
            missed_conditions=missed,
            residual_risk=residual_risk,
            next_step=None if success else "Escalate to human command and continue containment",
        )

    def _condition_met(self, condition: str, successful_tools: set[str]) -> bool:
        mapping = {
            "chamber_stabilized": "start_backup_cooling" in successful_tools,
            "batch_quarantined": "quarantine_batch" in successful_tools,
            "shipment_diverted": "divert_shipment" in successful_tools,
            "load_shed": "shed_load" in successful_tools,
            "transformer_isolated": "isolate_transformer" in successful_tools,
            "engineer_dispatched": "dispatch_field_engineer" in successful_tools,
        }
        return mapping.get(condition, False)
