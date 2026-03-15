from __future__ import annotations

import pandas as pd

from nova_arc.reporting.exporters import build_export_bundle


class StreamlitSurfaceAdapter:
    def publish(self, profile, state, plan, results, verification, replay_events):
        results_df = pd.DataFrame(
            [
                {
                    "tool": result.tool,
                    "success": result.success,
                    "category": result.category,
                    "output": result.output,
                    "bridge_label": result.bridge_label,
                    "timestamp": result.timestamp,
                }
                for result in results
            ]
        )
        if results_df.empty:
            results_df = pd.DataFrame(columns=["tool", "success", "category", "output", "bridge_label", "timestamp"])

        entities_df = pd.DataFrame(state.entities)
        evidence_df = pd.DataFrame(state.evidence)
        if entities_df.empty:
            entities_df = pd.DataFrame(columns=["type", "id", "status"])
        if evidence_df.empty:
            evidence_df = pd.DataFrame(columns=["id", "score", "modality", "title", "snippet"])
        actions_df = pd.DataFrame(verification.details.get("backend_snapshot", {}).get("actions", []))

        payload = {
            "profile": {
                "pack_id": profile.pack_id,
                "name": profile.name,
                "prime_directive": profile.prime_directive,
                "objectives": profile.objectives,
                "surface_layout": profile.surface_layout,
                "report_template": profile.report_template,
            },
            "state": {
                "incident_id": state.incident_id,
                "context": state.context,
                "source_transcript": state.source_transcript,
                "voice_events": state.voice_events,
                "situation_summary": state.situation_summary,
                "hazards": state.hazards,
                "signals": state.signals,
                "confidence": state.confidence,
                "risk_score": state.risk_score,
                "recommended_outcome": state.recommended_outcome,
                "entities": state.entities,
                "evidence": state.evidence,
                "backend_snapshot": state.backend_snapshot,
                "retrieval_trace": state.retrieval_trace,
            },
            "plan": {
                "intent": plan.intent,
                "strategy": plan.strategy,
                "requires_approval": plan.requires_approval,
                "approval_reason": plan.approval_reason,
                "fallback": plan.fallback,
                "raw_output": plan.raw_output,
                "sanitization_notes": plan.sanitization_notes,
                "steps": [
                    {
                        "tool": step.tool,
                        "args": step.args,
                        "rationale": step.rationale,
                        "expected_effect": step.expected_effect,
                    }
                    for step in plan.steps
                ],
            },
            "results": [
                {
                    "tool": result.tool,
                    "args": result.args,
                    "success": result.success,
                    "output": result.output,
                    "category": result.category,
                    "details": result.details,
                    "bridge_label": result.bridge_label,
                    "timestamp": result.timestamp,
                }
                for result in results
            ],
            "verification": {
                "success": verification.success,
                "summary": verification.summary,
                "achieved_conditions": verification.achieved_conditions,
                "missed_conditions": verification.missed_conditions,
                "residual_risk": verification.residual_risk,
                "next_step": verification.next_step,
                "details": verification.details,
            },
            "replay": replay_events,
            "tables": {
                "results_df": results_df,
                "timeline_df": pd.DataFrame([{"time": event["time"], "type": event["type"], "payload": str(event["payload"])} for event in replay_events]),
                "entities_df": entities_df,
                "evidence_df": evidence_df,
                "actions_df": actions_df,
            },
        }
        payload["exports"] = build_export_bundle(payload)
        return payload

    def publish_abort(self, profile, state, plan, replay_events):
        payload = {
            "aborted": True,
            "profile": {"pack_id": profile.pack_id, "name": profile.name, "prime_directive": profile.prime_directive},
            "state": {
                "context": state.context,
                "situation_summary": state.situation_summary,
                "risk_score": state.risk_score,
                "incident_id": state.incident_id,
            },
            "plan": {
                "intent": plan.intent,
                "strategy": plan.strategy,
                "requires_approval": plan.requires_approval,
                "approval_reason": plan.approval_reason,
            },
            "replay": replay_events,
        }
        payload["exports"] = build_export_bundle(payload)
        return payload
