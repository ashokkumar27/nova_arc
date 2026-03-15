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
        self.last_request = {}

    def plan(self, state, profile, policy_context, tool_registry):
        tool_schemas = tool_registry.describe_all()
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "text": (
                            f"pack_id: {profile.pack_id}\n"
                            f"prime_directive: {profile.prime_directive}\n"
                            f"objectives: {profile.objectives}\n"
                            f"current_situation: {state.situation_summary}\n"
                            f"hazards: {state.hazards}\n"
                            f"signals: {state.signals}\n"
                            f"evidence: {state.evidence}\n"
                            f"allowed_tools: {tool_schemas}\n"
                            "Use only allowed tools. Return only valid JSON. No markdown. No prose outside JSON."
                        )
                    }
                ],
            }
        ]
        tool_config = {
            "tools": [
                {
                    "toolSpec": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "inputSchema": {"json": tool["input_schema"]},
                    }
                }
                for tool in tool_schemas
            ]
        }
        system_prompt = (
            "You are Amazon Nova acting as a policy-aware incident planner. "
            "Return only valid JSON with keys intent, strategy, steps, fallback. "
            "Each step must include tool, args, rationale, expected_effect. "
            "Use only allowed tools and exact argument names from the allowed tool schemas."
        )
        self.last_request = {"system_prompt": system_prompt, "messages": messages, "tool_config": tool_config}
        response = self.planner_bridge.invoke(
            BridgeRequest(
                operation="plan",
                pack_id=profile.pack_id,
                payload={
                    "system_prompt": system_prompt,
                    "messages": messages,
                    "state": {
                        "summary": state.situation_summary,
                        "hazards": state.hazards,
                        "signals": state.signals,
                        "incident_id": state.incident_id,
                    },
                    "inference_config": {"maxTokens": 1400, "temperature": 0.1, "topP": 0.9},
                    "tool_config": tool_config,
                    "strict_json": True,
                },
            )
        )
        self.last_error = response.error
        self.last_usage = response.usage or {}
        if not response.ok:
            raise RuntimeError(response.error or "Planner bridge failed")

        data = response.result
        self.last_raw_output = data.get("raw_text") or data.get("raw_content") or data
        strategy = data.get("strategy")
        if not strategy:
            raise ValueError("Planner returned no strategy")

        steps = [
            ActionStep(
                tool=step["tool"],
                args=step.get("args", {}),
                rationale=step.get("rationale", "Planner step"),
                expected_effect=step.get("expected_effect", "Reduce operational risk"),
            )
            for step in data.get("steps", [])
            if step.get("tool")
        ]

        return ActionPlan(
            intent=data.get("intent", "Contain incident"),
            strategy=strategy,
            steps=steps,
            requires_approval=policy_context["requires_approval"],
            approval_reason=policy_context["approval_reason"],
            fallback=data.get("fallback") or "Escalate to human operations lead",
            raw_output=self.last_raw_output,
        )
