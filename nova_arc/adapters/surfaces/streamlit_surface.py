from __future__ import annotations

import pandas as pd


class StreamlitSurfaceAdapter:
    def publish(self, profile, state, plan, results, verification, replay_events):
        return {
            "profile": {
                "pack_id": profile.pack_id,
                "name": profile.name,
                "prime_directive": profile.prime_directive,
                "objectives": profile.objectives,
                "surface_layout": profile.surface_layout,
                "report_template": profile.report_template,
            },
            "state": {
                "context": state.context,
                "situation_summary": state.situation_summary,
                "hazards": state.hazards,
                "signals": state.signals,
                "confidence": state.confidence,
                "risk_score": state.risk_score,
                "recommended_outcome": state.recommended_outcome,
                "entities": state.entities,
                "evidence": state.evidence,
            },
            "plan": {
                "intent": plan.intent,
                "strategy": plan.strategy,
                "requires_approval": plan.requires_approval,
                "approval_reason": plan.approval_reason,
                "fallback": plan.fallback,
                "steps": [
                    {"tool": s.tool, "args": s.args, "rationale": s.rationale, "expected_effect": s.expected_effect}
                    for s in plan.steps
                ],
            },
            "results": [
                {"tool": r.tool, "args": r.args, "success": r.success, "output": r.output, "category": r.category, "timestamp": r.timestamp}
                for r in results
            ],
            "verification": {
                "success": verification.success,
                "summary": verification.summary,
                "achieved_conditions": verification.achieved_conditions,
                "missed_conditions": verification.missed_conditions,
                "residual_risk": verification.residual_risk,
                "next_step": verification.next_step,
            },
            "replay": replay_events,
            "tables": {
                "results_df": pd.DataFrame([
                    {"tool": r.tool, "success": r.success, "category": r.category, "output": r.output, "timestamp": r.timestamp}
                    for r in results
                ]),
                "timeline_df": pd.DataFrame([
                    {"time": e["time"], "type": e["type"], "payload": str(e["payload"])}
                    for e in replay_events
                ]),
                "entities_df": pd.DataFrame(state.entities),
                "evidence_df": pd.DataFrame(state.evidence),
            },
        }

    def publish_abort(self, profile, state, plan, replay_events):
        return {
            "aborted": True,
            "profile": {"pack_id": profile.pack_id, "name": profile.name, "prime_directive": profile.prime_directive},
            "state": {"context": state.context, "situation_summary": state.situation_summary, "risk_score": state.risk_score},
            "plan": {"intent": plan.intent, "strategy": plan.strategy, "requires_approval": plan.requires_approval, "approval_reason": plan.approval_reason},
            "replay": replay_events,
        }
