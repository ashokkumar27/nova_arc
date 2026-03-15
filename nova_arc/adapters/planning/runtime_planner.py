from __future__ import annotations

from nova_arc.bridges.contracts import BridgeRequest
from nova_arc.core.mission_profile import ActionPlan, ActionStep

from .base import PlannerAdapter


class RuntimePlannerAdapter(PlannerAdapter):
    def __init__(self, planner_bridge):
        self.planner_bridge = planner_bridge

    def plan(self, state, profile, policy_context, tool_registry):
        tool_schemas = tool_registry.describe_all()
        response = self.planner_bridge.invoke(
            BridgeRequest(
                operation="plan",
                pack_id=profile.pack_id,
                payload={
                    "system_prompt": (
                        "You are an autonomous incident commander. Build a safe, concise, multi-step plan "
                        "using only the allowed tools. Return JSON with intent, strategy, steps, fallback."
                    ),
                    "messages": [{
                        "role": "user",
                        "content": [{
                            "text": (
                                f"Prime Directive: {profile.prime_directive}\n"
                                f"Objectives: {profile.objectives}\n"
                                f"Current State: {state.situation_summary}\n"
                                f"Hazards: {state.hazards}\n"
                                f"Signals: {state.signals}\n"
                                f"Evidence: {state.evidence}\n"
                                f"Allowed Tools: {tool_schemas}"
                            )
                        }]
                    }],
                    "state": {
                        "summary": state.situation_summary,
                        "hazards": state.hazards,
                        "signals": state.signals,
                    },
                },
            )
        )
        if not response.ok:
            raise RuntimeError(response.error or "Planner bridge failed")
        data = response.result
        steps = [
            ActionStep(
                tool=s["tool"],
                args=s["args"],
                rationale=s["rationale"],
                expected_effect=s["expected_effect"],
            )
            for s in data.get("steps", [])
        ]
        return ActionPlan(
            intent=data.get("intent", "Contain incident"),
            strategy=data.get("strategy", "Assess and intervene"),
            steps=steps,
            requires_approval=policy_context["requires_approval"],
            approval_reason=policy_context["approval_reason"],
            fallback=data.get("fallback"),
        )
