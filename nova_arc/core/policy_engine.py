from __future__ import annotations

from .mission_profile import ActionPlan, MissionProfile, PerceivedState


class PolicyEngine:
    def __init__(self, auto_approve: bool = True):
        self.auto_approve = auto_approve

    def evaluate_state(self, profile: MissionProfile, state: PerceivedState) -> dict:
        requires_approval = state.risk_score >= profile.approval_threshold
        mandatory_notify = state.risk_score >= profile.mandatory_notify_threshold
        return {
            "requires_approval": requires_approval,
            "approval_reason": "Risk exceeds approval threshold" if requires_approval else None,
            "mandatory_notify": mandatory_notify,
        }

    def validate_plan(self, profile: MissionProfile, plan: ActionPlan, tool_registry) -> None:
        for step in plan.steps:
            tool = tool_registry.get(step.tool)
            if step.tool not in profile.allowed_tools:
                raise PermissionError(f"Tool '{step.tool}' is not allowed for pack '{profile.pack_id}'")
            if tool.category in profile.blocked_tool_categories:
                raise PermissionError(
                    f"Tool '{step.tool}' blocked by category '{tool.category}'"
                )

    def approve(self, plan: ActionPlan) -> bool:
        if not plan.requires_approval:
            return True
        if self.auto_approve:
            return True
        answer = input(f"Approve plan? {plan.approval_reason} (y/n): ").strip().lower()
        return answer == "y"
