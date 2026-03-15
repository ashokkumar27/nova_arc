from .mission_profile import MissionProfile, PerceivedState, ActionPlan


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
        allowed = set(profile.allowed_tools)

        for step in plan.steps:
            if step.tool not in allowed:
                raise PermissionError(
                    f"Planner returned forbidden tool '{step.tool}' for pack '{profile.pack_id}'. "
                    f"Allowed tools: {sorted(allowed)}"
                )

            tool = tool_registry.get(step.tool)

            if tool.category in profile.blocked_tool_categories:
                raise PermissionError(
                    f"Tool '{step.tool}' blocked by policy category '{tool.category}'"
                )

    def approve(self, plan: ActionPlan) -> bool:
        if not plan.requires_approval:
            return True
        if self.auto_approve:
            return True
        answer = input(f"Approve plan? {plan.approval_reason} (y/n): ").strip().lower()
        return answer == "y"