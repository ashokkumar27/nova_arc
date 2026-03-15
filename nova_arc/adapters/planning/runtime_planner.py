from __future__ import annotations

from nova_arc.bridges.contracts import BridgeRequest
from nova_arc.core.mission_profile import ActionPlan, ActionStep

from .base import PlannerAdapter


class RuntimePlannerAdapter(PlannerAdapter):
    def __init__(self, planner_bridge):
        self.planner_bridge = planner_bridge
        self.last_raw_output = None
        self.last_error = None
        self.last_usage = {}

    def plan(self, state, profile, policy_context, tool_registry):
        tool_schemas = tool_registry.describe_all()
        response = self.planner_bridge.invoke(
            BridgeRequest(
                operation="plan",
                pack_id=profile.pack_id,
                payload={
                    "system_prompt": (
                        "You are an autonomous incident commander. Return ONLY valid JSON with keys intent, strategy, steps, fallback. "
                        "Every step must include tool, args, rationale, expected_effect. Use only allowed tools."
                    ),
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "text": (
                                        f"Prime Directive: {profile.prime_directive}\n"
                                        f"Objectives: {profile.objectives}\n"
                                        f"Current State: {state.situation_summary}\n"
                                        f"Hazards: {state.hazards}\n"
                                        f"Signals: {state.signals}\n"
                                        f"Evidence: {state.evidence}\n"
                                        f"Allowed Tools: {tool_schemas}"
                                    )
                                }
                            ],
                        }
                    ],
                    "state": {
                        "summary": state.situation_summary,
                        "hazards": state.hazards,
                        "signals": state.signals,
                    },
                },
            )
        )
        self.last_error = response.error
        self.last_usage = response.usage or {}
        if not response.ok:
            raise RuntimeError(response.error or "Planner bridge failed")
        data = response.result
        self.last_raw_output = data.get("raw_text") or data
        strategy = data.get("strategy")
        if not strategy:
            raise ValueError("Live planner returned no strategy")
        steps = [
            ActionStep(
                tool=s["tool"],
                args=s.get("args", {}),
                rationale=s.get("rationale", "Planner step"),
                expected_effect=s.get("expected_effect", "Reduce operational risk"),
            )
            for s in data.get("steps", [])
            if s.get("tool")
        ]
        return ActionPlan(
            intent=data.get("intent", "Contain incident"),
            strategy=strategy,
            steps=steps,
            requires_approval=policy_context["requires_approval"],
            approval_reason=policy_context["approval_reason"],
            fallback=data.get("fallback") or "Escalate to human operations lead",
        )
